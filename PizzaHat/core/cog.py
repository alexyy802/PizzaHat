from io import BytesIO

import emoji
import requests
from colorthief import ColorThief
from discord import Color, PartialEmoji
from discord.ext.commands import Cog as DiscordCog
from discord.ext.commands import CogMeta as DiscordCogMeta
from PIL import Image


class CogMeta(DiscordCogMeta):
    """Metaclass used for passing an emoji parameter to a Cog object."""

    def __new__(mcs, *args, **kwargs):
        name, bases, attrs = args
        attrs["__cog_emoji__"] = kwargs.pop("emoji", None)

        mcs.instance = super().__new__(mcs, name, bases, attrs, **kwargs)
        return mcs.instance


class Cog(DiscordCog, metaclass=CogMeta):
    """
    Base class for all cogs that contains an emoji passed either by id
    or the raw name.

    Example usage: `class MyCog(Cog, emoji='❓')`
    """

    @property
    def emoji(self):
        if not hasattr(self, "__cog_emoji__"):
            return None

        e = self.__cog_emoji__  # type: ignore

        if isinstance(e, int):
            guild_emoji = self.bot.get_emoji(e)  # type: ignore
            return (
                PartialEmoji(
                    name=guild_emoji.name,
                    id=guild_emoji.id,
                    animated=guild_emoji.animated,
                )
                if guild_emoji
                else None
            )

        elif isinstance(e, str):
            if e.startswith("<") and e.endswith(">"):
                animated = e.startswith("<a:")
                name, emoji_id = e.rsplit(":", 1)
                name = name.split(":")[-1]
                return PartialEmoji(name=name, id=int(emoji_id[:-1]), animated=animated)
            else:
                return PartialEmoji(name=e)

        elif isinstance(e, PartialEmoji):
            return e

        else:
            return None

    @property
    def full_description(self):
        """The cog's emoji with the cog's description."""
        return (str((self.emoji or "")) + " " + self.description).strip()

    def _get_dominant_color_from_emoji(self):
        """Get the dominant color from the emoji."""
        if self.emoji:
            emoji_str = str(self.emoji)

            if emoji.is_emoji(emoji_str):
                try:
                    # For Unicode emojis, render emoji to PNG
                    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
                    img.paste(emoji.emojize(emoji_str))

                    # Convert to RGB
                    img = img.convert("RGB")

                    # Save to BytesIO object
                    img_byte_arr = BytesIO()
                    img.save(img_byte_arr, format="PNG")
                    img_byte_arr.seek(0)

                    # Get dominant color
                    color_thief = ColorThief(img_byte_arr)
                    dominant_color = color_thief.get_color(quality=1)

                    return Color.from_rgb(*dominant_color)
                except Exception:
                    return 0x456DD4
            else:
                try:
                    # For custom Discord emojis, fetch emoji image
                    emoji_url = str(self.emoji.url)
                    response = requests.get(emoji_url)
                    img = Image.open(BytesIO(response.content))

                    # Convert to RGB
                    img = img.convert("RGB")

                    # Save to BytesIO object
                    img_byte_arr = BytesIO()
                    img.save(img_byte_arr, format="PNG")
                    img_byte_arr.seek(0)

                    # Get dominant color
                    color_thief = ColorThief(img_byte_arr)
                    dominant_color = color_thief.get_color(quality=1)

                    return Color.from_rgb(*dominant_color)
                except Exception:
                    return 0x456DD4

        return 0x456DD4

    @property
    def color(self):
        """Get a color generated from the emoji, or a default color if not available."""
        return self._get_dominant_color_from_emoji()
