-- create schema
CREATE SCHEMA IF NOT EXISTS fixed_income AUTHORIZATION postgres;

-- Bond Static
CREATE TABLE IF NOT EXISTS fift.fixed_income.bond_static (
	"isin"	CHAR(12) PRIMARY KEY,
	"description" TEXT,
	"issue_date"	DATE,
	"maturity"	DATE,
	"amount_outstanding"	NUMERIC,
	"idx_lag"	TEXT,
	"is_inflation"	BOOLEAN,
	"cpn_type"	TEXT,
	"ccy"	CHAR(3),
	"cpn"	NUMERIC
);


-- Bond Prices
CREATE TABLE IF NOT EXISTS fift.fixed_income.bond_prices (
	"price_id"	TEXT PRIMARY KEY,
	"cob_date"	DATE NOT NULL,
	"clean_price"	NUMERIC,
	"dirty_price"	NUMERIC,
	"acc_int"	NUMERIC,
	"yield_tm"	NUMERIC,
	"mod_duration"	NUMERIC,
	"isin_id"	CHAR(12),
	"ccy" CHAR(3),
	FOREIGN KEY("isin_id") REFERENCES fift.fixed_income.bond_static("isin")
);


-- Risk Positions
CREATE TABLE IF NOT EXISTS fift.fixed_income.risk_positions (
	"pos_id"	TEXT PRIMARY KEY,
	"cob_date"	DATE NOT NULL,
	"trader"	TEXT NOT NULL,
	"isin"	CHAR(12) NOT NULL,
	"ccy"	CHAR(3) NOT NULL,
	"net_quantity"	NUMERIC NOT NULL,
	"net_amount"	NUMERIC NOT NULL,
	FOREIGN KEY("isin") REFERENCES fift.fixed_income.bond_static("isin")
);

-- exchange_rates
CREATE TABLE IF NOT EXISTS fift.fixed_income.exchange_rates (
	"cob_date"	DATE NOT NULL,
	"exchange_rate"	NUMERIC,
	"from_currency"	TEXT NOT NULL,
	"fx_id" TEXT NOT NULL,
	"to_currency"	TEXT NOT NULL,
	PRIMARY KEY("fx_id")
)
