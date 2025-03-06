from modules.db_ops.extract_from_query import get_postgres_data


sql_query = """SELECT ct.symbol, ct.float_shares, cs.region, cs.country, cs.gics_sector, ep.currency,
(ep.close_price * ex.exchange_rate) AS px_usd,
(ep.close_price * ex.exchange_rate * ct.float_shares) AS mcap_usd FROM cash_equity.company_statistics ct
LEFT JOIN cash_equity.equity_static cs ON ct.symbol = cs.symbol
LEFT JOIN cash_equity.equity_prices ep ON ct.symbol = ep.symbol_id AND ep.cob_date = '{cob_date}'
LEFT JOIN cash_equity.exchange_rates ex ON ep.currency = ex.from_currency AND ex.cob_date = '{cob_date}' AND ex.to_currency = 'USD'
WHERE ct.float_shares IS NOT NULL"""


def get_market_cap(cob_date: str, database: str = "fift", **kwargs):
    """
    Get market cap data for specific date.

    :param: cob_date: string representation of cob date as 'YYYY-MM-DD'
    :type: cob_date: str

    :example:
        >>> cob_date = "2023-11-09"
    """
    sql_query_fmt = sql_query.format(cob_date=cob_date)
    mcap_data = get_postgres_data(sql_query=sql_query_fmt, database = database, **kwargs)
    return mcap_data
