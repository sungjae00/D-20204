import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 기본 설정
st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    layout="wide"
)

st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")

# 데이터 불러오기 및 전처리
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"
    df = pd.read_csv(url)
    
    # genre 열 전처리: Pandas 문자열 전용 메서드를 사용해 첫 번째 장르만 추출 (TypeError 방지)
    df['genre'] = df['genre'].fillna('').astype(str).str.split('|').str[0]
    return df

df = load_data()

# -------------------------------------------------------------------
# 구역 1: 장르별 영화 편수 (도넛 그래프)
# -------------------------------------------------------------------
st.header("1. 장르별 영화 편수 분포")

genre_counts = df['genre'].value_counts().reset_index()
genre_counts.columns = ['장르', '편수']

fig_donut = px.pie(
    genre_counts,
    names='장르',
    values='편수',
    hole=0.4,
    title="장르별 영화 편수 비율"
)

# 마우스 호버 시 편수와 비율 표시
fig_donut.update_traces(
    textinfo='percent+label',
    hovertemplate="<b>%{label}</b><br>편수: %{value}편<br>비율: %{percent}<extra></extra>"
)

st.plotly_chart(fig_donut, use_container_width=True)

st.markdown("**💡 이 그래프로 알 수 있는 것**")
st.info("박스오피스 상위권 영화 중 어떤 장르가 가장 큰 비중을 차지하는지 장르별 편수 분포 점유율을 한눈에 파악할 수 있습니다.")

st.divider()

# -------------------------------------------------------------------
# 구역 2: 장르 및 영화별 총 관객수 (트리맵)
# -------------------------------------------------------------------
st.header("2. 장르 및 영화별 총 관객수 분포")

# 트리맵 생성: 계층구조(장르 -> 영화명), 칸 크기(총 관객수)
fig_treemap = px.treemap(
    df,
    path=['genre', 'movieNm'],
    values='total_audi',
    color='genre',
    title="장르 내 영화별 총 관객수 비중"
)

# 마우스 호버 시 영화명과 총 관객수 표시
fig_treemap.update_traces(
    hovertemplate="<b>%{label}</b><br>총 관객수: %{value:,.0f}명<extra></extra>"
)

st.plotly_chart(fig_treemap, use_container_width=True)

st.markdown("**💡 이 그래프로 알 수 있는 것**")
st.info("장르 전체의 관객 규모와 더불어, 특정 장르 안에서 어떤 영화가 가장 많은 관객을 동원하며 흥행을 이끌었는지 직관적으로 알 수 있습니다.")
