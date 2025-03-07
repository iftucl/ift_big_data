from modules.db_ops.extract_from_query import get_postgres_data


sql_query = """ SELECT symbol_id, close_price FROM cash_equity.equity_prices ep WHERE cob_date == '{business_date}'"""


def get_previous_close_px(cob_date: str, database: str = "fift", **kwargs):
    """
    Get market cap data for specific date.

    :param: cob_date: string representation of cob date as 'YYYY-MM-DD'
    :type: cob_date: str

    :example:
        >>> cob_date = "2023-11-09"
    """
    sql_query_fmt = sql_query.format(cob_date=cob_date)
    price_data = get_postgres_data(sql_query=sql_query_fmt, database = database, **kwargs)
    return price_data
