# Setup Guide

This project has two parts: a Flask API in `backend/` and a React app in `frontend/`.

## 1. Prerequisites

- Python 3.10+ recommended
- Node.js 18+ recommended
- `pip` and `npm`

## 2. Backend Setup

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the API:

```powershell
python api.py
```

The backend starts on `http://localhost:5000` by default.

## 3. Frontend Setup

From the repository root:

```powershell
cd frontend
npm install
npm start
```

The frontend starts on `http://localhost:3000`.

## 4. Production Build

Backend validation:

```powershell
python -m py_compile backend\api.py
```

Frontend production build:

```powershell
cd frontend
npm run build
```

## 5. Optional Environment Variables

Set these if you need to customize runtime behavior:

```powershell
$env:ALLOWED_ORIGINS="http://localhost:3000"
$env:FLASK_HOST="127.0.0.1"
$env:FLASK_DEBUG="false"
$env:REACT_APP_API_BASE="http://localhost:5000/api"
```

## 6. What to Commit

- Source files in `backend/` and `frontend/`
- `README.md` and `SETUP.md`
- `package-lock.json` files for reproducible installs
