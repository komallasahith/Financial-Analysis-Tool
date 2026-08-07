import pandas as pd


def detect_shocks(df, threshold=0.06):
    """
    Detect shock events across assets (clean version)

    Returns:
        One row per (date, asset) where shock occurs
    """

    return_cols = [col for col in df.columns if '_returns' in col]

    shock_events = []

    for date, row in df.iterrows():

        for col in return_cols:
            value = row[col]

            if abs(value) > threshold:
                asset = col.replace('_returns', '')

                shock_events.append({
                    'Date': date,
                    'Asset': asset,
                    'Return': value,
                    'Shock_Type': 'Positive' if value > 0 else 'Negative'
                })

    shock_df = pd.DataFrame(shock_events)

    # Sort
    shock_df = shock_df.sort_values(by='Date')

    return shock_df


def detect_major_shock_days(df, threshold=0.06):
    """
    Detect only major shock DAYS (one per date)
    """

    return_cols = [col for col in df.columns if '_returns' in col]

    major_shocks = []

    for date, row in df.iterrows():

        max_move = max(abs(row[col]) for col in return_cols)

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

    # 🔥 Per-asset shocks
    shocks = detect_shocks(processed_df, threshold=0.06)

    print("\n🔥 Asset-level shocks:", len(shocks))
    print(shocks.head())

    # 🔥 Per-day shocks (clean)
    major = detect_major_shock_days(processed_df, threshold=0.06)

    print("\n🔥 Major shock days:", len(major))
    print(major.head())