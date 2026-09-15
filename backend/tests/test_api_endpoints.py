import sys
from pathlib import Path
import pytest
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api import app
from retry import fetch_with_retry
from yf_session import get_session
import shock_detector
import propagation_model
import features


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    assert res.get_json()['status'] == 'ok'


def test_health_deep_endpoint(client):
    res = client.get('/api/health/deep')
    assert res.status_code in (200, 503)
    data = res.get_json()
    assert 'yahoo_reachable' in data
    assert 'sample_tickers' in data


def test_categories_endpoint(client):
    res = client.get('/api/categories')
    assert res.status_code == 200
    data = res.get_json()
    assert 'categories' in data
    assert 'tickers' in data


def test_empty_dataframe_raises_clean_503(monkeypatch, client):
    # Mock fetch_core_closes and _load_cache to test empty dataframe handling
    import api
    monkeypatch.setattr(api, '_load_cache', lambda *args, **kwargs: None)
    monkeypatch.setattr(api, 'fetch_core_closes', lambda **kwargs: pd.DataFrame())

    res_shocks = client.get('/api/shocks')
    assert res_shocks.status_code == 503
    json_shocks = res_shocks.get_json()
    assert json_shocks['error'] == 'no_data'
    assert 'Yahoo Finance' in json_shocks['hint']

    res_prop = client.get('/api/propagation')
    assert res_prop.status_code == 503
    json_prop = res_prop.get_json()
    assert json_prop['error'] == 'no_data'


def test_empty_dataframe_in_shock_detector():
    with pytest.raises(ValueError, match="No price data available"):
        shock_detector.detect_shocks(pd.DataFrame())

    with pytest.raises(ValueError, match="No price data available"):
        shock_detector.detect_shocks(None)


def test_empty_dataframe_in_propagation():
    with pytest.raises(ValueError, match="No price data available"):
        propagation_model.analyze_shock_propagation(pd.DataFrame(), pd.DataFrame())


def test_empty_dataframe_in_features():
    with pytest.raises(ValueError, match="No price data available"):
        features.process_price_data(pd.DataFrame())


def test_retry_mechanism():
    attempts = 0

    def flaky_func():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("Temporary timeout")
        return pd.DataFrame({'Close': [100, 101]})

    result = fetch_with_retry(flaky_func, max_attempts=3, base_delay=0.01)
    assert not result.empty
    assert attempts == 3
