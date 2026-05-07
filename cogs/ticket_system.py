import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime
import asyncio

LOG_CHANNEL_ID = 1500184309435338752
TICKETS_FILE = "tickets.json"
CONFIG_FILE = "ticket_config.json"


# ---------------------------
# MODALS
# ---------------------------
class TicketModal(discord.ui.Modal, title="Create Support Ticket"):
    username = discord.ui.TextInput(
        label="Username of person you're trading with",
        placeholder="Enter their username",
        required=True,
        max_length=100
    )
    trade_info = discord.ui.TextInput(
        label="What is the trade?",
        placeholder="Describe what you're trading",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    middleman = discord.ui.TextInput(
        label="Which MM do you want? (Optional)",
        placeholder="Leave empty if not needed",
        required=False,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cog = interaction.client.get_cog("TicketSystem")
        if not cog:
            return await interaction.followup.send("❌ Ticket system not loaded.", ephemeral=True)
        try:
            await cog.create_ticket(
                interaction,
                self.username.value,
                self.trade_info.value,
                self.middleman.value or "None"
            )
        except Exception as e:
            print("ERROR IN create_ticket():", e)
            await interaction.followup.send("❌ An internal error occurred.", ephemeral=True)


class ApplicationModal(discord.ui.Modal, title="Application Ticket"):
    reason = discord.ui.TextInput(
        label="Why are you opening this application ticket?",
        placeholder="Explain briefly",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cog = interaction.client.get_cog("TicketSystem")
        if not cog:
            return await interaction.followup.send("❌ Ticket system not loaded.", ephemeral=True)
        try:
            await cog.create_application_ticket(
                interaction,
                self.reason.value
            )
        except Exception as e:
            print("ERROR IN create_application_ticket():", e)
            await interaction.followup.send("❌ An internal error occurred.", ephemeral=True)


# ---------------------------
# PERSISTENT BUTTONS / VIEWS
# ---------------------------
class CreateTicketButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="📋 Create Ticket",
        style=discord.ButtonStyle.blurple,
        custom_id="ticket_create_button_persistent"
    )
    async def create_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal())


class CreateApplicationButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="📝 Apply",
        style=discord.ButtonStyle.primary,
        custom_id="application_create_button_persistent"
    )
    async def create_application_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())


class TicketControlsView(discord.ui.View):
    def __init__(self, bot, ticket_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.ticket_id = ticket_id

    @discord.ui.button(
        label="✅ Claim Ticket",
        style=discord.ButtonStyle.green,
        custom_id="ticket_claim_button"
    )
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("TicketSystem")
        if cog:
            await cog.claim_ticket(interaction, self.ticket_id, self, button)

    @discord.ui.button(
        label="🔒 Close Ticket",
        style=discord.ButtonStyle.red,
        custom_id="ticket_close_button"
    )
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("TicketSystem")
        if cog:
            await cog.close_ticket(interaction, self.ticket_id)


class ReopenTicketView(discord.ui.View):
    def __init__(self, bot, ticket_id):
        super().__init__(timeout=30)
        self.bot = bot
        self.ticket_id = ticket_id

    @discord.ui.button(
        label="🔓 Reopen Ticket",
        style=discord.ButtonStyle.blurple,
        custom_id="ticket_reopen_button"
    )
    async def reopen(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("TicketSystem")
        if cog:
            await cog.reopen_ticket(interaction, self.ticket_id)
            self.stop()


# ---------------------------
# COG
# ---------------------------
class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown_minutes = 5
        self.user_cooldowns = {}

        self.tickets = self.load_json(TICKETS_FILE)
        self.config = self.load_json(CONFIG_FILE)

        # Register persistent views for open tickets
        for ticket_id, data in self.tickets.items():
            if data.get("status") == "open":
                bot.add_view(TicketControlsView(bot, ticket_id))

    # JSON helpers
    def load_json(self, path):
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_json(self, path, data):
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    # Logging
    async def log(self, guild, title, description, color, **fields):
        channel = guild.get_channel(LOG_CHANNEL_ID)
        if not channel:
            return
        embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.utcnow())
        for name, value in fields.items():
            embed.add_field(name=name, value=value, inline=False)
        try:
            await channel.send(embed=embed)
        except Exception:
            pass

    # Cooldown
    def on_cooldown(self, user_id):
        now = datetime.utcnow()
        last = self.user_cooldowns.get(user_id)
        if not last:
            return False, 0
        diff = now - last
        remaining = self.cooldown_minutes * 60 - diff.total_seconds()
        return remaining > 0, max(1, int(remaining // 60))

    # ---------------------------
    # SETUP COMMANDS
    # ---------------------------
    @app_commands.command(name="ticketsetup", description="Setup the support ticket system")
    async def ticketsetup(self, interaction: discord.Interaction,
                          category: discord.CategoryChannel,
                          support_role: discord.Role,
                          notification_role: discord.Role):
        guild_id = str(interaction.guild.id)
        cfg = self.config.get(guild_id, {})
        cfg.update({
            "category_id": category.id,
            "support_role_id": support_role.id,
            "notification_role_id": notification_role.id
        })
        self.config[guild_id] = cfg
        self.save_json(CONFIG_FILE, self.config)
        embed = discord.Embed(
            title="✅ Ticket System Setup",
            description=(
                f"**Category:** {category.mention}\n"
                f"**Support Role:** {support_role.mention}\n"
                f"**Notification Role:** {notification_role.mention}\n"
                f"**Logs Channel:** <#{LOG_CHANNEL_ID}>"
            ),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="appsetup", description="Setup the application ticket system")
    async def appsetup(self, interaction: discord.Interaction,
                       category: discord.CategoryChannel,
                       support_role: discord.Role):
        guild_id = str(interaction.guild.id)
        cfg = self.config.get(guild_id, {})
        cfg.update({
            "app_category_id": category.id,
            "app_support_role_id": support_role.id
        })
        self.config[guild_id] = cfg
        self.save_json(CONFIG_FILE, self.config)
        embed = discord.Embed(
            title="✅ Application Ticket System Setup",
            description=(
                f"**Application Category:** {category.mention}\n"
                f"**Application Support Role:** {support_role.mention}\n"
                f"**Logs Channel:** <#{LOG_CHANNEL_ID}>"
            ),
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---------------------------
    # PANELS
    # ---------------------------
    @app_commands.command(name="ticketpanel", description="Create a support ticket panel")
    async def ticketpanel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.config:
            return await interaction.response.send_message("❌ Ticket system not setup.", ephemeral=True)
        embed = discord.Embed(
            title="🎫 Support Ticket System",
            description=(
                "Click the button below to create a support ticket.\n\n"
                "**Please provide:**\n"
                "• Username of the person you're trading with\n"
                "• What the trade is about\n"
                "• Preferred middleman (optional)"
            ),
            color=discord.Color.blurple()
        )
        view = CreateTicketButton(self.bot)
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Panel created!", ephemeral=True)

    @app_commands.command(name="apppanel", description="Create an application ticket panel")
    async def apppanel(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        cfg = self.config.get(guild_id)
        if not cfg or "app_category_id" not in cfg:
            return await interaction.response.send_message("❌ Application system not setup. Use /appsetup.", ephemeral=True)
        embed = discord.Embed(
            title="📨 Application Ticket",
            description="Click the button below to open an application ticket and explain why you're applying.",
            color=discord.Color.blurple()
        )
        view = CreateApplicationButton(self.bot)
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Application panel created!", ephemeral=True)

    # ---------------------------
    # CREATE SUPPORT TICKET
    # ---------------------------
    async def create_ticket(self, interaction, username, trade_info, middleman):
        try:
            guild = interaction.guild
            guild_id = str(guild.id)
            config = self.config.get(guild_id)
            if not config:
                return await interaction.followup.send("❌ Ticket system not configured.", ephemeral=True)

            on_cd, remaining = self.on_cooldown(interaction.user.id)
            if on_cd:
                return await interaction.followup.send(f"⏳ You can create another ticket in **{remaining} minute(s)**.", ephemeral=True)

            category = guild.get_channel(config["category_id"])
            support_role = guild.get_role(config["support_role_id"])
            notify_role = guild.get_role(config.get("notification_role_id"))

            notify_text = notify_role.mention if notify_role else "Support Team"

            ticket_id = f"ticket-{len(self.tickets) + 1}"

            channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", category=category)

            # Permissions
            await channel.set_permissions(interaction.user, view_channel=True, send_messages=True, read_message_history=True)
            if support_role:
                await channel.set_permissions(support_role, view_channel=True, send_messages=True, read_message_history=True)
            await channel.set_permissions(guild.default_role, view_channel=False)

            embed = discord.Embed(
                title="🎫 Support Ticket",
                description=f"**Ticket ID:** `{ticket_id}`",
                color=discord.Color.blurple(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="👤 Trader Username", value=username)
            embed.add_field(name="🔄 Trade Info", value=trade_info, inline=False)
            embed.add_field(name="👨‍⚖️ Middleman", value=middleman)
            embed.add_field(name="📝 Created by", value=interaction.user.mention)

            view = TicketControlsView(self.bot, ticket_id)
            msg = await channel.send(notify_text, embed=embed, view=view)

            self.tickets[ticket_id] = {
                "type": "support",
                "guild_id": guild.id,
                "channel_id": channel.id,
                "user_id": interaction.user.id,
                "username": username,
                "trade_info": trade_info,
                "middleman": middleman,
                "created_at": datetime.utcnow().isoformat(),
                "status": "open",
                "claimed_by": None,
                "message_id": msg.id
            }
            self.save_json(TICKETS_FILE, self.tickets)

            self.user_cooldowns[interaction.user.id] = datetime.utcnow()
            await interaction.followup.send(f"✅ Ticket created! {channel.mention}", ephemeral=True)

            await self.log(
                guild,
                "🆕 Ticket Created",
                f"Ticket `{ticket_id}` created.",
                discord.Color.green(),
                User=f"{interaction.user} (`{interaction.user.id}`)",
                Channel=channel.mention
            )
        except Exception as e:
            print("ERROR IN create_ticket():", e)
            try:
                await interaction.followup.send("❌ Failed to create ticket.", ephemeral=True)
            except Exception:
                pass

    # ---------------------------
    # CREATE APPLICATION TICKET
    # ---------------------------
    async def create_application_ticket(self, interaction, reason):
        try:
            guild = interaction.guild
            guild_id = str(guild.id)
            cfg = self.config.get(guild_id)
            if not cfg or "app_category_id" not in cfg:
                return await interaction.followup.send("❌ Application system not configured.", ephemeral=True)

            on_cd, remaining = self.on_cooldown(interaction.user.id)
            if on_cd:
                return await interaction.followup.send(f"⏳ You can create another ticket in **{remaining} minute(s)**.", ephemeral=True)

            category = guild.get_channel(cfg["app_category_id"])
            support_role = guild.get_role(cfg.get("app_support_role_id"))

            notify_text = support_role.mention if support_role else "Application Team"

            ticket_id = f"app-{len([t for t in self.tickets.values() if t.get('type')=='application']) + 1}"

            channel = await guild.create_text_channel(f"application-{interaction.user.name}", category=category)

            # Permissions
            await channel.set_permissions(interaction.user, view_channel=True, send_messages=True, read_message_history=True)
            if support_role:
                await channel.set_permissions(support_role, view_channel=True, send_messages=True, read_message_history=True)
            await channel.set_permissions(guild.default_role, view_channel=False)

            embed = discord.Embed(
                title="📝 Application Ticket",
                description=f"**Ticket ID:** `{ticket_id}`",
                color=discord.Color.blurple(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="🗒️ Reason", value=reason, inline=False)
            embed.add_field(name="📝 Created by", value=interaction.user.mention)

            view = TicketControlsView(self.bot, ticket_id)
            msg = await channel.send(notify_text, embed=embed, view=view)

            self.tickets[ticket_id] = {
                "type": "application",
                "guild_id": guild.id,
                "channel_id": channel.id,
                "user_id": interaction.user.id,
                "reason": reason,
                "created_at": datetime.utcnow().isoformat(),
                "status": "open",
                "claimed_by": None,
                "message_id": msg.id
            }
            self.save_json(TICKETS_FILE, self.tickets)

            self.user_cooldowns[interaction.user.id] = datetime.utcnow()
            await interaction.followup.send(f"✅ Application ticket created! {channel.mention}", ephemeral=True)

            await self.log(
                guild,
                "🆕 Application Ticket Created",
                f"Application ticket `{ticket_id}` created.",
                discord.Color.green(),
                User=f"{interaction.user} (`{interaction.user.id}`)",
                Channel=channel.mention
            )
        except Exception as e:
            print("ERROR IN create_application_ticket():", e)
            try:
                await interaction.followup.send("❌ Failed to create application ticket.", ephemeral=True)
            except Exception:
                pass

    # ---------------------------
    # ADD USER TO TICKET (support only)
    # ---------------------------
    @app_commands.command(name="ticketadd", description="Add a user to the current ticket (support role only)")
    @app_commands.describe(user="The user you want to add to this ticket")
    async def ticketadd(self, interaction: discord.Interaction, user: discord.Member):
        guild = interaction.guild
        channel = interaction.channel
        guild_id = str(guild.id)
        cfg = self.config.get(guild_id)
        if not cfg:
            return await interaction.response.send_message("❌ Ticket system not configured.", ephemeral=True)

        support_role = guild.get_role(cfg.get("support_role_id"))
        # Only support role allowed
        if not support_role or support_role not in interaction.user.roles:
            return await interaction.response.send_message("❌ You don't have permission to add users to tickets.", ephemeral=True)

        # Find ticket by channel
        ticket_id = None
        for tid, data in self.tickets.items():
            if data.get("channel_id") == channel.id:
                ticket_id = tid
                break
        if not ticket_id:
            return await interaction.response.send_message("❌ This command can only be used inside a ticket channel.", ephemeral=True)

        # Add permissions
        await channel.set_permissions(user, view_channel=True, send_messages=True, read_message_history=True)
        await interaction.response.send_message(f"✅ {user.mention} has been added to this ticket.", ephemeral=True)

        await self.log(
            guild,
            "➕ User Added to Ticket",
            f"{user.mention} was added to ticket `{ticket_id}`.",
            discord.Color.blue(),
            Added_By=f"{interaction.user} (`{interaction.user.id}`)",
            Added_User=f"{user} (`{user.id}`)",
            Channel=channel.mention
        )
        await channel.send(f"👤 {user.mention} has been added to the ticket by {interaction.user.mention}.")

       # ---------------------------
    # CLAIM
    # ---------------------------
    async def claim_ticket(self, interaction, ticket_id, view, button):

        ticket = self.tickets.get(ticket_id)

        if not ticket:
            return await interaction.response.send_message(
                "❌ Ticket not found.",
                ephemeral=True
            )

        guild = interaction.guild
        cfg = self.config.get(str(guild.id), {})

        support_role_id = cfg.get("support_role_id")

        if ticket.get("type") == "application":
            support_role_id = cfg.get(
                "app_support_role_id",
                support_role_id
            )

        support_role = guild.get_role(support_role_id)

        if not support_role or support_role not in interaction.user.roles:
            return await interaction.response.send_message(
                "❌ Only support team can claim tickets.",
                ephemeral=True
            )

        if ticket.get("claimed_by"):
            return await interaction.response.send_message(
                f"⚠ Already claimed by <@{ticket['claimed_by']}>.",
                ephemeral=True
            )

        ticket["claimed_by"] = interaction.user.id
        self.save_json(TICKETS_FILE, self.tickets)

        # MM LOG
        MEMBER_ROLE_ID = 1499866593084178434
        LOG_CHANNEL_ID = 1500529115906965605

        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)

        members = []

        for member in interaction.channel.members:
            if any(role.id == MEMBER_ROLE_ID for role in member.roles):
                members.append(member)

        members = members[:2]

        mentions = " ".join(
            member.mention for member in members
        )

        if log_channel:
            await log_channel.send(
                f"Ticket #{ticket_id} mmed by {interaction.user.mention}\n"
                f"Vouch here: {mentions}"
            )

        button.label = f"Claimed by {interaction.user.name}"
        button.disabled = True

        try:
            await interaction.response.edit_message(view=view)
        except Exception:
            pass

        await interaction.followup.send(
            "✅ Ticket claimed.",
            ephemeral=True
        )

        await self.log(
            guild,
            "📌 Ticket Claimed",
            f"Ticket `{ticket_id}` claimed.",
            discord.Color.gold(),
            Claimed_By=f"{interaction.user} (`{interaction.user.id}`)"
        )
    # ---------------------------
    # CLOSE
    # ---------------------------
    async def close_ticket(self, interaction, ticket_id):
        await interaction.response.defer(ephemeral=True)
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return await interaction.followup.send("❌ Ticket not found.", ephemeral=True)

        guild = interaction.guild
        cfg = self.config.get(str(guild.id), {})
        support_role_id = cfg.get("support_role_id")
        if ticket.get("type") == "application":
            support_role_id = cfg.get("app_support_role_id", support_role_id)
        support_role = guild.get_role(support_role_id)

        # Only support role allowed to close
        if not support_role or support_role not in interaction.user.roles:
            return await interaction.followup.send("❌ You don't have permission to close tickets.", ephemeral=True)

        channel = guild.get_channel(ticket["channel_id"])
        ticket["status"] = "closed"
        ticket["closed_by"] = interaction.user.id
        ticket["closed_at"] = datetime.utcnow().isoformat()
        self.save_json(TICKETS_FILE, self.tickets)

        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=f"Closed by {interaction.user.mention}.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="You have 30 seconds to reopen this ticket.")
        view = ReopenTicketView(self.bot, ticket_id)
        if channel:
            await channel.send(embed=embed, view=view)

        await interaction.followup.send(f"Ticket `{ticket_id}` closed.", ephemeral=True)

        await self.log(
            guild,
            "🔒 Ticket Closed",
            f"Ticket `{ticket_id}` closed.",
            discord.Color.red(),
            Closed_By=f"{interaction.user} (`{interaction.user.id}`)"
        )

        # Schedule deletion
        self.bot.loop.create_task(self.delete_after_delay(ticket_id, guild.id, channel.id if channel else None))

    async def delete_after_delay(self, ticket_id, guild_id, channel_id):
        await asyncio.sleep(30)
        ticket = self.tickets.get(ticket_id)
        if not ticket or ticket.get("status") != "closed":
            return
        guild = self.bot.get_guild(guild_id)
        channel = guild.get_channel(channel_id) if guild and channel_id else None
        try:
            if channel:
                await channel.delete(reason="Ticket closed and not reopened.")
        except Exception:
            pass
        ticket["status"] = "deleted"
        self.save_json(TICKETS_FILE, self.tickets)

    # ---------------------------
    # REOPEN
    # ---------------------------
    async def reopen_ticket(self, interaction, ticket_id):
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            return await interaction.response.send_message("❌ Ticket not found.", ephemeral=True)

        guild = interaction.guild
        channel = guild.get_channel(ticket["channel_id"])
        if ticket.get("status") != "closed":
            return await interaction.response.send_message("⚠ Ticket is not closed.", ephemeral=True)

        ticket["status"] = "open"
        ticket["reopened_by"] = interaction.user.id
        ticket["reopened_at"] = datetime.utcnow().isoformat()
        self.save_json(TICKETS_FILE, self.tickets)

        await self.log(
            guild,
            "🔓 Ticket Reopened",
            f"Ticket `{ticket_id}` reopened.",
            discord.Color.blurple(),
            Reopened_By=f"{interaction.user} (`{interaction.user.id}`)"
        )

        @commands.Cog.listener()
        async def on_message(self, message):

            if message.author.bot:
                return
    
            VOUCH_CHANNEL_ID = 1500529115906965605
            MEMBER_ROLE_ID = 1499866593084178434

            if message.channel.id != VOUCH_CHANNEL_ID:
                return
    
            if not message.reference:
                return

        if not any(role.id == MEMBER_ROLE_ID for role in message.author.roles):
            return

            replied_message = await message.channel.fetch_message(
            message.reference.message_id
)

        content = ""
        
        if replied_message.content:
            content += replied_message.content.lower()
        
        if replied_message.embeds:
            embed = replied_message.embeds[0]
        
            if embed.description:
                content += " " + embed.description.lower()
        
            if embed.title:
                content += " " + embed.title.lower()
        
        if "ticket #" not in content:
                    return
        
        try:
                    ticket_id = content.split("ticket #")[1].split(" ")[0].strip()
                    ticket_id = ticket_id.lower()
        except:
            return
        print("FOUND TICKET:", ticket_id)
        ticket = self.tickets.get(ticket_id)
            
        if not ticket:
            return
            
        ticket.setdefault("vouches", [])
            
        if message.author.id not in ticket["vouches"]:
                ticket["vouches"].append(message.author.id)
            
        self.save_json(TICKETS_FILE, self.tickets)
            
        if len(ticket["vouches"]) >= 2:
            
                ticket["status"] = "closed"
            
                self.save_json(TICKETS_FILE, self.tickets)
            
                guild = message.guild
                channel = guild.get_channel(ticket["channel_id"])
            
                if channel:
                    await channel.send("🔒 Ticket automatically closed after 2 vouches.")
                    await channel.edit(name=f"closed-{channel.name}")
            
                self.bot.loop.create_task(
                    self.delete_after_delay(
                        ticket_id,
                        guild.id,
                        channel.id
                    )
                )

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
