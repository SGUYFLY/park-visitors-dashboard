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
        if os.path.exists("parks.csv"):
            file_path = "parks.csv"
        else:
            st.error(f"❌ ไม่พบไฟล์ข้อมูลที่ '{file_path}' กรุณาตรวจสอบโฟลเดอร์ data/parks.csv")
            return None
    
    encodings = ['utf-8', 'utf-8-sig', 'tis-620', 'cp838', 'latin1']
    for enc in encodings:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            df.columns = df.columns.str.strip()  # ตัดช่องว่างเกินในชื่อคอลัมน์
            return df
        except Exception:
            continue
            
    st.error("❌ ไม่สามารถอ่านไฟล์ CSV ได้")
    return None

df = load_data()

# ---------------------------------------------------------
# 3. การประมวลผลและสร้างระบบกรองข้อมูล (Filter by Year & Park)
# ---------------------------------------------------------
if df is not None and not df.empty:
    
    # ตรวจหาคอลัมน์ ปี, อุทยาน, และจำนวนตัวเลข โดยอัตโนมัติ
    col_year = None
    for col in df.columns:
        if 'ปี' in col or 'year' in col.lower():
            col_year = col
            break
            
    col_park = None
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['อุทยาน', 'park', 'ชื่อ', 'name', 'สถานที่']):
            col_park = col
            break
    if not col_park:
        text_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
        if text_cols:
            col_park = text_cols[0]

    # --- Sidebar: ตัวกรองข้อมูล (Interactive Widgets) ---
    st.sidebar.header("⚙️ ตัวกรองข้อมูล (Filters)")

    # 1. ตัวกรองเลือกปี (Year Filter)
    if col_year and col_year in df.columns:
        years_list = sorted(df[col_year].dropna().unique().tolist())
        selected_years = st.sidebar.multiselect(
            f"📅 เลือกปี ({col_year}):",
            options=years_list,
            default=years_list  # เลือกทุกปีไว้เป็นค่าเริ่มต้น
        )
    else:
        selected_years = []

    # 2. ตัวกรองเลือกอุทยาน
    if col_park and col_park in df.columns:
        parks_list = sorted(df[col_park].dropna().unique().tolist())
        selected_parks = st.sidebar.multiselect(
            f"🌲 เลือกอุทยาน/สถานที่ ({col_park}):",
            options=parks_list,
            default=parks_list[:10] if len(parks_list) > 10 else parks_list
        )
    else:
        selected_parks = []

    # 3. เลือกคอลัมน์ตัวเลขที่ต้องการดูสถิติ
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    if col_year in num_cols:
        num_cols.remove(col_year)  # ตัดคอลัมน์ปีออกจากตัวเลือกตัวเลข
        
    if num_cols:
        col_value = st.sidebar.selectbox("📊 เลือกตัวเลขที่ต้องการดู:", num_cols, index=0)
    else:
        col_value = None

    # --- ประมวลผลการกรองข้อมูล ---
    filtered_df = df.copy()

    if col_year and selected_years:
        filtered_df = filtered_df[filtered_df[col_year].isin(selected_years)]
        
    if col_park and selected_parks:
        filtered_df = filtered_df[filtered_df[col_park].isin(selected_parks)]

    # ตรวจสอบว่ามีข้อมูลตรงตามเงื่อนไขหรือไม่
    if filtered_df.empty:
        st.warning("⚠️ ไม่พบข้อมูลตามตัวกรองที่เลือก กรุณาเลือกปีหรืออุทยานเพิ่มเติมในเมนูด้านข้าง")
        st.stop()

    # --- แสดงผลสรุป (KPI Metrics) ---
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("จำนวนรายการที่พบ", f"{len(filtered_df):,} รายการ")
    if col_value and col_value in filtered_df.columns:
        col_kpi2.metric(f"ผลรวม {col_value}", f"{filtered_df[col_value].sum():,.0f}")
        col_kpi3.metric(f"ค่าเฉลี่ย {col_value}", f"{filtered_df[col_value].mean():,.2f}")

    st.markdown("---")

    # --- แสดงกราฟ 2 กราฟ ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📊 กราฟที่ 1: สถิตินักท่องเที่ยวแยกตามอุทยาน")
        if col_park and col_value:
            park_summary = filtered_df.groupby(col_park)[col_value].sum().reset_index()
            fig_bar = px.bar(
                park_summary,
                x=col_park,
                y=col_value,
                color=col_park,
                title=f"ยอดรวม {col_value} แยกตามอุทยาน",
                text_auto='.2s'
            )
            fig_bar.update_layout(showlegend=False, xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        st.subheader("📈 กราฟที่ 2: แนวโน้มสถิตินักท่องเที่ยวรายปี")
        if col_year and col_value:
            year_summary = filtered_df.groupby(col_year)[col_value].sum().reset_index()
            fig_line = px.line(
                year_summary,
                x=col_year,
                y=col_value,
                markers=True,
                title=f"แนวโน้ม {col_value} แยกตามปี"
            )
            st.plotly_chart(fig_line, use_container_width=True)
        elif col_park and col_value:
            fig_pie = px.pie(
                filtered_df,
                names=col_park,
                values=col_value,
                title=f"สัดส่วน {col_value}",
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # ตารางแสดงข้อมูล
    with st.expander("📋 ดูตารางข้อมูลทั้งหมด (Data Table)"):
        st.dataframe(filtered_df, use_container_width=True)