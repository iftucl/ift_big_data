import math
from datetime import datetime
from typing import List, Dict, Any
from scipy import stats

from modules.data_models.trade_model import Trade
from modules.data_models.trade_suspect import TradeSuspect

def prepare_data(trades: List[Trade]) -> List[Dict[str, float]]:
    """
    Prepare data for regression by extracting quantity and notional,
    and ensuring quantity is always positive.
    """
    return [{"quantity": abs(trade.Quantity), "notional": trade.Notional} for trade in trades]

def calculate_means(data: List[Dict[str, float]]) -> Dict[str, float]:
    """Calculate the means of quantity and notional."""
    n = len(data)
    sum_x = sum(item['quantity'] for item in data)
    sum_y = sum(item['notional'] for item in data)
    return {"mean_x": sum_x / n, "mean_y": sum_y / n}

def calculate_beta(data: List[Dict[str, float]], means: Dict[str, float]) -> float:
    """Calculate the beta (slope) of the regression line."""
    numerator = sum((item['quantity'] - means['mean_x']) * (item['notional'] - means['mean_y']) for item in data)
    denominator = sum((item['quantity'] - means['mean_x']) ** 2 for item in data)
    return numerator / denominator

def estimate_notional(quantity: float, beta: float, means: Dict[str, float]) -> float:
    """Estimate notional value using the regression line."""
    return beta * (quantity - means['mean_x']) + means['mean_y']

def calculate_standard_error(data: List[Dict[str, float]], beta: float, means: Dict[str, float]) -> float:
    """Calculate the standard error of the estimate."""
    n = len(data)
    residuals = [(item['notional'] - estimate_notional(item['quantity'], beta, means)) ** 2 for item in data]
    return math.sqrt(sum(residuals) / (n - 2))

def is_within_confidence_interval(actual: float, estimated: float, se: float, confidence: float = 0.99) -> bool:
    """Check if the actual notional is within the confidence interval of the estimated notional."""
    z_score = stats.norm.ppf((1 + confidence) / 2) # For 99% confidence level
    margin = z_score * se
    lower_bound = estimated - margin
    upper_bound = estimated + margin
    return lower_bound <= actual <= upper_bound

def analyze_trades(trades: List[Trade]) -> Dict[str, Any]:
    """Analyze trades: perform regression, estimate notionals, and test confidence intervals."""
    data = prepare_data(trades)
    means = calculate_means(data)
    beta = calculate_beta(data, means)
    se = calculate_standard_error(data, beta, means)

    results = []
    for trade in trades:
        estimated_notional = estimate_notional(abs(trade.Quantity), beta, means)
        within_ci = is_within_confidence_interval(trade.Notional, estimated_notional, se)
        results.append(TradeSuspect(**trade.model_dump(), ValidationLabel="Regression test against same trades", IsSuspect=not within_ci, ValidationTime=datetime.now(timezone.utc)))
    return {
        "beta": beta,
        "standard_error": se,
        "trade_analysis": results
    }

