import duckdb
import pandas as pd


def get_aggregated_trades(trades_list: list[dict]) -> list[dict]:
    """
    Aggregate trade data
    ^^^^^^^^^^^^^^^^^^^^
    
    Aggregates by Trader, Symbol, Currency (Ccy), and Date, summing the Notional and Quantity values.    
    Also creates a unique position ID (`pos_id`) by concatenating the date, trader, symbol, and currency.

    :param trades_list: 
        A list of dictionaries where each dictionary represents a trade. Each dictionary is expected 
        to have the following keys:
        - Trader (str): The trader's name.
        - Symbol (str): The traded instrument's symbol.
        - Ccy (str): The currency of the trade.
        - Notional (str or numeric): The notional value of the trade.
        - Quantity (str or numeric): The quantity of the trade.
        - DateTime (str): A timestamp string in ISO 8601 format (e.g., '2023-11-23 08:02:49+00:00').

    :type trades_list: list[dict]

    :return: 
        A list of aggregated trade records, where each record is a dictionary with the following keys:
        - Trader (str): The trader's name.
        - Symbol (str): The traded instrument's symbol.
        - Ccy (str): The currency of the trade.
        - Date (str): The date extracted from the DateTime column in YYYY-MM-DD format.
        - pos_id (str): A unique position ID created by concatenating Date, Trader, Symbol, and Ccy.
        - Total_Notional (float): The sum of the notional values for the group.
        - Total_Quantity (float): The sum of the quantities for the group.

    :rtype: list[dict]
    """
    # Convert input list to DataFrame
    trades_df = pd.DataFrame(trades_list)

    # DuckDB query to aggregate data and create pos_id
    query = """
        SELECT 
            CONCAT(
                strftime(date_trunc('day', CAST(DateTime AS TIMESTAMP)), '%Y-%m-%d'),
                Trader,
                Symbol,
                Ccy
            ) AS pos_id,
            strftime(date_trunc('day', CAST(DateTime AS TIMESTAMP)), '%Y-%m-%d') AS cob_date,
            Trader AS trader, 
            Symbol AS symbol, 
            Ccy AS ccy,             
            SUM(CAST(Notional AS DOUBLE)) AS net_amount, 
            SUM(CAST(Quantity AS DOUBLE)) AS net_quantity
        FROM trades_df
        GROUP BY Trader, Symbol, Ccy, date_trunc('day', CAST(DateTime AS TIMESTAMP))
    """
    
    # Execute query using DuckDB
    aggregated_df = duckdb.query(query).to_df()

    # Convert result back to a list of dictionaries
    return aggregated_df.to_dict(orient="records")
