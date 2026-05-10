import discord
from discord.ext import commands
from discord import app_commands
import random

class GiveawayView(discord.ui.View):
    def __init__(self, prize):
        super().__init__(timeout=None)
        self.prize = prize
        self.entries = []

    @discord.ui.button(label="Join Giveaway", style=discord.ButtonStyle.green)
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):

        invites = await interaction.guild.invites()

        total_invites = 0

        for invite in invites:
            if invite.inviter == interaction.user:
                total_invites += invite.uses

        if total_invites < 1:
            await interaction.response.send_message(
                "❌ You need at least 1 invite to join this giveaway.",
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
        prize="Prize of the giveaway",
        duration="Duration in minutes"
    )
    async def giveaway(
        self,
        interaction: discord.Interaction,
        prize: str,
        duration: int
    ):

        view = GiveawayView(prize)

        embed = discord.Embed(
            title="🎉 Giveaway",
            description=f"Prize: **{prize}**\nRequirement: **1 Invite**",
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
