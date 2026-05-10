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
    duration="Duration in minutes",
    invites="Required invites",
    image="Image URL",
    role="Role to ping",
    requirement="Extra requirement"
)
async def giveaway(
    self,
    interaction: discord.Interaction,
    prize: str,
    duration: int,
    invites: int,
    image: str,
    role: discord.Role,
    requirement: str
):

    class GiveawayView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.entries = []

        @discord.ui.button(label="Join Giveaway", style=discord.ButtonStyle.green)
        async def join_giveaway(self, interaction2: discord.Interaction, button: discord.ui.Button):

            guild_invites = await interaction2.guild.invites()

            total_invites = 0

            for invite in guild_invites:
                if invite.inviter == interaction2.user:
                    total_invites += invite.uses

            if total_invites < invites:
                await interaction2.response.send_message(
                    f"❌ You need {invites} invites to join.",
                    ephemeral=True
                )
                return

            if interaction2.user.id in self.entries:
                await interaction2.response.send_message(
                    "❌ You already joined.",
                    ephemeral=True
                )
                return

            self.entries.append(interaction2.user.id)

            await interaction2.response.send_message(
                "✅ You joined the giveaway.",
                ephemeral=True
            )

    embed = discord.Embed(
        title="🎉 Giveaway",
        color=discord.Color.blurple()
    )

    embed.add_field(name="Prize", value=prize, inline=False)
    embed.add_field(name="Requirements", value=f"{invites} Invites\n{requirement}", inline=False)
    embed.add_field(name="Duration", value=f"{duration} Minutes", inline=False)

    embed.set_image(url=image)

    await interaction.response.send_message(
        content=role.mention,
        embed=embed,
        view=GiveawayView()
    )
