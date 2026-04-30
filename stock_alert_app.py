import streamlit as st
import yfinance as yf
import requests
import time
import json
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

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
#  FILE-BASED PERSISTENCE  (/tmp — no JS, no extra packages)
# ─────────────────────────────────────────────
# /tmp persists across Streamlit hot-reloads and user page refreshes
# within the same Streamlit Cloud container session.
# It is the most reliable zero-dependency approach available on Streamlit Cloud.

import os, pathlib, html

PERSIST_KEYS  = ["watchlist", "kline_period", "check_interval"]
SAVE_PATH         = pathlib.Path("/tmp/stock_alert_config.json")
TRIGGERED_PATH    = pathlib.Path("/tmp/stock_alert_triggered.json")

def save_to_storage():
    """Write config to /tmp as JSON."""
    payload = {k: st.session_state[k] for k in PERSIST_KEYS if k in st.session_state}
    try:
        SAVE_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

def load_from_storage() -> dict:
    """Read config from /tmp. Returns {} if file missing or corrupt."""
    try:
        if SAVE_PATH.exists():
            return json.loads(SAVE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def clear_storage():
    """Delete all saved files."""
    try:
        SAVE_PATH.unlink(missing_ok=True)
        TRIGGERED_PATH.unlink(missing_ok=True)
    except Exception:
        pass

def _persist_triggered():
    """Write last_triggered dict to /tmp so cooldowns survive restarts."""
    try:
        TRIGGERED_PATH.write_text(
            json.dumps(st.session_state.last_triggered), encoding="utf-8"
        )
    except Exception:
        pass

def _load_triggered() -> dict:
    """Load last_triggered from /tmp. Prune entries older than 10 min."""
    try:
        if TRIGGERED_PATH.exists():
            raw  = json.loads(TRIGGERED_PATH.read_text(encoding="utf-8"))
            cutoff = time.time() - 600   # discard entries older than 10 min
            return {k: v for k, v in raw.items() if v > cutoff}
    except Exception:
        pass
    return {}

# ─────────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────────
defaults = {
    "watchlist":       [],
    "monitoring":      False,
    "logs":            [],
    "last_triggered":  {},
    "market_data":     {},
    "kline_period":    "5m",
    "check_interval":  60,
    "last_check_time": 0.0,
    "_storage_loaded": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Load once per Python session (not per rerun) — no async, no flicker
if not st.session_state["_storage_loaded"]:
    _saved = load_from_storage()
    for k in PERSIST_KEYS:
        if k in _saved:
            st.session_state[k] = _saved[k]
    # Also restore cooldown timestamps so we don't re-alert right after restart
    st.session_state["last_triggered"] = _load_triggered()
    st.session_state["_storage_loaded"] = True

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
#  TRADING SESSION DETECTOR
# ─────────────────────────────────────────────
def _is_dst_us(dt_utc: datetime) -> bool:
    year = dt_utc.year
    mar = datetime(year, 3, 8, 7, 0, tzinfo=timezone.utc)
    mar += timedelta(days=(6 - mar.weekday()) % 7)
    nov = datetime(year, 11, 1, 6, 0, tzinfo=timezone.utc)
    nov += timedelta(days=(6 - nov.weekday()) % 7)
    return mar <= dt_utc < nov

def get_et_time() -> datetime:
    now_utc = datetime.now(timezone.utc)
    offset  = timedelta(hours=-4) if _is_dst_us(now_utc) else timedelta(hours=-5)
    return now_utc.astimezone(timezone(offset))

def get_trading_session() -> dict:
    """Returns session info: session name, label, colour, use_scraper flag."""
    et  = get_et_time()
    dow = et.weekday()          # 0=Mon … 6=Sun
    hm  = et.hour + et.minute / 60.0
    dst    = _is_dst_us(datetime.now(timezone.utc))
    tz_str = "EDT" if dst else "EST"

    if dow == 5 or (dow == 6 and hm < 20.0):
        return dict(session="CLOSED",  label="休市（週末）",          color="#9a9487",
                    use_scraper=False, et=et, tz=tz_str)
    if 4.0 <= hm < 9.5:
        return dict(session="PRE",     label="盤前 Pre-Market",       color="#7c5cbf",
                    use_scraper=True,  et=et, tz=tz_str)
    if 9.5 <= hm < 16.0:
        return dict(session="REGULAR", label="正式交易 Regular",       color="#3a7d5e",
                    use_scraper=False, et=et, tz=tz_str)
    if 16.0 <= hm < 20.0:
        return dict(session="POST",    label="盤後 After-Hours",       color="#c9821a",
                    use_scraper=True,  et=et, tz=tz_str)
    # hm >= 20 or hm < 4  (weekday or Sun night)
    return dict(session="NIGHT",   label="夜盤 Night Session",     color="#1a6fa8",
                use_scraper=True,  et=et, tz=tz_str)

# ─────────────────────────────────────────────
#  YAHOO FINANCE EXTENDED-HOURS SCRAPER
# ─────────────────────────────────────────────
_SCRAPER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

@st.cache_data(ttl=30)
def scrape_extended_price(ticker: str) -> dict:
    """
    Fetch extended-hours price via Yahoo Finance JSON API (primary)
    with HTML fallback. Returns dict:
      price          — best available price (pre > post > regular)
      regular_price  — last official close
      pre_price      — pre-market price
      post_price     — post/after-hours price
      source         — which endpoint succeeded
      error          — error message if all sources failed
    """
    result = {
        "price": None, "regular_price": None,
        "pre_price": None, "post_price": None,
        "source": None, "error": None,
    }

    def _safe_float(v):
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    # ── Primary: Yahoo Finance v8 JSON API ──────────────────────────────────
    for host in ("query1", "query2"):
        try:
            url  = f"https://{host}.finance.yahoo.com/v8/finance/quote?symbols={ticker}"
            resp = requests.get(url, headers=_SCRAPER_HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            ql = resp.json().get("quoteResponse", {}).get("result", [])
            if not ql:
                continue
            q = ql[0]
            result["regular_price"] = _safe_float(q.get("regularMarketPrice"))
            result["pre_price"]     = _safe_float(q.get("preMarketPrice"))
            result["post_price"]    = _safe_float(q.get("postMarketPrice"))
            result["source"]        = f"{host}.finance.yahoo.com (JSON API)"

            # Sanity-check each price against regularMarketPrice:
            # pre/post price should be within ±30% of regular close
            reg = result["regular_price"]
            if reg:
                for key in ("pre_price", "post_price"):
                    v = result[key]
                    if v is not None and not (reg * 0.70 <= v <= reg * 1.30):
                        result[key] = None   # discard implausible value

            result["price"] = (result["pre_price"] or
                               result["post_price"] or
                               result["regular_price"])
            if result["price"]:
                return result
        except Exception as e:
            result["error"] = str(e)[:80]
            continue

    # ── Fallback: Yahoo Finance v7 quote summary ─────────────────────────────
    try:
        url  = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}"
        resp = requests.get(url, headers=_SCRAPER_HEADERS, timeout=15)
        if resp.status_code == 200:
            ql = resp.json().get("quoteResponse", {}).get("result", [])
            if ql:
                q = ql[0]
                result["regular_price"] = _safe_float(q.get("regularMarketPrice"))
                result["pre_price"]     = _safe_float(q.get("preMarketPrice"))
                result["post_price"]    = _safe_float(q.get("postMarketPrice"))
                result["source"]        = "query1.finance.yahoo.com (v7 API)"
                reg = result["regular_price"]
                if reg:
                    for key in ("pre_price", "post_price"):
                        v = result[key]
                        if v is not None and not (reg * 0.70 <= v <= reg * 1.30):
                            result[key] = None
                result["price"] = (result["pre_price"] or
                                   result["post_price"] or
                                   result["regular_price"])
                if result["price"]:
                    return result
    except Exception as e:
        result["error"] = (result["error"] or "") + f" | v7: {str(e)[:60]}"

    # ── Last resort: HTML page — only trust explicit field-named tags ────────
    for url in [f"https://finance.yahoo.com/quote/{ticker}/",
                f"https://uk.finance.yahoo.com/quote/{ticker}/"]:
        try:
            resp = requests.get(url, headers=_SCRAPER_HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            PRICE_FIELDS = {"regularMarketPrice", "preMarketPrice", "postMarketPrice"}
            found = {}
            for tag in soup.find_all("fin-streamer", attrs={"data-field": True}):
                field = tag.get("data-field", "")
                if field not in PRICE_FIELDS:
                    continue
                raw = tag.get("data-value") or tag.get_text(strip=True)
                try:
                    val = float(str(raw).replace(",", ""))
                except (ValueError, TypeError):
                    continue
                if field not in found:
                    found[field] = val

            # Cross-validate: if we have regularMarketPrice, use it as anchor
            reg = found.get("regularMarketPrice")
            if reg and 0.5 <= reg <= 9_999:
                result["regular_price"] = reg
                for field, key in [("preMarketPrice","pre_price"),
                                    ("postMarketPrice","post_price")]:
                    v = found.get(field)
                    if v and (reg * 0.70 <= v <= reg * 1.30):
                        result[key] = v
                result["price"]  = (result["pre_price"] or
                                    result["post_price"] or
                                    result["regular_price"])
                result["source"] = f"HTML: {url}"
                if result["price"]:
                    return result
        except Exception as e:
            result["error"] = (result["error"] or "") + f" | HTML {str(e)[:50]}"

    return result

    return result

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def fetch_stock_data(ticker: str, kline: str, vol_days: int = 20,
                     live_price: float = None, price_source: str = "yfinance"):
    """
    Fetch OHLCV from yfinance.
    If live_price is provided (from extended-hours scraper), it overrides the
    last Close so that price conditions are evaluated against the real-time price.
    """
    period = KLINE_PERIOD_MAP.get(kline, "5d")
    try:
        hist = yf.Ticker(ticker).history(period=period, interval=kline)
        if hist.empty or len(hist) < 2:
            return None
        price   = live_price if live_price else float(hist["Close"].iloc[-1])
        volume  = float(hist["Volume"].iloc[-1])
        n       = min(vol_days, len(hist) - 1)
        avg_vol = float(hist["Volume"].iloc[-1 - n : -1].mean()) if n > 0 else 0
        vol_ratio = volume / avg_vol if avg_vol > 0 else 0
        return {
            "price":        price,
            "volume":       volume,
            "avg_vol":      avg_vol,
            "vol_ratio":    vol_ratio,
            "vol_days":     n,
            "price_source": price_source,
            "ts":           datetime.now().strftime("%H:%M:%S"),
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

def send_telegram(message: str) -> tuple:
    """Returns (success: bool, error_detail: str)."""
    token, chat_id = get_telegram_creds()
    if not token:
        return False, "Secrets 未設定 TELEGRAM_BOT_TOKEN"
    if not chat_id:
        return False, "Secrets 未設定 TELEGRAM_CHAT_ID"
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            timeout=15,
        )
        if r.status_code == 200:
            return True, ""
        else:
            try:
                detail = r.json().get("description", r.text[:120])
            except Exception:
                detail = r.text[:120]
            return False, f"HTTP {r.status_code}: {detail}"
    except requests.exceptions.ConnectionError as e:
        return False, f"連線失敗（網絡封鎖？）: {str(e)[:80]}"
    except requests.exceptions.Timeout:
        return False, "請求超時 (15s)"
    except Exception as e:
        return False, str(e)[:100]

# ─────────────────────────────────────────────
#  POLL CYCLE
# ─────────────────────────────────────────────
def run_poll_cycle():
    now = time.time()
    if now - st.session_state.last_check_time < st.session_state.check_interval:
        return
    st.session_state.last_check_time = now

    kline = st.session_state.kline_period

    # Detect trading session for scraper decision
    sess = get_trading_session()

    # Batch fetch: one call per unique ticker
    unique_tickers = list({item["ticker"] for item in st.session_state.watchlist if item.get("enabled", True)})
    for ticker in unique_tickers:
        days_needed = max(
            (item.get("vol_days", 20) for item in st.session_state.watchlist
             if item["ticker"] == ticker and item.get("enabled", True)),
            default=20,
        )

        # Extended-hours: try scraper first for live price
        live_price   = None
        price_source = "yfinance"
        if sess["use_scraper"]:
            scraped = scrape_extended_price(ticker)
            if scraped.get("price"):
                live_price   = scraped["price"]
                price_source = f"延伸時段爬取 ({scraped.get('source','yahoo')})"
                st.session_state.logs.insert(0, {
                    "ts":  datetime.now().strftime("%H:%M:%S"),
                    "msg": f"[爬取] {ticker} 延伸時段價格 ${live_price:.2f} ({sess['label']})",
                    "type": "info",
                })

        data = fetch_stock_data(ticker, kline, days_needed, live_price, price_source)
        if data is None:
            st.session_state.logs.insert(0, {
                "ts": datetime.now().strftime("%H:%M:%S"),
                "msg": f"[警告] {ticker} 數據獲取失敗",
                "type": "warn",
            })
        else:
            st.session_state.market_data[ticker] = data

    # Now check conditions per alert (each alert has its own cooldown via its id)
    for item in st.session_state.watchlist:
        if not item.get("enabled", True):
            continue
        ticker   = item["ticker"]
        alert_id = item.get("id", id(item))
        vol_days = item.get("vol_days", 20)
        data     = st.session_state.market_data.get(ticker)
        if data is None:
            continue

        # Recompute vol_ratio using this alert's specific N if different from fetched
        actual_n = data.get("vol_days", vol_days)
        triggered, desc = check_conditions(item, data)

        if triggered:
            # Use str(alert_id) as key — last_triggered is loaded from file as str keys
            aid_key = str(alert_id)
            last = st.session_state.last_triggered.get(aid_key, 0)
            if now - last > 300:
                st.session_state.last_triggered[aid_key] = now
                # Persist cooldown immediately so restarts don't re-trigger
                _persist_triggered()
                n_actual = data.get("vol_days", vol_days)
                safe_desc   = html.escape(desc)
                safe_ticker = html.escape(ticker)
                psrc        = html.escape(data.get("price_source", "yfinance"))
                sess_now    = get_trading_session()
                safe_sess   = html.escape(sess_now["label"])
                msg = (
                    f"🔔 <b>股票警報！</b>\n"
                    f"📌 股票：<b>{safe_ticker}</b>\n"
                    f"🕐 時段：{safe_sess}\n"
                    f"💰 價格：${data['price']:.2f}  ({psrc})\n"
                    f"📊 成交量：{data['volume']:,.0f}  (均量 {data['avg_vol']:,.0f}，{n_actual} 根)\n"
                    f"📈 量比：{data['vol_ratio']:.2f}x\n"
                    f"✅ 條件：{safe_desc}\n"
                    f"⏱ 時間：{data['ts']}"
                )
                ok, err = send_telegram(msg)
                log_msg = (
                    f"[觸發] {ticker} ${data['price']:.2f} — Telegram ✓"
                    if ok else
                    f"[觸發] {ticker} ${data['price']:.2f} — 失敗：{err}"
                )
                st.session_state.logs.insert(0, {
                    "ts": data["ts"],
                    "msg": log_msg,
                    "type": "trig" if ok else "err",
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
            ok, err = send_telegram("✅ <b>股票警報系統</b>\n測試訊息發送成功！")
            if ok:
                st.success("✓ 發送成功！")
            else:
                st.error(f"發送失敗：{err}")

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # ── Saved config status ──
    st.markdown('<div class="section-label">記憶設定</div>', unsafe_allow_html=True)
    saved_count = len(st.session_state.get("watchlist", []))
    if saved_count > 0:
        st.markdown(
            f'<span class="badge badge-on">● 已記憶 {saved_count} 個警報</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<span class="badge badge-wait">● 尚無記憶設定</span>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑 清除所有記憶"):
        clear_storage()
        st.session_state.watchlist      = []
        st.session_state.market_data    = {}
        st.session_state.last_triggered = {}
        st.session_state.monitoring     = False
        st.rerun()

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
    save_to_storage()
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
    save_to_storage()
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
            else:
                alert_id = int(time.time() * 1000)
                st.session_state.watchlist.append({
                    "id":        alert_id,
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
                save_to_storage()
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

# ── Trading session banner ──
_sess = get_trading_session()
_et_str = _sess["et"].strftime("%H:%M")
_sess_bg = {
    "PRE":     "#f0eafa", "REGULAR": "#eaf5f0",
    "POST":    "#fdf3e3", "NIGHT":   "#e8f4fd", "CLOSED":  "#f5f3ee",
}.get(_sess["session"], "#f5f3ee")
_sess_border = {
    "PRE":     "#b39ddb", "REGULAR": "#81c784",
    "POST":    "#ffb74d", "NIGHT":   "#4fc3f7", "CLOSED":  "#ddd9cf",
}.get(_sess["session"], "#ddd9cf")
_scraper_note = " ｜ 🕷 延伸時段爬取啟用" if _sess["use_scraper"] else ""
st.markdown(
    f'<div style="font-family:var(--mono);font-size:0.78rem;'
    f'background:{_sess_bg};border:1px solid {_sess_border};'
    f'border-radius:8px;padding:7px 14px;margin-bottom:10px;'
    f'color:{_sess["color"]};">'
    f'● {_sess["label"]} &nbsp;｜&nbsp; ET {_et_str} {_sess["tz"]}'
    f'{_scraper_note}</div>',
    unsafe_allow_html=True,
)

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

    # Count how many alerts exist per ticker for sub-labelling
    ticker_counts = {}
    ticker_seq    = {}   # item id -> "#N" label
    for item in st.session_state.watchlist:
        t = item["ticker"]
        ticker_counts[t] = ticker_counts.get(t, 0) + 1
    seq_tracker = {}
    for item in st.session_state.watchlist:
        t = item["ticker"]
        seq_tracker[t] = seq_tracker.get(t, 0) + 1
        ticker_seq[item.get("id", id(item))] = seq_tracker[t] if ticker_counts[t] > 1 else None

    for i, item in enumerate(st.session_state.watchlist):
        ticker   = item["ticker"]
        alert_id = item.get("id", i)
        data     = st.session_state.market_data.get(ticker)

        # Sub-label (#1, #2 …) only when same ticker appears more than once
        seq_label = ticker_seq.get(alert_id)
        display_ticker = f"{ticker} <span style='font-size:0.8rem;color:var(--muted)'>#{seq_label}</span>" if seq_label else ticker

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
            psrc       = data.get("price_source", "yfinance")
            src_tag    = f" ｜ 🕷 {psrc}" if "爬取" in psrc else ""
            vol_str    = (
                f"量比 {data['vol_ratio']:.2f}×  ｜  "
                f"均量（{n_actual}根）{data['avg_vol']:,.0f}  ｜  "
                f"更新 {data['ts']}{src_tag}"
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
                    &nbsp;{display_ticker}
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
            if st.button(lbl, key=f"tog_{alert_id}"):
                st.session_state.watchlist[i]["enabled"] = not item["enabled"]
                save_to_storage()
                st.rerun()
        with btn2:
            if st.button("刪除", key=f"del_{alert_id}"):
                st.session_state.watchlist.pop(i)
                if not any(w["ticker"] == ticker for w in st.session_state.watchlist):
                    st.session_state.market_data.pop(ticker, None)
                save_to_storage()
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
        cls = (
            "log-trig"  if e["type"] in ("trig", "err") else
            "log-warn"  if e["type"] == "warn" else
            "log-scrape" if e["type"] == "info" else
            "log-info"
        )
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
