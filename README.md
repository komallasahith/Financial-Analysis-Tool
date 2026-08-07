# AI Financial Analysis Tool

MarketPulse is a full-stack financial analysis app with a Flask backend and a React frontend. It fetches market data, calculates returns and volatility, detects shocks, analyzes propagation, and runs scenario simulations.

## Stack

- Backend: Flask, pandas, numpy, yfinance, flask-cors
- Frontend: React, React Router, Chart.js, ApexCharts, axios

## Features

- Market overview by asset and category
- Historical price and OHLC views
- Volatility and return analysis
- Shock detection and propagation analysis
- Shock simulation and trade demo views
- Responsive UI with charting support

## Project Structure

- `backend/` Flask API and data-processing modules
- `frontend/` React app and UI components
- `README.md` project overview
- `SETUP.md` local development and deployment setup

## Quick Start

1. Install backend dependencies from `backend/requirements.txt`.
2. Install frontend dependencies from `frontend/package.json`.
3. Run the backend API on port `5000`.
4. Run the frontend app on port `3000`.

See [SETUP.md](SETUP.md) for the exact commands.

## Environment Variables

- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins for the API.
- `FLASK_HOST`: Host used by the Flask server. Defaults to `127.0.0.1`.
- `FLASK_DEBUG`: Enable Flask debug mode with `true`, `1`, or `yes`.
- `REACT_APP_API_BASE`: Frontend API base URL. Defaults to `http://localhost:5000/api`.

## Notes

- No API keys are stored in the repository.
- Cached market data lives in `backend/cache/` and is ignored by Git.
- The frontend default build uses Create React App tooling and is ready for static hosting.

## Deployment

- Backend: deploy the Flask app with the required Python dependencies installed.
- Frontend: run `npm run build` in `frontend/` and deploy the generated `build/` directory.
