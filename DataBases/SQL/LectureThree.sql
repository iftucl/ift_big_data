/*
UCL -- Institute of Finance & Technology -- Big Data in Finance

Author	: Luca Cocconcelli
Lecture	: 2024-02-01
Topic	: SQL - Structured Query Language
*/

-- This is an in line SQL COMMENT

/*
Set up and downloads
for docker users, please follow instructions on wiki to install Docker Desktop and run
docker compose up to launch PostgresSQL

for non-docker users, download sqlite from here and follow installation instructions: https://www.sqlite.org/download.html

for Windows Users:
First, create a new folder e.g., C:\sqlite.
Second, extract the content of the file that you downloaded in the previous section to the C:\sqlite folder. You should see three programs in the C:\sqlite folder
Third, run sqlite3.exe

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

-- 2.c WHERE like: as before but it filters from the gics_industry field by using the like opearator with the % %
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
