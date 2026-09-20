"""
🌑 VOID Store Bot - Sistema de Loja (Reescrito)
Botões sem valores. Modal de nick antes de abrir.
O painel NÃO SOME ao clicar.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio

from utils.permissions import PermissionChecker
from utils.logger import logger
from config import config

# ====================================
# DADOS DOS PRODUTOS DA LOJA
# ====================================

PRODUTOS_LOJA = [
    {"id": "v4",         "nome": "⚙️ Engrenagem V4",  "preco": 29.90, "cor": 0x2b2d31},
    {"id": "frutas",     "nome": "🍎 Frutas",         "preco": 15.00, "cor": 0x9b59b6},
    {"id": "levels",     "nome": "⬆️ Levels",         "preco": 19.90, "cor": 0x3498db},
    {"id": "fragmentos", "nome": "💎 Fragmentos",     "preco": 12.00, "cor": 0xe74c3c},
    {"id": "money",      "nome": "💰 Money / Beli",   "preco": 9.90,  "cor": 0xf39c12},
    {"id": "materiais",  "nome": "📦 Farm Materiais", "preco": 24.90, "cor": 0x27ae60},
]

# ====================================
# MODAL DE NICK (Loja)
# ====================================

class ShopNickModal(discord.ui.Modal, title="Informações da Conta"):
    nick = discord.ui.TextInput(
        label="Nick da sua conta no jogo (opcional)",
        placeholder="Ex: VoidPlayer123",
        required=False,
        max_length=100
    )

    def __init__(self, produto_id: str, produto_nome: str):
        super().__init__()
        self.produto_id = produto_id
        self.produto_nome = produto_nome

    async def on_submit(self, interaction: discord.Interaction):
        # AQUI ESTÁ O SEGREDO: Usar defer para não fechar/editar o painel original
        await interaction.response.defer(ephemeral=True)
        
        cog = interaction.client.get_cog("Shop")
        if cog:
            await cog.criar_canal_compra(
                interaction, 
                self.produto_id, 
                self.produto_nome, 
                self.nick.value.strip() or "Não informado"
            )

# ====================================
# COG SHOP
# ====================================

class Shop(commands.Cog):
    """Sistema de Loja"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    # ====================================
    # INTERCEPTADOR DE BOTÕES (Global)
    # ====================================

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")

        # Identifica botões da loja: "buy:id"
        if custom_id.startswith("buy:"):
            produto_id = custom_id.replace("buy:", "")
            
            # Achar o nome do produto na lista
            produto_nome = "Produto"
            for p in PRODUTOS_LOJA:
                if p["id"] == produto_id:
                    produto_nome = p["nome"]
                    break
            
            modal = ShopNickModal(produto_id, produto_nome)
            await interaction.response.send_modal(modal)
            return

    # ====================================
    # COMANDO DO PAINEL
    # ====================================

    @app_commands.command(name="loja-painel", description="🛒 Cria o painel de compras da loja")
    async def loja_painel(self, interaction: discord.Interaction):
        # Verificar se tem um dos cargos autorizados
        if not await PermissionChecker.check_interaction_permissions(interaction, require_authorized=True):
            return

        embed = discord.Embed(
            title="🌑 𝐕𝐎𝐈𝐃 𝐒𝐭𝐨𝐫𝐞 | Loja Oficial",
            description=(
                "Bem-vindo à **VOID Store**! 🌑\n\n"
                "Clique no botão abaixo do produto desejado para iniciar sua compra.\n"
                "Um canal privado será criado para atendimento exclusivo.\n\n"
                "**💡 Como funciona:**\n"
                "1. Clique no botão do produto\n"
                "2. Informe seu Nick (opcional)\n"
                "3. Um canal privado será aberto\n"
                "4. Nossa equipe entrará em contato para gerar o PIX"
            ),
            color=0x000000
        )

        # Lista de preços no Embed (não no botão)
        lista_txt = ""
        for p in PRODUTOS_LOJA:
            lista_txt += f"{p['nome']} — `R$ {p['preco']:.2f}`\n"
        
        embed.add_field(name="📦 Produtos Disponíveis", value=lista_txt, inline=False)
        embed.set_footer(text="🌑 VOID Store | Pagamento via PIX")

        # Criar botões (SEM VALORES NO LABEL)
        view = discord.ui.View(timeout=None)
        
        # Organizar botões em linhas (máximo 5 por linha)
        for p in PRODUTOS_LOJA:
            btn = discord.ui.Button(
                label=p["nome"], # Apenas o nome!
                style=discord.ButtonStyle.blurple,
                custom_id=f"buy:{p['id']}" # ID fixo para o listener capturar
            )
            view.add_item(btn)

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel da loja enviado!", ephemeral=True)

    # ====================================
    # LÓGICA DE CRIAR CANAL
    # ====================================

    async def criar_canal_compra(self, interaction: discord.Interaction, produto_id: str, produto_nome: str, nick: str):
        guild = interaction.guild
        user = interaction.user

        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            await interaction.followup.send("❌ Categoria não configurada.", ephemeral=True)
            return

        category = guild.get_channel(category_id)
        channel_name = f"🛒-{produto_id}-{user.name}".lower()[:50]

        # Verificar se já existe
        for ch in category.text_channels:
            if ch.name == channel_name:
                await interaction.followup.send(f"⚠️ Você já tem um canal aberto: {ch.mention}", ephemeral=True)
                return

        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
            }

            # Adicionar cargos autorizados e staff
            for rid in config.AUTHORIZED_ROLE_IDS:
                r = guild.get_role(rid)
                if r: overwrites[r] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)

            # Embed de boas vindas no canal
            embed = discord.Embed(
                title=f"🛒 Pedido de Compra — {produto_nome}",
                description=f"Olá {user.mention}! Seu canal de compra foi aberto.",
                color=0x000000
            )
            embed.add_field(name="🎮 Nick informado", value=f"`{nick}`", inline=True)
            embed.add_field(name="📦 Produto", value=produto_nome, inline=True)
            embed.add_field(name="💬 Instrução", value="Aguarde um staff. Informe os detalhes do seu pedido e peça o PIX.", inline=False)
            
            # Botões de controle
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Fechar Canal", style=discord.ButtonStyle.red, emoji="🔒", custom_id="svc:fechar"))
            view.add_item(discord.ui.Button(label="Gerar PIX", style=discord.ButtonStyle.green, emoji="💳", custom_id="canal:pix"))

            await channel.send(content=f"{user.mention}", embed=embed, view=view)
            await interaction.followup.send(f"✅ Canal criado: {channel.mention}", ephemeral=True)

        except Exception as e:
            logger.error(f"Erro Loja: {e}")
            await interaction.followup.send("❌ Erro ao criar canal.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))
