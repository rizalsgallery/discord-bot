import discord
from discord.ext import commands
from discord import app_commands


# ----------------------------------------------------
# CONFIG — SET YOUR ROLE ID HERE
# ----------------------------------------------------
ALLOWED_ROLE_ID = 1499865433744998480  # CHANGE THIS TO YOUR STAFF ROLE ID


# ----------------------------------------------------
# MAIN COG
# ----------------------------------------------------
class ProcessVouchG1AC(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------------------------
    # PERMISSION CHECK
    # ---------------------------
    def has_permission(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(ALLOWED_ROLE_ID)
        return role in interaction.user.roles

    # ---------------------------
    # /process COMMAND
    # ---------------------------
    @app_commands.command(name="process", description="Send the PROCESS embed")
    async def process_cmd(self, interaction: discord.Interaction):

        if not self.has_permission(interaction):
            return await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True
            )

        # ---------------------------
        # EDIT THIS EMBED
        # ---------------------------
        embed = discord.Embed(
            title="📦 Process Started",
            description="Paste your PROCESS embed text here.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Sent by {interaction.user}")

        await interaction.response.send_message(embed=embed)

    # ---------------------------
    # /vouch COMMAND
    # ---------------------------
    @app_commands.command(name="vouch", description="Send the VOUCH embed")
    async def vouch_cmd(self, interaction: discord.Interaction):

        if not self.has_permission(interaction):
            return await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True
            )

        # ---------------------------
        # EDIT THIS EMBED
        # ---------------------------
        embed = discord.Embed(
            title="⭐ Vouch System",
            description="Thanks for using me as a MM for this trade. Please type following in ⁠Kick a Lucky Block⁠💬・chat and ⁠✅・vouches:",
            color=discord.Color.gold()
        )
        embed.set_footer(text="@(user) MM Vouch (Highly recomended)")

        await interaction.response.send_message(embed=embed)

    # ---------------------------
    # /g1ac COMMAND
    # ---------------------------
    @app_commands.command(name="g1ac", description="Send the G1AC embed")
    async def g1ac_cmd(self, interaction: discord.Interaction):

        if not self.has_permission(interaction):
            return await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True
            )

        # ---------------------------
        # EDIT THIS EMBED
        # ---------------------------
        embed = discord.Embed(
            title="🛡️ Private Server Link",
            description="Server link: https://www.roblox.com/share?code=aefe990e9c607a4995d9c15a321c3f2a&type=Server",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Sent by {interaction.user}")

        await interaction.response.send_message(embed=embed)


# ----------------------------------------------------
# SETUP
# ----------------------------------------------------
async def setup(bot):
    await bot.add_cog(ProcessVouchG1AC(bot))
