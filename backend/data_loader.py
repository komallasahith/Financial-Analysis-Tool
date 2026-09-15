import os
import json
import logging
from datetime import datetime
import pandas as pd
import yfinance as yf
from yf_session import get_session
from retry import fetch_with_retry

logger = logging.getLogger(__name__)

CACHE_DIR = os.getenv('CACHE_DIR', os.path.join(os.path.dirname(__file__), 'cache'))
SNAPSHOTS_DIR = os.path.join(os.path.dirname(__file__), 'data', 'snapshots')
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

DEFAULT_TICKERS = {
    'NIFTY':       '^NSEI',
    'SP500':       '^GSPC',
    'Nasdaq':      '^IXIC',
    'Gold':        'GC=F',
    'Silver':      'SI=F',
    'Platinum':    'PL=F',
    'BrentOil':    'BZ=F',
    'WTICrude':    'CL=F',
    'NaturalGas':  'NG=F',
    'Bitcoin':     'BTC-USD',
    'Ethereum':    'ETH-USD',
    'Copper':      'HG=F',
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


def load_from_cache(key: str, max_age_seconds: int = 86400):
    candidates = [
        os.path.join(CACHE_DIR, f"{key}.parquet"),
        os.path.join(CACHE_DIR, f"{key}.json")
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        if max_age_seconds is not None:
            age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))).total_seconds()
            if age > max_age_seconds:
                continue
        try:
            if path.endswith('.parquet'):
                return pd.read_parquet(path)
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            continue
    return None


def save_to_cache(key: str, data):
    try:
        if isinstance(data, pd.DataFrame):
            data.to_parquet(os.path.join(CACHE_DIR, f"{key}.parquet"), index=True)
        else:
            with open(os.path.join(CACHE_DIR, f"{key}.json"), 'w', encoding='utf-8') as f:
                json.dump(data, f)
    except Exception as e:
        logger.warning(f"Error saving to cache for {key}: {e}")


def load_with_stale_fallback(key: str, fetch_fn, ttl_seconds: int = 86400):
    # Try fresh cache first
    cached = load_from_cache(key, max_age_seconds=ttl_seconds)
    if cached is not None and not (hasattr(cached, "empty") and cached.empty):
        return cached

    # Try fetch
    try:
        fresh = fetch_fn()
        if fresh is not None and not (hasattr(fresh, "empty") and fresh.empty):
            save_to_cache(key, fresh)
            return fresh
        raise ValueError("Fetch returned empty data")
    except Exception as e:
        logger.warning(f"Fetch failed for {key}: {e}")
        # Fall back to stale cache if it exists, ignoring TTL
        stale = load_from_cache(key, max_age_seconds=None)
        if stale is not None and not (hasattr(stale, "empty") and stale.empty):
            logger.info(f"Serving stale cache for {key}")
            return stale
        raise


def _load_snapshot(name_or_symbol: str = "core_closes"):
    safe_name = name_or_symbol.lower().replace('^', '').replace('=', '_').replace('-', '_')
    candidates = [
        os.path.join(SNAPSHOTS_DIR, f"{safe_name}.parquet"),
        os.path.join(SNAPSHOTS_DIR, f"{name_or_symbol}.parquet"),
        os.path.join(SNAPSHOTS_DIR, "core_closes_snapshot.parquet")
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                df = pd.read_parquet(path)
                if not df.empty:
                    return df
            except Exception as e:
                logger.warning(f"Error loading snapshot from {path}: {e}")
    return None


def _normalize_dataframe(df, tickers):
    if isinstance(df.columns, pd.MultiIndex):
        df = df['Close'].copy()
        df.columns = [ticker for ticker in df.columns.get_level_values(0)]
    if isinstance(df.columns, pd.Index):
        df.columns = list(df.columns)
    symbol_to_name = {symbol: name for name, symbol in tickers.items()}
    df = df.rename(columns=symbol_to_name)
    df.index.name = 'Date'
    return df


def download_historical_data(start_date=None, end_date=None, period="1y", tickers=None):
    if tickers is None:
        tickers = DEFAULT_TICKERS

    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    symbols = list(tickers.values())
    print(f"Downloading {len(symbols)} tickers from Yahoo Finance...")

    try:
        session = get_session()
        if start_date:
            df = fetch_with_retry(
                yf.download,
                symbols,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=True,
                session=session,
            )
        else:
            df = fetch_with_retry(
                yf.download,
                symbols,
                period=period,
                progress=False,
                auto_adjust=True,
                session=session,
            )

        if df is None or df.empty:
            print('Download returned empty data set')
            snapshot_df = _load_snapshot("core_closes_snapshot")
            if snapshot_df is not None and not snapshot_df.empty:
                print("Returning fallback snapshot data")
                return snapshot_df
            return pd.DataFrame()

        df = _normalize_dataframe(df, tickers)
        # Equities and crypto trade on different calendars. Preserve dates when
        # at least one asset has data, while limiting stale forward fills.
        df = df.ffill(limit=3).dropna(how='all')

        print(f"Data downloaded successfully: {df.shape[0]} rows x {df.shape[1]} assets")
        return df
    except Exception as exc:
        print(f"Error downloading historical data: {exc}")
        snapshot_df = _load_snapshot("core_closes_snapshot")
        if snapshot_df is not None and not snapshot_df.empty:
            print("Returning fallback snapshot data after error")
            return snapshot_df
        return pd.DataFrame()


if __name__ == "__main__":
    df = download_historical_data(period="1y")

    print("\nFinal Data Info:")
    print(df.info())
    print(df.shape)
    print(df.head())