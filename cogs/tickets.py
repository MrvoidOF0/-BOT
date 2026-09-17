"""
🌑 VOID Store Bot - Sistema de Tickets
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime

from database.models import Ticket
from utils.embeds import VoidEmbeds
from utils.permissions import PermissionChecker
from utils.constants import TicketType, TicketStatus, Emojis
from utils.logger import logger
from config import config

class TicketButtons(discord.ui.View):
    """Botões do painel de tickets"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label="Compra",
        style=discord.ButtonStyle.green,
        emoji=Emojis.PURCHASE,
        custom_id="ticket:purchase"
    )
    async def purchase_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, TicketType.PURCHASE)
    
    @discord.ui.button(
        label="Serviço",
        style=discord.ButtonStyle.blurple,
        emoji=Emojis.SERVICE,
        custom_id="ticket:service"
    )
    async def service_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, TicketType.SERVICE)
    
    @discord.ui.button(
        label="Suporte",
        style=discord.ButtonStyle.gray,
        emoji=Emojis.SUPPORT,
        custom_id="ticket:support"
    )
    async def support_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, TicketType.SUPPORT)
    
    @discord.ui.button(
        label="Denúncia",
        style=discord.ButtonStyle.red,
        emoji=Emojis.REPORT,
        custom_id="ticket:report"
    )
    async def report_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, TicketType.REPORT)
    
    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        """Cria um ticket"""
        await interaction.response.defer(ephemeral=True)
        
        # Obter cog de tickets
        cog = interaction.client.get_cog("Tickets")
        if not cog:
            await interaction.followup.send(
                "❌ Sistema de tickets não disponível.",
                ephemeral=True
            )
            return
        
        await cog.handle_ticket_creation(interaction, ticket_type)

class TicketControlButtons(discord.ui.View):
    """Botões de controle dentro do ticket"""
    
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        label="Fechar",
        style=discord.ButtonStyle.red,
        emoji=Emojis.CLOSE,
        custom_id="ticket_control:close"
    )
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.close_ticket_confirm(interaction)
    
    @discord.ui.button(
        label="Assumir",
        style=discord.ButtonStyle.green,
        emoji="🙋",
        custom_id="ticket_control:claim"
    )
    async def claim_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.claim_ticket(interaction)
    
    @discord.ui.button(
        label="Adicionar",
        style=discord.ButtonStyle.blurple,
        emoji="➕",
        custom_id="ticket_control:add"
    )
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.add_user_modal(interaction)
    
    @discord.ui.button(
        label="Remover",
        style=discord.ButtonStyle.gray,
        emoji="➖",
        custom_id="ticket_control:remove"
    )
    async def remove_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Tickets")
        if cog:
            await cog.remove_user_modal(interaction)

class CloseConfirmView(discord.ui.View):
    """Confirmação de fechamento de ticket"""
    
    def __init__(self):
        super().__init__(timeout=60)
        self.value = None
    
    @discord.ui.button(label="Confirmar", style=discord.ButtonStyle.red, emoji=Emojis.SUCCESS)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        await interaction.response.defer()
    
    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.gray, emoji=Emojis.ERROR)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        await interaction.response.defer()

class AddUserModal(discord.ui.Modal, title="Adicionar Usuário"):
    """Modal para adicionar usuário ao ticket"""
    
    user_input = discord.ui.TextInput(
        label="ID ou Menção do Usuário",
        placeholder="123456789012345678 ou @usuario",
        required=True,
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        self.user_id = self.user_input.value.strip()
        await interaction.response.defer()

class RemoveUserModal(discord.ui.Modal, title="Remover Usuário"):
    """Modal para remover usuário do ticket"""
    
    user_input = discord.ui.TextInput(
        label="ID ou Menção do Usuário",
        placeholder="123456789012345678 ou @usuario",
        required=True,
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        self.user_id = self.user_input.value.strip()
        await interaction.response.defer()

class Tickets(commands.Cog):
    """Sistema completo de tickets"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        
        # Registrar views persistentes
        self.bot.add_view(TicketButtons())
        self.bot.add_view(TicketControlButtons())
    
    @app_commands.command(name="ticket-panel", description="📋 Cria o painel de tickets")
    @app_commands.checks.has_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        """Cria o painel de tickets"""
        
        # Verificar permissão de admin
        if not await PermissionChecker.check_interaction_permissions(interaction, require_admin=True):
            return
        
        # Criar embed
        embed = VoidEmbeds.ticket_panel()
        
        # Criar view com botões
        view = TicketButtons()
        
        # Enviar painel
        await interaction.channel.send(embed=embed, view=view)
        
        await interaction.response.send_message(
            f"{Emojis.SUCCESS} Painel de tickets criado!",
            ephemeral=True
        )
        
        logger.info(f"Ticket panel created by {interaction.user}")
    
    async def handle_ticket_creation(self, interaction: discord.Interaction, ticket_type: str):
        """Processa a criação de um ticket"""
        
        # Verificar se já tem ticket aberto deste tipo
        existing_ticket = await self.db.get_user_ticket(interaction.user.id, ticket_type)
        
        if existing_ticket:
            channel = interaction.guild.get_channel(existing_ticket.channel_id)
            if channel:
                await interaction.followup.send(
                    f"{Emojis.WARNING} Você já possui um ticket de {TicketType.get_name(ticket_type)} aberto: {channel.mention}",
                    ephemeral=True
                )
                return
        
        # Verificar categoria configurada
        if not config.TICKET_CATEGORY_ID:
            await interaction.followup.send(
                f"{Emojis.ERROR} Categoria de tickets não configurada. Use `/setup` primeiro.",
                ephemeral=True
            )
            return
        
        category = interaction.guild.get_channel(config.TICKET_CATEGORY_ID)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send(
                f"{Emojis.ERROR} Categoria de tickets inválida. Verifique a configuração.",
                ephemeral=True
            )
            return
        
        try:
            # Criar canal do ticket
            ticket_name = f"{TicketType.get_emoji(ticket_type)}-{interaction.user.name}".lower()
            
            # Configurar permissões
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    attach_files=True,
                    embed_links=True
                ),
                interaction.guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_channels=True,
                    manage_permissions=True
                )
            }
            
            # Adicionar staff/admin às permissões
            if config.STAFF_ROLE_ID:
                staff_role = interaction.guild.get_role(config.STAFF_ROLE_ID)
                if staff_role:
                    overwrites[staff_role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True
                    )
            
            if config.ADMIN_ROLE_ID:
                admin_role = interaction.guild.get_role(config.ADMIN_ROLE_ID)
                if admin_role:
                    overwrites[admin_role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        manage_channels=True
                    )
            
            # Criar canal
            ticket_channel = await category.create_text_channel(
                name=ticket_name,
                overwrites=overwrites,
                topic=f"Ticket de {TicketType.get_name(ticket_type)} - {interaction.user}"
            )
            
            # Criar registro no banco
            ticket = Ticket(
                channel_id=ticket_channel.id,
                creator_id=interaction.user.id,
                creator_name=str(interaction.user),
                ticket_type=ticket_type,
                status=TicketStatus.OPEN
            )
            
            await self.db.create_ticket(ticket)
            
            # Criar embed de boas-vindas
            welcome_embed = VoidEmbeds.ticket_created(ticket_type, interaction.user)
            
            # Criar botões de controle
            control_view = TicketControlButtons()
            
            # Enviar mensagem no ticket
            await ticket_channel.send(
                content=f"{interaction.user.mention}",
                embed=welcome_embed,
                view=control_view
            )
            
            # Confirmar criação
            await interaction.followup.send(
                f"{Emojis.SUCCESS} Ticket criado: {ticket_channel.mention}",
                ephemeral=True
            )
            
            # Log
            await self.db.create_log(
                "ticket",
                interaction.user.id,
                "created",
                f"Type: {ticket_type} | Channel: {ticket_channel.id}"
            )
            
            logger.info(f"Ticket created: {ticket_type} by {interaction.user} in {ticket_channel}")
            
            # Enviar log se configurado
            await self.send_ticket_log(
                interaction.guild,
                f"{Emojis.TICKET} **Ticket Criado**",
                f"**Usuário:** {interaction.user.mention}\n"
                f"**Tipo:** {TicketType.get_name(ticket_type)}\n"
                f"**Canal:** {ticket_channel.mention}"
            )
            
        except discord.Forbidden:
            await interaction.followup.send(
                f"{Emojis.ERROR} Não tenho permissão para criar canais.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            await interaction.followup.send(
                f"{Emojis.ERROR} Erro ao criar ticket. Tente novamente.",
                ephemeral=True
            )
    
    async def close_ticket_confirm(self, interaction: discord.Interaction):
        """Solicita confirmação para fechar ticket"""
        
        # Verificar se é um canal de ticket
        ticket = await self.db.get_ticket_by_channel(interaction.channel.id)
        
        if not ticket:
            await interaction.response.send_message(
                f"{Emojis.ERROR} Este não é um canal de ticket.",
                ephemeral=True
            )
            return
        
        # Verificar permissão
        is_creator = interaction.user.id == ticket.creator_id
        is_staff = PermissionChecker.is_staff(interaction.user)
        
        if not (is_creator or is_staff):
            await interaction.response.send_message(
                f"{Emojis.ERROR} Você não tem permissão para fechar este ticket.",
                ephemeral=True
            )
            return
        
        # Pedir confirmação
        view = CloseConfirmView()
        
        await interaction.response.send_message(
            f"{Emojis.WARNING} Tem certeza que deseja fechar este ticket?",
            view=view,
            ephemeral=True
        )
        
        # Aguardar resposta
        await view.wait()
        
        if view.value:
            await self.close_ticket(interaction, ticket)
        else:
            await interaction.edit_original_response(
                content=f"{Emojis.INFO} Fechamento cancelado.",
                view=None
            )
    
    async def close_ticket(self, interaction: discord.Interaction, ticket: Ticket):
        """Fecha um ticket"""
        
        try:
            # Atualizar banco
            await self.db.close_ticket(interaction.channel.id)
            
            # Mensagem de fechamento
            embed = VoidEmbeds.info(
                "Ticket Fechado",
                f"Este ticket foi fechado por {interaction.user.mention}.\n"
                f"O canal será deletado em 5 segundos."
            )
            
            await interaction.channel.send(embed=embed)
            
            # Log
            await self.db.create_log(
                "ticket",
                interaction.user.id,
                "closed",
                f"Ticket: {ticket.ticket_type} | Channel: {interaction.channel.id}"
            )
            
            logger.info(f"Ticket closed by {interaction.user}: {interaction.channel}")
            
            # Enviar log
            await self.send_ticket_log(
                interaction.guild,
                f"{Emojis.CLOSE} **Ticket Fechado**",
                f"**Canal:** {interaction.channel.name}\n"
                f"**Tipo:** {TicketType.get_name(ticket.ticket_type)}\n"
                f"**Fechado por:** {interaction.user.mention}\n"
                f"**Criador:** <@{ticket.creator_id}>"
            )
            
            # Aguardar e deletar canal
            await asyncio.sleep(5)
            await interaction.channel.delete()
            
        except Exception as e:
            logger.error(f"Error closing ticket: {e}")
            await interaction.followup.send(
                f"{Emojis.ERROR} Erro ao fechar ticket.",
                ephemeral=True
            )
    
    async def claim_ticket(self, interaction: discord.Interaction):
        """Staff assume o ticket"""
        
        # Verificar se é staff
        if not PermissionChecker.is_staff(interaction.user):
            await interaction.response.send_message(
                f"{Emojis.ERROR} Apenas staff pode assumir tickets.",
                ephemeral=True
            )
            return
        
        # Verificar se é ticket
        ticket = await self.db.get_ticket_by_channel(interaction.channel.id)
        
        if not ticket:
            await interaction.response.send_message(
                f"{Emojis.ERROR} Este não é um canal de ticket.",
                ephemeral=True
            )
            return
        
        # Atualizar ticket
        await self.db.claim_ticket(interaction.channel.id, interaction.user.id)
        
        # Confirmar
        embed = VoidEmbeds.success(
            "Ticket Assumido",
            f"{interaction.user.mention} assumiu este ticket."
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Log
        await self.db.create_log(
            "ticket",
            interaction.user.id,
            "claimed",
            f"Channel: {interaction.channel.id}"
        )
        
        logger.info(f"Ticket claimed by {interaction.user}: {interaction.channel}")
    
    async def add_user_modal(self, interaction: discord.Interaction):
        """Mostra modal para adicionar usuário"""
        
        # Verificar permissão
        if not PermissionChecker.is_staff(interaction.user):
            await interaction.response.send_message(
                f"{Emojis.ERROR} Apenas staff pode adicionar usuários.",
                ephemeral=True
            )
            return
        
        modal = AddUserModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        # Processar ID
        user_id_str = modal.user_id.replace("<@", "").replace(">", "").replace("!", "")
        
        try:
            user_id = int(user_id_str)
            member = interaction.guild.get_member(user_id)
            
            if not member:
                await interaction.followup.send(
                    f"{Emojis.ERROR} Usuário não encontrado.",
                    ephemeral=True
                )
                return
            
            # Adicionar permissão ao canal
            await interaction.channel.set_permissions(
                member,
                read_messages=True,
                send_messages=True
            )
            
            await interaction.followup.send(
                f"{Emojis.SUCCESS} {member.mention} adicionado ao ticket.",
                ephemeral=True
            )
            
            await interaction.channel.send(
                f"{member.mention} foi adicionado ao ticket por {interaction.user.mention}."
            )
            
            logger.info(f"User {member} added to ticket by {interaction.user}")
            
        except ValueError:
            await interaction.followup.send(
                f"{Emojis.ERROR} ID inválido.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error adding user to ticket: {e}")
            await interaction.followup.send(
                f"{Emojis.ERROR} Erro ao adicionar usuário.",
                ephemeral=True
            )
    
    async def remove_user_modal(self, interaction: discord.Interaction):
        """Mostra modal para remover usuário"""
        
        # Verificar permissão
        if not PermissionChecker.is_staff(interaction.user):
            await interaction.response.send_message(
                f"{Emojis.ERROR} Apenas staff pode remover usuários.",
                ephemeral=True
            )
            return
        
        modal = RemoveUserModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        # Processar ID
        user_id_str = modal.user_id.replace("<@", "").replace(">", "").replace("!", "")
        
        try:
            user_id = int(user_id_str)
            member = interaction.guild.get_member(user_id)
            
            if not member:
                await interaction.followup.send(
                    f"{Emojis.ERROR} Usuário não encontrado.",
                    ephemeral=True
                )
                return
            
            # Remover permissão do canal
            await interaction.channel.set_permissions(member, overwrite=None)
            
            await interaction.followup.send(
                f"{Emojis.SUCCESS} {member.mention} removido do ticket.",
                ephemeral=True
            )
            
            await interaction.channel.send(
                f"{member.mention} foi removido do ticket por {interaction.user.mention}."
            )
            
            logger.info(f"User {member} removed from ticket by {interaction.user}")
            
        except ValueError:
            await interaction.followup.send(
                f"{Emojis.ERROR} ID inválido.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error removing user from ticket: {e}")
            await interaction.followup.send(
                f"{Emojis.ERROR} Erro ao remover usuário.",
                ephemeral=True
            )
    
    async def send_ticket_log(self, guild: discord.Guild, title: str, description: str):
        """Envia log de ticket"""
        
        log_channel_id = config.TICKET_LOG_CHANNEL_ID or config.LOG_CHANNEL_ID
        
        if not log_channel_id:
            return
        
        log_channel = guild.get_channel(log_channel_id)
        
        if not log_channel:
            return
        
        embed = VoidEmbeds.default(title, description)
        
        try:
            await log_channel.send(embed=embed)
        except:
            pass

async def setup(bot: commands.Bot):
    """Setup function para carregar o cog"""
    await bot.add_cog(Tickets(bot))
