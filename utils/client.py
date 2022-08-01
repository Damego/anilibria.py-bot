from interactions import Client

from .database import DataBaseClient

__all__ = ["AniClient"]


class AniClient(Client):
    def __init__(self, token: str, mongo_url: str, **kwargs):
        super().__init__(token, **kwargs)

        self.database = DataBaseClient(mongo_url)
