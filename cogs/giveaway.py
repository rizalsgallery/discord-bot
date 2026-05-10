import time
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random

GIVEAWAY_ROLE_ID = 1499834061815025734

class GiveawayView(discord.ui.View):
    def __init__(self, invites_required):
        super().__init__(timeout=None)
        self.entries = []
        self.invites_required = invites_required

    @discord.ui.button(label="Join Giveaway", style=discord.ButtonStyle.green)
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):

        invites = await interaction.guild.invites()

        total_invites = 0

        for invite in invites:
            if invite.inviter == interaction.user:
                total_invites += invite.uses

        if total_invites < self.invites_required:
            await interaction.response.send_message(
                f"❌ You need {self.invites_required} invites to join.",
                ephemeral=True
            )
            return

        if interaction.user.id in self.entries:
            await interaction.response.send_message(
                "❌ You already joined.",
                ephemeral=True
            )
            return

        self.entries.append(interaction.user.id)

        await interaction.response.send_message(
            "✅ You joined the giveaway.",
            ephemeral=True
        )

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="giveaway", description="Create a giveaway")
    @app_commands.describe(
        prize="Prize",
        sponsor="Sponsor",
        winners="Amount of winners",
        duration="Duration",
        invites="Required invites",
        image="Image URL",
        extra="Extra requirement"
    )
    async def giveaway(
        self,
        interaction: discord.Interaction,
        prize: str,
        sponsor: discord.Member,
        winners: int,
        duration: str,
        invites: int,
        image: str,
        extra: str
    ):

        role = interaction.guild.get_role(GIVEAWAY_ROLE_ID)

        view = GiveawayView(invites)

        embed = discord.Embed(
            title="🎉 Giveaway",
            color=discord.Color.blurple()
        )

        embed.add_field(name="Prize", value=prize, inline=False)
        embed.add_field(name="Sponsor", value=sponsor.mention, inline=False)
        embed.add_field(name="Winners", value=str(winners), inline=False)
        time_amount = int(duration[:-1])

        if duration.endswith("m"):
            end_time = int(time.time()) + (time_amount * 60)

        elif duration.endswith("h"):
            end_time = int(time.time()) + (time_amount * 3600)

        embed.add_field(
        name="Ends",
        value=f"<t:{end_time}:R>",
        inline=False
    )
        embed.add_field(
            name="Invite Requirement",
            value=f"{invites} Invites",
            inline=False
        )
        
        embed.add_field(
            name="Extra Requirement",
            value=value=extra,
            inline=False
        )
        

        embed.set_image(url=image)

        await interaction.response.send_message(
            content=role.mention if role else None,
            embed=embed,
            view=view
        )

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
