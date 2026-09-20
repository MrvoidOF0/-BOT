import discord
from discord import app_commands
from discord.ext import commands
from utils.permissions import PermissionChecker
from config import config

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel_id = await self.bot.db.get_config("welcome_channel_id")
        if not channel_id: return
        channel = member.guild.get_channel(int(channel_id))
        if channel:
            embed = self.criar_embed(member)
            await channel.send(content=member.mention, embed=embed)

    def criar_embed(self, member):
        embed = discord.Embed(
            description=(
                f"👋 Bem-vindo(a) à **𝐕𝐎𝐈𝐃 𝐒𝐭𝐨𝐫𝐞**!\n\n"
                f"🛒 Tudo para deixar sua experiência no Blox Fruits mais fácil, rápida e segura.\n"
                f"📦 Confira nossos serviços, estoque e promoções!\n\n"
                f"**boas compras! ⚡**"
            ),
            color=0x000000
        )
        embed.set_author(name=f"{member.display_name} entrou!", icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="🌑 VOID Store")
        return embed

    @app_commands.command(name="welcome-configurar", description="👋 Configura o canal de boas-vindas")
    async def welcome_configurar(self, interaction, canal: discord.TextChannel):
        if not await PermissionChecker.check(interaction): return
        await self.bot.db.set_config("welcome_channel_id", str(canal.id))
        await interaction.response.send_message(f"✅ Canal definido: {canal.mention}", ephemeral=True)

    @app_commands.command(name="welcome-testar", description="👋 Testa as boas-vindas")
    async def welcome_testar(self, interaction):
        if not await PermissionChecker.check(interaction): return
        embed = self.criar_embed(interaction.user)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
