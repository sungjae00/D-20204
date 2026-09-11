import datetime
import pandas as pd
import pytz
import requests
import streamlit as st

# ==========================================
# 1. 페이지 기본 설정 및 타임존 계산
# ==========================================
st.set_page_config(page_title="어제 박스오피스 순위", page_icon="🎬", layout="wide")

# 배포 서버의 시계와 상관없이 한국 시간(KST)을 기준으로 '어제' 날짜 계산
kst = pytz.timezone("Asia/Seoul")
yesterday = datetime.datetime.now(kst) - datetime.timedelta(days=1)

target_date_api = yesterday.strftime("%Y%m%d")  # API 요청용 (YYYYMMDD)
target_date_display = yesterday.strftime(
    "%Y년 %m월 %d일"
)  # 화면 표시용 (YYYY년 MM월 DD일)

st.title(f"🎬 {target_date_display} 박스오피스")


# ==========================================
# 2. KOBIS API 데이터 호출 함수 (캐싱 적용)
# ==========================================
# 같은 날짜 요청 시 1시간(3600초) 동안 결과를 재사용하여 API 오뷰 및 과호출 방지
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
# Streamlit Cloud 비밀 설정에 'KOBIS_KEY'가 저장되어 있는지 확인
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
# 4. 에러 예외 처리
# ==========================================
# 4-1. 네트워크/요청 오류
if "network_error" in data:
    st.error("🌐 네트워크 연결에 실패했습니다.")
    st.info("KOBIS API 서버 응답이 지연되거나 인터넷 연결에 문제가 있을 수 있습니다. 잠시 후 다시 시도해 주세요.")
    st.stop()

# 4-2. API 인증키 오류 또는 오류 응답(faultInfo) 처리
if "faultInfo" in data:
    st.error("⚠️ API 오류가 발생했습니다.")
    fault = data["faultInfo"]
    st.warning(
        f"""
    **오류 원인:** {fault.get('message', '알 수 없는 오류')} (코드: {fault.get('errorCode', 'N/A')})
    
    **확인해 주세요:**
    1. Secrets에 등록한 `KOBIS_KEY`가 올바른지 확인해 주세요.
    2. KOBIS 개발자 센터에서 키 상태 및 일일 요청한도가 초과되지 않았는지 확인해 주세요.
    """
    )
    st.stop()

# 4-3. 영화 데이터 추출 및 빈 데이터 검증
box_office_result = data.get("boxOfficeResult", {})
daily_list = box_office_result.get("dailyBoxOfficeList", [])

if not daily_list:
    st.error("📂 영화 목록 데이터를 불러올 수 없습니다.")
    st.info("어제자 집계 데이터가 아직 업데이트되지 않았거나, 제공되는 데이터가 없습니다.")
    st.stop()


# ==========================================
# 5. 데이터 처리 및 숫자형 변환
# ==========================================
df = pd.DataFrame(daily_list)

# 문자열로 들어온 숫자 데이터들을 정수형(int)으로 정제
numeric_columns = ["rank", "audiCnt", "audiAcc", "scrnCnt"]
for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

# 순위 기준 정렬
df = df.sort_values("rank").reset_index(drop=True)


# ==========================================
# 6. 상단 1위 영화 지표 카드 (Metrics)
# ==========================================
top_1 = df.iloc[0]

st.subheader(f"🥇 오늘의 1위 영화: {top_1['movieNm']}")

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
    x="movieNm",
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

# 표에 보여줄 컬럼 선택 및 이름 변경
display_df = df[
    ["rank", "movieNm", "openDt", "audiCnt", "audiAcc", "scrnCnt"]
].copy()
display_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수(명)",
    "누적관객수(명)",
    "스크린수(개)",
]

# 화면 표출용 포맷 적용 (천 단위 쉼표 추가)
display_df["관객수(명)"] = display_df["관객수(명)"].map("{:,}".format)
display_df["누적관객수(명)"] = display_df["누적관객수(명)"].map("{:,}".format)
display_df["스크린수(개)"] = display_df["스크린수(개)"].map("{:,}".format)

st.dataframe(display_df, use_container_width=True, hide_index=True)
