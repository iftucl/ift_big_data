//-----------------------------------------------------------------------------------------------------------------------------------------------------------------
// UCL -- Institute of Finance & Technology
// Author  : Luca Cocconcelli
// Lecture : 2024-02-15
// Topic   : NoSQL DataBase - MongoDB
//-----------------------------------------------------------------------------------------------------------------------------------------------------------------


// 0. Housekeeping
// 0.1 to launch MongoDB on Windows:
// "C:\Program Files\MongoDB\Server\3.6\bin\mongod.exe"

// 0.2 to launch on iOS
// $ brew services start mongodb-community
// $ mongo


// 1. General:
cls // cleans the view;
help // returns a list of main commands in MongoDb;
exit // quit MongoDb native shell;
db.version() // returns which mongoDb version is installed;


// 2. Using DBs:
db // show in which active database we are working;
show dbs // show all active databases in MongoDb;
use EquitySP500 // switches to another db - also creates a new db (which will be displayed only when a new collection will be created within the new db);
db.dropDatabase() // deletes the current database; FYI when the last collection is deleted within a db also the db gets automatically deleted.


// 3. Create and Delete Collections:
show collections // shows all the collections available within the active database I am positioned;
db.createCollection("Static") // creates a new collection within the active db;
db.get("Static").drop() // deletes a collection within the current db;
db.Static.drop() // deletes a collection within the current db (same as above);


// 4. Documents:
// 4.1 insert
// db.Static.insert(<object> or <array of objects>) 
// this method insert objects or array of objects. It means that you can insert either one document or a list of documents;

// 4.2 insertOne
// db.Static.insertOne(<object>) 
// insert one document into a collection;
db.Static.insertOne({"Name": "Apple", "Ticker": "AAPL", "Sector":"InfoTech"}) // Example to insert one entry in the Static collection

// 4.3 insertMany
// db.Static.insertMany(<array of objects>)
// insert a set of documents into a collection;
db.Static.insertMany([{"Name": "Bloomberg", "Ticker": "BBG", "Sector":"Financials"},
					 {"Name": "Bank of America", "Ticker": "BAML", "Sector":"Banks"}]) // Example to insert multiple entries in the Static collection

// 4.4 remove
db.Static.remove({}) // deletes all documents within a collection


// 5. Read Documents:
// 5.1 findOne vs find methods
// db.Static.findOne(<query>, <fields>) 
// returns the document in a collection. Returns the Extended JSON Object. If no arguments are passed to to the function, it will return the first entry;
db.Static.findOne({Symbol: "AES"}, {Security: 1, GICSSector: 1})
// 5.2 find many documents
// db.Static.find(<query>, <fields>)
// list all documents in a collection. Returns cursor and cursor must be iterated to get documents in Extended JSON Format;
db.Static.find({GICSSector: "Financials"}, {Security: 1})
db.Static.find({GICSSector: "Financials"}, {Security: 1}).limit(5)
db.Static.find({GICSSector: "Financials"}).limit(5).pretty()

// Using Nested Documents
db.NestedStatic.find({"StaticData.GICSSector": "Financials"}).limit(5).pretty()

// 5.2 distinct method
db.Static.distinct("GICSSector")
db.NestedStatic.distinct("StaticData.GICSSector")

// 5.3 MongoDB and JavaScript
var colNames = db.Static.findOne() //we can leverage on JS as this is the native core of MongoDB
for (var col in colNames) {
	print(col);
}

// 6. Cursor
// 6.1 Cursor Method for Read Ops. It assigns the cursor to a variable, before performing any operation you need to assign the cursor to a variable:
// var cursor = db.<name_collection>.find(<args>);
var myFirstCursor = db.Static.find();

cursor.next() // Iterate one document; with this you can iterate one by one through the cursor:
cursor.hasNext() // Check if the cursors has a document next:
cursor.objsLeftInBatch() // And finally you can also check how many object are left into the current batch:
cursor.forEach(printjson) //And we can print each element in a cursor by using the forEach function and pass the function “printjson” as an argument, like this:
// or in JS style:
while ( myFirstCursor.hasNext() ) {
   printjson( myFirstCursor.next() );
}


var multipleDocs = db.Static.find().limit(5)
multipleDocs.forEach(
        function (doc) {
            print(`${doc.Symbol} is a ${doc.GICSSector} company.`);
        }
);


// 7. MongoDB Query:
// 7.1 Find Method
db.Static.findOne() // Find first document in a collection
db.Static.find() // Find all documents in a Collections
db.Static.find().limit(10) // Find all documents in a Collections but returns only 10
db.Static.find().limit(10).skip(5) // and skips the first 5
db.Static.find().limit(10).skip(5).sort({DividendYield:-1}) // and sorts by dividend yield
db.Static.find({PERatio: null}, {Symbol: 1}).limit(10) // finds all the PERatio values that are null

// 7.2 Find with conditions $eq, $ne, $gt, $lt, $gte, $lte
db.Static.find({GICSSector: {"$eq": "Utilities"}}) // find all stocks in Sector Utilities
db.Static.find({GICSSector: {"$ne": "Financials"}}) // find all stocks in Sector that are not Financials
db.Static.find({Beta: {"$lt": 1}}) // CounterCyclical Stocks only are kept!
db.Static.find({PERatio: {"$gt": 10, "$lte": 15 }}) // Find all equities with PE Ratio between 10 and 15
db.Static.find({PERatio: {"$gt": 10, "$lte": 15 }}).count() // Count all equities with PE Ratio between 10 and 15
db.Static.find({GICSSubIndustry: {"$gt": "P"}}) // all SubSectors with initial starting with N;
db.Static.find({GICSSubIndustry: {"$gt": "P"}}).sort({Symbol: 1}) // can check the outcome by running this query 

// 7.3 IN operator
db.Static.find({GICSSector: { "$in": [ "Financials", "Utilities" ] } }) // where $in stands for in the list;
db.Static.find({GICSSector: { "$nin": [ "Health Care", "Consumer Discretionary" ] } }) // where $in stands for NOT in the list.


// 7.3 AND / OR operators
db.Static.find({$and: [{ PERatio: {"$gte": 25} }, {GICSSector: {"$eq": "Financials" } } ] } )
db.Static.find({PERatio: {"$gte": 25}, GICSSector: {"$ne": "Financials" }}) // With different fields we can use the implicit and operator such as:

db.Static.find({$or: [{ PERatio: {"$gte": 25} }, {GICSSector: {"$eq": "Financials" } } ] } )

db.Static.find({$and: [{ PERatio: {"$gte": 15}}, {PERatio: {"$ne": 20 } } ] }) //But with the same field, the implicit and operator will be overwritten by the last condition.
// WHICH IS DIFFERENT FROM:
db.Static.find({ PERatio: {"$gte": 15}, PERatio: {"$ne": 45 } })

// 8. Filtering fields
db.Static.find({}, {Symbol: 1, Security: 1}).pretty()
db.Static.find({GICSSector: {"$eq": "Utilities"}}, {Symbol: 1, Security: 1, GICSSector: 1})
db.Static.find({PERatio: {"$gt": 10, "$lte": 15 }}, {GICSSector: 0,GICSSubIndustry: 0})

// 9.0 Aggregate Method
// 9.1 Aggregate all Sectors and return the average Beta by Sector
db.Static.aggregate([
	{$match: {} },
	{$group: {_id: "$GICSSector", average: {$avg: "$Beta"} } }])
// 9.2 Aggregate all Sectors and return the average for only these stocks that have a mkt cap gte than 500,000
db.Static.aggregate([
	{$match: {MarketCap: {"$gte": 1500000} } },
	{$group: {_id: "$GICSSector", average: {$avg: "$Beta"} } }])
	
// 9.3 Aggregate all Subsectors within the Financials Sector and return the average by SubSector  
db.Static.aggregate([
	{$match: {GICSSector: "Financials"} },
	{$group: {_id: "$GICSSubIndustry", total: {$avg: "$PERatio"} } }])

db.NestedStatic.aggregate([
	{$match: {"StaticData.GICSSector": "Health Care"} },
	{$group: {_id: "$StaticData.GICSSector", total: {$sum: "$MarketData.MarketCap"} } }])


// 10.0 Remove documents on conditions
db.Static.remove({})
// 10.1 Remove One document given condition
db.Static.remove({PERatio: {"$gte" : 100, "$lte" : 150}}, {justOne: true})
// 10.2 Remove all documents given conditions
db.Static.remove({PERatio: {"$gte" : 100, "$lte" : 150}})