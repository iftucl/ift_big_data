# Postgres ETL - Trades Aggregator

Aggregates trades from Minio to Postgres using Duckdb.

<p align="center">
    <a href=""><img src="../../../assets/img/minio_postgres_duckdb.png" alt="BigData-IFT"></a>
</p>


## Configuration

configuration file is stored in properties/conf.yaml. The configurations can be amended without affecting code logic.

## Depends on

To run this script you will need to start `postgres_db` and `minio` containers.

If you haven't created these containers yet, please run:

```bash

docker compose up minio postgres_db -d

```

else, if the containers already exists:

```bash

docker compose start minio postgres_db

```

## Script trigger

Script can be triggered as:

```bash

cd Scripts/Python/3_ETL_Duckdb_Postgres
poetry run python main.py --date_run='2023-11-23' --env_type='dev'

```

Please note command arg while the `env_type` is required `--date_run` is not mandatory.

In order to get a summary of main command args available:

```bash

python main.py --help

```

### Debug mode

Run it locally as:

```python

import os
os.chdir("Scripts/Python/3_ETL_Duckdb_Postgres")

```


