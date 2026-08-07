import pandas as pd
import numpy as np


# -------- RETURNS --------
def calculate_daily_returns(df):
    returns = df.pct_change()
    returns.columns = [col + '_returns' for col in df.columns]
    return returns


# -------- VOLATILITY --------
def calculate_rolling_volatility(df, window=30):
    returns = df.pct_change()
    volatility = returns.rolling(window=window).std() * np.sqrt(252)
    volatility.columns = [col + '_volatility' for col in df.columns]
    return volatility


# -------- NORMALIZATION --------
def normalize_prices(df):
    normalized = (df / df.iloc[0]) * 100
    normalized.columns = [col + '_normalized' for col in df.columns]
    return normalized


# -------- MAIN PIPELINE --------
def process_price_data(df):

    if df.empty:
        raise ValueError("Input dataframe is empty")

    result = df.copy()

    returns = calculate_daily_returns(df)
    volatility = calculate_rolling_volatility(df)
    normalized = normalize_prices(df)

    result = pd.concat([result, returns, volatility, normalized], axis=1)

    # IMPORTANT: remove NaN rows
    result = result.dropna()

    return result


# -------- TEST --------
if __name__ == "__main__":
    from data_loader import download_historical_data

    df = download_historical_data(period="1y")

    processed_df = process_price_data(df)

    print("\nFeature Engineering Done")
    print("Shape:", processed_df.shape)

    print("\nColumns:")
    print(processed_df.columns.tolist())

    print("\nPreview:")
    print(processed_df.head())

    print("\nInfo:")
    print(processed_df.info())

    print("\nSample Check:")
    print(processed_df[['NIFTY_returns', 'NIFTY_volatility', 'NIFTY_normalized']].head())