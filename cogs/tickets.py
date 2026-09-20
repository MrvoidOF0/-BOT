"""
🌑 VOID Store Bot - Sistema de Tickets
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils.permissions import PermissionChecker
from config import config

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Intercepta os cliques de fechar e suporte geral"""
        if interaction.type != discord.InteractionType.component: return
        cid = interaction.data.get("custom_id", "")

        # BOTÃO FECHAR
        if cid == "svc:fechar":
            # Resposta imediata para evitar erro de tempo
            await interaction.response.defer(ephemeral=True)
            await self.processar_fechamento(interaction)

        # BOTÃO SUPORTE GERAL
        if cid == "panel:suporte":
            await interaction.response.defer(ephemeral=True)
            await self.abrir_suporte(interaction)

        # BOTÃO PIX
        if cid == "canal:pix":
            if not PermissionChecker.is_authorized(interaction.user):
                return await interaction.response.send_message("❌ Apenas staff.", ephemeral=True)
            await interaction.response.send_message("💳 Use `/pix-gerar` para enviar a cobrança.", ephemeral=True)

    async def abrir_suporte(self, interaction: discord.Interaction):
        guild = interaction.guild
        cat = guild.get_channel(config.TICKET_CATEGORY_ID)
        ch = await cat.create_text_channel(name=f"💬-suporte-{interaction.user.name}", topic=f"Dono: {interaction.user.id}")
        
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Fechar Canal", style=discord.ButtonStyle.red, emoji="🔒", custom_id="svc:fechar"))
        
        await ch.send(f"{interaction.user.mention} Como podemos ajudar?", view=view)
        await interaction.followup.send(f"✅ Aberto em {ch.mention}", ephemeral=True)

    async def processar_fechamento(self, interaction: discord.Interaction):
        # Confirmação rápida
        view = discord.ui.View(timeout=30)
        btn_sim = discord.ui.Button(label="Sim, fechar", style=discord.ButtonStyle.danger)
        btn_nao = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.secondary)

        async def sim(i: discord.Interaction):
            await i.response.edit_message(content="✅ Canal será deletado em 5 segundos...", view=None)
            await i.channel.send("🔒 **Ticket encerrado.**")
            await asyncio.sleep(5)
            await i.channel.delete()

        async def nao(i: discord.Interaction):
            await i.response.edit_message(content="❌ Cancelado.", view=None)

        btn_sim.callback = sim
        btn_nao.callback = nao
        view.add_item(btn_sim)
        view.add_item(btn_nao)

        await interaction.followup.send("⚠️ **Deseja fechar o ticket?**", view=view, ephemeral=True)

    @app_commands.command(name="ticket-panel", description="🎫 Painel de Suporte")
    async def ticket_panel(self, interaction: discord.Interaction):
        if not await PermissionChecker.check_interaction_permissions(interaction): return
        embed = discord.Embed(title="🌑 VOID Store | Suporte", description="Clique abaixo para abrir um suporte.", color=0x000000)
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Abrir Suporte", style=discord.ButtonStyle.blurple, custom_id="panel:suporte"))
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Enviado!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
