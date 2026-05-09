import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()
MOD_ROLE_ID = 1499865433744998480

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def has_mod_role(self):
        """Check if user has the moderator role"""
        async def predicate(interaction: discord.Interaction) -> bool:
            if not MOD_ROLE_ID or MOD_ROLE_ID == 0:
                await interaction.response.send_message(
                    "❌ Mod role not configured. Please set MOD_ROLE_ID in .env file",
                    ephemeral=True
                )
                return False
            
            if MOD_ROLE_ID not in [role.id for role in interaction.user.roles]:
                await interaction.response.send_message(
                    "❌ Mod role not found in this server",
                    ephemeral=True
                )
                return False
            
            if mod_role not in interaction.user.roles:
                await interaction.response.send_message(
                    "❌ You don't have permission to use this command",
                    ephemeral=True
                )
                return False
            
            return True
        
        return app_commands.check(predicate)

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
        """Timeout a member"""
        if not MOD_ROLE_ID or MOD_ROLE_ID == 0:
            await interaction.response.send_message("❌ Mod role not configured", ephemeral=True)
            return
        
        mod_role = interaction.guild.get_role(MOD_ROLE_ID)
        if mod_role not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ You don't have permission to use this command",
                ephemeral=True
            )
            return

        if member == interaction.user:
            await interaction.response.send_message("❌ You can't timeout yourself", ephemeral=True)
            return

        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(
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
            
            await interaction.response.send_message(embed=embed)
            
            try:
                await member.send(f"You have been timed out in **{interaction.guild.name}** for {duration} minutes.\n**Reason:** {reason}")
            except:
                pass
        except Exception as e:
            await interaction.response.send_message(f"❌ Error timing out member: {str(e)}", ephemeral=True)

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(
        member="The member to kick",
        reason="Reason for kick"
    )
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided"
    ):
        """Kick a member from the server"""
        if not MOD_ROLE_ID or MOD_ROLE_ID == 0:
            await interaction.response.send_message("❌ Mod role not configured", ephemeral=True)
            return
        
        mod_role = interaction.guild.get_role(MOD_ROLE_ID)
        if mod_role not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ You don't have permission to use this command",
                ephemeral=True
            )
            return

        if member == interaction.user:
            await interaction.response.send_message("❌ You can't kick yourself", ephemeral=True)
            return

        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(
                "❌ You can't kick someone with equal or higher role",
                ephemeral=True
            )
            return

        try:
            await member.kick(reason=reason)
            
            embed = discord.Embed(
                title="👢 Member Kicked",
                color=discord.Color.orange(),
                description=f"**Member:** {member.mention}\n**Reason:** {reason}"
            )
            embed.set_footer(text=f"Actioned by {interaction.user}", icon_url=interaction.user.avatar.url)
            
            await interaction.response.send_message(embed=embed)
            
            try:
                await member.send(f"You have been kicked from **{interaction.guild.name}**.\n**Reason:** {reason}")
            except:
                pass
        except Exception as e:
            await interaction.response.send_message(f"❌ Error kicking member: {str(e)}", ephemeral=True)

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
        
        mod_role = interaction.guild.get_role(MOD_ROLE_ID)
        if mod_role not in interaction.user.roles:
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
