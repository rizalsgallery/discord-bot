import time
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random

HOST_ROLE_ID = 1503070325255176345
GIVEAWAY_ROLE_ID = 1499834061815025734
GIVEAWAY_HOST_ROLE_ID = 1503070325255176345
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
class ClaimView(discord.ui.View):
    def __init__(self, winners, host_role):
        super().__init__(timeout=1800)

        self.winners = winners
        self.claimed = []
        self.host_role = host_role

    @discord.ui.button(label="Claim Prize", style=discord.ButtonStyle.blurple)
    async def claim_prize(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id not in self.winners:
            await interaction.response.send_message(
                "❌ You are not a winner.",
                ephemeral=True
            )
            return

        if interaction.user.id in self.claimed:
            await interaction.response.send_message(
                "❌ You already claimed your prize.",
                ephemeral=True
            )
            return

        self.claimed.append(interaction.user.id)

        embed = discord.Embed(
            title="✅ Prize Claimed",
            description=f"{interaction.user.mention} claimed his prize!",
            color=discord.Color.green()
        )

        await interaction.response.send_message(
            content=f"<@&{HOST_ROLE_ID}>",
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True)
        )
class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @app_commands.check(
    lambda interaction:
    GIVEAWAY_HOST_ROLE_ID in [role.id for role in interaction.user.roles]
)
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
            value=extra,
            inline=False
        )
        

        embed.set_image(url=image)

        await interaction.response.send_message(
            content=role.mention if role else None,
            embed=embed,
            view=view
        )
        
        if duration.endswith("m"):
            wait_time = int(duration[:-1]) * 60
        
        elif duration.endswith("h"):
            wait_time = int(duration[:-1]) * 3600
        
        await asyncio.sleep(wait_time)
        
        if len(view.entries) == 0:
            await interaction.channel.send(
                "❌ No valid giveaway entries."
            )
            return
        
        winner_amount = min(winners, len(view.entries))
        
        winner_ids = random.sample(view.entries, winner_amount)
        
        winner_mentions = []
        
        for winner_id in winner_ids:
            winner = interaction.guild.get_member(winner_id)
        
            if winner:
                winner_mentions.append(winner.mention)
        
        winner_embed = discord.Embed(
            title="🎉 Giveaway Ended",
            description=(
                f"Winners:\n{', '.join(winner_mentions)}\n\n"
                f"You have **30 minutes** to claim your prize."
            ),
            color=discord.Color.green()
        )
        
        host_role = interaction.guild.get_role(GIVEAWAY_ROLE_ID)

        claim_view = ClaimView(
            winner_ids,
            host_role
        )
        
        await interaction.channel.send(
            content=" ".join(winner_mentions),
            embed=winner_embed,
            view=claim_view
        )

async def setup(bot):
    await bot.add_cog(Giveaway(bot))
