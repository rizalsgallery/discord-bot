async def claim_ticket(self, interaction, ticket_id, view, button):
    ticket = self.tickets.get(ticket_id)

    if not ticket:
        return await interaction.response.send_message(
            "❌ Ticket not found.",
            ephemeral=True
        )

    guild = interaction.guild
    cfg = self.config.get(str(guild.id), {})

    # Determine support role
    support_role_id = cfg.get("support_role_id")

    if ticket.get("type") == "application":
        support_role_id = cfg.get(
            "app_support_role_id",
            support_role_id
        )

    support_role = guild.get_role(support_role_id)

    # Permission check
    if not support_role or support_role not in interaction.user.roles:
        return await interaction.response.send_message(
            "❌ Only support team can claim tickets.",
            ephemeral=True
        )

    # Already claimed
    if ticket.get("claimed_by"):
        return await interaction.response.send_message(
            f"⚠ Already claimed by <@{ticket['claimed_by']}>.",
            ephemeral=True
        )

    # Save claimer
    ticket["claimed_by"] = interaction.user.id
    self.save_json(TICKETS_FILE, self.tickets)

    # MM LOG
    channel = interaction.channel

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

    # Update button
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
