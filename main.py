import datetime
import pandas as pd
import pytz
import requests
import streamlit as st

# ==========================================
# 1. 페이지 기본 설정 및 날짜 선택기
# ==========================================
st.set_page_config(page_title="일별 박스오피스 조회", page_icon="🎬", layout="wide")

# 한국 시간(KST) 기준으로 '어제' 날짜 계산 (집계 가능한 가장 최근 날짜)
kst = pytz.timezone("Asia/Seoul")
today_kst = datetime.datetime.now(kst).date()
yesterday = today_kst - datetime.timedelta(days=1)

st.title("🎬 일별 박스오피스")

# 달력(st.date_input)으로 날짜 선택 - 가장 늦은 날짜는 어제(yesterday)로 제한
selected_date = st.date_input(
    "조회할 날짜를 선택하세요",
    value=yesterday,
    max_value=yesterday,
    help="오늘 날짜는 아직 집계 전이므로 어제 날짜까지만 선택하실 수 있습니다.",
)

# API 요청용(YYYYMMDD) 및 화면 표시용 날짜 문자열 변환
target_date_api = selected_date.strftime("%Y%m%d")
target_date_display = selected_date.strftime("%Y년 %m월 %d일")

st.markdown(f"### 📅 {target_date_display} 기준")


# ==========================================
# 2. KOBIS API 데이터 호출 함수 (캐싱 적용)
# ==========================================
# 선택한 날짜별로 결과를 1시간 동안 기억(캐싱)하여 불필요한 API 재호출 방지
@st.cache_data(ttl=3600)
def get_daily_box_office(api_key, target_dt):
    url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {"key": api_key, "targetDt": target_dt}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"network_error": str(e)}


# ==========================================
# 3. 비밀 금고(Secrets) 키 검증 및 데이터 로드
# ==========================================
if "KOBIS_KEY" not in st.secrets or not st.secrets["KOBIS_KEY"]:
    st.error("🔑 인증키(KOBIS_KEY)를 찾을 수 없습니다.")
    st.info(
        """
    **확인해 주세요:**
    1. Streamlit Cloud의 앱 설정에서 **Secrets** 메뉴를 열어주세요.
    2. `KOBIS_KEY = "발급받은_키_문자열"` 형태로 정확히 등록되어 있는지 확인해 주세요.
    """
    )
    st.stop()

api_key = st.secrets["KOBIS_KEY"]
data = get_daily_box_office(api_key, target_date_api)


# ==========================================
# 4. 에러 및 예외 처리
# ==========================================
# 4-1. 네트워크 오류
if "network_error" in data:
    st.error("🌐 네트워크 연결에 실패했습니다.")
    st.info("API 서버 응답이 지연되거나 인터넷 연결에 문제가 있을 수 있습니다.")
    st.stop()

# 4-2. API 오류 (faultInfo)
if "faultInfo" in data:
    st.error("⚠️ API 오류가 발생했습니다.")
    fault = data["faultInfo"]
    st.warning(
        f"""
    **오류 원인:** {fault.get('message', '알 수 없는 오류')} (코드: {fault.get('errorCode', 'N/A')})
    
    **확인해 주세요:**
    1. Secrets에 등록한 `KOBIS_KEY`가 올바른지 확인해 주세요.
    2. KOBIS 개발자 센터에서 키 상태 및 일일 요청한도를 확인해 주세요.
    """
    )
    st.stop()

# 4-3. 영화 목록이 비어 있는 경우
box_office_result = data.get("boxOfficeResult", {})
daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.info("💡 그날은 아직 집계 전입니다.")
    st.stop()


# ==========================================
# 5. 데이터 처리 (숫자 변환, 화살표/트로피 추가)
# ==========================================
df = pd.DataFrame(daily_list)

# 문자열 숫자를 정수형(int)으로 정제
numeric_columns = ["rank", "rankInten", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

# 5-1. 순위 증감(rankInten)에 따른 화살표 기호 붙이기
def format_rank_change(val):
    if val > 0:
        return f"🔺 {val}"  # 상승 (빨간 위 화살표)
    elif val < 0:
        return f"🔻 {abs(val)}"  # 하강 (파란 아래 화살표)
    else:
        return "-"  # 변동 없음

df["rank_change"] = df["rankInten"].apply(format_rank_change)

# 5-2. 누적 관객 100만 명 이상 영화명 옆에 트로피(🏆) 붙이기
def format_movie_title(row):
    title = row["movieNm"]
    if row["audiAcc"] >= 1_000_000:
        return f"{title} 🏆"
    return title

df["display_movieNm"] = df.apply(format_movie_title, axis=1)

# 순위 기준 정렬
df = df.sort_values("rank").reset_index(drop=True)


# ==========================================
# 6. 상단 1위 영화 지표 카드 (Metrics)
# ==========================================
top_1 = df.iloc[0]

st.subheader(f"🥇 1위 영화: {top_1['display_movieNm']}")

col1, col2, col3 = st.columns(3)
col1.metric(label="일별 관객수", value=f"{top_1['audiCnt']:,} 명")
col2.metric(label="누적 관객수", value=f"{top_1['audiAcc']:,} 명")
col3.metric(label="스크린 수", value=f"{top_1['scrnCnt']:,} 개")

st.divider()


# ==========================================
# 7. 관객수 상위 5개 영화 막대그래프
# ==========================================
st.subheader("📊 관객수 TOP 5")

top_5_df = df.head(5)
st.bar_chart(
    data=top_5_df,
    x="display_movieNm",
    y="audiCnt",
    color="#FF4B4B",
    x_label="영화명",
    y_label="일별 관객수",
)

st.divider()


# ==========================================
# 8. 전체 박스오피스 순위 표
# ==========================================
st.subheader("📋 전체 순위표")

# 표에 출력할 컬럼 추출 및 레이블 이름 변경
display_df = df[
    [
        "rank",
        "rank_change",
        "display_movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt",
    ]
].copy()

display_df.columns = [
    "순위",
    "순위 증감",
    "영화명",
    "개봉일",
    "관객수(명)",
    "누적관객수(명)",
    "스크린수(개)",
]

# 숫자에 천 단위 쉼표 포맷 적용
display_df["관객수(명)"] = display_df["관객수(명)"].map("{:,}".format)
display_df["누적관객수(명)"] = display_df["누적관객수(명)"].map("{:,}".format)
display_df["스크린수(개)"] = display_df["스크린수(개)"].map("{:,}".format)

st.dataframe(display_df, use_container_width=True, hide_index=True)
