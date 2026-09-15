def safe_float(x, default=None):
    """
    Convert scalar, 1-element Series, or 1-element array to Python float.
    Returns `default` if conversion fails.
    """
    if x is None:
        return default
    try:
        # numpy scalar, pandas scalar
        if hasattr(x, 'item'):
            return float(x.item())
        # pandas Series or DataFrame
        if hasattr(x, 'iloc'):
            if len(x) == 0:
                return default
            return float(x.iloc[0])
        return float(x)
    except (TypeError, ValueError):
        return default
