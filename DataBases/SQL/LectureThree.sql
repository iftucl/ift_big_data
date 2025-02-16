/*
UCL -- Institute of Finance & Technology -- Big Data in Finance

Author	: Luca Cocconcelli
Lecture	: 2025-01-31
Topic	: SQL - Structured Query Language
*/

-- This is an in line SQL COMMENT

/*
Set up and downloads
for docker users, please follow instructions on wiki to install Docker Desktop and run
docker compose up to launch PostgresSQL

for non-docker users, download sqlite from here and follow installation instructions: https://www.sqlite.org/download.html

for Windows Users:
 - First, create a new folder e.g., C:\sqlite.
 - Second, extract the content of the file that you downloaded in the previous section to the C:\sqlite folder. You should see three programs in the C:\sqlite folder
 - Third, run sqlite3.exe

download sqlite browser from here https://sqlitebrowser.org/blog/portableapp-for-3-11-2-release-now-available/

For Mac Users check the tools page on Moodle. 

$ brew install sqlite

*/


/*--------------------------------------------------------------------------------------------------------------------------------------------------------------------
Section 1. SELECT statements
as an example: "SELECT what FROM whichTable;"
REMINDER! End your SQL Statements with the ";"
*/--------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 0. for pgadmin - docker users only:
-- in order to avoid the repetition of fixed_income schema in every query
SET search_path = cash_equity, "$user", public;

-- 1.a This SELECT statement returns all columns in the table equity_static
SELECT * FROM equity_static; 

-- 1.b This SELECT statement returns only the columns needed from the table equity_static
SELECT security, symbol, gics_sector FROM equity_static; 

-- 1.c This SELECT statement returns unique values contained into the trader column within portfolio_positions table. The output will be a trader names column
SELECT DISTINCT trader FROM portfolio_positions; 

-- 1.d here we introduce the LIMIT which returns only the top n rows needed (in this case 5, 6 or 7)
SELECT * FROM equity_prices LIMIT 5;
SELECT * FROM equity_static LIMIT 6;
SELECT * FROM portfolio_positions LIMIT 7;


/*--------------------------------------------------------------------------------------------------------------------------------------------------------------------
Section 2. WHERE Clause
as an example: "SELECT what FROM whichTable WHERE conditions;"
*/--------------------------------------------------------------------------------------------------------------------------------------------------------------------

-- 2.a WHERE equals: this statement selects all columns in the table equity_static where the gics_sector is Industrials.
SELECT * FROM equity_static WHERE gics_sector = 'Industrials';

-- 2.b WHERE equals: this statement selects all columns in the table equity_prices where the date is 21 November 2023
SELECT cob_date, symbol_id, close_price FROM equity_prices WHERE cob_date = '2023-11-21';

-- 2.c WHERE like: as before but it filters from the gics_industry field by using the like operator with the % %
SELECT symbol, gics_industry FROM equity_static WHERE gics_industry LIKE '%Health%';

-- 2.d WHERE is greater than: this query filters upon the condition that the trader position is greater than 10000000
SELECT symbol, trader, net_amount FROM portfolio_positions WHERE net_amount > 10000000;

-- 2.e  WHERE is less than: this query filters upon the condition that the price is less than 0 (hopefully returns an empty!)
SELECT symbol_id, cob_date, close_price FROM equity_prices WHERE close_price < 0;

-- 2.e WHERE in
SELECT symbol, security FROM equity_static WHERE gics_sector IN ('Health Care','Utilities');

-- 2.f WHERE is not null AND another condition is also used to filter out
SELECT limit_id FROM trader_limits -- for longer queries, we can write multiple lines...
WHERE limit_end IS NOT NULL
AND trader_id = 'MRH5231'; -- with this query we select all limits rule ids that are currently in place


/*--------------------------------------------------------------------------------------------------------------------------------------------------------------------
Section 3. GROUP BY statements
as an example: "SELECT what FROM whichTable GROUP BY columnToGroup;"
*/--------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 3.a simple GROUP BY equivalent to select distinct
SELECT region FROM equity_static GROUP BY region; -- grouping by region; in this case, it would be the equivalent of writing:
SELECT DISTINCT region FROM equity_static;

-- 3.b GROUP BY with COUNT function to summarise the number of companies by country
SELECT country, COUNT(symbol) AS no_companies -- AS operator will rename the output column name
FROM equity_static
GROUP BY country; -- in this query, we select the country Column and we create a new one (the count of companies per country date) and we group to know how many companies have same country

-- 3.c GROUP BY query with functions ROUND, SUM, AVG, MIN and MAX in order to summarise the min, max, total and the average
--     two traders summary position for a given date
SELECT trader, cob_date, SUM(net_amount) AS sum_amount,
ROUND(AVG(net_amount), 1) AS mean_amount, 
MIN(net_amount), MAX(net_amount) 
FROM portfolio_positions
WHERE trader IN ('MRH5231', 'DGR1983')  -- we want only positions for our traders
AND cob_date = '2023-10-27'		  -- and only for specific date
GROUP BY trader, cob_date
ORDER BY sum_amount DESC; 		-- this sorts out output from larger to smaller

/*-------------------------------------------------------------------------------------------------------------------------------------------------------------------- 
Section 4. JOINS statements
SELECT what FROM whichTableOne JOIN whichTableTwo ON whichTableOne.ID = whichTableTwo.ID;
*/--------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 4.a left join example: get the prices for ABBV in a specific date
SELECT symbol, security, cob_date, close_price FROM equity_static
LEFT JOIN equity_prices ON equity_static.symbol = equity_prices.symbol_id AND equity_prices.cob_date = '2021-04-15'
WHERE symbol = 'ABBV';

-- 4.b left join with some calculations. As an extra, we introduce HAVING clause
--     in this query, we take the derived trade price (i.e. amount bought in notional vs quantity)
--     and we compare it against the close price recorded in the market
SELECT symbol, equity_prices.cob_date,
	AVG(ABS(net_amount/net_quantity)) AS avg_trade_price, 
	AVG(close_price) AS close_px,
	AVG(ABS(net_amount/net_quantity)) / AVG(close_price) AS diff_px FROM portfolio_positions
LEFT JOIN equity_prices ON portfolio_positions.symbol = equity_prices.symbol_id 
WHERE equity_prices.cob_date = '2023-10-27'	
GROUP BY symbol, equity_prices.cob_date
HAVING AVG(ABS(net_amount/net_quantity)) / AVG(close_price) - 1 > 1 	-- HAVING is the WHERE condition applied on grouped data from which we have applied a function; 
ORDER BY diff_px DESC; 	-- WHERE clause is used for filtering rows and it applies on each and every row, while HAVING clause is used to filter groups in SQL
-- disclaimer: postgresql having doesn't support alias filtering while sqlite does

-- 4.c left join with tables containing same column names
-- you are tasked with the challenge of finding the largest 5 losses across all portfolios
-- for the day ending on 2023-10-27
SELECT portfolio_positions.trader,
	portfolio_positions.cob_date,
	portfolio_positions.symbol,
	portfolio_positions.net_amount,
	portfolio_positions.net_quantity, 
	portfolio_positions.net_quantity * equity_prices.close_price as mtm_amount, 
	portfolio_positions.net_quantity * equity_prices.close_price - portfolio_positions.net_amount as pnl
FROM portfolio_positions
LEFT JOIN equity_prices ON portfolio_positions.symbol = equity_prices.symbol_id AND portfolio_positions.cob_date = equity_prices.cob_date
WHERE portfolio_positions.cob_date = '2023-10-27'
ORDER BY pnl
LIMIT 5;

/*-------------------------------------------------------------------------------------------------------------------------------------------------------------------- 
SECTION 5
CASE to return column values based on conditions
*/--------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 5.a CASE WHEN operates as an if-else condition: it verifies if a condition is met, WHEN the condition is satisfied, returns a value, else moves to the next WHEN
-- condition. It ends the if-else loop when the END is met. In order to close the CASE statement you must declare where it END(S)
SELECT * FROM portfolio_positions WHERE net_quantity < 0;
SELECT symbol, ccy,
CASE 
	WHEN net_quantity < 0 THEN 'SHORT'
	WHEN net_quantity > 0 THEN 'LONG'
	ELSE 'NEUTRAL'
	END AS position_type,
SUM(net_amount)
FROM portfolio_positions 
WHERE cob_date = '2023-10-27'
GROUP BY symbol, ccy, position_type;


/*-------------------------------------------------------------------------------------------------------------------------------------------------------------------- 
SECTION 6
CREATE, DELETE & UPDATE operations
*/--------------------------------------------------------------------------------------------------------------------------------------------------------------------

-- 6.a we insert a position for DMZ1796 Trader
INSERT INTO fift.cash_equity.portfolio_positions 
	(pos_id, cob_date, trader, symbol, ccy, net_quantity, net_amount)
VALUES 
	('2023-10-27DMZ1796AAPLUSD', '2023-10-27', 'DMZ1796', 'AAPL', 'USD', 1000, 150000.00);
-- check the position now exists
SELECT * FROM portfolio_positions WHERE trader = 'DMZ1796' AND symbol = 'AAPL';

-- 6.b let's amend the quantity
UPDATE fift.cash_equity.portfolio_positions
SET net_quantity = 1500
WHERE trader = 'DMZ1796' AND symbol = 'AAPL';
-- check the update was successful
SELECT * FROM portfolio_positions WHERE trader = 'DMZ1796' AND symbol = 'AAPL';

-- 6.c let's now delete this entry
DELETE FROM fift.cash_equity.portfolio_positions
WHERE trader = 'DMZ1796' AND symbol = 'AAPL';
-- and now the position should be removed from our database
SELECT * FROM portfolio_positions WHERE trader = 'DMZ1796' AND symbol = 'AAPL';