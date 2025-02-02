# MongoDB Data Loader

## Introduction

Script to load trades (csv files) into MongoDB.

Input folder to database specifications:

- minio folder: ''
- mongodb: Database = Trades; Collection = TradingRecord

## Depends on

To run this script you will need to start `MongoDB` and `Minio` containers:

```bash

docker compose up minio mongodb -d

```

## Configuration

configuration file is stored in properties/conf.yaml. The configurations can be amended without affecting code logic.

## Script Trigger

in order to trigger this script:

```
cd ./Scripts/Python/5.Lecture_20221113/ETLMongoDB
poetry run python Main.py --env_type='dev'

```