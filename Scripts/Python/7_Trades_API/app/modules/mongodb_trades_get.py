from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from modules.db_clients.mongodb_client import GetMongoClient

from app.api_models.api_responses.trade_model import Trade

class TradeQuery(GetMongoClient):
    """
    Query class for trade data. Inherits connectivity from GetMongo.

    :param url: MongoDB connection URL.
    :type url: str
    :param database: Name of the MongoDB database.
    :type database: str
    :param collection: Name of the MongoDB collection.
    :type collection: str

    Methods:
        get_trades: Fetch trades with optional offset, limit, and regex search.
    """

    def get_trades(self, offset: Optional[int] = None, limit: Optional[int] = None, search: Optional[str] = None, match: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch trades from a MongoDB collection with optional offset, limit, and regex search.

        :param offset: Number of records to skip (for pagination).
        :type offset: int, optional
        :param limit: Maximum number of records to return.
        :type limit: int, optional
        :param search: Search string to match the beginning of the 'traderid' field.
        :type search: str, optional
        :return: List of matching trades.
        :rtype: List[Dict[str, Any]]
        """
        # Build the query
        query = {}
        if search:
            query["Trader"] = {"$regex": f"^{search}", "$options": "i"}
        if match:
            query["Trader"] = {"$eq": f"{match}"}

        # Create the cursor with the query
        cursor = self.client.find(query)

        # Apply offset if provided
        if offset is not None:
            cursor = cursor.skip(offset)

        # Apply limit if provided
        if limit is not None:
            cursor = cursor.limit(limit)

        # Fetch results as a list
        results = list(cursor)

        if not results:
            return list()
        return [Trade(**x) for x in results]

class TradeInsert(GetMongoClient):
    """
    Insert class for trade data. Inherits connectivity from GetMongo.

    Insert one record to the collection.

    :param url: MongoDB connection URL.
    :type url: str
    :param database: Name of the MongoDB database.
    :type database: str
    :param collection: Name of the MongoDB collection.
    :type collection: str

    Methods:
        get_trades: Fetch trades with optional offset, limit, and regex search.
    """
    def insert_trade(self, data_load: list[BaseModel] | BaseModel) -> List[Dict[str, Any]]:
        """
        Load trade(s) to a MongoDB collection.

        :param load_data: Search string to match the beginning of the 'traderid' field.
        :type load_data: list[BaseModel]
        :return: List of matching trades.
        :rtype: List[Dict[str, Any]]        
        """
        if not data_load:
            return None        
        if isinstance(data_load, list) or isinstance(data_load, tuple):
            response = self.client.insert_many([x.model_dump() for x in data_load])
        elif isinstance(data_load, BaseModel):
            response = self.client.insert_one(data_load.model_dump())
        return response.acknowledged
