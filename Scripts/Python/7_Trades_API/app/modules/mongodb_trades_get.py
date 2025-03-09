from typing import Optional, List, Dict, Any
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

    def get_trades(self, offset: Optional[int] = None, limit: Optional[int] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
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
            query["traderid"] = {"$regex": f"^{search}", "$options": "i"}  # Case-insensitive regex for 'traderid'

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

