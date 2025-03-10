# Trades API


## HOW TO?

### Depends on

In order to start this application you need to have these services available: redis (`redis`), mongodb (`mongo_db`) and postgresql (`postgres_db`).

If you have not yet build the containers, please build and launch the containers as:

```bash

docker compose up --build redis mongo_db postgres_db

```

In order to start the two containers:

```bash

docker compose start mongo_db postgres_db redis

```

### Start application

To launch the api:

```bash
cd Scripts/Python/7_Trades_API
poetry install
poetry run uvicorn main:app --host 0.0.0.0 --port 8010 --reload

```