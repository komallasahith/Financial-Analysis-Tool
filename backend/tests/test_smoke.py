import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from features import process_price_data
from propagation_model import analyze_shock_propagation, summarize_propagation
from shock_detector import detect_major_shock_days, detect_shocks
from simulator import simulate_shock


def test_process_price_data_handles_asynchronous_assets():
    prices = pd.DataFrame({
        'A': [100, 101, 102],
        'B': [10, None, 10.2],
    })

    result = process_price_data(prices)

    assert len(result) == 3
    assert result['B'].isna().sum() == 0


def test_detect_major_shock_days_handles_no_return_columns():
    result = detect_major_shock_days(pd.DataFrame({'A': [1, 2]}))

    assert result.empty
    assert list(result.columns) == ['Date', 'Max_Movement']


def test_detect_shocks_supports_z_scores():
    returns = pd.DataFrame({'A_returns': [0.01] * 20 + [0.2]})

    result = detect_shocks(returns, mode='z_score', z_threshold=3, rolling_window=20)

    assert not result.empty
    assert result.iloc[-1]['Asset'] == 'A'
    assert result.iloc[-1]['Z_Score'] > 3


def test_propagation_skips_missing_target_columns():
    returns = pd.DataFrame(
        {
            'A_returns': [0.1, 0, 0, 0],
            'Gold_returns': [0, 0.01, 0.02, 0.03],
        },
        index=pd.date_range('2024-01-01', periods=4),
    )
    shocks = pd.DataFrame([{'Date': returns.index[0], 'Asset': 'A', 'Return': 0.1}])

    result = analyze_shock_propagation(returns, shocks, window=3)

    assert len(result) == 1
    assert result.iloc[0]['Target_Asset'] == 'Gold'


def test_summarize_propagation_empty_is_schema_stable():
    result = summarize_propagation(pd.DataFrame())

    assert result.empty
    assert list(result.columns) == ['Source_Asset', 'Target_Asset', 'Avg_Impact']


def test_simulation_uses_supplied_baseline():
    result = simulate_shock({'A': {'Gold': 0.02}}, 'A', 0.1, baseline=0.1)

    assert result == {'Gold': 0.02}
