"""
🌑 VOID Store Bot - Sistema de Tickets por Serviço Específico
Engrenagem V4, Frutas, Levels, Fragmentos, Money, Farm de Materiais
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
# CONFIGURAÇÃO DOS SERVIÇOS
# ====================================

SERVICES = {
    "engrenagem_v4": {
        "name": "⚙️ Engrenagem V4",
        "description": "Farm completo de Engrenagem V4",
        "emoji": "⚙️",
        "color": 0x2b2d31,
        "price_range": "R$ 25,00 - R$ 35,00"
    },
    "frutas": {
        "name": "🍎 Frutas",
        "description": "Compra/venda de frutas do Blox Fruits",
        "emoji": "🍎",
        "color": 0x9b59b6,
        "price_range": "R$ 10,00 - R$ 50,00"
    },
    "levels": {
        "name": "⬆️ Levels",
        "description": "Level up no seu personagem",
        "emoji": "⬆️",
        "color": 0x3498db,
        "price_range": "R$ 15,00 - R$ 30,00"
    },
    "fragmentos": {
        "name": "💎 Fragmentos",
        "description": "Farm de fragmentos para raças",
        "emoji": "💎",
        "color": 0xe74c3c,
        "price_range": "R$ 10,00 - R$ 20,00"
    },
    "money": {
        "name": "💰 Money / Beli",
        "description": "Farm de dinheiro no jogo",
        "emoji": "💰",
        "color": 0xf39c12,
        "price_range": "R$ 8,00 - R$ 15,00"
    },
    "farm_materiais": {
        "name": "📦 Farm de Materiais",
        "description": "Farm de espadas, acessórios e itens",
        "emoji": "📦",
        "color": 0x27ae60,
        "price_range": "R$ 20,00 - R$ 40,00"
    }
}


# ====================================
# VIEW DO PAINEL DE SERVIÇOS
# ====================================

class ServicePanelView(discord.ui.View):
    """Painel com botões para cada serviço"""
    
    def __init__(self):
        super().__init__(timeout=None)
        
        for service_id, service_data in SERVICES.items():
            button = discord.ui.Button(
                label=service_data["name"],
                style=discord.ButtonStyle.blurple,
                emoji=service_data["emoji"],
                custom_id=f"service_open:{service_id}"
            )
            button.callback = self.create_service_callback(service_id, service_data)
            self.add_item(button)
    
    def create_service_callback(self, service_id: str, service_data: dict):
        async def callback(interaction: discord.Interaction):
            cog = interaction.client.get_cog("Services")
            if cog:
                await cog.open_service_ticket(interaction, service_id, service_data)
        return callback


# ====================================
# COG
# ====================================

class Services(commands.Cog):
    """Sistema de tickets por serviço específico"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        
        self.bot.add_view(ServicePanelView())
    
    @app_commands.command(name="servicos-painel", description="⚙️ Cria o painel de serviços")
    @app_commands.checks.has_permissions(administrator=True)
    async def services_panel(self, interaction: discord.Interaction):
        """Cria o painel de serviços no canal atual"""
        
        if not await PermissionChecker.check_interaction_permissions(interaction, require_admin=True):
            return
        
        embed = discord.Embed(
            title=f"{Emojis.VOID} 𝐕𝐎𝐈𝐃 𝐒𝐭𝐨𝐫𝐞 | Serviços",
            description=(
                "Escolha o serviço desejado abaixo.\n"
                "Um ticket privado será criado para atendimento exclusivo.\n\n"
                f"{Emojis.INFO} **Como funciona:**\n"
                f"1. Clique no botão do serviço\n"
                f"2. Descreva sua necessidade no ticket\n"
                f"3. Nossa equipe irá te atender\n"
                f"4. Pagamento via PIX\n"
                f"5. Entrega do serviço"
            ),
            color=0x000000,
            timestamp=discord.utils.utcnow()
        )
        
        services_list = ""
        for service_id, data in SERVICES.items():
            services_list += f"{data['emoji']} **{data['name']}** — {data['price_range']}\n"
        
        embed.add_field(name="🛠️ Serviços Disponíveis", value=services_list, inline=False)
        embed.set_footer(text="🌑 VOID Store | Atendimento rápido e seguro")
        
        view = ServicePanelView()
        
        await interaction.channel.send(embed=embed, view=view)
        
        await interaction.response.send_message(
            f"{Emojis.SUCCESS} Painel de serviços criado!",
            ephemeral=True
        )
        
        logger.info(f"Services panel created by {interaction.user}")
    
    async def open_service_ticket(self, interaction: discord.Interaction, service_id: str, service_data: dict):
        """Abre ticket para serviço específico"""
        
        await interaction.response.defer(ephemeral=True)
        
        # Verificar ticket duplicado
        existing = await self._find_user_service_ticket(interaction.user, interaction.guild, service_id)
        
        if existing:
            await interaction.followup.send(
                f"{Emojis.WARNING} Você já possui um ticket aberto para **{service_data['name']}**: {existing.mention}",
                ephemeral=True
            )
            return
        
        # Criar canal
        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            await interaction.followup.send(
                f"{Emojis.ERROR} Categoria não configurada. Use `/setup`.",
                ephemeral=True
            )
            return
        
        category = interaction.guild.get_channel(category_id)
        if not category:
            await interaction.followup.send(
                f"{Emojis.ERROR} Categoria não encontrada.",
                ephemeral=True
            )
            return
        
        try:
            channel_name = f"servico-{service_id}-{interaction.user.name}".lower()[:50]
            
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
                    manage_channels=True
                )
            }
            
            if config.STAFF_ROLE_ID:
                staff_role = interaction.guild.get_role(config.STAFF_ROLE_ID)
                if staff_role:
                    overwrites[staff_role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True
                    )
            
            channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic=f"Serviço: {service_data['name']} | Cliente: {interaction.user}"
            )
            
            embed = discord.Embed(
                title=f"{service_data['emoji']} {service_data['name']}",
                description=(
                    f"Olá {interaction.user.mention}!\n\n"
                    f"Seu ticket para **{service_data['name']}** foi criado.\n\n"
                    f"📝 **Descrição:** {service_data['description']}\n"
                    f"💰 **Faixa de preço:** {service_data['price_range']}\n\n"
                    f"---\n\n"
                    f"📋 **Por favor, informe:**\n"
                    f"• Seu nome no jogo (IGN)\n"
                    f"• O que exatamente você precisa\n"
                    f"• Seu nível atual (se aplicável)\n"
                    f"• Qualquer outra informação relevante\n\n"
                    f"⏱️ Nossa equipe responderá em breve!"
                ),
                color=service_data['color'],
                timestamp=discord.utils.utcnow()
            )
            
            # Botões de controle
            control_view = discord.ui.View()
            
            close_btn = discord.ui.Button(
                label="🔒 Fechar Ticket",
                style=discord.ButtonStyle.red,
                emoji=Emojis.CLOSE,
                custom_id=f"service_close:{interaction.user.id}:{service_id}"
            )
            control_view.add_item(close_btn)
            
            await channel.send(
                content=f"{interaction.user.mention} {config.STAFF_ROLE_ID and f'<@&{config.STAFF_ROLE_ID}>'}",
                embed=embed,
                view=control_view
            )
            
            await interaction.followup.send(
                f"{Emojis.SUCCESS} Ticket criado: {channel.mention}",
                ephemeral=True
            )
            
            # Log
            await self.db.create_log(
                "service",
                interaction.user.id,
                "ticket_created",
                f"Service: {service_id} | Channel: {channel.id}"
            )
            
            logger.info(f"Service ticket created: {service_id} by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error creating service ticket: {e}")
            await interaction.followup.send(
                f"{Emojis.ERROR} Erro ao criar ticket.",
                ephemeral=True
            )
    
    async def _find_user_service_ticket(self, user: discord.Member, guild: discord.Guild, service_id: str) -> Optional[discord.TextChannel]:
        """Procura ticket de serviço aberto do usuário"""
        
        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            return None
        
        category = guild.get_channel(category_id)
        if not category:
            return None
        
        for channel in category.text_channels:
            if channel.name.startswith(f"servico-{service_id}-"):
                return channel
        
        return None


async def setup(bot: commands.Bot):
    await bot.add_cog(Services(bot))
