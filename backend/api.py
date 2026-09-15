"""
MarketPulse — Flask REST API
Wraps existing backend modules and serves all data to the React frontend.
Does NOT modify any existing backend files.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
import json
import hashlib
import logging
from datetime import datetime
import sys

# ── Add backend dir to path so imports work ──────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from data_loader import download_historical_data
from features import process_price_data
from shock_detector import detect_shocks
from propagation_model import analyze_shock_propagation, summarize_propagation
from simulator import build_relationship_map, simulate_shock

app = Flask(__name__)
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger('marketpulse.api')


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    logger.exception('Unhandled API error: %s', error)
    return jsonify({'error': 'An internal server error occurred.'}), 500

_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001')
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
    'Large Cap Stocks':  ['Apple', 'Microsoft', 'Amazon', 'Tesla', 'Nvidia', 'Meta', 'Alphabet', 'Broadcom', 'AMD', 'Netflix', 'JPMorgan', 'Berkshire', 'Reliance', 'HDFCBank'],
}

CATEGORY_ICONS = {
    'Indices':           'IDX',
    'Precious Metals':   'PM',
    'Energy':            'ENG',
    'Crypto':            'CR',
    'Industrial Metals': 'MTL',
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


def _load_cache(key: str):
    base = _cache_path(key)
    candidates = [(f"{base}.parquet", 'parquet'), (f"{base}.json", 'json')]
    for path, kind in candidates:
        if not os.path.exists(path):
            continue
        age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))).total_seconds()
        if age > CACHE_TTL_SECONDS:
            return None
        try:
            if kind == 'parquet':
                return pd.read_parquet(path)
            with open(path, 'r', encoding='utf-8') as cache_file:
                return json.load(cache_file)
        except (OSError, ValueError, ImportError, TypeError):
            return None
    return None


def _save_cache(key: str, data):
    base = _cache_path(key)
    if isinstance(data, pd.DataFrame):
        data.to_parquet(f"{base}.parquet", index=True)
        return
    with open(f"{base}.json", 'w', encoding='utf-8') as cache_file:
        json.dump(data, cache_file)


# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHING
# ─────────────────────────────────────────────────────────────────────────────
def fetch_ticker_df(ticker_symbol: str, period: str = '1y', mode: str = 'historical', start: str = None, end: str = None) -> pd.DataFrame:
    """Fetch OHLCV for one ticker. mode='historical' serves from cache if fresh."""
    import yfinance as yf

    cache_key = f"ohlcv_{ticker_symbol}_{period}_{start or 'none'}_{end or 'none'}"
    if mode == 'historical':
        cached = _load_cache(cache_key)
        if cached is not None:
            return cached

    if start or end:
        df = yf.download(ticker_symbol, start=start, end=end, progress=False, auto_adjust=True)
    else:
        df = yf.download(ticker_symbol, period=period, progress=False, auto_adjust=True)

    if mode == 'historical' and not df.empty:
        _save_cache(cache_key, df)
    return df


def fetch_core_closes(period: str = '1y', mode: str = 'historical', start: str = None, end: str = None) -> pd.DataFrame:
    """Fetch close prices for the core assets with optional range support."""
    cache_key = f"core_closes_{period}_{start or 'none'}_{end or 'none'}"
    if mode == 'historical':
        cached = _load_cache(cache_key)
        if cached is not None:
            return cached
    df = download_historical_data(start_date=start, end_date=end, period=period)
    if mode == 'historical' and not df.empty:
        _save_cache(cache_key, df)
    return df


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df


def fetch_live_quote(ticker_symbol: str) -> dict:
    import yfinance as yf
    try:
        df = yf.download(ticker_symbol, period='2d', interval='1m', progress=False, auto_adjust=True)
        if df.empty:
            df = yf.download(ticker_symbol, period='5d', interval='1d', progress=False, auto_adjust=True)
        df = flatten_columns(df)
        if df.empty or 'Close' not in df.columns:
            return {}
        close = df['Close'].dropna()
        if len(close) == 0:
            return {}
        current = float(close.iloc[-1])
        previous = float(close.iloc[-2]) if len(close) >= 2 else current
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
        print(f"[verify] {ticker_symbol}: {e}")
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSIS HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def probability_positive(returns_series: pd.Series, window: int = 60) -> float:
    recent = returns_series.dropna().tail(window)
    if len(recent) == 0:
        return 50.0
    return round(float((recent > 0).sum() / len(recent) * 100), 1)


def investment_suggestion(vol: float, trend_30d: float, prob: float) -> dict:
    """Produce a beginner-friendly investment suggestion dict."""
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
        action = 'Consider gradual entry — momentum is positive.'
        trend_icon = ''
    elif trend_30d > 0.01:
        trend_lbl = 'Mild Uptrend'
        action = 'Watch for dips as entry points.'
        trend_icon = ''
    elif trend_30d > -0.01:
        trend_lbl = 'Sideways / Consolidating'
        action = 'Wait for a breakout before committing.'
        trend_icon = ''
    elif trend_30d > -0.04:
        trend_lbl = 'Mild Downtrend'
        action = 'Avoid new purchases; wait for stabilization.'
        trend_icon = ''
    else:
        trend_lbl = 'Strong Downtrend'
        action = 'High caution — consider exiting or staying out.'
        trend_icon = ''

    # Composite score (0-100, higher = better opportunity)
    score = min(100, max(0, round(
        (prob * 0.45) +
        (min(1, max(0, (trend_30d + 0.1) / 0.2)) * 100 * 0.35) +
        (max(0, (0.4 - vol) / 0.4) * 100 * 0.20),
        1
    )))

    if risk == 'Low':
        beginner_note = 'Good for beginners as a small diversified allocation.'
    elif risk == 'Medium':
        beginner_note = 'Suitable for investors with moderate risk tolerance.'
    else:
        beginner_note = 'High risk — only for experienced investors with stop-losses.'

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
def get_categories():
    """Return all categories, tickers, and icons."""
    return jsonify({
        'categories': CATEGORIES,
        'tickers': TICKERS,
        'category_icons': CATEGORY_ICONS,
        'asset_icons': ASSET_ICONS,
    })


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat() + 'Z'})


@app.route('/api/ready', methods=['GET'])
def ready():
    writable = os.access(CACHE_DIR, os.W_OK)
    status = 200 if writable else 503
    return jsonify({'status': 'ready' if writable else 'not_ready', 'cache_writable': writable}), status


@app.route('/api/data-quality', methods=['GET'])
def data_quality():
    period = request.args.get('period', '1y')
    start = request.args.get('start')
    end = request.args.get('end')
    mode = request.args.get('mode', 'historical')
    df = fetch_core_closes(period=period, mode=mode, start=start, end=end)
    if df.empty:
        return jsonify({'error': 'No core-asset data'}), 500
    return jsonify({
        'effective_start': str(df.index.min())[:10],
        'effective_end': str(df.index.max())[:10],
        'row_count': int(len(df)),
        'assets': {
            asset: {'missing_pct': round(float(df[asset].isna().mean() * 100), 2)}
            for asset in df.columns
        },
    })


@app.route('/api/algorithms', methods=['GET'])
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
def verify_quote():
    asset = request.args.get('asset', 'Gold')
    ticker = TICKERS.get(asset)
    if not ticker:
        return jsonify({'error': f'Unknown asset: {asset}'}), 400

    quote = fetch_live_quote(ticker)
    if not quote:
        return jsonify({'error': 'Unable to verify live quote.'}), 500

    return jsonify({'asset': asset, 'ticker': ticker, **quote})


@app.route('/api/summary', methods=['GET'])
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

            current  = float(close.iloc[-1])
            prev     = float(close.iloc[-2])
            chg_pct  = (current - prev) / prev * 100
            week_ago = float(close.iloc[-6]) if len(close) >= 6 else prev
            wk_chg   = (current - week_ago) / week_ago * 100

            returns = close.pct_change().dropna()
            vol = float(returns.rolling(30).std().iloc[-1] * np.sqrt(252) * 100) if len(returns) >= 30 else 0

            # 7-day sparkline
            sparkline = [round(float(p), 4) for p in close.tail(7).values]

            category = next((c for c, assets in CATEGORIES.items() if name in assets), 'Other')

            results.append({
                'name': name,
                'ticker': ticker,
                'currency': 'INR' if ticker.endswith('.NS') else 'USD',
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
            print(f"  [summary] {name} error: {e}")

    return jsonify({'assets': results, 'mode': mode, 'categories': CATEGORIES, 'category_icons': CATEGORY_ICONS})


@app.route('/api/price-history', methods=['GET'])
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
    if df.empty or 'Close' not in df.columns:
        return jsonify({'error': 'No data available'}), 500

    close = df['Close'].dropna()
    returns = close.pct_change()
    normalized = (close / close.iloc[0]) * 100

    return jsonify({
        'asset': asset,
        'ticker': ticker,
        'currency': 'INR' if ticker.endswith('.NS') else 'USD',
        'mode': mode,
        'period': period,
        'dates':      [str(d)[:10]                       for d in close.index],
        'prices':     [round(float(p), 4)                for p in close.values],
        'normalized': [round(float(n), 2)                for n in normalized.values],
        'returns':    [round(float(r) * 100, 4) if not np.isnan(r) else 0 for r in returns.values],
        'current_price':     round(float(close.iloc[-1]), 4),
        'start_price':       round(float(close.iloc[0]), 4),
        'total_return_pct':  round((float(close.iloc[-1]) - float(close.iloc[0])) / float(close.iloc[0]) * 100, 2),
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M IST'),
    })


@app.route('/api/ohlc', methods=['GET'])
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
    needed = [c for c in ['Open', 'High', 'Low', 'Close'] if c in df.columns]
    if len(needed) < 4:
        return jsonify({'error': 'OHLC data not available'}), 500

    df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

    candles = [
        {
            'x': str(date)[:10],
            'y': [round(float(row['Open']), 4), round(float(row['High']), 4),
                  round(float(row['Low']), 4),  round(float(row['Close']), 4)]
        }
        for date, row in df.iterrows()
    ]

    return jsonify({'asset': asset, 'ticker': ticker, 'mode': mode, 'candles': candles})


@app.route('/api/monthly-returns', methods=['GET'])
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
    if df.empty or 'Close' not in df.columns:
        return jsonify({'error': 'No data'}), 500

    close = df['Close'].dropna()
    monthly = close.resample('ME').last()
    monthly_ret = monthly.pct_change().dropna() * 100

    return jsonify({
        'asset': asset,
        'mode': mode,
        'months':  [str(d)[:7]           for d in monthly_ret.index],
        'returns': [round(float(r), 2)   for r in monthly_ret.values],
    })


@app.route('/api/scatter', methods=['GET'])
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
    if df.empty or 'Close' not in df.columns:
        return jsonify({'error': 'No data'}), 500

    close = df['Close'].dropna()
    ret = close.pct_change() * 100
    vol = ret.rolling(20).std()
    combo = pd.DataFrame({'r': ret, 'v': vol}).dropna()

    return jsonify({
        'asset': asset,
        'mode': mode,
        'points': [{'x': round(float(r['v']), 4), 'y': round(float(r['r']), 4)} for _, r in combo.iterrows()],
    })


@app.route('/api/radar', methods=['GET'])
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
            vol          = float(returns.rolling(30).std().iloc[-1] * np.sqrt(252) * 100)
            ann_return   = float(returns.mean() * 252 * 100)
            total_return = float((close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100)
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
            print(f"  [radar] {name}: {e}")

    return jsonify({'mode': mode, 'assets': data})


@app.route('/api/probability', methods=['GET'])
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
    if df.empty or 'Close' not in df.columns:
        return jsonify({'error': 'No data'}), 500

    close = df['Close'].dropna()
    returns = close.pct_change().dropna()

    prob     = probability_positive(returns, window)
    vol      = float(returns.rolling(30).std().iloc[-1] * np.sqrt(252)) if len(returns) >= 30 else 0.2
    trend30  = float(returns.tail(30).sum()) if len(returns) >= 30 else 0

    suggestion = investment_suggestion(vol, trend30, prob)

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
            'values': [round(float(v), 1)   for v in roll_prob.values],
        },
    })


@app.route('/api/shocks', methods=['GET'])
def get_shocks():
    """Shock events across core 4 assets."""
    period    = request.args.get('period', '1y')
    start     = request.args.get('start')
    end       = request.args.get('end')
    try:
        threshold = float(request.args.get('threshold', 0.06))
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
    if df.empty:
        return jsonify({'error': 'No core-asset data'}), 500

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
def get_propagation():
    """Cross-asset propagation heatmap."""
    period    = request.args.get('period', '1y')
    start     = request.args.get('start')
    end       = request.args.get('end')
    try:
        threshold = float(request.args.get('threshold', 0.06))
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
    processed = process_price_data(df)
    shocks = detect_shocks(processed, threshold=threshold, mode=detection_mode)
    propagation = analyze_shock_propagation(processed, shocks)
    summary = summarize_propagation(propagation)

    assets = ['NIFTY', 'Gold', 'Silver', 'BrentOil']
    matrix = {src: {tgt: 0.0 for tgt in assets} for src in assets}
    for _, row in summary.iterrows():
        src, tgt = row['Source_Asset'], row['Target_Asset']
        if src in matrix and tgt in matrix[src]:
            matrix[src][tgt] = round(float(row['Avg_Impact']) * 100, 4)

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
def simulate():
    """Simulate a shock on one of the 4 core assets."""
    body      = request.get_json(silent=True) or {}
    asset     = body.get('asset', 'BrentOil')
    try:
        shock_pct = float(body.get('shock_pct', 10))
    except (TypeError, ValueError):
        return jsonify({'error': 'shock_pct must be a number'}), 400

    if shock_pct < -100 or shock_pct > 100:
        return jsonify({'error': 'shock_pct must be between -100 and 100'}), 400
    period    = body.get('period', '1y')
    start     = body.get('start')
    end       = body.get('end')
    mode      = body.get('mode', 'historical')
    try:
        threshold = float(body.get('threshold', 0.06))
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
    processed = process_price_data(df)
    shocks = detect_shocks(processed, threshold=threshold, mode=detection_mode)
    propagation = analyze_shock_propagation(processed, shocks)
    summary = summarize_propagation(propagation)
    rel_map = build_relationship_map(summary)

    shock_baseline = shocks['Return'].abs().median() if not shocks.empty else threshold
    raw = simulate_shock(rel_map, asset, shock_pct / 100, baseline=float(shock_baseline))
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
    # Allow overriding the port via FLASK_PORT or generic PORT env vars
    try:
        port = int(os.getenv('FLASK_PORT', os.getenv('PORT', '5000')))
    except (TypeError, ValueError):
        port = 5000

    host = os.getenv('FLASK_HOST', '127.0.0.1')
    debug_flag = os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')

    print(f"MarketPulse API -> http://{host}:{port}")
    print(f"{len(TICKERS)} assets across {len(CATEGORIES)} categories")

    app.run(debug=debug_flag, port=port, host=host)
