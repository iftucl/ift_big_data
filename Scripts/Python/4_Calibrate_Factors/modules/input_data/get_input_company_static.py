from modules.db_ops.extract_from_query import get_postgres_data
from modules.data_models.static_model import EquityStatic


def get_equity_static(database: str = "fift", **kwargs):
    """
    Get equity static data for specific date.

    :param: cob_date: string representation of cob date as 'YYYY-MM-DD'
    :type: cob_date: str    
    """
    sql_query = """SELECT * FROM cash_equity.equity_static"""
    static_data = get_postgres_data(sql_query=sql_query, database = database, **kwargs)
    return [EquityStatic(company_id=x[0],
                         company_name=x[1],
                         sector_name=x[2],
                         industry_name=x[3],
                         country_id=x[4],
                         region_name=x[5]) for x in static_data]
