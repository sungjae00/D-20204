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

st.divider()

# -------------------------------------------------------------------
# 구역 3: 총 관객수 분포 (히스토그램)
# -------------------------------------------------------------------
st.header("3. 총 관객수 분포")

fig_hist = px.histogram(
    df,
    x='total_audi',
    nbins=25,
    labels={'total_audi': '총 관객수', 'count': '영화 수'},
    title="영화별 총 관객수 구간 분포"
)

fig_hist.update_traces(
    hovertemplate="관객수 구간: %{x}<br>영화 수: %{y}편<extra></extra>"
)

st.plotly_chart(fig_hist, use_container_width=True)

# 가장 관객 수가 많은 영화 데이터 추출
top_movie = df.loc[df['total_audi'].idxmax()]
top_movie_name = top_movie['movieNm']
top_movie_audi = top_movie['total_audi']

st.markdown("**💡 이 그래프로 알 수 있는 것**")
st.info(
    f"대부분의 영화가 100만~300만 명대 이하의 상대적으로 낮은 관객수 구간에 밀집되어 있으며, "
    f"일부 대형 흥행작만이 오른쪽에 외딴 구간을 형성하고 있음을 볼 수 있습니다. "
    f"이 중 가장 관객이 많은 영화는 **'{top_movie_name}'**(총 {top_movie_audi:,.0f}명)입니다."
)

st.divider()

# -------------------------------------------------------------------
# 구역 4: 개봉일 스크린수와 총 관객수의 관계 (산점도)
# -------------------------------------------------------------------
st.header("4. 개봉일 스크린수와 총 관객수의 관계")

fig_scatter = px.scatter(
    df,
    x='first_scrn',
    y='total_audi',
    color='genre',
    hover_name='movieNm',
    labels={
        'first_scrn': '개봉일 스크린수',
        'total_audi': '총 관객수',
        'genre': '장르'
    },
    title="개봉일 스크린수 대비 총 관객수 산점도"
)

# 마우스 호버 시 영화명, 스크린수, 관객수 표시
fig_scatter.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>개봉일 스크린수: %{x:,.0f}개<br>총 관객수: %{y:,.0f}명<extra></extra>"
)

st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("**💡 이 그래프로 알 수 있는 것**")
st.info("개봉 첫날 확보한 스크린수가 많을수록 대체로 총 관객수도 증가하는 양의 상관관계를 보이며, 초기 스크린 수가 적음에도 불구하고 높은 총 관객수를 기록한 흥행작 및 장르별 양상을 확인할 수 있습니다.")

st.divider()

# -------------------------------------------------------------------
# 구역 5: 주요 장르별 총 관객수 분포 (박스플롯)
# -------------------------------------------------------------------
st.header("5. 주요 장르별 총 관객수 분포 (10편 이상 장르)")

# 영화가 10편 이상인 장르만 필터링
genre_counts_series = df['genre'].value_counts()
valid_genres = genre_counts_series[genre_counts_series >= 10].index
df_box = df[df['genre'].isin(valid_genres)]

fig_box = px.box(
    df_box,
    x='genre',
    y='total_audi',
    color='genre',
    points='outliers',
    hover_name='movieNm',
    labels={
        'genre': '장르',
        'total_audi': '총 관객수'
    },
    title="10편 이상 제작된 장르별 총 관객수 상자 그림"
)

st.plotly_chart(fig_box, use_container_width=True)

st.markdown("**💡 이 그래프로 알 수 있는 것**")
st.info("영화 편수가 많은 주요 장르별 관객수의 중앙값과 사분위수(범위)를 비교할 수 있으며, 일반적인 범주를 크게 벗어나 독보적인 흥행을 기록한 아웃라이어(이상치) 영화들을 확인할 수 있습니다.")
