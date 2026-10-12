# Dashboard สถิตินักท่องเที่ยวอุทยานแห่งชาติ

แบบฝึกหัด Streamlit Data Visualization & Deployment
ข้อมูล: [data.go.th – สถิตินักท่องเที่ยวอุทยานแห่งชาติ](https://data.go.th/dataset/gdpublish-stat-tourism) (พ.ศ. 2550–2564)

- กราฟ 4 กราฟ (Plotly): รวมรายปี, Top N อุทยานฯ, แนวโน้มรายอุทยานฯ, Heatmap อุทยานฯ × ปี
- Interactive widgets: slider ช่วงปี, multiselect อุทยานฯ, slider Top N
- โหลดข้อมูลสดจาก data.go.th API ด้วย Pandas

## รันบนเครื่อง
```bash
pip install -r requirements.txt
streamlit run app.py
```
