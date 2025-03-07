import numpy as np
from scipy import stats
from typing import List, Tuple, Optional, Callable, Literal
from datetime import datetime, timedelta

def calculate_var(price_data: List[Tuple[datetime, float]], 
                  holding_period: int = 1, 
                  confidence_level: float = 0.95, 
                  scaling_function: Optional[Callable[[np.ndarray, int], np.ndarray]] = None,
                  var_type: Optional[Literal["parametric", "nonparametric"]] = "nonparametric",
                  use_squared_returns: bool = False) -> float:
    """
    Calculate Value at Risk (VaR) for a given time series of equity prices.

    This function calculates VaR using either parametric or non-parametric methods,
    with options for custom scaling of returns.

    :param price_data: List of tuples containing timestamp and price
    :type price_data: List[Tuple[datetime, float]]
    :param holding_period: Number of days for the holding period, defaults to 1
    :type holding_period: int, optional
    :param confidence_level: Confidence level for VaR calculation, defaults to 0.95
    :type confidence_level: float, optional
    :param scaling_function: Function to scale returns, defaults to None
    :type scaling_function: Optional[Callable[[np.ndarray, int], np.ndarray]], optional
    :param var_type: Type of VaR calculation ("parametric" or "nonparametric"), defaults to "nonparametric"
    :type var_type: Optional[Literal["parametric", "nonparametric"]], optional
    :return: Calculated Value at Risk
    :rtype: float

    :raises ValueError: If confidence_level is not between 0 and 1
    :raises ValueError: If holding_period is not a positive integer
    :raises ValueError: If var_type is not "parametric" or "nonparametric"

    .. note::
       The scaling_function, if provided, should take two arguments:
       the numpy array of returns and the holding period.

    .. seealso::
       - :func:`calculate_returns` for details on return calculation
       - :func:`calculate_parametric_var` for parametric VaR calculation
       - :func:`calculate_nonparametric_var` for non-parametric VaR calculation

    Example:
    >>> from datetime import datetime, timedelta
    >>> start_date = datetime(2025, 1, 1)
    >>> price_data = [(start_date + timedelta(days=i), 100 + i) for i in range(100)]
    >>> var = calculate_var(price_data, holding_period=5, confidence_level=0.99)
    >>> print(f"99% VaR (5-day holding period): {var:.4f}")
    99% VaR (5-day holding period): 0.1234
    """    
    # Sort price data and extract prices
    sorted_data = sorted(price_data)
    dates, prices = zip(*sorted_data)
    prices = np.array(prices)
    
    # Calculate returns based on holding period
    returns = calculate_returns(prices, holding_period, use_squared=use_squared_returns)
    
    # Scale returns if scaling function is provided
    if scaling_function is not None:
        returns = scaling_function(returns, holding_period)
    
    # Calculate VaR
    if var_type == "non-parametric":
        var = calculate_nonparametric_var(returns, confidence_level)
        return var
    
    var = calculate_parametric_var(returns, confidence_level, use_squared=use_squared_returns)
    return var

def calculate_returns(prices: np.ndarray, holding_period: int, use_squared: bool = False) -> np.ndarray:
    """
    Calculate returns based on the specified holding period.

    This function calculates returns for an array of prices. It provides with the option of calculation the 
    returns a squared return (:math:`{x}^2`).
    
    Args:
    -----
    :param prices: Array of prices
    :type prices: np.ndarray
    :param holding_period: Holding period in days. This will calculate the returns over 1,2,3,... days holding period.
    :type holding_period: int
    :param use_squared: Whether we are using squared returns or normal returns. Defaults to False.
    :type use_squared: bool
    :return: Calculated returns
    :rtype: np.ndarray
    """
    simple_returns = np.log(prices[holding_period:]) - np.log(prices[:-holding_period])
    if use_squared:
        return simple_returns ** 2    
    return simple_returns

def ewma_scaling(returns: np.ndarray, holding_period: int, lambda_: float = 0.94) -> np.ndarray:
    """
    Scale returns using Exponentially Weighted Moving Average (EWMA).
    
    Args:
    returns (np.ndarray): Array of returns
    holding_period (int): Number of days for the holding period
    lambda_ (float): Decay factor for EWMA (default: 0.94)
    
    Returns:
    np.ndarray: Scaled returns
    """
    weights = np.array([(1 - lambda_) * lambda_**i for i in range(len(returns))])
    weights = weights[::-1]  # Reverse the weights so that recent returns have higher weight
    weights /= np.sum(weights)  # Normalize weights
    
    return returns * weights * np.sqrt(holding_period)

def calculate_parametric_var(returns: np.ndarray, confidence_level: float, use_squared: bool = False) -> float:
    """
    Calculate Parametric Value at Risk (VaR) from returns.

    This function calculates VaR using the parametric method, assuming normally
    distributed returns.

    :param returns: Array of historical returns
    :type returns: numpy.ndarray
    :param confidence_level: Confidence level for VaR calculation
    :type confidence_level: float
    :param use_squared: Whether we are using squared returns or normal returns. Defaults to False.
    :type use_squared: bool
    :return: Calculated Value at Risk
    :rtype: float

    :raises ValueError: If confidence_level is not between 0 and 1
    :raises ValueError: If returns is empty

    .. note::
       This method assumes that returns are normally distributed. It may not
       be appropriate for assets with non-normal return distributions.

    .. seealso::
       :func:`calculate_nonparametric_var` for a non-parametric approach to VaR calculation

    Example:
    >>> import numpy as np
    >>> returns = np.array([0.02, -0.01, 0.03, -0.02, 0.01, -0.03, 0.02, -0.02, 0.01, -0.01])
    >>> var = calculate_parametric_var(returns, confidence_level=0.95)
    >>> print(f"95% Parametric VaR: {var:.4f}")
    95% Parametric VaR: 0.0382
    """
    if use_squared:
        mean = np.mean(returns)
        std_dev = np.sqrt(mean)  # For squared returns, std_dev is sqrt of mean    
    else:
        # Calculate the standard deviation of returns
        mean = np.mean(returns)
        std_dev = np.std(returns)    
    # Calculate the z-score for the given confidence level
    z_score = stats.norm.ppf(1 - confidence_level)    
    # Calculate VaR
    var = z_score * std_dev

    return var

def calculate_nonparametric_var(returns: np.ndarray, 
                                confidence_level: float = 0.99, 
                                holding_period: int = 1) -> float:
    """
    Calculate non-parametric Value at Risk using Historical Simulation method.

    This function implements the Historical Simulation approach to calculate
    Value at Risk (VaR) without assuming any particular distribution of returns.

    :param returns: Array of historical returns
    :type returns: numpy.ndarray
    :param confidence_level: Confidence level for VaR calculation, defaults to 0.99
    :type confidence_level: float, optional
    :param holding_period: Number of days for the holding period, defaults to 1
    :type holding_period: int, optional
    :return: Calculated Value at Risk
    :rtype: float

    :raises ValueError: If confidence_level is not between 0 and 1
    :raises ValueError: If holding_period is not a positive integer

    .. note::
       This method assumes that past returns are representative of future returns.
       It may not perform well for very high confidence levels or long holding periods
       if there's limited historical data.

    .. seealso::
       For parametric VaR calculation, refer to the `calculate_parametric_var` function.

    Example:
    >>> returns = np.array([0.02, -0.01, 0.03, -0.02, 0.01, -0.03, 0.02, -0.02, 0.01, -0.01])
    >>> var_95 = calculate_nonparametric_var(returns, confidence_level=0.95, holding_period=1)
    >>> print(f"95% VaR (1-day holding period): {var_95:.4f}")
    95% VaR (1-day holding period): 0.0300
    """    # Sort returns in ascending order
    sorted_returns = np.sort(returns)
    
    # Find the index corresponding to the VaR quantile
    var_index = int(len(sorted_returns) * (1 - confidence_level))
    
    # Calculate VaR
    var = -sorted_returns[var_index]

    # Adjust for holding period using the square root of time rule
    var_adjusted = var * np.sqrt(holding_period)
    
    return var_adjusted
