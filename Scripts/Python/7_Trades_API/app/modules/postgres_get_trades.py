from modules.db_clients.postgres_client import get_postgres_data

async def get_unique_trader_ids(database: str, **kwargs) -> list:
    """
    Get the list of active traders id

    :param database: the name of the database like 'fift'

    """
    sql_query="SELECT DISTINCT(trader_id) FROM cash_equity.trader_static"
    all_traders = get_postgres_data(sql_query=sql_query, database="fift")
    return [x[0] for x in all_traders]