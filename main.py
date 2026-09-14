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

  # 전체 데이터를 기준일자 순으로 정렬
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

fig_line = px.line(
    movie_df,
    x="기준일자",
    y="해당일관객수",
    title=f"{selected_movie} - 일별 관객수 변화",
    labels={"기준일자": "날짜", "해당일관객수": "일별 관객수"},
    markers=True,
)
st.plotly_chart(fig_line, use_container_width=True)
st.info("💡 **이 그래프로 알 수 있는 것:** (이곳에 해석 문구를 입력하세요.)")


# --------------------------------------------------
# [구역 2] 선택한 영화의 누적 관객수 영역 차트
# --------------------------------------------------
st.divider()
st.subheader(f"📊 2. [{selected_movie}] 누적 관객수 변화 (영역 차트)")

fig_area = px.area(
    movie_df,
    x="기준일자",
    y="누적관객수",
    title=f"{selected_movie} - 누적 관객수 증가 추이",
    labels={"기준일자": "날짜", "누적관객수": "누적 관객수"},
)
fig_area.update_traces(fillcolor="rgba(31, 119, 180, 0.4)")
st.plotly_chart(fig_area, use_container_width=True)
st.info("💡 **이 그래프로 알 수 있는 것:** (이곳에 해석 문구를 입력하세요.)")


# --------------------------------------------------
# [구역 3] TOP 10 20일 이상 진입 영화 중 누적 관객수 TOP 5 비교
# --------------------------------------------------
st.divider()
st.subheader(
    "🏆 3. 장기 흥행작(TOP 10 20일 이상) 누적 관객수 TOP 5 비교 (다중 선 그래프)"
)

if "순위" in df.columns:
  top10_df = df[df["순위"] <= 10]
else:
  top10_df = df

top10_days = top10_df.groupby("영화명")["기준일자"].nunique()
movies_over_20days = top10_days[top10_days >= 20].index

filtered_audience = movie_audience[
    movie_audience["영화명"].isin(movies_over_20days)
]
top5_movies = filtered_audience.head(5)["영화명"].tolist()
top5_df = df[df["영화명"].isin(top5_movies)]

fig_multi = px.line(
    top5_df,
    x="기준일자",
    y="누적관객수",
    color="영화명",
    title="TOP 10에 20일 이상 상주한 영화 중 누적 관객수 TOP 5 추이 비교",
    labels={"기준일자": "날짜", "누적관객수": "누적 관객수", "영화명": "영화 제목"},
)
st.plotly_chart(fig_multi, use_container_width=True)
st.info("💡 **이 그래프로 알 수 있는 것:** (이곳에 해석 문구를 입력하세요.)")


# --------------------------------------------------
# [구역 4] 전체 TOP 10 영화 일별 관객수 합계 및 7일 이동평균선
# --------------------------------------------------
st.divider()
st.subheader("📉 4. 전체 박스오피스 일별 관객수 합계 및 7일 이동평균선")

daily_summary = (
    top10_df.groupby("기준일자")["해당일관객수"].sum().reset_index()
)
daily_summary = daily_summary.sort_values("기준일자")
daily_summary["7일_이동평균"] = (
    daily_summary["해당일관객수"].rolling(window=7, min_periods=1).mean()
)

fig_ma = go.Figure()
fig_ma.add_trace(
    go.Scatter(
        x=daily_summary["기준일자"],
        y=daily_summary["해당일관객수"],
        mode="lines",
        name="일별 총관객수 (원본)",
        line=dict(color="rgba(180, 180, 180, 0.5)", width=1.5),
    )
)
fig_ma.add_trace(
    go.Scatter(
        x=daily_summary["기준일자"],
        y=daily_summary["7일_이동평균"],
        mode="lines",
        name="7일 이동평균선",
        line=dict(color="#d62728", width=3),
    )
)
fig_ma.update_layout(
    title="일별 TOP 10 총 관객수 및 7일 이동평균 추이",
    xaxis_title="날짜",
    yaxis_title="총 관객수",
    hovermode="x unified",
)
st.plotly_chart(fig_ma, use_container_width=True)
st.info("💡 **이 그래프로 알 수 있는 것:** (이곳에 해석 문구를 입력하세요.)")


# --------------------------------------------------
# [구역 5] 월별 총 관객수 합계 막대그래프
# --------------------------------------------------
st.divider()
st.subheader("📊 5. 월별 전체 관객수 합계 (막대그래프)")

daily_summary["연월"] = daily_summary["기준일자"].dt.strftime("%Y-%m")
monthly_summary = (
    daily_summary.groupby("연월")["해당일관객수"].sum().reset_index()
)

fig_bar = px.bar(
    monthly_summary,
    x="연월",
    y="해당일관객수",
    title="월별 박스오피스 총 관객수 비교",
    labels={"연월": "월(Year-Month)", "해당일관객수": "월간 총 관객수"},
    text_auto=".2s",
)
fig_bar.update_traces(marker_color="#1f77b4", textposition="outside")
fig_bar.update_layout(xaxis_type="category")
st.plotly_chart(fig_bar, use_container_width=True)
st.info("💡 **이 그래프로 알 수 있는 것:** (이곳에 해석 문구를 입력하세요.)")


# --------------------------------------------------
# [구역 6] 캘린더 히트맵 (신규 추가)
# --------------------------------------------------
st.divider()
st.subheader("📅 6. 월(주차별) × 요일별 일관객 합계 (캘린더 히트맵)")

# 1. 히트맵 전용 데이터 프레임 생성
heatmap_df = daily_summary.copy()

# 요일 지정 (월요일 ~ 일요일 순서 고정)
day_orders = ["월", "화", "수", "목", "금", "토", "일"]
day_map = {0: "월", 1: "화", 2: "수", 3: "목", 4: "금", 5: "토", 6: "일"}
heatmap_df["요일"] = heatmap_df["기준일자"].dt.dayofweek.map(day_map)

# Y축 그룹화를 위한 연월-주차 컬럼 및 마우스 오버용 yyyy-mm-dd 날짜 컬럼 생성
heatmap_df["주차"] = heatmap_df["기준일자"].dt.strftime("%Y-%m (%W주차)")
heatmap_df["날짜str"] = heatmap_df["기준일자"].dt.strftime("%Y-%m-%d")

# 2. 피벗 테이블로 변환 (행: 주차, 열: 요일)
pivot_val = heatmap_df.pivot(
    index="주차", columns="요일", values="해당일관객수"
)
pivot_date = heatmap_df.pivot(
    index="주차", columns="요일", values="날짜str"
)

# 요일 컬럼 순서를 월요일~일요일로 정렬
pivot_val = pivot_val.reindex(columns=day_orders)
pivot_date = pivot_date.reindex(columns=day_orders)

# 3. Plotly 히트맵 생성
fig_heatmap = go.Figure(
    data=go.Heatmap(
        z=pivot_val.values,
        x=day_orders,
        y=pivot_val.index,
        text=pivot_date.values,
        hovertemplate="<b>날짜</b>: %{text}<br><b>요일</b>: %{x}요일<br><b>총 관객수</b>: %{z:,.0f}명<extra></extra>",
        colorscale="Blues",  # 색이 진할수록 관객 수가 많음
    )
)

fig_heatmap.update_layout(
    title="주차별 × 요일별 일일 관객수 캘린더 히트맵",
    xaxis_title="요일 (월 ~ 일)",
    yaxis_title="월 (주차)",
    yaxis=dict(autorange="reversed"),  # 주차를 상단부터 시간순 정렬
)

st.plotly_chart(fig_heatmap, use_container_width=True)
st.info("💡 **이 그래프로 알 수 있는 것:** (이곳에 해석 문구를 입력하세요.)")
