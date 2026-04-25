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
#  CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

:root {
    --bg:     #0a0e17;
    --panel:  #111827;
    --border: #1e3a5f;
    --accent: #00d4ff;
    --green:  #00ff88;
    --red:    #ff4d6d;
    --yellow: #ffd60a;
    --muted:  #4a6080;
    --text:   #ccd6f6;
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
.status-ok   { color: var(--green); }
.status-wait { color: var(--muted); }
.status-trig { color: var(--red); font-weight: 700; }

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
.log-warn { color: var(--yellow); }
.log-trig { color: var(--red); font-weight: 700; }

.pill-on  { background:#003322; color:var(--green); border:1px solid var(--green);
            border-radius:20px; padding:2px 14px; font-size:0.85rem; }
.pill-off { background:#1a0a00; color:var(--yellow); border:1px solid var(--yellow);
            border-radius:20px; padding:2px 14px; font-size:0.85rem; }

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
hr { border-color: var(--border); }
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
    "last_triggered":  {},    # ticker -> unix timestamp
    "market_data":     {},    # ticker -> {price, vol_ratio, ts}
    "interval":        "5m",
    "check_freq":      300,
    "last_check_time": 0.0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
INTERVAL_MAP = {
    "1m":  ("1d",  "1m"),
    "2m":  ("5d",  "2m"),
    "5m":  ("5d",  "5m"),
    "15m": ("5d",  "15m"),
    "30m": ("1mo", "30m"),
}

def fetch_stock_data(ticker: str, interval: str):
    period, tf = INTERVAL_MAP.get(interval, ("5d", "5m"))
    try:
        hist = yf.Ticker(ticker).history(period=period, interval=tf)
        if hist.empty or len(hist) < 2:
            return None
        price     = float(hist["Close"].iloc[-1])
        volume    = float(hist["Volume"].iloc[-1])
        avg_vol   = float(hist["Volume"].iloc[:-1].mean())
        vol_ratio = volume / avg_vol if avg_vol > 0 else 0
        return {
            "price":     price,
            "vol_ratio": vol_ratio,
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
        vol_desc = f"量比 {vol_r:.1f}x ≥ {item['vol_mult']}x"
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
#  POLL CYCLE — called on every rerun
# ─────────────────────────────────────────────
def run_poll_cycle():
    """Fetch data & check alerts. Skips if called too soon after last cycle."""
    now = time.time()
    if now - st.session_state.last_check_time < st.session_state.check_freq:
        return
    st.session_state.last_check_time = now

    interval = st.session_state.interval
    for item in st.session_state.watchlist:
        if not item.get("enabled", True):
            continue
        ticker = item["ticker"]
        data   = fetch_stock_data(ticker, interval)

        if data is None:
            st.session_state.logs.insert(0, {
                "ts":   datetime.now().strftime("%H:%M:%S"),
                "msg":  f"[警告] {ticker} 數據獲取失敗",
                "type": "warn",
            })
            continue

        st.session_state.market_data[ticker] = data
        triggered, desc = check_conditions(item, data)

        if triggered:
            last = st.session_state.last_triggered.get(ticker, 0)
            if now - last > 300:   # 5-min cooldown
                st.session_state.last_triggered[ticker] = now
                msg = (
                    f"🔔 <b>股票警報！</b>\n"
                    f"📌 股票：<b>{ticker}</b>\n"
                    f"💰 價格：${data['price']:.2f}\n"
                    f"📊 量比：{data['vol_ratio']:.1f}x\n"
                    f"✅ 條件：{desc}\n"
                    f"🕐 時間：{data['ts']}"
                )
                ok = send_telegram(msg)
                st.session_state.logs.insert(0, {
                    "ts":   data["ts"],
                    "msg":  f"[觸發] {ticker} ${data['price']:.2f} ─ {'Telegram ✓' if ok else 'Telegram 發送失敗 ✗'}",
                    "type": "trig",
                })

    st.session_state.logs = st.session_state.logs[:100]

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 系統設定")
    st.markdown("---")

    tok, cid = get_telegram_creds()
    st.markdown("**Telegram 狀態**")
    if tok and cid:
        st.markdown('<span class="pill-on">● Secrets 已設定</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="pill-off">● Secrets 未設定</span>', unsafe_allow_html=True)

    if st.button("📨 發送測試訊息"):
        if not tok:
            st.error("未找到 TELEGRAM_BOT_TOKEN")
        elif not cid:
            st.error("未找到 TELEGRAM_CHAT_ID")
        else:
            ok = send_telegram("✅ <b>股票警報系統</b>\n測試訊息發送成功！")
            st.success("發送成功！") if ok else st.error("發送失敗，請檢查 Token/Chat ID")

    st.markdown("---")
    st.markdown("**監控間隔**")
    interval_choice = st.selectbox(
        "K線週期", ["1m", "2m", "5m", "15m", "30m"], index=2, key="interval_sel"
    )
    freq_map = {"1m": 60, "2m": 120, "5m": 300, "15m": 900, "30m": 1800}
    st.session_state.interval   = interval_choice
    st.session_state.check_freq = freq_map[interval_choice]
    st.caption(f"每 {st.session_state.check_freq // 60} 分鐘輪詢一次")

    st.markdown("---")
    st.markdown("**新增股票警報**")

    with st.form("add_stock_form", clear_on_submit=True):
        new_ticker = st.text_input("股票代號", placeholder="例如 TSLA").upper().strip()

        st.markdown("**價格條件**")
        c1, c2 = st.columns(2)
        with c1:
            price_dir = st.selectbox("方向", ["高於 >", "低於 <"])
        with c2:
            price_val = st.number_input("價格 ($)", min_value=0.01, value=400.0, step=1.0)

        use_vol = st.checkbox("加入成交量條件", value=True)
        vol_mult, logic = 2.0, "AND（兩者同時）"
        if use_vol:
            c3, c4 = st.columns(2)
            with c3:
                vol_mult = st.number_input("量比 (x 均量)", min_value=1.0, value=2.0, step=0.5)
            with c4:
                logic = st.selectbox("邏輯", ["AND（兩者同時）", "OR（任一滿足）"])

        if st.form_submit_button("➕ 新增"):
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
                # Immediately fetch so the card shows data right away
                data = fetch_stock_data(new_ticker, st.session_state.interval)
                if data:
                    st.session_state.market_data[new_ticker] = data
                st.rerun()

# ─────────────────────────────────────────────
#  MAIN PANEL
# ─────────────────────────────────────────────
st.markdown("# 🔔 股票即時警報系統")

elapsed   = time.time() - st.session_state.last_check_time
remaining = max(0, st.session_state.check_freq - elapsed)
if st.session_state.last_check_time == 0:
    timing_info = "尚未開始"
elif st.session_state.monitoring:
    timing_info = f"下次刷新：{int(remaining // 60)}分 {int(remaining % 60)}秒後"
else:
    timing_info = "已停止"

st.markdown(f"資料來源：**yfinance** ｜ 週期：**{st.session_state.interval}** ｜ {timing_info}")
st.markdown("---")

# Start / Stop buttons
ca, cb, cc = st.columns([1, 1, 4])
with ca:
    if st.button("▶ 開始監控", disabled=st.session_state.monitoring):
        if not st.session_state.watchlist:
            st.error("請先在側欄新增至少一隻股票")
        else:
            st.session_state.monitoring      = True
            st.session_state.last_check_time = 0.0   # force immediate first poll
            st.rerun()

with cb:
    if st.button("⏹ 停止監控", disabled=not st.session_state.monitoring):
        st.session_state.monitoring = False
        st.rerun()

with cc:
    label = '<span class="pill-on">● 監控中</span>' if st.session_state.monitoring \
            else '<span class="pill-off">● 已停止</span>'
    st.markdown(label, unsafe_allow_html=True)

st.markdown("---")

# ── Run poll cycle (only does real work when interval has elapsed) ──
if st.session_state.monitoring:
    run_poll_cycle()

# ── Watchlist cards ──
if not st.session_state.watchlist:
    st.info("👈 請在左側側欄新增要監控的股票")
else:
    st.markdown("### 📋 監控列表")
    for i, item in enumerate(st.session_state.watchlist):
        ticker = item["ticker"]
        data   = st.session_state.market_data.get(ticker)

        cond_price = f"價格 {item['price_dir']} ${item['price_val']:.2f}"
        if item["use_vol"]:
            logic_str = "AND" if "AND" in item["logic"] else "OR"
            cond_full = f"{cond_price}  <b>{logic_str}</b>  成交量 ≥ {item['vol_mult']}x 均量"
        else:
            cond_full = cond_price

        if data:
            triggered, _ = check_conditions(item, data)
            status_cls = "status-trig" if triggered else "status-ok"
            status_txt = "🚨 條件觸發！" if triggered else "✅ 監控中"
            price_str  = f"${data['price']:.2f}"
            vol_str    = f"成交量比率：{data['vol_ratio']:.1f}x ｜ 更新：{data['ts']}"
        else:
            status_cls = "status-wait"
            status_txt = "⏳ 等待數據..."
            price_str  = "—"
            vol_str    = "點擊「開始監控」後自動獲取數據"

        enabled_icon = "🟢" if item["enabled"] else "⚫"

        st.markdown(f"""
        <div class="metric-card">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span class="ticker">{enabled_icon} {ticker}</span>
                <span class="{status_cls}">{status_txt}</span>
            </div>
            <div class="price">{price_str}</div>
            <div class="vol">{vol_str}</div>
            <div style="margin-top:6px;font-size:0.82rem;color:#4a9eba;">條件：{cond_full}</div>
        </div>
        """, unsafe_allow_html=True)

        ce, cd, _ = st.columns([1, 1, 6])
        with ce:
            if st.button("暫停" if item["enabled"] else "啟用", key=f"tog_{i}"):
                st.session_state.watchlist[i]["enabled"] = not item["enabled"]
                st.rerun()
        with cd:
            if st.button("🗑 刪除", key=f"del_{i}"):
                st.session_state.watchlist.pop(i)
                st.session_state.market_data.pop(ticker, None)
                st.rerun()

# ── Alert log ──
st.markdown("---")
st.markdown("### 📜 警報記錄")

if st.session_state.logs:
    if st.button("🗑 清除記錄"):
        st.session_state.logs = []
        st.rerun()
    parts = []
    for e in st.session_state.logs[:50]:
        cls = "log-trig" if e["type"] == "trig" else ("log-warn" if e["type"] == "warn" else "")
        parts.append(f'<div class="{cls}">[{e["ts"]}] {e["msg"]}</div>')
    st.markdown(f'<div class="alert-log">{"".join(parts)}</div>', unsafe_allow_html=True)
else:
    st.markdown(
        '<div class="alert-log"><span style="color:#4a6080">— 尚無記錄 —</span></div>',
        unsafe_allow_html=True,
    )

# ── Auto-rerun loop: wake up when next poll is due ──
if st.session_state.monitoring:
    elapsed   = time.time() - st.session_state.last_check_time
    sleep_sec = max(5, st.session_state.check_freq - elapsed)
    # sleep_sec is how long until the next poll is needed;
    # we sleep briefly here so the page stays "live" and reruns itself
    time.sleep(min(sleep_sec, 30))  # wake up every 30s at most to refresh countdown
    st.rerun()
