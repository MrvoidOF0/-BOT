"""
🌑 VOID Store Bot - Sistema de Loja Final
Regra: O painel NUNCA some. Botões sem preços. Modal de nick obrigatório.
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
# CONFIGURAÇÃO DOS PRODUTOS
# ====================================

PRODUTOS = {
    "v4": {"nome": "Engrenagem V4", "emoji": "⚙️", "cor": 0x2b2d31},
    "frutas": {"nome": "Frutas", "emoji": "🍎", "cor": 0x9b59b6},
    "levels": {"nome": "Levels", "emoji": "⬆️", "cor": 0x3498db},
    "fragmentos": {"nome": "Fragmentos", "emoji": "💎", "cor": 0xe74c3c},
    "money": {"nome": "Money / Beli", "emoji": "💰", "cor": 0xf39c12},
    "materiais": {"nome": "Farm de Materiais", "emoji": "📦", "cor": 0x27ae60},
}

# ====================================
# MODAL DE INFORMAÇÕES (NICK)
# ====================================

class NickModal(discord.ui.Modal, title="Finalizar Pedido"):
    """Este modal aparece ao clicar no botão da loja"""
    
    nick = discord.ui.TextInput(
        label="Qual o seu Nick no jogo?",
        placeholder="Digite seu nick (Opcional)",
        required=False,
        max_length=100
    )

    def __init__(self, produto_id: str):
        super().__init__()
        self.produto_id = produto_id

    async def on_submit(self, interaction: discord.Interaction):
        """Quando o cliente envia o modal, o canal é criado"""
        # IMPORTANTE: Usamos defer para o painel da loja continuar lá sem alterações
        await interaction.response.defer(ephemeral=True)
        
        cog = interaction.client.get_cog("Shop")
        if cog:
            await cog.processar_abertura_canal(
                interaction, 
                self.produto_id, 
                self.nick.value.strip() or "Não informado"
            )

# ====================================
# COG SHOP
# ====================================

class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    # ====================================
    # LISTENER DE INTERAÇÃO (SEGURANÇA TOTAL)
    # ====================================

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Captura cliques nos botões com IDs específicos"""
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")

        # Se o botão começar com 'shop:', abre o modal correspondente
        if custom_id.startswith("shop:"):
            produto_id = custom_id.replace("shop:", "")
            if produto_id in PRODUTOS:
                await interaction.response.send_modal(NickModal(produto_id))
            return

    # ====================================
    # COMANDO DO PAINEL
    # ====================================

    @app_commands.command(name="loja-painel", description="🛒 Envia o painel de compras")
    async def loja_painel(self, interaction: discord.Interaction):
        """Envia a mensagem com botões que não expiram"""
        
        if not await PermissionChecker.check_interaction_permissions(interaction, require_authorized=True):
            return

        embed = discord.Embed(
            title="🌑 𝐕𝐎𝐈𝐃 𝐒𝐭𝐨𝐫𝐞 | Loja Blox Fruits",
            description=(
                "Seja bem-vindo à nossa loja oficial! 🛒\n\n"
                "Para realizar um pedido, clique no botão do serviço desejado abaixo.\n"
                "Um canal de atendimento exclusivo será aberto para você.\n\n"
                "**🚀 Como funciona:**\n"
                "1️⃣ Clique no botão do produto\n"
                "2️⃣ Informe seu nick no formulário\n"
                "3️⃣ Combine os detalhes no ticket\n"
                "4️⃣ Realize o pagamento via PIX"
            ),
            color=0x000000
        )
        
        # Tabela de preços apenas no texto do Embed
        precos = (
            "⚙️ **Engrenagem V4** — R$ 29,90\n"
            "🍎 **Frutas** — R$ 15,00\n"
            "⬆️ **Levels** — R$ 19,90\n"
            "💎 **Fragmentos** — R$ 12,00\n"
            "💰 **Money / Beli** — R$ 9,90\n"
            "📦 **Farm de Materiais** — R$ 24,90"
        )
        embed.add_field(name="💳 Tabela de Preços", value=precos, inline=False)
        embed.set_footer(text="🌑 VOID Store | Atendimento Rápido")

        # Criação dos botões SEM PREÇO no label
        view = discord.ui.View(timeout=None) # timeout=None faz os botões durarem pra sempre
        
        for pid, pinfo in PRODUTOS.items():
            view.add_item(discord.ui.Button(
                label=pinfo["nome"], 
                style=discord.ButtonStyle.blurple,
                emoji=pinfo["emoji"],
                custom_id=f"shop:{pid}" # ID único para o listener
            ))

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel enviado com sucesso!", ephemeral=True)

    # ====================================
    # LÓGICA DE CRIAÇÃO DO CANAL
    # ====================================

    async def processar_abertura_canal(self, interaction: discord.Interaction, produto_id: str, nick: str):
        guild = interaction.guild
        user = interaction.user
        produto = PRODUTOS[produto_id]

        # Verificar categoria
        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            return await interaction.followup.send("❌ Erro: Categoria de tickets não configurada.", ephemeral=True)

        category = guild.get_channel(category_id)
        channel_name = f"🛒-{produto_id}-{user.name}".lower()[:50]

        # Verificar se já tem canal aberto
        for ch in category.text_channels:
            if ch.name == channel_name:
                return await interaction.followup.send(f"⚠️ Você já tem um ticket de compra aberto: {ch.mention}", ephemeral=True)

        try:
            # Permissões do canal
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
            }

            # Adicionar cargos autorizados (seus 3 cargos de staff)
            for rid in config.AUTHORIZED_ROLE_IDS:
                r = guild.get_role(rid)
                if r: overwrites[r] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            # Criar canal
            channel = await category.create_text_channel(name=channel_name, overwrites=overwrites)

            # Embed de boas vindas dentro do Ticket
            embed = discord.Embed(
                title=f"{produto['emoji']} Novo Pedido — {produto['nome']}",
                description=f"Olá {user.mention}, este é seu canal de atendimento exclusivo!",
                color=produto['cor'],
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="🎮 Nick do Cliente", value=f"`{nick}`", inline=True)
            embed.add_field(name="📦 Produto", value=produto['nome'], inline=True)
            embed.add_field(name="💬 O que fazer?", value="Diga qual item ou serviço específico você deseja. Um staff irá te atender e gerar o PIX.", inline=False)
            embed.set_footer(text="🌑 VOID Store | Use os botões abaixo para gerenciar")

            # Botões de controle do ticket
            view = discord.ui.View(timeout=None)
            view.add_item(discord.ui.Button(label="Fechar Canal", style=discord.ButtonStyle.red, emoji="🔒", custom_id="svc:fechar"))
            view.add_item(discord.ui.Button(label="Gerar PIX", style=discord.ButtonStyle.green, emoji="💳", custom_id="canal:pix"))

            await channel.send(content=f"{user.mention} | <@&{config.STAFF_ROLE_ID or ''}>", embed=embed, view=view)
            
            # Resposta ephemeral avisando que abriu (isso não apaga o painel)
            await interaction.followup.send(f"✅ Seu ticket foi criado com sucesso: {channel.mention}", ephemeral=True)

        except Exception as e:
            logger.error(f"Erro ao abrir canal de compra: {e}")
            await interaction.followup.send("❌ Ocorreu um erro ao abrir o canal.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))
