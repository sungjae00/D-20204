import pandas as pd
import plotly.express as px
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

# [3. 영화 선택 기능]
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

# [5. 기타 - 구역 나누기]
st.divider()
st.subheader(f"📈 [{selected_movie}] 일별 관객수 추이")

# [4. 선그래프 그리기]
# Plotly를 이용해 기준일자별 해당일관객수 선 그래프 작성
fig = px.line(
    movie_df,
    x="기준일자",
    y="해당일관객수",
    title=f"{selected_movie} - 일별 관객수 변화 그래프",
    labels={"기준일자": "날짜", "해당일관객수": "일별 관객수"},
    markers=True,
)

# Plotly 그래프 출력
st.plotly_chart(fig, use_container_width=True)

# [5. 기타 - 설명 문구 자리]
st.info("💡 **이 그래프로 알 수 있는 것:** (이곳에 해석 문구를 입력하세요.)")

# 추후 다른 그래프를 추가할 구역 예시
st.divider()
st.subheader("📌 추가 분석 구역")
st.caption("새로운 그래프나 데이터 요약표가 들어갈 위치입니다.")
