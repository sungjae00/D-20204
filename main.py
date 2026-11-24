import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

# -----------------------------------------------------------------------------
# 1. Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Diamond Price Prediction & Model Dashboard",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. Data Loading & Model Training (Cached for Instant Performance)
# -----------------------------------------------------------------------------
@st.cache_resource
def load_and_train():
    train_df = pd.read_csv("train.csv")
    test_df = pd.read_csv("test.csv")

    feature_cols = [c for c in train_df.columns if c != "log_price"]
    X_train, y_train = train_df[feature_cols], train_df["log_price"]
    X_test, y_test = test_df[feature_cols], test_df["log_price"]

    model = LinearRegression()
    model.fit(X_train, y_train)

    # Predictions on Test Set
    y_pred_log = model.predict(X_test)
    y_actual_usd = np.exp(y_test)
    y_pred_usd = np.exp(y_pred_log)

    metrics = {
        "r2_log": r2_score(y_test, y_pred_log),
        "rmse_log": np.sqrt(mean_squared_error(y_test, y_pred_log)),
        "r2_usd": r2_score(y_actual_usd, y_pred_usd),
        "rmse_usd": np.sqrt(mean_squared_error(y_actual_usd, y_pred_usd)),
        "mae_usd": mean_absolute_error(y_actual_usd, y_pred_usd),
        "mape_pct": np.mean(np.abs((y_actual_usd - y_pred_usd) / y_actual_usd)) * 100,
        "train_rows": len(X_train),
        "test_rows": len(X_test),
    }

    coef_df = pd.DataFrame({
        "Feature": feature_cols,
        "Coefficient": model.coef_,
        "Price_Effect_Pct": (np.exp(model.coef_) - 1) * 100
    })

    eval_df = pd.DataFrame({
        "carat": np.exp(X_test["log_carat"]),
        "actual_usd": y_actual_usd,
        "pred_usd": y_pred_usd,
        "pred_log": y_pred_log,
        "resid_log": y_test - y_pred_log,
        "resid_usd": y_actual_usd - y_pred_usd
    })

    return model, feature_cols, metrics, coef_df, eval_df


try:
    model, feature_cols, metrics, coef_df, eval_df = load_and_train()
except FileNotFoundError:
    st.error("`train.csv` 또는 `test.csv` 파일을 찾을 수 없습니다. `main.py`와 동일한 폴더에 두 파일을 배치해 주세요.")
    st.stop()


# -----------------------------------------------------------------------------
# 3. Helper Function for Single Diamond Prediction
# -----------------------------------------------------------------------------
CUT_LEVELS = ["Fair", "Good", "Very Good", "Premium", "Ideal"]
COLOR_LEVELS = ["D", "E", "F", "G", "H", "I", "J"]
CLARITY_LEVELS = ["I1", "SI2", "SI1", "VS2", "VS1", "VVS2", "VVS1", "IF"]


def predict_diamond_price(carat: float, cut: str, color: str, clarity: str, depth: float, table: float) -> float:
    row = pd.DataFrame(0.0, index=[0], columns=feature_cols)
    row["log_carat"] = np.log(carat)
    row["depth"] = depth
    row["table"] = table

    if cut != "Fair" and f"cut_{cut}" in row.columns:
        row[f"cut_{cut}"] = 1.0
    if color != "D" and f"color_{color}" in row.columns:
        row[f"color_{color}"] = 1.0
    if clarity != "I1" and f"clarity_{clarity}" in row.columns:
        row[f"clarity_{clarity}"] = 1.0

    log_pred = model.predict(row)[0]
    return float(np.exp(log_pred))


# -----------------------------------------------------------------------------
# 4. Sidebar: Interactive Diamond Specification Inputs
# -----------------------------------------------------------------------------
st.sidebar.header("💎 다이아몬드 스펙 입력")
st.sidebar.caption("4C 등급 및 비율 수치를 조절하면 실시간으로 예측 가격이 계산됩니다.")

carat = st.sidebar.slider("중량 (Carat)", min_value=0.20, max_value=5.00, value=1.00, step=0.01)
cut = st.sidebar.select_slider("세공 등급 (Cut)", options=CUT_LEVELS, value="Ideal")
color = st.sidebar.select_slider("색상 등급 (Color, D=최상)", options=COLOR_LEVELS, value="G")
clarity = st.sidebar.select_slider("투명도 등급 (Clarity, IF=최상)", options=CLARITY_LEVELS, value="VS1")

with st.sidebar.expander("세부 비율 설정 (Depth / Table)", expanded=False):
    depth = st.slider("깊이 비율 (Depth %)", min_value=43.0, max_value=79.0, value=61.5, step=0.1)
    table = st.slider("테이블 비율 (Table %)", min_value=43.0, max_value=95.0, value=57.0, step=0.1)


# -----------------------------------------------------------------------------
# 5. Main Header & Tabs
# -----------------------------------------------------------------------------
st.title("💎 다이아몬드 가격 예측 및 선형 회귀 분석 대시보드")
st.markdown(
    f"정제된 데이터 **53,772건**(`train.csv`: {metrics['train_rows']:,}건 / `test.csv`: {metrics['test_rows']:,}건)을 "
    "기반으로 학습된 **로그-선형 회귀(Log-Linear Regression)** 모델입니다."
)

tab1, tab2 = st.tabs(["🔮 실시간 가격 예측기", "📊 모델 성능 및 잔차 분석 리포트"])

# =============================================================================
# TAB 1: Interactive Price Predictor
# =============================================================================
with tab1:
    pred_usd = predict_diamond_price(carat, cut, color, clarity, depth, table)
    # 68% prediction interval using residual std (~0.1353 in log space)
    resid_std = eval_df["resid_log"].std()
    low_usd = pred_usd * np.exp(-resid_std)
    high_usd = pred_usd * np.exp(resid_std)
    price_per_carat = pred_usd / carat

    col1, col2, col3 = st.columns(3)
    col1.metric("예상 적정 가격 (USD)", f"${pred_usd:,.2f}")
    col2.metric("캐럿당 단가 ($ / ct)", f"${price_per_carat:,.2f}")
    col3.metric("예상 가격 범위 (±1σ, 68%)", f"${low_usd:,.0f} ~ ${high_usd:,.0f}")

    st.divider()

    st.subheader("📈 선택한 스펙 기준 등급별 가격 변화 시뮬레이션")
    sim_col1, sim_col2 = st.columns(2)

    with sim_col1:
        st.markdown("**투명도(Clarity) 등급 변경 시 예상 가격**")
        clarity_prices = [
            {"Clarity": c, "Predicted_USD": predict_diamond_price(carat, cut, color, c, depth, table)}
            for c in CLARITY_LEVELS
        ]
        clarity_sim_df = pd.DataFrame(clarity_prices)
        fig_c, ax_c = plt.subplots(figsize=(6, 3.8))
        colors_bar = ["#ff6b6b" if c == clarity else "#4c72b0" for c in clarity_sim_df["Clarity"]]
        ax_c.bar(clarity_sim_df["Clarity"], clarity_sim_df["Predicted_USD"], color=colors_bar)
        ax_c.set_ylabel("Predicted Price ($)")
        ax_c.set_title(f"Price by Clarity ({carat:.2f}ct, {cut}, Color {color})")
        ax_c.grid(axis="y", linestyle="--", alpha=0.5)
        st.pyplot(fig_c)
        plt.close(fig_c)

    with sim_col2:
        st.markdown("**색상(Color) 등급 변경 시 예상 가격**")
        color_prices = [
            {"Color": col_grade, "Predicted_USD": predict_diamond_price(carat, cut, col_grade, clarity, depth, table)}
            for col_grade in COLOR_LEVELS
        ]
        color_sim_df = pd.DataFrame(color_prices)
        fig_col, ax_col = plt.subplots(figsize=(6, 3.8))
        colors_bar2 = ["#ff6b6b" if c == color else "#2ca02c" for c in color_sim_df["Color"]]
        ax_col.bar(color_sim_df["Color"], color_sim_df["Predicted_USD"], color=colors_bar2)
        ax_col.set_ylabel("Predicted Price ($)")
        ax_col.set_title(f"Price by Color ({carat:.2f}ct, {cut}, {clarity})")
        ax_col.grid(axis="y", linestyle="--", alpha=0.5)
        st.pyplot(fig_col)
        plt.close(fig_col)


# =============================================================================
# TAB 2: Model Performance & Residual Analysis Dashboard
# =============================================================================
with tab2:
    st.subheader("1. 테스트 세트 검증 성능 지표 (n = 10,755)")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("달러 기준 R²", f"{metrics['r2_usd']:.4f}")
    m2.metric("로그 기준 R²", f"{metrics['r2_log']:.4f}")
    m3.metric("RMSE (USD)", f"${metrics['rmse_usd']:,.2f}")
    m4.metric("MAE (USD)", f"${metrics['mae_usd']:,.2f}")
    m5.metric("MAPE (오차율)", f"{metrics['mape_pct']:.2f}%")

    st.divider()

    st.subheader("2. 회귀 계수(가중치) 및 가격 영향력 분석")
    c_left, c_right = st.columns([1.3, 1])

    with c_left:
        plot_coef = coef_df[coef_df["Feature"] != "log_carat"].sort_values("Coefficient", ascending=True)
        fig_coef, ax_coef = plt.subplots(figsize=(7, 5.5))
        bar_colors = ["#d9534f" if v < 0 else "#337ab7" for v in plot_coef["Coefficient"]]
        ax_coef.barh(plot_coef["Feature"], plot_coef["Price_Effect_Pct"], color=bar_colors)
        ax_coef.axvline(0, color="black", linewidth=1)
        ax_coef.set_xlabel("Price Change vs. Baseline (%)")
        ax_coef.set_title("Categorical & Ratio Feature Impact (% Effect)")
        ax_coef.grid(axis="x", linestyle="--", alpha=0.5)
        st.pyplot(fig_coef)
        plt.close(fig_coef)

    with c_right:
        st.markdown(
            """
            **핵심 해석 요약**
            * **중량 탄력성 (`log_carat = 1.8848`)**: 중량이 **1% 증가**할 때 가격은 평균 **약 1.88% 상승**합니다.
            * **투명도 (`clarity`, 기준 `I1`)**: `SI2`(+53%)부터 최상급 `IF`(**+204%**)까지 등급 서열대로 가격이 급등합니다.
            * **색상 (`color`, 기준 `D`)**: 무색(`D`)에서 황색기가 짙어질수록 하락해 `J` 등급은 **-39.9%** 낮게 형성됩니다.
            * **세공 (`cut`, 기준 `Fair`)**: `Ideal` 등급은 `Fair` 대비 **+16.9%**의 프리미엄을 가집니다.
            """
        )
        display_coef = coef_df.copy()
        display_coef["Coefficient"] = display_coef["Coefficient"].round(4)
        display_coef["Price_Effect_Pct"] = display_coef["Price_Effect_Pct"].round(2)
        st.dataframe(display_coef, height=270, use_container_width=True)

    st.divider()

    st.subheader("3. 잔차 분석 시각화 (Residual Analysis)")
    fig_res, axes = plt.subplots(2, 2, figsize=(13, 9.5))
    plt.style.use("seaborn-v0_8-whitegrid")

    # (1) Actual vs Predicted USD
    ax = axes[0, 0]
    ax.scatter(eval_df["actual_usd"], eval_df["pred_usd"], alpha=0.18, s=8, color="#1f77b4")
    ax.plot([0, 20000], [0, 20000], "r--", linewidth=1.6, label="Ideal Fit (y = x)")
    ax.set_xlim(0, 20000)
    ax.set_ylim(0, 22000)
    ax.set_title("1. Actual vs. Predicted Price (USD)", fontweight="bold")
    ax.set_xlabel("Actual Price ($)")
    ax.set_ylabel("Predicted Price ($)")
    ax.legend()

    # (2) Residuals vs Fitted (Log Scale)
    ax = axes[0, 1]
    ax.scatter(eval_df["pred_log"], eval_df["resid_log"], alpha=0.18, s=8, color="#2ca02c")
    ax.axhline(0, color="red", linestyle="--", linewidth=1.6, label="Zero Residual")
    ax.set_title("2. Residuals vs. Fitted Values (Log Scale)", fontweight="bold")
    ax.set_xlabel("Fitted log(Price)")
    ax.set_ylabel("Residual (Log)")
    ax.legend()

    # (3) Residual Histogram
    ax = axes[1, 0]
    sns.histplot(eval_df["resid_log"], bins=50, stat="density", kde=True, color="#4c72b0", alpha=0.5, ax=ax)
    x_norm = np.linspace(eval_df["resid_log"].min(), eval_df["resid_log"].max(), 200)
    ax.plot(x_norm, stats.norm.pdf(x_norm, eval_df["resid_log"].mean(), eval_df["resid_log"].std()), "r--", linewidth=1.6, label="Normal Curve")
    ax.set_title("3. Residual Distribution (Log Scale)", fontweight="bold")
    ax.set_xlabel("Residual (Log)")
    ax.legend()

    # (4) Q-Q Plot
    ax = axes[1, 1]
    (osm, osr), (slope, intercept, r_qq) = stats.probplot(eval_df["resid_log"], dist="norm", plot=None)
    ax.scatter(osm, osr, alpha=0.22, s=8, color="#9467bd")
    ax.plot(osm, slope * osm + intercept, "r--", linewidth=1.6, label=f"Theoretical Line (R={r_qq:.4f})")
    ax.set_title("4. Normal Q-Q Plot (Log Residuals)", fontweight="bold")
    ax.set_xlabel("Theoretical Quantiles")
    ax.set_ylabel("Sample Quantiles")
    ax.legend()

    plt.tight_layout()
    st.pyplot(fig_res)
    plt.close(fig_res)
