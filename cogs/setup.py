"""
🌑 VOID Store Bot - Sistema de Configuração Interativo
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from utils.embeds import VoidEmbeds
from utils.permissions import PermissionChecker
from utils.constants import Emojis
from utils.logger import logger
from config import config


# ====================================
# MODALS DE CONFIGURAÇÃO
# ====================================

class SetupTicketModal(discord.ui.Modal, title="Configurar Sistema de Tickets"):
    """Modal para configurar o sistema de tickets"""

    category_id = discord.ui.TextInput(
        label="ID da Categoria dos Tickets",
        placeholder="Ex: 1234567890123456789",
        required=True,
        max_length=20
    )

    log_channel_id = discord.ui.TextInput(
        label="ID do Canal de Logs de Tickets",
        placeholder="Ex: 1234567890123456789",
        required=False,
        max_length=20
    )

    transcript_channel_id = discord.ui.TextInput(
        label="ID do Canal de Transcripts",
        placeholder="Ex: 1234567890123456789 (deixe vazio para desativar)",
        required=False,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        results = []

        # Validar e salvar cada configuração
        if self.category_id.value:
            cat = interaction.guild.get_channel(int(self.category_id.value))
            if cat and isinstance(cat, discord.CategoryChannel):
                await interaction.client.db.set_config("ticket_category_id", self.category_id.value)
                results.append(f"{Emojis.SUCCESS} Categoria de tickets: {cat.name}")
            else:
                results.append(f"{Emojis.ERROR} Categoria inválida: {self.category_id.value}")

        if self.log_channel_id.value:
            ch = interaction.guild.get_channel(int(self.log_channel_id.value))
            if ch:
                await interaction.client.db.set_config("ticket_log_channel_id", self.log_channel_id.value)
                results.append(f"{Emojis.SUCCESS} Canal de logs: {ch.mention}")
            else:
                results.append(f"{Emojis.ERROR} Canal de log inválido")

        if self.transcript_channel_id.value:
            ch = interaction.guild.get_channel(int(self.transcript_channel_id.value))
            if ch:
                await interaction.client.db.set_config("ticket_transcript_channel_id", self.transcript_channel_id.value)
                results.append(f"{Emojis.SUCCESS} Canal de transcript: {ch.mention}")

        embed = VoidEmbeds.success(
            "Configuração de Tickets Salva",
            "\n".join(results) if results else "Nenhuma alteração realizada."
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


class SetupRolesModal(discord.ui.Modal, title="Configurar Cargos de Progressão"):
    """Modal para configurar IDs dos cargos de tier"""

    starter_id = discord.ui.TextInput(
        label="ID do Cargo Starter (R$25+)",
        placeholder="Ex: 1234567890123456789",
        required=False, max_length=20
    )

    plus_id = discord.ui.TextInput(
        label="ID do Cargo Plus (R$50+)",
        placeholder="Ex: 1234567890123456789",
        required=False, max_length=20
    )

    premium_id = discord.ui.TextInput(
        label="ID do Cargo Premium (R$100+)",
        placeholder="Ex: 1234567890123456789",
        required=False, max_length=20
    )

    supreme_id = discord.ui.TextInput(
        label="ID do Cargo Supreme (R$200+)",
        placeholder="Ex: 1234567890123456789",
        required=False, max_length=20
    )

    prestige_id = discord.ui.TextInput(
        label="ID do Cargo Prestige (R$350+)",
        placeholder="Ex: 1234567890123456789",
        required=False, max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        fields = {
            "starter_role_id": self.starter_id.value,
            "plus_role_id": self.plus_id.value,
            "premium_role_id": self.premium_id.value,
            "supreme_role_id": self.supreme_id.value,
            "prestige_role_id": self.prestige_id.value,
        }

        results = []
        for key, value in fields.items():
            if value and value.strip():
                role = interaction.guild.get_role(int(value.strip()))
                if role:
                    await interaction.client.db.set_config(key, value.strip())
                    results.append(f"{Emojis.SUCCESS} `{key}` → **{role.name}**")
                else:
                    results.append(f"{Emojis.ERROR} Cargo não encontrado para `{key}`: `{value}`")

        embed = VoidEmbeds.success(
            "Cargos de Progressão Salvos",
            "\n".join(results) if results else "Nenhuma configuração enviada."
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


class SetupLogsModal(discord.ui.Modal, title="Configurar Canais de Logs"):
    """Modal para configurar canais de log"""

    main_log = discord.ui.TextInput(
        label="Canal de Log Principal",
        placeholder="ID do canal principal de logs",
        required=False, max_length=20
    )

    mod_log = discord.ui.TextInput(
        label="Canal de Log de Moderação",
        placeholder="ID do canal de logs de moderação",
        required=False, max_length=20
    )

    order_log = discord.ui.TextInput(
        label="Canal de Log de Pedidos",
        placeholder="ID do canal de logs de pedidos",
        required=False, max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        fields = {
            "log_channel_id": self.main_log.value,
            "mod_log_channel_id": self.mod_log.value,
            "order_log_channel_id": self.order_log.value,
        }

        results = []
        for key, value in fields.items():
            if value and value.strip():
                ch = interaction.guild.get_channel(int(value.strip()))
                if ch:
                    await interaction.client.db.set_config(key, value.strip())
                    results.append(f"{Emojis.SUCCESS} `{key}` → {ch.mention}")
                else:
                    results.append(f"{Emojis.ERROR} Canal inválido para `{key}`")

        embed = VoidEmbeds.success(
            "Canais de Log Salvos",
            "\n".join(results) if results else "Nenhuma configuração enviada."
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


# ====================================
# VIEW PRINCIPAL DO SETUP
# ====================================

class SetupView(discord.ui.View):
    """Menu principal do painel de configuração"""

    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Tickets", style=discord.ButtonStyle.blurple, emoji=Emojis.TICKET, row=0)
    async def setup_tickets(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupTicketModal())

    @discord.ui.button(label="Cargos", style=discord.ButtonStyle.green, emoji=Emojis.CROWN, row=0)
    async def setup_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupRolesModal())

    @discord.ui.button(label="Logs", style=discord.ButtonStyle.gray, emoji="📜", row=0)
    async def setup_logs(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupLogsModal())

    @discord.ui.button(label="Ver Configurações", style=discord.ButtonStyle.secondary, emoji=Emojis.INFO, row=1)
    async def view_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Exibe todas as configurações salvas no banco"""
        await interaction.response.defer(ephemeral=True)

        keys = [
            "ticket_category_id",
            "ticket_log_channel_id",
            "log_channel_id",
            "mod_log_channel_id",
            "order_log_channel_id",
            "starter_role_id",
            "plus_role_id",
            "premium_role_id",
            "supreme_role_id",
            "prestige_role_id"
        ]

        lines = []
        for key in keys:
            value = await interaction.client.db.get_config(key)
            if value:
                # Tentar resolver o canal/cargo
                resolved = None
                obj = interaction.guild.get_channel(int(value)) or interaction.guild.get_role(int(value))
                if obj:
                    resolved = getattr(obj, 'mention', None) or getattr(obj, 'name', value)
                lines.append(f"**{key}:** {resolved or value}")
            else:
                lines.append(f"**{key}:** *Não configurado*")

        embed = VoidEmbeds.default(
            "⚙️ Configurações Atuais",
            "\n".join(lines)
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


# ====================================
# COG
# ====================================

class Setup(commands.Cog):
    """Sistema de configuração interativa via Slash Command"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    @app_commands.command(
        name="setup",
        description="⚙️ Abre o painel de configuração do VOID Store Bot"
    )
    async def setup(self, interaction: discord.Interaction):
        """Abre o painel de configuração interativo"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_admin=True):
            return

        embed = VoidEmbeds.default(
            f"{Emojis.SETTINGS} VOID Store — Painel de Configuração",
            "Selecione abaixo o que deseja configurar.\n\n"
            f"{Emojis.TICKET} **Tickets** — Categoria e canais de log de tickets\n"
            f"{Emojis.CROWN} **Cargos** — IDs dos cargos de progressão\n"
            f"📜 **Logs** — Canais de log de moderação e pedidos\n"
            f"{Emojis.INFO} **Ver Configurações** — Visualize o que está salvo\n\n"
            f"*Todas as configurações são salvas no banco de dados.*"
        )

        view = SetupView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        logger.info(f"Setup panel opened by {interaction.user}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Setup(bot))
