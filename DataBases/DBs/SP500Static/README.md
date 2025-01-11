# MongoDB Collections

## Introduction

This folders contains a json dump of 2 collection with Equity Static data for S&P500 Stocks.

## Load to MongoDB

Step 1: Identify where you MongoDB bin is on your file system.
Step 2: Take note of the path to the Mongodb bin, as an example:

```
C:/Program Files/MongoDB/Server/4.2/bin/

```

Step 3: open Git Bash or Shell or cmd in the present directory, amend the below <insert_path_to_mongo_bin> with the MongoDB bin path as shown in previous steps.
Step 4: run below command

```

"<insert_path_to_mongo_bin>/mongoimport" --db EquitySP500 --collection Static < ./SP500Data.json --jsonArray

```
