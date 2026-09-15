import yfinance as yf
import pandas as pd
from datetime import datetime

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
        if start_date:
            df = yf.download(symbols, start=start_date, end=end_date, progress=False, auto_adjust=True)
        else:
            df = yf.download(symbols, period=period, progress=False, auto_adjust=True)

        if df.empty:
            print('Download returned empty data set')
            return pd.DataFrame()

        df = _normalize_dataframe(df, tickers)
        # Equities and crypto trade on different calendars. Preserve dates when
        # at least one asset has data, while limiting stale forward fills.
        df = df.ffill(limit=3).dropna(how='all')

        print(f"Data downloaded successfully: {df.shape[0]} rows x {df.shape[1]} assets")
        return df
    except Exception as exc:
        print(f"Error downloading historical data: {exc}")
        return pd.DataFrame()


if __name__ == "__main__":
    df = download_historical_data(period="1y")

    print("\nFinal Data Info:")
    print(df.info())
    print(df.shape)
    print(df.head())