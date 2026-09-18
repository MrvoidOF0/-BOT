"""
🌑 VOID Store Bot - Canal de Stock com Auto-Embed e Ticket de Compra
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio

from utils.permissions import PermissionChecker
from utils.logger import logger
from config import config


CANAL_STOCK_ID = 1549948220317106186


# ====================================
# MODAL DE INFORMAÇÕES DO CLIENTE
# ====================================

class CompraInfoModal(discord.ui.Modal, title="Informações para Compra"):
    """Modal que aparece ao clicar em Comprar"""

    nome_conta = discord.ui.TextInput(
        label="Nome da sua conta no jogo (IGN)",
        placeholder="Ex: VoidPlayer123",
        required=True,
        max_length=100
    )

    nivel_atual = discord.ui.TextInput(
        label="Seu nível atual no jogo",
        placeholder="Ex: 2400",
        required=True,
        max_length=20
    )

    fruta_atual = discord.ui.TextInput(
        label="Sua fruta atual (se aplicável)",
        placeholder="Ex: Dragon, Leopard... ou Nenhuma",
        required=False,
        max_length=100
    )

    senha_conta = discord.ui.TextInput(
        label="Senha da conta (OPCIONAL)",
        placeholder="Deixe vazio se não quiser informar agora",
        required=False,
        max_length=100
    )

    observacoes = discord.ui.TextInput(
        label="Observações / O que deseja comprar",
        placeholder="Descreva o que você viu no stock e quer comprar",
        required=True,
        style=discord.TextStyle.long,
        max_length=500
    )

    def __init__(self, produto_info: str):
        super().__init__()
        self.produto_info = produto_info

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        cog = interaction.client.get_cog("StockDisplay")
        if cog:
            await cog.criar_canal_compra(
                interaction=interaction,
                produto_info=self.produto_info,
                nome_conta=self.nome_conta.value,
                nivel_atual=self.nivel_atual.value,
                fruta_atual=self.fruta_atual.value or "Não informado",
                senha_conta=self.senha_conta.value or "Não informado",
                observacoes=self.observacoes.value
            )


# ====================================
# VIEW DO BOTÃO COMPRAR
# ====================================

class StockBuyView(discord.ui.View):
    """View com o botão Comprar para cada embed de stock"""

    def __init__(self, produto_info: str):
        super().__init__(timeout=None)
        self.produto_info = produto_info

    @discord.ui.button(
        label="Comprar Agora",
        style=discord.ButtonStyle.green,
        emoji="🛒",
        custom_id="stock:buy"
    )
    async def comprar(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Abre modal de informações antes de criar o canal"""
        modal = CompraInfoModal(produto_info=self.produto_info)
        await interaction.response.send_modal(modal)


# ====================================
# VIEW DE CONTROLE DO CANAL DE COMPRA
# ====================================

class CompraControlView(discord.ui.View):
    """Botões dentro do canal de compra criado pelo stock"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Canal",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="stock_compra:close"
    )
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("StockDisplay")
        if cog:
            await cog.fechar_canal_compra(interaction)

    @discord.ui.button(
        label="Gerar PIX",
        style=discord.ButtonStyle.green,
        emoji="💳",
        custom_id="stock_compra:pix"
    )
    async def pix_rapido(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not PermissionChecker.is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas staff pode gerar PIX.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "💳 Use `/pix-gerar valor:XX.XX cliente:@usuario` para enviar a cobrança.",
            ephemeral=True
        )


# ====================================
# COG
# ====================================

class StockDisplay(commands.Cog):
    """Sistema de stock com auto-embed e canal de compra"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.bot.add_view(CompraControlView())

    # ====================================
    # LISTENER: AUTO-EMBED
    # ====================================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Transforma mensagens no canal de stock em embeds com botão de comprar"""

        if message.author.bot:
            return

        if message.channel.id != CANAL_STOCK_ID:
            return

        # Verificar se é staff/autorizado
        if not PermissionChecker.has_authorized_role(message.author):
            return

        conteudo = message.content.strip()
        if not conteudo or len(conteudo) < 2:
            return

        # Limpar menções perigosas
        texto = conteudo.replace("@everyone", "").replace("@here", "").strip()

        # Deletar mensagem original (deixa o canal limpo)
        try:
            await message.delete()
        except discord.Forbidden:
            pass
        except Exception:
            pass

        # Criar embed
        embed = discord.Embed(
            title="📦 VOID Store — Produto Disponível",
            description=texto,
            color=0x000000,
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="🛒 Como comprar",
            value=(
                "Clique no botão **Comprar Agora** abaixo.\n"
                "Preencha suas informações e um canal privado será aberto para você."
            ),
            inline=False
        )

        embed.set_footer(
            text=f"🌑 VOID Store | {message.created_at.strftime('%d/%m/%Y %H:%M')}"
        )

        # Criar view com botão — passando o texto como identificação do produto
        view = StockBuyView(produto_info=texto[:200])

        await message.channel.send(embed=embed, view=view)

        await self.db.create_log(
            "stock", message.author.id, "auto_embed",
            f"Channel: {message.channel.id} | Len: {len(texto)}"
        )

        logger.info(f"Stock auto-embed created by {message.author}")

    # ====================================
    # CRIAR CANAL DE COMPRA (via stock)
    # ====================================

    async def criar_canal_compra(
        self,
        interaction: discord.Interaction,
        produto_info: str,
        nome_conta: str,
        nivel_atual: str,
        fruta_atual: str,
        senha_conta: str,
        observacoes: str
    ):
        """Cria canal privado de compra para o cliente que veio do stock"""

        guild = interaction.guild
        user = interaction.user

        # Verificar categoria
        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            await interaction.followup.send(
                "❌ Categoria de tickets não configurada. Fale com um admin.",
                ephemeral=True
            )
            return

        category = guild.get_channel(category_id)
        if not category:
            await interaction.followup.send(
                "❌ Categoria não encontrada.", ephemeral=True
            )
            return

        # Verificar canal duplicado
        channel_name = f"compra-stock-{user.name}".lower()[:50]
        for ch in category.text_channels:
            if ch.name == channel_name:
                await interaction.followup.send(
                    f"⚠️ Você já possui um canal de compra aberto: {ch.mention}\n"
                    f"Por favor, finalize ou feche antes de abrir um novo.",
                    ephemeral=True
                )
                return

        try:
            # Permissões do canal
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    attach_files=True
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_channels=True,
                    manage_permissions=True
                )
            }

            if config.STAFF_ROLE_ID:
                staff_role = guild.get_role(config.STAFF_ROLE_ID)
                if staff_role:
                    overwrites[staff_role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True
                    )

            # Adicionar os 3 cargos autorizados
            for role_id in config.AUTHORIZED_ROLE_IDS:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True
                    )

            # Criar canal
            channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic=f"Compra via Stock | Cliente: {user} | {produto_info[:80]}"
            )

            # Embed principal do canal
            embed = discord.Embed(
                title="🛒 Nova Compra via Stock",
                description=f"Canal criado para {user.mention}",
                color=0x000000,
                timestamp=discord.utils.utcnow()
            )

            embed.add_field(
                name="📦 Produto Solicitado",
                value=f"```{produto_info[:400]}```",
                inline=False
            )

            embed.add_field(
                name="👤 Informações da Conta",
                value=(
                    f"**IGN:** `{nome_conta}`\n"
                    f"**Nível:** `{nivel_atual}`\n"
                    f"**Fruta:** `{fruta_atual}`\n"
                    f"**Senha:** `{'🔒 Não informada' if senha_conta == 'Não informado' else senha_conta}`"
                ),
                inline=True
            )

            embed.add_field(
                name="📝 Observações",
                value=observacoes,
                inline=True
            )

            embed.add_field(
                name="📋 Próximos Passos",
                value=(
                    "1. ⏳ Aguarde a equipe\n"
                    "2. 💳 Você receberá o PIX\n"
                    "3. ✅ Pague e envie o comprovante\n"
                    "4. 🎮 Receba seu produto!"
                ),
                inline=False
            )

            embed.set_footer(text="🌑 VOID Store | Compra segura e rápida")

            # Mencionar staff
            staff_mention = f"<@&{config.STAFF_ROLE_ID}>" if config.STAFF_ROLE_ID else ""

            await channel.send(
                content=f"{user.mention} {staff_mention}",
                embed=embed,
                view=CompraControlView()
            )

            await interaction.followup.send(
                f"✅ Canal de compra criado: {channel.mention}\n"
                f"Nossa equipe responderá em breve!",
                ephemeral=True
            )

            await self.db.create_log(
                "stock", user.id, "buy_channel_created",
                f"Channel: {channel.id} | Product: {produto_info[:80]}"
            )

            logger.info(f"Stock buy channel created for {user}: {channel.name}")

        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Sem permissão para criar canais.", ephemeral=True
            )
        except Exception as e:
            logger.error(f"Erro ao criar canal de compra via stock: {e}")
            await interaction.followup.send(
                "❌ Erro ao criar canal. Tente novamente.", ephemeral=True
            )

    # ====================================
    # FECHAR CANAL DE COMPRA
    # ====================================

    async def fechar_canal_compra(self, interaction: discord.Interaction):
        """Fecha o canal de compra via stock"""

        is_staff = PermissionChecker.is_staff(interaction.user)
        is_owner = interaction.channel.topic and str(interaction.user) in interaction.channel.topic

        if not (is_staff or is_owner):
            await interaction.response.send_message(
                "❌ Você não pode fechar este canal.", ephemeral=True
            )
            return

        # Confirmação
        view = discord.ui.View()
        confirm = discord.ui.Button(label="Confirmar", style=discord.ButtonStyle.red, emoji="✅")
        cancel = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.gray, emoji="❌")
        confirmado = False

        async def confirm_cb(i: discord.Interaction):
            nonlocal confirmado
            confirmado = True
            view.stop()
            await i.response.defer()

        async def cancel_cb(i: discord.Interaction):
            view.stop()
            await i.response.defer()

        confirm.callback = confirm_cb
        cancel.callback = cancel_cb
        view.add_item(confirm)
        view.add_item(cancel)

        await interaction.response.send_message(
            "⚠️ Tem certeza que deseja fechar este canal?",
            view=view,
            ephemeral=True
        )

        await view.wait()

        if confirmado:
            try:
                await interaction.edit_original_response(
                    content="✅ Canal será fechado em instantes.", view=None
                )

                embed = discord.Embed(
                    title="🔒 Canal Fechado",
                    description=f"Fechado por {interaction.user.mention}. Deletando em 5 segundos...",
                    color=0xff0000
                )
                await interaction.channel.send(embed=embed)

                await asyncio.sleep(5)
                await interaction.channel.delete()

            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Erro ao fechar canal de compra: {e}")
        else:
            await interaction.edit_original_response(
                content="❌ Fechamento cancelado.", view=None
            )

    # ====================================
    # COMANDOS MANUAIS
    # ====================================

    @app_commands.command(name="stock-embed", description="📦 Cria embed manual no canal de stock")
    @app_commands.describe(
        texto="Texto do anúncio (qualquer tamanho)",
        titulo="Título do embed (opcional)",
        cor_hex="Cor em hex (opcional, ex: #9b59b6)"
    )
    async def stock_embed_command(
        self,
        interaction: discord.Interaction,
        texto: str,
        titulo: Optional[str] = None,
        cor_hex: Optional[str] = None
    ):
        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        cor = 0x000000
        if cor_hex:
            try:
                cor = int(cor_hex.replace("#", ""), 16)
            except ValueError:
                pass

        embed = discord.Embed(
            title=titulo or "📦 VOID Store — Produto Disponível",
            description=texto,
            color=cor,
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="🛒 Como comprar",
            value="Clique no botão **Comprar Agora** para abrir um canal privado de atendimento.",
            inline=False
        )

        embed.set_footer(
            text=f"🌑 VOID Store | {interaction.user.display_name}"
        )

        view = StockBuyView(produto_info=texto[:200])

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(StockDisplay(bot))
