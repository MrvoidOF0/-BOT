"""
🌑 VOID Store Bot - Sistema de Tickets CORRIGIDO
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio

from database.models import Ticket
from utils.embeds import VoidEmbeds
from utils.permissions import PermissionChecker
from utils.constants import TicketType, TicketStatus, Emojis
from utils.logger import logger
from config import config


# ====================================
# VIEW DE CONTROLE DO TICKET
# ====================================

class TicketControlView(discord.ui.View):
    """Botões dentro do ticket — persistentes"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Ticket",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="void_ticket:close"
    )
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.iniciar_fechamento(interaction)

    @discord.ui.button(
        label="Assumir",
        style=discord.ButtonStyle.green,
        emoji="🙋",
        custom_id="void_ticket:claim"
    )
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.assumir_ticket(interaction)

    @discord.ui.button(
        label="Adicionar",
        style=discord.ButtonStyle.blurple,
        emoji="➕",
        custom_id="void_ticket:add"
    )
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.adicionar_usuario(interaction)

    @discord.ui.button(
        label="Remover",
        style=discord.ButtonStyle.gray,
        emoji="➖",
        custom_id="void_ticket:remove"
    )
    async def remove_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.remover_usuario(interaction)


class ConfirmarFechamentoView(discord.ui.View):
    """Confirmação de fechamento"""

    def __init__(self):
        super().__init__(timeout=60)
        self.confirmado = False

    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.red, emoji="✅")
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmado = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.gray, emoji="❌")
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.confirmado = False
        self.stop()
        await interaction.response.defer()


class TicketPanelView(discord.ui.View):
    """Painel de abertura de tickets"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Compra",
        style=discord.ButtonStyle.green,
        emoji="🛒",
        custom_id="void_panel:purchase"
    )
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.abrir_ticket(interaction, "purchase")

    @discord.ui.button(
        label="Suporte",
        style=discord.ButtonStyle.blurple,
        emoji="💬",
        custom_id="void_panel:support"
    )
    async def support(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.abrir_ticket(interaction, "support")

    @discord.ui.button(
        label="Denúncia",
        style=discord.ButtonStyle.red,
        emoji="🚨",
        custom_id="void_panel:report"
    )
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.abrir_ticket(interaction, "report")


class AddUserModal(discord.ui.Modal, title="Adicionar Usuário"):
    user_input = discord.ui.TextInput(
        label="ID do Usuário",
        placeholder="Cole o ID numérico do usuário",
        required=True,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()


class RemoveUserModal(discord.ui.Modal, title="Remover Usuário"):
    user_input = discord.ui.TextInput(
        label="ID do Usuário",
        placeholder="Cole o ID numérico do usuário",
        required=True,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()


class Tickets(commands.Cog):
    """Sistema de tickets corrigido"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.bot.add_view(TicketPanelView())
        self.bot.add_view(TicketControlView())

    @app_commands.command(name="ticket-panel", description="🎫 Cria o painel de atendimento")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌑 VOID Store | Central de Atendimento",
            description=(
                "Selecione o tipo de atendimento desejado:\n\n"
                "🛒 **Compra** — Realizar uma compra\n"
                "💬 **Suporte** — Tirar dúvidas\n"
                "🚨 **Denúncia** — Reportar um problema"
            ),
            color=0x000000
        )
        embed.set_footer(text="🌑 VOID Store")

        await interaction.channel.send(embed=embed, view=TicketPanelView())
        await interaction.response.send_message("✅ Painel criado!", ephemeral=True)

    async def abrir_ticket(self, interaction: discord.Interaction, tipo: str):
        """Abre um ticket"""

        await interaction.response.defer(ephemeral=True)

        # Verificar duplicado
        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            await interaction.followup.send(
                "❌ Categoria de tickets não configurada. Use `/setup`.",
                ephemeral=True
            )
            return

        category = interaction.guild.get_channel(category_id)
        if not category:
            await interaction.followup.send("❌ Categoria não encontrada.", ephemeral=True)
            return

        # Verificar se já tem ticket do mesmo tipo
        nome_prefixo = f"ticket-{tipo}-{interaction.user.name}".lower()[:50]
        for ch in category.text_channels:
            if ch.name == nome_prefixo:
                await interaction.followup.send(
                    f"⚠️ Você já tem um ticket aberto: {ch.mention}",
                    ephemeral=True
                )
                return

        try:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    attach_files=True
                ),
                interaction.guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_channels=True,
                    manage_permissions=True
                )
            }

            if config.STAFF_ROLE_ID:
                role = interaction.guild.get_role(config.STAFF_ROLE_ID)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True
                    )

            channel = await category.create_text_channel(
                name=nome_prefixo,
                overwrites=overwrites
            )

            nomes = {"purchase": "Compra", "support": "Suporte", "report": "Denúncia"}
            emojis = {"purchase": "🛒", "support": "💬", "report": "🚨"}

            embed = discord.Embed(
                title=f"{emojis[tipo]} Ticket de {nomes[tipo]}",
                description=(
                    f"Olá {interaction.user.mention}!\n\n"
                    f"Seu ticket foi criado. A equipe responderá em breve.\n"
                    f"Por favor, descreva sua necessidade."
                ),
                color=0x000000,
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text="🌑 VOID Store")

            await channel.send(
                content=f"{interaction.user.mention}",
                embed=embed,
                view=TicketControlView()
            )

            await interaction.followup.send(
                f"✅ Ticket criado: {channel.mention}",
                ephemeral=True
            )

            # Salvar no banco
            ticket = Ticket(
                channel_id=channel.id,
                creator_id=interaction.user.id,
                creator_name=str(interaction.user),
                ticket_type=tipo,
                status="open"
            )
            await self.db.create_ticket(ticket)

        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Sem permissão para criar canais.", ephemeral=True
            )
        except Exception as e:
            logger.error(f"Erro ao criar ticket: {e}")
            await interaction.followup.send("❌ Erro ao criar ticket.", ephemeral=True)

    async def iniciar_fechamento(self, interaction: discord.Interaction):
        """Inicia o processo de fechar o ticket"""

        # Verificar se é ticket
        ticket = await self.db.get_ticket_by_channel(interaction.channel.id)
        is_staff = PermissionChecker.is_staff(interaction.user)
        is_creator = ticket and ticket.creator_id == interaction.user.id

        if not (is_staff or is_creator):
            await interaction.response.send_message(
                "❌ Você não pode fechar este ticket.", ephemeral=True
            )
            return

        # Pedir confirmação
        view = ConfirmarFechamentoView()
        await interaction.response.send_message(
            "⚠️ **Tem certeza que deseja fechar este ticket?**",
            view=view,
            ephemeral=True
        )

        await view.wait()

        if view.confirmado:
            await self._fechar_canal(interaction)
        else:
            await interaction.edit_original_response(
                content="❌ Fechamento cancelado.",
                view=None
            )

    async def _fechar_canal(self, interaction: discord.Interaction):
        """Fecha e deleta o canal do ticket"""

        try:
            # Avisar no canal
            embed = discord.Embed(
                title="🔒 Ticket Fechado",
                description=(
                    f"Este ticket foi fechado por {interaction.user.mention}.\n"
                    "O canal será deletado em **5 segundos**."
                ),
                color=0xff0000,
                timestamp=discord.utils.utcnow()
            )

            # Editar resposta original
            await interaction.edit_original_response(
                content="✅ Ticket fechado com sucesso.",
                view=None
            )

            # Enviar aviso no canal
            await interaction.channel.send(embed=embed)

            # Atualizar banco
            await self.db.close_ticket(interaction.channel.id)

            # Log
            await self.db.create_log(
                "ticket",
                interaction.user.id,
                "closed",
                f"Channel: {interaction.channel.id}"
            )

            # Aguardar e deletar
            await asyncio.sleep(5)
            await interaction.channel.delete(reason=f"Ticket fechado por {interaction.user}")

        except discord.NotFound:
            pass  # Canal já foi deletado
        except discord.Forbidden:
            logger.error("Sem permissão para deletar o canal do ticket")
        except Exception as e:
            logger.error(f"Erro ao fechar ticket: {e}")

    async def assumir_ticket(self, interaction: discord.Interaction):
        if not PermissionChecker.is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas staff pode assumir tickets.", ephemeral=True
            )
            return

        await self.db.claim_ticket(interaction.channel.id, interaction.user.id)

        embed = discord.Embed(
            description=f"✅ {interaction.user.mention} assumiu este ticket.",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)

    async def adicionar_usuario(self, interaction: discord.Interaction):
        if not PermissionChecker.is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas staff pode adicionar usuários.", ephemeral=True
            )
            return

        modal = AddUserModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        try:
            uid = int(modal.user_input.value.strip())
            member = interaction.guild.get_member(uid)
            if not member:
                await interaction.followup.send("❌ Usuário não encontrado.", ephemeral=True)
                return

            await interaction.channel.set_permissions(
                member,
                read_messages=True,
                send_messages=True
            )
            await interaction.followup.send(f"✅ {member.mention} adicionado.", ephemeral=True)
            await interaction.channel.send(f"➕ {member.mention} foi adicionado ao ticket.")

        except ValueError:
            await interaction.followup.send("❌ ID inválido.", ephemeral=True)

    async def remover_usuario(self, interaction: discord.Interaction):
        if not PermissionChecker.is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas staff pode remover usuários.", ephemeral=True
            )
            return

        modal = RemoveUserModal()
        await interaction.response.send_modal(modal)
        await modal.wait()

        try:
            uid = int(modal.user_input.value.strip())
            member = interaction.guild.get_member(uid)
            if not member:
                await interaction.followup.send("❌ Usuário não encontrado.", ephemeral=True)
                return

            await interaction.channel.set_permissions(member, overwrite=None)
            await interaction.followup.send(f"✅ {member.mention} removido.", ephemeral=True)
            await interaction.channel.send(f"➖ {member.mention} foi removido do ticket.")

        except ValueError:
            await interaction.followup.send("❌ ID inválido.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
