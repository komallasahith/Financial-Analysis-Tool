"""
Generate historical snapshot files in backend/data/snapshots/
Used as offline fallback when Yahoo Finance is blocked or unreachable.
"""
import os
import sys
import pandas as pd
import yfinance as yf

sys.path.insert(0, os.path.dirname(__file__))
from yf_session import get_session
from data_loader import DEFAULT_TICKERS, _normalize_dataframe

def generate_snapshots():
    out_dir = os.path.join(os.path.dirname(__file__), 'data', 'snapshots')
    os.makedirs(out_dir, exist_ok=True)
    session = get_session()

    symbols = list(DEFAULT_TICKERS.values())
    print(f"Downloading {len(symbols)} tickers for global snapshot...")
    try:
        raw_df = yf.download(symbols, period="2y", progress=False, auto_adjust=True, session=session)
        if not raw_df.empty:
            norm_df = _normalize_dataframe(raw_df, DEFAULT_TICKERS)
            norm_df = norm_df.ffill(limit=3).dropna(how='all')
            norm_df.to_parquet(os.path.join(out_dir, "core_closes_snapshot.parquet"), index=True)
            print("Saved core_closes_snapshot.parquet:", norm_df.shape)
    except Exception as e:
        print(f"Error downloading all tickers: {e}")

    for name, sym in DEFAULT_TICKERS.items():
        try:
            print(f"Downloading snapshot for {name} ({sym})...")
            df = yf.download(sym, period="2y", progress=False, auto_adjust=True, session=session)
            if not df.empty:
                safe_name = name.lower()
                safe_sym = sym.replace('^', '').replace('=', '_').replace('-', '_').lower()
                df.to_parquet(os.path.join(out_dir, f"{safe_name}.parquet"), index=True)
                df.to_parquet(os.path.join(out_dir, f"{safe_sym}.parquet"), index=True)
        except Exception as e:
            print(f"Error for {name}: {e}")

    print("Snapshots generation complete!")

if __name__ == '__main__':
    generate_snapshots()
