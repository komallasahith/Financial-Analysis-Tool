import pandas as pd


def detect_shocks(df, threshold=0.06, mode='fixed_pct', z_threshold=3.0, rolling_window=60):
    """
    Detect shock events across assets (clean version)

    Returns:
        One row per (date, asset) where shock occurs
    """
    if df is None or df.empty:
        raise ValueError("No price data available — Yahoo Finance returned nothing")

    return_cols = [col for col in df.columns if col.endswith('_returns')]

    shock_events = []

    for date, row in df.iterrows():

        for col in return_cols:
            value = row[col]

            if pd.isna(value):
                continue
            if mode == 'z_score':
                rolling_std = df[col].rolling(rolling_window, min_periods=20).std()
                scale = rolling_std.loc[date]
                is_shock = pd.notna(scale) and scale > 0 and abs(value / scale) > z_threshold
                z_score = float(value / scale) if pd.notna(scale) and scale > 0 else None
            else:
                is_shock = abs(value) > threshold
                z_score = None

            if is_shock:
                asset = col.replace('_returns', '')

                event = {
                    'Date': date,
                    'Asset': asset,
                    'Return': value,
                    'Shock_Type': 'Positive' if value > 0 else 'Negative'
                }
                if z_score is not None:
                    event['Z_Score'] = z_score
                shock_events.append(event)

    shock_df = pd.DataFrame(shock_events)

    # Sort
    if not shock_df.empty:
        shock_df = shock_df.sort_values(by='Date')

    return shock_df


def detect_major_shock_days(df, threshold=0.06):
    """
    Detect only major shock DAYS (one per date)
    """

    return_cols = [col for col in df.columns if '_returns' in col]

    if not return_cols:
        return pd.DataFrame(columns=['Date', 'Max_Movement'])

    major_shocks = []

    for date, row in df.iterrows():

        values = [abs(row[col]) for col in return_cols if pd.notna(row[col])]
        if not values:
            continue
        max_move = max(values)

        if max_move > threshold:
            major_shocks.append({
                'Date': date,
                'Max_Movement': max_move
            })

    return pd.DataFrame(major_shocks)


# ---------------- TEST ----------------
if __name__ == "__main__":
    from data_loader import download_historical_data
    from features import process_price_data

    df = download_historical_data(period="1y")
    processed_df = process_price_data(df)

    # Per-asset shocks
    shocks = detect_shocks(processed_df, threshold=0.06)

    print("\n🔥 Asset-level shocks:", len(shocks))
    print(shocks.head())

    # Per-day shocks
    major = detect_major_shock_days(processed_df, threshold=0.06)

    print("\n🔥 Major shock days:", len(major))
    print(major.head())