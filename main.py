import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Park Visitors Dashboard", layout="wide")

st.title("🌲 Dashboard สถิตินักท่องเที่ยวในอุทยานแห่งชาติ")
st.caption("ข้อมูลจาก data.go.th (กรมอุทยานแห่งชาติ สัตว์ป่า และพันธุ์พืช)")

# 2. โหลดข้อมูลอย่างปลอดภัย
@st.cache_data
def load_data():
    file_path = "data.csv"  # เปลี่ยนเป็นชื่อไฟล์ CSV ของคุณ หรือระบุ URL ตรง
    
    if not os.path.exists(file_path):
        st.error(f"ไม่พบไฟล์ข้อมูล '{file_path}' กรุณาตรวจสอบว่าอัปโหลดไฟล์ลง GitHub แล้วหรือยัง")
        return None
        
    try:
        # ลองอ่านไฟล์ CSV (รองรับทั้ง utf-8 และ tis-620 ของภาษาไทย)
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='tis-620')
        return df
    except Exception as e:
        st.error(f"โหลดข้อมูลไม่สำเร็จ: {e}")
        return None

df = load_data()

if df is not None and not df.empty:
    # แสดงตัวอย่างข้อมูล (Raw Data)
    with st.expander("🔍 ดูข้อมูลตัวอย่าง (Raw Data)"):
        st.dataframe(df)

    # หาชื่อคอลัมน์แรกที่เป็นข้อความมาใช้ทำ Filter
    text_cols = df.select_dtypes(include=['object']).columns.tolist()
    num_cols = df.select_dtypes(include=['number']).columns.tolist()

    if text_cols and num_cols:
        col_category = text_cols[0]
        col_value = num_cols[0]

        # 3. Interactive Widget (Selectbox & Slider)
        st.sidebar.header("⚙️ ตัวกรองข้อมูล")
        categories = df[col_category].dropna().unique().tolist()
        selected_category = st.sidebar.selectbox(f"เลือก {col_category}:", categories)

        # กรองข้อมูลตามที่เลือก
        filtered_df = df[df[col_category] == selected_category]

        st.subheader(f"📌 ข้อมูลของ: {selected_category}")

        col1, col2 = st.columns(2)

        # 4. กราฟที่ 1: Plotly Bar Chart
        with col1:
            st.markdown("### 📊 กราฟที่ 1: แสดงข้อมูลแบบแท่ง")
            fig1 = px.bar(
                filtered_df, 
                x=filtered_df.index, 
                y=col_value, 
                title=f"{col_value} - {selected_category}",
                color_discrete_sequence=['#2E7D32']
            )
            st.plotly_chart(fig1, use_container_width=True)

        # 5. กราฟที่ 2: Plotly Pie / Line Chart
        with col2:
            st.markdown("### 📈 กราฟที่ 2: สัดส่วนข้อมูลภาพรวม")
            top10_df = df.groupby(col_category)[col_value].sum().reset_index().nlargest(10, col_value)
            fig2 = px.pie(
                top10_df, 
                names=col_category, 
                values=col_value, 
                title=f"10 อันดับสูงสุดของ {col_category}"
            )
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("รูปแบบไฟล์ CSV ไม่ตรงกับโครงสร้างที่รองรับ (ต้องมีทั้งคอลัมน์ข้อความและตัวเลข)")