import pyarrow as pa


'''
Setup schema for write ops in parquet
'''

def generate_parquet_schema():
    """
    parquet_schema
    ==============
    ----
    Notes
    
    ----

    Parquet Schema Definition 
    to write parquet files
    """

    schema = pa.schema([('DateTime', pa.string()),
                        ('TradeId', pa.string()),
                        ('Trader', pa.string()),
                        ('ISIN', pa.string()),
                        ('Quantity', pa.int64()),
                        ('Notional', pa.float64()),
                        ('TradeType', pa.string()),
                        ('Ccy', pa.string()),
                        ('Counterparty', pa.string())
                        ])
    return schema