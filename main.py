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
    
    # genre 열 전처리: '|' 구분자로 나눈 후 첫 번째 장르만 추출
    df['genre'] = df['genre'].astype(str).apply(lambda x: x.split('|')[0] if '|' in x else x)
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

# 마우스 호버 시 편수와 비율이 보이도록 설정
fig_donut.update_traces(
    textinfo='percent+label',
    hovertemplate="<b>%{label}</b><br>편수: %{value}편<br>비율: %{percent}"
)

st.plotly_chart(fig_donut, use_container_width=True)

st.markdown("**💡 이 그래프로 알 수 있는 것**")
st.info("박스오피스 상위권 영화 중 어떤 장르가 가장 큰 비중을 차지하는지 장르별 분포 점유율을 한눈에 파악할 수 있습니다.")

st.divider()

# -------------------------------------------------------------------
# 구역 2: 개봉일 스크린수와 총 관객수의 관계 (산점도)
# -------------------------------------------------------------------
st.header("2. 개봉일 스크린수와 총 관객 수의 관계")

fig_scatter = px.scatter(
    df,
    x='first_scrn',
    y='total_audi',
    color='genre',
    hover_name='movieNm',
    labels={'first_scrn': '개봉일 스크린수', 'total_audi': '총 관객수', 'genre': '장르'},
    title="개봉일 스크린수 대비 총 관객수 분포"
)

st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("**💡 이 그래프로 알 수 있는 것**")
st.info("초기 스크린 확보 수가 최종 흥행(총 관객수)에 미치는 상관관계 및 장르별 흥행 양상을 확인할 수 있습니다.")

st.divider()

# -------------------------------------------------------------------
# 구역 3: 10위권 머문 날수 분포 (히스토그램)
# -------------------------------------------------------------------
st.header("3. 10위권 머문 날수 분포")

fig_hist = px.histogram(
    df,
    x='days_in_top10',
    nbins=20,
    labels={'days_in_top10': '10위권 머문 날수', 'count': '영화 수'},
    title="TOP 10 생존 기간 분포"
)

st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("**💡 이 그래프로 알 수 있는 것**")
st.info("대부분의 영화가 박스오피스 TOP 10 순위권 내에 며칠 동안 머무르는지 전체적인 롱런 여부 및 유지 기간 분포를 알 수 있습니다.")
