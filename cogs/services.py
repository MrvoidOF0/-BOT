"""
🌑 VOID Store Bot - Cog de Atendimento e Gerenciamento de Serviços/Tickets
Painéis dedicados para V4, Farm de Frutas, Leveis, Money e Suporte Geral.
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
        "titulo": "🌑 VOID STORE | RAÇA V4",
        "descricao": (
            "⚔️ **SERVIÇO DE DESPERTAR RAÇA V4**\n\n"
            "Desperte o poder máximo da sua raça com total segurança e rapidez!\n\n"
            "> 🌌 **Engrenagens & Trial V4**\n"
            "> ⚡ **Treino de Habilidade**\n"
            "> 👑 **Full V4 Garantida**\n\n"
            "🛒 *Clique no botão abaixo para abrir seu atendimento e consultar os valores!*"
        ),
        "cor": 0x9333EA,  # Roxo
        "emoji": "⚡",
        "label": "Comprar Raça V4"
    },
    "frutas": {
        "titulo": "🍎 VOID STORE | FARM DE FRUTAS",
        "descricao": (
            "🍓 **FARM & COLETA DE FRUTAS**\n\n"
            "Consiga as frutas mais raras do Blox Fruits sem perder tempo!\n\n"
            "> 📦 **Notificador de Frutas**\n"
            "> 🌊 **Farm no Mar (Sea Events)**\n"
            "> 🎲 **Giro Automático de Frutas**\n\n"
            "🛒 *Clique no botão abaixo para abrir seu atendimento e garantir sua fruta!*"
        ),
        "cor": 0xEF4444,  # Vermelho
        "emoji": "🍎",
        "label": "Comprar Farm de Frutas"
    },
    "level": {
        "titulo": "⭐ VOID STORE | FARM DE NÍVEIS (LEVEL)",
        "descricao": (
            "📈 **UPE SEU PERSONAGEM AO NÍVEL MÁXIMO**\n\n"
            "Deixe o processo chato de farm conosco e receba sua conta no Level Max rápido!\n\n"
            "> 🎯 **Level 1 ao 2550 (Max)**\n"
            "> ⚔️ **Farm por Milhar de Level**\n"
            "> 🛡️ **Segurança Total na sua Conta**\n\n"
            "🛒 *Clique no botão abaixo para abrir seu atendimento e fazer um orçamento!*"
        ),
        "cor": 0x3B82F6,  # Azul
        "emoji": "📈",
        "label": "Comprar Level Max"
    },
    "money": {
        "titulo": "💰 VOID STORE | FARM DE BELI & FRAGMENS",
        "descricao": (
            "💎 **FARM DE BELI E FRAGMENTOS**\n\n"
            "Fique rico no jogo para comprar qualquer estilo de luta ou item!\n\n"
            "> 💵 **Milhões de Beli**\n"
            "> 🔮 **Dezenas de Milhares de Fragmentos**\n"
            "> 🏴‍☠️ **Farm Rápido e Seguro**\n\n"
            "🛒 *Clique no botão abaixo para abrir seu atendimento!*"
        ),
        "cor": 0xEAB308,  # Amarelo / Dourado
        "emoji": "💰",
        "label": "Comprar Beli / Fragmentos"
    },
    "geral": {
        "titulo": "🌑 VOID STORE | CENTRAL DE ATENDIMENTO",
        "descricao": (
            "🛒 **CENTRAL DE DÚVIDAS E SERVIÇOS GERAIS**\n\n"
            "Precisa de algo personalizado, tiras dúvidas ou suporte em compras?\n\n"
            "> 💬 **Atendimento Direto com a Staff**\n"
            "> 🔒 **Canal 100% Privado**\n\n"
            "🛒 *Clique no botão abaixo para iniciar o atendimento!*"
        ),
        "cor": 0x2B2D31,  # Escuro
        "emoji": "🛒",
        "label": "Abrir Atendimento"
    }
}


# ====================================
# VIEWS INTERATIVAS
# ====================================

class OpenTicketView(discord.ui.View):
    """Painel público onde o cliente clica para abrir o atendimento"""

    def __init__(self, service_type: str = "geral", label: str = "Abrir Atendimento", emoji: str = "🛒"):
        super().__init__(timeout=None)
        
        # Cria o botão personalizado de acordo com o serviço
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
        
        # Identifica o tipo de serviço através do custom_id
        custom_id = interaction.data.get("custom_id", "ticket:open:geral")
        service_type = custom_id.split(":")[-1] if len(custom_id.split(":")) > 2 else "geral"

        channel_name = f"🛒-{service_type}-{user.name}".lower().replace(" ", "-")

        # Verifica se o cliente já possui um canal aberto deste tipo
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(
                f"⚠️ Você já possui um canal deste atendimento aberto: {existing_channel.mention}",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Configurações de permissão do canal privado
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

            service_info = SERVICOS_CONFIG.get(service_type, SERVICOS_CONFIG["geral"])

            embed_ticket = discord.Embed(
                title=f"🌑 VOID Store | Atendimento - {service_type.upper()}",
                description=(
                    f"Olá {user.mention}, seja bem-vindo ao seu atendimento de **{service_info['titulo']}**!\n\n"
                    "> 📌 Descreva exatamente os detalhes do serviço que você deseja.\n"
                    "> 💳 Clique no botão abaixo **`Gerar Pagamento PIX`** para pagar.\n"
                    "> 🔒 Para encerrar e deletar este canal, clique em **`Encerrar Canal`**."
                ),
                color=service_info["cor"]
            )
            embed_ticket.set_footer(text="🌑 VOID Store • Atendimento Seguro")

            await channel.send(content=f"{user.mention}", embed=embed_ticket, view=TicketControlView())
            await interaction.followup.send(f"✅ Seu atendimento foi criado com sucesso: {channel.mention}", ephemeral=True)

        except Exception as e:
            logger.error(f"Erro ao criar canal de atendimento para {user}: {e}")
            await interaction.followup.send("❌ Não foi possível criar o canal. Verifique as permissões do bot.", ephemeral=True)


class TicketControlView(discord.ui.View):
    """View contendo os botões dentro do canal privado do cliente"""

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
            description="Este canal será **excluído** permanentemente em **5 segundos**...",
            color=0xEF4444
        )
        embed_closing.set_footer(text="🌑 VOID Store • Canal sendo encerrado")
        await interaction.followup.send(embed=embed_closing)

        await asyncio.sleep(5)

        try:
            await interaction.channel.delete(reason=f"Atendimento encerrado por {interaction.user}")
            logger.info(f"Canal {interaction.channel.name} deletado por {interaction.user}.")
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
        # Registra handlers genéricos para cada tipo de serviço
        for stype, cfg in SERVICOS_CONFIG.items():
            self.bot.add_view(OpenTicketView(service_type=stype, label=cfg["label"], emoji=cfg["emoji"]))

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Intercepta os cliques nos botões de abertura de ticket dinâmicos"""
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
        description="🛒 Publica um painel de atendimento para um serviço específico"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(servico=[
        app_commands.Choice(name="🌌 Raça V4", value="v4"),
        app_commands.Choice(name="🍎 Farm de Frutas", value="frutas"),
        app_commands.Choice(name="📈 Farm de Level", value="level"),
        app_commands.Choice(name="💰 Farm de Beli/Money", value="money"),
        app_commands.Choice(name="🛒 Central Geral / Suporte", value="geral")
    ])
    async def setup_atendimento(self, interaction: discord.Interaction, servico: app_commands.Choice[str]):
        config = SERVICOS_CONFIG.get(servico.value, SERVICOS_CONFIG["geral"])

        embed = discord.Embed(
            title=config["titulo"],
            description=config["descricao"],
            color=config["cor"]
        )
        embed.set_footer(text="🌑 VOID Store • Atendimento Rápido e Garantido")

        view = OpenTicketView(
            service_type=servico.value,
            label=config["label"],
            emoji=config["emoji"]
        )

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Painel de **{servico.name}** enviado com sucesso!", ephemeral=True)

    @app_commands.command(
        name="fechar",
        description="🔒 Força o fechamento e exclusão do canal de atendimento atual"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def fechar_canal(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔒 **Encerrando e excluindo este canal em 5 segundos...**")
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Canal fechado via /fechar por {interaction.user}")
        except Exception as e:
            logger.error(f"Erro ao fechar canal via comando: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Services(bot))
