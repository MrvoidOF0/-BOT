"""
🌑 VOID Store Bot - Embeds Padronizados
"""

import discord
from datetime import datetime
from typing import Optional, List
from .constants import Colors, Emojis

class VoidEmbeds:
    """Classe para criar embeds padronizados do VOID Store Bot"""
    
    @staticmethod
    def _get_footer() -> dict:
        """Retorna o footer padrão"""
        return {
            "text": "🌑 VOID Store",
            "icon_url": None  # Você pode adicionar URL de ícone aqui
        }
    
    @staticmethod
    def _get_timestamp() -> datetime:
        """Retorna timestamp atual"""
        return datetime.now()
    
    @classmethod
    def default(
        cls,
        title: str,
        description: str,
        color: int = Colors.VOID_PRIMARY
    ) -> discord.Embed:
        """
        Cria um embed padrão
        
        Args:
            title: Título do embed
            description: Descrição
            color: Cor do embed
            
        Returns:
            Embed configurado
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=cls._get_timestamp()
        )
        embed.set_footer(**cls._get_footer())
        return embed
    
    @classmethod
    def success(
        cls,
        title: str,
        description: str
    ) -> discord.Embed:
        """Embed de sucesso"""
        return cls.default(
            title=f"{Emojis.SUCCESS} {title}",
            description=description,
            color=Colors.SUCCESS
        )
    
    @classmethod
    def error(
        cls,
        title: str,
        description: str
    ) -> discord.Embed:
        """Embed de erro"""
        return cls.default(
            title=f"{Emojis.ERROR} {title}",
            description=description,
            color=Colors.ERROR
        )
    
    @classmethod
    def warning(
        cls,
        title: str,
        description: str
    ) -> discord.Embed:
        """Embed de aviso"""
        return cls.default(
            title=f"{Emojis.WARNING} {title}",
            description=description,
            color=Colors.WARNING
        )
    
    @classmethod
    def info(
        cls,
        title: str,
        description: str
    ) -> discord.Embed:
        """Embed informativo"""
        return cls.default(
            title=f"{Emojis.INFO} {title}",
            description=description,
            color=Colors.INFO
        )
    
    @classmethod
    def ticket_panel(cls) -> discord.Embed:
        """Embed do painel de tickets"""
        embed = discord.Embed(
            title=f"{Emojis.VOID} 𝐕𝐎𝐈𝐃 𝐒𝐭𝐨𝐫𝐞 | Central de Atendimento",
            description=(
                f"{Emojis.TICKET} **Central de Atendimento**\n\n"
                "Selecione abaixo o tipo de atendimento desejado:\n\n"
                f"{Emojis.PURCHASE} **Compra** - Realizar uma compra\n"
                f"{Emojis.SERVICE} **Serviço** - Solicitar um serviço\n"
                f"{Emojis.SUPPORT} **Suporte** - Tirar dúvidas\n"
                f"{Emojis.REPORT} **Denúncia** - Reportar problema"
            ),
            color=Colors.VOID_PRIMARY,
            timestamp=cls._get_timestamp()
        )
        embed.set_footer(**cls._get_footer())
        return embed
    
    @classmethod
    def ticket_created(
        cls,
        ticket_type: str,
        user: discord.Member
    ) -> discord.Embed:
        """Embed de ticket criado"""
        from .constants import TicketType
        
        embed = discord.Embed(
            title=f"{TicketType.get_emoji(ticket_type)} Ticket de {TicketType.get_name(ticket_type)}",
            description=(
                f"**Ticket aberto por:** {user.mention}\n"
                f"**Tipo:** {TicketType.get_name(ticket_type)}\n\n"
                f"{Emojis.INFO} Nossa equipe responderá em breve.\n"
                f"{Emojis.WARNING} Por favor, descreva seu problema ou necessidade."
            ),
            color=Colors.VOID_PRIMARY,
            timestamp=cls._get_timestamp()
        )
        embed.set_footer(**cls._get_footer())
        return embed
    
    @classmethod
    def order_created(
        cls,
        order_id: str,
        client: discord.Member,
        product: str,
        value: float
    ) -> discord.Embed:
        """Embed de pedido criado"""
        from .helpers import format_currency
        
        embed = discord.Embed(
            title=f"{Emojis.ORDER} Pedido {order_id}",
            description=f"{Emojis.SUCCESS} Pedido criado com sucesso!",
            color=Colors.SUCCESS,
            timestamp=cls._get_timestamp()
        )
        embed.add_field(name="Cliente", value=client.mention, inline=True)
        embed.add_field(name="Produto", value=product, inline=True)
        embed.add_field(name="Valor", value=format_currency(value), inline=True)
        embed.add_field(name="Status", value=f"{Emojis.PENDING} Pendente", inline=True)
        embed.set_footer(**cls._get_footer())
        return embed
    
    @classmethod
    def role_updated(
        cls,
        user: discord.Member,
        old_role: Optional[str],
        new_role: str,
        total_spent: float
    ) -> discord.Embed:
        """Embed de cargo atualizado"""
        from .helpers import format_currency
        
        description = f"{Emojis.CROWN} **Cargo Atualizado!**\n\n"
        
        if old_role:
            description += f"**Cargo Anterior:** {old_role}\n"
        
        description += (
            f"**Novo Cargo:** {new_role}\n"
            f"**Total Gasto:** {format_currency(total_spent)}"
        )
        
        embed = discord.Embed(
            title=f"{Emojis.SUCCESS} Parabéns, {user.name}!",
            description=description,
            color=Colors.SUCCESS,
            timestamp=cls._get_timestamp()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(**cls._get_footer())
        return embed
    
    @classmethod
    def task_created(
        cls,
        task_id: int,
        name: str,
        priority: str,
        assignee: Optional[discord.Member] = None
    ) -> discord.Embed:
        """Embed de tarefa criada"""
        from .constants import Emojis, TaskPriority
        
        priority_emojis = {
            TaskPriority.HIGH: Emojis.HIGH_PRIORITY,
            TaskPriority.MEDIUM: Emojis.MEDIUM_PRIORITY,
            TaskPriority.LOW: Emojis.LOW_PRIORITY
        }
        
        embed = discord.Embed(
            title=f"{Emojis.TASK} Tarefa #{task_id}",
            description=f"**Nome:** {name}",
            color=Colors.SUCCESS,
            timestamp=cls._get_timestamp()
        )
        embed.add_field(
            name="Prioridade",
            value=f"{priority_emojis.get(priority, Emojis.INFO)} {priority.title()}",
            inline=True
        )
        
        if assignee:
            embed.add_field(name="Responsável", value=assignee.mention, inline=True)
        
        embed.add_field(name="Status", value=f"{Emojis.PENDING} Pendente", inline=True)
        embed.set_footer(**cls._get_footer())
        return embed
    
    @classmethod
    def inventory_item(
        cls,
        name: str,
        category: str,
        quantity: int,
        price: float,
        status: str
    ) -> discord.Embed:
        """Embed de item do estoque"""
        from .helpers import format_currency
        from .constants import StockStatus
        
        status_emojis = {
            StockStatus.AVAILABLE: Emojis.IN_STOCK,
            StockStatus.LOW_STOCK: Emojis.LOW_STOCK,
            StockStatus.OUT_OF_STOCK: Emojis.OUT_OF_STOCK
        }
        
        embed = discord.Embed(
            title=f"{Emojis.INVENTORY} {name}",
            color=Colors.VOID_PRIMARY,
            timestamp=cls._get_timestamp()
        )
        embed.add_field(name="Categoria", value=category, inline=True)
        embed.add_field(name="Quantidade", value=str(quantity), inline=True)
        embed.add_field(name="Preço", value=format_currency(price), inline=True)
        embed.add_field(
            name="Status",
            value=f"{status_emojis.get(status, Emojis.INFO)} {status.replace('_', ' ').title()}",
            inline=True
        )
        embed.set_footer(**cls._get_footer())
        return embed
    
    @classmethod
    def help_category(
        cls,
        category: str,
        description: str,
        commands: List[dict]
    ) -> discord.Embed:
        """Embed de categoria de ajuda"""
        embed = discord.Embed(
            title=f"{Emojis.HELP} Ajuda - {category}",
            description=description,
            color=Colors.VOID_PRIMARY,
            timestamp=cls._get_timestamp()
        )
        
        for cmd in commands:
            embed.add_field(
                name=f"/{cmd['name']}",
                value=cmd['description'],
                inline=False
            )
        
        embed.set_footer(**cls._get_footer())
        return embed
