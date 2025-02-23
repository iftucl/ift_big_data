import numpy as np
from scipy import stats

def calculate_market_cap_factor(market_caps: np.ndarray) -> np.ndarray:
    """
    Calculate a factor based on market capitalization that gives more weight to small-cap returns.

    :param market_caps: Array of market capitalizations
    :return: Array of factors to scale returns
    """
    # Step 1: Transform market cap to log-normal distribution.
    # Here we make the assumption on the distribution of Market cap
    # Empirical evidence suggests we have a small number of very large caps and long tail of smaller caps
    log_market_caps = np.log(market_caps)

    # Step 2: Derive log-normal distribution parameters
    log_mean = np.mean(log_market_caps)
    log_std = np.std(log_market_caps)

    # Step 3: Derive normal distribution parameters
    # To interpret the results in the original scale, we need to
    # use the properties of the log-normal distribution.
    normal_mean = np.exp(log_mean + log_std**2 / 2)
    normal_std = np.sqrt((np.exp(log_std**2) - 1) * np.exp(2*log_mean + log_std**2))

    # Step 4: Calculate z-scores
    z_scores = (market_caps - normal_mean) / normal_std

    # Step 5: Transform z-scores to factors using cumulative normal distribution (inverse mapping)
    # the minus before the z-scores is to give tilting to smaller caps
    factors = stats.norm.cdf(-z_scores)

    return factors
