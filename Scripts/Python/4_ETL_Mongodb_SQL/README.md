# ETL SQLite Aggregation

## Introduction

Script to aggregate trades from MongoDB and load to SQLite.

Input Mongo database to SQLite database specifications:

- mongodb: Database = Trades; Collection = TradingRecord
- SQLite: Table = trader_positions (create if not exist from SQLite client class in modules/db/sqlite_db.py)

## Configuration

configuration file is stored in properties/conf.yaml. The configurations can be amended without affecting code logic.

## Script Trigger

in order to trigger this script:

```
cd ./Scripts/Python/5.Lecture_20221113/ETLSQLite
python Main.py --date_run 2017-07-21

```