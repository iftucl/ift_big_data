from modules.data_models.static_model import EquityStatic
from modules.db_ops.redis_client import store_company_params

def load_market_moves_redis(company_statics: list[EquityStatic], sector_ret_dist):
    """
    Load param for data validation to redis.
    
    """

    for item in company_statics:        
        distribution_param=[x.model_dump() for x in sector_ret_dist if x.sector_name == item.sector_name]
        store_company_params(company_id=item.company_id, store_company_params=distribution_param[0])


