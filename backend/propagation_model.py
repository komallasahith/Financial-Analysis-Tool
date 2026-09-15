import pandas as pd


def analyze_shock_propagation(df, shocks, window=3):
    """
    Analyze how shocks propagate to other assets.

    Parameters:
    ----------
    df : processed dataframe
    shocks : detected shocks
    window : number of days after shock

    Returns:
    -------
    propagation DataFrame
    """
    if df is None or df.empty:
        raise ValueError("No price data available — Yahoo Finance returned nothing")

    assets = ['NIFTY', 'Gold', 'Silver', 'BrentOil']

    results = []

    for _, shock in shocks.iterrows():

        shock_date = shock['Date']
        source_asset = shock['Asset']

        # Get future window (skip same day)
        future = df.loc[shock_date:].iloc[1:window+1]

        if len(future) < window:
            continue

        for target in assets:

            if target == source_asset:
                continue

            col = f"{target}_returns"
            if col not in future.columns or future[col].isna().all():
                continue

            # Average movement after shock
            impact = future[col].mean()

            results.append({
                'Shock_Date': shock_date,
                'Source_Asset': source_asset,
                'Target_Asset': target,
                'Avg_Impact': impact
            })

    return pd.DataFrame(results)


def summarize_propagation(propagation_df):
    """
    Average relationship between assets
    """

    required = ['Source_Asset', 'Target_Asset', 'Avg_Impact']
    if propagation_df.empty:
        return pd.DataFrame(columns=required)

    summary = propagation_df.groupby(
        ['Source_Asset', 'Target_Asset']
    )['Avg_Impact'].mean().reset_index()

    return summary


# ---------------- TEST ----------------
if __name__ == "__main__":
    from data_loader import download_historical_data
    from features import process_price_data
    from shock_detector import detect_shocks

    # Step 1
    df = download_historical_data(period="1y")

    # Step 2
    processed_df = process_price_data(df)

    # Step 3 (CLEAN SHOCKS)
    shocks = detect_shocks(processed_df, threshold=0.06)

    print("\nShocks used:", len(shocks))

    # Step 4: core logic
    propagation = analyze_shock_propagation(processed_df, shocks)

    print("\nPropagation sample:")
    print(propagation.head())

    # Step 5: summary
    summary = summarize_propagation(propagation)

    print("\nCross-Asset Relationships:")
    print(summary)
    