import numpy as np
from scipy import stats
from typing import List, Tuple

def tilt_weights(factor_list: list[dict], weights: None = None):

    if not weights:
        equal_weight = 1 / len(factor_list)
        factor_weights = [{x: y, "weight": equal_weight, "factor_weight": equal_weight * y} for x, y in factor_list.items()]
        total_weight = sum([x["factor_weight"] for x in factor_weights])
        factor_final = [{**x, "tilted_weight": x["factor_weight"] / total_weight} for x in factor_weights]
        sum([x["tilted_weight"] for x in factor_final])
        


def calculate_market_cap_factors(company_data: List[Tuple[str, float]]) -> dict:
    """
    Calculate market cap factors for a list of companies and map them back to symbols.

    :param company_data: List of tuples containing (company symbol, market cap)
    :return: Dictionary mapping company symbols to their calculated factors
    :example:
        >>> from modules.input_data.get_input_market_cap import get_market_cap
        >>> mcap_data = get_market_cap("2023-11-09")
        >>> company_data = [(x[0], x[7]) for x in mcap_data if x[7]]
        >>> mcap_factor = calculate_market_cap_factors(company_data)
    """
    # Separate symbols and market caps
    symbols, market_caps = zip(*company_data)
    market_caps = np.array(market_caps)

    # Calculate factors using the original function
    factors = calculate_market_cap_factor(market_caps)

    # Map factors back to symbols
    factor_list = dict(zip(symbols, factors))
    return factor_list


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
