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

    assets = ['NIFTY', 'Gold', 'Silver', 'BrentOil']

    results = []

    for _, shock in shocks.iterrows():

        shock_date = shock['Date']
        source_asset = shock['Asset']

        # Get future window (skip same day)
        future = df.loc[shock_date:].iloc[1:window+1]

        if future.empty:
            continue

        for target in assets:

            if target == source_asset:
                continue

            # Average movement after shock
            impact = future[f"{target}_returns"].mean()

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

    # Step 4 ⭐ CORE LOGIC
    propagation = analyze_shock_propagation(processed_df, shocks)

    print("\nPropagation sample:")
    print(propagation.head())

    # Step 5 ⭐ SUMMARY
    summary = summarize_propagation(propagation)

    print("\n🔥 Cross-Asset Relationships:")
    print(summary)
    