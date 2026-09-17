"""
🌑 VOID Store Bot - Sistema de Pedidos
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal
from datetime import datetime

from database.models import Order, Purchase
from utils.embeds import VoidEmbeds
from utils.permissions import PermissionChecker
from utils.constants import OrderStatus, Emojis
from utils.helpers import format_currency, generate_order_id
from utils.logger import logger
from config import config

class Orders(commands.Cog):
    """Sistema de gerenciamento de pedidos e vendas"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    @app_commands.command(name="pedido-criar", description="📦 Cria um novo pedido para um cliente")
    @app_commands.describe(
        cliente="O cliente que realizou a compra",
        produto="Nome do produto ou serviço",
        valor="Valor total do pedido (ex: 29.90)",
        notas="Observações adicionais"
    )
    async def create_order(
        self, 
        interaction: discord.Interaction, 
        cliente: discord.Member, 
        produto: str, 
        valor: float, 
        notas: Optional[str] = None
    ):
        """Cria um pedido manualmente"""
        
        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        await interaction.response.defer()

        # 1. Garantir que o usuário existe no banco
        user = await self.db.get_user(cliente.id)
        if not user:
            await self.db.create_user(cliente.id, str(cliente))

        # 2. Gerar ID do pedido
        order_count = await self.db.get_next_order_number()
        order_id = generate_order_id(order_count)

        # 3. Criar objeto do pedido
        new_order = Order(
            order_id=order_id,
            client_id=cliente.id,
            client_name=str(cliente),
            product=produto,
            value=valor,
            responsible_id=interaction.user.id,
            responsible_name=str(interaction.user),
            status=OrderStatus.PENDING,
            notes=notas
        )

        # 4. Salvar no banco
        result = await self.db.create_order(new_order)

        if result:
            embed = VoidEmbeds.order_created(order_id, cliente, produto, valor)
            if notas:
                embed.add_field(name="Notas", value=notas, inline=False)
            
            await interaction.followup.send(embed=embed)
            
            # Log
            await self.db.create_log("order", interaction.user.id, "created", f"Order ID: {order_id}")
            logger.info(f"Order {order_id} created by {interaction.user}")
        else:
            await interaction.followup.send(f"{Emojis.ERROR} Erro ao salvar o pedido no banco de dados.")

    @app_commands.command(name="pedido-status", description="🟡 Altera o status de um pedido")
    @app_commands.describe(
        order_id="ID do pedido (ex: VOID-0001)",
        status="Novo status do pedido"
    )
    async def update_status(
        self, 
        interaction: discord.Interaction, 
        order_id: str, 
        status: Literal["pendente", "andamento", "concluido", "cancelado"]
    ):
        """Atualiza o status e processa a venda se concluído"""
        
        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        await interaction.response.defer()
        
        # Mapeamento de status
        status_map = {
            "pendente": OrderStatus.PENDING,
            "andamento": OrderStatus.IN_PROGRESS,
            "concluido": OrderStatus.COMPLETED,
            "cancelado": OrderStatus.CANCELLED
        }
        
        new_status = status_map[status]
        order = await self.db.get_order(order_id.upper())

        if not order:
            await interaction.followup.send(f"{Emojis.ERROR} Pedido `{order_id}` não encontrado.")
            return

        # Se já estiver concluído, evitar duplicar gasto
        if order.status == OrderStatus.COMPLETED and new_status == OrderStatus.COMPLETED:
            await interaction.followup.send(f"{Emojis.WARNING} Este pedido já consta como concluído.")
            return

        # Atualizar no banco
        success = await self.db.update_order_status(order.order_id, new_status)

        if success:
            # Se for CONCLUÍDO, processar progresso de gastos do cliente
            if new_status == OrderStatus.COMPLETED:
                await self.process_order_completion(interaction, order)
            
            embed = VoidEmbeds.success(
                "Status Atualizado",
                f"O pedido `{order.order_id}` foi alterado para: **{status.upper()}**"
            )
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"{Emojis.ERROR} Erro ao atualizar status.")

    async def process_order_completion(self, interaction: discord.Interaction, order: Order):
        """Processa a conclusão de uma venda (Gasto acumulado e Cargos)"""
        
        # 1. Registrar a compra no histórico
        purchase = Purchase(
            user_id=order.client_id,
            order_id=order.order_id,
            amount=order.value
        )
        await self.db.create_purchase(purchase)

        # 2. Atualizar o gasto total do usuário
        await self.db.update_user_spent(order.client_id, order.value)

        # 3. Chamar o Cog de Roles para verificar se o cliente subiu de nível
        roles_cog = self.bot.get_cog("Roles")
        if roles_cog:
            member = interaction.guild.get_member(order.client_id)
            if member:
                await roles_cog.check_user_tier(member)

    @app_commands.command(name="pedido-consultar", description="🔍 Consulta detalhes de um pedido")
    async def get_order_details(self, interaction: discord.Interaction, order_id: str):
        """Busca informações de um pedido específico"""
        
        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        order = await self.db.get_order(order_id.upper())
        if not order:
            await interaction.response.send_message(f"{Emojis.ERROR} Pedido não encontrado.", ephemeral=True)
            return

        embed = VoidEmbeds.default(f"Detalhes do Pedido {order.order_id}", "")
        embed.add_field(name="Cliente", value=f"<@{order.client_id}>", inline=True)
        embed.add_field(name="Valor", value=format_currency(order.value), inline=True)
        embed.add_field(name="Produto", value=order.product, inline=True)
        embed.add_field(name="Status", value=order.status.upper(), inline=True)
        embed.add_field(name="Responsável", value=order.responsible_name, inline=True)
        embed.add_field(name="Data", value=order.created_at.strftime("%d/%m/%Y"), inline=True)
        
        if order.notes:
            embed.add_field(name="Notas", value=order.notes, inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Orders(bot))
