import discord
from discord.ext import commands
  
AUTO_ROLE_ID = 1499866593084178434
  
  
class AutoRole(commands.Cog):
    def __init__(self, bot):
          self.bot = bot
  
    @commands.Cog.listener()
    async def on_member_join(self, member):
  
        role = member.guild.get_role(AUTO_ROLE_ID)
  
        if role:
            try:
                await member.add_roles(role)
            except Exception as e:
                  print(e)
  

async def setup(bot):
    await bot.add_cog(AutoRole(bot))
