"""Dashboard: สถิติจำนวนนักท่องเที่ยวอุทยานแห่งชาติ (พ.ศ. 2550-2564)
ข้อมูล: data.go.th  https://data.go.th/dataset/gdpublish-stat-tourism
"""
import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="นักท่องเที่ยวอุทยานแห่งชาติ", page_icon="🌲", layout="wide")

API_URL = "https://data.go.th/api/3/action/datastore_search"
RES_2550_2563 = "9c7b36e2-823e-4598-b231-14e126c2046a"  # คอลัมน์: ปี, หน่วยงาน, จำนวนนักท่องเที่ยว
RES_2564 = "7447d47e-49bf-4c29-b583-6158344c855e"        # คอลัมน์: ปี, หน่วยงาน, "2564"
LOCAL_CSV = os.path.join(os.path.dirname(__file__), "data", "parks.csv")


def _fetch(resource_id: str) -> pd.DataFrame:
    """ดึงข้อมูลจาก data.go.th API เป็น DataFrame
    ตั้ง limit=5000 เพื่อให้ได้ครบทุกแถวในครั้งเดียว (ชุด 2550-2563 มี 1,862 แถว)"""
    r = requests.get("https://data.go.th/api/3/action/datastore_search",
                     params={"resource_id": resource_id, "limit": 5000}, timeout=30)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["result"]["records"])
    return df


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns={"ปี": "year", "หน่วยงาน": "park"})
    # ปี 2564 ตั้งชื่อคอลัมน์จำนวนเป็น "2564"
    if "จำนวนนักท่องเที่ยว" not in df.columns:
        num_cols = [c for c in df.columns if str(c).isdigit()]
        df = df.rename(columns={num_cols[0]: "จำนวนนักท่องเที่ยว"})
    df["visitors"] = pd.to_numeric(
        df["จำนวนนักท่องเที่ยว"].astype(str).str.replace(r"[,\s]", "", regex=True),
        errors="coerce")
    df["park"] = df["park"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year", "visitors"])
    df["year"] = df["year"].astype(int)
    return df[["year", "park", "visitors"]]


@st.cache_data(ttl=6 * 3600, show_spinner="กำลังโหลดข้อมูลจาก data.go.th ...")
def load_data() -> pd.DataFrame:
    try:
        raw = [_fetch(RES_2550_2563), _fetch(RES_2564)]
        df = pd.concat([_clean(d) for d in raw], ignore_index=True)
    except Exception:
        if not os.path.exists(LOCAL_CSV):
            raise
        df = _clean(pd.read_csv(LOCAL_CSV))
    return df.groupby(["year", "park"], as_index=False)["visitors"].sum()


try:
    data = load_data()
except Exception as e:  # noqa: BLE001
    st.error(f"โหลดข้อมูลไม่สำเร็จ: {e}")
    st.stop()

# ---------------------------------------------------------------- Sidebar widgets
st.sidebar.header("🔎 ตัวกรองข้อมูล")
y_min, y_max = int(data["year"].min()), int(data["year"].max())
y_from, y_to = st.sidebar.slider("ช่วงปี (พ.ศ.)", y_min, y_max, (y_min, y_max))
all_parks = sorted(data["park"].unique())
sel_parks = st.sidebar.multiselect("อุทยานฯ (ว่าง = ทั้งหมด)", all_parks)
top_n = st.sidebar.slider("จำนวนอุทยานฯ ในกราฟอันดับ (Top N)", 5, 30, 10)

df = data[(data["year"] >= y_from) & (data["year"] <= y_to)]
if sel_parks:
    df = df[df["park"].isin(sel_parks)]

# ---------------------------------------------------------------- Header + KPI
st.title("🌲 สถิตินักท่องเที่ยวอุทยานแห่งชาติ")
st.caption("ข้อมูลจาก [data.go.th](https://data.go.th/dataset/gdpublish-stat-tourism) "
           "· กรมอุทยานแห่งชาติ สัตว์ป่า และพันธุ์พืช · หน่วย: คน")

if df.empty:
    st.warning("ไม่มีข้อมูลตามเงื่อนไขที่เลือก กรุณาปรับตัวกรอง")
    st.stop()

by_year = df.groupby("year", as_index=False)["visitors"].sum()
by_park = df.groupby("park", as_index=False)["visitors"].sum().sort_values("visitors", ascending=False)
peak = by_year.loc[by_year["visitors"].idxmax()]

c1, c2, c3, c4 = st.columns(4)
c1.metric("นักท่องเที่ยวรวม", f"{df['visitors'].sum():,.0f} คน")
c2.metric("จำนวนอุทยานฯ", f"{df['park'].nunique():,}")
c3.metric("ปีที่มากที่สุด", f"พ.ศ. {int(peak['year'])}", f"{peak['visitors']:,.0f} คน", delta_color="off")
c4.metric("อุทยานฯ ที่มากที่สุด", by_park.iloc[0]["park"].replace("อุทยานแห่งชาติ", "อช."),
          f"{by_park.iloc[0]['visitors']:,.0f} คน", delta_color="off")

# ---------------------------------------------------------------- Charts
left, right = st.columns(2)

with left:
    fig1 = px.line(by_year, x="year", y="visitors", markers=True,
                   labels={"year": "ปี (พ.ศ.)", "visitors": "จำนวนนักท่องเที่ยว (คน)"},
                   title="กราฟที่ 1: จำนวนนักท่องเที่ยวรวมรายปี")
    fig1.update_xaxes(dtick=1)
    st.plotly_chart(fig1, width="stretch")

with right:
    top = by_park.head(top_n).sort_values("visitors")
    fig2 = px.bar(top, x="visitors", y="park", orientation="h",
                  labels={"park": "อุทยานแห่งชาติ", "visitors": "จำนวนนักท่องเที่ยวรวม (คน)"},
                  title=f"กราฟที่ 2: {top_n} อุทยานฯ ที่มีนักท่องเที่ยวสูงสุด ({y_from}–{y_to})")
    st.plotly_chart(fig2, width="stretch")

left2, right2 = st.columns(2)

with left2:
    top_names = by_park.head(min(top_n, 8))["park"].tolist()
    trend = df[df["park"].isin(top_names)]
    fig3 = px.line(trend, x="year", y="visitors", color="park", markers=True,
                   labels={"year": "ปี (พ.ศ.)", "visitors": "คน", "park": "อุทยานฯ"},
                   title="กราฟที่ 3: แนวโน้มรายปีของอุทยานฯ อันดับต้น ๆ")
    fig3.update_xaxes(dtick=1)
    st.plotly_chart(fig3, width="stretch")

with right2:
    heat = (df[df["park"].isin(by_park.head(top_n)["park"])]
            .pivot_table(index="park", columns="year", values="visitors", aggfunc="sum"))
    fig4 = px.imshow(heat, aspect="auto", color_continuous_scale="YlGn",
                     labels={"x": "ปี (พ.ศ.)", "y": "อุทยานฯ", "color": "คน"},
                     title="กราฟที่ 4: Heatmap อุทยานฯ × ปี")
    st.plotly_chart(fig4, width="stretch")

st.caption("หมายเหตุ: รวมข้อมูล พ.ศ. 2550–2563 และ พ.ศ. 2564 จากสองชุดไฟล์ในชุดข้อมูลเดียวกัน; "
           "ช่องที่ไม่มีข้อมูลในต้นฉบับถูกตัดออก")

with st.expander("📄 ตารางข้อมูล"):
    show = df.rename(columns={"year": "ปี", "park": "อุทยานแห่งชาติ", "visitors": "จำนวนนักท่องเที่ยว (คน)"})
    st.dataframe(show, width="stretch", hide_index=True)
    st.download_button("ดาวน์โหลด CSV (ตามตัวกรอง)", show.to_csv(index=False).encode("utf-8-sig"),
                       "park_visitors_filtered.csv", "text/csv")
