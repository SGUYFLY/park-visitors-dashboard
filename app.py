import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ---------------------------------------------------------
# 1. ตั้งค่าหน้าเว็บ Streamlit
# ---------------------------------------------------------
st.set_page_config(
    page_title="Park Visitors Dashboard",
    page_icon="🌲",
    layout="wide"
)

st.title("🌲 Dashboard สถิตินักท่องเที่ยวในอุทยานแห่งชาติ")
st.caption("ข้อมูลจาก data.go.th (กรมอุทยานแห่งชาติ สัตว์ป่า และพันธุ์พืช)")

# ---------------------------------------------------------
# 2. ฟังก์ชันโหลดข้อมูล (อ่านจาก data/parks.csv)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    file_path = os.path.join("data", "parks.csv")
    
    if not os.path.exists(file_path):
        st.error(f"❌ ไม่พบไฟล์ข้อมูลที่ '{file_path}' กรุณาตรวจสอบว่ามีไฟล์ parks.csv อยู่ในโฟลเดอร์ data")
        return None
    
    # ลองอ่านไฟล์ด้วยการลอง Encoding ภาษาไทยหลายๆ แบบ
    encodings = ['utf-8', 'utf-8-sig', 'tis-620', 'cp838', 'latin1']
    for enc in encodings:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            df.columns = df.columns.str.strip()  # ตัดช่องว่างเกินในชื่อคอลัมน์
            return df
        except Exception:
            continue
            
    st.error("❌ ไม่สามารถอ่านไฟล์ CSV ได้ กรุณาตรวจสอบรูปแบบไฟล์")
    return None

df = load_data()

# ---------------------------------------------------------
# 3. ส่วนประมวลผลและแสดงผลข้อมูล
# ---------------------------------------------------------
if df is not None and not df.empty:
    # ค้นหาคอลัมน์ประเภทข้อความและตัวเลขโดยอัตโนมัติ
    text_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
    num_cols = df.select_dtypes(include=['number']).columns.tolist()

    if not text_cols or not num_cols:
        st.warning("⚠️ ไฟล์ CSV ต้องมีทั้งคอลัมน์ข้อความและตัวเลข")
        st.dataframe(df)
        st.stop()

    # Sidebar: ตัวกรองข้อมูล (Interactive Widgets)
    st.sidebar.header("⚙️ ตัวกรองข้อมูล (Filters)")
    
    cat_col = st.sidebar.selectbox("เลือกคอลัมน์ประเภท (Category):", text_cols, index=0)
    val_col = st.sidebar.selectbox("เลือกคอลัมน์ตัวเลข (Value):", num_cols, index=0)

    # Widget สอง: Multiselect สำหรับเลือกรายการย่อย
    unique_items = df[cat_col].dropna().unique().tolist()
    selected_items = st.sidebar.multiselect(
        f"เลือก {cat_col}:",
        options=unique_items,
        default=unique_items[:10] if len(unique_items) > 10 else unique_items
    )

    if not selected_items:
        st.warning("กรุณาเลือกอย่างน้อย 1 รายการจากตัวกรองด้านข้าง")
        st.stop()

    # กรองข้อมูลตามที่เลือก
    filtered_df = df[df[cat_col].isin(selected_items)]

    # แสดง KPI สรุปผล
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("รายการทั้งหมด", f"{len(filtered_df):,} รายการ")
    col_kpi2.metric(f"ผลรวม {val_col}", f"{filtered_df[val_col].sum():,.0f}")
    col_kpi3.metric(f"ค่าเฉลี่ย {val_col}", f"{filtered_df[val_col].mean():,.2f}")

    st.markdown("---")

    # กราฟที่ 1 และ 2 (ตามเกณฑ์ข้อกำหนด)
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader(f"📊 กราฟที่ 1: แสดงเปรียบเทียบ {val_col}")
        fig_bar = px.bar(
            filtered_df,
            x=cat_col,
            y=val_col,
            color=cat_col,
            title=f"ยอดรวม {val_col} แยกตาม {cat_col}",
            text_auto='.2s'
        )
        fig_bar.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        st.subheader(f"🥧 กราฟที่ 2: สัดส่วนข้อมูล {val_col}")
        fig_pie = px.pie(
            filtered_df,
            names=cat_col,
            values=val_col,
            title=f"สัดส่วน {val_col}",
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # ตารางข้อมูล Raw Data
    with st.expander("📋 ดูตารางข้อมูลทั้งหมด (Data Table)"):
        st.dataframe(filtered_df, use_container_width=True)