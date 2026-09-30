"""
🌑 VOID Store Bot - Cog de Contas Aleatórias
Painel de compra de Contas Random com criação de canal e botão de fechamento.
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio

# ID da categoria onde os canais de atendimento serão criados
CATEGORY_ID = 1551636304989519993


# ====================================
# VIEWS INTERATIVAS
# ====================================

class TicketCloseView(discord.ui.View):
    """View dos botões dentro do canal privado de compra da conta"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Encerrar Canal",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="ticket:contas_close"
    )
    async def btn_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        embed_closing = discord.Embed(
            title="🔒 Encerramento de Atendimento",
            description="Este canal será **excluído** em **5 segundos**...",
            color=0xEF4444
        )
        embed_closing.set_footer(text="VOID Store • Canal sendo encerrado")
        await interaction.followup.send(embed=embed_closing)

        await asyncio.sleep(5)

        try:
            await interaction.channel.delete(reason=f"Atendimento de conta encerrado por {interaction.user}")
        except Exception as e:
            print(f"Erro ao deletar canal {interaction.channel.name}: {e}")

    @discord.ui.button(
        label="Gerar Pagamento PIX",
        style=discord.ButtonStyle.success,
        emoji="💳",
        custom_id="ticket:contas_pix"
    )
    async def btn_pix(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Tenta usar a cog do PIX caso exista
        cog_pix = interaction.client.get_cog("Pix")
        if cog_pix and hasattr(cog_pix, "pix_gerar"):
            await cog_pix.pix_gerar(interaction)
        else:
            embed_pix = discord.Embed(
                title="💳 Chave PIX | VOID Store",
                description="Envie o valor correspondente para a chave Pix abaixo e mande o comprovante neste canal:\n\n`pix@voidstore.com`",
                color=0x22C55E
            )
            await interaction.response.send_message(embed=embed_pix, ephemeral=True)


class ContasPublicView(discord.ui.View):
    """View pública do painel de contas com o botão para abrir o canal"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Comprar Conta Aleatória",
        style=discord.ButtonStyle.primary,
        emoji="🎲",
        custom_id="contas:open_ticket"
    )
    async def btn_buy(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        # Nome do canal individual
        channel_name = f"🎲-conta-{user.name}".lower().replace(" ", "-")

        # Verifica se o cliente já possui um canal aberto
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(
                f"⚠️ Você já possui um canal de compra aberto: {existing_channel.mention}",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Busca a categoria onde o canal deve ser criado
        category = guild.get_channel(CATEGORY_ID)
        if not isinstance(category, discord.CategoryChannel):
            category = None

        # Permissões do canal privado
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        try:
            # Criando o canal dentro da categoria especificada
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"Canal de compra de Conta Aleatória aberto por {user}"
            )

            embed_ticket = discord.Embed(
                title="🎲 VOID Store | Atendimento de Conta Aleatória",
                description=(
                    f"Seu canal exclusivo de compra foi aberto com sucesso!\n\n"
                    f"👤 **Cliente:** {user.mention}\n"
                    f"📦 **Produto:** Conta Blox Fruits Aleatória (Random)\n"
                    f"⚡ **Status:** Aguardando Pagamento / Staff\n\n"
                    "📝 **Instruções:**\n"
                    "1. Clique no botão **Gerar Pagamento PIX** para obter os dados de pagamento.\n"
                    "2. Envie o comprovante aqui no chat se necessário.\n"
                    "3. Após a confirmação, os dados da conta serão entregues por um atendente.\n"
                    "4. Para cancelar ou fechar este chat, clique em **Encerrar Canal**."
                ),
                color=0x2B2D31
            )
            embed_ticket.set_footer(text="VOID Store • Atendimento Seguro e Qualificado")

            # Envia o embed com os botões de controle (PIX e Fechar)
            await channel.send(content=f"{user.mention}", embed=embed_ticket, view=TicketCloseView())
            await interaction.followup.send(f"✅ Seu canal de compra foi criado: {channel.mention}", ephemeral=True)

        except Exception as e:
            print(f"Erro ao criar canal de compra de conta para {user}: {e}")
            await interaction.followup.send("❌ Não foi possível criar o canal. Verifique as permissões do bot.", ephemeral=True)


# ====================================
# COG / COMANDO SLASH
# ====================================

class Contas(commands.Cog):
    """Gerenciamento do painel de Contas Aleatórias da VOID Store"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        """Registra as Views persistentes no bot"""
        self.bot.add_view(ContasPublicView())
        self.bot.add_view(TicketCloseView())

    @app_commands.command(
        name="contas",
        description="🎲 Publica o painel profissional de compra de Contas Aleatórias"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def contas_cmd(self, interaction: discord.Interaction):
        """Envia o painel principal de Contas Aleatórias no canal"""

        embed = discord.Embed(
            title="🎲 CONTAS ALEATÓRIAS | VOID STORE",
            description=(
                "Adquira sua conta do Blox Fruits com o melhor preço e entrega garantida!\n\n"
                "📊 **Informações da Conta:**\n"
                "> 🔹 Level, Frutas e Estilos de Luta aleatórios\n"
                "> 🔹 Chance de conter itens e Game Passes raros\n"
                "> 🔹 Acesso total e segurança na entrega\n\n"
                "💳 **Pagamento seguro via PIX**\n"
                "⚡ **Entrega rápida após confirmação**\n"
                "🎟️ **Atendimento exclusivo por canal privado**\n\n"
                "Clique no botão abaixo para abrir seu canal de compra."
            ),
            color=0x2B2D31
        )

        embed.set_footer(
            text="VOID Store • Clique no botão abaixo para iniciar",
            icon_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None
        )

        view = ContasPublicView()

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel de Contas Aleatórias publicado com sucesso!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Contas(bot))
