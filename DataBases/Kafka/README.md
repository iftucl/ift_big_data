# Kafka Connect

Kafka connect is a data integration component of Kafka: by means of data connector streams data from kafka to other data platforms (and viceversa).

In this use case, we use Kafka Connect to sink new trades submitted to Kafka (via the API end point fast trades) into MongoDB.



## Docker setup

a service called `kafkaconnect` is added to the docker-compose file.
This container named `connect` is built via the image stored in ./Scripts/Python/6.Lecture_20240321/Dockerfile.

The docker file builds the container from the image of kafka connect provided by Confluent and also adds the jar needed to sink kafka topics into MongoDB collections.

## Configure sink Topic to MongoDB


in kafka connect, you can start a sink from kafka topic into mongodb by submitting a post request to the kafka connect api

```
curl -X POST -H "Content-Type: application/json" -d '{"name":"test-stream-trades",
 "config":{"topics":"fast_trades",
 "connector.class":"com.mongodb.kafka.connect.MongoSinkConnector",
 "tasks.max":"1",
 "connection.uri":"mongodb://mongo_db:27017",
 "database":"Trades",
 "collection":"FastTrades",
 "key.converter":"org.apache.kafka.connect.storage.StringConverter",
 "value.converter":"org.apache.kafka.connect.storage.StringConverter",
 "key.converter.schemas.enable":"false",
 "value.converter.schemas.enable":"false",
 "value.projection.list":"tokenNumber",
 "value.projection.type":"whitelist"
}}' localhost:8083/connectors

```

To check a job has been created, you can perform the following get request

```

curl localhost:8083/connectors/test-stream-trades --request GET

```
to stop a sink worker you can perform the following:

```
curl localhost:8083/connectors/test-stream-trades --request DELETE

```


to update the config you can do following:

curl -X PUT -H "Content-Type: application/json" -d '{"topics":"fast_trades",
 "connector.class":"com.mongodb.kafka.connect.MongoSinkConnector",
 "connection.uri":"mongodb://mongo_db:27017",
 "database":"Trades",
 "collection":"FastTrades",
 "key.converter":"org.apache.kafka.connect.storage.StringConverter",
 "value.converter":"org.apache.kafka.connect.storage.StringConverter",
 "key.converter.schemas.enable":"false",
 "value.converter.schemas.enable":"false",
 "document.id.strategy":"com.mongodb.kafka.connect.sink.processor.id.strategy.BsonOidStrategy",
 "document.id.strategy":"com.mongodb.kafka.connect.sink.processor.id.strategy.PartialValueStrategy",
 "value.projection.list":"tokenNumber",
 "value.projection.type":"whitelist"
}' localhost:8083/connectors/test-stream-trades/config