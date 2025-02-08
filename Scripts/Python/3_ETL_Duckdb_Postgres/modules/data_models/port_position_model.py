from sqlalchemy import Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import types, Table, Column

Base = declarative_base()

class PortfolioPositions(Base):
    __table__ = Table(
        'portfolio_positions', 
        Base.metadata,
        Column('pos_id', types.Text, primary_key=True),
        Column('cob_date', types.Date),
        Column('trader', types.Text),
        Column('symbol', types.Text),
        Column('ccy', types.Text),
        Column('net_quantity', types.Numeric),
        Column('net_amount', types.Numeric),
        schema='cash_equity')
