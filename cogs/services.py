"""
🌑 VOID Store Bot - Cog de Atendimento e Gerenciamento de Serviços/Tickets
Painéis dedicados para Blox Fruits com tabelas de valores e suporte completo.
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils.logger import setup_logger

logger = setup_logger("Services")


# ====================================
# CONFIGURAÇÕES DOS PAINÉIS DE SERVIÇOS
# ====================================

SERVICOS_CONFIG = {
    "v4": {
        "titulo": "🌑 VOID Store | ⚡ Desbloqueio V4 & Gears",
        "descricao": (
            "Obtenha os melhores pacotes com a maior rapidez e segurança do mercado.\n\n"
            "📊 **Tabela de Valores**\n"
            "> 🔹 Gear 1 ➔ **R$ 8.00**\n"
            "> 🔹 Gear 2 ➔ **R$ 8.00**\n"
            "> 🔹 Gear 3 ➔ **R$ 10.00**\n"
            "> 🔹 Gear 4 ➔ **R$ 12.00**\n"
            "> 👑 V4 Completa ➔ **R$ 30.00**\n\n"
            "❓ **Como comprar?**\n"
            "Clique no botão abaixo correspondente ao pacote desejado para abrir um canal de compra exclusivo."
        ),
        "cor": 0x9333EA,  # Roxo
        "emoji": "⚡",
        "label": "Comprar V4 / Gears"
    },
    "level": {
        "titulo": "🌑 VOID Store | 📈 Farm de Level",
        "descricao": (
            "Obtenha os melhores pacotes com a maior rapidez e segurança do mercado.\n\n"
            "📊 **Tabela de Valores**\n"
            "> 🔹 +100 níveis ➔ **R$ 2.00**\n"
            "> 🔹 +300 níveis ➔ **R$ 5.00**\n"
            "> 🔹 +500 níveis ➔ **R$ 8.00**\n"
            "> 🔹 +1.000 níveis ➔ **R$ 14.00**\n"
            "> 👑 Level Máximo ➔ **R$ 22.00**\n\n"
            "❓ **Como comprar?**\n"
            "Clique no botão abaixo correspondente ao pacote desejado para abrir um canal de compra exclusivo."
        ),
        "cor": 0x3B82F6,  # Azul
        "emoji": "📈",
        "label": "Comprar Farm de Level"
    },
    "materiais": {
        "titulo": "🌑 VOID Store | 📦 Farm de Materiais",
        "descricao": (
            "Obtenha os melhores pacotes com a maior rapidez e segurança do mercado.\n\n"
            "📊 **Tabela de Valores**\n"
            "> 🔹 Comuns 100x ➔ **R$ 2.00**\n"
            "> 🔹 Incomuns 100x ➔ **R$ 3.00**\n"
            "> 🔹 Raros 100x ➔ **R$ 5.00**\n"
            "> 🔹 Especiais 100x ➔ **R$ 7.00**\n\n"
            "❓ **Como comprar?**\n"
            "Clique no botão abaixo correspondente ao pacote desejado para abrir um canal de compra exclusivo."
        ),
        "cor": 0x10B981,  # Verde
        "emoji": "📦",
        "label": "Comprar Materiais"
    },
    "money": {
        "titulo": "🌑 VOID Store | 💰 Farm de Money (Beli)",
        "descricao": (
            "Obtenha os melhores pacotes com a maior rapidez e segurança do mercado.\n\n"
            "📊 **Tabela de Valores**\n"
            "> 🔹 5M Beli ➔ **R$ 4.00**\n"
            "> 🔹 10M Beli ➔ **R$ 7.00**\n"
            "> 🔹 25M Beli ➔ **R$ 15.00**\n"
            "> 🔹 50M Beli ➔ **R$ 27.00**\n\n"
            "❓ **Como comprar?**\n"
            "Clique no botão abaixo correspondente ao pacote desejado para abrir um canal de compra exclusivo."
        ),
        "cor": 0xEAB308,  # Amarelo
        "emoji": "💰",
        "label": "Comprar Beli"
    },
    "fragments": {
        "titulo": "🌑 VOID Store | 🔮 Farm de Fragments",
        "descricao": (
            "Obtenha os melhores pacotes com a maior rapidez e segurança do mercado.\n\n"
            "📊 **Tabela de Valores**\n"
            "> 🔹 5.000 Fragments ➔ **R$ 3.00**\n"
            "> 🔹 10.000 Fragments ➔ **R$ 6.00**\n"
            "> 🔹 25.000 Fragments ➔ **R$ 13.00**\n"
            "> 🔹 50.000 Fragments ➔ **R$ 24.00**\n\n"
            "❓ **Como comprar?**\n"
            "Clique no botão abaixo correspondente ao pacote desejado para abrir um canal de compra exclusivo."
        ),
        "cor": 0x8B5CF6,  # Roxo Claro
        "emoji": "🔮",
        "label": "Comprar Fragments"
    },
    "frutas": {
        "titulo": "🌑 VOID Store | 🍎 Farm de Frutas",
        "descricao": (
            "Obtenha os melhores pacotes com a maior rapidez e segurança do mercado.\n\n"
            "📊 **Tabela de Valores**\n"
            "> 🔹 1 hora ➔ **R$ 3.00**\n"
            "> 🔹 2 horas ➔ **R$ 5.00**\n"
            "> 🔹 3 horas ➔ **R$ 7.00**\n"
            "> 🔹 5 horas ➔ **R$ 10.00**\n"
            "> 🔹 10 horas ➔ **R$ 18.00**\n\n"
            "❓ **Como comprar?**\n"
            "Clique no botão abaixo correspondente ao pacote desejado para abrir um canal de compra exclusivo."
        ),
        "cor": 0xEF4444,  # Vermelho
        "emoji": "🍎",
        "label": "Comprar Farm de Frutas"
    }
}


# ====================================
# VIEWS INTERATIVAS
# ====================================

class OpenTicketView(discord.ui.View):
    """Painel público com botão para criação de ticket"""

    def __init__(self, service_type: str = "v4", label: str = "Comprar", emoji: str = "🛒"):
        super().__init__(timeout=None)
        
        btn = discord.ui.Button(
            label=label,
            style=discord.ButtonStyle.primary,
            emoji=emoji,
            custom_id=f"ticket:open:{service_type}"
        )
        btn.callback = self.btn_open_ticket
        self.add_item(btn)

    async def btn_open_ticket(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        custom_id = interaction.data.get("custom_id", "ticket:open:v4")
        service_type = custom_id.split(":")[-1] if len(custom_id.split(":")) > 2 else "v4"

        channel_name = f"🛒-{service_type}-{user.name}".lower().replace(" ", "-")

        # Verifica se o utilizador já tem um canal deste serviço aberto
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(
                f"⚠️ Já possui um canal de atendimento aberto para este serviço: {existing_channel.mention}",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        try:
            channel = await guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                reason=f"Atendimento de {service_type.upper()} aberto por {user}"
            )

            service_info = SERVICOS_CONFIG.get(service_type, SERVICOS_CONFIG["v4"])

            embed_ticket = discord.Embed(
                title=f"Exclusivo • {service_info['titulo']}",
                description=(
                    f"Seu canal de atendimento exclusivo foi aberto! Confira as informações do seu pedido abaixo e aguarde a equipe.\n\n"
                    f"👤 **Cliente:** {user.mention}\n"
                    f"📦 **Pacote Selecionado:** {service_info['label']}\n"
                    f"⚡ **Status:** Aguardando Staff\n\n"
                    "📝 **Instruções ao Cliente:**\n"
                    "Informe os detalhes do seu pedido no chat abaixo e clique no botão **Gerar Pagamento PIX** para pagar."
                ),
                color=service_info["cor"]
            )
            embed_ticket.set_footer(text="VOID Store • Atendimento Seguro e Qualificado")

            await channel.send(content=f"{user.mention}", embed=embed_ticket, view=TicketControlView())
            await interaction.followup.send(f"✅ O seu canal de atendimento foi criado com sucesso: {channel.mention}", ephemeral=True)

        except Exception as e:
            logger.error(f"Erro ao criar canal de atendimento para {user}: {e}")
            await interaction.followup.send("❌ Não foi possível criar o canal. Verifique as permissões do bot.", ephemeral=True)


class TicketControlView(discord.ui.View):
    """View dos botões dentro do canal privado do cliente"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Encerrar Canal",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="ticket:close"
    )
    async def btn_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        embed_closing = discord.Embed(
            title="🔒 Encerramento de Atendimento",
            description="Este canal será **excluído** em **5 segundos**...",
            color=0xEF4444
        )
        embed_closing.set_footer(text="VOID Store • Canal a encerrar")
        await interaction.followup.send(embed=embed_closing)

        await asyncio.sleep(5)

        try:
            await interaction.channel.delete(reason=f"Atendimento encerrado por {interaction.user}")
            logger.info(f"Canal {interaction.channel.name} deletado com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao deletar canal {interaction.channel.name}: {e}")

    @discord.ui.button(
        label="Gerar Pagamento PIX",
        style=discord.ButtonStyle.success,
        emoji="💳",
        custom_id="ticket:gerar_pix"
    )
    async def btn_pix(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog_pix = interaction.client.get_cog("Pix")
        if cog_pix:
            await cog_pix.pix_gerar(interaction)
        else:
            await interaction.response.send_message(
                "❌ O módulo de PIX não está ativo no momento.",
                ephemeral=True
            )


# ====================================
# COG SERVICES / TICKETS
# ====================================

class Services(commands.Cog):
    """Gerenciamento de canais de atendimento e tickets da VOID Store"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        """Registra as Views no bot ao iniciar"""
        self.bot.add_view(TicketControlView())
        for stype, cfg in SERVICOS_CONFIG.items():
            self.bot.add_view(OpenTicketView(service_type=stype, label=cfg["label"], emoji=cfg["emoji"]))

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Intercepta os cliques nos botões de abertura de ticket"""
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")
        if custom_id.startswith("ticket:open:"):
            view = OpenTicketView()
            await view.btn_open_ticket(interaction)

    # ====================================
    # COMANDOS SLASH
    # ====================================

    @app_commands.command(
        name="setup-atendimento",
        description="🛒 Publica o painel de atendimento para o serviço selecionado"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(servico=[
        app_commands.Choice(name="⚡ Desbloqueio V4 & Gears", value="v4"),
        app_commands.Choice(name="📈 Farm de Level", value="level"),
        app_commands.Choice(name="📦 Farm de Materiais", value="materiais"),
        app_commands.Choice(name="💰 Farm de Money (Beli)", value="money"),
        app_commands.Choice(name="🔮 Farm de Fragments", value="fragments"),
        app_commands.Choice(name="🍎 Farm de Frutas", value="frutas")
    ])
    async def setup_atendimento(self, interaction: discord.Interaction, servico: app_commands.Choice[str]):
        config = SERVICOS_CONFIG.get(servico.value, SERVICOS_CONFIG["v4"])

        embed = discord.Embed(
            title=config["titulo"],
            description=config["descricao"],
            color=config["cor"]
        )
        embed.set_footer(text="VOID Store • Atendimento Rápido e Seguro")

        view = OpenTicketView(
            service_type=servico.value,
            label=config["label"],
            emoji=config["emoji"]
        )

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Painel de **{servico.name}** enviado com sucesso!", ephemeral=True)

    @app_commands.command(
        name="fechar",
        description="🔒 Força o fechamento e eliminação do canal de atendimento atual"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def fechar_canal(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔒 **A encerrar e eliminar este canal em 5 segundos...**")
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Canal fechado via /fechar por {interaction.user}")
        except Exception as e:
            logger.error(f"Erro ao fechar canal via comando: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Services(bot))
