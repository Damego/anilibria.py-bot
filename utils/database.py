from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

from .models import GuildData

__all__ = ["DataBaseClient"]


class DataBaseClient:
    def __init__(self, url: str):
        self._client: MongoClient | AsyncIOMotorClient = AsyncIOMotorClient(url)
        self.collection = self._client["ANILIBRIA_BOT"]["GUILDS"]
        self.global_coll = self._client["GLOBAL"]["OTHER"]
        self.guilds: list[GuildData] = []

    async def get_guilds(self) -> list[GuildData]:
        guilds_cursor = self.collection.find()
        guilds = []
        async for guild_data in guilds_cursor:
            guild_data["id"] = guild_data.pop("_id")
            guilds.append(GuildData(**guild_data))
        self.guilds = guilds
        return guilds

    def get_guild(self, guild_id: int) -> GuildData:
        for guild in self.guilds:
            if guild.id == guild_id:
                return guild

    async def add_guild(self, guild_id: int):
        await self.collection.insert_one(
            {"_id": guild_id, "subscriptions": [], "channel_id": None}
        )
        guild = GuildData(id=guild_id, subscriptions=[], channel_id=None)
        self.guilds.append(guild)
        return guild

    async def remove_guild(self, guild_id: int):
        await self.collection.delete_one({"_id": guild_id})

        for guild in self.guilds:
            if guild.id == guild_id:
                self.guilds.remove(guild)
                break

    async def add_subscription(self, guild_id: int, title_id: int):
        await self.collection.update_one(
            {"_id": guild_id}, {"$push": {"subscriptions": title_id}}, upsert=True
        )

        for guild in self.guilds:
            if guild.id == guild_id:
                guild.subscriptions.append(title_id)
                break

    async def remove_subscription(self, guild_id: int, title_id: int):
        await self.collection.update_one(
            {"_id": guild_id}, {"$pull": {"subscriptions": title_id}}, upsert=True
        )

        for guild in self.guilds:
            if guild.id == guild_id:
                guild.subscriptions.remove(title_id)
                break

    async def set_channel(self, guild_id: int, channel_id: int):
        await self.collection.update_one(
            {"_id": guild_id}, {"$set": {"channel_id": channel_id}}, upsert=True
        )

        for guild in self.guilds:
            if guild.id == guild_id:
                guild.channel_id = channel_id
                break
