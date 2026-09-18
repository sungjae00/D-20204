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
    
    # genre 열 전처리: 첫 번째 장르만 추출 및 결측치/빈값 처리
    df['genre'] = df['genre'].fillna('기타').astype(str).str.split('|').str[0]
    df['genre'] = df['genre'].replace('', '기타')
    
    # nation 열 결측치 및 빈값 처리 (선버스트 오류 방지)
    df['nation'] = df['nation'].fillna('기타').astype(str).replace('', '기타')
    
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

st.divider()

# -------------------------------------------------------------------
# 구역 6: 스크린수, 첫 주 관객수, 총 관객수의 관계 (버블 차트)
# -------------------------------------------------------------------
st.header("6. 스크린수·첫 주 관객수·총 관객수의 관계 (버블 차트)")

fig_bubble = px.scatter(
    df,
    x='first_scrn',
    y='total_audi',
    size='first_week_audi',
    color='genre',
    hover_name='movieNm',
    hover_data={
        'first_scrn': ':,',
        'total_audi': ':,',
        'first_week_audi': ':,'
    },
    labels={
        'first_scrn': '개봉일 스크린수',
        'total_audi': '총 관객수',
        'first_week_audi': '개봉 첫 주 관객수',
        'genre': '장르'
    },
    title="개봉일 스크린수 대비 총 관객수 (버블 크기: 개봉 첫 주 관객수)"
)

st.plotly_chart(fig_bubble, use_container_width=True)

st.markdown("**💡 이 그래프로 알 수 있는 것**")
st.info("스크린수와 최종 관객수의 상관관계뿐만 아니라, 버블의 크기를 통해 개봉 첫 주 초반 집객력(첫 주 관객수)이 최종 흥행 규모에 어떠한 영향을 미치는지 복합적으로 파악할 수 있습니다.")

st.divider()

# -------------------------------------------------------------------
# 구역 7: 제작 국가 및 장르별 영화 편수 (선버스트 차트)
# -------------------------------------------------------------------
st.header("7. 제작 국가 및 장르별 영화 편수 분포")

# 제작 국가와 장르별 영화 편수 미리 집계
df_sunburst = df.groupby(['nation', 'genre']).size().reset_index(name='count')

fig_sunburst = px.sunburst(
    df_sunburst,
    path=['nation', 'genre'],
    values='count',
    title="제작 국가 및 장르별 영화 편수 계층 구조"
)

# 마우스 호버 시 영역명과 편수 표시
fig_sunburst.update_traces(
    hovertemplate="<b>%{label}</b><br>영화 편수: %{value}편<extra></extra>"
)

st.plotly_chart(fig_sunburst, use_container_width=True)

st.markdown("**💡 이 그래프로 알 수 있는 것**")
st.info("주요 제작 국가별로 어떤 장르의 영화가 주로 제작·개봉되는지 국가와 장르 간의 계층적 비중과 세부 구성비를 한눈에 비교할 수 있습니다.")

st.divider()

# -------------------------------------------------------------------
# 구역 8: 10위권에 오래 머문 영화는 총 관객도 많은가 (산점도)
# -------------------------------------------------------------------
st.header("8. 10위권에 오래 머문 영화는 총 관객도 많은가")

fig_scatter_stay = px.scatter(
    df,
    x='days_in_top10',
    y='total_audi',
    color='genre',
    hover_name='movieNm',
    labels={
        'days_in_top10': '10위권 머문 날수',
        'total_audi': '총 관객수',
        'genre': '장르'
    },
    title="10위권에 오래 머문 영화는 총 관객도 많은가"
)

# 마우스 호버 시 영화명, 머문 날수, 관객수 표시
fig_scatter_stay.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>10위권 머문 날수: %{x}일<br>총 관객수: %{y:,.0f}명<extra></extra>"
)

st.plotly_chart(fig_scatter_stay, use_container_width=True)

st.markdown("**💡 이 그래프로 알 수 있는 것**")
st.info("박스오피스 10위권 내에 오래 상주한 영화일수록 대체로 총 관객수도 높게 형성되는 양의 상관관계를 보이며, 관객 집객력의 장기 유지(롱런)가 총 관객수에 미치는 영향을 알 수 있습니다.")
