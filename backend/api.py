"""
MarketPulse — Flask REST API
Wraps existing backend modules and serves all data to the React frontend.
"""

from functools import wraps
import hashlib
import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import numpy as np
import pandas as pd
from werkzeug.exceptions import HTTPException
import yfinance as yf

# ── Add backend dir to path so imports work ──────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from yf_session import get_session
from retry import fetch_with_retry
from data_loader import (
    download_historical_data,
    load_from_cache,
    save_to_cache,
    load_with_stale_fallback,
    _load_snapshot,
)
from utils import safe_float
from features import process_price_data
from shock_detector import detect_shocks
from propagation_model import analyze_shock_propagation, summarize_propagation
from simulator import build_relationship_map, simulate_shock

app = Flask(__name__)
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger('marketpulse.api')
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=['120 per minute'],
    storage_uri=os.getenv('RATELIMIT_STORAGE_URI', 'memory://'),
)



def safe_endpoint(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as e:
            return jsonify({
                "error": "no_data",
                "message": str(e),
                "hint": "Yahoo Finance may be blocking the request. Try again in a moment.",
            }), 503
        except Exception as e:
            app.logger.error(f"Unhandled error in {fn.__name__}: {e}\n{traceback.format_exc()}")
            return jsonify({
                "error": "internal_error",
                "message": "Data temporarily unavailable. Please retry.",
                "endpoint": fn.__name__,
            }), 503
    return wrapper


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    if isinstance(error, HTTPException):
        return jsonify({'error': error.description}), error.code
    logger.exception('Unhandled API error: %s', error)
    return jsonify({'error': 'An internal server error occurred.'}), 500


_origins = os.getenv(
    'ALLOWED_ORIGINS',
    'http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001'
)
ALLOWED_ORIGINS = [o.strip() for o in _origins.split(',') if o.strip()]
CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})

# ─────────────────────────────────────────────────────────────────────────────
# Supported tickers and metadata
# ─────────────────────────────────────────────────────────────────────────────
TICKERS = {
    # Indices
    'NIFTY':       '^NSEI',
    'SP500':       '^GSPC',
    'Nasdaq':      '^IXIC',
    # Precious Metals
    'Gold':        'GC=F',
    'Silver':      'SI=F',
    'Platinum':    'PL=F',
    # Energy
    'BrentOil':    'BZ=F',
    'WTICrude':    'CL=F',
    'NaturalGas':  'NG=F',
    # Crypto
    'Bitcoin':     'BTC-USD',
    'Ethereum':    'ETH-USD',
    # Industrial
    'Copper':      'HG=F',
    # Large cap stocks
    'Apple':       'AAPL',
    'Microsoft':   'MSFT',
    'Amazon':      'AMZN',
    'Tesla':       'TSLA',
    'Nvidia':      'NVDA',
    'Meta':        'META',
    'Alphabet':    'GOOGL',
    'Broadcom':    'AVGO',
    'AMD':         'AMD',
    'Netflix':     'NFLX',
    'JPMorgan':    'JPM',
    'Berkshire':   'BRK-B',
    'Reliance':    'RELIANCE.NS',
    'HDFCBank':    'HDFCBANK.NS',
}

CATEGORIES = {
    'Indices':           ['NIFTY', 'SP500', 'Nasdaq'],
    'Precious Metals':   ['Gold', 'Silver', 'Platinum'],
    'Energy':            ['BrentOil', 'WTICrude', 'NaturalGas'],
    'Crypto':            ['Bitcoin', 'Ethereum'],
    'Industrial Metals': ['Copper'],
    'Indian Equities':   ['Reliance', 'HDFCBank'],
    'Large Cap Stocks':  [
        'Apple', 'Microsoft', 'Amazon', 'Tesla', 'Nvidia', 'Meta',
        'Alphabet', 'Broadcom', 'AMD', 'Netflix', 'JPMorgan',
        'Berkshire'
    ],
}

CATEGORY_ICONS = {
    'Indices':           'IDX',
    'Precious Metals':   'PM',
    'Energy':            'ENG',
    'Crypto':            'CR',
    'Industrial Metals': 'MTL',
    'Indian Equities':   'IND',
    'Large Cap Stocks':  'STK',
}

ASSET_ICONS = {
    'NIFTY': 'N', 'SP500': 'S', 'Nasdaq': 'Q',
    'Gold': 'Au', 'Silver': 'Ag', 'Platinum': 'Pt',
    'BrentOil': 'Br', 'WTICrude': 'WT', 'NaturalGas': 'NG',
    'Bitcoin': 'BTC', 'Ethereum': 'ETH',
    'Copper': 'Cu',
    'Apple': 'AAPL', 'Microsoft': 'MSFT', 'Amazon': 'AMZN',
    'Tesla': 'TSLA', 'Nvidia': 'NVDA', 'Meta': 'META',
    'Alphabet': 'GOOGL', 'Broadcom': 'AVGO', 'AMD': 'AMD', 'Netflix': 'NFLX',
    'JPMorgan': 'JPM', 'Berkshire': 'BRK', 'Reliance': 'REL', 'HDFCBank': 'HDF',
}

# Original 4 assets (used by existing backend modules)
CORE_ASSETS = ['NIFTY', 'Gold', 'Silver', 'BrentOil']

# ─────────────────────────────────────────────────────────────────────────────
# CACHE HELPERS
# ─────────────────────────────────────────────────────────────────────────────
CACHE_DIR = os.getenv('CACHE_DIR', os.path.join(os.path.dirname(__file__), 'cache'))
CACHE_SCHEMA_VERSION = 1
CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '86400'))
os.makedirs(CACHE_DIR, exist_ok=True)
try:
    os.chmod(CACHE_DIR, 0o700)
except OSError:
    pass


def _cache_path(key: str) -> str:
    digest = hashlib.sha256(f"{CACHE_SCHEMA_VERSION}:{key}".encode('utf-8')).hexdigest()
    return os.path.join(CACHE_DIR, f"cache_{CACHE_SCHEMA_VERSION}_{digest}")


def _load_cache(key: str, max_age_seconds: int = CACHE_TTL_SECONDS):
    base = _cache_path(key)
    candidates = [(f"{base}.parquet", 'parquet'), (f"{base}.json", 'json')]
    for path, kind in candidates:
        if not os.path.exists(path):
            continue
        if max_age_seconds is not None:
            age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))).total_seconds()
            if age > max_age_seconds:
                continue
        try:
            if kind == 'parquet':
                return pd.read_parquet(path)
            with open(path, 'r', encoding='utf-8') as cache_file:
                return json.load(cache_file)
        except (OSError, ValueError, ImportError, TypeError):
            continue
    return None


def _save_cache(key: str, data):
    base = _cache_path(key)
    if isinstance(data, pd.DataFrame):
        try:
            data.to_parquet(f"{base}.parquet", index=True)
        except ImportError:
            logger.warning('PyArrow is not installed; skipping DataFrame cache write')
        return
    with open(f"{base}.json", 'w', encoding='utf-8') as cache_file:
        json.dump(data, cache_file)


# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHING
# ─────────────────────────────────────────────────────────────────────────────
def fetch_ticker_df(
    ticker_symbol: str,
    period: str = '1y',
    mode: str = 'historical',
    start: str = None,
    end: str = None
) -> pd.DataFrame:
    """Fetch OHLCV for one ticker using master cache."""
    from data_loader import get_price_data
    master = get_price_data(start_date=start, end_date=end, mode=mode)
    
    if isinstance(master.columns, pd.MultiIndex):
        if ticker_symbol in master.columns.get_level_values(1):
            return master.xs(ticker_symbol, level=1, axis=1)
    
    return pd.DataFrame()


def fetch_core_closes(
    period: str = '1y',
    mode: str = 'historical',
    start: str = None,
    end: str = None
) -> pd.DataFrame:
    """Fetch close prices for the core assets using master cache."""
    from data_loader import get_price_data, DEFAULT_TICKERS, _normalize_dataframe
    master = get_price_data(start_date=start, end_date=end, mode=mode)
    return _normalize_dataframe(master, DEFAULT_TICKERS)


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df


def fetch_live_quote(ticker_symbol: str) -> dict:
    try:
        session = get_session()
        df = fetch_with_retry(
            yf.download,
            ticker_symbol,
            period='5d',
            interval='1d',
            progress=False,
            auto_adjust=True,
            session=session,
        )
        df = flatten_columns(df)
        if df is None or df.empty or 'Close' not in df.columns:
            return {}
        close = df['Close'].dropna()
        if len(close) == 0:
            return {}
        current = safe_float(close.iloc[-1])
        previous = safe_float(close.iloc[-2]) if len(close) >= 2 else current
        last_updated = close.index[-1]
        if hasattr(last_updated, 'strftime'):
            last_updated = last_updated.strftime('%Y-%m-%d %H:%M')
        else:
            last_updated = str(last_updated)[:19]

        return {
            'ticker': ticker_symbol,
            'current_price': round(current, 4),
            'previous_close': round(previous, 4),
            'last_updated': last_updated,
            'source': 'Yahoo Finance',
            'sources': [{'name': 'Yahoo Finance', 'price': round(current, 4), 'timestamp': last_updated}],
        }
    except Exception as e:
        logger.warning(f"[verify] {ticker_symbol}: {e}")
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSIS HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def probability_positive(returns_series: pd.Series, window: int = 60) -> float:
    recent = returns_series.dropna().tail(window)
    if len(recent) == 0:
        return 50.0
    return round(safe_float((recent > 0).sum() / len(recent) * 100), 1)


def market_context(vol: float, trend_30d: float, prob: float) -> dict:
    """Describe historical market conditions without making a trade recommendation."""
    # Risk
    if vol < 0.15:
        risk, risk_color = 'Low', 'green'
    elif vol < 0.35:
        risk, risk_color = 'Medium', 'yellow'
    else:
        risk, risk_color = 'High', 'red'

    # Trend
    if trend_30d > 0.04:
        trend_lbl = 'Strong Uptrend'
        action = 'Historical momentum is positive; review the underlying data and risk context.'
        trend_icon = ''
    elif trend_30d > 0.01:
        trend_lbl = 'Mild Uptrend'
        action = 'Historical momentum is mildly positive; monitor whether the pattern persists.'
        trend_icon = ''
    elif trend_30d > -0.01:
        trend_lbl = 'Sideways / Consolidating'
        action = 'Historical returns are broadly range-bound; no directional conclusion is implied.'
        trend_icon = ''
    elif trend_30d > -0.04:
        trend_lbl = 'Mild Downtrend'
        action = 'Historical momentum is mildly negative; monitor for changes in trend and volatility.'
        trend_icon = ''
    else:
        trend_lbl = 'Strong Downtrend'
        action = 'Historical momentum is strongly negative; downside risk has been elevated in this sample.'
        trend_icon = ''

    # Composite score (0-100, higher = better opportunity)
    score = min(100, max(0, round(
        (prob * 0.45) +
        (min(1, max(0, (trend_30d + 0.1) / 0.2)) * 100 * 0.35) +
        (max(0, (0.4 - vol) / 0.4) * 100 * 0.20),
        1
    )))

    if risk == 'Low':
        beginner_note = 'Observed volatility was relatively low in this sample; diversification and independent research still matter.'
    elif risk == 'Medium':
        beginner_note = 'Observed volatility was moderate in this sample; this is descriptive, not a suitability assessment.'
    else:
        beginner_note = 'Observed volatility was high in this sample; losses can be significant and future behavior is uncertain.'

    text = (
        f"This asset currently shows {risk.lower()} volatility. {trend_lbl}. "
        f"Over the past 60 trading days, {prob:.0f}% were positive. "
        f"{action} {beginner_note}"
    )

    return {
        'risk_level': risk,
        'risk_color': risk_color,
        'trend': trend_lbl,
        'trend_icon': trend_icon,
        'action': action,
        'score': score,
        'text': text,
        'probability_positive': prob,
    }


# ─────────────────────────────────────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/api/categories', methods=['GET'])
@safe_endpoint
def get_categories():
    """Return all categories, tickers, and icons."""
    return jsonify({
        'categories': CATEGORIES,
        'tickers': TICKERS,
        'category_icons': CATEGORY_ICONS,
        'asset_icons': ASSET_ICONS,
    })


@app.route('/api/health', methods=['GET'])
@safe_endpoint
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now(timezone.utc).isoformat()})


@app.route('/api/ready', methods=['GET'])
@safe_endpoint
def ready():
    writable = os.access(CACHE_DIR, os.W_OK)
    status = 200 if writable else 503
    return jsonify({'status': 'ready' if writable else 'not_ready', 'cache_writable': writable}), status


@app.route('/api/health/deep', methods=['GET'])
@safe_endpoint
def health_deep():
    result = {"yahoo_reachable": False, "sample_tickers": {}}
    try:
        session = get_session()
        df = fetch_with_retry(
            yf.download,
            "AAPL",
            period="5d",
            progress=False,
            auto_adjust=True,
            session=session,
            max_attempts=2,
            base_delay=1.0,
        )
        result["yahoo_reachable"] = not df.empty
        result["sample_tickers"]["AAPL"] = "ok" if not df.empty else "empty"
    except Exception as e:
        result["sample_tickers"]["AAPL"] = f"error: {e}"
    return jsonify(result)


@app.route('/api/data-quality', methods=['GET'])
@safe_endpoint
def data_quality():
    period = request.args.get('period', '1y')
    start = request.args.get('start')
    end = request.args.get('end')
    mode = request.args.get('mode', 'historical')
    df = fetch_core_closes(period=period, mode=mode, start=start, end=end)
    if df is None or df.empty:
        raise ValueError("No price data available — Yahoo Finance returned nothing")
    return jsonify({
        'effective_start': str(df.index.min())[:10],
        'effective_end': str(df.index.max())[:10],
        'row_count': int(len(df)),
        'assets': {
            asset: {'missing_pct': round(safe_float(df[asset].isna().mean() * 100), 2)}
            for asset in df.columns
        },
    })


@app.route('/api/algorithms', methods=['GET'])
@safe_endpoint
def get_algorithms():
    """Return a short summary of the models used in analysis."""
    return jsonify({
        'algorithms': [
            {
                'name': 'Shock detector',
                'description': 'Identifies strong daily moves using the selected threshold and flags them as market shocks.',
            },
            {
                'name': 'Propagation model',
                'description': 'Examines the following trading days to measure how shocks ripple into related assets.',
            },
            {
                'name': 'Portfolio signal',
                'description': 'Ranks assets using volatility, total return, and the probability of positive trading days.',
            },
            {
                'name': 'ML status',
                'description': 'No predictive ML model is currently served. Historical calculations remain explicitly educational until walk-forward validation is available.',
            },
        ],
        'data_source': 'Yahoo Finance',
        'notes': 'All pricing uses actual trading session data and adjusts for weekends and market holidays. NSE and Nasdaq are reference sources only; quotes are not automatically cross-verified.',
    })


@app.route('/api/verify', methods=['GET'])
@limiter.limit('10 per minute')
@safe_endpoint
def verify_quote():
    asset = request.args.get('asset', 'Gold')
    ticker = TICKERS.get(asset)
    if not ticker:
        return jsonify({'error': f'Unknown asset: {asset}'}), 400

    quote = fetch_live_quote(ticker)
    if not quote:
        raise ValueError(f"Unable to verify live quote for {asset} from Yahoo Finance")

    return jsonify({'asset': asset, 'ticker': ticker, **quote})


@app.route('/api/summary', methods=['GET'])
@safe_endpoint
def get_summary():
    """Summary card for all assets — price, change, volatility."""
    period = request.args.get('period', '1y')
    start  = request.args.get('start')
    end    = request.args.get('end')
    mode   = request.args.get('mode', 'historical')

    results = []
    for name, ticker in TICKERS.items():
        try:
            df = fetch_ticker_df(ticker, period=period, mode=mode, start=start, end=end)
            df = flatten_columns(df)
            if df.empty or 'Close' not in df.columns:
                continue
            close = df['Close'].dropna()
            if len(close) < 5:
                continue

            current  = safe_float(close.iloc[-1])
            prev     = safe_float(close.iloc[-2])
            chg_pct  = (current - prev) / prev * 100
            week_ago = safe_float(close.iloc[-6]) if len(close) >= 6 else prev
            wk_chg   = (current - week_ago) / week_ago * 100

            returns = close.pct_change().dropna()
            vol = safe_float(returns.rolling(30).std().iloc[-1] * np.sqrt(252) * 100) if len(returns) >= 30 else 0

            # 7-day sparkline
            sparkline = [round(safe_float(p), 4) for p in close.tail(7).values]

            category = next((c for c, assets in CATEGORIES.items() if name in assets), 'Other')

            results.append({
                'name': name,
                'ticker': ticker,
                'currency': 'INR' if name == 'NIFTY' or ticker.endswith('.NS') else 'USD',
                'icon': ASSET_ICONS.get(name, name[:3]),
                'category': category,
                'category_icon': CATEGORY_ICONS.get(category, category[:3].upper()),
                'price': round(current, 4),
                'change_pct': round(chg_pct, 2),
                'week_change_pct': round(wk_chg, 2),
                'volatility_pct': round(vol, 2),
                'sparkline': sparkline,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'mode': mode,
            })
        except Exception as e:
            logger.warning(f"[summary] {name} error: {e}")

    if not results:
        raise ValueError("No price data available — Yahoo Finance returned nothing")

    return jsonify({'assets': results, 'mode': mode, 'categories': CATEGORIES, 'category_icons': CATEGORY_ICONS})


@app.route('/api/asset-detail', methods=['GET'])
@safe_endpoint
def get_asset_detail():
    asset = request.args.get('asset')
    period = request.args.get('period', '1y')
    mode = request.args.get('mode', 'historical')
    start = request.args.get('start')
    end = request.args.get('end')
    
    ticker = TICKERS.get(asset)
    if not ticker:
        return jsonify({'error': 'invalid_asset', 'asset': asset}), 400
        
    df = fetch_ticker_df(ticker, period, mode, start, end)
    df = flatten_columns(df)
    if df.empty or 'Close' not in df.columns:
        raise ValueError("No data available")
        
    # We will invoke the logic for each component directly or just recreate it here
    close = df['Close'].dropna()
    returns = close.pct_change().dropna()
    
    # 1. Price History
    normalized = close / close.iloc[0] * 100
    price_history = {
        'dates':      [str(d.date()) for d in close.index],
        'prices':     [round(safe_float(p), 4)                for p in close.values],
        'normalized': [round(safe_float(n), 2)                for n in normalized.values],
        'returns':    [round(safe_float(r) * 100, 4) if not np.isnan(r) else 0 for r in returns.values],
        'current_price':     round(safe_float(close.iloc[-1]), 4),
        'start_price':       round(safe_float(close.iloc[0]), 4),
        'total_return_pct':  round((safe_float(close.iloc[-1]) - safe_float(close.iloc[0])) / safe_float(close.iloc[0]) * 100, 2),
    }
    
    # 2. OHLC
    df_ohlc = df[['Open', 'High', 'Low', 'Close']].dropna()
    ohlc = []
    for date, row in df_ohlc.iterrows():
        ohlc.append({
            'x': str(date.date()),
            'y': [
                round(safe_float(row['Open']), 4),
                round(safe_float(row['High']), 4),
                round(safe_float(row['Low']), 4),
                round(safe_float(row['Close']), 4),
            ]
        })
        
    # 3. Monthly Returns
    df_mon = df.copy()
    df_mon['Month'] = df_mon.index.to_period('M')
    monthly = df_mon.groupby('Month')['Close'].apply(lambda x: (x.iloc[-1] / x.iloc[0]) - 1).dropna() * 100
    monthly_returns = {
        'months':  [str(m) for m in monthly.index],
        'returns': [round(safe_float(r), 2)   for r in monthly.values],
    }
    
    # 4. Scatter
    rolling_vol = returns.rolling(20).std() * np.sqrt(252) * 100
    combo = pd.DataFrame({'r': returns * 100, 'v': rolling_vol}).dropna()
    scatter = {
        'points': [{'x': round(safe_float(r['v']), 4), 'y': round(safe_float(r['r']), 4)} for _, r in combo.iterrows()],
    }
    
    # 5. Radar
    if len(close) >= 30:
        vol = safe_float(returns.rolling(30).std().iloc[-1] * np.sqrt(252) * 100)
        ann_return = safe_float(returns.mean() * 252 * 100)
        total_return = safe_float((close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100)
        prob = probability_positive(returns)
        radar = {
            'assets': [{
                'asset': asset,
                'icon': ASSET_ICONS.get(asset, '📊'),
                'annualized_return': round(ann_return, 2),
                'volatility': round(vol, 2),
                'total_return': round(total_return, 2),
                'probability_positive': prob,
            }]
        }
    else:
        radar = {'assets': []}
        
    # 6. Probability
    prob_val = probability_positive(returns, window=60)
    
    return jsonify({
        'asset': asset,
        'period': period,
        'mode': mode,
        'price_history': price_history,
        'ohlc': ohlc,
        'monthly_returns': monthly_returns,
        'scatter': scatter,
        'radar': radar,
        'probability': prob_val
    })


@app.route('/api/price-history', methods=['GET'])
@safe_endpoint
def get_price_history():
    """Line / Area chart — Close prices over time."""
    asset  = request.args.get('asset', 'Gold')
    period = request.args.get('period', '1y')
    start  = request.args.get('start')
    end    = request.args.get('end')
    mode   = request.args.get('mode', 'historical')

    ticker = TICKERS.get(asset)
    if not ticker:
        return jsonify({'error': f'Unknown asset: {asset}'}), 400

    df = fetch_ticker_df(ticker, period=period, mode=mode, start=start, end=end)
    df = flatten_columns(df)
    if df is None or df.empty or 'Close' not in df.columns:
        raise ValueError("No price data available — Yahoo Finance returned nothing")

    close = df['Close'].dropna()
    if len(close) == 0:
        raise ValueError("No close price data available")

    returns = close.pct_change()
    normalized = (close / close.iloc[0]) * 100

    return jsonify({
        'asset': asset,
        'ticker': ticker,
        'currency': 'INR' if ticker.endswith('.NS') else 'USD',
        'mode': mode,
        'period': period,
        'dates':      [str(d)[:10]                       for d in close.index],
        'prices':     [round(safe_float(p), 4)                for p in close.values],
        'normalized': [round(safe_float(n), 2)                for n in normalized.values],
        'returns':    [round(safe_float(r) * 100, 4) if not np.isnan(r) else 0 for r in returns.values],
        'current_price':     round(safe_float(close.iloc[-1]), 4),
        'start_price':       round(safe_float(close.iloc[0]), 4),
        'total_return_pct':  round((safe_float(close.iloc[-1]) - safe_float(close.iloc[0])) / safe_float(close.iloc[0]) * 100, 2),
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M IST'),
    })


@app.route('/api/ohlc', methods=['GET'])
@safe_endpoint
def get_ohlc():
    """Candlestick chart — OHLC data."""
    asset  = request.args.get('asset', 'Gold')
    period = request.args.get('period', '1y')
    start  = request.args.get('start')
    end    = request.args.get('end')
    mode   = request.args.get('mode', 'historical')

    ticker = TICKERS.get(asset)
    if not ticker:
        return jsonify({'error': f'Unknown asset: {asset}'}), 400

    df = fetch_ticker_df(ticker, period=period, mode=mode, start=start, end=end)
    df = flatten_columns(df)
    if df is None or df.empty:
        raise ValueError("No price data available — Yahoo Finance returned nothing")

    needed = [c for c in ['Open', 'High', 'Low', 'Close'] if c in df.columns]
    if len(needed) < 4:
        raise ValueError("OHLC data not available")

    df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])
    if df.empty:
        raise ValueError("OHLC data rows are empty")

    candles = [
        {
            'x': str(date)[:10],
            'y': [
                round(safe_float(row['Open']), 4),
                round(safe_float(row['High']), 4),
                round(safe_float(row['Low']), 4),
                round(safe_float(row['Close']), 4),
            ],
        }
        for date, row in df.iterrows()
    ]

    return jsonify({'asset': asset, 'ticker': ticker, 'mode': mode, 'candles': candles})


@app.route('/api/monthly-returns', methods=['GET'])
@safe_endpoint
def get_monthly_returns():
    """Bar chart — monthly returns."""
    asset  = request.args.get('asset', 'Gold')
    period = request.args.get('period', '2y')
    start  = request.args.get('start')
    end    = request.args.get('end')
    mode   = request.args.get('mode', 'historical')

    ticker = TICKERS.get(asset)
    if not ticker:
        return jsonify({'error': f'Unknown asset: {asset}'}), 400

    df = fetch_ticker_df(ticker, period=period, mode=mode, start=start, end=end)
    df = flatten_columns(df)
    if df is None or df.empty or 'Close' not in df.columns:
        raise ValueError("No price data available — Yahoo Finance returned nothing")

    close = df['Close'].dropna()
    if len(close) == 0:
        raise ValueError("No close price data available")

    monthly = close.resample('ME').last()
    monthly_ret = monthly.pct_change().dropna() * 100

    return jsonify({
        'asset': asset,
        'mode': mode,
        'months':  [str(d)[:7]           for d in monthly_ret.index],
        'returns': [round(safe_float(r), 2)   for r in monthly_ret.values],
    })


@app.route('/api/scatter', methods=['GET'])
@safe_endpoint
def get_scatter():
    """Scatter — daily return vs 20-day rolling volatility."""
    asset  = request.args.get('asset', 'Gold')
    period = request.args.get('period', '1y')
    start  = request.args.get('start')
    end    = request.args.get('end')
    mode   = request.args.get('mode', 'historical')

    ticker = TICKERS.get(asset)
    if not ticker:
        return jsonify({'error': f'Unknown asset: {asset}'}), 400

    df = fetch_ticker_df(ticker, period=period, mode=mode, start=start, end=end)
    df = flatten_columns(df)
    if df is None or df.empty or 'Close' not in df.columns:
        raise ValueError("No price data available — Yahoo Finance returned nothing")

    close = df['Close'].dropna()
    if len(close) < 20:
        raise ValueError("Insufficient data points for scatter analysis")

    ret = close.pct_change() * 100
    vol = ret.rolling(20).std()
    combo = pd.DataFrame({'r': ret, 'v': vol}).dropna()

    return jsonify({
        'asset': asset,
        'mode': mode,
        'points': [{'x': round(safe_float(r['v']), 4), 'y': round(safe_float(r['r']), 4)} for _, r in combo.iterrows()],
    })


@app.route('/api/radar', methods=['GET'])
@safe_endpoint
def get_radar():
    """Radar — compare assets on 4 metrics."""
    period = request.args.get('period', '1y')
    start  = request.args.get('start')
    end    = request.args.get('end')
    mode   = request.args.get('mode', 'historical')
    assets_param = request.args.get('assets', '')
    selected = assets_param.split(',') if assets_param else list(TICKERS.keys())

    data = []
    for name in selected:
        ticker = TICKERS.get(name)
        if not ticker:
            continue
        try:
            df = fetch_ticker_df(ticker, period=period, mode=mode, start=start, end=end)
            df = flatten_columns(df)
            if df.empty or 'Close' not in df.columns:
                continue
            close = df['Close'].dropna()
            if len(close) < 30:
                continue
            returns = close.pct_change().dropna()
            vol          = safe_float(returns.rolling(30).std().iloc[-1] * np.sqrt(252) * 100)
            ann_return   = safe_float(returns.mean() * 252 * 100)
            total_return = safe_float((close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100)
            prob         = probability_positive(returns)

            data.append({
                'asset': name,
                'icon': ASSET_ICONS.get(name, '📊'),
                'annualized_return': round(ann_return, 2),
                'volatility': round(vol, 2),
                'total_return': round(total_return, 2),
                'probability_positive': prob,
            })
        except Exception as e:
            logger.warning(f"[radar] {name}: {e}")

    if not data:
        raise ValueError("No price data available — Yahoo Finance returned nothing")

    return jsonify({'mode': mode, 'assets': data})


@app.route('/api/probability', methods=['GET'])
@safe_endpoint
def get_probability():
    """Probability of positive return + beginner investment suggestion."""
    asset  = request.args.get('asset', 'Gold')
    period = request.args.get('period', '1y')
    start  = request.args.get('start')
    end    = request.args.get('end')
    mode   = request.args.get('mode', 'historical')
    try:
        window = int(request.args.get('window', 60))
    except (TypeError, ValueError):
        return jsonify({'error': 'window must be an integer'}), 400

    if window < 10 or window > 365:
        return jsonify({'error': 'window must be between 10 and 365'}), 400

    ticker = TICKERS.get(asset)
    if not ticker:
        return jsonify({'error': f'Unknown asset: {asset}'}), 400

    df = fetch_ticker_df(ticker, period=period, mode=mode, start=start, end=end)
    df = flatten_columns(df)
    if df is None or df.empty or 'Close' not in df.columns:
        raise ValueError("No price data available — Yahoo Finance returned nothing")

    close = df['Close'].dropna()
    if len(close) < 10:
        raise ValueError("Insufficient data points for probability analysis")

    returns = close.pct_change().dropna()

    prob     = probability_positive(returns, window)
    vol      = safe_float(returns.rolling(30).std().iloc[-1] * np.sqrt(252)) if len(returns) >= 30 else 0.2
    trend30  = safe_float(returns.tail(30).sum()) if len(returns) >= 30 else 0

    suggestion = market_context(vol, trend30, prob)

    recent = returns.tail(window)
    win_days  = int((recent > 0).sum())
    loss_days = int((recent < 0).sum())

    # Rolling probability (30-day window, weekly samples)
    roll_prob = returns.rolling(30).apply(lambda x: (x > 0).mean() * 100)
    roll_prob = roll_prob.dropna()

    return jsonify({
        'asset': asset,
        'mode': mode,
        'probability_positive_pct': prob,
        'win_days': win_days,
        'loss_days': loss_days,
        'window_days': window,
        'annualized_volatility_pct': round(vol * 100, 2),
        'trend_30d_pct': round(trend30 * 100, 2),
        'suggestion': suggestion,
        'rolling_probability': {
            'dates':  [str(d)[:10]          for d in roll_prob.index],
            'values': [round(safe_float(v), 1)   for v in roll_prob.values],
        },
    })


@app.route('/api/shocks', methods=['GET'])
@safe_endpoint
def get_shocks():
    """Shock events across core 4 assets."""
    period    = request.args.get('period', '1y')
    start     = request.args.get('start')
    end       = request.args.get('end')
    try:
        threshold = safe_float(request.args.get('threshold', 0.06))
    except (TypeError, ValueError):
        return jsonify({'error': 'threshold must be a number'}), 400

    if threshold <= 0 or threshold > 1:
        return jsonify({'error': 'threshold must be between 0 and 1'}), 400
    mode      = request.args.get('mode', 'historical')
    detection_mode = request.args.get('detection_mode', 'fixed_pct')
    if detection_mode not in ('fixed_pct', 'z_score'):
        return jsonify({'error': 'detection_mode must be fixed_pct or z_score'}), 400

    cache_key = f"shocks_{period}_{threshold}_{detection_mode}_{start or 'none'}_{end or 'none'}"
    if mode == 'historical':
        cached = _load_cache(cache_key)
        if cached:
            return jsonify(cached)

    df = fetch_core_closes(period=period, mode=mode, start=start, end=end)
    if df is None or df.empty:
        raise ValueError("No price data available — Yahoo Finance returned nothing")

    processed = process_price_data(df)
    shocks = detect_shocks(processed, threshold=threshold, mode=detection_mode)

    # Convert dates to strings for JSON
    if not shocks.empty:
        shocks['Date'] = shocks['Date'].astype(str)

    result = {
        'mode': mode,
        'threshold': threshold,
        'detection_mode': detection_mode,
        'total_shocks': len(shocks),
        'shocks': shocks.to_dict(orient='records') if not shocks.empty else [],
    }
    if mode == 'historical':
        _save_cache(cache_key, result)

    return jsonify(result)


@app.route('/api/propagation', methods=['GET'])
@safe_endpoint
def get_propagation():
    """Cross-asset propagation heatmap."""
    period    = request.args.get('period', '1y')
    start     = request.args.get('start')
    end       = request.args.get('end')
    try:
        threshold = safe_float(request.args.get('threshold', 0.06))
    except (TypeError, ValueError):
        return jsonify({'error': 'threshold must be a number'}), 400

    if threshold <= 0 or threshold > 1:
        return jsonify({'error': 'threshold must be between 0 and 1'}), 400
    mode      = request.args.get('mode', 'historical')
    detection_mode = request.args.get('detection_mode', 'fixed_pct')
    if detection_mode not in ('fixed_pct', 'z_score'):
        return jsonify({'error': 'detection_mode must be fixed_pct or z_score'}), 400

    cache_key = f"propagation_{period}_{threshold}_{detection_mode}_{start or 'none'}_{end or 'none'}"
    if mode == 'historical':
        cached = _load_cache(cache_key)
        if cached:
            return jsonify(cached)

    df = fetch_core_closes(period=period, mode=mode, start=start, end=end)
    if df is None or df.empty:
        raise ValueError("No price data available — Yahoo Finance returned nothing")

    processed = process_price_data(df)
    shocks = detect_shocks(processed, threshold=threshold, mode=detection_mode)
    propagation = analyze_shock_propagation(processed, shocks)
    summary = summarize_propagation(propagation)

    assets = ['NIFTY', 'Gold', 'Silver', 'BrentOil']
    matrix = {src: {tgt: 0.0 for tgt in assets} for src in assets}
    for _, row in summary.iterrows():
        src, tgt = row['Source_Asset'], row['Target_Asset']
        if src in matrix and tgt in matrix[src]:
            matrix[src][tgt] = round(safe_float(row['Avg_Impact']) * 100, 4)

    result = {
        'mode': mode,
        'summary': summary.to_dict(orient='records'),
        'heatmap_matrix': matrix,
        'assets': assets,
    }
    if mode == 'historical':
        _save_cache(cache_key, result)

    return jsonify(result)


@app.route('/api/simulate', methods=['POST'])
@limiter.limit('20 per minute')
@safe_endpoint
def simulate():
    """Simulate a shock on one of the 4 core assets."""
    body      = request.get_json(silent=True) or {}
    asset     = body.get('asset', 'BrentOil')
    try:
        shock_pct = safe_float(body.get('shock_pct', 10))
    except (TypeError, ValueError):
        return jsonify({'error': 'shock_pct must be a number'}), 400

    if shock_pct < -100 or shock_pct > 100:
        return jsonify({'error': 'shock_pct must be between -100 and 100'}), 400
    period    = body.get('period', '1y')
    start     = body.get('start')
    end       = body.get('end')
    mode      = body.get('mode', 'historical')
    try:
        threshold = safe_float(body.get('threshold', 0.06))
    except (TypeError, ValueError):
        return jsonify({'error': 'threshold must be a number'}), 400
    if threshold <= 0 or threshold > 1:
        return jsonify({'error': 'threshold must be between 0 and 1'}), 400
    detection_mode = body.get('detection_mode', 'fixed_pct')
    if detection_mode not in ('fixed_pct', 'z_score'):
        return jsonify({'error': 'detection_mode must be fixed_pct or z_score'}), 400

    if asset not in CORE_ASSETS:
        return jsonify({'error': f'Simulation only supports: {CORE_ASSETS}'}), 400

    df = fetch_core_closes(period=period, mode=mode, start=start, end=end)
    if df is None or df.empty:
        raise ValueError("No price data available — Yahoo Finance returned nothing")

    processed = process_price_data(df)
    shocks = detect_shocks(processed, threshold=threshold, mode=detection_mode)
    propagation = analyze_shock_propagation(processed, shocks)
    summary = summarize_propagation(propagation)
    rel_map = build_relationship_map(summary)

    shock_baseline = shocks['Return'].abs().median() if not shocks.empty else threshold
    raw = simulate_shock(rel_map, asset, shock_pct / 100, baseline=safe_float(shock_baseline))
    impacts = [
        {
            'target': k,
            'impact_pct': round(v * 100, 4),
            'direction': 'Positive' if v > 0 else 'Negative',
        }
        for k, v in raw.items() if k != 'error'
    ]

    return jsonify({
        'source_asset': asset,
        'shock_pct': shock_pct,
        'threshold': threshold,
        'detection_mode': detection_mode,
        'mode': mode,
        'impacts': impacts,
    })


if __name__ == '__main__':
    try:
        port = int(os.getenv('FLASK_PORT', os.getenv('PORT', '5000')))
    except (TypeError, ValueError):
        port = 5000

    host = os.getenv('FLASK_HOST', '127.0.0.1')
    debug_flag = os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')

    print(f"MarketPulse API -> http://{host}:{port}")
    print(f"{len(TICKERS)} assets across {len(CATEGORIES)} categories")

    app.run(debug=debug_flag, port=port, host=host)

# At the bottom of api.py, after all routes are registered:
import collections
endpoint_names = [rule.endpoint for rule in app.url_map.iter_rules()]
dupes = [name for name, count in collections.Counter(endpoint_names).items() if count > 1]
if dupes:
    raise RuntimeError(f"Duplicate Flask endpoints detected: {dupes}")
