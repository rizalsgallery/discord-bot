import discord
from discord.ext import commands
from discord import app_commands

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

        embed = discord.Embed(
            title="🎉 Giveaway",
            color=discord.Color.blurple()
        )

        embed.add_field(name="Prize", value=prize, inline=False)
        embed.add_field(
            name="Requirements",
            value=f"{invites} Invites\n{requirement}",
            inline=False
        )

        embed.add_field(
            name="Duration",
            value=f"{duration} Minutes",
            inline=False
        )

        embed.set_image(url=image)

        await interaction.response.send_message(
            content=role.mention,
            embed=embed,
            view=GiveawayView(invites)
        )

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
