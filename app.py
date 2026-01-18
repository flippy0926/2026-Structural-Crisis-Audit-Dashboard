import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import requests
from datetime import datetime, timedelta

# --- API Keys ---
# Try to get from Streamlit Secrets, otherwise use hardcoded fallback (for local dev without secrets.toml)
try:
    FRED_API_KEY = st.secrets["FRED_API_KEY"]
except (FileNotFoundError, KeyError):
    # Fallback for local development if secrets.toml is missing
    FRED_API_KEY = "e09f54a44ff56e93a9e6ef6a44bf77dd"

# --- Page Configuration ---
st.set_page_config(
    page_title="2026 Structural Crisis Audit",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="collapsed", # Default collapsed
)

# --- Translations & Report Texts ---
TRANSLATIONS = {
    "title": {
        "English": "2026 Structural Crisis Audit Dashboard",
        "日本語": "2026年 構造的危機監査ダッシュボード"
    },
    "fcf_capex": {
        "English": "FCF/CapEx Ratio",
        "日本語": "FCF/CapEx 比率"
    },
    "sp500_label": {
        "English": "S&P 500 Current",
        "日本語": "S&P 500 現在値"
    },
    "nyfang_label": {
        "English": "NYSE FANG+ Index",
        "日本語": "NYSE FANG+ 指数"
    },
    "l1_title": {
        "English": "Layer 1: FANG+ Capital Durability Audit",
        "日本語": "レイヤー1: FANG+ 資本耐久性監査"
    },
    "l2_title": {
        "English": "Layer 2: Systemic Liquidity Friction Monitor",
        "日本語": "レイヤー2: システム流動性摩擦モニター"
    },
    "l1_desc": {
        "日本語": """
        主要AI関連銘柄（NYSE FANG+構成銘柄）におけるフリーキャッシュフロー（$FCF$）と設備投資（$CapEx$）の相関を監視します。市場価格を支える最大の「盾」は、これら企業の圧倒的なキャッシュ生成能力にあります。しかし、AIインフラの物理的構築コスト（電力・チップ・データセンター）が $FCF$ を上回り、$FCF/CapEx$ 比率が $1.0$ を割り込む事態は、企業が自律的な資金循環を喪失し、不足分を「銀行の未使用融資枠（Unused Commitments）」に依存し始めることを意味します。これは、民間企業のインフラ投資が銀行システム全体の流動性を吸い取り、市場を「構造的窒息」へ導く物理的な前兆であると定義します。
        """,
        "English": """
        We monitor the correlation between Free Cash Flow ($FCF$) and Capital Expenditure ($CapEx$) among major AI-related constituents (NYSE FANG+). The primary "Shield" supporting market valuations is the overwhelming cash-generating capacity of these firms. However, should the physical costs of AI infrastructure—such as power, semiconductors, and data centers—exceed $FCF$, resulting in an $FCF/CapEx$ ratio below $1.0$, it signifies that these firms have lost fiscal autonomy and begun to rely on "Unused Bank Commitments" to fund their requirements. We define this transition as a physical precursor to "Structural Suffocation," where systemic liquidity is drained from the banking system to sustain capital-intensive infrastructure, ultimately destabilizing the broader market.
        """
    },
    "l2_desc": {
        "日本語": """
        これらの指標は、金融システムの深層における**「準備金の過不足」と「資本の真の価格」**を直接的に示す4つの独立変数です。$SOFR - IORB$ スプレッド: 銀行間準備金の需給。$5bps$ 超過はシステム全体の摩擦を示唆。$TNX$ 5MA 乖離: 金利再設定の加速速度。実質金利 ($DFII10$): インフレ調整後の剥き出しの資本コスト。入札テール ($Auction\ Tail$): 公的債務の需要断絶とディーラーの受入限界。スプレッドが $5bps$ を超え、実質金利が急騰する状態は、流動性の土台が揺らぎ、市場が衝撃に対して極めて脆弱な**「砂上の楼閣」**と化しているサインです。テールの拡大と金利の加速は、バリュエーションの強制的な再設定を促す物理的トリガーとなります。
        """,
        "English": """
        These metrics are four independent variables that directly measure "reserve supply/demand" and the "true price of capital" within the deep layers of the financial system. $SOFR - IORB$ Spread: Bank reserve surplus or deficit. A spread above $5bps$ signals systemic friction. $TNX$ 5MA Deviation: The velocity of interest rate repricing. Real Yield ($DFII10$): The naked cost of capital after inflation adjustments. Auction Tail: Fracture in debt demand and dealer capacity limits. A state where the spread exceeds $5bps$ alongside a spike in real yields signifies a crumbling liquidity foundation, rendering the market highly vulnerable to systemic shocks. Widening tails and yield acceleration act as physical triggers for a forced repricing of valuations.
        """
    },
    "spread_title": {
        "English": "Overnight Rates (SOFR vs IORB)",
        "日本語": "翌日物金利 (SOFR vs IORB)"
    },
    "tail_title": {
        "English": "Treasury Tail Risk",
        "日本語": "米国債入札テール"
    }
}

REPORTS = {
    "HEALTHY": {
        "日本語": """
        **健全：業績相場（Earnings-Driven Equilibrium）**
        現在の市場は強固な業績の盾に守られた理想的な均衡状態にあります。$SPX$ は $6,880$ の構造的防衛線を維持しており、$SOFR$ スプレッドも $5bps$ 未満と、銀行システム内の流動性は円滑に循環しています。
        FANG+構成銘柄のキャッシュフロー（$FCF$）は巨大なAIインフラ投資（$CapEx$）を十分にカバーしており、銀行の未使用融資枠を占有することなく自律的な成長を継続しています。
        この局面では、成長率（$g$）が資本コスト（$r$）を支配しており、物理的な制約（電力・与信・担保金）は業績の拡大によって吸収されています。
        構造的断層のリスクは極めて低く、自社株買いが市場の流動性供給装置として正常に機能しています。ナラティブと物理的事実の乖離は最小限であり、監査上の決壊兆候は検出されていません。
        
        **構造的留意事項**
        *   **マクロ指標の変節に対する感度**：良好な業績データの裏側で、$SOFR$ スプレッドの微増や入札テールの発生といった「初期の摩擦」が、構造的均衡を崩す可能性を常に監視すること。
        *   **リスクシナリオの継続的検証**：均衡状態の継続中であっても、3月の断層に向けた物理的制約の蓄積状況について、客観的なデータに基づいた検証を怠らないこと。
        """,
        "English": """
        **Health: Earnings-Driven Equilibrium**
        The market currently resides in an ideal equilibrium, fortified by a robust Earnings Shield. The $SPX$ maintains its structural defense line at $6,880$, while the $SOFR$ spread remains below $5bps$, indicating a smooth circulation of liquidity within the banking system.
        Free Cash Flow ($FCF$) among FANG+ constituents sufficiently covers massive AI infrastructure investments ($CapEx$), allowing for autonomous growth without encroaching upon unused bank credit lines.
        In this phase, the growth rate ($g$) dominates the cost of capital ($r$), and physical constraints—such as power, credit, and collateral requirements—are being absorbed by expanding earnings.
        The divergence between narrative and physical reality remains minimal, and no structural fracture points have been detected. The Buyback mechanism functions effectively as a liquidity provision device for the market.
        
        **Structural Observations**
        *   **Sensitivity to Macro Shifts**: Even during strong earnings cycles, maintain vigilance for "initial friction," such as subtle increases in the $SOFR$ spread or Treasury auction tails, which may signal a shift in structural equilibrium.
        *   **Continuous Validation of Risk Scenarios**: Persist in verifying the accumulation of physical constraints leading into the March "Structural Fault," ensuring that assessments are grounded in objective data rather than prevailing optimism.
        """
    },
    "WARNING": {
        "日本語": """
        **警告：ナラティブ延命（Narrative-Driven Friction）**
        市場構造に物理的摩擦が顕在化しています。株価指数は $6,880$ の境界線上で推移していますが、**限界的準備金の減少（$SOFR$ 上昇）** により、流動性の供給能力が低下しつつあります。
        現在の価格水準を支えているのは実体的な流動性ではなく、ナラティブ（期待）による浮力です。FANG+各社の $CapEx$ 増大が銀行の与信枠を占有し始めており、限界的な貸出余力が低下する「資本の石化」が進行しています。
        3月の借換需要（企業の壁）に向けた負のエネルギーが蓄積されており、自社株買いの執行速度が物理的コストの増大に追いつかなくなるリスクを示唆しています。
        業績の盾は摩耗し始めており、僅かな物理的ショックが断層の引き金となる臨界点にあります。価格の推移よりも流動性の質の監視を優先すべき局面であり、均衡が崩れる前兆を捉えることが監査の主目的となります。
        
        **構造的留意事項**
        *   **流動性指標の優先**：価格の維持に関わらず、流動性指標が悪化した状態では構造的な脆弱性が高まっている事実を認識し、リスク許容度の再評価を行うこと。
        *   **個別銘柄の耐久性乖離**：FANG+内でも $FCF/CapEx$ 比率が悪化した銘柄と健全な銘柄の「耐久性の差」を精査し、セクター一括の楽観視を避けること。
        """,
        "English": """
        **Warning: Narrative-Driven Friction**
        Physical friction is becoming manifest within the market structure. While the price index hovers near the $6,880$ boundary, a reduction in marginal reserves ($SOFR$ spike) indicates a declining capacity for liquidity provision.
        Current price levels are being sustained by narrative-driven buoyancy rather than substantive liquidity. Increasing $CapEx$ from FANG+ firms is beginning to occupy bank credit lines, leading to a "petrification of capital" and a decrease in marginal lending capacity.
        Negative energy is accumulating toward the March refinancing cycle (The Corporate Wall), suggesting a risk that the velocity of share buybacks may fail to keep pace with rising physical costs.
        The Earnings Shield is beginning to wear thin, and the market is at a critical threshold where minor physical shocks could trigger a structural fault. In this phase, monitoring the quality of liquidity must take precedence over tracking price movements.
        
        **Structural Observations**
        *   **Prioritization of Liquidity Metrics**: Recognize that structural vulnerability remains high when liquidity metrics deteriorate, regardless of price stability. Re-evaluate risk tolerances based on liquidity flow rather than index levels.
        *   **Divergence in Constituent Durability**: Scrutinize the "durability gap" among FANG+ members—specifically the $FCF/CapEx$ ratio of individual firms—and avoid treating the sector as a monolithic entity.
        """
    },
    "CRITICAL": {
        "日本語": """
        **決壊：構造的崩壊（Structural Collapse Phase）**
        構造的決壊が確認されました。$SPX$ が $6,880$ を割り込み、あるいは FANG+ が $11,820$ のガンマ・フリップ・ポイントを突破したことで、市場は自己増幅的な下落フェーズに突入しています。
        業績の盾は物理的コスト（金利・電力・与信）の激増によって粉砕され、自社株買いによる価格維持能力は大幅に低下しています。銀行準備金の枯渇により、マーケットメーカーのヘッジ行動が価格変動を増幅させる「負のフィードバック」が発生しています。
        もはや価格を支える構造的根拠は極めて限定的となり、$5,300$ が次の均衡点として統計的に有力な領域に入りました。
        全てのナラティブは棄却され、物理的な支払能力と流動性の絶対量のみが市場を支配する強制的な価格再設定の局面です。救済措置としての期待は「インフレの物理的粘着性」によって遮断されており、期待に基づいた判断は機能しにくい状態にあります。
        
        **構造的留意事項**
        *   **客観的接地帯の確認**：均衡点（$5,300$）への接地と流動性の回復が数値（$SOFR$ 等）で確認されるまで、根拠のない価格反転を前提とした予断を持たないこと。
        *   **事実に基づいた状況判断**：特定の政治的・経済的ニュースによる希望的観測を排し、目の前の「価格と流動性の乖離」という物理的事実のみを判断の基軸とすること。
        """,
        "English": """
        **Critical: Structural Collapse Phase**
        A structural collapse has been confirmed. The $SPX$ has breached the $6,880$ defense line, or the $NYFANG$ has crossed the Gamma Flip Point at $11,820$, plunging the market into a self-reinforcing downward phase.
        The Earnings Shield has been shattered by a surge in physical costs (interest, power, and credit), and the capacity for price maintenance via buybacks has significantly diminished. The exhaustion of bank reserves has triggered a "negative feedback loop," with market maker hedging activity amplifying price volatility.
        Structural justifications for current price levels are now extremely limited, and $5,300$ has entered the zone of statistical probability as the next equilibrium point. All narratives have been rejected, and the market is in a phase of forced price resetting, dominated solely by physical solvency and the absolute volume of liquidity.
        Expectations for policy relief are obstructed by "physical inflation stickiness," rendering narrative-based judgments ineffective.
        
        **Structural Observations**
        *   **Verification of Objective Grounding**: Avoid making assumptions about price reversals until an objective grounding at the equilibrium point ($5,300$) and a recovery in liquidity ($SOFR$, etc.) are confirmed by data.
        *   **Fact-Based Situational Assessment**: Disregard any hopeful speculation driven by political or economic news. Decisions should be anchored exclusively in the physical reality of the "price-liquidity gap."
        """
    }
}

# --- Custom CSS ---
st.markdown("""
    <style>
        /* Import Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Main Background */
        .stApp {
            background-color: #F4F7F9;
        }
        
        /* Hide sidebar completely */
        [data-testid="stSidebar"] {
            display: none;
        }
        
        /* Judgment Panel */
        .judgment-panel {
            background-color: #FFFFFF;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin-bottom: 25px;
            border-left: 8px solid #ddd;
        }
        .panel-healthy { border-left-color: #28A745; }
        .panel-warning { border-left-color: #FFC107; }
        .panel-critical { border-left-color: #DC3545; }
        
        .judgment-title {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 15px;
        }

        /* Metrics Strip Panel */
        .metrics-strip {
            background-color: #fff;
            border-radius: 10px;
            padding: 15px 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
            border: 1px solid #eee;
        }
        
        .stat-box {
            text-align: center;
        }
        .stat-label {
            font-size: 0.85rem;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }
        .stat-value {
            font-size: 1.4rem;
            font-weight: 700;
            color: #222;
        }
        .stat-sub {
            font-size: 0.8rem;
            color: #888;
        }

        /* Card Styles */
        .metric-card {
            background-color: #FFFFFF;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.03);
            margin-bottom: 15px;
            border: 1px solid #EAEAEA;
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        .warning-card {
            border-left: 5px solid #FF4B4B !important;
        }

        /* Hide Streamlit Header/Footer */
        header[data-testid="stHeader"] { display: none; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        
        .block-container { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# --- Session State for Language ---
if 'language' not in st.session_state:
    st.session_state.language = "日本語"

def set_lang(lang):
    st.session_state.language = lang

lang = st.session_state.language

# --- Data Loading ---
# --- Google Sheet URLs ---
CONFIG_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTPFDp3yDMtcAChS7vdE2yUlv-tvCw5cPDlI5-k8dm-ZUYCMiQ6_ydWHZui7G92WxEbkaUFvap2lFa6/pub?output=csv"
LIQUIDITY_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRp0T72A5SmCOEuxj-guQ5ErHi7PWWtS05dAJdQnwx2ccEjdBRLHXIrcwfDYnnF9iguA7oMZLyGNpAr/pub?output=csv"

@st.cache_data(ttl=600)
def load_config():
    try:
        # Fetch from Google Sheet
        config = pd.read_csv(CONFIG_SHEET_URL)
        return config
    except Exception:
        # Fallback to local
        try:
            return pd.read_csv("data/Config.csv")
        except:
            return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_live_metrics():
    # FANG Metrics
    tickers = ["META", "AMZN", "NFLX", "GOOGL", "MSFT", "AAPL", "NVDA", "TSLA", "SNOW", "AVGO"]
    rows = []
    for t in tickers:
        try:
            tick = yf.Ticker(t)
            hist = tick.history(period="1d")
            price = float(hist['Close'].iloc[-1]) if not hist.empty else 0
            
            # Simple caching attempt for financials
            try:
                cf = tick.cashflow
                fcf = cf.loc["Free Cash Flow"].iloc[0] if "Free Cash Flow" in cf.index else 0
                capex = cf.loc["Capital Expenditure"].iloc[0] if "Capital Expenditure" in cf.index else 0
            except:
                fcf = 0
                capex = 0
                
            rows.append({"Ticker": t, "Price": round(price, 2), "FCF": fcf, "CapEx": capex})
        except:
            rows.append({"Ticker": t, "Price": 0, "FCF": 0, "CapEx": 0})
    return pd.DataFrame(rows)

@st.cache_data(ttl=3600)
def get_market_data_fred_yfinance():
    data = {}
    try:
        spx = yf.Ticker("^GSPC").history(period="1d")
        data['SPX'] = float(spx['Close'].iloc[-1]) if not spx.empty else 6900.0
        nyfang = yf.Ticker("^NYFANG").history(period="1d")
        data['NYFANG'] = float(nyfang['Close'].iloc[-1]) if not nyfang.empty else 12000.0
    except:
        data['SPX'] = 6900.0
        data['NYFANG'] = 12000.0

    # 2. Rates from FRED API (Direct) & Yahoo (TNX)
    try:
        # Helper to fetch series
        def fetch_fred_series(series_id, limit=300):
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series_id}&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit={limit}"
            r = requests.get(url)
            if r.ok and r.json().get('observations'):
                return r.json()['observations']
            return []

        # Latest values
        sofr_latest = fetch_fred_series('SOFR', 1)
        iorb_latest = fetch_fred_series('IORB', 1)
        
        data['SOFR'] = float(sofr_latest[0]['value']) if sofr_latest else 5.30
        data['IORB'] = float(iorb_latest[0]['value']) if iorb_latest else 5.40
        data['Spread'] = data['SOFR'] - data['IORB']
        
        # --- History Fetching (Common Range: ~2026-01-01 to Present) ---
        # We fetch ~300 days to be safe, then filter in UI or here.
        
        # A. SOFR vs IORB
        obs_sofr = fetch_fred_series('SOFR', 300)
        obs_iorb = fetch_fred_series('IORB', 300)
        
        if obs_sofr and obs_iorb:
             df_sofr = pd.DataFrame(obs_sofr)
             df_iorb = pd.DataFrame(obs_iorb)
             df_sofr['value'] = pd.to_numeric(df_sofr['value'], errors='coerce')
             df_sofr['date'] = pd.to_datetime(df_sofr['date'])
             df_sofr = df_sofr[['date', 'value']].rename(columns={'value': 'SOFR'})
             
             df_iorb['value'] = pd.to_numeric(df_iorb['value'], errors='coerce')
             df_iorb['date'] = pd.to_datetime(df_iorb['date'])
             df_iorb = df_iorb[['date', 'value']].rename(columns={'value': 'IORB'})
             
             df_rates = pd.merge(df_sofr, df_iorb, on='date', how='inner').sort_values('date')
             data['Rates_History'] = df_rates
        else:
             data['Rates_History'] = pd.DataFrame()

        # B. Real Yield (DFII10)
        obs_real = fetch_fred_series('DFII10', 300)
        if obs_real:
            df_real = pd.DataFrame(obs_real)
            df_real['value'] = pd.to_numeric(df_real['value'], errors='coerce')
            df_real['date'] = pd.to_datetime(df_real['date'])
            data['Real_Yield'] = df_real.sort_values('date')
        else:
            data['Real_Yield'] = pd.DataFrame()

        # C. TNX Divergence (Yahoo)
        tnx = yf.Ticker("^TNX").history(period="6mo") # Get enough for MA
        if not tnx.empty:
            tnx = tnx[['Close']].reset_index()
            tnx['Date'] = pd.to_datetime(tnx['Date']).dt.tz_localize(None) # Remove timezone
            tnx['MA5'] = tnx['Close'].rolling(window=5).mean()
            tnx['Divergence'] = tnx['Close'] - tnx['MA5']
            data['TNX_Div'] = tnx.dropna()
        else:
            data['TNX_Div'] = pd.DataFrame()

    except Exception as e:
        data['SOFR'] = 5.30
        data['IORB'] = 5.40
        data['Spread'] = -0.10
        data['Rates_History'] = pd.DataFrame()
        data['Real_Yield'] = pd.DataFrame()
        data['TNX_Div'] = pd.DataFrame()

    return data

@st.cache_data(ttl=600)
def load_mock_liquidity():
    try:
        df = pd.read_csv(LIQUIDITY_SHEET_URL)
        
        # Rename columns (Handle potential JP headers)
        # Assuming col 0 is Date and col 1 is Tail based on sheet structure
        if len(df.columns) >= 2:
            df.columns.values[0] = "Date"
            df.columns.values[1] = "Treasury_Tail"
            
        # Ensure 'Date' is datetime. 
        df['Date'] = pd.to_datetime(df['Date'], format='mixed', errors='coerce') 
        return df[['Date', 'Treasury_Tail']].dropna()
    except Exception as e:
        # Fallback to local
        try:
             df = pd.read_csv("data/Market_Liquidity.csv")
             df['Date'] = pd.to_datetime(df['Date'], format='mixed', errors='coerce')
             return df
        except:
             return pd.DataFrame()

# Load
config_df = load_config()
metrics_df = get_live_metrics()
market_data = get_market_data_fred_yfinance()
liquidity_df_mock = load_mock_liquidity()

def get_config_val(key, default=0):
    try:
        val = config_df.loc[config_df['Key'] == key, 'Value'].iloc[0]
        return float(val)
    except:
        return default

# --- Logic ---
SPX_FRICTION = get_config_val("SPX_FRICTION", 7020)
SPX_DEFENSE = get_config_val("SPX_DEFENSE", 6880)
FANG_FRICTION = get_config_val("FANG_FRICTION", 12450)
FANG_FLIP = get_config_val("FANG_FLIP", 11820) 

val_spx = market_data.get('SPX')
val_nyfang = market_data.get('NYFANG')
val_sofr = market_data.get('SOFR')
val_iorb = market_data.get('IORB')
val_spread = val_sofr - val_iorb
logic_spread_threshold = 0.05 

is_critical_price = (val_spx <= SPX_DEFENSE) or (val_nyfang <= FANG_FLIP)
is_warning_price = (val_spx <= SPX_FRICTION) or (val_nyfang <= FANG_FRICTION)
is_liquidity_stress = val_spread >= logic_spread_threshold

final_status = "HEALTHY"
if is_critical_price and is_liquidity_stress:
    final_status = "CRITICAL"
elif is_warning_price or is_liquidity_stress:
    final_status = "WARNING"
else:
    final_status = "HEALTHY"

STATUS_MAP = {
    "HEALTHY": {"color": "#28A745", "icon": "🟢", "class": "panel-healthy"},
    "WARNING": {"color": "#FFC107", "icon": "🟡", "class": "panel-warning"},
    "CRITICAL": {"color": "#DC3545", "icon": "🔴", "class": "panel-critical"}
}
current_meta = STATUS_MAP[final_status]

# --- Layout ---

# Header: Title and Settings/Lang
c_head_L, c_head_R = st.columns([8, 1])
with c_head_L:
    st.title(TRANSLATIONS['title'][lang])
with c_head_R:
    # Right align language
    st.markdown('<div style="text-align: right; margin-top: 10px;">', unsafe_allow_html=True)
    selected_lang = st.radio("Lang", ["JP", "EN"], index=0 if lang=="日本語" else 1, horizontal=True, label_visibility="collapsed", key="lang_main")
    
    if selected_lang == "JP" and lang != "日本語":
        set_lang("日本語")
        st.rerun()
    elif selected_lang == "EN" and lang != "English":
        set_lang("English")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# 1. Judgment Panel (Main Statement)
st.markdown(f"""
<div class="judgment-panel {current_meta['class']}">
    <div class="judgment-title" style="color: {current_meta['color']}">
        {current_meta['icon']} {REPORTS[final_status][lang].splitlines()[1].strip()}
    </div>
    <div style="font-size: 1.05rem; line-height: 1.6; color: #333;">
""", unsafe_allow_html=True)
st.markdown(REPORTS[final_status][lang])
st.markdown("</div></div>", unsafe_allow_html=True)

# 2. Metrics Strip (Relocated Below)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card" style="text-align:center;">
        <div class="stat-label">S&P 500</div>
        <div class="stat-value">{val_spx:,.0f}</div>
        <div class="stat-sub">Defense: {SPX_DEFENSE:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card" style="text-align:center;">
        <div class="stat-label">NY FANG+</div>
        <div class="stat-value">{val_nyfang:,.0f}</div>
        <div class="stat-sub">Flip: {FANG_FLIP:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card" style="text-align:center;">
        <div class="stat-label">SOFR</div>
        <div class="stat-value">{val_sofr:.2f}%</div>
        <div class="stat-sub">Target: < 5.35%</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    spread_bps = (val_sofr - val_iorb) * 100
    color = "red" if spread_bps >= 5 else "green"
    st.markdown(f"""
    <div class="metric-card" style="text-align:center;">
        <div class="stat-label">Spread (SOFR-IORB)</div>
        <div class="stat-value" style="color:{color}">{spread_bps:.1f} bps</div>
        <div class="stat-sub">Limit: +5.0 bps</div>
    </div>
    """, unsafe_allow_html=True)


# 3. Main Content (Layers Stacked)
st.divider()

# Layer 1
st.subheader(TRANSLATIONS['l1_title'][lang])
st.markdown(TRANSLATIONS['l1_desc'][lang])

# --- Layer 1 Messages ---
L1_MESSAGES = {
    "HEALTHY": {
        "JP": "🟢 **健全 (自律的均衡)**\n企業のキャッシュ生成能力（$FCF$）がAIインフラ投資（$CapEx$）を十分に凌駕しています。外部の銀行与信に依存することなく投資と株主還元を両立できる「業績の盾」が強固に機能しており、構造的均衡は維持されています。",
        "EN": "🟢 **DURABLE (Autonomous Equilibrium)**\nCorporate cash generation ($FCF$) sufficiently exceeds AI infrastructure investment ($CapEx$). The 'Earnings Shield' is functioning robustly, enabling both investment and shareholder returns without reliance on external bank credit. Structural equilibrium remains intact."
    },
    "WARNING": {
        "JP": "🟡 **警告 (耐久性の摩擦)**\n投資コストの増大によりキャッシュ余力が急速に低下しています。自律的な資金循環の限界点（$1.0$）に接近しており、僅かな収益悪化やコスト増が「銀行融資枠の占有」を引き起こすリスクが高まっています。",
        "EN": "🟡 **STRAINED (Friction in Durability)**\nIncreasing investment costs are rapidly depleting cash buffers. The metrics are approaching the threshold of fiscal autonomy ($1.0$). High risk remains that any minor earnings deterioration or cost spike will trigger a 'seizure of bank credit lines.'"
    },
    "CRITICAL": {
        "JP": "🔴 **決壊 (自律性の喪失と窒息)**\n物理的投資コストがキャッシュ生成能力を突破しました。企業は自律性を失い、不足分を銀行の「未使用融資枠」に依存し始めています。これはシステム全体の準備金を占有し、市場を構造的窒息へ導く物理的な決壊サインです。",
        "EN": "🔴 **BROKEN (Loss of Autonomy & Suffocation)**\nPhysical investment costs have breached cash-generating capacity. Firms have lost fiscal autonomy and begun relying on 'Unused Bank Commitments.' This signifies a physical rupture, where systemic reserves are drained, leading the market toward structural suffocation."
    }
}

# Calculate Aggregate FCF/CapEx Durability
l1_total_fcf = metrics_df['FCF'].sum()
l1_total_capex = abs(metrics_df['CapEx'].sum())
l1_durability_ratio = l1_total_fcf / l1_total_capex if l1_total_capex > 0 else 1.5

if l1_durability_ratio < 1.0:
    l1_status = "CRITICAL" 
elif l1_durability_ratio <= 1.2:
    l1_status = "WARNING"
else:
    l1_status = "HEALTHY"

l1_meta = STATUS_MAP[l1_status]
l1_msg_key = "JP" if lang == "日本語" else "EN"

st.markdown(f"""
<div class="judgment-panel {l1_meta['class']}" style="padding: 15px; margin-bottom: 20px;">
    {L1_MESSAGES[l1_status][l1_msg_key]}
    <hr style="margin: 10px 0; opacity: 0.3;">
    <div style="font-size: 0.9rem; font-weight: bold;">
        Systemic Ratio: {l1_durability_ratio:.2f}x (Total FCF: ${l1_total_fcf/1e9:,.0f}B / Total CapEx: ${l1_total_capex/1e9:,.0f}B)
    </div>
</div>
""", unsafe_allow_html=True)

cols = st.columns(4)
for idx, row in metrics_df.iterrows():
    ticker = row['Ticker']
    price = row['Price']
    fcf = row['FCF']
    capex = row['CapEx']
    
    safe_capex = abs(capex) if capex != 0 else 1
    ratio = fcf / safe_capex
    ratio_fmt = f"{ratio:.2f}x"
    is_warning = ratio < 1.0
    warning_class = "warning-card" if is_warning else ""
    text_color = "#D32F2F" if is_warning else "#2E7D32"
    
    with cols[idx % 4]:
        st.markdown(f"""
        <div class="metric-card {warning_class}">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 5px;">
                <h3 style="margin:0; font-size:1.2rem;">{ticker}</h3>
                <span style="font-weight:bold; color:#555;">${price:,.0f}</span>
            </div>
            <div style="font-size:1.5rem; font-weight:bold; color:{text_color}; margin-bottom: -5px;">
                {ratio_fmt}
            </div>
            <div style="font-size:0.8rem; color:#555;">
                (FCF: ${fcf/1e9:,.1f}B / CapEx: ${abs(capex)/1e9:,.1f}B)
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- Layer 2 Messages (Detailed) ---
L2_MESSAGES = {
    "SOFR_IORB": {
        "HEALTHY": {
            "JP": "**正常 (流動性充足)**：準備金がシステム全体に円滑に循環しており、民間金融システムの資金供給能力に摩擦は認められない。",
            "EN": "**Liquidity Sufficiency**: Reserves are circulating smoothly. No notable friction detected in the funding capacity of the private banking system."
        },
        "WARNING": {
            "JP": "**摩擦 (準備金逼迫)**：準備金の減少により短期調達コストが上昇。ショックに対するバッファーが低下し、構造的な脆弱性が顕在化。",
            "EN": "**Reserve Tightness**: Diminishing reserves are driving up funding costs. The buffer against shocks is decreasing, revealing structural vulnerabilities."
        },
        "CRITICAL": {
            "JP": "**逼迫 (システム的窒息)**：民間銀行間の融資余力が物理的に枯渇。流動性の土台が揺らぎ、市場は「砂上の楼閣」の状態にあると判定。",
            "EN": "**Systemic Suffocation**: Funding capacity between banks has evaporated. The liquidity foundation is unstable; the market is assessed as a 'house of cards'."
        }
    },
    "TNX_DEV": {
        "HEALTHY": {
            "JP": "**安定 (均衡状態)**：金利変動が短期平均の範囲内に収束。市場は現在の資本コストを正常に消化しており、価格再設定の圧力は低い。",
            "EN": "**Equilibrium**: Yield fluctuations are within the short-term average. The market is absorbing capital costs; repricing pressure remains low."
        },
        "WARNING": {
            "JP": "**摩擦 (加速の兆候)**：金利が短期平均から不自然に逸脱。バリュエーションへの下方圧力が強まり、価格再設定の衝撃波が発生。",
            "EN": "**Signs of Acceleration**: Yields are deviating from the average. Downward pressure on valuations is intensifying, generating a repricing shockwave."
        },
        "CRITICAL": {
            "JP": "**逼迫 (暴走)**：金利の加速が物理的限界に到達。全ての資産価格に対し、物理的な下方修正を強いる局面。",
            "EN": "**Forced Repricing**: Yield acceleration has reached a physical limit, compelling a downward revision across all asset classes."
        }
    },
    "REAL_YIELD": {
        "HEALTHY": {
            "JP": "**正常 (許容資本自律性)**：実質コストが成長の許容範囲内。FANG+の「業績の盾」および投資の継続性を損なわない水準。",
            "EN": "**Capital Autonomy**: Real costs remain within the range of growth. Levels do not compromise the 'Earnings Shield' or investment continuity."
        },
        "WARNING": {
            "JP": "**摩擦 (利幅の浸食)**：実質コスト上昇が企業の再投資効率を圧迫。キャッシュフローの耐久性に歪みが生じ、成長株モデルが揺らぐ。",
            "EN": "**Margin Erosion**: Rising real costs are straining reinvestment efficiency. Distortions in cash flow durability are challenging growth stock models."
        },
        "CRITICAL": {
            "JP": "**逼迫 (資本の石化)**：剥き出しのコストが企業の成長を物理的に停止させる。成長株モデルの論理的崩壊を誘発する臨界点。",
            "EN": "**Petrification of Capital**: Naked costs are physically halting growth. A critical threshold that triggers the logical collapse of growth stock models."
        }
    },
    "TAIL": {
        "HEALTHY": {
            "JP": "**正常 (吸収旺盛な需要)**：投資家による国債吸収が円滑。プライマリー・ディーラーのバランスシートに十分な受入余力が存在。",
            "EN": "**Robust Demand**: Treasury absorption is smooth. Primary dealers maintain sufficient capacity on their balance sheets."
        },
        "WARNING": {
            "JP": "**摩擦 (受入限界の予兆)**：最終需要が減退し、ディーラーが在庫を抱え込まされ始めている。市場血管の「詰まり」が発生。",
            "EN": "**Signs of Capacity Limits**: Final demand is waning; dealers are being forced to carry inventory. 'Blockages' are emerging in the market."
        },
        "CRITICAL": {
            "JP": "**逼迫 (国家の壁の亀裂)**：需要が物理的に減衰。国債市場の機能不全が、システム全体の決壊リスクを急激に高めている状態。",
            "EN": "**Fracture in the Wall**: Demand is physically decaying. Treasury market dysfunction is escalating the risk of a systemic collapse."
        }
    },
    "COMPOSITE": {
        "HEALTHY": {
            "JP": "✅ **STABLE (安定)**\n構造的均衡が維持されています。物理的制約による市場への直接的な圧力は最小限です。",
            "EN": "✅ **STABLE**\nStructural equilibrium is maintained. Direct pressure on the market from physical constraints is minimal."
        },
        "WARNING": {
            "JP": "⚠️ **CAUTION (警戒)**\n複数の指標で摩擦が検出されました。流動性の土台に歪みが生じており、構造的遷移への警戒が必要です。",
            "EN": "⚠️ **CAUTION**\nFriction detected across multiple metrics. Distortions in the liquidity foundation suggest a need for vigilance regarding structural transitions."
        },
        "CRITICAL": {
            "JP": "🚨 **EMERGENCY (緊急)**\nシステム的決壊リスクが臨界点に到達しました。期待（ナラティブ）が剥落し、物理的な価格再設定が優先される局面です。",
            "EN": "🚨 **EMERGENCY**\nSystemic collapse risk has reached a critical threshold. Narrative buoyancy is evaporating; physical repricing now dominates the phase."
        }
    }
}

# --- Layer 2 Logic Functions ---
def evaluate_l2_status(sofr_spread, tnx_dev, real_yield, tail):
    # 1. SOFR - IORB Logic
    if sofr_spread > 0.05: s_sofr = "CRITICAL"
    elif sofr_spread > 0.00: s_sofr = "WARNING"
    else: s_sofr = "HEALTHY"
    
    # 2. TNX Deviation Logic
    if tnx_dev > 0.15: s_tnx = "CRITICAL"
    elif tnx_dev > 0.05: s_tnx = "WARNING"
    else: s_tnx = "HEALTHY"
    
    # 3. Real Yield Logic
    if real_yield > 2.50: s_real = "CRITICAL"
    elif real_yield > 2.00: s_real = "WARNING"
    else: s_real = "HEALTHY"
    
    # 4. Auction Tail Logic
    if tail > 3.0: s_tail = "CRITICAL"
    elif tail > 1.0: s_tail = "WARNING"
    else: s_tail = "HEALTHY"
    
    # Composite Logic
    # 🚨 EMERGENCY: 2+ CRITICAL
    # ⚠️ CAUTION: 2+ (CRITICAL or WARNING) (Wait, prompt says "2 or more YELLOW" for Caution. Often implies inclusive. I'll stick to strict hierarchy)
    results = [s_sofr, s_tnx, s_real, s_tail]
    red_count = results.count("CRITICAL")
    yellow_count = results.count("WARNING")
    
    if red_count >= 2:
        comp_status = "CRITICAL"
    elif (red_count + yellow_count) >= 2:
        comp_status = "WARNING"
    else:
        comp_status = "HEALTHY"
        
    return comp_status, s_sofr, s_tnx, s_real, s_tail

# Layer 2: Liquidity Thrombus (4 Columns)
st.subheader(TRANSLATIONS['l2_title'][lang])
st.markdown(TRANSLATIONS['l2_desc'][lang])

# Prepare Data for L2 Evaluation
val_rates_hist = market_data.get('Rates_History', pd.DataFrame())
val_tnx_div = market_data.get('TNX_Div', pd.DataFrame())
val_real_yield = market_data.get('Real_Yield', pd.DataFrame())
val_tail_df = liquidity_df_mock 

# Current Values (Latest)
l2_sofr_spread = val_spread * 100 # to bps? No, logic uses % units in code?
# Logic in Prompt: 0.05% -> > 0.05.
# My `data['Spread']` is `SOFR - IORB`. If SOFR=5.35, IORB=5.40, Diff=-0.05.
# If SOFR=5.45, IORB=5.40, Diff=0.05.
# Prompt thresholds: > 0.05% (i.e. > 5bps if unit is yield point).
# So raw difference is correct.
cur_spread = val_spread 

# TNX Dev
cur_tnx_dev = 0.0
if not val_tnx_div.empty:
    cur_tnx_dev = val_tnx_div['Divergence'].iloc[-1]

# Real Yield
cur_real_yield = 0.0
if not val_real_yield.empty:
    cur_real_yield = val_real_yield['value'].iloc[-1]

# Tail
cur_tail = 0.0
if not val_tail_df.empty:
    # Get latest tail
    cur_tail = val_tail_df['Treasury_Tail'].iloc[-1]

# Evaluate
comp_stat, s_sofr, s_tnx, s_real, s_tail = evaluate_l2_status(cur_spread, cur_tnx_dev, cur_real_yield, cur_tail)

# Composite Panel
l2_meta = STATUS_MAP[comp_stat]
l2_msg_key = "JP" if lang == "日本語" else "EN"
st.markdown(f"""
<div class="judgment-panel {l2_meta['class']}" style="padding: 15px; margin-bottom: 20px;">
    {L2_MESSAGES['COMPOSITE'][comp_stat][l2_msg_key]}
</div>
""", unsafe_allow_html=True)

l2_c1, l2_c2, l2_c3, l2_c4 = st.columns(4)

chart_config = dict(
    paper_bgcolor='rgba(0,0,0,0)', 
    plot_bgcolor='rgba(0,0,0,0)', 
    height=200,
    margin=dict(l=0, r=0, t=10, b=0),
    font=dict(size=10)
)
date_cutoff = pd.Timestamp("2026-01-01")

def render_l2_card(col, title, status, msg_dict, fig):
    meta = STATUS_MAP[status]
    msg = msg_dict[status][l2_msg_key]
    with col:
        st.markdown(f"**{title}**")
        st.markdown(f"<span style='color:{meta['color']}'>{meta['icon']} {status}</span>", unsafe_allow_html=True)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("*No Data*")
        
        st.markdown(f"""
        <div style="font-size: 0.8rem; background: #f9f9f9; padding: 10px; border-radius: 5px; border-left: 3px solid {meta['color']};">
            {msg}
        </div>
        """, unsafe_allow_html=True)

# 1. SOFR vs IORB Trend
fig_1 = None
if val_rates_hist is not None and not val_rates_hist.empty:
    df = val_rates_hist[val_rates_hist['date'] >= date_cutoff]
    if not df.empty:
        fig_1 = px.line(df, x='date', y='SOFR')
        fig_1.add_trace(go.Scatter(x=df['date'], y=df['IORB'], name='IORB', line=dict(dash='dash', color='orange')))
        fig_1.update_layout(**chart_config, showlegend=False)

render_l2_card(l2_c1, "SOFR - IORB Spread", s_sofr, L2_MESSAGES['SOFR_IORB'], fig_1)

# 2. TNX Divergence
fig_2 = None
if val_tnx_div is not None and not val_tnx_div.empty:
    df = val_tnx_div[val_tnx_div['Date'] >= date_cutoff]
    if not df.empty:
        fig_2 = px.bar(df, x='Date', y='Divergence', color='Divergence', color_continuous_scale='RdYlGn_r')
        fig_2.update_layout(**chart_config)
        fig_2.update_coloraxes(showscale=False)

render_l2_card(l2_c2, "TNX 5MA Deviation", s_tnx, L2_MESSAGES['TNX_DEV'], fig_2)

# 3. Real Yield
fig_3 = None
if val_real_yield is not None and not val_real_yield.empty:
    df = val_real_yield[val_real_yield['date'] >= date_cutoff]
    if not df.empty:
        fig_3 = px.line(df, x='date', y='value')
        fig_3.update_traces(line_color='#9C27B0')
        fig_3.update_layout(**chart_config)

render_l2_card(l2_c3, "Real Yield (10Y TIPS)", s_real, L2_MESSAGES['REAL_YIELD'], fig_3)

# 4. Tail
fig_4 = None
if not val_tail_df.empty:
    # Filter Window: Cur Month +/- 3 months
    now = datetime.now()
    start_date = now - timedelta(days=90)
    end_date = now + timedelta(days=90)
    
    # Ensure Date column is valid
    val_tail_df = val_tail_df.dropna(subset=['Date'])
    
    # Filter
    df = val_tail_df[(val_tail_df['Date'] >= start_date) & (val_tail_df['Date'] <= end_date)].copy()
    
    if not df.empty:
        # Format Date to YYYY-MM string for categorical axis (removes Days visual)
        df['Month'] = df['Date'].dt.strftime('%Y-%m')
        
        fig_4 = px.bar(df, x='Month', y='Treasury_Tail')
        fig_4.update_traces(marker_color='#007BFF')
        fig_4.update_layout(
            **chart_config,
            xaxis=dict(type='category') # Ensure it treats YYYY-MM as categories
        )

render_l2_card(l2_c4, f"{TRANSLATIONS['tail_title'][lang]}", s_tail, L2_MESSAGES['TAIL'], fig_4)
