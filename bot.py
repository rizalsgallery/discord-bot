import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
print("TOKEN:", TOKEN)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

class TicketBot(commands.Bot):
    async def setup_hook(self):
        # Load cogs
        cogs_dir = "./cogs"
        for filename in os.listdir(cogs_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                await self.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded {filename}")

        # Register persistent views AFTER cogs load
        from cogs.ticket_system import CreateTicketButton
        self.add_view(CreateTicketButton(self))

bot = TicketBot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    
    guild = discord.Object(id=1499534653399371886)

    bot.tree.clear_commands(guild=guild)
    await bot.tree.sync(guild=guild)
    synced = await bot.tree.sync()

    print(f"Synced {len(synced)} commands")
    print(f"{bot.user} is online!")

bot.run(TOKEN)
