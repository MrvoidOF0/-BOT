"""
🌑 VOID Store Bot - Sistema de Tickets e Fechamento Blindado
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils.permissions import PermissionChecker
from config import config

# ====================================
# VIEW PERSISTENTE (Ouvidor do Botão)
# ====================================

class PersistentCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Canal", 
        style=discord.ButtonStyle.red, 
        emoji="🔒", 
        custom_id="svc:fechar" 
    )
    async def fechar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Chama a confirmação
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.confirmar_fechamento(interaction)

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        # IMPORTANTE: Registra o ouvidor do botão assim que o bot liga
        self.bot.add_view(PersistentCloseView())

    # ====================================
    # LÓGICA DE CONFIRMAÇÃO E DELEÇÃO
    # ====================================

    async def confirmar_fechamento(self, interaction: discord.Interaction):
        # Apenas staff ou o dono do ticket pode fechar
        dono_id = 0
        if interaction.channel.topic:
            # Puxa o ID do dono que salvamos no tópico do canal
            try: dono_id = int("".join(filter(str.isdigit, interaction.channel.topic)))
            except: pass

        if not PermissionChecker.is_authorized(interaction.user) and interaction.user.id != dono_id:
            return await interaction.response.send_message("❌ Você não tem permissão para fechar este ticket.", ephemeral=True)

        # Responde IMEDIATAMENTE para evitar o erro de 'não respondeu a tempo'
        view_confirma = discord.ui.View(timeout=60)
        btn_sim = discord.ui.Button(label="Sim, fechar", style=discord.ButtonStyle.danger, emoji="✅")
        btn_nao = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.secondary, emoji="❌")

        async def sim_callback(i: discord.Interaction):
            await i.response.edit_message(content="✅ O canal será deletado em 5 segundos...", view=None)
            embed = discord.Embed(description="🔒 **Ticket encerrado.**", color=0xff0000)
            await i.channel.send(embed=embed)
            await asyncio.sleep(5)
            await i.channel.delete()

        async def nao_callback(i: discord.Interaction):
            await i.response.edit_message(content="❌ Fechamento cancelado.", view=None)

        btn_sim.callback = sim_callback
        btn_nao.callback = nao_callback
        view_confirma.add_item(btn_sim)
        view_confirma.add_item(btn_nao)

        await interaction.response.send_message(
            "⚠️ **Deseja fechar este atendimento permanentemente?**", 
            view=view_confirma, 
            ephemeral=True
        )

    # ====================================
    # COMANDO DE SUPORTE
    # ====================================

    @app_commands.command(name="ticket-panel", description="🎫 Painel de Suporte")
    async def ticket_panel(self, interaction: discord.Interaction):
        if not await PermissionChecker.check_interaction_permissions(interaction): return

        embed = discord.Embed(title="🌑 VOID Store | Suporte", description="Clique abaixo para abrir um suporte geral.", color=0x000000)
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Abrir Suporte", style=discord.ButtonStyle.blurple, custom_id="panel:suporte"))
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Enviado!", ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component: return
        cid = interaction.data.get("custom_id", "")
        
        if cid == "panel:suporte":
            await interaction.response.defer(ephemeral=True)
            cat = interaction.guild.get_channel(config.TICKET_CATEGORY_ID)
            ch = await cat.create_text_channel(name=f"💬-suporte-{interaction.user.name}", topic=f"Dono: {interaction.user.id}")
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Fechar Canal", style=discord.ButtonStyle.red, emoji="🔒", custom_id="svc:fechar"))
            await ch.send(f"{interaction.user.mention} Bem-vindo! Como podemos ajudar?", view=view)
            await interaction.followup.send(f"✅ Aberto em {ch.mention}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
