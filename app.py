import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import requests
import numpy as np
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

# --- Translations & Report Texts ---
MAIN_EXPLANATION = {
    "English": """
    Purpose of this Audit
    This dashboard monitors Structural Risks that price trends often mask. 
    It tracks the "physical" constraints of liquidity and credit transmission to detect hidden fractures before they manifest as a market crash.
    """,
    "日本語": """
    本監査の目的
    このダッシュボードは、株価のトレンドが隠蔽しがちな「構造的リスク」を監視します。
    流動性の物理的制約やクレジット市場からの波及経路を可視化し、市場崩壊として顕在化する前の「隠れた亀裂」を検知することを目的としています。
    """
}

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
        "English": "AI Physical Liquidity Core 5 (APLC-5) Audit",
        "日本語": "AI物理流動性コア5社（APLC-5）監査"
    },
    "l2_title": {
        "English": "Layer 2: Systemic Liquidity Friction Monitor",
        "日本語": "レイヤー2: システム流動性摩擦モニター"
    },
    "l1_desc": {
        "日本語": """
<b>AI物理流動性コア5社（APLC-5）</b>とは、AIインフラを支える上で最も大きな<b>物理的現金支払能力</b>を持ち、市場全体の流動性構造に決定的な影響を与える主要企業群を指す。
本監査では、各社の<b>フリーキャッシュフロー（FCF）</b>と、AIインフラの構築・維持に必要な<b>物理コスト</b>（設備投資、電力コスト増加分、送電網確保のための予約・担保費用）との関係を監視する。
これらの合計コストがFCFを上回り、<b>物理的支払能力指標（PSR）が1.0を下回る</b>場合、企業は自律的な資金循環を喪失し、<b>銀行の未使用融資枠など外部流動性への依存</b>を開始した状態と定義する。
これは、AIインフラ投資が金融システム全体の流動性を吸収し、市場を<b>構造的な流動性ストレス（構造的窒息）</b>へ導く初期の物理的兆候である。
""",
        "English": """
<b>AI Physical Liquidity Core 5 (APLC-5)</b> refers to the group of companies whose <b>physical cash-paying capacity</b> is most critical to sustaining AI infrastructure and whose investment behavior has a decisive impact on system-wide market liquidity.
This framework monitors the relationship between <b>free cash flow (FCF)</b> and the <b>physical costs required to build and maintain AI infrastructure</b>, including capital expenditures, rising electricity costs, and power-grid reservation or collateral fees.
When total physical costs exceed FCF and the <b>Physical Solvency Ratio (PSR) falls below 1.0</b>, firms are considered to have lost financial self-sufficiency and to be relying on <b>external liquidity</b>, such as unused bank credit commitments.
This condition is defined as an early physical signal that AI infrastructure investment is absorbing financial-system liquidity and pushing the market toward <b>structural liquidity stress</b>.
"""
    },
    "l2_desc": {
        "日本語": """
これらの指標は、金融システムの深層における<b>「準備金の過不足」と「資本の真の価格」</b>を直接的に示す4つの独立変数です。$SOFR - IORB$ スプレッド: 銀行間準備金の需給。$5bps$ 超過はシステム全体の摩擦を示唆。$TNX$ 5MA 乖離: 金利再設定の加速速度。実質金利 ($DFII10$): インフレ調整後の剥き出しの資本コスト。入札テール ($Auction\ Tail$): 公的債務の需要断絶とディーラーの受入限界。スプレッドが $5bps$ を超え、実質金利が急騰する状態は、流動性の土台が揺らぎ、市場が衝撃に対して極めて脆弱な<b>「砂上の楼閣」</b>と化しているサインです。テールの拡大と金利の加速は、バリュエーションの強制的な再設定を促す物理的トリガーとなります。
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
    },
    "sidebar_stress": {
        "English": "⚡ Physical Stress Test",
        "日本語": "⚡ 物理的ストレステスト"
    },
    "sidebar_fee": {
        "English": "Reserv. Fee ($/MW-day)",
        "日本語": "電力利用担保金 ($/MW-日)"
    },
    "defense": { "English": "Defense: ", "日本語": "防衛線: " },
    "flip": { "English": "Flip: ", "日本語": "フリップ: " },
    "target": { "English": "Target: ", "日本語": "目標: " },
    "limit": { "English": "Limit: ", "日本語": "限界: " },
    "spread_metric_label": { "English": "Spread (SOFR-IORB)", "日本語": "スプレッド (SOFR-IORB)" },
    "fcf_label": { "English": "FCF", "日本語": "FCF" },
    "burden_label": { "English": "Burden", "日本語": "物理コスト" },
    "capex_label": { "English": "CapEx", "日本語": "設備投資" },
    "elec_label": { "English": "Elec", "日本語": "電力代上昇" },
    "res_label": { "English": "Res", "日本語": "予約容量確保料" },
    "l2_sofr": { "English": "SOFR - IORB Spread", "日本語": "SOFR - IORB スプレッド" },
    "l2_tnx": { "English": "TNX 5MA Deviation", "日本語": "10年債金利 5MA乖離" },
    "l2_real": { "English": "Real Yield (10Y TIPS)", "日本語": "実質金利 (10年TIPS)" },
    "l2_real": { "English": "Real Yield (10Y TIPS)", "日本語": "実質金利 (10年TIPS)" },
    "no_data": { "English": "No Data", "日本語": "データなし" },
    
    # --- Quarterly Table Translations ---
    "quarter": { "日本語": "四半期", "English": "Quarter" },
    "net_income": { "日本語": "純利益（NI）", "English": "Net Income" },
    "ocf": { "日本語": "営業キャッシュフロー（OCF）", "English": "Operating Cash Flow" },
    "capex": { "日本語": "設備投資（CapEx）", "English": "Capital Expenditure" },
    "fcf": { "日本語": "フリーキャッシュフロー（FCF）", "English": "Free Cash Flow" },
    "capex_ni": { "日本語": "CapEx / 純利益", "English": "CapEx / Net Income" },
    "capex_ocf": { "日本語": "CapEx / OCF", "English": "CapEx / OCF" },
    "psr": { "日本語": "物理的ソルベンシー比率（PSR）", "English": "Physical Solvency Ratio (PSR)" },
    "capex_status": { "日本語": "CapEx 状態", "English": "CapEx Status" }
}

COLUMN_LABEL_MAP = {
    "Quarter": "quarter",
    "NetIncome": "net_income",
    "OperatingCashFlow": "ocf",
    "CapitalExpenditure": "capex",
    "FCF": "fcf",
    "CapEx_to_NI": "capex_ni",
    "CapEx_to_OCF": "capex_ocf",
    "PSR": "psr",
    "CapEx_Status": "capex_status"
}

CAPEX_STATUS_LABELS = {
    "HEALTHY": {
        "日本語": "健全（回収設計あり）",
        "English": "Healthy (Self-Recovering)"
    },
    "BOUNDARY": {
        "日本語": "境界（耐久力低下）",
        "English": "Boundary (Durability Erosion)"
    },
    "BLACK_HOLE": {
        "日本語": "ブラックホール（資金吸収）",
        "English": "Black Hole (Liquidity Sink)"
    }
}

CAPEX_HEALTH_LABELS = {
    "HEALTHY": {
        "日本語": "健全",
        "English": "Healthy"
    },
    "BOUNDARY": {
        "日本語": "境界（デッドクロス）",
        "English": "Boundary (Dead Cross)"
    },
    "BLACK_HOLE": {
        "日本語": "物理的ブラックホール",
        "English": "Physical Black Hole"
    }
}

CAPEX_HEALTH_DESC = {
    "HEALTHY": {
        "日本語": "CapExは利益および営業キャッシュフローで自律的に賄われており、健全な成長投資です。",
        "English": "CapEx is fully covered by earnings and operating cash flow, indicating healthy growth investment."
    },
    "BOUNDARY": {
        "日本語": "CapExが純利益または営業キャッシュフローを上回り始めており、デッドクロスの初期段階にあります。",
        "English": "CapEx has begun to exceed net income or operating cash flow, indicating an early-stage dead cross."
    },
    "BLACK_HOLE": {
        "日本語": "CapExと物理コストがキャッシュ創出能力を超過し、流動性を吸収する物理的ブラックホールに入りつつあります。",
        "English": "CapEx and physical costs exceed cash generation capacity, indicating entry into a physical liquidity black hole."
    }
}

def t_capex_health(key: str, lang: str) -> str:
    return CAPEX_HEALTH_LABELS.get(key, {}).get(lang, key)

def t_capex_desc(key: str, lang: str) -> str:
    return CAPEX_HEALTH_DESC.get(key, {}).get(lang, "")

def localize_quarterly_df(df, lang):
    renamed_cols = {
        col: TRANSLATIONS[COLUMN_LABEL_MAP[col]][lang]
        for col in df.columns
        if col in COLUMN_LABEL_MAP
    }
    return df.rename(columns=renamed_cols)



REPORTS = {
    "HEALTHY": {
        "日本語": """
<b>健全：業績相場（Earnings-Driven Equilibrium）</b>
現在の市場は強固な業績の盾に守られた理想的な均衡状態にあります。$SPX$ は $6,880$ の構造的防衛線を維持しており、$SOFR$ スプレッドも $5bps$ 未満と、銀行システム内の流動性は円滑に循環しています。
FANG+構成銘柄のキャッシュフロー（$FCF$）は巨大なAIインフラ投資（$CapEx$）を十分にカバーしており、銀行の未使用融資枠を占有することなく自律的な成長を継続しています。
この局面では、成長率（$g$）が資本コスト（$r$）を支配しており、物理的な制約（電力・与信・担保金）は業績の拡大によって吸収されています。
構造的断層のリスクは極めて低く、自社株買いが市場の流動性供給装置として正常に機能しています。ナラティブと物理的事実の乖離は最小限であり、監査上の決壊兆候は検出されていません。

<b>構造的留意事項</b>
*   <b>マクロ指標の変節に対する感度</b>：良好な業績データの裏側で、$SOFR$ スプレッドの微増や入札テールの発生といった「初期の摩擦」が、構造的均衡を崩す可能性を常に監視すること。
*   <b>リスクシナリオの継続的検証</b>：均衡状態の継続中であっても、3月の断層に向けた物理的制約の蓄積状況について、客観的なデータに基づいた検証を怠らないこと。
""",
        "English": """
<b>Health: Earnings-Driven Equilibrium</b>
The market currently resides in an ideal equilibrium, fortified by a robust Earnings Shield. The $SPX$ maintains its structural defense line at $6,880$, while the $SOFR$ spread remains below $5bps$, indicating a smooth circulation of liquidity within the banking system.
Free Cash Flow ($FCF$) among FANG+ constituents sufficiently covers massive AI infrastructure investments ($CapEx$), allowing for autonomous growth without encroaching upon unused bank credit lines.
In this phase, the growth rate ($g$) dominates the cost of capital ($r$), and physical constraints—such as power, credit, and collateral requirements—are being absorbed by expanding earnings.
The divergence between narrative and physical reality remains minimal, and no structural fracture points have been detected. The Buyback mechanism functions effectively as a liquidity provision device for the market.

<b>Structural Observations</b>
*   <b>Sensitivity to Macro Shifts</b>: Even during strong earnings cycles, maintain vigilance for "initial friction," such as subtle increases in the $SOFR$ spread or Treasury auction tails, which may signal a shift in structural equilibrium.
*   <b>Continuous Validation of Risk Scenarios</b>: Persist in verifying the accumulation of physical constraints leading into the March "Structural Fault," ensuring that assessments are grounded in objective data rather than prevailing optimism.
"""
    },
    "WARNING": {
        "日本語": """
<b>警告：ナラティブ延命（Narrative-Driven Friction）</b>
市場構造に物理的摩擦が顕在化しています。株価指数は $6,880$ の境界線上で推移していますが、<b>限界的準備金の減少（$SOFR$ 上昇）</b> により、流動性の供給能力が低下しつつあります。
現在の価格水準を支えているのは実体的な流動性ではなく、ナラティブ（期待）による浮力です。FANG+各社の $CapEx$ 増大が銀行の与信枠を占有し始めており、限界的な貸出余力が低下する「資本の石化」が進行しています。
3月の借換需要（企業の壁）に向けた負のエネルギーが蓄積されており、自社株買いの執行速度が物理的コストの増大に追いつかなくなるリスクを示唆しています。
業績の盾は摩耗し始めており、僅かな物理的ショックが断層の引き金となる臨界点にあります。価格の推移よりも流動性の質の監視を優先すべき局面であり、均衡が崩れる前兆を捉えることが監査の主目的となります。

<b>構造的留意事項</b>
*   <b>流動性指標の優先</b>：価格の維持に関わらず、流動性指標が悪化した状態では構造的な脆弱性が高まっている事実を認識し、リスク許容度の再評価を行うこと。
*   <b>個別銘柄の耐久性乖離</b>：FANG+内でも $FCF/CapEx$ 比率が悪化した銘柄と健全な銘柄の「耐久性の差」を精査し、セクター一括の楽観視を避けること。
""",
        "English": """
<b>Warning: Narrative-Driven Friction</b>
Physical friction is becoming manifest within the market structure. While the price index hovers near the $6,880$ boundary, a reduction in marginal reserves ($SOFR$ spike) indicates a declining capacity for liquidity provision.
Current price levels are being sustained by narrative-driven buoyancy rather than substantive liquidity. Increasing $CapEx$ from FANG+ firms is beginning to occupy bank credit lines, leading to a "petrification of capital" and a decrease in marginal lending capacity.
Negative energy is accumulating toward the March refinancing cycle (The Corporate Wall), suggesting a risk that the velocity of share buybacks may fail to keep pace with rising physical costs.
The Earnings Shield is beginning to wear thin, and the market is at a critical threshold where minor physical shocks could trigger a structural fault. In this phase, monitoring the quality of liquidity must take precedence over tracking price movements.

<b>Structural Observations</b>
*   <b>Prioritization of Liquidity Metrics</b>: Recognize that structural vulnerability remains high when liquidity metrics deteriorate, regardless of price stability. Re-evaluate risk tolerances based on liquidity flow rather than index levels.
*   <b>Divergence in Constituent Durability</b>: Scrutinize the "durability gap" among FANG+ members—specifically the $FCF/CapEx$ ratio of individual firms—and avoid treating the sector as a monolithic entity.
"""
    },
    "CRITICAL": {
        "日本語": """
<b>決壊：構造的崩壊（Structural Collapse Phase）</b>
構造的決壊が確認されました。$SPX$ が $6,880$ を割り込み、あるいは FANG+ が $11,820$ のガンマ・フリップ・ポイントを突破したことで、市場は自己増幅的な下落フェーズに突入しています。
業績の盾は物理的コスト（金利・電力・与信）の激増によって粉砕され、自社株買いによる価格維持能力は大幅に低下しています。銀行準備金の枯渇により、マーケットメーカーのヘッジ行動が価格変動を増幅させる「負のフィードバック」が発生しています。
もはや価格を支える構造的根拠は極めて限定的となり、$5,300$ が次の均衡点として統計的に有力な領域に入りました。
全てのナラティブは棄却され、物理的な支払能力と流動性の絶対量のみが市場を支配する強制的な価格再設定の局面です。救済措置としての期待は「インフレの物理的粘着性」によって遮断されており、期待に基づいた判断は機能しにくい状態にあります。

<b>構造的留意事項</b>
*   <b>客観的接地帯の確認</b>：均衡点（$5,300$）への接地と流動性の回復が数値（$SOFR$ 等）で確認されるまで、根拠のない価格反転を前提とした予断を持たないこと。
*   <b>事実に基づいた状況判断</b>：特定の政治的・経済的ニュースによる希望的観測を排し、目の前の「価格と流動性の乖離」という物理的事実のみを判断の基軸とすること。
""",
        "English": """
<b>Critical: Structural Collapse Phase</b>
A structural collapse has been confirmed. The $SPX$ has breached the $6,880$ defense line, or the $NYFANG$ has crossed the Gamma Flip Point at $11,820$, plunging the market into a self-reinforcing downward phase.
The Earnings Shield has been shattered by a surge in physical costs (interest, power, and credit), and the capacity for price maintenance via buybacks has significantly diminished. The exhaustion of bank reserves has triggered a "negative feedback loop," with market maker hedging activity amplifying price volatility.
Structural justifications for current price levels are now extremely limited, and $5,300$ has entered the zone of statistical probability as the next equilibrium point. All narratives have been rejected, and the market is in a phase of forced price resetting, dominated solely by physical solvency and the absolute volume of liquidity.
Expectations for policy relief are obstructed by "physical inflation stickiness," rendering narrative-based judgments ineffective.

<b>Structural Observations</b>
*   <b>Verification of Objective Grounding</b>: Avoid making assumptions about price reversals until an objective grounding at the equilibrium point ($5,300$) and a recovery in liquidity ($SOFR$, etc.) are confirmed by data.
*   <b>Fact-Based Situational Assessment</b>: Disregard any hopeful speculation driven by political or economic news. Decisions should be anchored exclusively in the physical reality of the "price-liquidity gap."
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
        
        
        /* Judgment Panel */
        .judgment-panel {
            background-color: #FFFFFF;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin-bottom: 25px;
        }
        
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

        /* Equal Height Columns Fix (Flexbox) - Final CSS Only Version */
        
        /* Ensure the row stretches its columns */
        [data-testid="stHorizontalBlock"] {
            align-items: stretch;
        }
        
        /* Ensure columns are flex containers */
        [data-testid="column"] {
            display: flex;
            flex-direction: column; 
        }
        
        /* The vertical block inside column should grow */
        [data-testid="column"] > div[data-testid="stVerticalBlock"] {
             flex: 1;
             display: flex;
             flex-direction: column;
        }
        
        /* 
           Target ONLY the element containers that hold our cards.
           We use :has(.metric-card) to be specific so we don't stretch graphs or text.
        */
        div.element-container:has(.metric-card) {
             flex: 1;
             display: flex;
             flex-direction: column;
        }
        
        div.element-container:has(.metric-card) > div.stMarkdown,
        div[data-testid="stMarkdownContainer"]:has(.metric-card) {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100%;
        }
        
        div[data-testid="stMarkdownContainer"]:has(.metric-card) > p {
            flex: 1;
            display: flex;
            flex-direction: column;
            height: 100%;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Card Styles */
        .metric-card {
            background-color: #FFFFFF;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.03);
            border: 1px solid #EAEAEA;
            transition: transform 0.2s;
            margin-bottom: 15px !important;
            
            /* Sizing */
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            flex-grow: 1; 
            height: 100%; 
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        .warning-card {
            border-left: 5px solid #FF4B4B !important;
        }

        /* Hide Streamlit Header/Footer */
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

@st.cache_data(ttl=3600)
def build_capex_audit_from_yf(tickers):
    """
    yfinance の quarterly_income_stmt / quarterly_cashflow から
    直近四半期の Net Income / OCF / CapEx を自動取得して
    CapEx監査用の DataFrame を返す。
    """
    rows = []
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            inc_q = tk.quarterly_income_stmt
            cf_q  = tk.quarterly_cashflow

            if inc_q is None or cf_q is None or inc_q.empty or cf_q.empty:
                continue

            # 最新四半期（列0が一番新しい前提）
            period = inc_q.columns[0]

            # --- Net Income ---
            ni_candidates = [
                "Net Income",
                "NetIncome",
                "Net Income Common Stockholders",
            ]
            net_income = None
            for idx_name in ni_candidates:
                if idx_name in inc_q.index:
                    net_income = inc_q.loc[idx_name, period]
                    break

            # --- Operating Cash Flow ---
            ocf_candidates = [
                "Total Cash From Operating Activities",
                "Cash From Operating Activities",
                "Operating Cash Flow",
            ]
            ocf = None
            for idx_name in ocf_candidates:
                if idx_name in cf_q.index:
                    ocf = cf_q.loc[idx_name, period]
                    break

            # --- CapEx ---
            capex_candidates = [
                "Capital Expenditure",
                "Capital Expenditures",
                "Investment In Property, Plant, and Equipment",
            ]
            capex = None
            for idx_name in capex_candidates:
                if idx_name in cf_q.index:
                    capex = cf_q.loc[idx_name, period]
                    break

            if net_income is None and ocf is None and capex is None:
                continue

            rows.append({
                "Ticker": t,
                "Period": str(period).split()[0], # YYYY-MM-DD format
                "NI_Q": float(net_income) if net_income is not None else np.nan,
                "OCF_Q": float(ocf) if ocf is not None else np.nan,
                "CapEx_Q": float(capex) if capex is not None else np.nan,
            })

        except Exception as e:
            # st.warning(f"[CapEx audit] Error fetching {t}: {e}")
            continue

    if not rows:
        return pd.DataFrame(columns=["Ticker", "Period", "NI_Q", "OCF_Q", "CapEx_Q"])

    return pd.DataFrame(rows)


def classify_capex_health(row):
    psr = row.get("PSR", np.nan)
    c_ni = row.get("CapEx_to_NI", np.nan)
    c_ocf = row.get("CapEx_to_OCF", np.nan)

    # 物理的なブラックホール：
    # PSR < 1.0 かつ CapEx が利益 or OCF を食い潰している
    if (not np.isnan(psr) and psr < 1.0) and (
        (not np.isnan(c_ni) and c_ni > 1.0) or
        (not np.isnan(c_ocf) and c_ocf > 1.0)
    ):
        return "BLACK_HOLE"

    # Dead Cross が出ているが PSR > 1.0 → 境界域
    if ((not np.isnan(c_ni) and c_ni > 1.0) or
        (not np.isnan(c_ocf) and c_ocf > 1.0)):
        return "BOUNDARY"

    # それ以外はとりあえず健全
    return "HEALTHY"


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

# Session removed - relying on standard yfinance with delay
import time

@st.cache_data(ttl=3600)
def get_live_metrics_v2():
    # FANG Metrics
    tickers = ["META", "AMZN", "NFLX", "GOOGL", "MSFT", "AAPL", "NVDA", "TSLA", "SNOW", "AVGO", "AMAT", "LRCX", "KLAC", "ASML", "TER"]
    rows = []
    for t in tickers:
        try:
            time.sleep(0.2) # Avoid Rate Limit
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
        except Exception as e:
            st.warning(f"Error fetching {t}: {e}")
            rows.append({"Ticker": t, "Price": 0, "FCF": 0, "CapEx": 0})
    return pd.DataFrame(rows)

@st.cache_data(ttl=3600)
def get_market_data_fred_yfinance_v2():
    data = {}
    try:
        time.sleep(0.2)
        spx = yf.Ticker("^GSPC").history(period="1d")
        data['SPX'] = float(spx['Close'].iloc[-1]) if not spx.empty else 6900.0
        
        time.sleep(0.2)
        nyfang = yf.Ticker("^NYFANG").history(period="1d")
        data['NYFANG'] = float(nyfang['Close'].iloc[-1]) if not nyfang.empty else 12000.0
    except Exception as e:
        st.warning(f"Error fetching SPX/FANG: {e}")
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
        data['SOFR_Date'] = sofr_latest[0]['date'] if sofr_latest else "-"
        data['IORB_Date'] = iorb_latest[0]['date'] if iorb_latest else "-"
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
        time.sleep(0.2)
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
        data['SOFR_Date'] = "-"
        data['IORB_Date'] = "-"
        data['Spread'] = -0.10
        data['Rates_History'] = pd.DataFrame()
        data['Real_Yield'] = pd.DataFrame()
        data['TNX_Div'] = pd.DataFrame()

    return data

# --- Helper: Price Series Fetcher for Credit Panel ---

@st.cache_data(ttl=3600)
def fetch_price_series(tickers, days=120):
    """
    Simple wrapper around yfinance for multiple tickers.
    Returns Adjusted Close DataFrame for the past `days`.
    """
    if isinstance(tickers, str):
        tickers = [tickers]
    end = datetime.today()
    start = end - timedelta(days=days)
    try:
        # Avoid Rate Limit
        time.sleep(0.3)
        data = yf.download(tickers, start=start, end=end, progress=False)
        
        # Access 'Adj Close' or 'Close' (Handling updated yfinance structure)
        if 'Adj Close' in data:
            df_price = data['Adj Close']
        elif 'Close' in data:
            df_price = data['Close']
        else:
             return pd.DataFrame()

        if isinstance(df_price, pd.Series):
            df_price = df_price.to_frame()
            
        return df_price.dropna(how="all")
    except Exception as e:
        st.warning(f"Price fetch error: {e}")
        return pd.DataFrame()

# --- Helper: HY OAS from FRED (ICE BofA US High Yield OAS) ---

@st.cache_data(ttl=3600)
def fetch_hy_oas_series(series_id="BAMLH0A0HYM2", limit=365):
    """
    Fetch HY OAS series from FRED.
    Returns DataFrame with columns: ['date', 'value'].
    """
    url = (
        "https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={series_id}"
        f"&api_key={FRED_API_KEY}"
        "&file_type=json&sort_order=asc"
        f"&limit={limit}"
    )
    try:
        r = requests.get(url)
        r.raise_for_status()
        js = r.json()
        obs = js.get("observations", [])
        if not obs:
            return pd.DataFrame()
        df = pd.DataFrame(obs)
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df.dropna(subset=['value'])
        return df[['date', 'value']]
    except Exception as e:
        st.warning(f"HY OAS fetch error: {e}")
        return pd.DataFrame()

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
metrics_df = get_live_metrics_v2()
market_data = get_market_data_fred_yfinance_v2()
liquidity_df_mock = load_mock_liquidity()

def get_config_val(key, default=0):
    try:
        val = config_df.loc[config_df['Key'] == key, 'Value'].iloc[0]
        return float(val)
    except:
        return default

# --- Logic ---
# Global Logic for Layout Control removed as requested.




STATUS_MAP = {
    "HEALTHY": {"color": "#28A745", "icon": "🟢", "class": "panel-healthy"},
    "WARNING": {"color": "#FFC107", "icon": "🟡", "class": "panel-warning"},
    "CRITICAL": {"color": "#DC3545", "icon": "🔴", "class": "panel-critical"}
}


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

# Purpose Explanation (Moved here)
st.markdown(MAIN_EXPLANATION['日本語' if lang == '日本語' else 'English'])


# Global Judgment Panel and Metrics Strip Removed
# --- Tab Layout ---
st.markdown('<div style="margin-bottom: 10px;"></div>', unsafe_allow_html=True)
tab_titles = {
    "English": ["APLC-5 Audit", "Liquidity Friction", "Transmission Monitor", "Danger Source", "Survivor Map"],
    "日本語": ["APLC-5 監査", "流動性摩擦", "伝播モニター", "危険源モニター", "Survivor マップ"]
}
tabs = st.tabs(tab_titles[lang])

with tabs[0]:
    # Layer 1
    st.subheader(TRANSLATIONS['l1_title'][lang])
    st.markdown(TRANSLATIONS['l1_desc'][lang], unsafe_allow_html=True)

    # --- Layer 1 Messages ---
    L1_MESSAGES = {
        "HEALTHY": {
            "JP": "🟢 <b>健全 (自律的均衡)</b>\n企業のキャッシュ生成能力（$FCF$）がAIインフラ投資（$CapEx$）を十分に凌駕しています。外部の銀行与信に依存することなく投資と株主還元を両立できる「業績の盾」が強固に機能しており、構造的均衡は維持されています。",
            "EN": "🟢 <b>DURABLE (Autonomous Equilibrium)</b>\nCorporate cash generation ($FCF$) sufficiently exceeds AI infrastructure investment ($CapEx$). The 'Earnings Shield' is functioning robustly, enabling both investment and shareholder returns without reliance on external bank credit. Structural equilibrium remains intact."
        },
        "WARNING": {
            "JP": "🟡 <b>警告 (耐久性の摩擦)</b>\n投資コストの増大によりキャッシュ余力が急速に低下しています。自律的な資金循環の限界点（$1.0$）に接近しており、僅かな収益悪化やコスト増が「銀行融資枠の占有」を引き起こすリスクが高まっています。",
            "EN": "🟡 <b>STRAINED (Friction in Durability)</b>\nIncreasing investment costs are rapidly depleting cash buffers. The metrics are approaching the threshold of fiscal autonomy ($1.0$). High risk remains that any minor earnings deterioration or cost spike will trigger a 'seizure of bank credit lines.'"
        },
        "CRITICAL": {
            "JP": "🔴 <b>決壊 (自律性の喪失と窒息)</b>\n物理的投資コストがキャッシュ生成能力を突破しました。企業は自律性を失い、不足分を銀行の「未使用融資枠」に依存し始めています。これはシステム全体の準備金を占有し、市場を構造的窒息へ導く物理的な決壊サインです。",
            "EN": "🔴 <b>BROKEN (Loss of Autonomy & Suffocation)</b>\nPhysical investment costs have breached cash-generating capacity. Firms have lost fiscal autonomy and begun relying on 'Unused Bank Commitments.' This signifies a physical rupture, where systemic reserves are drained, leading the market toward structural suffocation."
        }
    }

    # --- New Data Source: Physical Metrics ---
    PHYSICAL_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRgul7PbiP2EYy8KiPmMglhd2R-oXTriikeZCZxQHKtrxLgbwJyEiGuprBsdAEDMR_F2te9E2GQRTYb/pub?output=csv"

    @st.cache_data(ttl=3600)
    def load_physical_metrics():
        try:
            df = pd.read_csv(PHYSICAL_SHEET_URL)
            # Rename Japanese columns to internal English keys
            # 銘柄 (Ticker), 電力総使用量 (Annual TWh), 電力上昇単価 (Δ$/MWh), 予約費用単価 (加重 $/MW-day), ...
            col_map = {
                "銘柄 (Ticker)": "Ticker_Raw",
                "電力総使用量 (Annual TWh)": "TWh",
                "電力上昇単価 (Δ$/MWh)": "Price_Delta",
                "予約費用単価 (加重 $/MW-day)": "Res_Fee_Unit"
            }
            # Check if columns exist (sometimes names vary slightly)
            df_cols = df.columns.tolist()
            # Simple mapping by index if names are tricky, but let's try strict first or soft match
            # Let's map by likely position if standard map fails? 
            # Actually, let's just rename based on known Japanese headers provided in inspection.
            
            # Clean specific chars like $, \n etc if needed, but CSV usually handles cleanly.
            # But wait, Ticker_Raw is "Amazon (AMZN)". Need to extract AMZN.
            
            df_clean = pd.DataFrame()
            # Find column checking
            for c in df.columns:
                if "Ticker" in c: col_map[c] = "Ticker_Raw"
                elif "TWh" in c: col_map[c] = "TWh"
                elif "Δ$/MWh" in c: col_map[c] = "Price_Delta"
                elif "MW-day" in c: col_map[c] = "Res_Fee_Unit"
                
            df = df.rename(columns=col_map)
            
            # Extract Ticker
            df['Ticker'] = df['Ticker_Raw'].apply(lambda x: x.split('(')[-1].replace(')', '').strip() if '(' in str(x) else str(x))
            
            # Clean numeric columns (remove $, +, etc)
            def clean_num(x):
                if isinstance(x, str):
                    return float(x.replace('$','').replace('+','').replace(',',''))
                return float(x)
                
            df['TWh'] = df['TWh'].apply(clean_num)
            df['Price_Delta'] = df['Price_Delta'].apply(clean_num)
            df['Res_Fee_Unit'] = df['Res_Fee_Unit'].apply(clean_num)
            
            return df[['Ticker', 'TWh', 'Price_Delta', 'Res_Fee_Unit']]
        except Exception as e:
            st.error(f"Physical Data Load Error: {e}")
            # Fallback empty or local
            try:
                 df = pd.read_csv("data/Physical_Metrics.csv")
                 # Apply same logic... (omitted for brevity, assume similar structure or handle basic)
                 # Basic rename
                 df = df.rename(columns={df.columns[0]:"Ticker_Raw", df.columns[1]:"TWh", df.columns[2]:"Price_Delta", df.columns[3]:"Res_Fee_Unit"})
                 df['Ticker'] = df['Ticker_Raw'].apply(lambda x: x.split('(')[-1].replace(')', '').strip() if '(' in str(x) else str(x))
                 return df
            except:
                 return pd.DataFrame()

    physical_df = load_physical_metrics()

    # Merge Physical with Financials
    metrics_df = pd.merge(metrics_df, physical_df, on='Ticker', how='left')
    # Fill NaNs for physics with 0
    metrics_df[['TWh', 'Price_Delta', 'Res_Fee_Unit']] = metrics_df[['TWh', 'Price_Delta', 'Res_Fee_Unit']].fillna(0)

    # --- Logic: Calculate PSR ---
    # PSR = FCF / (CapEx + Delta_Elec + Res_Fee)
    # Delta_Elec = TWh * 1,000,000 * Price_Delta
    # Res_Fee = (Wait, prompt said: "Capacity (MW) * Unit Price * 365")
    # BUT, the CSV does NOT have "Capacity (MW)". 
    # The CSV has "TWh". 
    # Ah, the PROMPT said "Reservation_Fee Calculation: Estimated Contract Capacity (MW) * ...".
    # But the CSV inspection shows columns: Ticker, TWh, Price Delta, Res Fee Unit. 
    # It MISSES "Capacity (MW)".
    # HOWEVER, TWh and Capacity are related. Capacity (MW) ~= (TWh * 1e6) / (8760 * Utilization).
    # OR check if I missed a column?
    # The user prompted "Data Source ...". I viewed it. It has "Ticker, TWh, Delta$, ResFee$, MainCause".
    # NO Capacity MW column.
    # I will Infer Capacity? Or is there a default logic?
    # "Reservation_Fee (予約費用): 推定契約容量 (MW) * ... "
    # Let's ESTIMATE MW from TWh assuming Data Center load factor (e.g. 90% or 100% flat?).
    # MW = (TWh * 1,000,000) / (24 * 365). 
    # Let's use that for now to complete the logic.

    def calc_psr_row(row):
        fcf = row['FCF']
        capex = abs(row['CapEx']) # Ensure positive
        
        # Physics
        twh = row['TWh']
        p_delta = row['Price_Delta']
        res_unit = row['Res_Fee_Unit']
        
        # 1. Delta Electricity Cost
        # TWh * 1,000,000 (MWh) * Price Delta
        delta_elec_cost = twh * 1_000_000 * p_delta
        
        # 2. Reservation Fee
        # MW = (TWh * 1e6) / 8760 (Assuming 100% Load Factor)
        est_mw = (twh * 1_000_000) / 8760
        
        # Fee = MW * UnitPrice * 365
        res_fee_cost = est_mw * res_unit * 365
        
        # Total Physical Burden
        burden = capex + delta_elec_cost + res_fee_cost
        
        psr = fcf / burden if burden > 0 else 0
        return psr, delta_elec_cost, res_fee_cost, burden

    # Apply
    metrics_df[['PSR', 'Cost_Elec', 'Cost_Res', 'Total_Burden']] = metrics_df.apply(lambda r: pd.Series(calc_psr_row(r)), axis=1)


    # --- APLC-5 Specific Logic ---
    APLC5_TICKERS = ["AMZN", "MSFT", "GOOGL", "META", "NVDA"]
    SURVIVOR_UNIVERSE = ["AMAT", "LRCX", "KLAC", "ASML", "TER"]

    # Filter for APLC-5 (Delayed to after Calculation to capture Survivor Data)
    # metrics_df = metrics_df[metrics_df['Ticker'].isin(APLC5_TICKERS)].copy()

    # Sensitivity Slider (Placed in Sidebar)
    with st.sidebar:
        st.divider()
        st.markdown(f"### {TRANSLATIONS['sidebar_stress'][lang]}")
        # Default to PJM approx ($315)
        global_res_fee = st.slider(TRANSLATIONS['sidebar_fee'][lang], 0.0, 1000.0, 315.0, 5.0, help="Adjust PJM/Global capacity reservation costs")

        
        # Delta Price Slider (Optional, but good for sensitivity)
        # global_price_delta = st.slider("Elec. Price Delta ($/MWh)", 0.0, 100.0, 30.0) 
        # For now, just Fee as requested.

    # --- PSR Calculation with Sensitivity ---
    def calc_psr_row(row, override_fee):
        fcf = row['FCF']
        capex = abs(row['CapEx']) 
        
        # Physics
        twh = row['TWh']
        p_delta = row['Price_Delta']
        
        # Use Slider Value for Sensitivity (Global Stress)
        # Or keep individual if slider is at "default"? 
        # Prompt says: "When PJM price is manipulated... 5 companies fluctuate".
        # This implies using the slider value as the active unit price.
        res_unit = override_fee
        
        # 1. Delta Electricity Cost
        delta_elec_cost = twh * 1_000_000 * p_delta
        
        # 2. Reservation Fee
        # MW = (TWh * 1e6) / 8760
        est_mw = (twh * 1_000_000) / 8760
        
        # Fee = MW * UnitPrice * 365
        res_fee_cost = est_mw * res_unit * 365
        
        # Total Physical Burden
        burden = capex + delta_elec_cost + res_fee_cost
        
        psr = fcf / burden if burden > 0 else 0
        return psr, delta_elec_cost, res_fee_cost, burden

    # Apply Calculation
    metrics_df[['PSR', 'Cost_Elec', 'Cost_Res', 'Total_Burden']] = metrics_df.apply(
        lambda r: pd.Series(calc_psr_row(r, global_res_fee)), axis=1
    )

    # --- Split Dataframes ---
    # Save Full/Survivor data
    survivor_df = metrics_df[metrics_df['Ticker'].isin(SURVIVOR_UNIVERSE)].copy()

    # Filter for APLC-5 (Restoring original variable for downstream APLC cards)
    metrics_df = metrics_df[metrics_df['Ticker'].isin(APLC5_TICKERS)].copy()

    # --- CapEx Audit Integration ---
    capex_audit_df = build_capex_audit_from_yf(APLC5_TICKERS)
    metrics_df = pd.merge(metrics_df, capex_audit_df, on="Ticker", how="left")

    # Metrics Calc (Defense against NaN)
    metrics_df["CapEx_to_NI"] = np.where(metrics_df["NI_Q"].abs() > 0, metrics_df["CapEx_Q"].abs() / metrics_df["NI_Q"].abs(), np.nan)
    metrics_df["CapEx_to_OCF"] = np.where(metrics_df["OCF_Q"].abs() > 0, metrics_df["CapEx_Q"].abs() / metrics_df["OCF_Q"].abs(), np.nan)

    metrics_df["CapExHealth"] = metrics_df.apply(classify_capex_health, axis=1)


    # --- APLC-5 Status Definitions ---
    APLC_MESSAGES = {
        "LEVEL_1": {
            "PSR": "> 1.4",
            "Color": "#28A745", # Green
            "Title_EN": "Structural Safety Zone",
            "Title_JP": "構造的安全域",
            "JP": "物理的自律性が極めて高い状態です。事業が生み出す現金が、巨額の設備投資（CapEx）のみならず、激しい電気代上昇や、送電網確保のための電力利用担保金（Reservation Fee）を支払ってもなお、40%以上の余力を残しています。外部資金や銀行与信に頼ることなく、自社の力だけでAI革命を継続できる唯一の領域です。エネルギー市場のボラティリティを完全に遮断できる「物理的な盾」を保持しています。",
            "EN": "High physical autonomy. Cash generation remains robust enough to absorb massive CapEx, electricity cost increases, and capacity reservation fees while maintaining a 40% buffer. These firms can sustain the AI revolution without credit dependency. This zone represents the ultimate 'Physical Shield,' where structural resilience allows the entity to withstand extreme volatility in energy markets and financial shocks."
        },
        "LEVEL_2": {
            "PSR": "1.1 - 1.4",
            "Color": "#FFC107", # Yellow
            "Title_EN": "Alert Zone",
            "Title_JP": "警戒域",
            "JP": "収益性は高いものの、インフラコストの膨張が「物理的な盾」を削り取っています。設備投資の規模に対し、予想を超える電気代上昇や電力利用担保金がキャッシュフローを侵食し、安全域が縮小しています。物理的な裏付けが薄まり、株価の正当化が「期待（ナラティブ）」に依存し始めるフェーズです。わずかなコスト増で下位ランクへ転落する脆弱性を孕んでおり、資本の自由度が物理的制約によって奪われ始めています。",
            "EN": "Profitability is intact, but rising infrastructure costs are thinning the 'Physical Shield.' Expanding CapEx combined with unforeseen electricity cost increases and capacity reservation fees are eroding cash flow margins. As physical backing weakens, valuation logic begins to shift toward narrative dependency. This zone indicates a vulnerability where even minor cost spikes can trigger a transition to the Pre-Fracture Zone as physical limits restrict capital flexibility."
        },
        "LEVEL_3": {
            "PSR": "1.0 - 1.1",
            "Color": "#FD7E14", # Orange
            "Title_EN": "Pre-Fracture Zone",
            "Title_JP": "破断準備域",
            "JP": "物理的限界が目前に迫り、外部与信（借金）への依存が不可避となる段階です。稼ぎ出す現金が、設備投資と電気代上昇・電力利用担保金の支払いでほぼ枯渇しています。この状態では、自社株買いの停止や格付けの再評価が現実味を帯びます。「強者」が物理コストによって「与信依存」に転じる臨界点であり、金融市場全体の流動性が低下した瞬間に、インフラ拡張が停止するリスクを内包した断層の境界線です。",
            "EN": "Physical limits are imminent, making credit dependency mandatory. Cash flow is almost entirely consumed by CapEx, electricity cost increases, and capacity reservation fees. At this juncture, share buybacks may cease, and credit rating reassessment becomes a reality. This is the critical tipping point where 'Strong Entities' become debt-dependent due to physical costs, creating a fault line where any tightening of market liquidity could freeze infrastructure expansion."
        },
        "LEVEL_4": {
            "PSR": "< 1.0",
            "Color": "#DC3545", # Red
            "Title_EN": "Physical Deficit Zone",
            "Title_JP": "物理的赤字域",
            "JP": "構造的破綻。AIを稼働させるための電気代と電力利用担保金、そして継続的な設備投資が、稼ぎ出す現金を上回る「逆ざや」が発生しています。もはやAIは利益を生む資産ではなく、市場全体の流動性を吸い上げる「物理的負債」と化しています。この現金の消失は、金融システムを窒息させる断層となり、ナラティブでは決して解決できない「物理的な死」を予見させます。システム全体の決壊の起点となる最悪のステータスです。",
            "EN": "Structural collapse. A 'physical deficit' has emerged where the electricity costs, reservation fees, and continuous CapEx required to sustain AI exceed cash generation. AI has transformed from a profit-generating asset into a 'physical liability' that drains global market liquidity. This evaporation of cash creates a systemic fracture that suffocates the financial system, signaling a 'Physical Death' that no narrative can rectify. This is the ultimate red line of systemic failure."
        }
    }

    def get_psr_level(psr):
        if psr > 1.4: return "LEVEL_1"
        elif psr >= 1.1: return "LEVEL_2"
        elif psr >= 1.0: return "LEVEL_3"
        else: return "LEVEL_4"

    # --- Main Indicator: Minimum PSR ---
    min_psr_row = metrics_df.loc[metrics_df['PSR'].idxmin()]
    min_psr_val = min_psr_row['PSR']
    min_psr_ticker = min_psr_row['Ticker']
    min_level_key = get_psr_level(min_psr_val)
    min_level_data = APLC_MESSAGES[min_level_key]

    l1_msg_key = "JP" if lang == "日本語" else "EN"
    title_key = f"Title_{l1_msg_key}"

    # Labels based on lang
    label_weakest = "APLC-5 Minimum PSR (Weakest Link)" if lang == "English" else "APLC-5 最低PSR (最弱リンク)"
    label_psr = "Physical Solvency Ratio" if lang == "English" else "物理的ソルベンシー比率"


    # Display Main Indicator
    st.markdown(f"""
    <div class="judgment-panel" style="border-top: 4px solid {min_level_data['Color']}; padding: 25px;">
        <div style="font-size: 1rem; color: #666; font-weight: bold; text-transform: uppercase; margin-bottom: 5px;">
            {label_weakest}
        </div>
        <div style="display: flex; align-items: baseline; gap: 15px;">
            <div style="font-size: 3.5rem; font-weight: 800; color: {min_level_data['Color']}; line-height: 1;">
                {min_psr_val:.2f}
            </div>
            <div style="font-size: 1.5rem; font-weight: 600; color: #333;">
                {min_psr_ticker}
            </div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {min_level_data['Color']};">
                {min_level_data[title_key]}
            </div>
        </div>
        <div style="margin-top: 15px; font-size: 1rem; line-height: 1.6;">
            {min_level_data[l1_msg_key]}
        </div>
    </div>
    """, unsafe_allow_html=True)






    # Cards (Fixed Loop Bug: use reset_index to ensure 0-based idx for columns)
    cols = st.columns(len(metrics_df)) 
    for idx, row in metrics_df.reset_index(drop=True).iterrows():
        ticker = row['Ticker']
        price = row['Price']
        psr = row['PSR']
        fcf = row['FCF']
        burden = row['Total_Burden']
        
        capex = abs(row['CapEx'])
        c_elec = row['Cost_Elec']
        c_res = row['Cost_Res']
        

        # --- CapEx Health Logic (UI) ---
        health = row.get("CapExHealth", "HEALTHY")
        health_color_map = {
            "HEALTHY": "#28A745",
            "BOUNDARY": "#FFC107",
            "BLACK_HOLE": "#DC3545"
        }
        health_color = health_color_map.get(health, "#6c757d")
        
        # Translate status
        health_label = t_capex_health(health, lang)
        health_desc  = t_capex_desc(health, lang)
        status_title = "CapEx Status:" if lang == "English" else "CapEx 状態:"

        # Level Determine
        lvl_key = get_psr_level(psr)
        lvl_data = APLC_MESSAGES[lvl_key]
        
        # Card styling (Clean container)
        # Use border-top instead of inner div to ensure visibility
        
        with cols[idx % 5]:
            st.markdown(f"""
            <div class="metric-card" style="border-top: 4px solid {lvl_data['Color']}; padding: 15px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 5px;">
                    <h3 style="margin:0; font-size:1.1rem;">{ticker}</h3>
                    <span style="font-weight:bold; color:#888; font-size: 0.9rem;">${price:,.0f}</span>
                </div>
                <div style="font-size:0.7rem; color:#888;">{label_psr}</div>
                <div style="font-size:1.8rem; font-weight:800; color:{lvl_data['Color']}; margin-bottom: 5px;">
                    {psr:.2f}
                </div>
                 <div style="font-size:0.7rem; color:{lvl_data['Color']}; font-weight:bold; margin-bottom: 8px;">
                    {lvl_data[title_key]}
                </div>
                <div style="font-size:0.65rem; color:#666; background:#f8f9fa; padding:6px; border-radius:4px;">
                    <div style="display:flex; justify-content:space-between;">
                        <span>{TRANSLATIONS['fcf_label'][lang]}</span>
                        <span>${fcf/1e9:,.2f}B</span>
                    </div>
                    <div style="border-top:1px solid #ddd; margin-top:2px; padding-top:2px; display:flex; justify-content:space-between;">
                        <span>{TRANSLATIONS['burden_label'][lang]}</span>
                        <span>${burden/1e9:,.2f}B</span>
                    </div>
                    <div style="margin-top:4px; padding-top:4px; border-top:1px dashed #eee; color:#888; font-size: 0.6rem; display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end;">
                       <span>{TRANSLATIONS['capex_label'][lang]}: ${capex/1e9:,.2f}B</span>
                       <span>{TRANSLATIONS['elec_label'][lang]}: ${c_elec/1e9:,.2f}B</span>
                       <span>{TRANSLATIONS['res_label'][lang]}: ${c_res/1e9:,.2f}B</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # --- CapEx Audit Table UI (Moved) ---
    st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
    st.markdown("#### APLC-5 CapEx Quarterly Audit" if lang=="English" else "#### APLC-5 CapEx四半期監査")

    # 1. Create Internal Data View (Strict English Keys)
    quarterly_view = pd.DataFrame()
    quarterly_view["Ticker"] = metrics_df["Ticker"] # Keep Ticker as index-like column
    quarterly_view["Quarter"] = metrics_df["Period"]
    quarterly_view["NetIncome"] = (metrics_df["NI_Q"] / 1e9)
    quarterly_view["OperatingCashFlow"] = (metrics_df["OCF_Q"] / 1e9)
    quarterly_view["CapitalExpenditure"] = (metrics_df["CapEx_Q"] / 1e9)
    quarterly_view["CapEx_to_NI"] = metrics_df["CapEx_to_NI"]
    quarterly_view["CapEx_to_OCF"] = metrics_df["CapEx_to_OCF"]
    quarterly_view["CapEx_Status"] = metrics_df["CapExHealth"]

    # 2. Translate Status Values (Value Translation only)
    quarterly_view["CapEx_Status"] = quarterly_view["CapEx_Status"].apply(
        lambda x: CAPEX_STATUS_LABELS.get(x, {}).get(lang, x)
    )

    # 3. Localize Columns (Header Translation)
    display_df = localize_quarterly_df(quarterly_view, lang)

    # 4. formatting (Dynamic mapping based on lang)
    format_rules = {
        "NetIncome": "${:.2f}B",
        "OperatingCashFlow": "${:.2f}B",
        "CapitalExpenditure": "${:.2f}B",
        "CapEx_to_NI": "{:.2f}",
        "CapEx_to_OCF": "{:.2f}",
    }

    # Map internal keys to current display columns
    display_format = {
        TRANSLATIONS[COLUMN_LABEL_MAP[k]][lang]: v 
        for k, v in format_rules.items() 
        if k in COLUMN_LABEL_MAP
    }

    # 5. Styling Function
    def highlight_status(val):
        # Reverse lookup or brute force check
        color = "black" 
        for key, trans_dict in CAPEX_STATUS_LABELS.items():
            if val == trans_dict.get(lang, ""):
                if key == "HEALTHY": color = "#28A745"
                elif key == "BOUNDARY": color = "#BD8804" 
                elif key == "BLACK_HOLE": color = "#DC3545"
                break
                
        return f'color: {color}; font-weight: bold;'

    status_col_name = TRANSLATIONS[COLUMN_LABEL_MAP["CapEx_Status"]][lang]

    st.dataframe(
        display_df.style.format(display_format).map(highlight_status, subset=[status_col_name]),
        use_container_width=True
    )

    # --- Legend Section (Moved) ---
    legend_cols = st.columns(3)
    status_keys = ["HEALTHY", "BOUNDARY", "BLACK_HOLE"]
    status_colors = {"HEALTHY": "#28A745", "BOUNDARY": "#BD8804", "BLACK_HOLE": "#DC3545"}
    icons = {"HEALTHY": "🟢", "BOUNDARY": "🟡", "BLACK_HOLE": "🔴"}

    for i, key in enumerate(status_keys):
        c_label = CAPEX_STATUS_LABELS[key][lang]
        c_desc = CAPEX_HEALTH_DESC[key][lang]
        c_color = status_colors[key]
        
        with legend_cols[i]:
            st.markdown(f"""
            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; height: 100%;">
                <div style="color: {c_color}; font-weight: bold; margin-bottom: 5px;">
                    {icons[key]} {c_label}
                </div>
                <div style="font-size: 0.8rem; line-height: 1.4; color: #555;">
                    {c_desc}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)


# --- Layer 2 Messages (Detailed) ---
L2_MESSAGES = {
    "SOFR_IORB": {
        "HEALTHY": {
            "JP": "<b>正常 (流動性充足)</b>：準備金がシステム全体に円滑に循環しており、民間金融システムの資金供給能力に摩擦は認められない。",
            "EN": "<b>Liquidity Sufficiency</b>: Reserves are circulating smoothly. No notable friction detected in the funding capacity of the private banking system."
        },
        "WARNING": {
            "JP": "<b>摩擦 (準備金逼迫)</b>：準備金の減少により短期調達コストが上昇。ショックに対するバッファーが低下し、構造的な脆弱性が顕在化。",
            "EN": "<b>Reserve Tightness</b>: Diminishing reserves are driving up funding costs. The buffer against shocks is decreasing, revealing structural vulnerabilities."
        },
        "CRITICAL": {
            "JP": "<b>逼迫 (システム的窒息)</b>：民間銀行間の融資余力が物理的に枯渇。流動性の土台が揺らぎ、市場は「砂上の楼閣」の状態にあると判定。",
            "EN": "<b>Systemic Suffocation</b>: Funding capacity between banks has evaporated. The liquidity foundation is unstable; the market is assessed as a 'house of cards'."
        }
    },
    "TNX_DEV": {
        "HEALTHY": {
            "JP": "<b>安定 (均衡状態)</b>：金利変動が短期平均の範囲内に収束。市場は現在の資本コストを正常に消化しており、価格再設定の圧力は低い。",
            "EN": "<b>Equilibrium</b>: Yield fluctuations are within the short-term average. The market is absorbing capital costs; repricing pressure remains low."
        },
        "WARNING": {
            "JP": "<b>摩擦 (加速の兆候)</b>：金利が短期平均から不自然に逸脱。バリュエーションへの下方圧力が強まり、価格再設定の衝撃波が発生。",
            "EN": "<b>Signs of Acceleration</b>: Yields are deviating from the average. Downward pressure on valuations is intensifying, generating a repricing shockwave."
        },
        "CRITICAL": {
            "JP": "<b>逼迫 (暴走)</b>：金利の加速が物理的限界に到達。全ての資産価格に対し、物理的な下方修正を強いる局面。",
            "EN": "<b>Forced Repricing</b>: Yield acceleration has reached a physical limit, compelling a downward revision across all asset classes."
        }
    },
    "REAL_YIELD": {
        "HEALTHY": {
            "JP": "<b>正常 (許容資本自律性)</b>：実質コストが成長の許容範囲内。FANG+の「業績の盾」および投資の継続性を損なわない水準。",
            "EN": "<b>Capital Autonomy</b>: Real costs remain within the range of growth. Levels do not compromise the 'Earnings Shield' or investment continuity."
        },
        "WARNING": {
            "JP": "<b>摩擦 (利幅の浸食)</b>：実質コスト上昇が企業の再投資効率を圧迫。キャッシュフローの耐久性に歪みが生じ、成長株モデルが揺らぐ。",
            "EN": "<b>Margin Erosion</b>: Rising real costs are straining reinvestment efficiency. Distortions in cash flow durability are challenging growth stock models."
        },
        "CRITICAL": {
            "JP": "<b>逼迫 (資本の石化)</b>：剥き出しのコストが企業の成長を物理的に停止させる。成長株モデルの論理的崩壊を誘発する臨界点。",
            "EN": "<b>Petrification of Capital</b>: Naked costs are physically halting growth. A critical threshold that triggers the logical collapse of growth stock models."
        }
    },
    "TAIL": {
        "HEALTHY": {
            "JP": "<b>正常 (吸収旺盛な需要)</b>：投資家による国債吸収が円滑。プライマリー・ディーラーのバランスシートに十分な受入余力が存在。",
            "EN": "<b>Robust Demand</b>: Treasury absorption is smooth. Primary dealers maintain sufficient capacity on their balance sheets."
        },
        "WARNING": {
            "JP": "<b>摩擦 (受入限界の予兆)</b>：最終需要が減退し、ディーラーが在庫を抱え込まされ始めている。市場血管の「詰まり」が発生。",
            "EN": "<b>Signs of Capacity Limits</b>: Final demand is waning; dealers are being forced to carry inventory. 'Blockages' are emerging in the market."
        },
        "CRITICAL": {
            "JP": "<b>逼迫 (国家の壁の亀裂)</b>：需要が物理的に減衰。国債市場の機能不全が、システム全体の決壊リスクを急激に高めている状態。",
            "EN": "<b>Fracture in the Wall</b>: Demand is physically decaying. Treasury market dysfunction is escalating the risk of a systemic collapse."
        }
    },
    "COMPOSITE": {
        "HEALTHY": {
            "JP": "✅ <b>STABLE (安定)</b>\n構造的均衡が維持されています。物理的制約による市場への直接的な圧力は最小限です。",
            "EN": "✅ <b>STABLE</b>\nStructural equilibrium is maintained. Direct pressure on the market from physical constraints is minimal."
        },
        "WARNING": {
            "JP": "⚠️ <b>CAUTION (警戒)</b>\n複数の指標で摩擦が検出されました。流動性の土台に歪みが生じており、構造的遷移への警戒が必要です。",
            "EN": "⚠️ <b>CAUTION</b>\nFriction detected across multiple metrics. Distortions in the liquidity foundation suggest a need for vigilance regarding structural transitions."
        },
        "CRITICAL": {
            "JP": "🚨 <b>EMERGENCY (緊急)</b>\nシステム的決壊リスクが臨界点に到達しました。期待（ナラティブ）が剥落し、物理的な価格再設定が優先される局面です。",
            "EN": "🚨 <b>EMERGENCY</b>\nSystemic collapse risk has reached a critical threshold. Narrative buoyancy is evaporating; physical repricing now dominates the phase."
        }
    }
}

# --- UI Helper Functions ---
def render_metric_card(col, title, value_str, status, msg_dict, lang, chart_fig=None):
    """
    Renders a unified metric card with:
    - Left-aligned text
    - Top border color based on status
    - Embedded description
    - Optional chart below the card
    """
    
    # Map status to color and icon (Unified Scheme based on Danger Source Monitor)
    # Status input can be: "HEALTHY"/"WARNING"/"CRITICAL" OR "NORMAL"/"WATCH"/"DANGER"
    
    # Normalizing status to internal keys for color mapping
    status_map = {
        "HEALTHY": "NORMAL", "NORMAL": "NORMAL",
        "WARNING": "WATCH", "WATCH": "WATCH",
        "CRITICAL": "DANGER", "DANGER": "DANGER",
        "UNKNOWN": "UNKNOWN"
    }
    
    normalized_status = status_map.get(status, "UNKNOWN")
    
    colors = {
        "DANGER": "#DC3545", # Red
        "WATCH": "#FFC107",  # Yellow
        "NORMAL": "#28A745", # Green
        "UNKNOWN": "#6c757d" # Gray
    }
    
    icons = {
        "DANGER": "🔴",
        "WATCH": "🟡",
        "NORMAL": "🟢",
        "UNKNOWN": "⚪"
    }

    c = colors.get(normalized_status, "#6c757d")
    icon = icons.get(normalized_status, "⚪")
    
    # Get message
    # msg_dict is expected to be { "STATUS": {"JP": "...", "EN": "..."} }
    # Need to handle potential key mismatch if msg_dict uses different keys than status
    # Assuming msg_dict keys match the input 'status' string exactly
    
    msg_obj = msg_dict.get(status, {})
    msg = msg_obj.get("JP" if lang == "日本語" else "EN", "")
    
    with col:
        st.markdown(f"""
        <div class="metric-card" style="border-top:4px solid {c}; margin-bottom:10px;">
          <div style="font-weight:600;margin-bottom:4px;">
            {icon} {title}
          </div>
          <div style="font-size:0.85rem;margin-bottom:6px; font-weight:bold;">
            {value_str}
          </div>
          <div style="font-size:0.75rem;color:#555;line-height:1.4;">
            {msg}
          </div>
        </div>
        """, unsafe_allow_html=True)
        
        if chart_fig:
            st.plotly_chart(chart_fig, use_container_width=True, config={'displayModeBar': False})
        elif chart_fig is not None: # explicitly passed as None implies "No Data" or intended empty
             st.markdown(f"<div style='text-align:center; color:#999; font-size:0.8rem; margin-bottom:10px;'>*No Chart Data*</div>", unsafe_allow_html=True)

# --- Logic Functions ---
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

with tabs[1]:
    # Liquidity Monitor (Title Updated: removed Layer 2 label)
    l2_title_clean = "Systemic Liquidity Friction Monitor" if lang == "English" else "システム流動性摩擦モニター"
    st.subheader(l2_title_clean)
    st.markdown(TRANSLATIONS['l2_desc'][lang], unsafe_allow_html=True)

    # Prepare Data for L2 Evaluation
    val_sofr = market_data.get('SOFR', 5.3)
    val_iorb = market_data.get('IORB', 5.4)
    val_spread = val_sofr - val_iorb

    val_rates_hist = market_data.get('Rates_History', pd.DataFrame())
    val_tnx_div = market_data.get('TNX_Div', pd.DataFrame())
    val_real_yield = market_data.get('Real_Yield', pd.DataFrame())
    val_tail_df = liquidity_df_mock 

    # Current Values (Latest)
    l2_sofr_spread = val_spread * 100 
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
        cur_tail = val_tail_df['Treasury_Tail'].iloc[-1]

    # Evaluate
    comp_stat, s_sofr, s_tnx, s_real, s_tail = evaluate_l2_status(cur_spread, cur_tnx_dev, cur_real_yield, cur_tail)

    # Composite Panel
    l2_meta = STATUS_MAP[comp_stat]
    l2_msg_key = "JP" if lang == "日本語" else "EN"
    st.markdown(f'''
    <div class="judgment-panel {l2_meta['class']}" style="padding: 15px; margin-bottom: 20px;">
        {L2_MESSAGES['COMPOSITE'][comp_stat][l2_msg_key]}
    </div>
    ''', unsafe_allow_html=True)

    l2_c1, l2_c2, l2_c3, l2_c4 = st.columns(4)

    chart_config = dict(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        height=200,
        margin=dict(l=0, r=0, t=10, b=0),
        font=dict(size=10)
    )
    date_cutoff = pd.Timestamp("2026-01-01")

# --- Credit → Equity Status Logic ---


# --- Credit -> Equity Transmission Monitor (New Logic) ---

C2E_MESSAGES = {
    "HEALTHY": {
        "日本語": "クレジット市場と株式市場のストレスはまだ限定的で、伝播経路には大きな亀裂は見られません。局所的なショックであれば吸収可能な状態です。",
        "English": "Stress in credit and equities remains contained. No major fracture is visible along the transmission path yet, and localized shocks are still absorbable."
    },
    "WARNING": {
        "日本語": "クレジット側の劣化に対し、株式側の反応が強まりつつあります。流動性の逃げ場が細り、1〜2発のショックで一段深い波及に転じる局面です。",
        "English": "Credit deterioration is starting to propagate into equities. Liquidity escape routes are narrowing, and one or two shocks could trigger a deeper contagion."
    },
    "CRITICAL": {
        "日本語": "クレジットの崩れが株式へ本格的に波及しています。複数の市場が同時に流動性不足へ向かう自己増幅フェーズに入りつつあります。",
        "English": "Credit weakness is now fully bleeding into equities. Multiple markets are sliding into a self-reinforcing liquidity shortage phase."
    }
}

def judge_credit_to_equity(credit_stress, equity_reaction):
    """
    credit_stress, equity_reaction ∈ {"LOW","MEDIUM","HIGH"}
    """
    # クレジット高ストレス & 株も崩れている → CRITICAL
    if credit_stress == "HIGH" and equity_reaction == "HIGH":
        return "CRITICAL"
    # クレジット高ストレスだが株はまだ粘っている → WARNING
    if credit_stress == "HIGH" and equity_reaction in ("LOW","MEDIUM"):
        return "WARNING"
    # クレジット中ストレス & 株中〜高反応 → WARNING
    if credit_stress == "MEDIUM" and equity_reaction in ("MEDIUM","HIGH"):
        return "WARNING"
    # それ以外 → HEALTHY
    return "HEALTHY"

CREDIT_EQ_STATUS_TEXT = {
    "HEALTHY": {
        "JP": (
            "🟢 安定：データセンター関連REITの相対パフォーマンスは大きく崩れておらず、"
            "HYスプレッドも平常レンジ内に収まっています。"
            "クレジット市場はまだAIデータセンター向けの資金供給を許容しており、"
            "半導体装置株もSOXXに対して優位性または中立を維持しています。"
            "融資条件のタイト化は始まっていても、建設や設備投資のパイプラインが一気に"
            "遮断される段階には至っていない状態です。"
        ),
        "EN": (
            "🟢 HEALTHY: Data-center REITs have not meaningfully broken down versus the REIT complex, "
            "and HY spreads remain within a normal range. The credit market still tolerates funding "
            "for AI data-center projects, while semiconductor equipment names are holding up "
            "relatively well versus SOXX. Tightening may have begun at the margin, but the capital "
            "pipeline has not yet been structurally shut off."
        )
    },
    "WARNING": {
        "JP": (
            "🟡 警戒：SRVR/VNQ や装置株相対がじりじりと劣化し、HYスプレッドも拡大方向に"
            "動いています。まだ全面的な信用収縮ではありませんが、"
            "新規DC案件やAI向け設備投資に対する貸し手の選別が強まり、"
            "マージンの低いプロジェクトから順に延期・縮小されるリスクが高まっています。"
            "クレジットショックに発展する前段階として要監視のゾーンです。"
        ),
        "EN": (
            "🟡 WARNING: SRVR/VNQ and the semi-equipment relative are grinding lower while HY spreads "
            "trend wider. This is not yet a full-blown credit crunch, but lenders are becoming more "
            "selective toward new data-center and AI CapEx projects. Lower-margin or marginal deals "
            "are at growing risk of delay or downsizing. This zone represents a pre-shock phase that "
            "requires close monitoring."
        )
    },
    "CRITICAL": {
        "JP": (
            "🔴 危険：データセンター関連クレジットと半導体装置株が同時に崩れ、"
            "HYスプレッドも大きく跳ね上がっています。"
            "これはクレジット市場がDC関連証券やレバレッジド案件のリスクを持ち切れず、"
            "資金パイプを絞り始めたサインです。"
            "AIインフラ投資のキャンセルや大幅な見直しが株価とマクロの双方に波及しやすい、"
            "構造的ストレスの臨界状態と判断されます。"
        ),
        "EN": (
            "🔴 CRITICAL: Data-center credit proxies and semi-equipment relative performance are both "
            "breaking down while HY spreads spike sharply higher. This signals that the credit market "
            "is no longer willing to warehouse DC-related and highly leveraged risk, and is actively "
            "choking off funding. The probability of cancelled or radically re-scoped AI infrastructure "
            "projects rises sharply, with stress likely to spill over into both equities and the macro "
            "environment."
        )
    }
}

def evaluate_credit_equity_status(dc_chg_30d: float, hy_oas_bps: float, semi_chg_30d: float) -> str:
    """
    三変数から Credit→Equity の構造ストレスレベルを判定
    """
    # 1. Determine Stress Levels
    # Credit Stress (DC or HY)
    c_stress = "LOW"
    if hy_oas_bps > 450 or dc_chg_30d < -15.0:
        c_stress = "HIGH"
    elif hy_oas_bps > 350 or dc_chg_30d < -5.0:
        c_stress = "MEDIUM"
        
    # Equity Reaction (Semi)
    e_react = "LOW"
    if semi_chg_30d < -15.0:
        e_react = "HIGH"
    elif semi_chg_30d < -5.0:
        e_react = "MEDIUM"
        
    return judge_credit_to_equity(c_stress, e_react)

# --- Individual Metric Status Logic ---

DC_MONITOR_STATUS_TEXT = {
    "HEALTHY": {
        "JP": "DC REITはREIT全体と同程度で推移。DC関連クレジット劣化はまだ限定的です。",
        "EN": "DC REITs track the broader REIT complex; little sign yet of DC-specific credit stress."
    },
    "WARNING": {
        "JP": "DC REITがREIT全体をじりじりアンダーパフォーム。資金の選別が始まりつつあります。",
        "EN": "DC REITs are grinding lower vs. peers, suggesting lenders and equity investors are turning selective."
    },
    "CRITICAL": {
        "JP": "DC REITが大幅に崩れ、DC案件への資金パイプが絞られ始めた可能性が高い局面です。",
        "EN": "Severe DC REIT underperformance signals funding pipes for new DC projects may be actively choking off."
    }
}

HY_MONITOR_STATUS_TEXT = {
    "HEALTHY": {
        "JP": "HYスプレッドは平常レンジ内。リスク資産へのクレジット供給は概ね維持されています。",
        "EN": "HY spreads remain in a normal band; credit supply to risky assets is broadly intact."
    },
    "WARNING": {
        "JP": "HYスプレッドが拡大基調。レバレッジドDCや周辺セクターへの新規与信は絞られやすい局面です。",
        "EN": "HY spreads are widening, making it harder to finance leveraged DC and adjacent projects at the margin."
    },
    "CRITICAL": {
        "JP": "HYスプレッドが急拡大。ハイイールド全体のリスク回避が進み、資金調達環境は危険水域です。",
        "EN": "HY spreads have blown out; broad de-risking in credit is pushing funding conditions into danger."
    }
}

SEMI_MONITOR_STATUS_TEXT = {
    "HEALTHY": {
        "JP": "装置株はSOXXと同等か優位。AI向けCapEx期待はまだ大きく後退していません。",
        "EN": "Semi-equipment names are in line with or beating SOXX; AI CapEx expectations remain broadly intact."
    },
    "WARNING": {
        "JP": "装置株がSOXXをジリ安で下回り、DC関連クレジット悪化が受注期待を侵食し始めています。",
        "EN": "Equipment stocks are underperforming SOXX, hinting that DC credit stress is starting to erode order hopes."
    },
    "CRITICAL": {
        "JP": "装置株がSOXXを大きくアンダーパフォーム。AI/DC向け設備投資のキャンセル懸念が高い局面です。",
        "EN": "Sharp underperformance vs SOXX suggests rising risk of AI/DC CapEx cuts or outright project cancellations."
    }
}

def classify_dc_status(dc_chg_30d: float) -> str:
    if dc_chg_30d is None:
        return "HEALTHY"
    if dc_chg_30d > -5.0:
        return "HEALTHY"
    elif dc_chg_30d > -15.0:
        return "WARNING"
    else:
        return "CRITICAL"

def classify_hy_status(hy_oas_bps: float) -> str:
    if hy_oas_bps is None:
        return "HEALTHY"
    if hy_oas_bps < 350:
        return "HEALTHY"
    elif hy_oas_bps < 450:
        return "WARNING"
    else:
        return "CRITICAL"

def classify_semi_status(semi_chg_30d: float) -> str:
    if semi_chg_30d is None:
        return "HEALTHY"
    if semi_chg_30d > -5.0:
        return "HEALTHY"
    elif semi_chg_30d > -15.0:
        return "WARNING"
    else:
        return "CRITICAL"

# --- Credit → Equity Transmission Panel ---

def credit_to_equity_panel(lang: str):
    """
    DC関連クレジット → HYスプレッド → 半導体装置 伝播モニター
    """
    # タイトル & 説明文
    if lang == "日本語":
        title = "クレジット → 株式 伝播モニター"
        st.subheader(title)
        desc = (
            "このパネルは「データセンター関連クレジット → ハイイールド債全体 → "
            "半導体装置・AI CapEx期待」という伝播経路を監視します。"
            "AIデータセンターは多額の借入と証券化（ABS・CMBS）によって建設されており、"
            "テナントの投資減速や電力コスト高騰が起きると、最初に傷むのはこれらクレジット商品です。"
            "そこで SRVR/VNQ でデータセンターREITの相対劣化をとらえ、"
            "HY OAS でクレジット全体への波及を確認し、最後に AMAT・LRCX 等の装置株と SOXX の相対で、"
            "AI向け設備投資の息切れが株式市場にどう現れているかを可視化します。"
        )
        label_dc = "DC関連REIT 相対 (SRVR/VNQ)"
        label_hy = "HYスプレッド (ICE BofA HY OAS)"
        label_semi = "半導体装置 相対 (AMAT,LRCX,KLAC,ASML / SOXX)"
    else:
        title = "Credit → Equity Transmission Monitor"
        st.subheader(title)
        desc = (
            "This panel tracks the transmission chain from data-center related credit to the broader "
            "high-yield market and finally into semiconductor equipment and AI CapEx expectations. "
            "Large AI data centers are typically financed with leveraged structures and securitized debt "
            "(ABS/CMBS). When tenants slow spending or power costs surge, stress first appears in those "
            "credit instruments. We therefore watch SRVR/VNQ as a proxy for data-center REIT underperformance, "
            "HY OAS as the high-yield risk gauge, and the relative performance of equipment names "
            "(AMAT, LRCX, etc.) versus SOXX to see how tightening credit conditions feed back into equity "
            "and AI investment sentiment."
        )
        label_dc = "DC-related REIT Relative (SRVR/VNQ)"
        label_hy = "HY Spread (ICE BofA HY OAS)"
        label_semi = "Semi Equipment Relative (AMAT,LRCX,KLAC,ASML / SOXX)"

    label_change30 = "30日変化率" if lang == "日本語" else "30D Change"
    label_latest = "最新値" if lang == "日本語" else "Latest"
    label_bps = "bps"
    label_no_data = "データなし" if lang == "日本語" else "No Data"

    # --- Metrics Logic ---
    dc_chg_30d = None
    hy_oas_bps = None
    semi_chg_30d = None

    # 1) DC Credit Calc (SRVR / VNQ)
    px_dc = fetch_price_series(["SRVR", "VNQ"], days=120)
    ratio_dc = None
    if not px_dc.empty and all(t in px_dc.columns for t in ["SRVR", "VNQ"]):
        ratio_dc = px_dc["SRVR"] / px_dc["VNQ"]
        if len(ratio_dc) > 22:
            dc_chg_30d = (ratio_dc.iloc[-1] / ratio_dc.iloc[-22] - 1) * 100
        else:
            dc_chg_30d = 0.0
    
    # 2) HY OAS Calc
    df_hy = fetch_hy_oas_series()
    if not df_hy.empty:
        # FRED data is %, so 3.05 means 3.05%. bps = 305.
        hy_oas_bps = float(df_hy['value'].iloc[-1]) * 100
    
    # 3) Semi Eq Calc
    tickers_semi = ["AMAT", "LRCX", "KLAC", "ASML", "SOXX"]
    px_semi = fetch_price_series(tickers_semi, days=120)
    ratio_semi = None
    needed = ["AMAT", "LRCX", "KLAC", "ASML", "SOXX"]
    if not px_semi.empty and all(t in px_semi.columns for t in needed):
        semi_eq = px_semi[["AMAT", "LRCX", "KLAC", "ASML"]].mean(axis=1)
        ratio_semi = semi_eq / px_semi["SOXX"]
        if len(ratio_semi) > 22:
            semi_chg_30d = (ratio_semi.iloc[-1] / ratio_semi.iloc[-22] - 1) * 100
        else:
            semi_chg_30d = 0.0

    # --- Comprehensive Judgment ---
    comm_status = evaluate_credit_equity_status(dc_chg_30d if dc_chg_30d is not None else 0, 
                                                hy_oas_bps if hy_oas_bps is not None else 300, 
                                                semi_chg_30d if semi_chg_30d is not None else 0)
    
    # Render Comprehensive Panel
    meta = STATUS_MAP[comm_status]
    msg = C2E_MESSAGES[comm_status]["日本語" if lang=="日本語" else "English"]
    
    st.markdown(f"""
    <div class="judgment-panel {meta['class']}" style="margin-bottom:25px;">
      <div class="judgment-title" style="color:{meta['color']}">
        {meta['icon']} {title} Status: {comm_status}
      </div>
      <div style="font-size:0.95rem; line-height:1.6;">
        {msg}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Render: 3 Column Charts ---
    col_dc, col_hy, col_semi = st.columns(3)

    # Col 1: DC Credit
    status_dc = "UNKNOWN"
    val_str_dc = "N/A"
    fig_dc = None
    
    if ratio_dc is not None:
        status_dc = classify_dc_status(dc_chg_30d)
        val_str_dc = f"{dc_chg_30d:.1f}%"
        
        # Convert to Plotly
        # ratio_dc is Series with DateTimeIndex
        df_p = ratio_dc.to_frame(name="SRVR/VNQ").reset_index()
        # Ensure x-axis column name is handled (usually "Date" or index name)
        x_col = df_p.columns[0]
        
        fig_dc = px.line(df_p, x=x_col, y="SRVR/VNQ")
        fig_dc.update_layout(**chart_config, showlegend=False)
        
        meta = STATUS_MAP[status_dc]
        fig_dc.update_traces(line_color=meta['color'])

    render_metric_card(col_dc, label_dc, val_str_dc, status_dc, DC_MONITOR_STATUS_TEXT, lang, fig_dc)

    # Col 2: HY OAS
    status_hy = "UNKNOWN"
    val_str_hy = "N/A"
    fig_hy = None

    if df_hy is not None and not df_hy.empty:
        status_hy = classify_hy_status(hy_oas_bps)
        val_str_hy = f"{hy_oas_bps:.0f} {label_bps}"
        
        # df_hy usually has 'date' and 'value'
        fig_hy = px.line(df_hy, x='date', y='value')
        fig_hy.update_layout(**chart_config, showlegend=False)
        
        meta = STATUS_MAP[status_hy]
        fig_hy.update_traces(line_color=meta['color'])
    
    render_metric_card(col_hy, label_hy, val_str_hy, status_hy, HY_MONITOR_STATUS_TEXT, lang, fig_hy)

    # Col 3: Semi Eq
    status_semi = "UNKNOWN"
    val_str_semi = "N/A"
    fig_semi = None

    if ratio_semi is not None:
        status_semi = classify_semi_status(semi_chg_30d)
        val_str_semi = f"{semi_chg_30d:.1f}%"
        
        # ratio_semi is Series
        df_p = ratio_semi.to_frame(name="SemiEq/SOXX").reset_index()
        x_col = df_p.columns[0]
        
        fig_semi = px.line(df_p, x=x_col, y="SemiEq/SOXX")
        fig_semi.update_layout(**chart_config, showlegend=False)
        
        meta = STATUS_MAP[status_semi]
        fig_semi.update_traces(line_color=meta['color'])

    render_metric_card(col_semi, label_semi, val_str_semi, status_semi, SEMI_MONITOR_STATUS_TEXT, lang, fig_semi)

def render_l2_card(col, title, status, msg_dict, fig, val_str=""):
    render_metric_card(col, title, val_str, status, msg_dict, lang, fig)

# 1. SOFR vs IORB Trend
fig_1 = None
if val_rates_hist is not None and not val_rates_hist.empty:
    df = val_rates_hist[val_rates_hist['date'] >= date_cutoff]
    if not df.empty:
        fig_1 = px.line(df, x='date', y='SOFR')
        fig_1.add_trace(go.Scatter(x=df['date'], y=df['IORB'], name='IORB', line=dict(dash='dash', color='orange')))
        fig_1.update_layout(**chart_config, showlegend=False)

render_l2_card(l2_c1, TRANSLATIONS['l2_sofr'][lang], s_sofr, L2_MESSAGES['SOFR_IORB'], fig_1, f"{cur_spread*100:.2f} bps")

# 2. TNX Divergence
fig_2 = None
if val_tnx_div is not None and not val_tnx_div.empty:
    df = val_tnx_div[val_tnx_div['Date'] >= date_cutoff]
    if not df.empty:
        fig_2 = px.bar(df, x='Date', y='Divergence', color='Divergence', color_continuous_scale='RdYlGn_r')
        fig_2.update_layout(**chart_config)
        fig_2.update_coloraxes(showscale=False)

render_l2_card(l2_c2, TRANSLATIONS['l2_tnx'][lang], s_tnx, L2_MESSAGES['TNX_DEV'], fig_2, f"{cur_tnx_dev:.2f}")

# 3. Real Yield
fig_3 = None
if val_real_yield is not None and not val_real_yield.empty:
    df = val_real_yield[val_real_yield['date'] >= date_cutoff]
    if not df.empty:
        fig_3 = px.line(df, x='date', y='value')
        fig_3.update_traces(line_color='#9C27B0')
        fig_3.update_layout(**chart_config)

render_l2_card(l2_c3, TRANSLATIONS['l2_real'][lang], s_real, L2_MESSAGES['REAL_YIELD'], fig_3, f"{cur_real_yield:.2f}%")

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

render_l2_card(l2_c4, f"{TRANSLATIONS['tail_title'][lang]}", s_tail, L2_MESSAGES['TAIL'], fig_4, f"{cur_tail:.2f}")

with tabs[2]:
    # --- Credit → Equity Transmission Monitor ---
    credit_to_equity_panel(lang)

# --- New: Danger Source Data (Equity / Credit Proxies) ---

@st.cache_data(ttl=3600)
def get_danger_source_data():
    """
    危険源モニタ用の価格データを取得
    - Semi 装置: AMAT, LRCX, KLAC, ASML（等ウェイト合成）
    - セクター: SOXX
    - Credit Proxy: DC/インフラ系 REIT vs HY ETF
      ※ETFは無料で取れる代替として扱う
    """
    tickers = {
        "semi_equip": ["AMAT", "LRCX", "KLAC", "ASML"],
        "sector": ["SOXX"],
        "dc_credit_proxy": ["SRVR"],   # データセンター REIT ETF 例
        "hy_proxy": ["HYG"],           # ハイイールドETF 例
    }
    
    end = datetime.utcnow()
    start = end - timedelta(days=365)  # 1年分
    
    data = {}
    for group, names in tickers.items():
        for t in names:
            try:
                hist = yf.Ticker(t).history(start=start, end=end)
                if hist.empty:
                    continue
                hist = hist[['Close']].rename(columns={'Close': t})
                if group not in data:
                    data[group] = hist
                else:
                    data[group] = data[group].join(hist, how='outer')
            except Exception as e:
                st.warning(f"Error fetching {t} for danger source: {e}")
    
    return data

def compute_relative_perf(data):
    """
    Semi 装置（AMAT/LRCX/KLAC/ASML 等ウェイト）と SOXX の
    直近 N 日リターンを比較し、Relative Performance を返す
    """
    semi_df = data.get("semi_equip")
    sector_df = data.get("sector")
    if semi_df is None or sector_df is None:
        return None
    
    # 等ウェイト合成
    semi_prices = semi_df.dropna()
    if semi_prices.empty:
        return None
    semi_prices['EQ'] = semi_prices.mean(axis=1)
    
    # セクター
    soxx = sector_df[['SOXX']].dropna()
    
    # 共通日付
    df = semi_prices[['EQ']].join(soxx, how='inner')
    if df.empty:
        return None
    
    # 直近 20 営業日リターン
    window = 20
    if len(df) < window:
        window = len(df)
        
    recent = df.iloc[-window:]
    if recent.empty:
        return None

    semi_ret = recent['EQ'].iloc[-1] / recent['EQ'].iloc[0] - 1.0
    soxx_ret = recent['SOXX'].iloc[-1] / recent['SOXX'].iloc[0] - 1.0
    
    rel = semi_ret - soxx_ret  # 「装置だけ売られているか？」
    return {
        "semi_ret": semi_ret,
        "soxx_ret": soxx_ret,
        "relative": rel
    }

def compute_dc_credit_divergence(data):
    """
    データセンター/インフラ REIT ETF (SRVR) と HY ETF (HYG)
    のスプレッドを簡易的に測る。
    実際の OAS ではなく「価格リターン差」をクレジット感応 proxy とする。
    """
    dc_df = data.get("dc_credit_proxy")
    hy_df = data.get("hy_proxy")
    if dc_df is None or hy_df is None:
        return None
    
    dc = dc_df[['SRVR']].dropna()
    hy = hy_df[['HYG']].dropna()
    df = dc.join(hy, how='inner')
    if df.empty:
        return None
    
    window = 60  # クレジットとしては少し長め
    if len(df) < window:
        window = len(df)
        
    recent = df.iloc[-window:]
    if recent.empty:
         return None

    dc_ret = recent['SRVR'].iloc[-1] / recent['SRVR'].iloc[0] - 1.0
    hy_ret = recent['HYG'].iloc[-1] / recent['HYG'].iloc[0] - 1.0
    
    # HY は「リスク資産全体」、SRVR がそれより悪化していれば
    # 「DC クレジットだけ先に裂けている」サイン
    spread = dc_ret - hy_ret   # マイナス大きいほど危険
    return {
        "dc_ret": dc_ret,
        "hy_ret": hy_ret,
        "spread": spread
    }

def compute_physical_vs_market(metrics_df, market_data):
    """
    最弱PSRと指数リターンのミスマッチを判定する材料を出す
    """
    if metrics_df.empty:
        return None
    
    # 既に作っている APLC-5 の最弱 PSR
    if 'PSR' in metrics_df.columns:
        min_psr_val = metrics_df['PSR'].min()
    else:
        return None
    
    # 指数リターン（ここでは SPX を代表に）
    # market_data['SPX'] is just latest price. Need history or fetch new.
    # The Prompt code fetches fresh history.
    try:
        spx_hist = yf.Ticker("^GSPC").history(period="1mo")
        if spx_hist.empty:
            spx_ret = 0.0
        else:
            spx_ret = spx_hist['Close'].iloc[-1] / spx_hist['Close'].iloc[0] - 1.0
    except:
        spx_ret = 0.0
    
    return {
        "min_psr": min_psr_val,
        "spx_ret": spx_ret
    }

# --- Judgment Logic ---

def judge_relative_perf(rel):
    if rel is None:
        return "UNKNOWN"
    if rel < -0.10:
        return "DANGER"
    elif rel < -0.05:
        return "WATCH"
    else:
        return "NORMAL"

RELATIVE_MSG = {
    "NORMAL": {
        "JP": "装置株とSOXXの相対パフォーマンスは安定しており、現時点では選別的な売り圧力は顕在化していません。",
        "EN": "Semi equipment remains in line with SOXX; no clear sign yet of selective de-risking focused on this segment."
    },
    "WATCH": {
        "JP": "指数は維持されている一方で、装置株だけがやや劣後し始めており、資金の静かな引き上げが進行している可能性があります。",
        "EN": "The index is holding up, but semi equipment is starting to lag, suggesting a quiet rotation of capital away from this pocket."
    },
    "DANGER": {
        "JP": "SOXXが崩れていないにもかかわらず装置株だけが大きく売られており、市場が構造的なリスク源として切り捨て始めた局面と考えられます。",
        "EN": "Semi equipment is being sold hard while SOXX holds up, indicating the market may be isolating this group as a structural risk source."
    },
    "UNKNOWN": {
        "JP": "必要な価格データが取得できず、この指標からは相対的なリスクシグナルを判定できていません。",
        "EN": "Required price data is missing; no relative risk signal can be inferred from this metric at the moment."
    }
}

def judge_dc_credit(spread):
    if spread is None:
        return "UNKNOWN"
    if spread < -0.10:
        return "DANGER"
    elif spread < -0.05:
        return "WATCH"
    else:
        return "NORMAL"

DC_CREDIT_MSG = {
    "NORMAL": {
        "JP": "データセンター/インフラREITとハイイールド全体の動きは概ね揃っており、DCクレジットだけが先行して悪化している兆しはありません。",
        "EN": "DC/infra REITs are broadly tracking HY; there is no clear sign that DC credit is deteriorating ahead of the broader high-yield complex."
    },
    "WATCH": {
        "JP": "ハイイールド全体に比べてDC/インフラREITのリターンが見劣りしており、クレジット市場がこの領域のリスクを意識し始めた可能性があります。",
        "EN": "DC/infra REITs are underperforming HY, hinting that credit markets may be starting to discriminate against this segment."
    },
    "DANGER": {
        "JP": "ハイイールド全体がまだ崩れていないにもかかわらず、DC/インフラREITだけが大きく売り込まれており、データセンター関連クレジットがサブプライム的な「真の発火点」になりつつあるリスクがあります。",
        "EN": "DC/infra REITs are sharply lagging HY, suggesting DC-linked credit is being singled out as a potential ‘subprime-style’ ignition point."
    },
    "UNKNOWN": {
        "JP": "DC/インフラREITまたはHY ETFの価格データが不足しており、クレジット乖離シグナルは判定不能です。",
        "EN": "Price data for DC/infra REIT or HY ETF is insufficient, so the DC credit divergence signal cannot be evaluated."
    }
}

def judge_physical_vs_market(min_psr, spx_ret):
    if min_psr is None:
        return "UNKNOWN"
    
    # 物理はまだ耐えている or 1.0に近い
    if min_psr >= 1.1:
        return "NORMAL"
    
    # PSR<1.0 なのに、SPX が上昇 or 横ばい → ナラティブ優勢
    if min_psr < 1.0 and spx_ret > 0.05:
        return "DANGER"
    elif min_psr < 1.0:
        return "WATCH"
    
    # 1.0〜1.1 くらいで SPX も重くなっている → 物理と市場が同期し始めている
    return "WATCH"

PHYSICAL_MARKET_MSG = {
    "NORMAL": {
        "JP": "最弱PSRもまだ1.1以上を維持しており、物理コストと株価の動きは大きく矛盾していません。現時点ではナラティブと物理の乖離は限定的です。",
        "EN": "Even the weakest PSR remains above 1.1, so market pricing is not in gross conflict with physical constraints; narrative and physics are still roughly aligned."
    },
    "WATCH": {
        "JP": "一部の企業でPSRが1.0割れに接近または下回り始めており、物理的な支払能力が限界に近づいています。指数はまだ崩れていないものの、物理と価格の間にきしみが生じています。",
        "EN": "Some PSRs are drifting toward or below 1.0, signalling stressed physical solvency. Indices have not broken yet, but tension between cash reality and price is building."
    },
    "DANGER": {
        "JP": "最弱PSRが1.0を大きく下回る一方、SPXはなおプラス圏にあり、物理的な赤字を無視したナラティブだけが株価を支えている状態です。時間差を伴う決壊リスクが高まっています。",
        "EN": "The weakest PSR is well below 1.0 while the SPX remains positive, implying equity is levitating purely on narrative above a physically insolvent core; a delayed but violent adjustment risk is elevated."
    },
    "UNKNOWN": {
        "JP": "APLC-5のPSRまたは指数リターンが取得できず、物理と市場のミスマッチは本指標からは判定できません。",
        "EN": "APLC-5 PSR or index return data is unavailable, so the physical-vs-market mismatch cannot be assessed from this metric."
    }
}

# --- Danger Source Hazard & Matrix Messages ---

HAZARD_MESSAGES = {
    "HEALTHY": {
        "日本語": "データセンター関連のクレジット指標はおおむね安定しており、過剰レバレッジが即座に破断する兆候は限定的です。",
        "English": "Credit metrics around data centers remain broadly stable, with limited signs that leveraged structures are on the verge of immediate rupture."
    },
    "WARNING": {
        "日本語": "データセンター関連のスプレッドや価格に歪みが現れています。まだ表面化していないものの、将来の不良化クラスターの前触れとなり得る局面です。",
        "English": "Spreads and prices on data-center-related credit are starting to distort. The stress is not yet explosive, but it resembles the early shape of a future default cluster."
    },
    "CRITICAL": {
        "日本語": "データセンター関連クレジットが明確に崩れ始めています。証券化ビークルを経由して、他のハイイールドや株式へ波及する引き金となり得る状態です。",
        "English": "Data-center-related credit is visibly breaking. Securitized structures here are capable of seeding stress into broader high-yield markets and equities."
    }
}

QUADRANT_MESSAGES = {
    "Q1_ACTIVE_SHOCK": {
        "日本語ラベル": "即時反応ゾーン",
        "EnglishLabel": "Active Shock Zone",
        "日本語": "市場はこのリスクに高感度かつ急速に反応中です。評価軸が短期間で切り替わり、大きな価格調整が走りやすい局面です。",
        "English": "The market is highly sensitive and rapidly repricing this risk. Valuation regimes are shifting quickly, making large moves more likely."
    },
    "Q2_LATE_AWAKENING": {
        "日本語ラベル": "目覚め遅延ゾーン",
        "EnglishLabel": "Late Awakening Zone",
        "日本語": "これまで軽視されていたリスクに、市場がようやく反応し始めています。織り込みは初期段階で、歪み是正の余地が大きい状態です。",
        "English": "The market is only now starting to react to this risk. Pricing-in is in its early stage, leaving substantial room for distortion to unwind."
    },
    "Q3_OVERPRICED_FADE": {
        "日本語ラベル": "過剰織り込み解消ゾーン",
        "EnglishLabel": "Overpriced Fade Zone",
        "日本語": "リスク感度は高いままですが、織り込みはピークアウトしつつあります。過剰反応の反動で、逆方向の調整が入りやすい局面です。",
        "English": "The market remains highly sensitive, but pricing-in is fading. Prior overreaction is at risk of mean reversion or sharp counter-moves."
    },
    "Q4_COMPLACENT_BLIND": {
        "日本語ラベル": "盲点・油断ゾーン",
        "EnglishLabel": "Complacent Blind-Spot Zone",
        "日本語": "リスク認識も価格反応も鈍く、楽観バイアスが強い状態です。将来のショックの種が静かに積み上がる「見えない危険域」です。",
        "English": "Both awareness and price response are muted, reflecting strong optimism bias. This is a hidden danger zone where future shocks quietly accumulate."
    },
    "CENTER_HIGH_HOLD": {
        "日本語ラベル": "高感度・様子見帯",
        "EnglishLabel": "High-Sensitivity Hold Zone",
        "日本語": "市場はこのリスクを強く意識していますが、新たな織り込み方向は定まっていません。次の材料次第で上にも下にも振れやすい帯域です。",
        "English": "The market is highly aware of this risk, but pricing direction is on hold. The next catalyst can easily push repricing up or down."
    },
    "CENTER_LOW_QUIET": {
        "日本語ラベル": "静穏・無関心帯",
        "EnglishLabel": "Quiet Unaware Zone",
        "日本語": "市場はこのリスクをほとんど意識していません。今は問題になっていないように見えますが、将来的な「一気の織り込み」の温床にもなり得ます。",
        "English": "The market is largely unaware of this risk. It appears irrelevant for now, but this calm can become the seedbed of sudden future repricing."
    }
}

def to_axis_values(sens_level, vel_level):
    sens_high = sens_level in ("HIGH","MEDIUM")
    x = 1 if sens_high else -1

    if vel_level == "ACCEL":
        y = 1
    elif vel_level == "DISCONNECT":
        y = -1
    else:
        y = 0
    return x, y

def quadrant_label(sens_level, vel_level):
    sens_high = sens_level in ("HIGH","MEDIUM")

    if vel_level == "ACCEL":
        if sens_high: return "Q1_ACTIVE_SHOCK"
        else:         return "Q2_LATE_AWAKENING"
    elif vel_level == "DISCONNECT":
        if sens_high: return "Q3_OVERPRICED_FADE"
        else:         return "Q4_COMPLACENT_BLIND"
    else:  # STABLE
        if sens_high: return "CENTER_HIGH_HOLD"
        else:         return "CENTER_LOW_QUIET"

# --- Danger Source Monitor Section ---

with tabs[3]:
    section_title = "Danger Source Monitor" if lang == "English" else "危険源モニター"
    st.subheader(section_title)

    # 説明文（短め）
    if lang == "日本語":
        st.markdown("""
    データセンター関連クレジットと半導体装置セクターが、指数より一足先に「静かに壊れ始めていないか」を検知するためのモニタです。  
    ここでは、**装置株 vs SOXX の相対パフォーマンス**,  **DCクレジットとHYの乖離**, **物理PSRと株価のミスマッチ**の3軸で「危ない側だけ深く沈んでいく」動きを監視します。
    """)
    else:
        st.markdown("""
    This monitor is designed to detect whether data-center credit and semi equipment are starting to break **quietly ahead of the index**.  
    It tracks three axes: **semi vs SOXX relative performance**,**DC credit vs HY divergence**, and **mismatch between physical PSR and index pricing**,to flag situations where the “dangerous side” is sinking in isolation.
    """)

    try:
        danger_data = get_danger_source_data()
        
        rel_info   = compute_relative_perf(danger_data)
        cred_info  = compute_dc_credit_divergence(danger_data)
        phys_info  = compute_physical_vs_market(metrics_df, market_data)
        
        rel_status = judge_relative_perf(rel_info['relative'] if rel_info else None)
        cred_status = judge_dc_credit(cred_info['spread'] if cred_info else None)
        phys_status = judge_physical_vs_market(
            phys_info['min_psr'] if phys_info else None,
            phys_info['spx_ret'] if phys_info else 0.0
        )
        
        # --- Comprehensive Hazard Status & Matrix ---
        
        # Dummy Logic for Demonstration (As requested)
        # Ideally this comes from aggregating the 3 cards below
        hazard_status = "HEALTHY"
        if cred_status == "DANGER" or rel_status == "DANGER":
             hazard_status = "CRITICAL"
        elif cred_status == "WATCH" or rel_status == "WATCH":
             hazard_status = "WARNING"
             
        # Dummy Matrix Inputs
        sens_level = "HIGH" 
        vel_level = "STABLE"
        
        # 1. Hazard Status Panel
        h_meta = STATUS_MAP[hazard_status]
        h_msg = HAZARD_MESSAGES[hazard_status]["日本語" if lang=="日本語" else "English"]
        
        st.markdown(f"""
        <div class="judgment-panel {h_meta['class']}" style="margin-bottom:25px;">
          <div class="judgment-title" style="color:{h_meta['color']}">
            {h_meta['icon']} {section_title} Status: {hazard_status}
          </div>
          <div style="font-size:0.95rem; line-height:1.6;">
            {h_msg}
          </div>
        </div>
        """, unsafe_allow_html=True)

        # 2. Sensitivity x Velocity Matrix
        st.markdown("#### 感度 × 速度 マトリクス" if lang=="日本語" else "Sensitivity × Velocity Matrix")

        mx, my = to_axis_values(sens_level, vel_level)
        quad = quadrant_label(sens_level, vel_level)
        qmeta = QUADRANT_MESSAGES[quad]
        q_label = qmeta["日本語ラベル" if lang=="日本語" else "EnglishLabel"]
        q_text = qmeta["日本語" if lang=="日本語" else "English"]

        fig_matrix = go.Figure()
        fig_matrix.add_trace(go.Scatter(
            x=[mx], y=[my],
            mode="markers+text",
            text=[q_label],
            textposition="top center",
            marker=dict(size=20, color=h_meta['color'], line=dict(width=2, color='DarkSlateGrey'))
        ))
        
        # Quadrant Lines/Layout
        fig_matrix.update_layout(
            xaxis=dict(range=[-1.5,1.5], zeroline=True, tickvals=[-1,1], ticktext=["Low Sens","High Sens"]),
            yaxis=dict(range=[-1.5,1.5], zeroline=True, tickvals=[-1,0,1], ticktext=["Disconnect","Stable","Accel"]),
            height=300,
            margin=dict(l=40,r=40,t=20,b=20),
            plot_bgcolor='rgba(240,240,240,0.5)'
        )
        # Add annotation for axes? Maybe simple is better as per instructions
        
        st.plotly_chart(fig_matrix, use_container_width=True)
        
        st.markdown(f"""
        <div style="font-size:0.9rem; background:#f9f9f9; padding:10px; border-radius:5px; margin-bottom:30px; border-left:4px solid #666;">
            <b>{q_label}</b>: {q_text}
        </div>
        """, unsafe_allow_html=True)
        
        col_rel, col_cred, col_phys = st.columns(3)
        
        # 1) Relative Performance Card
        val_str_rel = "N/A"
        if rel_info:
            val_str_rel = f"Relative 20d: {rel_info['relative']*100:.1f}%"
        
        render_metric_card(col_rel, "Semi vs SOXX", val_str_rel, rel_status, RELATIVE_MSG, lang)
        
        
        # 2) DC Credit Card
        val_str_cred = "N/A"
        if cred_info:
            val_str_cred = f"Price Spread 60d: {cred_info['spread']*100:.1f}%"
        
        render_metric_card(col_cred, "DC Credit vs HY", val_str_cred, cred_status, DC_CREDIT_MSG, lang)

        
        # 3) Physical vs Market Card
        val_str_phys = "N/A"
        if phys_info:
            val_str_phys = f"Min PSR: {phys_info['min_psr']:.2f} / SPX 1m: {phys_info['spx_ret']*100:.1f}%"
            
        render_metric_card(col_phys, "Physical vs Market", val_str_phys, phys_status, PHYSICAL_MARKET_MSG, lang)

    except Exception as e:
        st.error(f"Error in Danger Source Monitor: {e}")



# --- Semiconductor Survivor Map (Live Status) ---

with tabs[4]:
    survivor_title = "Semiconductor Survivor Map" if lang == "English" else "半導体 Survivor マップ"
    st.subheader(survivor_title)

    # --- Survivor Logic ---

    def classify_struct_rank(psr: float) -> str:
        if pd.isna(psr): return "BROKEN"
        if psr >= 1.3: return "STRONG"
        elif psr >= 1.1: return "MID"
        elif psr >= 1.0: return "WEAK"
        else: return "BROKEN"

    def classify_market_rank(rel20: float, rel60: float) -> str:
        if pd.isna(rel20) or pd.isna(rel60): return "DUMPED"
        if rel20 >= -0.02 and rel60 >= -0.05: return "FAVORED"
        elif rel20 >= -0.08 and rel60 >= -0.15: return "NEUTRAL"
        else: return "DUMPED"

    def classify_final_class(struct_rank: str, market_rank: str,
                             psr: float, rel20: float, rel60: float) -> str:
        """
        Anti-Reverse Logic for Final Class
        """
        # Base
        base_survivor = (struct_rank in ["STRONG", "MID"] and market_rank in ["FAVORED", "NEUTRAL"])
        base_hazard   = (struct_rank in ["WEAK", "BROKEN"] and market_rank == "DUMPED")

        # Anti-Reverse: Require Margin for Promotion
        if base_survivor:
            # Strict condition for promotion
            if (psr >= 1.35) and (rel60 >= -0.02) and (rel20 >= -0.01):
                return "Survivor"
            else:
                return "Watch"

        if base_hazard:
            return "Hazard"

        # Default Middle
        return "Watch"

    @st.cache_data(ttl=3600)
    def get_semi_relative_returns(universe, days=180):
        # Fetch Universe + Benchmark
        px = fetch_price_series(universe + ["SOXX"], days=days)
        if px.empty:
            return {}
        
        # Common Dates
        px = px.dropna(how="any")

        results = {}
        
        def period_ret(series, window):
            if len(series) < window: return 0.0
            return float(series.iloc[-1] / series.iloc[-window] - 1.0)
        
        if "SOXX" not in px.columns:
            return {}

        soxx = px["SOXX"]
        r20x = period_ret(soxx, 20)
        r60x = period_ret(soxx, 60)

        for ticker in universe:
            if ticker not in px.columns:
                continue
            s = px[ticker]
            r20 = period_ret(s, 20)
            r60 = period_ret(s, 60)
            
            results[ticker] = {
                "R20": r20,
                "R60": r60,
                "R20_SOXX": r20x,
                "R60_SOXX": r60x,
                "rel20": r20 - r20x,
                "rel60": r60 - r60x
            }
        return results

    def build_semi_class_table(df_input, lang: str):
        # df_input should be survivor_df
        if df_input.empty:
            return pd.DataFrame()
        
        univ = df_input["Ticker"].tolist()
        rel_map = get_semi_relative_returns(univ, days=180)

        records = []
        for _, row in df_input.iterrows():
            ticker = row["Ticker"]
            psr = row.get("PSR", np.nan)
            
            rel = rel_map.get(ticker, {})
            rel20 = rel.get("rel20", np.nan)
            rel60 = rel.get("rel60", np.nan)

            if np.isnan(psr) or np.isnan(rel20) or np.isnan(rel60):
                final_class = "Unknown"
                struct_rank = None
                market_rank = None
            else:
                struct_rank = classify_struct_rank(psr)
                market_rank = classify_market_rank(rel20, rel60)
                final_class = classify_final_class(struct_rank, market_rank, psr, rel20, rel60)
            
            records.append({
                "Ticker": ticker,
                "PSR": psr,
                "rel20": rel20,
                "rel60": rel60,
                "StructRank": struct_rank,
                "MarketRank": market_rank,
                "Class": final_class
            })
        return pd.DataFrame(records)

    # --- UI Visualization ---

    if lang == "日本語":
        st.markdown("""
        AIサイクルのなかで<b>「どの装置銘柄が物理的に生き残りやすいか」</b>、<b>「どの銘柄が構造的な危険源になりつつあるか」</b>を可視化します。<br>
        横軸はPSRによる<b>物理的耐久度</b>、縦軸はSOXXに対する<b>相対パフォーマンス</b>です。
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        This map visualizes <b>which equipment names are physically positioned to survive the AI cycle versus which are becoming structural hazards</b>.<br>
        The X-axis represents <b>Physical Durability (PSR)</b>, and the Y-axis shows <b>Relative Performance vs SOXX</b>.
        """, unsafe_allow_html=True)

    # Compute Data
    semi_table = build_semi_class_table(survivor_df, lang)

    if semi_table.empty:
        st.warning("No data available for Survivor Universe.")
    else:
        # 1. Summary Counts
        cnt_surv = (semi_table["Class"] == "Survivor").sum()
        cnt_haz  = (semi_table["Class"] == "Hazard").sum()
        cnt_watch = (semi_table["Class"] == "Watch").sum()
        cnt_unknown = (semi_table["Class"] == "Unknown").sum()
        
        if lang == "日本語":
            unit = "銘柄"
            lbl_s, lbl_h, lbl_w, lbl_u = "Survivor", "Hazard", "Watch", "Unknown"
        else:
            unit = "Stocks"
            lbl_s, lbl_h, lbl_w, lbl_u = "Survivor", "Hazard", "Watch", "Unknown"

        c1, c2, c3, c4 = st.columns(4)
        # Cards
        for c, label, count, color in [
            (c1, f"{lbl_s}: {cnt_surv}", cnt_surv, "#007bff"),
            (c2, f"{lbl_h}: {cnt_haz}", cnt_haz, "#dc3545"),
            (c3, f"{lbl_w}: {cnt_watch}", cnt_watch, "#ffc107"),
            (c4, f"{lbl_u}: {cnt_unknown}", cnt_unknown, "#6c757d"),
        ]:
            with c:
                st.markdown(f"""
                <div class="metric-card" style="border-top:4px solid {color}; text-align:center; padding:15px;">
                  <div style="font-weight:bold; font-size:1rem; color:{color};">{label}</div>
                </div>
                """, unsafe_allow_html=True)

        # 2. Scatter Plot
        df_plot = semi_table.copy()
        # Clamp PSR for plotting
        if "PSR" in df_plot.columns:
            df_plot["PSR_clamped"] = df_plot["PSR"].clip(0, 2.5) # View range
            
            fig = go.Figure()
            
            color_map = {
                "Survivor": "#007bff", # Blue
                "Hazard": "#dc3545",   # Red
                "Watch": "#ffc107",    # Yellow
                "Unknown": "#6c757d"   # Gray
            }
            
            for cls in ["Survivor", "Hazard", "Watch", "Unknown"]:
                sub = df_plot[df_plot["Class"] == cls]
                if sub.empty: continue
                
                fig.add_trace(go.Scatter(
                    x=sub["PSR_clamped"],
                    y=sub["rel20"] * 100,
                    mode="markers+text",
                    text=sub["Ticker"],
                    textposition="top center",
                    marker=dict(size=14, color=color_map[cls], line=dict(width=1, color="#333"), opacity=0.9),
                    name=cls
                ))
                
            fig.add_vline(x=1.0, line_dash="dash", line_color="red", opacity=0.5, annotation_text="PSR=1.0")
            fig.add_vline(x=1.3, line_dash="dash", line_color="green", opacity=0.5, annotation_text="PSR=1.3")
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

            fig.update_layout(
                height=400,
                margin=dict(l=40, r=40, t=30, b=40),
                xaxis_title="Physical Durability (PSR)",
                yaxis_title="20d Relative vs SOXX (%)",
                plot_bgcolor="rgba(248,248,248,0.8)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)

        # 3. Detail Cards
        st.markdown("##### Detailed Status")
        d_cols = st.columns(len(semi_table))
        for i, row in semi_table.iterrows():
            # Iterate safely
            col = d_cols[i % 5] # wrap if many
            
            cls = row["Class"]
            color = color_map.get(cls, "#6c757d")
            ticker = row["Ticker"]
            psr = row.get("PSR", 0)
            r20 = row.get("rel20", 0) * 100
            r60 = row.get("rel60", 0) * 100
            
            with col:
                st.markdown(f"""
                <div class="metric-card" style="border-left:4px solid {color}; padding:15px;">
                  <div style="font-weight:700; margin-bottom:5px; font-size:1.1rem;">{ticker}</div>
                  <div style="font-size:0.8rem; color:#444; margin-bottom:2px;"><b>{cls}</b></div>
                  <div style="font-size:0.75rem; color:#666;">
                    PSR: {psr:.2f}<br>
                    20d Rel: {r20:+.1f}%<br>
                    60d Rel: {r60:+.1f}%
                  </div>
                </div>
                """, unsafe_allow_html=True)


