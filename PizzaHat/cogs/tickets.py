import chat_exporter
import discord
from async_lru import alru_cache
from core.bot import PizzaHat
from core.cog import Cog
from discord import ButtonStyle, Interaction, ui
from discord.ext import commands
from discord.ext.commands import Context


class TicketView(ui.View):
    def __init__(self, bot):
        self.bot = bot
        self.thread_id = None
        super().__init__(timeout=None)

    @ui.button(emoji="<:P_ticket:1220678462839197756>", custom_id="create_ticket_btn")
    @commands.bot_has_permissions(create_private_threads=True)
    async def create_ticket(self, interaction: Interaction, button: ui.Button):
        if not interaction.guild:
            return

        thread = await interaction.channel.create_thread(  # type: ignore
            name=f"ticket-{interaction.user}",
            reason=f"Ticket created by {interaction.user}",
            invitable=False,  # type: ignore
        )
        await thread.add_user(interaction.user)

        em = discord.Embed(
            title="Ticket created!",
            description=f"Welcome {interaction.user.mention} `[{interaction.user}]`. Support team will get back to you shortly.",
            color=self.bot.color,
            timestamp=interaction.created_at,
        )
        em.set_footer(
            text=interaction.user,
            icon_url=(interaction.user.avatar.url if interaction.user.avatar else None),
        )

        await thread.send(
            content=f"{interaction.user.mention}",
            embed=em,
            view=TicketSettings(thread.id),
        )
        self.thread_id = thread.id


class TicketSettings(ui.View):
    def __init__(self, thread_id: int):
        self.thread_id = thread_id
        super().__init__(timeout=None)

    @ui.button(
        label="Close Ticket",
        emoji="🔐",
        style=ButtonStyle.red,
        custom_id="close_ticket_btn",
    )
    async def close_ticket(self, interaction: Interaction, button: ui.Button):
        if interaction.guild is not None:
            thread = interaction.guild.get_thread(self.thread_id)

            if thread:
                await interaction.response.send_message(
                    content="Ticket thread has been archived!"
                )
                await thread.edit(archived=True, locked=True)
            else:
                await interaction.followup.send(content="Unable to find ticket thread!")

    @ui.button(
        label="Transcript",
        emoji="📝",
        style=ButtonStyle.blurple,
        custom_id="ticket_transcript_btn",
    )
    async def ticket_transcript(self, interaction: Interaction, button: ui.Button):
        if interaction.guild is not None:
            thread = interaction.guild.get_thread(self.thread_id)

            if thread:
                msg = await chat_exporter.quick_export(thread)  # type: ignore
                await chat_exporter.quick_link(thread, msg)
            else:
                await interaction.followup.send(
                    content="Unable to generate transcript for this ticket."
                )


class Tickets(Cog, emoji=1220678462839197756):
    """Button ticket system for support and help!"""

    def __init__(self, bot: PizzaHat):
        self.bot: PizzaHat = bot

    @commands.command(aliases=["tickets"])
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def ticket(self, ctx: Context, channel: discord.TextChannel):
        """
        Set up the Ticket system in the server by sending the `Create Ticket` message.

        In order for this to work, the bot must have Manage Server permissions.

        To use this command, you must have Manage Server permission.
        """

        em = discord.Embed(
            title="Create a ticket!",
            description="Click <:P_ticket:1220678462839197756> to create/open a new ticket.",
            color=discord.Color.gold(),
        )
        em.set_thumbnail(url="https://i.imgur.com/mOTlTBy.png")

        view = TicketView(self.bot)
        await channel.send(embed=em, view=view)
        await ctx.message.add_reaction(self.bot.yes)


async def setup(bot):
    await bot.add_cog(Tickets(bot))
