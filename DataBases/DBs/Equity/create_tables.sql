-- create schema
CREATE SCHEMA IF NOT EXISTS cash_equity AUTHORIZATION postgres;

-- Equity Static
CREATE TABLE IF NOT EXISTS fift.cash_equity.equity_static (
	"symbol" CHAR(12) PRIMARY KEY,
	"security" TEXT,
	"gics_sector"	TEXT,
	"gics_industry"	TEXT,
	"country"	TEXT,
	"region"	TEXT	
);


-- Equity Prices
CREATE TABLE IF NOT EXISTS fift.cash_equity.equity_prices (
	"price_id"	VARCHAR(252) PRIMARY KEY,
	"open_price"	NUMERIC,
	"close_price"	NUMERIC,
	"volume"	NUMERIC,
	"currency" CHAR(3),
	"cob_date"	DATE NOT NULL,
	"symbol_id"	CHAR(12)
	
);
ALTER TABLE fift.cash_equity.equity_prices ALTER COLUMN price_id TYPE VARCHAR(252);

-- Portfolio Positions
CREATE TABLE IF NOT EXISTS fift.cash_equity.portfolio_positions (
	"pos_id" TEXT PRIMARY KEY,
	"cob_date"	DATE NOT NULL,
	"trader"	CHAR(7) NOT NULL,
	"symbol"	CHAR(12) NOT NULL,
	"ccy"	CHAR(3) NOT NULL,
	"net_quantity"	NUMERIC NOT NULL,
	"net_amount"	NUMERIC NOT NULL
);

ALTER TABLE fift.cash_equity.portfolio_positions ALTER COLUMN pos_id TYPE VARCHAR(252);

-- Exchange Rates
CREATE TABLE IF NOT EXISTS fift.cash_equity.exchange_rates (
	"from_currency"	CHAR(3) NOT NULL,
	"to_currency"	CHAR(3) NOT NULL,
	"exchange_rate"	NUMERIC,
	"cob_date"	DATE NOT NULL,
	"fx_id" TEXT NOT NULL,	
	PRIMARY KEY("fx_id")
);


-- trader limits
CREATE TABLE IF NOT EXISTS fift.cash_equity.trader_limits (
	"limit_id" TEXT PRIMARY KEY,
    "trader_id" CHAR(7),
    "limit_type" TEXT,
	"limit_category" TEXT,
	"limit_amount" INTEGER NOT NULL,
	"currency" CHAR(3),
    "limit_start" DATE NOT NULL,
    "limit_end" DATE
);

-- Trader Static
CREATE TABLE IF NOT EXISTS fift.cash_equity.trader_static (
    "trader_id" CHAR(7) PRIMARY KEY,
    "trader_name" TEXT,
    "fund_name" TEXT,
    "fund_type" CHAR(3) NOT NULL,
    "fund_focus" TEXT,
	"fund_currency" CHAR(3) NOT NULL,
	"is_active" CHAR(1) NOT NULL,
	"golive_date" DATE NOT NULL,
	"termination_date" DATE, 
	"region_focus" TEXT
);
