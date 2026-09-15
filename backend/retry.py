import time
import logging

logger = logging.getLogger(__name__)


def fetch_with_retry(fn, *args, max_attempts=3, base_delay=2.0, **kwargs):
    """Retry a fetch call with exponential backoff."""
    last_error = None
    for attempt in range(max_attempts):
        try:
            result = fn(*args, **kwargs)
            # Treat empty DataFrame as failure
            if hasattr(result, "empty") and result.empty:
                raise ValueError("Empty result")
            return result
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt+1}/{max_attempts} failed: {e}")
            if attempt < max_attempts - 1:
                time.sleep(base_delay * (2 ** attempt))
    raise last_error
