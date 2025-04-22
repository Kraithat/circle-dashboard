
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="รายงานความเสียหาย เซอร์เคิล คอนโด", layout="wide")

st.title("📊 รายงานความเสียหาย: เซอร์เคิล คอนโดมิเนียม")
st.markdown("**ข้อมูลจากเหตุการณ์แผ่นดินไหว วันที่ 28 มีนาคม 2568**")

# --- Static Data ---
df_damage = pd.DataFrame({
    'ประเภทความเสียหาย (Damage Type)': [
        'ผนังแตกร้าว (Cracked wall)',
        'กระเบื้องหลุด/แตก (Loose/broken tiles)',
        'เพดานแตกร้าว (Cracked ceiling)',
        'ประตู/หน้าต่าง (Doors/windows)',
        'ท่อ (ประปา) (Pipes)',
        'เฟอร์นิเจอร์เสียหาย (Damaged furniture)',
        'น้ำรั่วซึม (Water leak)',
        'ระบบไฟฟ้า (Electrical system)',
        'ระบบล้มเหลว (System failure)'
    ],
    'ความถี่ (Frequency)': [580, 330, 220, 160, 60, 50, 45, 30, 15]
}).sort_values(by='ความถี่ (Frequency)', ascending=True)

df_severity = pd.DataFrame({
    'หมายเลขห้อง (Room ID)': ['1674/479', '1674/379', '1674/47'],
    'คะแนนความรุนแรง (Severity Score)': [15.0, 14.5, 14.0]
})

df_tower = pd.DataFrame({
    'อาคาร (Tower)': ['Tower 1', 'Tower 2'],
    'จำนวนห้อง (Number of Rooms)': [11, 22]
})

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["📌 ความเสียหาย", "🚨 ห้องเร่งด่วน", "🏢 การกระจายตัวห้อง", "📋 วิเคราะห์จากแบบสอบถาม"])

# --- Tab 1 ---
with tab1:
    st.subheader("ประเภทความเสียหายที่พบบ่อย")
    fig_damage = px.bar(df_damage,
                        x='ความถี่ (Frequency)',
                        y='ประเภทความเสียหาย (Damage Type)',
                        orientation='h',
                        height=500)
    st.plotly_chart(fig_damage, use_container_width=True)

# --- Tab 2 ---
with tab2:
    st.subheader("คะแนนความรุนแรงของห้องเร่งด่วน")
    fig_severity = px.bar(df_severity,
                          x='หมายเลขห้อง (Room ID)',
                          y='คะแนนความรุนแรง (Severity Score)',
                          text='คะแนนความรุนแรง (Severity Score)',
                          height=400)
    fig_severity.update_traces(textposition='outside')
    st.plotly_chart(fig_severity, use_container_width=True)

# --- Tab 3 ---
with tab3:
    st.subheader("จำนวนห้องสำรวจในแต่ละอาคาร")
    fig_pie = px.pie(df_tower,
                     names='อาคาร (Tower)',
                     values='จำนวนห้อง (Number of Rooms)',
                     hole=0.3)
    fig_pie.update_traces(textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

# --- Tab 4 ---
with tab4:
    st.subheader("📋 วิเคราะห์จากแบบสอบถาม")

    df_freq = pd.read_csv("damage_frequency.csv")
    df_top = pd.read_csv("top10_damaged_rooms.csv")
    df_survey = pd.read_csv("survey_filtered_data.csv")

    # Filter options
    unique_types = sorted(df_survey['Damage Types'].dropna().unique())
    selected_types = st.multiselect("เลือกประเภทความเสียหายที่ต้องการดู", unique_types, default=unique_types)

    df_filtered = df_survey[df_survey['Damage Types'].isin(selected_types)].copy()

    st.markdown("### 🔎 ประเภทความเสียหายจากผู้ตอบแบบสอบถาม")
    fig_survey = px.bar(df_freq[df_freq['ประเภทความเสียหาย'].isin(selected_types)],
                        x='จำนวนที่พบ',
                        y='ประเภทความเสียหาย',
                        orientation='h',
                        height=500)
    st.plotly_chart(fig_survey, use_container_width=True)

    st.markdown("### 🧱 10 ห้องที่พบความเสียหายหลายประเภทมากที่สุด")
    st.dataframe(df_top, use_container_width=True)

    st.markdown("### 🖼️ รายการความเสียหายพร้อมลิงก์ภาพ")
    df_filtered['Image Link'] = df_filtered['Image Link'].apply(
        lambda x: f'<a href="{x}" target="_blank">ดูภาพ</a>' if pd.notnull(x) else '')
    st.write(df_filtered[['Room No', 'Damage Types', 'Image Link']].to_html(escape=False, index=False), unsafe_allow_html=True)
