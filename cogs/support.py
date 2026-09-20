"""
🌑 VOID Store Bot - Suporte Dedicado (Reescrito)
"""

import discord
from discord import app_commands
from discord.ext import commands
from utils.permissions import PermissionChecker
from config import config

class Support(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="painel-suporte", description="💬 Cria o painel de suporte")
    async def painel_suporte(self, interaction: discord.Interaction):
        if not await PermissionChecker.check_interaction_permissions(interaction, require_authorized=True):
            return

        embed = discord.Embed(
            title="💬 VOID Store | Central de Suporte",
            description="Precisa de ajuda? Clique no botão abaixo para abrir um ticket.",
            color=0x5865f2
        )
        
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(
            label="Abrir Suporte", 
            style=discord.ButtonStyle.blurple, 
            emoji="💬", 
            custom_id="suporte:abrir"
        ))

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel de suporte criado!", ephemeral=True)

    async def handle_abrir(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        user = interaction.user
        category = interaction.guild.get_channel(config.TICKET_CATEGORY_ID)
        channel_name = f"suporte-{user.name}".lower()[:50]

        try:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
            }
            # Adicionar cargos autorizados
            for rid in config.AUTHORIZED_ROLE_IDS:
                r = interaction.guild.get_role(rid)
                if r: overwrites[r] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)

            embed = discord.Embed(title="💬 Ticket de Suporte", description=f"Olá {user.mention}, como podemos ajudar?", color=0x5865f2)
            
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Fechar Suporte", style=discord.ButtonStyle.red, emoji="🔒", custom_id="svc:fechar"))

            await channel.send(embed=embed, view=view)
            await interaction.followup.send(f"✅ Suporte aberto: {channel.mention}", ephemeral=True)
        except:
            await interaction.followup.send("❌ Erro ao abrir suporte.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Support(bot))
