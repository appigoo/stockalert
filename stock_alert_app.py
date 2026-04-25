import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time
import threading
from datetime import datetime
import json

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
#  CUSTOM CSS  (dark trading terminal aesthetic)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

:root {
    --bg:        #0a0e17;
    --panel:     #111827;
    --border:    #1e3a5f;
    --accent:    #00d4ff;
    --green:     #00ff88;
    --red:       #ff4d6d;
    --yellow:    #ffd60a;
    --muted:     #4a6080;
    --text:      #ccd6f6;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Rajdhani', sans-serif;
}

[data-testid="stSidebar"] {
    background: #0d1420 !important;
    border-right: 1px solid var(--border);
}

h1, h2, h3 { font-family: 'Rajdhani', sans-serif; font-weight: 700; color: var(--accent); }
h1 { font-size: 2rem; letter-spacing: 2px; text-transform: uppercase; }

.metric-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 10px;
    font-family: 'Share Tech Mono', monospace;
}
.metric-card .ticker { color: var(--accent); font-size: 1.3rem; font-weight: 700; }
.metric-card .price  { color: var(--green); font-size: 1.6rem; }
.metric-card .vol    { color: var(--yellow); font-size: 0.9rem; }
.metric-card .status-ok   { color: var(--green); }
.metric-card .status-wait { color: var(--muted); }
.metric-card .status-trig { color: var(--red); font-weight: 700; animation: blink 1s step-end infinite; }

@keyframes blink { 50% { opacity: 0; } }

.alert-log {
    background: #080d14;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.82rem;
    color: var(--green);
    max-height: 320px;
    overflow-y: auto;
}
.alert-log .log-warn { color: var(--yellow); }
.alert-log .log-err  { color: var(--red); }

.pill-on  { background:#003322; color:var(--green); border:1px solid var(--green);
            border-radius:20px; padding:2px 12px; font-size:0.8rem; }
.pill-off { background:#1a0a00; color:var(--yellow); border:1px solid var(--yellow);
            border-radius:20px; padding:2px 12px; font-size:0.8rem; }

div[data-testid="stButton"] > button {
    background: transparent;
    border: 1px solid var(--accent);
    color: var(--accent);
    font-family: 'Rajdhani', sans-serif;
    font-weight: 600;
    letter-spacing: 1px;
    border-radius: 4px;
    transition: all .2s;
}
div[data-testid="stButton"] > button:hover {
    background: var(--accent);
    color: var(--bg);
}

div[data-testid="stSelectbox"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stTextInput"] label { color: var(--accent) !important; font-weight: 600; }

.stSelectbox > div > div { background: var(--panel) !important; border-color: var(--border) !important; }

hr { border-color: var(--border); }

/* hide Streamlit branding */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  TELEGRAM HELPERS
# ─────────────────────────────────────────────
def get_telegram_creds():
    try:
        token   = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        return token, chat_id
    except Exception:
        return None, None

def send_telegram(message: str) -> bool:
    token, chat_id = get_telegram_creds()
    if not token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False

def test_telegram() -> tuple[bool, str]:
    token, chat_id = get_telegram_creds()
    if not token:
        return False, "未找到 TELEGRAM_BOT_TOKEN"
    if not chat_id:
        return False, "未找到 TELEGRAM_CHAT_ID"
    ok = send_telegram("✅ <b>股票警報系統</b>\n測試訊息發送成功！")
    return ok, "發送成功！" if ok else "發送失敗，請檢查 Token / Chat ID"

# ─────────────────────────────────────────────
#  SESSION STATE INIT
# ─────────────────────────────────────────────
if "watchlist" not in st.session_state:
    # Each item: {ticker, price_dir, price_val, use_vol, vol_mult, vol_days, logic, enabled}
    st.session_state.watchlist = []

if "monitoring" not in st.session_state:
    st.session_state.monitoring = False

if "logs" not in st.session_state:
    st.session_state.logs = []

if "last_triggered" not in st.session_state:
    st.session_state.last_triggered = {}   # ticker -> last alert timestamp

if "market_data" not in st.session_state:
    st.session_state.market_data = {}      # ticker -> {price, volume, avg_vol, ts}

if "interval" not in st.session_state:
    st.session_state.interval = "5m"

if "check_freq" not in st.session_state:
    st.session_state.check_freq = 60       # seconds between checks

# ─────────────────────────────────────────────
#  DATA FETCH
# ─────────────────────────────────────────────
INTERVAL_MAP = {
    "1m":  ("1d",  "1m"),
    "2m":  ("5d",  "2m"),
    "5m":  ("5d",  "5m"),
    "15m": ("5d",  "15m"),
    "30m": ("1mo", "30m"),
}

def fetch_stock_data(ticker: str, interval: str) -> dict | None:
    period, tf = INTERVAL_MAP.get(interval, ("5d", "5m"))
    try:
        tk   = yf.Ticker(ticker)
        hist = tk.history(period=period, interval=tf)
        if hist.empty or len(hist) < 2:
            return None
        price   = float(hist["Close"].iloc[-1])
        volume  = float(hist["Volume"].iloc[-1])
        avg_vol = float(hist["Volume"].iloc[:-1].mean())
        return {
            "price":   price,
            "volume":  volume,
            "avg_vol": avg_vol,
            "vol_ratio": volume / avg_vol if avg_vol > 0 else 0,
            "ts":      datetime.now().strftime("%H:%M:%S"),
        }
    except Exception:
        return None

# ─────────────────────────────────────────────
#  CONDITION CHECKER
# ─────────────────────────────────────────────
def check_conditions(item: dict, data: dict) -> tuple[bool, str]:
    price   = data["price"]
    vol_r   = data["vol_ratio"]

    # Price condition
    if item["price_dir"] == "高於 >":
        price_ok = price > item["price_val"]
        price_desc = f"價格 ${price:.2f} > ${item['price_val']:.2f}"
    else:
        price_ok = price < item["price_val"]
        price_desc = f"價格 ${price:.2f} < ${item['price_val']:.2f}"

    # Volume condition
    if item["use_vol"]:
        vol_ok   = vol_r >= item["vol_mult"]
        vol_desc = f"成交量 {vol_r:.1f}x 均量（設定 {item['vol_mult']}x）"
    else:
        vol_ok   = True
        vol_desc = ""

    # Combine
    logic = item["logic"]
    if not item["use_vol"]:
        triggered = price_ok
        desc = price_desc
    elif logic == "AND（兩者同時）":
        triggered = price_ok and vol_ok
        desc = f"{price_desc}  &  {vol_desc}"
    else:
        triggered = price_ok or vol_ok
        desc = f"{price_desc}  |  {vol_desc}"

    return triggered, desc

# ─────────────────────────────────────────────
#  MONITORING LOOP  (runs in background thread)
# ─────────────────────────────────────────────
def monitoring_loop():
    while st.session_state.monitoring:
        interval = st.session_state.interval
        now      = time.time()

        for item in st.session_state.watchlist:
            if not item.get("enabled", True):
                continue
            ticker = item["ticker"]
            data   = fetch_stock_data(ticker, interval)
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
                # cooldown: don't re-alert within 5 minutes
                last = st.session_state.last_triggered.get(ticker, 0)
                if now - last > 300:
                    st.session_state.last_triggered[ticker] = now
                    msg = (
                        f"🔔 <b>股票警報！</b>\n"
                        f"📌 股票：<b>{ticker}</b>\n"
                        f"💰 價格：${data['price']:.2f}\n"
                        f"📊 成交量比率：{data['vol_ratio']:.1f}x\n"
                        f"✅ 條件：{desc}\n"
                        f"🕐 時間：{data['ts']}"
                    )
                    ok = send_telegram(msg)
                    log_entry = {
                        "ts":   data["ts"],
                        "msg":  f"[觸發] {ticker} ${data['price']:.2f} — {'Telegram 已發送 ✓' if ok else 'Telegram 發送失敗 ✗'}",
                        "type": "trig",
                    }
                    st.session_state.logs.insert(0, log_entry)

        # Keep logs at max 100
        st.session_state.logs = st.session_state.logs[:100]

        freq = st.session_state.check_freq
        time.sleep(freq)

# ─────────────────────────────────────────────
#  SIDEBAR — SETTINGS
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 系統設定")
    st.markdown("---")

    # Telegram test
    st.markdown("**Telegram 狀態**")
    tok, cid = get_telegram_creds()
    if tok and cid:
        st.markdown('<span class="pill-on">● Secrets 已設定</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="pill-off">● Secrets 未設定</span>', unsafe_allow_html=True)

    if st.button("📨 發送測試訊息"):
        ok, msg = test_telegram()
        if ok:
            st.success(msg)
        else:
            st.error(msg)

    st.markdown("---")
    st.markdown("**監控間隔**")
    interval_choice = st.selectbox(
        "K線週期",
        ["1m", "2m", "5m", "15m", "30m"],
        index=2,
        key="interval_sel",
    )
    st.session_state.interval = interval_choice

    check_freq_map = {"1m": 60, "2m": 120, "5m": 300, "15m": 900, "30m": 1800}
    st.session_state.check_freq = check_freq_map[interval_choice]
    st.caption(f"每 {st.session_state.check_freq // 60} 分鐘檢查一次")

    st.markdown("---")
    st.markdown("**新增股票警報**")

    with st.form("add_stock_form", clear_on_submit=True):
        new_ticker = st.text_input("股票代號", placeholder="TSLA").upper().strip()

        st.markdown("**價格條件**")
        col1, col2 = st.columns([1, 1])
        with col1:
            price_dir = st.selectbox("方向", ["高於 >", "低於 <"])
        with col2:
            price_val = st.number_input("價格 ($)", min_value=0.01, value=400.0, step=1.0)

        use_vol = st.checkbox("加入成交量條件", value=True)
        if use_vol:
            col3, col4 = st.columns([1, 1])
            with col3:
                vol_mult = st.number_input("量比 (x 均量)", min_value=1.0, value=2.0, step=0.5)
            with col4:
                logic = st.selectbox("條件邏輯", ["AND（兩者同時）", "OR（任一滿足）"])
        else:
            vol_mult = 2.0
            logic    = "AND（兩者同時）"

        submitted = st.form_submit_button("➕ 新增")
        if submitted:
            if not new_ticker:
                st.error("請輸入股票代號")
            elif any(w["ticker"] == new_ticker for w in st.session_state.watchlist):
                st.warning(f"{new_ticker} 已在監控列表中")
            else:
                st.session_state.watchlist.append({
                    "ticker":    new_ticker,
                    "price_dir": price_dir,
                    "price_val": price_val,
                    "use_vol":   use_vol,
                    "vol_mult":  vol_mult,
                    "logic":     logic,
                    "enabled":   True,
                })
                st.success(f"已新增 {new_ticker}")

# ─────────────────────────────────────────────
#  MAIN PANEL
# ─────────────────────────────────────────────
st.markdown("# 🔔 股票即時警報系統")
st.markdown(f"資料來源：**yfinance** ｜ 週期：**{st.session_state.interval}** ｜ 每 **{st.session_state.check_freq // 60}** 分鐘刷新")
st.markdown("---")

# Start / Stop buttons
col_a, col_b, col_c = st.columns([1, 1, 4])
with col_a:
    if st.button("▶ 開始監控", disabled=st.session_state.monitoring):
        if not st.session_state.watchlist:
            st.error("請先在側欄新增至少一隻股票")
        else:
            st.session_state.monitoring = True
            t = threading.Thread(target=monitoring_loop, daemon=True)
            t.start()
            st.success("監控已啟動！")

with col_b:
    if st.button("⏹ 停止監控", disabled=not st.session_state.monitoring):
        st.session_state.monitoring = False
        st.info("監控已停止")

status_label = (
    '<span class="pill-on">● 監控中</span>' if st.session_state.monitoring
    else '<span class="pill-off">● 已停止</span>'
)
with col_c:
    st.markdown(status_label, unsafe_allow_html=True)

st.markdown("---")

# ─── Watchlist cards ───
if not st.session_state.watchlist:
    st.info("👈 請在左側側欄新增要監控的股票")
else:
    st.markdown("### 📋 監控列表")

    for i, item in enumerate(st.session_state.watchlist):
        ticker = item["ticker"]
        data   = st.session_state.market_data.get(ticker)

        # Build condition summary
        cond_price = f"價格 {item['price_dir']} ${item['price_val']:.2f}"
        if item["use_vol"]:
            cond_vol = f"成交量 ≥ {item['vol_mult']}x 均量"
            logic_str = "AND" if "AND" in item["logic"] else "OR"
            cond_full = f"{cond_price}  <b>{logic_str}</b>  {cond_vol}"
        else:
            cond_full = cond_price

        if data:
            triggered, _ = check_conditions(item, data)
            status_cls  = "status-trig" if triggered else "status-ok"
            status_txt  = "🚨 條件觸發！" if triggered else "✅ 監控中"
            price_str   = f"${data['price']:.2f}"
            vol_str     = f"成交量比率：{data['vol_ratio']:.1f}x | 更新：{data['ts']}"
        else:
            status_cls  = "status-wait"
            status_txt  = "⏳ 等待數據..."
            price_str   = "—"
            vol_str     = ""

        enabled_icon = "🟢" if item["enabled"] else "⚫"

        card_html = f"""
        <div class="metric-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="ticker">{enabled_icon} {ticker}</span>
                <span class="{status_cls}">{status_txt}</span>
            </div>
            <div class="price">{price_str}</div>
            <div class="vol">{vol_str}</div>
            <div style="margin-top:6px; font-size:0.82rem; color:#4a9eba;">條件：{cond_full}</div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

        col_en, col_del, _ = st.columns([1, 1, 6])
        with col_en:
            label = "暫停" if item["enabled"] else "啟用"
            if st.button(label, key=f"tog_{i}"):
                st.session_state.watchlist[i]["enabled"] = not item["enabled"]
                st.rerun()
        with col_del:
            if st.button("🗑 刪除", key=f"del_{i}"):
                st.session_state.watchlist.pop(i)
                st.session_state.market_data.pop(ticker, None)
                st.rerun()

# ─── Alert log ───
st.markdown("---")
st.markdown("### 📜 警報記錄")

if st.session_state.logs:
    if st.button("🗑 清除記錄"):
        st.session_state.logs = []
        st.rerun()

    log_html_parts = []
    for entry in st.session_state.logs[:50]:
        cls = {"trig": "status-trig", "warn": "log-warn", "err": "log-err"}.get(entry["type"], "")
        log_html_parts.append(f'<div class="{cls}">[{entry["ts"]}] {entry["msg"]}</div>')

    st.markdown(
        f'<div class="alert-log">{"".join(log_html_parts)}</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown('<div class="alert-log"><span style="color:#4a6080">— 尚無記錄 —</span></div>', unsafe_allow_html=True)

# ─── Auto-refresh when monitoring ───
if st.session_state.monitoring:
    time.sleep(2)
    st.rerun()
