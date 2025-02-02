# Random Trade Generator

## Introduction

Random trade generator script.

This script generates random trades in batches file csv files which will be save into minio bucket iftbigdata:

- folder: 'DataLake/Trades'

## Configuration

configuration file is stored in properties/conf.yaml. The configurations can be amended without affecting code logic.

## Depends on

To run this script you will need to start `postgres_db` and `minio` containers:

```bash

docker compose up minio postgres_db -d

```


## Script trigger

Script can be triggered as:

```bash

cd Scripts/Python/0_RandomTrades
poetry run python main.py --date_run='2023-11-23' --env_type='dev' --output_file='csv' --input_database='Postgres'

```

Please note command arg --date_run is mandatory while other command args are optional.

In order to get a summary of main command args available:

```

python main.py --help

```

### Debug mode

Run it locally as:

```python

import os
os.chdir("Scripts/Python/0_RandomTrades")

```


