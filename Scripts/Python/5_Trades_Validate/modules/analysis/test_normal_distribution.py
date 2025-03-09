from scipy.stats import norm
from datetime import datetime, timezone

from modules.utils import trades_validate_logger
from modules.data_models.trade_suspect import TradeSuspect
from modules.db.redis_manager import get_company_params
from modules.data_models.trade_model import Trade


def test_trades_peers(single_trade: Trade, confidence_level: float = 0.01) -> TradeSuspect:
    """
    Perform a hypothesis test to check if a stock's return comes from the same distribution
    as its sector's returns.
   
    The z-score measures how many standard deviations away the latest stock return
    is from the sector mean:

    .. math::

        z = \frac{x_{\text{latest}} - \mu}{\sigma}

    
    For a two-tailed test at a confidence level :math:`\alpha = 0.01`, the critical z-score is calculated as:

    .. math::

        z_{\text{critical}} = \Phi^{-1}(1 - \frac{\alpha}{2})

    Where :math:`\Phi^{-1}` is the inverse cumulative distribution function (percent-point function)
    of the standard normal distribution.
    We compare the absolute value of the calculated z-score ($|z|$) to the critical z-score ($z_{\text{critical}}$):
    
    - If:

    .. math::

    |z| > z_{\text{critical}}

    Reject the null hypothesis (:math:`H_0`), meaning that it is unlikely that
    :math:`x_{\text{latest}}` comes from the same distribution as the sector returns.
    
    :param latest_return: The latest return of the stock
    :param sector_returns: A list of returns for stocks in the same sector
    :param confidence_level: The confidence level for hypothesis testing (default: 0.01)
    :return: A string indicating whether to reject or fail to reject the null hypothesis
    """    
    # derive the implied trade price
    derived_price = single_trade.Notional / single_trade.Quantity
    # get calibrated factors from redis
    calibrated_params = get_company_params(company_id=single_trade.Symbol)
    if not calibrated_params:
        return TradeSuspect(**single_trade.model_dump(), ValidationLabel="No available parameters for testing", IsSuspect=True, ValidationTime=datetime.now(timezone.utc))
    if not calibrated_params.get("previous_close", None):
        return TradeSuspect(**single_trade.model_dump(), ValidationLabel="No available close price", IsSuspect=True, ValidationTime=datetime.now(timezone.utc))
    # derive trade price
    derived_return = derived_price / float(calibrated_params["previous_close"]) - 1
    # calc z score based on sector average and standard deviation of returns
    z_score = derived_return - calibrated_params["sector_average"] / calibrated_params["sector_stdev"]
    # critical value for a two tailed distribution
    critical_value = norm.ppf(1 - confidence_level / 2)
    # Step 4: Perform hypothesis test
    if abs(z_score) > critical_value:
        trades_validate_logger.info(f"Reject H0: The stock's return ({single_trade.Symbol}) does NOT come from the same distribution.")
        return TradeSuspect(**single_trade.model_dump(), ValidationLabel="Sector Return Validation", IsSuspect=True, ValidationTime=datetime.now(timezone.utc))
    else:
        trades_validate_logger.info(f"Fail to reject H0: The stock's return ({single_trade.Symbol}) may come from the same distribution.")
        return TradeSuspect(**single_trade.model_dump(), ValidationLabel="Sector Return Validation", IsSuspect=False, ValidationTime=datetime.now(timezone.utc))
