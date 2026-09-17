"""
🌑 VOID Store Bot - Sistema de Estoque
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from database.models import InventoryItem
from utils.embeds import VoidEmbeds
from utils.permissions import PermissionChecker
from utils.constants import StockStatus, Emojis
from utils.helpers import format_currency
from utils.logger import logger
from config import config


class Inventory(commands.Cog):
    """Sistema de gerenciamento de produtos e estoque"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    inventory_group = app_commands.Group(
        name="estoque",
        description="📦 Gerenciamento de estoque e produtos"
    )

    @inventory_group.command(name="adicionar", description="📦 Cadastra ou incrementa item no estoque")
    @app_commands.describe(
        nome="Nome do produto ou item",
        categoria="Categoria do produto (ex: Contas, Serviços, Itens)",
        quantidade="Quantidade disponível",
        preco="Preço unitário em Reais (ex: 15.00)"
    )
    async def add_item(
        self,
        interaction: discord.Interaction,
        nome: str,
        categoria: str,
        quantidade: int,
        preco: float
    ):
        """Adiciona um item ao estoque"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        if quantidade < 0 or preco < 0:
            await interaction.response.send_message(
                f"{Emojis.ERROR} Quantidade e preço não podem ser negativos.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        # Verificar se já existe item com esse nome
        existing_item = await self.db.get_inventory_item(nome.strip())

        if existing_item:
            # Apenas incrementa quantidade
            new_qty = existing_item.quantity + quantidade
            await self.db.update_inventory_quantity(existing_item.name, new_qty)

            embed = VoidEmbeds.success(
                "Estoque Atualizado",
                f"Item **{existing_item.name}** já existia. A quantidade foi somada!\n\n"
                f"**Quantidade Anterior:** {existing_item.quantity}\n"
                f"**Adicionado:** +{quantidade}\n"
                f"**Total Atual:** {new_qty}"
            )
            await interaction.followup.send(embed=embed)
            return

        # Definir status inicial
        if quantidade == 0:
            status = StockStatus.OUT_OF_STOCK
        elif quantidade <= config.LOW_STOCK_THRESHOLD:
            status = StockStatus.LOW_STOCK
        else:
            status = StockStatus.AVAILABLE

        item = InventoryItem(
            name=nome.strip(),
            category=categoria.strip(),
            quantity=quantidade,
            price=preco,
            status=status
        )

        result = await self.db.create_inventory_item(item)

        if result:
            embed = VoidEmbeds.inventory_item(
                item.name,
                item.category,
                item.quantity,
                item.price,
                item.status
            )
            await interaction.followup.send(
                content=f"{Emojis.SUCCESS} Produto cadastrado com sucesso!",
                embed=embed
            )

            # Sincronizar Google Sheets
            sheets_cog = self.bot.get_cog("Sheets")
            if sheets_cog:
                await sheets_cog.sync_inventory(item)

            await self.db.create_log(
                "inventory",
                interaction.user.id,
                "item_created",
                f"Product: {nome} | Qty: {quantidade} | Price: {preco}"
            )
        else:
            await interaction.followup.send(
                f"{Emojis.ERROR} Falha ao salvar produto no banco de dados.",
                ephemeral=True
            )

    @inventory_group.command(name="remover", description="📦 Remove unidades do estoque")
    @app_commands.describe(
        nome="Nome exato do produto",
        quantidade="Quantidade de unidades a abater"
    )
    async def remove_quantity(
        self,
        interaction: discord.Interaction,
        nome: str,
        quantidade: int
    ):
        """Reduz a quantidade de um produto"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        if quantidade <= 0:
            await interaction.response.send_message(
                f"{Emojis.ERROR} A quantidade para remoção deve ser maior que zero.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        item = await self.db.get_inventory_item(nome.strip())

        if not item:
            await interaction.followup.send(
                f"{Emojis.ERROR} Produto `{nome}` não encontrado no estoque.",
                ephemeral=True
            )
            return

        if item.quantity < quantidade:
            await interaction.followup.send(
                f"{Emojis.ERROR} Estoque insuficiente. Estoque atual: **{item.quantity}** unidades.",
                ephemeral=True
            )
            return

        new_qty = item.quantity - quantidade
        await self.db.update_inventory_quantity(item.name, new_qty)

        embed = VoidEmbeds.success(
            "Estoque Atualizado",
            f"**Produto:** {item.name}\n"
            f"**Removido:** -{quantidade} unidades\n"
            f"**Estoque Restante:** {new_qty} unidades"
        )

        if new_qty <= config.LOW_STOCK_THRESHOLD and new_qty > 0:
            embed.add_field(
                name="Aviso",
                value=f"{Emojis.LOW_STOCK} Este item entrou em **Baixo Estoque**!",
                inline=False
            )
        elif new_qty == 0:
            embed.add_field(
                name="Aviso",
                value=f"{Emojis.OUT_OF_STOCK} Este item está **Esgotado**!",
                inline=False
            )

        await interaction.followup.send(embed=embed)

        # Sincronizar Google Sheets
        item.quantity = new_qty
        sheets_cog = self.bot.get_cog("Sheets")
        if sheets_cog:
            await sheets_cog.sync_inventory(item)

        await self.db.create_log(
            "inventory",
            interaction.user.id,
            "stock_reduced",
            f"Product: {nome} | Removed: {quantidade} | Remaining: {new_qty}"
        )

    @inventory_group.command(name="consultar", description="🔍 Consulta informações de um produto")
    @app_commands.describe(nome="Nome do produto")
    async def check_item(self, interaction: discord.Interaction, nome: str):
        """Consulta um item específico"""

        await interaction.response.defer()

        item = await self.db.get_inventory_item(nome.strip())

        if not item:
            await interaction.followup.send(
                f"{Emojis.ERROR} Produto `{nome}` não encontrado.",
                ephemeral=True
            )
            return

        embed = VoidEmbeds.inventory_item(
            item.name,
            item.category,
            item.quantity,
            item.price,
            item.status
        )
        await interaction.followup.send(embed=embed)

    @inventory_group.command(name="listar", description="📦 Exibe todos os itens do estoque da loja")
    async def list_inventory(self, interaction: discord.Interaction):
        """Lista todo o estoque público/staff"""

        await interaction.response.defer()

        items = await self.db.get_all_inventory()

        if not items:
            await interaction.followup.send(
                f"{Emojis.INFO} Nenhum produto cadastrado no momento.",
                ephemeral=True
            )
            return

        embed = VoidEmbeds.default(
            f"{Emojis.INVENTORY} Estoque — VOID Store",
            "Confira os produtos e serviços disponíveis:"
        )

        # Agrupar por categorias
        categories = {}
        for item in items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)

        for category, cat_items in categories.items():
            content = []
            for item in cat_items:
                s_emoji = (
                    Emojis.IN_STOCK if item.quantity > config.LOW_STOCK_THRESHOLD
                    else Emojis.LOW_STOCK if item.quantity > 0
                    else Emojis.OUT_OF_STOCK
                )
                content.append(
                    f"{s_emoji} **{item.name}** — {format_currency(item.price)} "
                    f"(`{item.quantity} disponíveis`)"
                )

            embed.add_field(
                name=f"📁 {category.upper()}",
                value="\n".join(content),
                inline=False
            )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Inventory(bot))
