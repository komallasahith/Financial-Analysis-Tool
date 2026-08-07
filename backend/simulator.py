import pandas as pd


def build_relationship_map(summary_df):
    relation_map = {}

    for _, row in summary_df.iterrows():
        source = row['Source_Asset']
        target = row['Target_Asset']
        impact = row['Avg_Impact']

        if source not in relation_map:
            relation_map[source] = {}

        relation_map[source][target] = impact

    return relation_map


def simulate_shock(relation_map, asset, shock_value):
    if asset not in relation_map:
        return {"error": "Asset not found"}

    results = {}

    baseline = 0.06  # baseline shock used in training

    for target, impact in relation_map[asset].items():
        scale_factor = shock_value / baseline
        predicted = impact * scale_factor
        results[target] = predicted

    return results


# ---------------- RUN FULL PIPELINE ----------------
if __name__ == "__main__":
    from data_loader import download_historical_data
    from features import process_price_data
    from shock_detector import detect_shocks
    from propagation_model import analyze_shock_propagation, summarize_propagation

    # Step 1: Load data
    df = download_historical_data(period="1y")

    # Step 2: Feature engineering
    processed_df = process_price_data(df)

    # Step 3: Shock detection
    shocks = detect_shocks(processed_df, threshold=0.06)

    # Step 4: Propagation analysis
    propagation = analyze_shock_propagation(processed_df, shocks)
    summary = summarize_propagation(propagation)

    # Step 5: Build relationship map
    relation_map = build_relationship_map(summary)

    # ---------------- SIMULATION ----------------
    print("\n===== FINANCIAL SHOCK SIMULATION =====")

    test_cases = [
        ("BrentOil", 0.10),
        ("Gold", 0.08),
        ("Silver", -0.07)
    ]

    for asset, value in test_cases:
        result = simulate_shock(relation_map, asset, value)

        print(f"\nInput Shock: {asset} {value*100:.1f}%")

        for k, v in result.items():
            print(f"{k}: {v*100:.2f}%")