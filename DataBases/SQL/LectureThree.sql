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
SET search_path = fixed_income, "$user", public;

-- 1.a This SELECT statement returns all columns in the table bond_static
SELECT * FROM bond_static; 

-- 1.b This SELECT statement returns only the columns needed from the table bond_static
SELECT description, isin, issue_date FROM bond_static; 

-- 1.c This SELECT statement returns unique values contained into the trader column within risk_positions table. The output will be a trader names column
SELECT DISTINCT trader FROM risk_positions; 

-- 1.d here we introduce the LIMIT which returns only the top n rows needed (in this case 5, 6 or 7)
SELECT * FROM bond_prices LIMIT 5;
SELECT * FROM bond_static LIMIT 6;
SELECT * FROM risk_positions LIMIT 7;


/*--------------------------------------------------------------------------------------------------------------------------------------------------------------------
Section 2. WHERE Clause
as an example: "SELECT what FROM whichTable WHERE conditions;"
*/--------------------------------------------------------------------------------------------------------------------------------------------------------------------

-- 2.a WHERE equals: this statement selects all columns in the table bond_static where the CPN Type is STRIP
SELECT * FROM bond_static WHERE cpn_type = 'STRIP';

-- 2.b WHERE equals: this statement selects all columns in the table bond_prices where the date is 01-Jul-2016
SELECT cob_date, isin_id, clean_price FROM bond_prices WHERE cob_date = '01-Jul-2016';

-- 2.c WHERE like: as before but it filters from the description field by using the like opearator with the % %
SELECT isin, description FROM bond_static WHERE cpn_type LIKE '%STRIP%';

-- 2.d WHERE is greater than: this query filters upon the condition that the amount outstanding is greater than 1000
SELECT isin, amount_outstanding FROM bond_static WHERE amount_outstanding > 1000;

-- 2.e  WHERE is greater than: this query filters upon the condition that the dirty price is greater than 300
SELECT isin_id, cob_date, dirty_price FROM bond_prices WHERE dirty_price > 300;

-- 2.e WHERE in
SELECT isin FROM bond_static WHERE cpn_type IN ('STRIP','FIXED');

-- 2.f WHERE is not null AND another condition is also used to filter out
SELECT isin FROM bond_static -- for longer queries, we can write multiple lines...
WHERE issue_date IS NOT NULL
AND cpn_type = 'FIXED'; -- with this query we select all isins that have an issue_date in our DB and also thos that have a FIXED coupon



/*--------------------------------------------------------------------------------------------------------------------------------------------------------------------
Section 3. GROUP BY statements
as an example: "SELECT what FROM whichTable GROUP BY columnToGroup;"
*/--------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 3.a simple GROUP BY equivalent to select distinct
SELECT maturity FROM bond_static GROUP BY maturity; -- grouping by maturity; in this case, it would be the equivalent of writing:
SELECT DISTINCT maturity FROM bond_static;

-- 3.b GROUP BY with COUNT function to summarise the number of isins by maturity
SELECT maturity, COUNT(isin) AS no_isins -- AS operator will rename the output column name
FROM bond_static
GROUP BY maturity; -- in this query, we select the maturity Column and we create a new one (the count of isin per maturity date) and we group to know how many isins have same maturity

-- 3.c GROUP BY query with functions ROUND, SUM, AVG, MIN and MAX in order to summarise the min, max, total and the average aoumnt issued by the DMO in each auction
SELECT SUM(amount_outstanding) AS sum_amount,
ROUND(AVG(amount_outstanding), 1) AS mean_amount, 
MIN(amount_outstanding), MAX(amount_outstanding) 
FROM bond_static
WHERE issue_date IS NOT NULL     	  -- this excludes from our calculation anything that is missing
GROUP BY issue_date
ORDER BY sum_amount DESC 		-- this sorts out output from larger to smaller
LIMIT 5; 						-- this limits the output table only to the top 5 rows

/*-------------------------------------------------------------------------------------------------------------------------------------------------------------------- 
Section 4. JOINS statements
SELECT what FROM whichTableOne JOIN whichTableTwo ON whichTableOne.ID = whichTableTwo.ID;
*/--------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 4.a left join example and filter out on a isin
SELECT isin, maturity, cob_date, clean_price, yield_tm FROM bond_static
LEFT JOIN bond_prices ON bond_static.isin = bond_prices.isin_id
WHERE isin = 'GB00BBDR7T29';

-- 4.b left join with some calculations. As an extra, we introduce HAVING clause
SELECT isin, AVG(clean_price) AS avg_px, AVG(yield_tm) AS avg_yield FROM bond_static
LEFT JOIN bond_prices ON bond_static.isin = bond_prices.isin_id 
GROUP BY isin 
HAVING AVG(clean_price) > 120 	-- HAVING is the WHERE condition applied on grouped data from which we have applied a function; 
ORDER BY avg_px DESC; 	-- WHERE clause is used for filtering rows and it applies on each and every row, while HAVING clause is used to filter groups in SQL
-- disclaimer: postgresql having doesn't support alias filtering while sqlite does

-- 4.c left join with tables containing same column names
SELECT risk_positions.trader, risk_positions.cob_date, risk_positions.isin, risk_positions.net_amount,risk_positions.net_quantity, 
risk_positions.net_quantity * bond_prices.dirty_price as mtm_amount, 
risk_positions.net_quantity * bond_prices.dirty_price - risk_positions.net_amount as pnl
FROM risk_positions
LEFT JOIN bond_prices ON risk_positions.isin = bond_prices.isin_id AND risk_positions.cob_date = bond_prices.cob_date
WHERE risk_positions.cob_date = '2016-07-01'; 

/*-------------------------------------------------------------------------------------------------------------------------------------------------------------------- 
SECTION 5
CASE to return column values based on conditions
*/--------------------------------------------------------------------------------------------------------------------------------------------------------------------
-- 5.a CASE WHEN operates as an if-else condition: it verifies if a condition is met, WHEN the condition is satisfied, returns a value, else moves to the next WHEN
-- condition. It ends the if-else loop when the END is met. In order to close the CASE statement you must declare where it END(S)

SELECT cpn_type, 
CASE 
	WHEN cpn_type = 'IL' THEN 'INFLATION'
	WHEN cpn_type = 'FIXED' THEN 'Fixed Coupon'
	WHEN cpn_type = 'STRIP' THEN 'Strip Bond'
	ELSE 'unknown'
	END AS my_new_cpn_type
FROM fixed_income.bond_static GROUP BY cpn_type, my_new_cpn_type;

--5.b CASE is a very powerful tool and helps in creating temporary data transformation to assist in our data query operations.

SELECT bs.isin, bs.cpn_type, bp.clean_price, bp.dirty_price, 
bp.acc_int, CASE 
		     WHEN bs.cpn_type = 'IL' THEN bp.dirty_price + bp.acc_int 
			 ELSE bp.clean_price + bp.acc_int END AS mtm_price
FROM (
SELECT * FROM fixed_income.bond_prices WHERE cob_date = '2016-07-01'
) AS bp
LEFT JOIN fixed_income.bond_static AS bs ON bp.isin_id = bs.isin;



/*--------------------------------------------------------------------------------------------------------------------------------------------------------------------
Section 0. Create our first database in SQLite
Data Types:
NULL
INTEGER
REAL 
TEXT
BLOB
We need to specify what a column contains when we create a table
*/--------------------------------------------------------------------------------------------------------------------------------------------------------------------

-- 0.a from SQLite command line 
sqlite3 BondPrice.db
-- if already created, we need to tell sqlite where our db is.. as an example:
.open C:\sqlite\db\BondPrice.db
-- 0.b now we can check which database we have and which tables are in there as
.database
.tables
-- 0.c to exit, just type
.exit

-- 0.c DELETE tables in SQL
-- WARNING STARTS!!! Think Carefully before running this code!!!
DROP TABLE bond_prices;
DROP TABLE bond_static;
-- WARNING ENDS!!!

-- 0.d CREATE tables in SQL
CREATE TABLE bond_static (
    isin PRIMARY KEY,
    description TEXT,
    issue_date TEXT,
    maturity TEXT,
    amount_outstanding INTEGER,
	idx_lag TEXT,
	is_inflation TEXT,
	cpn_type TEXT,
	ccy TEXT,
	cpn INTEGER
);

CREATE TABLE bond_prices (
    price_id INTEGER PRIMARY KEY,
    cob_date TEXT NOT NULL,
    clean_price INTEGER,
    dirty_price INTEGER,
    acc_int INTEGER,
	yield INTEGER,
	mod_duration INTEGER,
	isin_id TEXT,
	FOREIGN KEY (isin_id) REFERENCES bond_static (isin)
);

CREATE TABLE risk_positions (
    pos_id INTEGER PRIMARY KEY,
    cob_date TEXT NOT NULL,
    trader TEXT NOT NULL,
    isin TEXT NOT NULL,
    ccy TEXT NOT NULL,
	net_quantity INTEGER NOT NULL,
	net_amount INTEGER NOT NULL,
	FOREIGN KEY (isin) REFERENCES bond_static (isin)
);


-- 0.e SET NULLs
-- UPDATE tableName SET columnName = NULL WHERE columnName = 'NULL';
UPDATE bond_static SET idx_lag = NULL WHERE idx_lag = 'NULL';


