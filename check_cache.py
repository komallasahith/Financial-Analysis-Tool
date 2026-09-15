import os, json, hashlib, pandas as pd
CACHE_DIR = 'backend/cache'
CACHE_SCHEMA_VERSION = 1
def _cache_path(key):
    return os.path.join(CACHE_DIR, f'cache_{CACHE_SCHEMA_VERSION}_{hashlib.sha256(f"{CACHE_SCHEMA_VERSION}:{key}".encode()).hexdigest()}')

for t in ['^NSEI', '^GSPC', 'AAPL', 'BTC-USD', 'AMZN']:
    p = _cache_path(f'ohlcv_{t}_1y_none_none') + '.parquet'
    if os.path.exists(p):
        df = pd.read_parquet(p)
        print(t, df['Close'].iloc[-1].item() if 'Close' in df.columns else 'No Close')
    else:
        print(t, 'Not cached')
