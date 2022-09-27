import asyncio
from os import getenv

import anilibria
import interactions
from dotenv import load_dotenv

from utils.client import AniClient
from utils import (
    render_components,
    render_embed,
    render_notification_message,
    render_select_title,
)

load_dotenv()

bot = AniClient(getenv("TOKEN"), getenv("MONGO_URL"))
client = anilibria.AniLibriaClient()


@bot.event
async def on_start():
    await bot.change_presence(
        interactions.ClientPresence(
            status=interactions.StatusType.DND,
            activities=[
                interactions.PresenceActivity(
                    name="аниме", type=interactions.PresenceActivityType.WATCHING
                )
            ],
        )
    )
    await bot.database.get_guilds()

    await asyncio.sleep(5)
    for guild in bot.guilds:
        if int(guild.id) not in [guild_data.id for guild_data in bot.database.guilds]:
            await bot.database.add_guild(int(guild.id))


@client.event
async def on_connect():
    print("Connected to anilibria API")


@client.event
async def on_title_serie(event: anilibria.TitleSerieEvent):
    to_send = render_notification_message(event)
    for guild in bot.database.guilds:
        channel = await get_channel(guild.channel_id)
        if channel is None:
            continue

        if event.title.id in guild.subscriptions or not guild.subscriptions:
            await channel.send(**to_send)


async def get_channel(channel_id: int | None) -> interactions.Channel | None:
    if channel_id is None:
        return
    return await interactions.get(bot, interactions.Channel, object_id=channel_id)


@bot.event
async def on_ready():
    print("Anilibria bot ready")


@bot.command(name="anilibria", description="Command for other commands")
async def _anilibria(ctx: interactions.CommandContext):
    await ctx.defer()
    ...


@_anilibria.subcommand(name="random", description="Показывает рандомный тайтл")
async def random_title(ctx: interactions.CommandContext):
    title = await client.get_random_title()
    embed = render_embed(ctx, title)
    components = render_components(title, False)
    await ctx.send(embeds=embed, components=components)


@_anilibria.subcommand(name="search", description="Ищет аниме")
@interactions.option(
    option_type=interactions.OptionType.STRING,
    name="query",
    description="Название аниме",
    required=True,
)
async def search_title(ctx: interactions.CommandContext, query: str):
    titles = await client.search_titles(search=[query])
    if not titles:
        return await ctx.send(f"По запросу `{query}` ничего не найдено!")

    if len(titles) == 1:
        title = titles[0]
        embed = render_embed(ctx, title)
        guild_data = bot.database.get_guild(int(ctx.guild_id))
        components = render_components(title, subscribe=title.id not in guild_data.subscriptions)
        await ctx.send(embeds=embed, components=components)
        return

    components = render_select_title(titles)
    await ctx.send(
        f"Найдено `{len(titles)}` тайтла(ов), удовлетворяющие вашему запросу.\nВыберите один их них для продолжения.",
        components=components,
    )


@bot.component("select_title")
async def select_title(ctx: interactions.ComponentContext, title_id: str):
    await ctx.defer(edit_origin=True)
    title = await client.get_title(id=title_id)
    embed = render_embed(ctx, title)
    guild_data = bot.database.get_guild(int(ctx.guild_id))
    components = render_components(title, subscribe=title.id not in guild_data.subscriptions)
    await ctx.edit(content=None, embeds=embed, components=components)


@_anilibria.subcommand(
    name="set-notification-channel", description="Устанавливает канал для уведомлений"
)
@interactions.option(
    option_type=interactions.OptionType.CHANNEL,
    name="channel",
    description="Канал для уведомлений",
    required=True,
    channel_types=[interactions.ChannelType.GUILD_TEXT],
)
async def set_notification_channel(ctx: interactions.CommandContext, channel: interactions.Channel):
    if not has_admin_perm(ctx):
        return await ctx.send("У вас недостаточно прав", ephemeral=True)
    try:
        message = await channel.send(
            "Проверка доступа к каналу. Сообщение удалится через 5 секунд."
        )
    except interactions.LibraryException:
        return await ctx.send(f"Нет доступа к каналу {channel.mention}")

    async def remove_message(message: interactions.Message):
        await asyncio.sleep(5)
        await message.delete()

    loop = asyncio.get_event_loop()
    loop.create_task(remove_message(message))

    await bot.database.set_channel(int(ctx.guild_id), int(channel.id))
    await ctx.send("Канал для уведомлений установлен!")


async def subscribe_on_title(ctx: interactions.ComponentContext, title_id: str | int):
    await bot.database.add_subscription(int(ctx.guild_id), int(title_id))

    message = ctx.message
    await ctx.send("Вы успешно подписались", ephemeral=True)
    components = message.components
    components[0].components[-1].disabled = True
    await message.edit(components=components)


async def unsubscribe_on_title(ctx: interactions.ComponentContext, title_id: str | int):
    await bot.database.remove_subscription(int(ctx.guild_id), int(title_id))

    message = ctx.message
    await ctx.send("Вы успешно отписались", ephemeral=True)
    components = message.components
    components[0].components[-1].disabled = True
    await message.edit(components=components)


@bot.event
async def on_component(ctx: interactions.ComponentContext):
    if not has_admin_perm(ctx):
        return await ctx.send("У вас недостаточно прав", ephemeral=True)
    try:
        custom_id, title_id = ctx.custom_id.split("|")
    except ValueError:
        return

    match custom_id:
        case "subscribe":
            await subscribe_on_title(ctx, title_id)
        case "unsubscribe":
            await unsubscribe_on_title(ctx, title_id)


def has_admin_perm(ctx: interactions.ComponentContext | interactions.CommandContext):
    return (
        ctx.author.permissions & interactions.Permissions.ADMINISTRATOR.value
        == interactions.Permissions.ADMINISTRATOR.value
    )


client.startwith(bot._ready())
