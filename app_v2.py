import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go

# ── 頁面設定 ──
st.set_page_config(
    page_title="AI 機車騎乘風險即時評估系統",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 自訂樣式 ──
st.markdown("""
<style>
  .main-title {
    font-size: 28px; font-weight: 700;
    color: #1A365D; margin-bottom: 4px;
  }
  .sub-title {
    font-size: 14px; color: #718096; margin-bottom: 20px;
  }
  .kpi-card {
    background: #EBF8FF; border-radius: 10px;
    padding: 16px; text-align: center;
    border-left: 4px solid #2B6CB0;
  }
  .kpi-value { font-size: 26px; font-weight: 700; color: #1A365D; }
  .kpi-label { font-size: 12px; color: #718096; }
  .risk-high   { color: #C53030; font-weight: 700; }
  .risk-mid    { color: #D69E2E; font-weight: 700; }
  .risk-low    { color: #276749; font-weight: 700; }
  .info-box {
    background: #EBF8FF; border-left: 4px solid #2B6CB0;
    border-radius: 0 8px 8px 0; padding: 12px 16px;
    font-size: 13px; color: #2C5282; margin-top: 10px;
  }
</style>
""", unsafe_allow_html=True)

# ── 讀取資料 ──
@st.cache_data
def load_data():
    df = pd.read_csv('taipei_accident_with_poi.csv', encoding='utf-8-sig')
    road = pd.read_csv('road_accident_summary.csv', encoding='utf-8-sig')
    return df, road

df, road_df = load_data()

# 時段順序
TIME_ORDER = ['深夜（0-6點）','早峰（6-9點）','上午（9-12點）',
              '午間（12-14點）','下午（14-18點）','晚峰（18-21點）','夜間（21-24點）']

# ── 側邊欄 ──
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Soochow_University_Taiwan_logo.svg/240px-Soochow_University_Taiwan_logo.svg.png", width=80)
    st.markdown("### 🏍️ AI 機車風險系統")
    st.markdown("**東吳大學巨量資料管理學院**")
    st.markdown("---")
    st.markdown("#### 🔍 篩選條件")

    selected_district = st.multiselect(
        "行政區",
        options=sorted(df['行政區_擷取'].dropna().unique().tolist()),
        default=[]
    )
    selected_time = st.multiselect(
        "時段",
        options=TIME_ORDER,
        default=[]
    )
    selected_poi = st.multiselect(
        "周邊主要商家類型",
        options=['餐飲','辦公大樓','便利商店','購物商場'],
        default=[]
    )
    st.markdown("---")
    st.markdown("#### 📋 資料說明")
    st.markdown("""
    - **事故資料**：台北市114年死傷交通事故明細
    - **商家資料**：OpenStreetMap（osmnx）
    - **分析筆數**：22,760筆
    - **分析日期**：2025年10月
    """)

# ── 套用篩選 ──
df_filtered = df.copy()
if selected_district:
    df_filtered = df_filtered[df_filtered['行政區_擷取'].isin(selected_district)]
if selected_time:
    df_filtered = df_filtered[df_filtered['時段'].isin(selected_time)]
if selected_poi:
    df_filtered = df_filtered[df_filtered['主要商家類型'].isin(selected_poi)]

# ── 主標題 ──
st.markdown('<div class="main-title">🏍️ AI 機車騎乘風險即時評估系統</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">台北市114年機車事故分析儀表板 × 商家環境關聯分析</div>', unsafe_allow_html=True)

# ── KPI 卡片 ──
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value">{len(df_filtered):,}</div>
        <div class="kpi-label">篩選後事故數</div>
    </div>""", unsafe_allow_html=True)
with k2:
    top_road = road_df.iloc[0]['路段'] if len(road_df) > 0 else '-'
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value" style="font-size:18px;">{top_road}</div>
        <div class="kpi-label">最高風險路段</div>
    </div>""", unsafe_allow_html=True)
with k3:
    if len(df_filtered) > 0:
        top_time = df_filtered['時段'].value_counts().index[0]
    else:
        top_time = '-'
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value" style="font-size:16px;">{top_time}</div>
        <div class="kpi-label">最高風險時段</div>
    </div>""", unsafe_allow_html=True)
with k4:
    if len(df_filtered) > 0:
        top_dist = df_filtered['行政區_擷取'].value_counts().index[0]
    else:
        top_dist = '-'
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value" style="font-size:18px;">{top_dist}</div>
        <div class="kpi-label">事故最多行政區</div>
    </div>""", unsafe_allow_html=True)
with k5:
    if len(df_filtered) > 0:
        intersection_pct = int((df_filtered['是否路口'] == '路口').mean() * 100)
    else:
        intersection_pct = 0
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-value">{intersection_pct}%</div>
        <div class="kpi-label">路口事故佔比</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── 分頁 ──
tab1, tab2, tab3 = st.tabs(["🗺️ 事故熱點地圖", "📊 商家與事故關聯", "🛣️ 高風險路段"])

# ════════════════════════════════
# Tab 1：事故熱點地圖
# ════════════════════════════════
with tab1:
    col_map, col_info = st.columns([2, 1])

    with col_map:
        st.markdown("##### 事故分布地圖（最多顯示 2,000 筆）")
        sample = df_filtered.dropna(subset=['座標-X','座標-Y'])
        sample = sample.sample(min(2000, len(sample)), random_state=42) if len(sample) > 2000 else sample

        m = folium.Map(
            location=[25.05, 121.535],
            zoom_start=13,
            tiles="OpenStreetMap"
        )

        for _, row in sample.iterrows():
            color = '#E53E3E' if row['死亡人數'] > 0 else \
                    '#ED8936' if row['主要商家類型'] == '餐飲' else \
                    '#3182CE' if row['主要商家類型'] == '辦公大樓' else '#805AD5'
            folium.CircleMarker(
                location=[row['座標-Y'], row['座標-X']],
                radius=6 if row['死亡人數'] > 0 else 4,
                color='white',
                weight=1,
                fill=True,
                fill_color=color,
                fill_opacity=0.75,
                popup=folium.Popup(f"""
                    <b>{row.get('路段','未知路段')}</b><br>
                    行政區：{row['行政區_擷取']}<br>
                    時段：{row['時段']}<br>
                    周邊主要：{row['主要商家類型']}<br>
                    死亡：{int(row['死亡人數'])} 受傷：{int(row['受傷人數'])}
                """, max_width=200)
            ).add_to(m)

        st_folium(m, width=700, height=480)

    with col_info:
        st.markdown("##### 圖例說明")
        st.markdown("""
        🔴 **死亡事故**  
        🟠 **餐飲區事故**  
        🔵 **辦公區事故**  
        🟣 **其他事故**
        """)
        st.markdown("---")
        st.markdown("##### 篩選後統計")
        if len(df_filtered) > 0:
            dist_count = df_filtered['行政區_擷取'].value_counts().head(5).reset_index()
            dist_count.columns = ['行政區','事故數']
            st.dataframe(dist_count, hide_index=True, use_container_width=True)
        st.markdown("""
        <div class="info-box">
        路口事故佔整體事故約67%，顯示路口是最需要注意的危險地點。
        </div>
        """, unsafe_allow_html=True)

# ════════════════════════════════
# Tab 2：商家與事故關聯
# ════════════════════════════════
with tab2:
    col_a, col_b = st.columns(2)

    with col_a:
        # 時段圖
        time_data = df_filtered.groupby('時段').size().reset_index(name='事故數')
        time_data['排序'] = time_data['時段'].map({t:i for i,t in enumerate(TIME_ORDER)})
        time_data = time_data.sort_values('排序')
        max_n = time_data['事故數'].max() if len(time_data) > 0 else 1
        time_data['顏色'] = time_data['事故數'].apply(lambda x: '#E53E3E' if x == max_n else '#2B6CB0')

        fig_time = px.bar(
            time_data, x='時段', y='事故數',
            title='各時段事故數量',
            color='顏色', color_discrete_map='identity',
        )
        fig_time.update_layout(showlegend=False, height=300,
            plot_bgcolor='white', paper_bgcolor='white',
            title_font_size=14, margin=dict(t=40,b=20,l=20,r=20))
        fig_time.update_xaxes(tickangle=-30)
        st.plotly_chart(fig_time, use_container_width=True)

        # 商家類型圓餅
        poi_data = df_filtered[df_filtered['主要商家類型'].isin(['餐飲','辦公大樓'])]['主要商家類型'].value_counts().reset_index()
        poi_data.columns = ['類型','事故數']
        fig_pie = px.pie(
            poi_data, names='類型', values='事故數',
            title='餐飲區 vs 辦公區事故占比',
            color_discrete_sequence=['#ED8936','#2B6CB0'],
        )
        fig_pie.update_layout(height=300, title_font_size=14,
            margin=dict(t=40,b=20,l=20,r=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        # 各區圖
        dist_data = df_filtered[df_filtered['行政區_擷取'] != '未知'].groupby('行政區_擷取').size().reset_index(name='事故數').sort_values('事故數')
        fig_dist = px.bar(
            dist_data, x='事故數', y='行政區_擷取',
            orientation='h', title='各行政區事故數量',
            color_discrete_sequence=['#2B6CB0'],
        )
        fig_dist.update_layout(height=300, showlegend=False,
            plot_bgcolor='white', paper_bgcolor='white',
            title_font_size=14, margin=dict(t=40,b=20,l=20,r=20))
        st.plotly_chart(fig_dist, use_container_width=True)

        # 交叉折線圖
        cross = df_filtered[df_filtered['主要商家類型'].isin(['餐飲','辦公大樓'])].groupby(['主要商家類型','時段']).size().reset_index(name='事故數')
        cross['排序'] = cross['時段'].map({t:i for i,t in enumerate(TIME_ORDER)})
        cross = cross.sort_values('排序')
        fig_cross = px.line(
            cross, x='時段', y='事故數', color='主要商家類型',
            title='餐飲 vs 辦公區 各時段事故趨勢',
            color_discrete_map={'餐飲':'#ED8936','辦公大樓':'#2B6CB0'},
            markers=True,
        )
        fig_cross.update_layout(height=300, title_font_size=14,
            plot_bgcolor='white', paper_bgcolor='white',
            margin=dict(t=40,b=20,l=20,r=20))
        fig_cross.update_xaxes(tickangle=-30)
        st.plotly_chart(fig_cross, use_container_width=True)

    st.markdown("""
    <div class="info-box">
    辦公大樓密集區事故數量遠高於餐飲區，推測與通勤流量有關。
    餐飲密集區在晚峰（18-21點）事故比例較高，與用餐後出行模式相符。
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════
# Tab 3：高風險路段
# ════════════════════════════════
with tab3:
    col_t, col_c = st.columns([3, 2])

    with col_t:
        st.markdown("##### 高風險路段排名（前15名）")
        top15 = road_df.head(15)[['路段','事故總數','受傷總數','死亡總數','主要商家類型']].copy()
        top15['死亡總數'] = top15['死亡總數'].fillna(0).astype(int)
        top15['受傷總數'] = top15['受傷總數'].fillna(0).astype(int)
        top15.insert(0, '排名', range(1, len(top15)+1))

        def highlight_top3(row):
            if row['排名'] <= 3:
                return ['background-color: #FFF5F5'] * len(row)
            return [''] * len(row)

        st.dataframe(
            top15.style.apply(highlight_top3, axis=1),
            hide_index=True,
            use_container_width=True,
            height=480
        )

    with col_c:
        # 路段事故長條圖
        fig_road = px.bar(
            top15.sort_values('事故總數'),
            x='事故總數', y='路段',
            orientation='h',
            title='前15高風險路段事故數',
            color='主要商家類型',
            color_discrete_map={'餐飲':'#ED8936','辦公大樓':'#2B6CB0'},
        )
        fig_road.update_layout(height=480, title_font_size=14,
            plot_bgcolor='white', paper_bgcolor='white',
            margin=dict(t=40,b=20,l=20,r=20))
        st.plotly_chart(fig_road, use_container_width=True)

    st.markdown("""
    <div class="info-box">
    前15名高風險路段中，辦公大樓密集區佔多數，顯示辦公商圈的通勤流量是主要風險因子。
    忠孝東路4段為餐飲密集區中事故最多的路段（253件），值得特別注意。
    </div>
    """, unsafe_allow_html=True)
