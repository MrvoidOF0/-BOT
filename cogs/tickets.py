"""
🌑 VOID Store Bot - Tickets (Reescrito)
Usa on_interaction ao invés de Views persistentes.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio

from database.models import Ticket
from utils.permissions import PermissionChecker
from utils.logger import logger
from config import config


class AddUserModal(discord.ui.Modal, title="Adicionar Usuário"):
    user_id_input = discord.ui.TextInput(
        label="ID do Usuário",
        placeholder="Cole o ID numérico aqui",
        required=True,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog._adicionar_usuario(interaction, self.user_id_input.value)


class RemoveUserModal(discord.ui.Modal, title="Remover Usuário"):
    user_id_input = discord.ui.TextInput(
        label="ID do Usuário",
        placeholder="Cole o ID numérico aqui",
        required=True,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog._remover_usuario(interaction, self.user_id_input.value)


class Tickets(commands.Cog):
    """Sistema de tickets"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    # ====================================
    # PAINEL
    # ====================================

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

        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="Compra", style=discord.ButtonStyle.green,
            emoji="🛒", custom_id="panel:compra"
        ))
        view.add_item(discord.ui.Button(
            label="Suporte", style=discord.ButtonStyle.blurple,
            emoji="💬", custom_id="panel:suporte"
        ))
        view.add_item(discord.ui.Button(
            label="Denúncia", style=discord.ButtonStyle.red,
            emoji="🚨", custom_id="panel:denuncia"
        ))

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel criado!", ephemeral=True)

    # ====================================
    # ABRIR TICKET
    # ====================================

    async def abrir_ticket(self, interaction: discord.Interaction, tipo: str):
        """Abre canal de ticket"""

        await interaction.response.defer(ephemeral=True)

        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            await interaction.followup.send(
                "❌ Categoria não configurada. Use `/setup`.", ephemeral=True
            )
            return

        category = interaction.guild.get_channel(category_id)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send("❌ Categoria inválida.", ephemeral=True)
            return

        nomes = {"compra": "🛒 Compra", "suporte": "💬 Suporte", "denuncia": "🚨 Denúncia"}
        channel_name = f"ticket-{tipo}-{interaction.user.name}".lower()[:50]

        for ch in category.text_channels:
            if ch.name == channel_name:
                await interaction.followup.send(
                    f"⚠️ Você já tem um ticket aberto: {ch.mention}", ephemeral=True
                )
                return

        try:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True, manage_permissions=True),
            }

            if config.STAFF_ROLE_ID:
                r = interaction.guild.get_role(config.STAFF_ROLE_ID)
                if r:
                    overwrites[r] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            for rid in config.AUTHORIZED_ROLE_IDS:
                r = interaction.guild.get_role(rid)
                if r:
                    overwrites[r] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic=f"Ticket {tipo} | {interaction.user.id}"
            )

            embed = discord.Embed(
                title=f"{nomes.get(tipo, 'Ticket')}",
                description=(
                    f"Olá {interaction.user.mention}!\n\n"
                    f"Seu ticket foi criado com sucesso.\n"
                    f"Descreva sua necessidade e a equipe responderá em breve."
                ),
                color=0x000000,
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text="🌑 VOID Store")

            view = discord.ui.View()
            view.add_item(discord.ui.Button(
                label="Fechar Ticket", style=discord.ButtonStyle.red,
                emoji="🔒", custom_id="ticket:fechar"
            ))
            view.add_item(discord.ui.Button(
                label="Assumir", style=discord.ButtonStyle.green,
                emoji="🙋", custom_id="ticket:assumir"
            ))
            view.add_item(discord.ui.Button(
                label="Adicionar", style=discord.ButtonStyle.blurple,
                emoji="➕", custom_id="ticket:adicionar"
            ))
            view.add_item(discord.ui.Button(
                label="Remover", style=discord.ButtonStyle.gray,
                emoji="➖", custom_id="ticket:remover"
            ))

            staff_mention = f"<@&{config.STAFF_ROLE_ID}>" if config.STAFF_ROLE_ID else ""

            await channel.send(
                content=f"{interaction.user.mention} {staff_mention}",
                embed=embed,
                view=view
            )

            await interaction.followup.send(
                f"✅ Ticket criado: {channel.mention}", ephemeral=True
            )

            ticket = Ticket(
                channel_id=channel.id,
                creator_id=interaction.user.id,
                creator_name=str(interaction.user),
                ticket_type=tipo,
                status="open"
            )
            await self.db.create_ticket(ticket)

            logger.info(f"Ticket criado: {channel.name} por {interaction.user}")

        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão para criar canais.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro criar ticket: {e}")
            await interaction.followup.send("❌ Erro ao criar ticket.", ephemeral=True)

    # ====================================
    # HANDLERS DOS BOTÕES
    # ====================================

    async def handle_fechar(self, interaction: discord.Interaction):
        """Fechar ticket"""

        ticket = await self.db.get_ticket_by_channel(interaction.channel.id)
        is_staff = PermissionChecker.is_staff(interaction.user)
        is_creator = ticket and ticket.creator_id == interaction.user.id

        if not (is_staff or is_creator):
            await interaction.response.send_message(
                "❌ Você não pode fechar este ticket.", ephemeral=True
            )
            return

        view = discord.ui.View()
        btn_sim = discord.ui.Button(label="Confirmar", style=discord.ButtonStyle.red)
        btn_nao = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.gray)
        confirmado = False

        async def sim(i: discord.Interaction):
            nonlocal confirmado
            confirmado = True
            view.stop()
            await i.response.defer()

        async def nao(i: discord.Interaction):
            view.stop()
            await i.response.defer()

        btn_sim.callback = sim
        btn_nao.callback = nao
        view.add_item(btn_sim)
        view.add_item(btn_nao)

        await interaction.response.send_message(
            "⚠️ **Fechar este ticket?**", view=view, ephemeral=True
        )
        await view.wait()

        if not confirmado:
            await interaction.edit_original_response(
                content="❌ Cancelado.", view=None
            )
            return

        try:
            await interaction.edit_original_response(
                content="✅ Fechando...", view=None
            )

            embed = discord.Embed(
                description=f"🔒 Ticket fechado por {interaction.user.mention}. Deletando em **5 segundos**...",
                color=0xff0000
            )
            await interaction.channel.send(embed=embed)

            await self.db.close_ticket(interaction.channel.id)
            await self.db.create_log(
                "ticket", interaction.user.id, "fechado",
                f"Channel: {interaction.channel.id}"
            )

            await asyncio.sleep(5)
            await interaction.channel.delete()

        except discord.NotFound:
            pass
        except Exception as e:
            logger.error(f"Erro fechar ticket: {e}")

    async def handle_assumir(self, interaction: discord.Interaction):
        if not PermissionChecker.is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas staff.", ephemeral=True
            )
            return
        await self.db.claim_ticket(interaction.channel.id, interaction.user.id)
        embed = discord.Embed(
            description=f"✅ {interaction.user.mention} assumiu este ticket.",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)

    async def handle_adicionar(self, interaction: discord.Interaction):
        if not PermissionChecker.is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas staff.", ephemeral=True
            )
            return
        await interaction.response.send_modal(AddUserModal())

    async def handle_remover(self, interaction: discord.Interaction):
        if not PermissionChecker.is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas staff.", ephemeral=True
            )
            return
        await interaction.response.send_modal(RemoveUserModal())

    async def _adicionar_usuario(self, interaction: discord.Interaction, uid_str: str):
        try:
            uid = int(uid_str.strip())
            member = interaction.guild.get_member(uid)
            if not member:
                await interaction.followup.send("❌ Usuário não encontrado.", ephemeral=True)
                return
            await interaction.channel.set_permissions(
                member, read_messages=True, send_messages=True
            )
            await interaction.followup.send(f"✅ {member.mention} adicionado.", ephemeral=True)
            await interaction.channel.send(f"➕ {member.mention} foi adicionado ao ticket.")
        except ValueError:
            await interaction.followup.send("❌ ID inválido.", ephemeral=True)

    async def _remover_usuario(self, interaction: discord.Interaction, uid_str: str):
        try:
            uid = int(uid_str.strip())
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
