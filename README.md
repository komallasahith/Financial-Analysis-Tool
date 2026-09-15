# MarketPulse

MarketPulse is an educational market-research desk for comparing indices, commodities, crypto assets, US equities, and Indian equities. It loads adjusted Yahoo Finance prices, calculates transparent historical features, detects unusual moves, measures short-horizon cross-asset propagation, and runs illustrative shock scenarios.

**This is not investment advice.** Results are historical and illustrative. They are not predictions, recommendations, or validated live-trading signals.

## Run locally

Backend:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python backend\api.py
```

Frontend:

```powershell
cd frontend
npm install
$env:REACT_APP_API_BASE="http://127.0.0.1:5000/api"
npm start
```

The API uses port `5000`. Create React App uses `3000`; if that port is occupied, use `3001` and keep `ALLOWED_ORIGINS` configured for that port.

## Main pages

- **Overview**: latest quotes, daily and weekly movement, annualized volatility, and exportable rows.
- **Asset detail**: price line, normalized performance area, monthly returns, OHLC candles, scatter, radar, and historical statistics.
- **Cross-asset**: shock frequency, propagation matrix, comparison radar, and method notes.
- **Scenarios**: scale observed propagation relationships to a chosen shock.
- **Trade lab**: educational historical position calculation for selected US stocks.
- **How it works**: project documentation, formulas, algorithms, sources, and limitations.

## Data universe

The current tracked assets include NIFTY, S&P 500, Nasdaq, gold, silver, platinum, Brent crude, WTI crude, natural gas, Bitcoin, Ethereum, copper, Apple, Microsoft, Amazon, Tesla, Nvidia, Meta, Alphabet, Broadcom, AMD, Netflix, JPMorgan, Berkshire Hathaway, Reliance Industries, and HDFC Bank.

Yahoo Finance is the primary programmatic source. The app preserves `USD` for US instruments and `INR` for `.NS` instruments. NSE and Nasdaq pages are useful public reference sources ([NSE Reliance quote](https://www.nseindia.com/get-quotes/equity?symbol=RELIANCE), [Nasdaq Apple quote](https://www.nasdaq.com/market-activity/stocks/aapl)), but the application does not combine them with Yahoo prices or claim automated cross-source verification. Timestamp, adjustment, currency, and session differences can make displayed values differ.

## Calculations

- **Daily return**: `close[t] / close[t-1] - 1`.
- **Rolling volatility**: 30-observation sample standard deviation of returns multiplied by `sqrt(252)`.
- **Normalized price**: `close / first_close * 100`.
- **Positive-day probability**: positive observed returns divided by returns in the selected trailing window.
- **Fixed shock**: `abs(return) > threshold`.
- **Z-score shock**: `return / rolling_std`, using a 60-observation window, at least 20 observations, and a default level of 3.
- **Propagation**: mean target return over the next three available trading rows, excluding the shock row and incomplete windows.
- **Scenario**: observed impact multiplied by `requested_shock / median_abs_detected_shock`.

Feature and data-quality details are documented in [METHODOLOGY.md](METHODOLOGY.md) and in the in-app How it works page at `http://localhost:3001/how-it-works`.

## API highlights

- `GET /api/health`
- `GET /api/ready`
- `GET /api/categories`
- `GET /api/summary`
- `GET /api/price-history?asset=Apple`
- `GET /api/data-quality`
- `GET /api/shocks?detection_mode=z_score`
- `GET /api/propagation`
- `POST /api/simulate`
- `GET /api/algorithms`

## Environment variables

- `ALLOWED_ORIGINS`: comma-separated browser origins.
- `FLASK_HOST`, `FLASK_PORT`, `FLASK_DEBUG`: Flask runtime settings.
- `CACHE_DIR`: cache directory, default `backend/cache`.
- `CACHE_TTL_SECONDS`: cache lifetime, default `86400`.
- `REACT_APP_API_BASE`: frontend API base URL.

## Engineering notes

The backend cache uses versioned hashed Parquet/JSON files rather than pickle. `pyarrow` is required for DataFrame caching. Market calendars are asynchronous; the loader forward-fills at most three rows and drops only rows where all assets are missing. The repository does not currently serve a predictive ML model or claim walk-forward ML validation, quote verification, or predictive performance.

## Validation

```powershell
python -m py_compile backend\api.py backend\features.py backend\shock_detector.py backend\propagation_model.py backend\simulator.py
cd frontend
npm run build
```
