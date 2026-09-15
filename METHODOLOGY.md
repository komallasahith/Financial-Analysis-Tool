# MarketPulse Methodology

## Scope

MarketPulse is an educational and research application. It is not investment advice, a portfolio manager, or a live trading system. Historical relationships can break, prices can be delayed, and the outputs have not been validated for live trading.

## Data

The application uses Yahoo Finance through `yfinance` as its primary price-data source. The current universe includes indices, commodities, crypto assets, US equities, and Indian equities listed with `.NS` symbols. The dashboard preserves the quote currency for Indian National Stock Exchange instruments (`INR`) and US instruments (`USD`).

NSE and Nasdaq public quote pages were checked as reference sources during documentation. They are not silently combined with Yahoo data and the application does not claim a quote is cross-source verified. Exchange pages can differ because of timestamp, adjustment, currency, and trading-session conventions.

Prices are adjusted by Yahoo Finance before feature calculations. Equity and crypto calendars are asynchronous, so prices are forward-filled for at most three rows and rows are removed only when every asset is missing. The data-quality endpoint exposes effective dates, row count, and missing percentages.

## Feature calculations

For close price $P_t$:

- Daily return: $r_t = P_t / P_{t-1} - 1$.
- Rolling volatility: sample standard deviation of the last 30 daily returns, annualized as $\sigma_{annual} = \operatorname{std}(r)\sqrt{252}$.
- Normalized price: $N_t = 100P_t/P_0$.
- Positive-day probability: positive returns divided by observed returns in the selected trailing window.
- Trend: sum of the latest 30 daily returns.

## Shock detection

`fixed_pct` flags an asset when $|r_t|$ exceeds the user threshold. `z_score` divides the daily return by its rolling 60-observation standard deviation, requiring at least 20 observations, and flags values whose absolute z-score exceeds 3 by default. Fixed percentage detection remains available for comparison and compatibility.

## Propagation

For each shock on date $T$, the same-day row is excluded. The model examines the next three available trading rows and calculates the mean target return. A shock near the end of the dataset is excluded unless the complete three-row window exists. Missing target columns or all-missing target windows are skipped. The current propagation map uses NIFTY, Gold, Silver, and BrentOil as its core targets.

## Scenarios

A requested shock is scaled against the median absolute return of detected shocks in the selected dataset. The observed historical relationship is multiplied by the requested shock divided by that baseline. This is a transparent sensitivity exercise, not a predictive model.

## Validation and limitations

The current project does not yet provide walk-forward backtesting, supervised ML propagation, regime detection, or independent quote verification. Those features must be added with out-of-sample metrics before being described as predictive. Yahoo Finance availability, exchange holidays, adjusted-price conventions, currency differences, and short samples all affect results.
