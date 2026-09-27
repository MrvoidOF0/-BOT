"""
🌑 VOID Store Bot - Cog de Painel de Game Passes
Painel de seleção dinâmica via Select Menu (Discord.py UI)
"""

import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import setup_logger

logger = setup_logger("Gamepass")

# ====================================
# BASE DE DADOS DAS GAME PASSES
# ====================================

GAMEPASSES_DATA = {
    "2x_money": {
        "nome": "2x Money",
        "emoji": "💰",
        "robux": 450,
        "preco": "R$ 21,60",
        "descricao": "Dobra todo o dinheiro (Beli) obtido durante a sua jogatina."
    },
    "2x_mastery": {
        "nome": "2x Mastery",
        "emoji": "⚡",
        "robux": 450,
        "preco": "R$ 21,60",
        "descricao": "Dobra a quantidade de experiência de Mastery (Maestria) obtida com armas e frutas."
    },
    "2x_boss_drops": {
        "nome": "2x Boss Drops",
        "emoji": "👑",
        "robux": 350,
        "preco": "R$ 16,80",
        "descricao": "Aumenta significativamente a chance de obter itens e recompensas raras de bosses."
    },
    "fast_boats": {
        "nome": "Fast Boats",
        "emoji": "🚤",
        "robux": 350,
        "preco": "R$ 16,80",
        "descricao": "Libera barcos especiais, ultra velozes e exclusivos no jogo."
    },
    "dark_blade": {
        "nome": "Dark Blade",
        "emoji": "🗡️",
        "robux": 1200,
        "preco": "R$ 57,60",
        "descricao": "Desbloqueia a lendária espada Dark Blade diretamente no seu inventário."
    },
    "fruit_notifier": {
        "nome": "Fruit Notifier",
        "emoji": "🍎",
        "robux": 2700,
        "preco": "R$ 129,60",
        "descricao": "Notifica quando uma fruta nasce no servidor e indica a distância exata em metros até ela."
    },
    "fruit_storage": {
        "nome": "+1 Fruit Storage",
        "emoji": "🍏",
        "robux": 400,
        "preco": "R$ 19,20",
        "descricao": "Aumenta a capacidade do seu inventário permitindo armazenar uma cópia adicional de cada fruta."
    }
}


# ====================================
# COMPONENTES DE INTERFACE (UI)
# ====================================

class GamepassSelect(discord.ui.Select):
    """Menu Selecionável de Game Passes"""

    def __init__(self):
        options = [
            discord.SelectOption(
                label="2x Money",
                value="2x_money",
                description="Robux: 450 | R$ 21,60",
                emoji="💰"
            ),
            discord.SelectOption(
                label="2x Mastery",
                value="2x_mastery",
                description="Robux: 450 | R$ 21,60",
                emoji="⚡"
            ),
            discord.SelectOption(
                label="2x Boss Drops",
                value="2x_boss_drops",
                description="Robux: 350 | R$ 16,80",
                emoji="👑"
            ),
            discord.SelectOption(
                label="Fast Boats",
                value="fast_boats",
                description="Robux: 350 | R$ 16,80",
                emoji="🚤"
            ),
            discord.SelectOption(
                label="Dark Blade",
                value="dark_blade",
                description="Robux: 1.200 | R$ 57,60",
                emoji="🗡️"
            ),
            discord.SelectOption(
                label="Fruit Notifier",
                value="fruit_notifier",
                description="Robux: 2.700 | R$ 129,60",
                emoji="🍎"
            ),
            discord.SelectOption(
                label="+1 Fruit Storage",
                value="fruit_storage",
                description="Robux: 400 | R$ 19,20",
                emoji="🍏"
            )
        ]

        super().__init__(
            placeholder="🛒 Selecione uma Game Pass",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="gamepass:select_menu"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_key = self.values[0]
        gp_info = GAMEPASSES_DATA.get(selected_key)

        if not gp_info:
            await interaction.response.send_message("❌ Game Pass não encontrada.", ephemeral=True)
            return

        # Embed detalhado da Game Pass selecionada (Visual Dark VOID)
        embed_detalhe = discord.Embed(
            title=f"{gp_info['emoji']} {gp_info['nome']} | VOID Store",
            description=(
                f"**Descrição:**\n> {gp_info['descricao']}\n\n"
                f"📊 **Comparativo de Valores:**\n"
                f"> 🎮 **Preço no Roblox:** `{gp_info['robux']} Robux`\n"
                f"> 💳 **Preço VOID Store:** **{gp_info['preco']}**\n\n"
                f"📌 **Como realizar a compra?**\n"
                f"Para adquirir esta Game Pass, **abra um ticket de atendimento** em nosso servidor e informe o item desejado aos nossos atendentes!"
            ),
            color=0x2B2D31  # Preto/Cinza escuro da identidade VOID
        )

        embed_detalhe.set_footer(
            text="VOID Store • Pagamento Seguro | Entrega Rápida | Suporte Garantido",
            icon_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None
        )

        # Atualiza a mensagem mantendo o mesmo Select Menu interativo
        await interaction.response.edit_message(embed=embed_detalhe, view=self.view)


class GamepassView(discord.ui.View):
    """View persistente do painel de Game Passes"""

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GamepassSelect())


# ====================================
# COG / COMANDO SLASH
# ====================================

class Gamepass(commands.Cog):
    """Gerenciamento do painel de Game Passes da VOID Store"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        """Registra a View persistente ao carregar a Cog"""
        self.bot.add_view(GamepassView())

    @app_commands.command(
        name="gamepass",
        description="🎮 Publica o painel profissional de compra de Game Passes"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def gamepass_cmd(self, interaction: discord.Interaction):
        """Envia o painel de seleção de Game Passes no canal"""

        embed_main = discord.Embed(
            title="🎮 GAME PASSES | VOID STORE",
            description=(
                "Escolha abaixo a Game Pass que deseja comprar.\n"
                "Tenha acesso a vantagens exclusivas no Blox Fruits através da **VOID Store**.\n\n"
                "💳 **Pagamento seguro**\n"
                "⚡ **Entrega rápida**\n"
                "🎟️ **Suporte por ticket**"
            ),
            color=0x2B2D31  # Estilo limpo em tom cinza/preto escuro do Discord
        )

        embed_main.set_footer(
            text="VOID Store • Selecione uma opção no menu abaixo",
            icon_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None
        )

        view = GamepassView()

        # Responde ao administrador confirmando o envio e publica o painel público no canal
        await interaction.channel.send(embed=embed_main, view=view)
        await interaction.response.send_message("✅ Painel de Game Passes publicado com sucesso!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Gamepass(bot))
