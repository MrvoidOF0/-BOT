"""
🌑 VOID Store Bot - Sistema de Ajuda Completo
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from utils.embeds import VoidEmbeds
from utils.constants import Emojis, Colors
from utils.logger import logger


# ====================================
# DADOS DOS COMANDOS
# ====================================

HELP_DATA = {
    "tickets": {
        "emoji": Emojis.TICKET,
        "title": "Tickets",
        "description": "Sistema de atendimento via tickets privados.",
        "permission": "Todos / Staff",
        "commands": [
            {
                "name": "ticket-panel",
                "description": "Cria o painel de tickets no canal atual.",
                "permission": "Administrador",
                "usage": "/ticket-panel",
                "example": "/ticket-panel"
            }
        ]
    },
    "pedidos": {
        "emoji": Emojis.ORDER,
        "title": "Pedidos",
        "description": "Sistema completo de gerenciamento de pedidos e vendas.",
        "permission": "Staff",
        "commands": [
            {
                "name": "pedido-criar",
                "description": "Cria um novo pedido para um cliente.",
                "permission": "Staff",
                "usage": "/pedido-criar cliente:@usuario produto:Nome valor:29.90",
                "example": "/pedido-criar cliente:@João produto:Conta Premium valor:29.90 notas:Urgente"
            },
            {
                "name": "pedido-status",
                "description": "Altera o status de um pedido existente.",
                "permission": "Staff",
                "usage": "/pedido-status order_id:VOID-0001 status:concluido",
                "example": "/pedido-status order_id:VOID-0005 status:andamento"
            },
            {
                "name": "pedido-consultar",
                "description": "Exibe todos os detalhes de um pedido.",
                "permission": "Staff",
                "usage": "/pedido-consultar order_id:VOID-0001",
                "example": "/pedido-consultar order_id:VOID-0003"
            }
        ]
    },
    "cargos": {
        "emoji": Emojis.CROWN,
        "title": "Cargos por Compras",
        "description": (
            "Cargos de progressão baseados no valor total gasto. "
            "Atualizados automaticamente ao concluir um pedido."
        ),
        "permission": "Staff / Admin",
        "commands": [
            {
                "name": "cliente adicionar-gasto",
                "description": "Adiciona valor ao histórico de gastos de um cliente.",
                "permission": "Staff",
                "usage": "/cliente adicionar-gasto membro:@usuario valor:50.00",
                "example": "/cliente adicionar-gasto membro:@João valor:100.00 motivo:Compra manual"
            },
            {
                "name": "cliente consultar",
                "description": "Exibe o perfil de compras completo do cliente.",
                "permission": "Staff",
                "usage": "/cliente consultar membro:@usuario",
                "example": "/cliente consultar membro:@João"
            },
            {
                "name": "cliente resetar-gasto",
                "description": "Reseta o total gasto de um cliente para R$ 0,00.",
                "permission": "Administrador",
                "usage": "/cliente resetar-gasto membro:@usuario",
                "example": "/cliente resetar-gasto membro:@João motivo:Estorno"
            },
            {
                "name": "cliente remover-gasto",
                "description": "Remove um valor específico do histórico do cliente.",
                "permission": "Administrador",
                "usage": "/cliente remover-gasto membro:@usuario valor:20.00",
                "example": "/cliente remover-gasto membro:@João valor:50.00 motivo:Estorno parcial"
            }
        ]
    },
    "vip": {
        "emoji": Emojis.VIP,
        "title": "VIP",
        "description": "Sistema de cargo VIP independente da progressão de compras.",
        "permission": "Staff / Todos",
        "commands": [
            {
                "name": "vip conceder",
                "description": "Concede o cargo VIP a um usuário.",
                "permission": "Staff",
                "usage": "/vip conceder membro:@usuario",
                "example": "/vip conceder membro:@João motivo:Adquiriu o plano VIP"
            },
            {
                "name": "vip remover",
                "description": "Remove o cargo VIP de um usuário.",
                "permission": "Staff",
                "usage": "/vip remover membro:@usuario",
                "example": "/vip remover membro:@João motivo:Plano expirado"
            },
            {
                "name": "vip info",
                "description": "Exibe os benefícios do plano VIP.",
                "permission": "Todos",
                "usage": "/vip info",
                "example": "/vip info"
            },
            {
                "name": "vip listar",
                "description": "Lista todos os membros com cargo VIP.",
                "permission": "Staff",
                "usage": "/vip listar",
                "example": "/vip listar"
            }
        ]
    },
    "booster": {
        "emoji": Emojis.BOOSTER,
        "title": "Booster",
        "description": "Benefícios automáticos para quem dá boost no servidor.",
        "permission": "Automático / Staff",
        "commands": [
            {
                "name": "booster info",
                "description": "Exibe os benefícios do cargo Booster.",
                "permission": "Todos",
                "usage": "/booster info",
                "example": "/booster info"
            },
            {
                "name": "booster listar",
                "description": "Lista todos os boosters ativos no servidor.",
                "permission": "Staff",
                "usage": "/booster listar",
                "example": "/booster listar"
            }
        ]
    },
    "tarefas": {
        "emoji": Emojis.TASK,
        "title": "Tarefas",
        "description": "Sistema interno de gestão de tarefas da equipe.",
        "permission": "Staff",
        "commands": [
            {
                "name": "tarefa criar",
                "description": "Cria uma nova tarefa interna para a equipe.",
                "permission": "Staff",
                "usage": "/tarefa criar nome:Título prioridade:alta",
                "example": "/tarefa criar nome:Entregar pedidos prioridade:alta responsavel:@Ana prazo:25/12/2025"
            },
            {
                "name": "tarefa listar",
                "description": "Lista todas as tarefas, com filtro opcional por status.",
                "permission": "Staff",
                "usage": "/tarefa listar",
                "example": "/tarefa listar status:pendente"
            },
            {
                "name": "tarefa concluir",
                "description": "Marca uma tarefa como concluída.",
                "permission": "Staff",
                "usage": "/tarefa concluir tarefa_id:1",
                "example": "/tarefa concluir tarefa_id:5"
            },
            {
                "name": "tarefa cancelar",
                "description": "Cancela uma tarefa existente.",
                "permission": "Staff",
                "usage": "/tarefa cancelar tarefa_id:1",
                "example": "/tarefa cancelar tarefa_id:3"
            }
        ]
    },
    "estoque": {
        "emoji": Emojis.INVENTORY,
        "title": "Estoque",
        "description": "Gerenciamento de produtos e quantidades disponíveis.",
        "permission": "Staff / Todos",
        "commands": [
            {
                "name": "estoque adicionar",
                "description": "Cadastra ou incrementa um produto no estoque.",
                "permission": "Staff",
                "usage": "/estoque adicionar nome:Produto categoria:Contas quantidade:10 preco:29.90",
                "example": "/estoque adicionar nome:Conta Roblox categoria:Contas quantidade:5 preco:15.00"
            },
            {
                "name": "estoque remover",
                "description": "Abate unidades do estoque de um produto.",
                "permission": "Staff",
                "usage": "/estoque remover nome:Produto quantidade:2",
                "example": "/estoque remover nome:Conta Roblox quantidade:1"
            },
            {
                "name": "estoque consultar",
                "description": "Consulta as informações de um produto específico.",
                "permission": "Todos",
                "usage": "/estoque consultar nome:Produto",
                "example": "/estoque consultar nome:Conta Roblox"
            },
            {
                "name": "estoque listar",
                "description": "Exibe o catálogo completo de produtos disponíveis.",
                "permission": "Todos",
                "usage": "/estoque listar",
                "example": "/estoque listar"
            }
        ]
    },
    "moderacao": {
        "emoji": "🛡️",
        "title": "Moderação",
        "description": "Ferramentas de moderação e controle do servidor.",
        "permission": "Moderador / Admin",
        "commands": [
            {
                "name": "ban",
                "description": "Bane permanentemente um usuário do servidor.",
                "permission": "Ban Members",
                "usage": "/ban membro:@usuario",
                "example": "/ban membro:@usuario motivo:Violação das regras deletar_mensagens:1"
            },
            {
                "name": "kick",
                "description": "Expulsa um usuário do servidor.",
                "permission": "Kick Members",
                "usage": "/kick membro:@usuario",
                "example": "/kick membro:@usuario motivo:Comportamento inadequado"
            },
            {
                "name": "timeout",
                "description": "Silencia um usuário por um período (em minutos).",
                "permission": "Moderate Members",
                "usage": "/timeout membro:@usuario duracao:60",
                "example": "/timeout membro:@usuario duracao:1440 motivo:Flood"
            },
            {
                "name": "untimeout",
                "description": "Remove o timeout de um usuário antecipadamente.",
                "permission": "Moderate Members",
                "usage": "/untimeout membro:@usuario",
                "example": "/untimeout membro:@usuario motivo:Revisão"
            },
            {
                "name": "warn",
                "description": "Emite um aviso formal para um usuário.",
                "permission": "Staff",
                "usage": "/warn membro:@usuario motivo:Texto",
                "example": "/warn membro:@usuario motivo:Spam no chat"
            },
            {
                "name": "clear",
                "description": "Deleta mensagens em massa no canal atual.",
                "permission": "Manage Messages",
                "usage": "/clear quantidade:10",
                "example": "/clear quantidade:50 membro:@usuario"
            }
        ]
    },
    "sheets": {
        "emoji": "📊",
        "title": "Google Sheets",
        "description": "Integração e sincronização com planilha Google.",
        "permission": "Staff",
        "commands": [
            {
                "name": "sheets-status",
                "description": "Verifica se a integração com Google Sheets está ativa.",
                "permission": "Staff",
                "usage": "/sheets-status",
                "example": "/sheets-status"
            }
        ]
    },
    "configuracao": {
        "emoji": Emojis.SETTINGS,
        "title": "Configuração",
        "description": "Configuração geral do bot e do servidor.",
        "permission": "Administrador",
        "commands": [
            {
                "name": "setup",
                "description": "Abre o painel de configuração interativo do bot.",
                "permission": "Administrador",
                "usage": "/setup",
                "example": "/setup"
            },
            {
                "name": "ticket-panel",
                "description": "Publica o painel de atendimento no canal atual.",
                "permission": "Administrador",
                "usage": "/ticket-panel",
                "example": "/ticket-panel"
            }
        ]
    }
}


# ====================================
# SELECT MENU DE CATEGORIAS
# ====================================

class HelpSelectMenu(discord.ui.Select):
    """Menu de seleção de categoria de ajuda"""

    def __init__(self):
        options = []
        for key, data in HELP_DATA.items():
            options.append(
                discord.SelectOption(
                    label=data["title"],
                    value=key,
                    emoji=data["emoji"],
                    description=data["description"][:90]
                )
            )

        super().__init__(
            placeholder="Selecione uma categoria...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        category_key = self.values[0]
        data = HELP_DATA[category_key]

        embed = discord.Embed(
            title=f"{data['emoji']} Ajuda — {data['title']}",
            description=data["description"],
            color=0x000000
        )

        embed.add_field(
            name="Permissão Geral",
            value=data["permission"],
            inline=False
        )

        for cmd in data["commands"]:
            embed.add_field(
                name=f"/{cmd['name']}",
                value=(
                    f"**Função:** {cmd['description']}\n"
                    f"**Permissão:** `{cmd['permission']}`\n"
                    f"**Uso:** `{cmd['usage']}`\n"
                    f"**Exemplo:** `{cmd['example']}`"
                ),
                inline=False
            )

        embed.set_footer(text="🌑 VOID Store | Use o menu abaixo para navegar")

        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    """View do sistema de ajuda"""

    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(HelpSelectMenu())


# ====================================
# COG
# ====================================

class Help(commands.Cog):
    """Sistema de ajuda interativo e completo"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="❓ Exibe a ajuda completa do VOID Store Bot"
    )
    @app_commands.describe(
        categoria="Exibe ajuda diretamente de uma categoria específica"
    )
    @app_commands.choices(categoria=[
        app_commands.Choice(name="🎫 Tickets", value="tickets"),
        app_commands.Choice(name="📦 Pedidos", value="pedidos"),
        app_commands.Choice(name="👑 Cargos", value="cargos"),
        app_commands.Choice(name="💎 VIP", value="vip"),
        app_commands.Choice(name="🚀 Booster", value="booster"),
        app_commands.Choice(name="📋 Tarefas", value="tarefas"),
        app_commands.Choice(name="📦 Estoque", value="estoque"),
        app_commands.Choice(name="🛡️ Moderação", value="moderacao"),
        app_commands.Choice(name="📊 Google Sheets", value="sheets"),
        app_commands.Choice(name="⚙️ Configuração", value="configuracao"),
    ])
    async def help(
        self,
        interaction: discord.Interaction,
        categoria: Optional[str] = None
    ):
        """Exibe o menu de ajuda completo ou de uma categoria"""

        if categoria and categoria in HELP_DATA:
            # Ajuda direta de categoria específica
            data = HELP_DATA[categoria]
            embed = discord.Embed(
                title=f"{data['emoji']} Ajuda — {data['title']}",
                description=data["description"],
                color=0x000000
            )
            embed.add_field(
                name="Permissão Geral",
                value=data["permission"],
                inline=False
            )
            for cmd in data["commands"]:
                embed.add_field(
                    name=f"/{cmd['name']}",
                    value=(
                        f"**Função:** {cmd['description']}\n"
                        f"**Permissão:** `{cmd['permission']}`\n"
                        f"**Uso:** `{cmd['usage']}`\n"
                        f"**Exemplo:** `{cmd['example']}`"
                    ),
                    inline=False
                )
            embed.set_footer(text="🌑 VOID Store | /help para o menu principal")
            view = HelpView()
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return

        # Menu principal
        embed = discord.Embed(
            title=f"{Emojis.VOID} 𝐕𝐎𝐈𝐃 𝐒𝐭𝐨𝐫𝐞 | BOT — Ajuda",
            description=(
                "Bem-vindo ao sistema de ajuda da **VOID Store**.\n\n"
                "Use o menu abaixo para explorar os comandos por categoria.\n\n"
                f"{Emojis.TICKET} **Tickets** — Sistema de atendimento\n"
                f"{Emojis.ORDER} **Pedidos** — Gerenciamento de vendas\n"
                f"{Emojis.CROWN} **Cargos** — Progressão de clientes\n"
                f"{Emojis.VIP} **VIP** — Plano exclusivo\n"
                f"{Emojis.BOOSTER} **Booster** — Benefícios de boost\n"
                f"{Emojis.TASK} **Tarefas** — Gestão interna\n"
                f"{Emojis.INVENTORY} **Estoque** — Produtos e serviços\n"
                f"🛡️ **Moderação** — Ferramentas de controle\n"
                f"📊 **Google Sheets** — Integração de dados\n"
                f"{Emojis.SETTINGS} **Configuração** — Setup do bot"
            ),
            color=0x000000
        )
        embed.set_footer(text="🌑 VOID Store | Selecione uma categoria abaixo")

        view = HelpView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        logger.info(f"/help used by {interaction.user}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
