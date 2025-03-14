"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2022-11-19
Topic   : mongo_db.py
Project : MongoDB Trades aggregator
Desc    : Class to aggregate data from MongoDB


"""
from pymongo import MongoClient
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import date
import os


class GetMongoClient:
    """
    Handles MongoDB connectivity.

    :param url: MongoDB connection URL.
    :type url: str
    :param database: Name of the MongoDB database.
    :type database: str
    :param collection: Name of the MongoDB collection.
    :type collection: str
    """

    def __init__(self, url: Optional[str] = None, database: Optional[str] = None, collection: Optional[str] = None):
        self.mongo_url = url or os.getenv("MONGO_URL")
        self.mongo_database = database or os.getenv("MONGO_DATABASE")
        self.mongo_collection = collection or os.getenv("MONGO_COLLECTION")

        if not all([self.mongo_url, self.mongo_database, self.mongo_collection]):
            raise ValueError("Missing required MongoDB configuration.")

    def _init_mongo_client(self):
        """
        Initialize and return a MongoDB collection object.

        :return: A MongoDB collection object.
        :rtype: pymongo.collection.Collection
        """
        client = MongoClient(self.mongo_url)
        db = client[self.mongo_database]
        return db[self.mongo_collection]

    @property
    def client(self):
        """
        Property to get the MongoDB collection object.

        :return: A MongoDB collection object.
        :rtype: pymongo.collection.Collection
        """
        return self._init_mongo_client()


class BaseQuery(ABC):
    """
    Abstract base class defining the interface for querying a database.

    Subclasses must implement the following methods:
      - find_by_date
      - find_by_field
      - aggregate_data
    """

    @abstractmethod
    def find_by_date(self, business_date: date) -> List[Dict[str, Any]]:
        """
        Find records by a specific date.

        :param business_date: The date to search for.
        :type business_date: date
        :return: List of records matching the date.
        :rtype: List[Dict[str, Any]]
        """
        pass

    @abstractmethod
    def find_by_field(self, field: str, value: Any) -> List[Dict[str, Any]]:
        """
        Find records by a specific field and value.

        :param field: The field to search in.
        :type field: str
        :param value: The value to search for.
        :type value: Any
        :return: List of records matching the criteria.
        :rtype: List[Dict[str, Any]]
        """
        pass

    @abstractmethod
    def aggregate_data(self, business_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Aggregate data based on specific criteria.

        :param business_date: The date to aggregate data for. If None, aggregates all data.
        :type business_date: Optional[date]
        :return: Aggregated data.
        :rtype: List[Dict[str, Any]]
        """
        pass


class TradeQuery(GetMongoClient, BaseQuery):
    """
    Query class for trade data. Inherits connectivity from GetMongo and implements query methods from BaseQuery.

    :param url: MongoDB connection URL.
    :type url: str
    :param database: Name of the MongoDB database.
    :type database: str
    :param collection: Name of the MongoDB collection.
    :type collection: str
    """

    def find_by_date(self, business_date: date) -> List[Dict[str, Any]]:
        """
        Find trades by a specific date.

        :param business_date: The date to search for.
        :type business_date: date
        :return: List of trades matching the date.
        :rtype: List[Dict[str, Any]]
        """
        return list(self.client.find({"date": business_date}))

    def find_by_field(self, field: str, value: Any) -> List[Dict[str, Any]]:
        """
        Find trades by a specific field and value.

        :param field: The field to search in.
        :type field: str
        :param value: The value to search for.
        :type value: Any
        :return: List of trades matching the criteria.
        :rtype: List[Dict[str, Any]]
        """
        return list(self.client.find({field: value}))
