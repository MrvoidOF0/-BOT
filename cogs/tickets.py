"""
🌑 VOID Store Bot - Sistema de Tickets e Fechamento Universal
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils.permissions import PermissionChecker
from utils.logger import logger
from config import config

# ====================================
# VIEW PERSISTENTE DE FECHAMENTO
# ====================================

class PersistentCloseView(discord.ui.View):
    """Esta view fica na memória do bot e ouve o custom_id 'svc:fechar'"""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Canal", 
        style=discord.ButtonStyle.red, 
        emoji="🔒", 
        custom_id="svc:fechar"
    )
    async def fechar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.processar_fechamento(interaction)

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        # REGISTRA A VIEW PARA O BOT OUVIR O BOTÃO MESMO APÓS REINICIAR
        self.bot.add_view(PersistentCloseView())

    # ====================================
    # LISTENER PARA OUTROS BOTÕES NO TICKET
    # ====================================

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        
        custom_id = interaction.data.get("custom_id", "")

        # Suporte Geral
        if custom_id == "panel:suporte":
            await self.abrir_ticket(interaction, "suporte")
        
        # Botão de PIX dentro de qualquer canal
        if custom_id == "canal:pix":
            if not PermissionChecker.is_staff(interaction.user):
                return await interaction.response.send_message("❌ Somente staff pode gerar PIX.", ephemeral=True)
            await interaction.response.send_message("💳 Use o comando `/pix-gerar` para enviar a cobrança PIX.", ephemeral=True)

    # ====================================
    # LÓGICA DE FECHAMENTO
    # ====================================

    async def processar_fechamento(self, interaction: discord.Interaction):
        """Executa a confirmação e deleta o canal"""
        
        # Verificar permissão (Staff ou criador do canal)
        is_staff = PermissionChecker.is_staff(interaction.user)
        # Verifica se o ID do usuário está no tópico do canal (onde salvamos o ID ao criar)
        dono_id = ""
        if interaction.channel.topic:
            dono_id = "".join(filter(str.isdigit, interaction.channel.topic))

        if not is_staff and str(interaction.user.id) != dono_id:
            return await interaction.response.send_message("❌ Você não tem permissão para fechar este ticket.", ephemeral=True)

        # Botões de confirmação temporários
        confirm_view = discord.ui.View(timeout=30)
        btn_sim = discord.ui.Button(label="Sim, fechar", style=discord.ButtonStyle.red, emoji="✅")
        btn_nao = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.gray, emoji="❌")

        async def confirm_callback(i: discord.Interaction):
            await i.response.edit_message(content="✅ Fechando ticket...", embed=None, view=None)
            embed_aviso = discord.Embed(
                description=f"🔒 Ticket fechado por {i.user.mention}\nDeletando em **5 segundos**...",
                color=0xff0000
            )
            await i.channel.send(embed=embed_aviso)
            await asyncio.sleep(5)
            await i.channel.delete()

        async def cancel_callback(i: discord.Interaction):
            await i.response.edit_message(content="❌ Fechamento cancelado.", embed=None, view=None)

        btn_sim.callback = confirm_callback
        btn_nao.callback = cancel_callback
        confirm_view.add_item(btn_sim)
        confirm_view.add_item(btn_nao)

        await interaction.response.send_message(
            content="⚠️ **Você deseja fechar este ticket permanentemente?**",
            view=confirm_view,
            ephemeral=True
        )

    # ====================================
    # COMANDO DO PAINEL DE SUPORTE
    # ====================================

    @app_commands.command(name="ticket-panel", description="🎫 Painel de Atendimento Geral")
    async def ticket_panel(self, interaction: discord.Interaction):
        if not await PermissionChecker.check_interaction_permissions(interaction, require_authorized=True):
            return

        embed = discord.Embed(
            title="🌑 VOID Store | Atendimento",
            description="Clique no botão abaixo para abrir um ticket de suporte geral.",
            color=0x000000
        )
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Abrir Suporte", style=discord.ButtonStyle.blurple, custom_id="panel:suporte"))
        
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel enviado!", ephemeral=True)

    async def abrir_ticket(self, interaction: discord.Interaction, tipo: str):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        cat = guild.get_channel(config.TICKET_CATEGORY_ID)
        
        channel = await cat.create_text_channel(
            name=f"💬-{tipo}-{interaction.user.name}",
            topic=f"Ticket Suporte | {interaction.user.id}"
        )
        
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Fechar Suporte", style=discord.ButtonStyle.red, emoji="🔒", custom_id="svc:fechar"))

        await channel.send(f"{interaction.user.mention} Bem-vindo ao suporte! Como podemos ajudar?", view=view)
        await interaction.followup.send(f"✅ Ticket aberto: {channel.mention}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
