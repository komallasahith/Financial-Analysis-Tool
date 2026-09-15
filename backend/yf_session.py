"""Shared yfinance session with browser-like headers to reduce blocks."""
import yfinance as yf

_session = None


def get_session():
    global _session
    if _session is not None:
        return _session
    try:
        # yfinance 0.2.54+ ships curl_cffi-backed sessions
        from curl_cffi import requests as curl_requests
        _session = curl_requests.Session(impersonate="chrome")
    except ImportError:
        import requests
        _session = requests.Session()
        _session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })
    return _session
