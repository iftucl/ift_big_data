from modules.data_models.static_model import EquityStatic
from modules.db_ops.redis_client import store_company_params

def load_market_moves_redis(company_statics: list[EquityStatic], sector_ret_dist, close_price):
    """
    Load param for data validation to redis.

    """

    for item in company_statics:
        previous_close = [x for x in close_price if x[0] == item.company_id]
        if previous_close:            
            close_px = previous_close[0][1]
        else:
            close_px = None
        distribution_param=[x.model_dump() for x in sector_ret_dist if x.sector_name == item.sector_name][0]
        distribution_param["previous_close"] = close_px
        store_company_params(company_id=item.company_id, params=distribution_param)


