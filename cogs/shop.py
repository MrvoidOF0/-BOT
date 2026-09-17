"""
🌑 VOID Store Bot - Painel de Loja com Botões de Compra
Cada botão abre um canal dedicado para aquele produto/serviço.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Dict, List
import asyncio

from utils.embeds import VoidEmbeds
from utils.permissions import PermissionChecker
from utils.constants import Emojis
from utils.logger import logger
from config import config


# ====================================
# CONFIGURAÇÃO DOS PRODUTOS/SERVIÇOS
# ====================================

# Você pode editar esta lista para adicionar/remover produtos
SHOP_PRODUCTS = [
    {
        "id": "engrenagem_v4",
        "name": "⚙️ Engrenagem V4",
        "description": "Farm completo de Engrenagem V4 no Blox Fruits",
        "price": 29.90,
        "emoji": "⚙️",
        "color": 0x2b2d31,
        "category": "farm"
    },
    {
        "id": "frutas",
        "name": "🍎 Frutas",
        "description": "Frutas aleatórias ou específicas do Blox Fruits",
        "price": 15.00,
        "emoji": "🍎",
        "color": 0x9b59b6,
        "category": "frutas"
    },
    {
        "id": "levels",
        "name": "⬆️ Levels",
        "description": "Level up rápido e seguro no seu personagem",
        "price": 19.90,
        "emoji": "⬆️",
        "color": 0x3498db,
        "category": "level"
    },
    {
        "id": "fragmentos",
        "name": "💎 Fragmentos",
        "description": "Farm de fragmentos para raças e upgrades",
        "price": 12.00,
        "emoji": "💎",
        "color": 0xe74c3c,
        "category": "farm"
    },
    {
        "id": "money",
        "name": "💰 Money / Beli",
        "description": "Farm de dinheiro/Beli no Blox Fruits",
        "price": 9.90,
        "emoji": "💰",
        "color": 0xf39c12,
        "category": "farm"
    },
    {
        "id": "farm_materiais",
        "name": "📦 Farm de Materiais",
        "description": "Farm de materiais diversos (espadas, acessórios, etc)",
        "price": 24.90,
        "emoji": "📦",
        "color": 0x27ae60,
        "category": "farm"
    },
]


# ====================================
# VIEW DO PAINEL DE LOJA
# ====================================

class ShopPanelView(discord.ui.View):
    """View com botões para cada produto da loja"""
    
    def __init__(self):
        super().__init__(timeout=None)
        
        # Adicionar botões dinamicamente
        for product in SHOP_PRODUCTS:
            button = discord.ui.Button(
                label=product["name"],
                style=discord.ButtonStyle.blurple,
                emoji=product["emoji"],
                custom_id=f"shop_buy:{product['id']}"
            )
            button.callback = self.create_buy_callback(product)
            self.add_item(button)
    
    def create_buy_callback(self, product: dict):
        """Cria callback dinâmico para cada produto"""
        async def callback(interaction: discord.Interaction):
            cog = interaction.client.get_cog("Shop")
            if cog:
                await cog.handle_buy_button(interaction, product)
        return callback


# ====================================
# VIEW DE CONFIRMAÇÃO DE COMPRA
# ====================================

class BuyConfirmView(discord.ui.View):
    """View de confirmação após clicar em comprar"""
    
    def __init__(self, product: dict, user: discord.Member):
        super().__init__(timeout=300)  # 5 minutos
        self.product = product
        self.user = user
        self.value = None
    
    @discord.ui.button(label="✅ Confirmar Compra", style=discord.ButtonStyle.green, emoji=Emojis.SUCCESS)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "confirmed"
        self.stop()
        await interaction.response.defer()
    
    @discord.ui.button(label="❌ Cancelar", style=discord.ButtonStyle.red, emoji=Emojis.ERROR)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "cancelled"
        self.stop()
        await interaction.response.defer()


# ====================================
# COG PRINCIPAL
# ====================================

class Shop(commands.Cog):
    """Sistema de loja com botões de compra"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        
        # Registrar view persistente
        self.bot.add_view(ShopPanelView())
    
    # ====================================
    # COMANDOS
    # ====================================
    
    @app_commands.command(name="loja-painel", description="🛒 Cria o painel de loja com botões de compra")
    @app_commands.checks.has_permissions(administrator=True)
    async def shop_panel(self, interaction: discord.Interaction):
        """Cria o painel de loja no canal atual"""
        
        if not await PermissionChecker.check_interaction_permissions(interaction, require_admin=True):
            return
        
        # Criar embed da loja
        embed = discord.Embed(
            title=f"{Emojis.VOID} 𝐕𝐎𝐈𝐃 𝐒𝐭𝐨𝐫𝐞 | Loja Oficial",
            description=(
                "Bem-vindo à **VOID Store**! 🌑\n\n"
                "Clique no botão abaixo do produto desejado para iniciar sua compra.\n"
                "Um canal privado será criado para atendimento exclusivo.\n\n"
                f"{Emojis.INFO} **Como funciona:**\n"
                f"1. Clique no botão do produto\n"
                f"2. Confirme sua compra\n"
                f"3. Um canal privado será aberto\n"
                f"4. Nossa equipe entrará em contato\n"
                f"5. Pagamento via PIX com QR Code automático\n\n"
                f"⚠️ **Atenção:** Cada cliente pode ter apenas 1 canal de compra aberto por vez."
            ),
            color=0x000000,
            timestamp=discord.utils.utcnow()
        )
        
        # Adicionar lista de produtos
        products_text = ""
        for product in SHOP_PRODUCTS:
            products_text += f"{product['emoji']} **{product['name']}** — `R$ {product['price']:.2f}`\n"
        
        embed.add_field(
            name="📦 Produtos Disponíveis",
            value=products_text,
            inline=False
        )
        
        embed.set_footer(text="🌑 VOID Store | Pagamento 100% seguro via PIX")
        
        # Criar view com botões
        view = ShopPanelView()
        
        # Enviar painel
        await interaction.channel.send(embed=embed, view=view)
        
        await interaction.response.send_message(
            f"{Emojis.SUCCESS} Painel de loja criado com sucesso!",
            ephemeral=True
        )
        
        logger.info(f"Shop panel created by {interaction.user}")
    
    @app_commands.command(name="loja-adicionar-produto", description="🛒 Adiciona um produto à loja (admin)")
    @app_commands.describe(
        nome="Nome do produto",
        descricao="Descrição do produto",
        preco="Preço em reais",
        emoji="Emoji do produto",
        categoria="Categoria do produto"
    )
    async def add_product(
        self,
        interaction: discord.Interaction,
        nome: str,
        descricao: str,
        preco: float,
        emoji: str,
        categoria: str
    ):
        """Adiciona um produto à lista da loja (requer reinício do bot)"""
        
        if not await PermissionChecker.check_interaction_permissions(interaction, require_admin=True):
            return
        
        # Este comando apenas mostra como adicionar
        # Para adicionar permanentemente, edite SHOP_PRODUCTS no código
        
        embed = discord.Embed(
            title="➕ Adicionar Produto",
            description=(
                f"Para adicionar produtos permanentemente à loja:\n\n"
                f"1. Edite o arquivo `cogs/shop.py`\n"
                f"2. Adicione um novo item na lista `SHOP_PRODUCTS`\n"
                f"3. Reinicie o bot no Railway\n\n"
                f"**Exemplo de entrada:**\n"
                f"```python\n"
                f"{{\n"
                f'    "id": "produto_exemplo",\n'
                f'    "name": "📦 Nome do Produto",\n'
                f'    "description": "Descrição do produto",\n'
                f'    "price": 29.90,\n'
                f'    "emoji": "📦",\n'
                f'    "color": 0x2b2d31,\n'
                f'    "category": "categoria"\n'
                f"}}\n"
                f"```"
            ),
            color=0x000000
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    # ====================================
    # HANDLERS
    # ====================================
    
    async def handle_buy_button(self, interaction: discord.Interaction, product: dict):
        """Processa o clique no botão de compra"""
        
        await interaction.response.defer(ephemeral=True)
        
        # Verificar se usuário já tem canal de compra aberto
        existing_channel = await self._find_user_buy_channel(interaction.user, interaction.guild)
        
        if existing_channel:
            await interaction.followup.send(
                f"{Emojis.WARNING} Você já possui um canal de compra aberto: {existing_channel.mention}\n"
                f"Por favor, finalize ou feche seu atendimento atual antes de iniciar uma nova compra.",
                ephemeral=True
            )
            return
        
        # Mostrar confirmação
        embed = discord.Embed(
            title=f"{product['emoji']} Confirmar Compra",
            description=(
                f"Você está prestes a iniciar a compra de:\n\n"
                f"**{product['name']}**\n"
                f"{product['description']}\n\n"
                f"💰 **Valor:** `R$ {product['price']:.2f}`\n\n"
                f"Ao confirmar:\n"
                f"• Um canal privado será criado\n"
                f"• Você receberá o QR Code do PIX\n"
                f"• Nossa equipe irá te atender\n\n"
                f"⏱️ Você tem **5 minutos** para confirmar."
            ),
            color=product['color'],
            timestamp=discord.utils.utcnow()
        )
        
        view = BuyConfirmView(product, interaction.user)
        
        msg = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        
        # Aguardar resposta
        await view.wait()
        
        if view.value == "confirmed":
            await self._create_buy_channel(interaction, product)
        elif view.value == "cancelled":
            await interaction.edit_original_response(
                content=f"{Emojis.INFO} Compra cancelada.",
                embed=None,
                view=None
            )
        else:
            await interaction.edit_original_response(
                content=f"{Emojis.WARNING} Tempo esgotado. Tente novamente.",
                view=None
            )
    
    async def _create_buy_channel(self, interaction: discord.Interaction, product: dict):
        """Cria canal privado de compra"""
        
        guild = interaction.guild
        
        # Verificar categoria configurada
        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            await interaction.followup.send(
                f"{Emojis.ERROR} Categoria de tickets não configurada. Use `/setup` primeiro.",
                ephemeral=True
            )
            return
        
        category = guild.get_channel(category_id)
        if not category:
            await interaction.followup.send(
                f"{Emojis.ERROR} Categoria de tickets não encontrada.",
                ephemeral=True
            )
            return
        
        try:
            # Criar nome do canal
            channel_name = f"compra-{product['id']}-{interaction.user.name}".lower()[:50]
            
            # Configurar permissões
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    attach_files=True,
                    embed_links=True
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_channels=True,
                    manage_permissions=True
                )
            }
            
            # Adicionar staff
            if config.STAFF_ROLE_ID:
                staff_role = guild.get_role(config.STAFF_ROLE_ID)
                if staff_role:
                    overwrites[staff_role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True
                    )
            
            # Criar canal
            channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic=f"Compra: {product['name']} | Cliente: {interaction.user}"
            )
            
            # Criar embed de boas-vindas
            welcome_embed = discord.Embed(
                title=f"{product['emoji']} Compra Iniciada — {product['name']}",
                description=(
                    f"Olá {interaction.user.mention}! 👋\n\n"
                    f"Seu canal de compra foi criado com sucesso.\n\n"
                    f"📦 **Produto:** {product['name']}\n"
                    f"📝 **Descrição:** {product['description']}\n"
                    f"💰 **Valor:** `R$ {product['price']:.2f}`\n\n"
                    f"---\n\n"
                    f"🔄 **Próximos passos:**\n"
                    f"1. Aguarde um membro da equipe\n"
                    f"2. Você receberá o QR Code do PIX\n"
                    f"3. Após confirmação do pagamento, entregaremos seu produto\n\n"
                    f"⏱️ **Tempo de atendimento:** Geralmente em até 10 minutos"
                ),
                color=product['color'],
                timestamp=discord.utils.utcnow()
            )
            
            # Botões de controle
            control_view = discord.ui.View()
            
            # Botão PIX
            pix_button = discord.ui.Button(
                label="📱 Gerar PIX",
                style=discord.ButtonStyle.green,
                emoji="💳",
                custom_id=f"pix_generate:{interaction.user.id}:{product['id']}"
            )
            
            # Botão Fechar
            close_button = discord.ui.Button(
                label="🔒 Fechar Compra",
                style=discord.ButtonStyle.red,
                emoji=Emojis.CLOSE,
                custom_id=f"buy_close:{interaction.user.id}:{product['id']}"
            )
            
            control_view.add_item(pix_button)
            control_view.add_item(close_button)
            
            # Enviar mensagem no canal
            await channel.send(
                content=f"{interaction.user.mention} {config.STAFF_ROLE_ID and f'<@&{config.STAFF_ROLE_ID}>'}",
                embed=welcome_embed,
                view=control_view
            )
            
            # Confirmar para o usuário
            await interaction.edit_original_response(
                content=f"{Emojis.SUCCESS} Canal de compra criado: {channel.mention}",
                embed=None,
                view=None
            )
            
            # Registrar no banco (se tiver tabela de compras)
            # await self.db.create_purchase_channel(...)
            
            logger.info(f"Buy channel created: {channel.name} for {interaction.user} - Product: {product['id']}")
            
            # Log
            await self.db.create_log(
                "shop",
                interaction.user.id,
                "buy_channel_created",
                f"Product: {product['id']} | Channel: {channel.id} | Value: {product['price']}"
            )
            
        except discord.Forbidden:
            await interaction.edit_original_response(
                content=f"{Emojis.ERROR} Não tenho permissão para criar canais.",
                embed=None,
                view=None
            )
        except Exception as e:
            logger.error(f"Error creating buy channel: {e}")
            await interaction.edit_original_response(
                content=f"{Emojis.ERROR} Erro ao criar canal de compra. Tente novamente.",
                embed=None,
                view=None
            )
    
    async def _find_user_buy_channel(self, user: discord.Member, guild: discord.Guild) -> Optional[discord.TextChannel]:
        """Procura canal de compra aberto do usuário"""
        
        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            return None
        
        category = guild.get_channel(category_id)
        if not category:
            return None
        
        for channel in category.text_channels:
            if channel.name.startswith("compra-") and user.id in [m.id for m in channel.overwrites.keys() if isinstance(m, discord.Member)]:
                # Verificar se o usuário tem permissão de leitura
                perms = channel.permissions_for(user)
                if perms.read_messages:
                    return channel
        
        return None


async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))
