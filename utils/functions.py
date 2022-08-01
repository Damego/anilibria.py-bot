from interactions import (
    Button,
    ButtonStyle,
    CommandContext,
    Embed,
    Color,
    SelectMenu,
    SelectOption,
)
from anilibria import TitleSerieEvent, Title

__all__ = [
    "render_components",
    "render_select_title",
    "render_embed",
    "render_notification_message",
]


def render_components(
    title: Title, show_subscribe_button: bool = True, subscribe: bool = True
) -> list[Button]:
    components = [Button(label="Смотреть", style=ButtonStyle.LINK, url=title.url)]
    if show_subscribe_button:
        components.append(
            Button(
                label="Подписаться",
                style=ButtonStyle.PRIMARY,
                custom_id=f"subscribe|{title.id}",
            )
            if subscribe
            else Button(
                label="Отписаться",
                style=ButtonStyle.DANGER,
                custom_id=f"unsubscribe|{title.id}",
            )
        )
    return components


def render_select_title(titles: list[Title]) -> list[SelectMenu]:
    components = [
        SelectMenu(
            placeholder="Выберите тайтл",
            options=[
                SelectOption(label=title.names.ru[:100], value=str(title.id))
                for title in titles
            ],
            custom_id="select_title",
        )
    ]
    return components


def render_embed(ctx: CommandContext, title: Title) -> Embed:
    embed = Embed(
        title=title.names.ru, description=title.description, color=Color.blurple()
    )
    embed.add_field(
        name="Информация",
        value=f"**Сезон:** `{title.season.year}, {title.season.string}`\n"
        f"**Тип:** `{title.type.full_string}`\n"
        f"**Текущее количество серий:** `{title.player.series.last}`\n"
        f"**Жанры:** `{', '.join(title.genres)}`",
    )
    if title.announce:
        embed.add_field(name="Дополнительная информация", value=title.announce)
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.user.avatar_url)
    embed.set_image(url=title.posters.small.full_url)

    return embed


def render_notification_message(event: TitleSerieEvent):
    title = event.title
    embed = Embed(title=title.names.ru, color=Color.blurple())
    embed.set_image(url=title.posters.small.full_url)
    embed.set_author(name="Новая серия!")
    embed.set_footer(text=f"Серия: {event.episode.serie}")

    components = render_components(title, False)
    return {"embeds": embed, "components": components}
