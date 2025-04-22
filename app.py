
"""app.py – Circle Condominium Damage Dashboard (robust v1.2)
================================================================
• หากไม่มีไฟล์ `secrets.toml` จะไม่เกิดข้อผิดพลาดอีก — ใช้ ENV `ALLOW_IMAGES` เป็นตัวเลือกสำรอง
• ยังรองรับโหมดไม่มี Streamlit เหมือนเดิม + unit tests ภายใน
"""

from __future__ import annotations

import os
from datetime import datetime
from types import SimpleNamespace

# ---------------------------------------------------------------------------
# Optional Streamlit import (provide stub if absent) -------------------------
# ---------------------------------------------------------------------------
try:
    import streamlit as st  # type: ignore
    STREAMLIT_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover
    STREAMLIT_AVAILABLE = False

    class _SidebarStub:
        def __enter__(self):
            return st

        def __exit__(self, exc_type, exc, tb):
            return False

    class _StreamlitStub(SimpleNamespace):
        def __getattr__(self, item):
            if item in {"columns", "sidebar"}:
                return lambda *a, **kw: [self] * (a[0] if a else 1)
            if item == "cache_data":
                return lambda *a, **kw: (lambda fn: fn)
            if item in {"secrets", "slider"}:
                return {}
            if item in {"multiselect", "text_input", "checkbox"}:
                return (
                    lambda *a, **kw: kw.get("default", [])
                    if item == "multiselect"
                    else ""
                )
            return lambda *a, **kw: None

    st = _StreamlitStub()  # type: ignore

# ---------------------------------------------------------------------------
# 3rd‑party libs (Plotly optional) ------------------------------------------
# ---------------------------------------------------------------------------
import pandas as pd

try:
    import plotly.express as px  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    class _PXStub:
        @staticmethod
        def bar(*_, **__):
            return None

    px = _PXStub()  # type: ignore

# ---------------------------------------------------------------------------
# Page configuration (only if Streamlit present) ----------------------------
# ---------------------------------------------------------------------------
if STREAMLIT_AVAILABLE:
    st.set_page_config(
        page_title="Circle Condo Damage Dashboard",
        page_icon="🏢",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    st.markdown(
        """
        <style>
        @media (max-width: 768px) {.block-container {padding: 1rem;}}
        .css-1aumxhk {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Data loading & caching ----------------------------------------------------
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False) if STREAMLIT_AVAILABLE else (lambda fn: fn)  # type: ignore
def load_data() -> pd.DataFrame:
    for path in ("data/damage_data.parquet", "data/damage_data.csv"):
        try:
            if path.endswith("parquet"):
                return pd.read_parquet(path)
            return pd.read_csv(path)
        except FileNotFoundError:
            continue
    return pd.DataFrame()

df = load_data()
if "Damages Found" in df.columns:
    df["Damage Type List"] = df["Damages Found"].fillna("").apply(
        lambda x: [d.strip() for d in x.split(",") if d.strip()]
    )
else:
    df["Damage Type List"] = [[] for _ in range(len(df))]

# ---------------------------------------------------------------------------
# Sidebar filters -----------------------------------------------------------
# ---------------------------------------------------------------------------
with st.sidebar:  # type: ignore
    st.header("🔍 Filters")

    query = st.text_input(
        "Search by Room No. / keyword", placeholder="e.g. 1674/1113 or water leak"
    )
    towers = st.multiselect(
        "Tower",
        options=sorted(df.get("Tower", pd.Series(dtype=str)).dropna().unique()),
        default=sorted(df.get("Tower", pd.Series(dtype=str)).dropna().unique()),
    )
    all_dtypes = sorted({d for lst in df["Damage Type List"] for d in lst})
    damage_types = st.multiselect("Damage Type", options=all_dtypes)

    if "Severity Score" in df.columns and not df.empty:
        min_sv, max_sv = float(df["Severity Score"].min()), float(df["Severity Score"].max())
    else:
        min_sv, max_sv = 0.0, 10.0
    severity_range = st.slider(
        "Severity Score range", min_sv, max_sv, (min_sv, max_sv), step=0.5
    )

    # Safe secrets / env lookup
    try:
        _secret_val = st.secrets.get("ALLOW_IMAGES", None)
    except Exception:
        _secret_val = None
    allow_images_flag = _secret_val if _secret_val is not None else os.getenv("ALLOW_IMAGES", "false")
    allow_images = str(allow_images_flag).lower() == "true"
    show_images = st.checkbox("Display room images", value=False) if allow_images else False

    if not df.empty:
        st.download_button(
            "📥 Download full data (CSV)",
            df.to_csv(index=False).encode("utf-8-sig"),
            file_name="circle_damage_all.csv",
        )

# ---------------------------------------------------------------------------
# Helper – filtering logic --------------------------------------------------
# ---------------------------------------------------------------------------
def apply_filters(data: pd.DataFrame) -> pd.DataFrame:
    filtered = data.copy()
    if query:
        filtered = filtered[
            filtered.get("Room No", pd.Series(dtype=str)).str.contains(query, case=False, na=False)
            | filtered.get("Damages Found", pd.Series(dtype=str)).str.contains(
                query, case=False, na=False
            )
        ]
    if towers:
        filtered = filtered[filtered.get("Tower", pd.Series(dtype=str)).isin(towers)]
    if damage_types:
        filtered = filtered[
            filtered["Damage Type List"].apply(lambda lst: any(d in lst for d in damage_types))
        ]
    if "Severity Score" in filtered.columns and severity_range:
        filtered = filtered[
            (filtered["Severity Score"] >= severity_range[0])
            & (filtered["Severity Score"] <= severity_range[1])
        ]
    return filtered

filtered_df = apply_filters(df)

# ---------------------------------------------------------------------------
# KPI & Charts (Streamlit only) --------------------------------------------
# ---------------------------------------------------------------------------
if STREAMLIT_AVAILABLE:
    st.subheader("📊 Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Reports", len(filtered_df))
    if "Severity Score" in filtered_df.columns and not filtered_df.empty:
        c2.metric("Avg. Severity", f"{filtered_df['Severity Score'].mean():.1f}")
    c3.metric("Unique Rooms", filtered_df.get("Room No", pd.Series()).nunique())

    if not filtered_df.empty:
        tally = (
            filtered_df.explode("Damage Type List")["Damage Type List"].value_counts().head(10)
        )
        fig = px.bar(
            tally,
            y=tally.index,
            x=tally.values,
            orientation="h",
            labels={"y": "Damage Type", "x": "Reports"},
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data matches the selected filters.")

    st.subheader("🗂 Detailed Records")
    st.dataframe(filtered_df, use_container_width=True, height=480)

    if show_images and not filtered_df.empty:
        st.subheader("📸 Room Images")
        for _, row in filtered_df.iterrows():
            if pd.notna(row.get("Image URL")) and row["Image URL"]:
                st.image(
                    row["Image URL"], caption=row.get("Room No", ""), use_column_width=True
                )

    st.caption(f"Last updated: {datetime.utcnow():%Y-%m-%d %H:%M UTC}")

# ---------------------------------------------------------------------------
# Lightweight tests ---------------------------------------------------------
# ---------------------------------------------------------------------------
def _run_tests() -> None:
    sample = pd.DataFrame(
        {
            "Room No": ["101", "102"],
            "Tower": ["A", "B"],
            "Damages Found": ["Water leak", "Cracked wall"],
            "Severity Score": [5, 7],
        }
    )
    sample["Damage Type List"] = sample["Damages Found"].str.split(",")

    global query, towers, damage_types, severity_range
    query, towers, damage_types, severity_range = "", ["A", "B"], [], (0, 10)
    assert len(apply_filters(sample)) == 2, "Default filter should return all rows"

    query = "101"
    assert apply_filters(sample)["Room No"].tolist() == ["101"], "Keyword filter failed"

    query, damage_types = "", ["Water leak"]
    assert apply_filters(sample)["Room No"].tolist() == ["101"], "Damage‑type filter failed"

    print("✅ All tests passed")


if __name__ == "__main__":
    _run_tests()
