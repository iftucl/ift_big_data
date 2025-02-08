from sqlalchemy import Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import types, Table, Column

Base = declarative_base()

class RiskPositions(Base):
    __table__ = Table(
        'risk_positions', 
        Base.metadata,
        Column('pos_id', types.Text, primary_key=True),
        Column('cob_date', types.Date),
        Column('trader', types.Text),
        Column('isin', types.Text),
        Column('ccy', types.Text),
        Column('net_amount', types.Numeric),
        Column('net_quantity', types.Numeric),
        schema='fixed_income')
