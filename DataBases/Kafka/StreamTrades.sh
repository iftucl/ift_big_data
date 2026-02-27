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
