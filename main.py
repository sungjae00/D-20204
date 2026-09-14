import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# 페이지 기본 설정 (넓은 레이아웃 적용)
st.set_page_config(page_title="영화 박스오피스 데이터 분석", layout="wide")


# [1. 데이터 불러오기]
# @st.cache_data 데코레이터를 사용하여 매번 불러오지 않고 저장된 데이터를 재사용합니다.
@st.cache_data
def load_data():
  url = "https://raw.githubusercontent.com/keep-growing-park/data-science/refs/heads/main/dataset/kobis_1year_boxoffice.csv"
  df = pd.read_csv(url)

  # [2. 날짜 전처리]
  # 결측치가 있는 행 제거
  df = df.dropna()

  # "기준일자" 컬럼을 datetime 형식으로 변환
  df["기준일자"] = pd.to_datetime(df["기준일자"])

  # 전체 데이터를 기준일자 순으로 정렬 (이동평균 계산을 위해 날짜 순 정렬 필수)
  df = df.sort_values(by="기준일자")

  return df


# 데이터 로드
df = load_data()

# 메인 타이틀
st.title("🎬 박스오피스 영화 데이터 분석")

# [3. 영화 선택 기능 준비]
# 영화별 최고 누적관객수를 구해 내림차순 정렬 후 목록 추출
movie_audience = (
    df.groupby("영화명")["누적관객수"]
    .max()
    .reset_index()
    .sort_values(by="누적관객수", ascending=False)
)
sorted_movies = movie_audience["영화명"].tolist()

# 셀렉트박스로 영화 선택
selected_movie = st.selectbox("분석할 영화를 선택하세요:", sorted_movies)

# 사용자가 선택한 영화의 데이터만 추출
movie_df = df[df["영화명"] == selected_movie]


# --------------------------------------------------
# [구역 1] 선택한 영화의 일별 관객수 선 그래프
# --------------------------------------------------
st.divider()
st.subheader(f"📈 1. [{selected_movie}] 일별 관객수 추이 (선 그래프)")

# Plotly 선 그래프
fig_line = px.line(
    movie_df,
    x="기준일자",
    y="해당일관객수",
    title=f"{selected_movie} - 일별 관객수 변화",
    labels={"기준일자": "날짜", "해당일관객수": "일별 관객수"},
    markers=True,
)

# 그래프 출력
st.plotly_chart(fig_line, use_container_width=True)

# 그래프 설명 문구 자리
st.info("💡 **이 그래프로 알 수 있는 것:** (이곳에 해석 문구를 입력하세요.)")


# --------------------------------------------------
# [구역 2] 선택한 영화의 누적 관객수 영역 차트
# --------------------------------------------------
st.divider()
st.subheader(f"📊 2. [{selected_movie}] 누적 관객수 변화 (영역 차트)")

# Plotly 영역 차트 (px.area 사용)
fig_area = px.area(
    movie_df,
    x="기준일자",
    y="누적관객수",
    title=f"{selected_movie} - 누적 관객수 증가 추이",
    labels={"기준일자": "날짜", "누적관객수": "누적 관객수"},
)

# 영역 차트 색상 및 투명도 살짝 조정
fig_area.update_traces(fillcolor="rgba(31, 119, 180, 0.4)")

# 그래프 출력
st.plotly_chart(fig_area, use_container_width=True)

# 그래프 설명 문구 자리
st.info("💡 **이 그래프로 알 수 있는 것:** (이곳에 해석 문구를 입력하세요.)")


# --------------------------------------------------
# [구역 3] TOP 10 20일 이상 진입 영화 중 누적 관객수 TOP 5 비교
# --------------------------------------------------
st.divider()
st.subheader(
    "🏆 3. 장기 흥행작(TOP 10 20일 이상) 누적 관객수 TOP 5 비교 (다중 선 그래프)"
)

# 1. TOP 10에 진입한 데이터만 필터링 ('순위' 컬럼이 있으면 10위 이하, 없으면 전체 사용)
if "순위" in df.columns:
  top10_df = df[df["순위"] <= 10]
else:
  top10_df = df

# 2. 영화별 TOP 10 진입 일수 계산
top10_days = top10_df.groupby("영화명")["기준일자"].nunique()

# 3. TOP 10에 20일 이상 등장한 영화만 선택
movies_over_20days = top10_days[top10_days >= 20].index

# 4. 조건을 만족하는 영화 중 누적 관객수 상위 5개 영화 선택
filtered_audience = movie_audience[
    movie_audience["영화명"].isin(movies_over_20days)
]
top5_movies = filtered_audience.head(5)["영화명"].tolist()

# 5. 최종 선택된 5개 영화의 데이터 추출
top5_df = df[df["영화명"].isin(top5_movies)]

# 6. Plotly 다중 선 그래프 생성
fig_multi = px.line(
    top5_df,
    x="기준일자",
    y="누적관객수",
    color="영화명",
    title="TOP 10에 20일 이상 상주한 영화 중 누적 관객수 TOP 5 추이 비교",
    labels={"기준일자": "날짜", "누적관객수": "누적 관객수", "영화명": "영화 제목"},
)

# 그래프 출력
st.plotly_chart(fig_multi, use_container_width=True)

# 그래프 설명 문구 자리
st.info("💡 **이 그래프로 알 수 있는 것:** (이곳에 해석 문구를 입력하세요.)")


# --------------------------------------------------
# [구역 4] 전체 TOP 10 영화 일별 관객수 합계 및 7일 이동평균선 (신규 추가)
# --------------------------------------------------
st.divider()
st.subheader("📉 4. 전체 박스오피스 일별 관객수 합계 및 7일 이동평균선")

# 1. 기준일자별 TOP 10 영화의 해당일관객수 총합 구하기
daily_summary = (
    top10_df.groupby("기준일자")["해당일관객수"].sum().reset_index()
)
daily_summary = daily_summary.sort_values("기준일자")

# 2. 7일 이동평균 계산 (rolling window=7)
daily_summary["7일_이동평균"] = (
    daily_summary["해당일관객수"].rolling(window=7, min_periods=1).mean()
)

# 3. Plotly Graph Objects를 활용해 두 선을 커스텀 스타일로 겹쳐서 작성
fig_ma = go.Figure()

# 원본 일별 관객수 합계 (연한 색상/얇은 선)
fig_ma.add_trace(
    go.Scatter(
        x=daily_summary["기준일자"],
        y=daily_summary["해당일관객수"],
        mode="lines",
        name="일별 총관객수 (원본)",
        line=dict(color="rgba(180, 180, 180, 0.5)", width=1.5),
    )
)

# 7일 이동평균 (진한 색상/두꺼운 선)
fig_ma.add_trace(
    go.Scatter(
        x=daily_summary["기준일자"],
        y=daily_summary["7일_이동평균"],
        mode="lines",
        name="7일 이동평균선",
        line=dict(color="#d62728", width=3),
    )
)

# 그래프 레이아웃 설정
fig_ma.update_layout(
    title="일별 TOP 10 총 관객수 및 7일 이동평균 추이",
    xaxis_title="날짜",
    yaxis_title="총 관객수",
    hovermode="x unified",
)

# 그래프 출력
st.plotly_chart(fig_ma, use_container_width=True)

# 그래프 설명 문구 자리
st.info("💡 **이 그래프로 알 수 있는 것:** (이곳에 해석 문구를 입력하세요.)")
