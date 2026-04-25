import streamlit as st
import yfinance as yf
import requests
import time
from datetime import datetime

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="股票警報系統",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CSS — light, warm, rounded card style
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Noto+Sans+TC:wght@400;500;700&display=swap');

:root {
    --bg:        #f5f3ee;
    --surface:   #ffffff;
    --surface2:  #f0ede6;
    --border:    #ddd9cf;
    --accent:    #3a7d5e;
    --accent2:   #5a9e7a;
    --red:       #c0392b;
    --orange:    #e07b39;
    --yellow:    #c9a227;
    --muted:     #9a9487;
    --text:      #2d2a22;
    --text2:     #6b6457;
    --mono:      'IBM Plex Mono', monospace;
    --sans:      'Noto Sans TC', sans-serif;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--sans);
}
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { font-family: var(--sans); }

/* typography */
h1 { font-family: var(--sans); font-size: 1.5rem; font-weight: 700; color: var(--text); letter-spacing: .5px; }
h2, h3 { font-family: var(--sans); font-weight: 700; color: var(--text); font-size: 1rem; }
label { color: var(--text2) !important; font-size: 0.85rem !important; }

/* cards */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}
.ticker-label {
    font-family: var(--mono);
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: 1px;
}
.price-display {
    font-family: var(--mono);
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--text);
    margin: 4px 0;
}
.vol-display {
    font-family: var(--mono);
    font-size: 0.82rem;
    color: var(--muted);
    margin-top: 2px;
}
.cond-display {
    font-family: var(--mono);
    font-size: 0.78rem;
    color: var(--text2);
    background: var(--surface2);
    border-radius: 6px;
    padding: 5px 10px;
    margin-top: 10px;
    border-left: 3px solid var(--accent);
}

/* status badges */
.badge {
    font-family: var(--mono);
    font-size: 0.75rem;
    border-radius: 20px;
    padding: 3px 12px;
    font-weight: 600;
    letter-spacing: .5px;
}
.badge-on    { background:#e8f5ee; color:#2e7d52; border:1px solid #b2d8c0; }
.badge-off   { background:#fdf3e3; color:#b07c1a; border:1px solid #f0d494; }
.badge-wait  { background:#f0ede6; color:#9a9487; border:1px solid #ddd9cf; }
.badge-trig  { background:#fdecea; color:#c0392b; border:1px solid #f5b7b1; }

/* status dot */
.dot-ok   { color: #3a7d5e; }
.dot-wait { color: #9a9487; }
.dot-trig { color: #c0392b; font-weight: 700; }

/* log panel */
.log-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px 16px;
    font-family: var(--mono);
    font-size: 0.78rem;
    color: var(--text2);
    max-height: 280px;
    overflow-y: auto;
    line-height: 1.9;
}
.log-trig  { color: var(--red); }
.log-warn  { color: var(--orange); }
.log-info  { color: var(--text2); }

/* section labels */
.section-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 8px;
    margin-top: 4px;
}

/* divider */
.divider { border: none; border-top: 1px solid var(--border); margin: 16px 0; }

/* Streamlit overrides */
div[data-testid="stButton"] > button {
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text);
    font-family: var(--sans);
    font-size: 0.85rem;
    border-radius: 8px;
    padding: 4px 14px;
    transition: all .15s;
}
div[data-testid="stButton"] > button:hover {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
}
div[data-testid="stButton"] > button:disabled {
    opacity: 0.35;
}
.stSelectbox > div > div,
.stNumberInput > div > div > input,
.stTextInput > div > div > input {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: 0.85rem !important;
}
div[data-testid="stSelectbox"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stCheckbox"] label {
    color: var(--text2) !important;
    font-size: 0.82rem !important;
    font-family: var(--sans) !important;
}
.stAlert { border-radius: 10px !important; }
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
defaults = {
    "watchlist":       [],
    "monitoring":      False,
    "logs":            [],
    "last_triggered":  {},
    "market_data":     {},
    "kline_period":    "5m",    # yfinance interval for OHLCV data
    "check_interval":  60,      # seconds between monitor cycles
    "last_check_time": 0.0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
# yfinance requires a matching period for each interval
KLINE_PERIOD_MAP = {
    "1m":  "1d",
    "5m":  "5d",
    "15m": "5d",
    "30m": "1mo",
    "1h":  "1mo",
    "1d":  "1y",
}

CHECK_INTERVAL_OPTIONS = {
    "30秒":   30,
    "1分鐘":  60,
    "2分鐘":  120,
    "5分鐘":  300,
    "10分鐘": 600,
    "15分鐘": 900,
}

KLINE_OPTIONS = ["1m", "5m", "15m", "30m", "1h", "1d"]

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def fetch_stock_data(ticker: str, kline: str, vol_days: int = 20):
    period = KLINE_PERIOD_MAP.get(kline, "5d")
    try:
        hist = yf.Ticker(ticker).history(period=period, interval=kline)
        if hist.empty or len(hist) < 2:
            return None
        price   = float(hist["Close"].iloc[-1])
        volume  = float(hist["Volume"].iloc[-1])
        # Use last N bars (excluding current) for average; cap at available bars
        n       = min(vol_days, len(hist) - 1)
        avg_vol = float(hist["Volume"].iloc[-1 - n : -1].mean()) if n > 0 else 0
        vol_ratio = volume / avg_vol if avg_vol > 0 else 0
        return {
            "price":     price,
            "volume":    volume,
            "avg_vol":   avg_vol,
            "vol_ratio": vol_ratio,
            "vol_days":  n,           # actual bars used (may be less than requested)
            "ts":        datetime.now().strftime("%H:%M:%S"),
        }
    except Exception:
        return None

def check_conditions(item: dict, data: dict):
    price = data["price"]
    vol_r = data["vol_ratio"]

    if item["price_dir"] == "高於 >":
        price_ok   = price > item["price_val"]
        price_desc = f"價格 ${price:.2f} > ${item['price_val']:.2f}"
    else:
        price_ok   = price < item["price_val"]
        price_desc = f"價格 ${price:.2f} < ${item['price_val']:.2f}"

    if item["use_vol"]:
        vol_ok   = vol_r >= item["vol_mult"]
        n_actual = data.get("vol_days", item.get("vol_days", 20))
        vol_desc = f"量比 {vol_r:.2f}x ≥ {item['vol_mult']}x（{n_actual}根均量）"
        if "AND" in item["logic"]:
            triggered = price_ok and vol_ok
            desc = f"{price_desc}  AND  {vol_desc}"
        else:
            triggered = price_ok or vol_ok
            desc = f"{price_desc}  OR  {vol_desc}"
    else:
        triggered = price_ok
        desc      = price_desc

    return triggered, desc

def get_telegram_creds():
    try:
        return st.secrets["TELEGRAM_BOT_TOKEN"], st.secrets["TELEGRAM_CHAT_ID"]
    except Exception:
        return None, None

def send_telegram(message: str) -> bool:
    token, chat_id = get_telegram_creds()
    if not token or not chat_id:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
        return r.status_code == 200
    except Exception:
        return False

# ─────────────────────────────────────────────
#  POLL CYCLE
# ─────────────────────────────────────────────
def run_poll_cycle():
    now = time.time()
    if now - st.session_state.last_check_time < st.session_state.check_interval:
        return
    st.session_state.last_check_time = now

    kline = st.session_state.kline_period
    for item in st.session_state.watchlist:
        if not item.get("enabled", True):
            continue
        ticker = item["ticker"]
        vol_days = item.get("vol_days", 20)
        data     = fetch_stock_data(ticker, kline, vol_days)

        if data is None:
            st.session_state.logs.insert(0, {
                "ts": datetime.now().strftime("%H:%M:%S"),
                "msg": f"[警告] {ticker} 數據獲取失敗",
                "type": "warn",
            })
            continue

        st.session_state.market_data[ticker] = data
        triggered, desc = check_conditions(item, data)

        if triggered:
            last = st.session_state.last_triggered.get(ticker, 0)
            if now - last > 300:
                st.session_state.last_triggered[ticker] = now
                n_actual = data.get("vol_days", vol_days)
                msg = (
                    f"🔔 <b>股票警報！</b>\n"
                    f"📌 股票：<b>{ticker}</b>\n"
                    f"💰 價格：${data['price']:.2f}\n"
                    f"📊 成交量：{data['volume']:,.0f}  (均量 {data['avg_vol']:,.0f}，{n_actual} 根)\n"
                    f"📈 量比：{data['vol_ratio']:.2f}x\n"
                    f"✅ 條件：{desc}\n"
                    f"🕐 時間：{data['ts']}"
                )
                ok = send_telegram(msg)
                st.session_state.logs.insert(0, {
                    "ts": data["ts"],
                    "msg": f"[觸發] {ticker} ${data['price']:.2f} — {'Telegram ✓' if ok else 'Telegram 失敗 ✗'}",
                    "type": "trig",
                })

    st.session_state.logs = st.session_state.logs[:100]

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 系統設定")
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Telegram ──
    st.markdown('<div class="section-label">Telegram</div>', unsafe_allow_html=True)
    tok, cid = get_telegram_creds()
    if tok and cid:
        st.markdown('<span class="badge badge-on">● Secrets 已設定</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-off">● Secrets 未設定</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📨 發送測試訊息"):
        if not tok or not cid:
            st.error("請先設定 Streamlit Secrets")
        else:
            ok = send_telegram("✅ <b>股票警報系統</b>\n測試訊息發送成功！")
            st.success("發送成功！") if ok else st.error("發送失敗，請檢查 Token/Chat ID")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Monitoring interval (separate from K-line) ──
    st.markdown('<div class="section-label">監控間隔（多久檢查一次）</div>', unsafe_allow_html=True)
    check_label = st.selectbox(
        "檢查頻率",
        list(CHECK_INTERVAL_OPTIONS.keys()),
        index=1,   # default 1分鐘
        key="check_interval_sel",
        label_visibility="collapsed",
    )
    st.session_state.check_interval = CHECK_INTERVAL_OPTIONS[check_label]
    st.caption(f"每 {check_label} 向 yfinance 查詢一次")

    st.markdown('<br>', unsafe_allow_html=True)

    # ── K-line period (separate) ──
    st.markdown('<div class="section-label">K線週期（數據 Timeframe）</div>', unsafe_allow_html=True)
    kline_choice = st.selectbox(
        "K線週期",
        KLINE_OPTIONS,
        index=1,   # default 5m
        key="kline_sel",
        label_visibility="collapsed",
    )
    st.session_state.kline_period = kline_choice
    st.caption(f"使用 yfinance {kline_choice} K線數據計算條件")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Add stock ──
    st.markdown('<div class="section-label">新增股票警報</div>', unsafe_allow_html=True)

    with st.form("add_stock_form", clear_on_submit=True):
        new_ticker = st.text_input("股票代號", placeholder="TSLA").upper().strip()

        c1, c2 = st.columns(2)
        with c1:
            price_dir = st.selectbox("價格方向", ["高於 >", "低於 <"])
        with c2:
            price_val = st.number_input("目標價 ($)", min_value=0.01, value=400.0, step=1.0)

        use_vol = st.checkbox("＋成交量條件", value=True)
        vol_mult, vol_days, logic = 2.0, 20, "AND（兩者同時）"
        if use_vol:
            c3, c4 = st.columns(2)
            with c3:
                vol_mult = st.number_input("量比 X (×均量)", min_value=1.0, value=2.0, step=0.5)
            with c4:
                vol_days = st.number_input("均量根數 N", min_value=1, max_value=200, value=20, step=1)
            logic = st.selectbox("條件邏輯", ["AND（兩者同時）", "OR（任一滿足）"])

        if st.form_submit_button("➕ 新增"):
            if not new_ticker:
                st.error("請輸入股票代號")
            elif any(w["ticker"] == new_ticker for w in st.session_state.watchlist):
                st.warning(f"{new_ticker} 已在列表中")
            else:
                st.session_state.watchlist.append({
                    "ticker":    new_ticker,
                    "price_dir": price_dir,
                    "price_val": price_val,
                    "use_vol":   use_vol,
                    "vol_mult":  vol_mult,
                    "vol_days":  vol_days,
                    "logic":     logic,
                    "enabled":   True,
                })
                data = fetch_stock_data(new_ticker, st.session_state.kline_period, vol_days)
                if data:
                    st.session_state.market_data[new_ticker] = data
                st.rerun()

# ─────────────────────────────────────────────
#  MAIN PANEL
# ─────────────────────────────────────────────

# ── Header ──
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown("# 🔔 股票警報系統")

elapsed   = time.time() - st.session_state.last_check_time
remaining = max(0, st.session_state.check_interval - elapsed)

with col_status:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.monitoring:
        st.markdown(f'<span class="badge badge-on">● 監控中</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-off">● 已停止</span>', unsafe_allow_html=True)

# ── Config summary bar ──
kline_lbl   = st.session_state.kline_period
check_lbl   = [k for k, v in CHECK_INTERVAL_OPTIONS.items() if v == st.session_state.check_interval][0]
if st.session_state.monitoring and st.session_state.last_check_time > 0:
    next_str = f"下次更新：{int(remaining // 60)}分 {int(remaining % 60)}秒後"
elif st.session_state.last_check_time == 0:
    next_str = "尚未開始"
else:
    next_str = "已停止"

st.markdown(
    f'<div style="font-family:var(--mono);font-size:0.8rem;color:var(--muted);margin-bottom:16px;">'
    f'K線週期：<b style="color:var(--text2)">{kline_lbl}</b> &nbsp;｜&nbsp; '
    f'監控間隔：<b style="color:var(--text2)">{check_lbl}</b> &nbsp;｜&nbsp; '
    f'{next_str}</div>',
    unsafe_allow_html=True,
)

# ── Control buttons ──
cb1, cb2, cb3 = st.columns([1, 1, 5])
with cb1:
    if st.button("▶ 開始", disabled=st.session_state.monitoring):
        if not st.session_state.watchlist:
            st.error("請先新增股票")
        else:
            st.session_state.monitoring      = True
            st.session_state.last_check_time = 0.0
            st.rerun()
with cb2:
    if st.button("⏹ 停止", disabled=not st.session_state.monitoring):
        st.session_state.monitoring = False
        st.rerun()

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ── Poll cycle ──
if st.session_state.monitoring:
    run_poll_cycle()

# ── Watchlist ──
if not st.session_state.watchlist:
    st.markdown(
        '<div class="card" style="text-align:center;color:var(--muted);padding:40px;">'
        '← 請在左側新增要監控的股票'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown('<div class="section-label">監控列表</div>', unsafe_allow_html=True)

    for i, item in enumerate(st.session_state.watchlist):
        ticker = item["ticker"]
        data   = st.session_state.market_data.get(ticker)

        # Build condition text
        cond_price = f"{item['price_dir']}  ${item['price_val']:.2f}"
        if item["use_vol"]:
            n_cfg     = item.get("vol_days", 20)
            logic_str = "AND" if "AND" in item["logic"] else "OR"
            cond_text = f"價格 {cond_price}  {logic_str}  成交量 ≥ {item['vol_mult']}× （{n_cfg}根均量）"
        else:
            cond_text = f"價格 {cond_price}"

        if data:
            triggered, _ = check_conditions(item, data)
            badge_cls  = "badge-trig" if triggered else "badge-on"
            badge_txt  = "🚨 條件觸發" if triggered else "✓ 監控中"
            dot_cls    = "dot-trig"   if triggered else "dot-ok"
            price_str  = f"${data['price']:,.2f}"
            n_actual   = data.get("vol_days", item.get("vol_days", 20))
            vol_str    = (
                f"量比 {data['vol_ratio']:.2f}×  ｜  "
                f"均量（{n_actual}根）{data['avg_vol']:,.0f}  ｜  "
                f"更新 {data['ts']}"
            )
        else:
            badge_cls  = "badge-wait"
            badge_txt  = "⏳ 等待數據"
            dot_cls    = "dot-wait"
            price_str  = "—"
            vol_str    = "開始監控後自動載入"

        enabled_dot = "●" if item["enabled"] else "○"
        enabled_col = "var(--accent)" if item["enabled"] else "var(--muted)"

        st.markdown(f"""
        <div class="card">
            <div class="card-header">
                <span class="ticker-label">
                    <span style="color:{enabled_col};font-size:0.9rem;">{enabled_dot}</span>
                    &nbsp;{ticker}
                </span>
                <span class="badge {badge_cls}">{badge_txt}</span>
            </div>
            <div class="price-display">{price_str}</div>
            <div class="vol-display">{vol_str}</div>
            <div class="cond-display">條件：{cond_text}</div>
        </div>
        """, unsafe_allow_html=True)

        btn1, btn2, _ = st.columns([1, 1, 6])
        with btn1:
            lbl = "暫停" if item["enabled"] else "啟用"
            if st.button(lbl, key=f"tog_{i}"):
                st.session_state.watchlist[i]["enabled"] = not item["enabled"]
                st.rerun()
        with btn2:
            if st.button("刪除", key=f"del_{i}"):
                st.session_state.watchlist.pop(i)
                st.session_state.market_data.pop(ticker, None)
                st.rerun()

# ── Alert log ──
st.markdown('<hr class="divider">', unsafe_allow_html=True)

log_col, clr_col = st.columns([5, 1])
with log_col:
    st.markdown('<div class="section-label">警報記錄</div>', unsafe_allow_html=True)
with clr_col:
    if st.session_state.logs:
        if st.button("清除"):
            st.session_state.logs = []
            st.rerun()

if st.session_state.logs:
    rows = []
    for e in st.session_state.logs[:60]:
        cls = "log-trig" if e["type"] == "trig" else ("log-warn" if e["type"] == "warn" else "log-info")
        rows.append(f'<div class="{cls}">[{e["ts"]}]&nbsp;&nbsp;{e["msg"]}</div>')
    st.markdown(f'<div class="log-panel">{"".join(rows)}</div>', unsafe_allow_html=True)
else:
    st.markdown(
        '<div class="log-panel" style="color:var(--muted);text-align:center;padding:30px 0;">— 尚無警報記錄 —</div>',
        unsafe_allow_html=True,
    )

# ── Auto-rerun loop ──
if st.session_state.monitoring:
    elapsed   = time.time() - st.session_state.last_check_time
    sleep_sec = max(5, st.session_state.check_interval - elapsed)
    time.sleep(min(sleep_sec, 20))
    st.rerun()
