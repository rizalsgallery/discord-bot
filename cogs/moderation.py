import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()
MOD_ROLE_ID = 1499865378023538688

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
            
            
            
            
    @app_commands.command(name="timeout", description="Timeout a member for a specified duration")
    @app_commands.describe(
        member="The member to timeout",
        duration="Duration in minutes",
        reason="Reason for timeout"
    )
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration: int,
        reason: str = "No reason provided"
    ):
        await interaction.response.defer()
        """Timeout a member"""
        if not MOD_ROLE_ID or MOD_ROLE_ID == 0:
            await interaction.followup.send("❌ Mod role not configured", ephemeral=True)
            return
            
        if MOD_ROLE_ID not in [role.id for role in interaction.user.roles]:
            print([role.id for role in interaction.user.roles])
            print(MOD_ROLE_ID)
            await interaction.followup.send(
                "❌ You don't have permission to use this command",
                ephemeral=True
            )
            return

        if member == interaction.user:
            await interaction.followup.send("❌ You can't timeout yourself", ephemeral=True)
            return

        if member.top_role >= interaction.user.top_role:
            await interaction.followup.send(
                "❌ You can't timeout someone with equal or higher role",
                ephemeral=True
            )
            return

        try:
            await member.timeout(timedelta(minutes=duration), reason=reason)
            
            embed = discord.Embed(
                title="⏱️ Member Timed Out",
                color=discord.Color.orange(),
                description=f"**Member:** {member.mention}\n**Duration:** {duration} minutes\n**Reason:** {reason}"
            )
            embed.set_footer(text=f"Actioned by {interaction.user}", icon_url=interaction.user.avatar.url)
            
            await interaction.followup.send(embed=embed)
            
            try:
                await member.send(f"You have been timed out in **{interaction.guild.name}** for {duration} minutes.\n**Reason:** {reason}")
            except:
                pass
        except Exception as e:
            print("TIMEOUT ERROR:", e)
            await interaction.followup.send(
                f"❌ Error timing out member: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.describe(
        member="The member to warn",
        reason="Reason for warning"
    )
    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided"
    ):
        await interaction.response.defer()

        if MOD_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.followup.send(
                "❌ You don't have permission to use this command",
                ephemeral=True
            )
            return

        if not hasattr(self, "warns"):
            self.warns = {}

        user_id = str(member.id)

        if user_id not in self.warns:
            self.warns[user_id] = 0

        self.warns[user_id] += 1

        warn_count = self.warns[user_id]

        embed = discord.Embed(
            title="⚠️ Member Warned",
            color=discord.Color.yellow(),
            description=f"**Member:** {member.mention}\n**Warn:** #{warn_count}\n**Reason:** {reason}"
        )

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(
        member="The member to ban",
        reason="Reason for ban"
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided"
    ):
        """Ban a member from the server"""
        if not MOD_ROLE_ID or MOD_ROLE_ID == 0:
            await interaction.response.send_message("❌ Mod role not configured", ephemeral=True)
            return
        
        if MOD_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message(
                "❌ You don't have permission to use this command",
                ephemeral=True
            )
            return

        if member == interaction.user:
            await interaction.response.send_message("❌ You can't ban yourself", ephemeral=True)
            return

        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(
                "❌ You can't ban someone with equal or higher role",
                ephemeral=True
            )
            return

        try:
            await member.ban(reason=reason)
            
            embed = discord.Embed(
                title="🔨 Member Banned",
                color=discord.Color.red(),
                description=f"**Member:** {member.mention}\n**Reason:** {reason}"
            )
            embed.set_footer(text=f"Actioned by {interaction.user}", icon_url=interaction.user.avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
            try:
                await member.send(f"You have been banned from **{interaction.guild.name}**.\n**Reason:** {reason}")
            except:
                pass
        except Exception as e:
            await interaction.response.send_message(f"❌ Error banning member: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
