from anilibria.api.models.attrs_utils import DictSerializer, define

__all__ = ["GuildData"]


@define()
class GuildData(DictSerializer):
    id: int
    subscriptions: list[int]
    channel_id: int
