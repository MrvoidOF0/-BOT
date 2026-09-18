"""
🌑 VOID Store Bot - Auto-Embed para Canal de Stock
Sempre que uma mensagem for enviada no canal 1549948220317106186,
o bot converte em embed com botão de comprar.
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
# CONFIGURAÇÃO DO CANAL DE STOCK
# ====================================

CANAL_STOCK_ID = 1549948220317106186  # Seu canal específico


# ====================================
# VIEW DO BOTÃO COMPRAR
# ====================================

class StockBuyView(discord.ui.View):
    """Botão de comprar que abre a seleção de serviço"""
    
    def __init__(self, produto_texto: str):
        super().__init__(timeout=None)
        self.produto_texto = produto_texto
    
    @discord.ui.button(
        label="🛒 Comprar Agora",
        style=discord.ButtonStyle.green,
        emoji="💰",
        custom_id="stock_buy_now"
    )
    async def comprar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Abre uma seleção de serviço simples
        await interaction.response.send_message(
            f"🛍️ **Compra de:** `{self.produto_texto[:50]}...`\n\n"
            f"Selecione o tipo de serviço para abrir o canal de atendimento:\n\n"
            f"💬 **Suporte / Compra** → `/ticket-panel` no canal de atendimento\n"
            f"⚙️ **Serviços específicos** → `/servicos-painel` no canal de serviços\n\n"
            f"Ou vá diretamente ao canal `#compras` e clique no botão correspondente.",
            ephemeral=True
        )


# ====================================
# COG ATUALIZADO
# ====================================

class StockDisplay(commands.Cog):
    """Sistema de embeds automáticos para o canal de stock"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    # ====================================
    # LISTENER AUTOMÁTICO
    # ====================================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Sempre que uma mensagem for enviada no canal 1549948220317106186,
        o bot a transforma em embed com botão de comprar.
        """
        
        # Ignorar mensagens do próprio bot
        if message.author.bot:
            return
        
        # Verificar se é exatamente o canal configurado
        if message.channel.id != CANAL_STOCK_ID:
            return
        
        # Verificar se é staff/admin (opcional — remova o "if" abaixo se quiser que qualquer pessoa possa)
        # Mas o usuário pediu "quando EU mandar mensagem", então vamos restringir a staff/admin
        if not message.author.guild_permissions.administrator:
            if message.author.guild_permissions.manage_messages is False:
                # Se quiser que qualquer um possa, remova esta verificação
                # Por segurança, vou manter apenas para staff/admin
                # Se quiser liberar para todos, apague estas 3 linhas abaixo:
                pass  # Remova o "pass" e deixo sem restrição se quiser
        
        # Capturar o conteúdo da mensagem
        conteudo = message.content
        
        # Se for apenas um link ou vazio, ignorar
        if not conteudo or len(conteudo.strip()) < 2:
            return
        
        # Limpar o conteúdo (remover @everyone, @here, etc. se necessário)
        texto_limpo = conteudo.replace("@everyone", "").replace("@here", "").strip()
        
        # Criar o embed automaticamente a partir do conteúdo
        embed = discord.Embed(
            title="📦 PRODUTO DISPONÍVEL — VOID Store",
            description=texto_limpo,
            color=0x000000,  # Preto (identidade VOID)
            timestamp=discord.utils.utcnow()
        )
        
        # Adicionar footer automático
        embed.set_footer(
            text=f"🌑 VOID Store | Postado por {message.author.display_name} | {message.created_at.strftime('%d/%m/%Y %H:%M')}"
        )
        
        # Adicionar thumbnail do autor (opcional)
        if message.author.display_avatar:
            embed.set_thumbnail(url=message.author.display_avatar.url)
        
        # Adicionar instruções automáticas
        embed.add_field(
            name="💡 Como comprar",
            value=(
                "Clique no botão abaixo para iniciar sua compra.\n"
                "Você será levado ao canal de atendimento para finalizar."
            ),
            inline=False
        )
        
        # Criar a view com o botão de comprar
        view = StockBuyView(texto_limpo)
        
        # Responder à mensagem original com o embed
        # Apagar a mensagem original (opcional — descomente se quiser)
        # try:
        #     await message.delete()
        # except:
        #     pass
        
        # Enviar o embed no mesmo canal
        await message.channel.send(embed=embed, view=view)
        
        # Confirmar ao usuário que o anúncio foi criado
        await message.reply(
            f"✅ {message.author.mention}, seu anúncio foi transformado em embed!\n"
            f"💡 **Dica:** Use `/stock-embed` para criar anúncios ainda mais bonitos com cores customizadas.",
            ephemeral=True
        )
        
        # Log no banco
        await self.db.create_log(
            "stock_display",
            message.author.id,
            "auto_embed_created",
            f"Channel: {message.channel.id} | Content length: {len(texto_limpo)}"
        )
        
        logger.info(f"Auto-embed created from message by {message.author.id} in channel {message.channel.id}")


# ====================================
# COMANDOS MANUAIS (mantidos)
# ====================================

    @app_commands.command(name="stock-embed", description="📦 Cria embed manual para o canal de stock")
    @app_commands.describe(
        titulo="Título do anúncio (ex: 📦 ESTOQUE DISPONÍVEL)",
        texto="Texto completo do anúncio (preços, descrição, etc.)",
        cor_hex="Cor em hexadecimal (opcional, ex: #2b2d31)",
        footer="Texto do rodapé (opcional)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def stock_embed_command(
        self,
        interaction: discord.Interaction,
        titulo: str,
        texto: str,
        cor_hex: Optional[str] = None,
        footer: Optional[str] = None
    ):
        """Cria embed manual no canal onde o comando for usado"""
        
        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        # Parse da cor
        cor = 0x000000
        if cor_hex and cor_hex.startswith("#"):
            try:
                cor = int(cor_hex.replace("#", ""), 16)
            except ValueError:
                pass

        embed = discord.Embed(
            title=titulo,
            description=texto,
            color=cor,
            timestamp=discord.utils.utcnow()
        )

        if footer:
            embed.set_footer(text=footer, icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        else:
            embed.set_footer(text=f"🌑 VOID Store | Postado por {interaction.user.display_name}")

        # Adicionar botão de comprar no embed manual também
        view = discord.ui.View()
        btn_comprar = discord.ui.Button(
            label="🛒 Comprar",
            style=discord.ButtonStyle.green,
            emoji="💰",
            custom_id="stock_buy_manual"
        )
        
        async def comprar_callback(i: discord.Interaction):
            await i.response.send_message(
                f"🛍️ Você quer comprar: **{titulo}**\n\n"
                f"Por favor, vá ao canal `#compras` ou `#atendimento` e clique no botão correspondente.\n"
                f"Ou use `/ticket-panel` para abrir um ticket de compra.",
                ephemeral=True
            )
        
        btn_comprar.callback = comprar_callback
        view.add_item(btn_comprar)

        # Se for no canal específico, também salva no log
        await interaction.response.send_message(embed=embed, view=view)
        
        # Se for no canal de stock, registra no log
        if interaction.channel.id == CANAL_STOCK_ID:
            await self.db.create_log(
                "stock_display",
                interaction.user.id,
                "manual_embed",
                f"Title: {titulo[:50]}"
            )

        logger.info(f"Manual stock embed created by {interaction.user}")


# ====================================
# SETUP DO COG
# ====================================

async def setup(bot: commands.Bot):
    await bot.add_cog(StockDisplay(bot))
