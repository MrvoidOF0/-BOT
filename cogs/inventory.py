"""
🌑 VOID Store Bot - Sistema de Estoque CORRIGIDO
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
    """Sistema de gerenciamento de estoque"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    inventory_group = app_commands.Group(
        name="estoque",
        description="📦 Gerenciamento de estoque"
    )

    @inventory_group.command(name="adicionar", description="📦 Adiciona item ao estoque")
    @app_commands.describe(
        nome="Nome do produto",
        categoria="Categoria",
        quantidade="Quantidade",
        preco="Preço unitário"
    )
    async def adicionar(
        self,
        interaction: discord.Interaction,
        nome: str,
        categoria: str,
        quantidade: int,
        preco: float
    ):
        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        if quantidade < 0 or preco < 0:
            await interaction.response.send_message(
                "❌ Quantidade e preço não podem ser negativos.", ephemeral=True
            )
            return

        await interaction.response.defer()

        # Definir status inicial
        threshold = config.LOW_STOCK_THRESHOLD
        if quantidade == 0:
            status = StockStatus.OUT_OF_STOCK
        elif quantidade <= threshold:
            status = StockStatus.LOW_STOCK
        else:
            status = StockStatus.AVAILABLE

        # Verificar se já existe
        existing = await self.db.get_inventory_item(nome.strip())

        if existing:
            new_qty = existing.quantity + quantidade
            success = await self.db.update_inventory_quantity(existing.name, new_qty)

            if success:
                embed = VoidEmbeds.success(
                    "Estoque Atualizado",
                    f"**{existing.name}** já existia. Quantidade somada!\n\n"
                    f"**Anterior:** {existing.quantity}\n"
                    f"**Adicionado:** +{quantidade}\n"
                    f"**Total:** {new_qty}"
                )
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send("❌ Erro ao atualizar estoque.", ephemeral=True)
            return

        # Criar novo item
        item = InventoryItem(
            name=nome.strip(),
            category=categoria.strip(),
            quantity=quantidade,
            price=preco,
            status=status
        )

        result = await self.db.create_inventory_item(item)

        if result:
            embed = discord.Embed(
                title=f"✅ Produto Cadastrado",
                description=f"**{nome}** foi adicionado ao estoque!",
                color=0x00ff00
            )
            embed.add_field(name="Categoria", value=categoria, inline=True)
            embed.add_field(name="Quantidade", value=str(quantidade), inline=True)
            embed.add_field(name="Preço", value=format_currency(preco), inline=True)
            embed.add_field(name="Status", value=status.replace("_", " ").title(), inline=True)
            embed.set_footer(text="🌑 VOID Store")

            await interaction.followup.send(embed=embed)

            await self.db.create_log(
                "inventory", interaction.user.id, "created",
                f"Product: {nome} | Qty: {quantidade} | Price: {preco}"
            )
        else:
            await interaction.followup.send("❌ Erro ao cadastrar produto.", ephemeral=True)

    @inventory_group.command(name="remover", description="📦 Remove unidades do estoque")
    @app_commands.describe(
        nome="Nome exato do produto",
        quantidade="Quantidade a remover"
    )
    async def remover(
        self,
        interaction: discord.Interaction,
        nome: str,
        quantidade: int
    ):
        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        if quantidade <= 0:
            await interaction.response.send_message(
                "❌ Quantidade deve ser maior que zero.", ephemeral=True
            )
            return

        await interaction.response.defer()

        item = await self.db.get_inventory_item(nome.strip())

        if not item:
            await interaction.followup.send(
                f"❌ Produto `{nome}` não encontrado. Verifique o nome exato com `/estoque listar`.",
                ephemeral=True
            )
            return

        if item.quantity < quantidade:
            await interaction.followup.send(
                f"❌ Estoque insuficiente.\n"
                f"**Disponível:** {item.quantity} unidades\n"
                f"**Tentou remover:** {quantidade} unidades",
                ephemeral=True
            )
            return

        new_qty = item.quantity - quantidade
        success = await self.db.update_inventory_quantity(item.name, new_qty)

        if success:
            embed = VoidEmbeds.success(
                "Estoque Atualizado",
                f"**{item.name}**\n\n"
                f"**Removido:** -{quantidade}\n"
                f"**Restante:** {new_qty}"
            )

            if new_qty == 0:
                embed.add_field(name="⚠️ Alerta", value="🔴 Produto **ESGOTADO**!", inline=False)
            elif new_qty <= config.LOW_STOCK_THRESHOLD:
                embed.add_field(name="⚠️ Alerta", value="🟡 Produto em **BAIXO ESTOQUE**!", inline=False)

            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("❌ Erro ao atualizar estoque.", ephemeral=True)

    @inventory_group.command(name="consultar", description="🔍 Consulta um produto")
    @app_commands.describe(nome="Nome do produto")
    async def consultar(self, interaction: discord.Interaction, nome: str):
        await interaction.response.defer()

        item = await self.db.get_inventory_item(nome.strip())

        if not item:
            await interaction.followup.send(
                f"❌ Produto `{nome}` não encontrado.",
                ephemeral=True
            )
            return

        status_emojis = {
            "available": "🟢 Disponível",
            "low_stock": "🟡 Baixo Estoque",
            "out_of_stock": "🔴 Esgotado"
        }

        embed = discord.Embed(
            title=f"📦 {item.name}",
            color=0x000000
        )
        embed.add_field(name="Categoria", value=item.category, inline=True)
        embed.add_field(name="Quantidade", value=str(item.quantity), inline=True)
        embed.add_field(name="Preço", value=format_currency(item.price), inline=True)
        embed.add_field(name="Status", value=status_emojis.get(item.status, item.status), inline=True)
        embed.set_footer(text="🌑 VOID Store")

        await interaction.followup.send(embed=embed)

    @inventory_group.command(name="listar", description="📦 Lista todos os produtos do estoque")
    async def listar(self, interaction: discord.Interaction):
        await interaction.response.defer()

        items = await self.db.get_all_inventory()

        if not items:
            await interaction.followup.send(
                "📦 Nenhum produto cadastrado no estoque ainda.\n"
                "Use `/estoque adicionar` para começar!",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📦 Estoque — VOID Store",
            description="Produtos cadastrados:",
            color=0x000000,
            timestamp=discord.utils.utcnow()
        )

        categories: dict = {}
        for item in items:
            cat = item.category or "Sem Categoria"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)

        for cat, cat_items in categories.items():
            lines = []
            for it in cat_items:
                if it.quantity > config.LOW_STOCK_THRESHOLD:
                    s = "🟢"
                elif it.quantity > 0:
                    s = "🟡"
                else:
                    s = "🔴"
                lines.append(f"{s} **{it.name}** — {format_currency(it.price)} ({it.quantity}x)")

            embed.add_field(
                name=f"📁 {cat}",
                value="\n".join(lines),
                inline=False
            )

        embed.set_footer(text=f"🌑 VOID Store | {len(items)} produto(s) cadastrado(s)")
        await interaction.followup.send(embed=embed)

    @inventory_group.command(name="editar", description="✏️ Edita preço ou quantidade de um produto")
    @app_commands.describe(
        nome="Nome do produto",
        nova_quantidade="Nova quantidade (deixe vazio para não alterar)",
        novo_preco="Novo preço (deixe vazio para não alterar)"
    )
    async def editar(
        self,
        interaction: discord.Interaction,
        nome: str,
        nova_quantidade: Optional[int] = None,
        novo_preco: Optional[float] = None
    ):
        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        await interaction.response.defer()

        item = await self.db.get_inventory_item(nome.strip())
        if not item:
            await interaction.followup.send(
                f"❌ Produto `{nome}` não encontrado.", ephemeral=True
            )
            return

        alteracoes = []

        if nova_quantidade is not None:
            await self.db.update_inventory_quantity(item.name, nova_quantidade)
            alteracoes.append(f"**Quantidade:** {item.quantity} → {nova_quantidade}")

        if novo_preco is not None:
            # Atualizar preço no banco
            if self.db.db_type == "sqlite":
                await self.db.connection.execute(
                    "UPDATE inventory SET price = ?, updated_at = datetime('now') WHERE name = ?",
                    (novo_preco, item.name)
                )
                await self.db.connection.commit()
            alteracoes.append(f"**Preço:** {format_currency(item.price)} → {format_currency(novo_preco)}")

        if not alteracoes:
            await interaction.followup.send(
                "⚠️ Nenhuma alteração informada.", ephemeral=True
            )
            return

        embed = VoidEmbeds.success(
            "Produto Atualizado",
            f"**{item.name}** foi editado:\n\n" + "\n".join(alteracoes)
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Inventory(bot))
