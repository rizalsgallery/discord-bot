import discord
from discord.ext import commands
from discord import app_commands


# ----------------------------------------------------
# MODAL FOR CREATING EMBEDS
# ----------------------------------------------------
class EmbedModal(discord.ui.Modal, title="Create Custom Embed"):

    title_input = discord.ui.TextInput(
        label="Embed Title",
        placeholder="Enter the embed title",
        required=True,
        max_length=256
    )

    description_input = discord.ui.TextInput(
        label="Embed Description",
        placeholder="Enter the embed description",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=4000
    )

    footer_input = discord.ui.TextInput(
        label="Embed Footer",
        placeholder="Enter the embed footer (optional)",
        required=False,
        max_length=2048
    )

    color_input = discord.ui.TextInput(
        label="Color (Hex Code)",
        placeholder="e.g., FF0000 or leave empty for default",
        required=False,
        max_length=6
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Called automatically when the modal is submitted"""

        # Convert user → Member
        member = interaction.guild.get_member(interaction.user.id)

        if member is None:
            return await interaction.response.send_message(
                "❌ Could not verify your permissions.",
                ephemeral=True
            )

        # Prepare modal data
        modal_data = {
            "title": self.title_input.value,
            "description": self.description_input.value,
            "footer": self.footer_input.value or f"Created by {interaction.user}",
            "color": self.color_input.value or "5865F2"
        }

        # Build channel list
        channels = [
            ch for ch in interaction.guild.text_channels
            if ch.permissions_for(member).send_messages

        ]

        if not channels:
            return await interaction.response.send_message(
                "❌ No channels available.",
                ephemeral=True
            )

        # Create view
        view = ChannelSelectView(modal_data)

        # Add channel options
        options = [
            discord.SelectOption(label=ch.name[:100], value=str(ch.id))
            for ch in channels[:25]
        ]
        view.children[0].options = options

        # Send channel select menu
        await interaction.response.send_message(
            "📝 Select a channel to send the embed:",
            view=view,
            ephemeral=True
        )


# ----------------------------------------------------
# CHANNEL SELECT VIEW
# ----------------------------------------------------
class ChannelSelectView(discord.ui.View):
    def __init__(self, modal_data: dict):
        super().__init__(timeout=60)
        self.modal_data = modal_data

    @discord.ui.select(
        placeholder="Select a channel to send the embed",
        min_values=1,
        max_values=1,
        custom_id="channel_select"
    )
    async def select_channel(self, interaction: discord.Interaction, select: discord.ui.Select):

        channel_id = int(select.values[0])
        channel = interaction.guild.get_channel(channel_id)

        if not channel:
            return await interaction.response.send_message("❌ Channel not found.", ephemeral=True)

        # Parse color
        try:
            color_hex = self.modal_data["color"].replace("#", "")
            color_hex = color_hex.ljust(6, "0")
            color_value = int(color_hex, 16)
            color = discord.Color(color_value)
        except:
            color = discord.Color.blurple()

        # Build embed
        embed = discord.Embed(
            title=self.modal_data["title"],
            description=self.modal_data["description"],
            color=color
        )
        embed.set_footer(text=self.modal_data["footer"])

        # Try sending embed
        try:
            await channel.send(embed=embed)
            await interaction.response.send_message(
                f"✅ Embed sent to {channel.mention}",
                ephemeral=True
            )
            self.stop()

        except discord.Forbidden:
            await interaction.response.send_message(
                f"❌ I don't have permission to send messages in {channel.mention}",
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error sending embed: {e}",
                ephemeral=True
            )


# ----------------------------------------------------
# COG
# ----------------------------------------------------
class EmbedCreator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="embed", description="Create and send a custom embed")
    async def create_embed(self, interaction: discord.Interaction):
        """Open the embed creation modal"""

        modal = EmbedModal()
        await interaction.response.send_modal(modal)


async def setup(bot):
    await bot.add_cog(EmbedCreator(bot))
