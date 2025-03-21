import requests
import json
from requests.exceptions import HTTPError, ConnectionError

KAFKA_CONNECT_URL = "http://localhost:8083/connectors"
CONNECTOR_NAME = "test-stream-trades"

connector_config = {
    "config": {
        "connector.class": "com.mongodb.kafka.connect.MongoSinkConnector",
        "tasks.max": "1",
        "topics": "fast_trades",
        "connection.uri": "mongodb://mongo_db:27017",
        "database": "Trades",
        "collection": "FastTrades",
        "key.converter": "org.apache.kafka.connect.storage.StringConverter",
        "value.converter": "org.apache.kafka.connect.storage.StringConverter",
        "key.converter.schemas.enable": "false",
        "value.converter.schemas.enable": "false",
        "value.projection.list": "tokenNumber",
        "value.projection.type": "whitelist"
    }
}

try:
    # Check existing connectors
    response = requests.get(f"{KAFKA_CONNECT_URL}/{CONNECTOR_NAME}/status")
    
    if response.status_code == 200:
        print(f"Connector {CONNECTOR_NAME} already exists")
    elif response.status_code == 404:
        # Create new connector using PUT for idempotent creation
        put_response = requests.put(
            f"{KAFKA_CONNECT_URL}/{CONNECTOR_NAME}/config",
            headers={"Content-Type": "application/json"},
            data=json.dumps(connector_config)
        )
        put_response.raise_for_status()
        print(f"Successfully created connector: {json.dumps(put_response.json(), indent=2)}")

except ConnectionError as e:
    print(f"Connection failed: {str(e)}")
    print("Verify Kafka Connect is running on port 8083")
except HTTPError as e:
    if e.response.status_code == 409:
        print(f"Connector {CONNECTOR_NAME} already exists (race condition)")
    else:
        print(f"HTTP Error: {str(e)}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")
