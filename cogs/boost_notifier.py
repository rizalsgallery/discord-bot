import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import json

load_dotenv()

class BoostNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.boost_settings = self.load_boost_settings()

    def load_boost_settings(self):
        """Load boost settings from file"""
        if os.path.exists('boost_settings.json'):
            with open('boost_settings.json', 'r') as f:
                return json.load(f)
        return {}

    def save_boost_settings(self):
        """Save boost settings to file"""
        with open('boost_settings.json', 'w') as f:
            json.dump(self.boost_settings, f, indent=4)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Detect when a member boosts the server"""
        # Check if user just started boosting
        if before.premium_since is None and after.premium_since is not None:
            guild = after.guild
            
            # Get the boost channel for this guild
            channel_id = self.boost_settings.get(str(guild.id))
            if not channel_id:
                return
            
            channel = guild.get_channel(channel_id)
            if not channel:
                return

            embed = discord.Embed(
                title="🚀 Server Boost!",
                description=f"{after.mention} just boosted the server!",
                color=discord.Color.magenta()
            )
            embed.add_field(name="Boost Level", value=f"Level {guild.premium_tier}", inline=False)
            embed.add_field(name="Total Boosts", value=f"{guild.premium_subscription_count}", inline=False)
            embed.set_thumbnail(url=after.avatar.url if after.avatar else None)
            
            try:
                await channel.send(embed=embed)
            except Exception as e:
                print(f"Error sending boost notification: {e}")

    @app_commands.command(name="setboostchannel", description="Set the channel for boost notifications")
    @app_commands.describe(channel="The channel to send boost notifications to")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_boost_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the channel where boost notifications will be sent"""
        self.boost_settings[str(interaction.guild.id)] = channel.id
        self.save_boost_settings()
        
        embed = discord.Embed(
            title="✅ Boost Channel Set",
            description=f"Boost notifications will be sent to {channel.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="getboostchannel", description="Get the current boost notification channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def get_boost_channel(self, interaction: discord.Interaction):
        """Get the current boost notification channel"""
        channel_id = self.boost_settings.get(str(interaction.guild.id))
        
        if not channel_id:
            await interaction.response.send_message("❌ No boost channel set for this server", ephemeral=True)
            return
        
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            embed = discord.Embed(
                title="📢 Current Boost Channel",
                description=f"Boost notifications are sent to {channel.mention}",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="⚠️ Boost Channel Not Found",
                description="The configured boost channel no longer exists",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(BoostNotifier(bot))
