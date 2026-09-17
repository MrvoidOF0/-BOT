"""
🌑 VOID Store Bot - Sistema de Embeds para Canal de Stock
Permite criar embeds customizáveis com qualquer texto.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from utils.embeds import VoidEmbeds
from utils.permissions import PermissionChecker
from utils.constants import Emojis
from utils.logger import logger


# ====================================
# MODAL PARA CRIAR EMBED
# ====================================

class StockEmbedModal(discord.ui.Modal, title="Criar Embed de Stock"):
    """Modal para criar embed customizado"""
    
    title_input = discord.ui.TextInput(
        label="Título do Embed",
        placeholder="Ex: 📦 ESTOQUE DISPONÍVEL",
        required=True,
        max_length=256
    )
    
    description_input = discord.ui.TextInput(
        label="Descrição / Conteúdo",
        placeholder="Cole aqui seu texto. Você pode usar **negrito**, *itálico*, etc.",
        required=True,
        style=discord.TextStyle.long,
        max_length=4096
    )
    
    color_input = discord.ui.TextInput(
        label="Cor (hex opcional)",
        placeholder="Ex: #2b2d31 ou deixe vazio para preto",
        required=False,
        max_length=20
    )
    
    footer_input = discord.ui.TextInput(
        label="Footer (opcional)",
        placeholder="Ex: 🌑 VOID Store | Atualizado hoje",
        required=False,
        max_length=2048
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        cog = interaction.client.get_cog("StockDisplay")
        if cog:
            await cog.create_stock_embed(
                interaction,
                self.title_input.value,
                self.description_input.value,
                self.color_input.value,
                self.footer_input.value
            )


# ====================================
# COG
# ====================================

class StockDisplay(commands.Cog):
    """Sistema de embeds para canal de stock"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
    
    @app_commands.command(name="stock-embed", description="📦 Cria um embed customizado para o canal de stock")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def stock_embed_command(self, interaction: discord.Interaction):
        """Abre modal para criar embed de stock"""
        
        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return
        
        modal = StockEmbedModal()
        await interaction.response.send_modal(modal)
    
    async def create_stock_embed(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        color_hex: Optional[str],
        footer: Optional[str]
    ):
        """Cria e envia o embed de stock"""
        
        # Parse da cor
        color = 0x000000  # Preto padrão
        if color_hex:
            try:
                color_hex = color_hex.replace("#", "")
                color = int(color_hex, 16)
            except ValueError:
                pass
        
        # Criar embed
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=discord.utils.utcnow()
        )
        
        if footer:
            embed.set_footer(text=footer, icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        else:
            embed.set_footer(text="🌑 VOID Store")
        
        # Botão de editar/deletar (apenas para staff)
        view = discord.ui.View()
        
        edit_btn = discord.ui.Button(
            label="✏️ Editar",
            style=discord.ButtonStyle.secondary,
            custom_id=f"stock_edit:{interaction.user.id}"
        )
        
        delete_btn = discord.ui.Button(
            label="🗑️ Deletar",
            style=discord.ButtonStyle.danger,
            custom_id=f"stock_delete:{interaction.user.id}"
        )
        
        view.add_item(edit_btn)
        view.add_item(delete_btn)
        
        # Enviar
        await interaction.followup.send(embed=embed, view=view)
        
        logger.info(f"Stock embed created by {interaction.user}")
    
    @app_commands.command(name="stock-listar", description="📦 Lista todos os itens do estoque formatado")
    async def stock_list(self, interaction: discord.Interaction):
        """Lista o estoque em formato de embed bonito"""
        
        # Buscar itens do banco
        items = await self.db.get_all_inventory()
        
        if not items:
            await interaction.response.send_message(
                f"{Emojis.INFO} Nenhum item no estoque.",
                ephemeral=True
            )
            return
        
        # Agrupar por categoria
        categories = {}
        for item in items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)
        
        # Criar embed
        embed = discord.Embed(
            title="📦 𝐄𝐒𝐓𝐎𝐐𝐔𝐄 — 𝐕𝐎𝐈𝐃 𝐒𝐭𝐨𝐫𝐞",
            description="Confira nossos produtos disponíveis:",
            color=0x000000,
            timestamp=discord.utils.utcnow()
        )
        
        for category, cat_items in categories.items():
            items_text = ""
            for item in cat_items:
                status_emoji = "🟢" if item.quantity > 5 else "🟡" if item.quantity > 0 else "🔴"
                items_text += f"{status_emoji} **{item.name}** — `R$ {item.price:.2f}` ({item.quantity}x)\n"
            
            embed.add_field(
                name=f"📁 {category.upper()}",
                value=items_text or "Nenhum item",
                inline=False
            )
        
        embed.set_footer(text="🌑 VOID Store | Preços podem variar")
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(StockDisplay(bot))
