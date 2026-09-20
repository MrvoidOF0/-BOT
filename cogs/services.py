"""
🌑 VOID Store Bot - Sistema de Serviços Reescrito
Sem valores nos botões. Modal de nick antes de abrir canal.
Canal mostra nick + serviço. Staff conversa e gera PIX depois.
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
# DADOS DOS SERVIÇOS
# ====================================

SERVICOS = {
    "frutas": {
        "nome": "🍎 Farm de Frutas",
        "descricao": "Farm de frutas durante o tempo escolhido.",
        "cor": 0x9b59b6,
        "instrucao_canal": (
            "Olá! Informe qual **fruta** você deseja fazer o farm\n"
            "e por **quantas horas**.\n\n"
            "**Tabela de preços:**\n"
            "• 1 hora — R$ 3,00\n"
            "• 2 horas — R$ 5,00\n"
            "• 3 horas — R$ 7,00\n"
            "• 5 horas — R$ 10,00\n"
            "• 10 horas — R$ 18,00"
        ),
        "opcoes": [
            {"label": "1 hora",   "preco": 3.00},
            {"label": "2 horas",  "preco": 5.00},
            {"label": "3 horas",  "preco": 7.00},
            {"label": "5 horas",  "preco": 10.00},
            {"label": "10 horas", "preco": 18.00},
        ]
    },
    "level": {
        "nome": "⭐ Farm de Level",
        "descricao": "Level up rápido e seguro no seu personagem.",
        "cor": 0x3498db,
        "instrucao_canal": (
            "Olá! Informe seu **nível atual** e qual **pacote** deseja.\n\n"
            "**Tabela de preços:**\n"
            "• +100 níveis — R$ 2,00\n"
            "• +300 níveis — R$ 5,00\n"
            "• +500 níveis — R$ 8,00\n"
            "• +1.000 níveis — R$ 14,00\n"
            "• Level Máximo — R$ 22,00"
        ),
        "opcoes": [
            {"label": "+100 níveis",   "preco": 2.00},
            {"label": "+300 níveis",   "preco": 5.00},
            {"label": "+500 níveis",   "preco": 8.00},
            {"label": "+1.000 níveis", "preco": 14.00},
            {"label": "Level Máximo",  "preco": 22.00},
        ]
    },
    "materiais": {
        "nome": "🧪 Farm de Materiais",
        "descricao": "Farm de materiais de todos os tipos.",
        "cor": 0x27ae60,
        "instrucao_canal": (
            "Olá! Informe qual **tipo de material** e qual **quantidade** deseja.\n\n"
            "**Tabela de preços (100 unidades):**\n"
            "• Comuns 100x — R$ 2,00\n"
            "• Incomuns 100x — R$ 3,00\n"
            "• Raros 100x — R$ 5,00\n"
            "• Especiais 100x — R$ 7,00"
        ),
        "opcoes": [
            {"label": "Comuns 100x",    "preco": 2.00},
            {"label": "Incomuns 100x",  "preco": 3.00},
            {"label": "Raros 100x",     "preco": 5.00},
            {"label": "Especiais 100x", "preco": 7.00},
        ]
    },
    "v4": {
        "nome": "⚙️ V4 / Gear",
        "descricao": "Desbloqueie as engrenagens V4 do seu personagem.",
        "cor": 0xe74c3c,
        "instrucao_canal": (
            "Olá! Informe qual **Gear** deseja desbloquear.\n\n"
            "**Tabela de preços:**\n"
            "• Gear 1 — R$ 8,00\n"
            "• Gear 2 — R$ 8,00\n"
            "• Gear 3 — R$ 10,00\n"
            "• Gear 4 — R$ 12,00\n"
            "• V4 Completa (todas) — R$ 30,00"
        ),
        "opcoes": [
            {"label": "Gear 1",        "preco": 8.00},
            {"label": "Gear 2",        "preco": 8.00},
            {"label": "Gear 3",        "preco": 10.00},
            {"label": "Gear 4",        "preco": 12.00},
            {"label": "V4 Completa",   "preco": 30.00},
        ]
    },
    "money": {
        "nome": "💵 Farm de Money",
        "descricao": "Farm de Beli (dinheiro) no Blox Fruits.",
        "cor": 0xf39c12,
        "instrucao_canal": (
            "Olá! Informe qual **quantidade de Beli** deseja.\n\n"
            "**Tabela de preços:**\n"
            "• 5M Beli — R$ 4,00\n"
            "• 10M Beli — R$ 7,00\n"
            "• 25M Beli — R$ 15,00\n"
            "• 50M Beli — R$ 27,00"
        ),
        "opcoes": [
            {"label": "5M Beli",  "preco": 4.00},
            {"label": "10M Beli", "preco": 7.00},
            {"label": "25M Beli", "preco": 15.00},
            {"label": "50M Beli", "preco": 27.00},
        ]
    },
    "fragmentos": {
        "nome": "💎 Farm de Fragments",
        "descricao": "Farm de fragmentos para raças e upgrades.",
        "cor": 0x1abc9c,
        "instrucao_canal": (
            "Olá! Informe qual **quantidade de Fragments** deseja.\n\n"
            "**Tabela de preços:**\n"
            "• 5.000 Fragments — R$ 3,00\n"
            "• 10.000 Fragments — R$ 6,00\n"
            "• 25.000 Fragments — R$ 13,00\n"
            "• 50.000 Fragments — R$ 24,00"
        ),
        "opcoes": [
            {"label": "5.000 Fragments",  "preco": 3.00},
            {"label": "10.000 Fragments", "preco": 6.00},
            {"label": "25.000 Fragments", "preco": 13.00},
            {"label": "50.000 Fragments", "preco": 24.00},
        ]
    },
}


# ====================================
# MODAL DE NICK (antes de abrir canal)
# ====================================

class NickModal(discord.ui.Modal):
    """
    Aparece quando o cliente clica num serviço.
    Pede apenas o nick da conta (opcional).
    Depois abre o canal de atendimento.
    """

    nick = discord.ui.TextInput(
        label="Nick da sua conta no jogo (opcional)",
        placeholder="Ex: VoidPlayer123 — deixe vazio se preferir informar depois",
        required=False,
        max_length=100
    )

    def __init__(self, service_id: str, service_nome: str, opcao_label: str, opcao_preco: float):
        super().__init__(title=f"Pedido: {service_nome}")
        self.service_id = service_id
        self.service_nome = service_nome
        self.opcao_label = opcao_label
        self.opcao_preco = opcao_preco

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        cog = interaction.client.get_cog("Services")
        if cog:
            await cog.criar_canal_servico(
                interaction=interaction,
                service_id=self.service_id,
                service_nome=self.service_nome,
                opcao_label=self.opcao_label,
                opcao_preco=self.opcao_preco,
                nick=self.nick.value.strip() if self.nick.value else "Não informado"
            )


# ====================================
# FACTORY DE VIEWS POR SERVIÇO
# ====================================

def criar_view(service_id: str, service_nome: str, opcoes: list) -> discord.ui.View:
    """
    Cria a view de botões de um serviço.
    Os botões mostram APENAS o nome da opção (sem valor).
    Ao clicar abre o NickModal.
    """

    view = discord.ui.View(timeout=None)

    for opcao in opcoes:
        btn = discord.ui.Button(
            label=opcao["label"],          # apenas o nome, sem preço
            style=discord.ButtonStyle.blurple,
            custom_id=f"svc_{service_id}_{opcao['label'].replace(' ', '_').lower()}"
        )

        def make_cb(sid, snome, olabel, opreco):
            async def callback(interaction: discord.Interaction):
                modal = NickModal(
                    service_id=sid,
                    service_nome=snome,
                    opcao_label=olabel,
                    opcao_preco=opreco
                )
                await interaction.response.send_modal(modal)
            return callback

        btn.callback = make_cb(
            service_id,
            service_nome,
            opcao["label"],
            opcao["preco"]
        )
        view.add_item(btn)

    return view


# ====================================
# VIEW DE CONTROLE DO CANAL
# ====================================

class ServiceControlView(discord.ui.View):
    """Botões dentro do canal de serviço"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Canal",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="svc_ctrl:close"
    )
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Services")
        if cog:
            await cog.fechar_canal(interaction)

    @discord.ui.button(
        label="Gerar PIX",
        style=discord.ButtonStyle.green,
        emoji="💳",
        custom_id="svc_ctrl:pix"
    )
    async def pix(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not PermissionChecker.is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas staff pode gerar PIX.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "💳 Use `/pix-gerar valor:XX.XX cliente:@usuario` para enviar a cobrança PIX.",
            ephemeral=True
        )


# ====================================
# COG
# ====================================

class Services(commands.Cog):
    """Sistema de serviços com preços e modal de nick"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

        # Registrar views persistentes de cada serviço
        for service_id, data in SERVICOS.items():
            view = criar_view(service_id, data["nome"], data["opcoes"])
            self.bot.add_view(view)

        # Registrar view de controle
        self.bot.add_view(ServiceControlView())

    # ====================================
    # CRIAR CANAL DE SERVIÇO
    # ====================================

    async def criar_canal_servico(
        self,
        interaction: discord.Interaction,
        service_id: str,
        service_nome: str,
        opcao_label: str,
        opcao_preco: float,
        nick: str
    ):
        """
        Cria o canal privado de atendimento.
        Chamado após o cliente preencher o NickModal.
        """

        guild = interaction.guild
        user = interaction.user
        data = SERVICOS.get(service_id, {})

        # Verificar categoria
        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            await interaction.followup.send(
                "❌ Categoria de tickets não configurada. Avise um administrador.",
                ephemeral=True
            )
            return

        category = guild.get_channel(category_id)
        if not category:
            await interaction.followup.send(
                "❌ Categoria não encontrada.", ephemeral=True
            )
            return

        # Nome do canal
        channel_name = f"{service_id}-{user.name}".lower()[:50]

        # Verificar duplicado
        for ch in category.text_channels:
            if ch.name == channel_name:
                await interaction.followup.send(
                    f"⚠️ Você já tem um canal deste serviço aberto: {ch.mention}\n"
                    f"Finalize ou feche antes de abrir um novo.",
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
                topic=f"{service_nome} | {opcao_label} | {user}"
            )

            # ── Embed de abertura do canal ──
            embed = discord.Embed(
                title=f"{data.get('nome', service_nome)}",
                color=data.get("cor", 0x000000),
                timestamp=discord.utils.utcnow()
            )

            embed.add_field(
                name="👤 Cliente",
                value=f"{user.mention}",
                inline=True
            )

            embed.add_field(
                name="🎮 Nick no Jogo",
                value=f"`{nick}`",
                inline=True
            )

            embed.add_field(
                name="📦 Serviço Solicitado",
                value=f"**{service_nome}**\n`{opcao_label}`",
                inline=True
            )

            # Instrução específica do serviço
            embed.add_field(
                name="💬 O que fazer agora",
                value=data.get("instrucao_canal", "Aguarde a equipe para mais informações."),
                inline=False
            )

            embed.set_footer(text="🌑 VOID Store | Atendimento rápido e seguro")
            embed.set_thumbnail(url=user.display_avatar.url)

            # Mencionar staff
            staff_mention = f"<@&{config.STAFF_ROLE_ID}>" if config.STAFF_ROLE_ID else ""

            await channel.send(
                content=f"{user.mention} {staff_mention}",
                embed=embed,
                view=ServiceControlView()
            )

            # Confirmar para o cliente (sem fechar nada)
            await interaction.followup.send(
                f"✅ Canal criado: {channel.mention}\n"
                f"Nossa equipe responderá em breve!",
                ephemeral=True
            )

            # Log
            await self.db.create_log(
                "service",
                user.id,
                "channel_created",
                f"Service: {service_id} | Option: {opcao_label} | Price: {opcao_preco}"
            )

            logger.info(
                f"Service channel: {channel.name} | "
                f"User: {user} | Service: {service_id} | Option: {opcao_label}"
            )

        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Sem permissão para criar canais.", ephemeral=True
            )
        except Exception as e:
            logger.error(f"Erro ao criar canal de serviço: {e}")
            await interaction.followup.send(
                "❌ Erro ao criar canal. Tente novamente.", ephemeral=True
            )

    # ====================================
    # FECHAR CANAL
    # ====================================

    async def fechar_canal(self, interaction: discord.Interaction):
        """Fecha e deleta o canal de serviço com confirmação"""

        is_staff = PermissionChecker.is_staff(interaction.user)
        channel_topic = interaction.channel.topic or ""
        is_creator = str(interaction.user) in channel_topic

        if not (is_staff or is_creator):
            await interaction.response.send_message(
                "❌ Você não pode fechar este canal.", ephemeral=True
            )
            return

        # Botões de confirmação inline
        confirmado = False
        view = discord.ui.View()

        confirm_btn = discord.ui.Button(
            label="Sim, fechar",
            style=discord.ButtonStyle.red,
            emoji="✅"
        )
        cancel_btn = discord.ui.Button(
            label="Cancelar",
            style=discord.ButtonStyle.gray,
            emoji="❌"
        )

        async def confirm_cb(i: discord.Interaction):
            nonlocal confirmado
            confirmado = True
            view.stop()
            await i.response.defer()

        async def cancel_cb(i: discord.Interaction):
            view.stop()
            await i.response.defer()

        confirm_btn.callback = confirm_cb
        cancel_btn.callback = cancel_cb
        view.add_item(confirm_btn)
        view.add_item(cancel_btn)

        await interaction.response.send_message(
            "⚠️ **Fechar este canal?**",
            view=view,
            ephemeral=True
        )

        await view.wait()

        if confirmado:
            try:
                await interaction.edit_original_response(
                    content="✅ Fechando canal...", view=None
                )

                embed = discord.Embed(
                    description=(
                        f"🔒 Canal fechado por {interaction.user.mention}.\n"
                        f"Deletando em **5 segundos**..."
                    ),
                    color=0xff0000
                )
                await interaction.channel.send(embed=embed)

                await self.db.create_log(
                    "service",
                    interaction.user.id,
                    "channel_closed",
                    f"Channel: {interaction.channel.id}"
                )

                await asyncio.sleep(5)
                await interaction.channel.delete(
                    reason=f"Canal fechado por {interaction.user}"
                )

            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Erro ao fechar canal: {e}")
        else:
            await interaction.edit_original_response(
                content="❌ Fechamento cancelado.", view=None
            )

    # ====================================
    # COMANDOS DE PAINEL (um por serviço)
    # ====================================

    async def _criar_painel(self, interaction: discord.Interaction, service_id: str):
        """Lógica compartilhada para criar qualquer painel de serviço"""

        data = SERVICOS[service_id]

        # Linha de preços para o embed
        precos_txt = "\n".join(
            f"• **{op['label']}** — `R$ {op['preco']:.2f}`"
            for op in data["opcoes"]
        )

        embed = discord.Embed(
            title=data["nome"],
            description=(
                f"{data['descricao']}\n\n"
                f"**Clique no botão da opção desejada.**\n"
                f"Você preencherá um breve formulário e um canal\n"
                f"privado será aberto para seu atendimento."
            ),
            color=data["cor"],
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="💰 Preços",
            value=precos_txt,
            inline=False
        )

        embed.add_field(
            name="📋 Como funciona",
            value=(
                "1. Clique na opção desejada\n"
                "2. Informe seu nick (opcional)\n"
                "3. Um canal privado será aberto\n"
                "4. Converse com a equipe e realize o pagamento"
            ),
            inline=False
        )

        embed.set_footer(text="🌑 VOID Store | Serviço rápido e seguro")

        view = criar_view(service_id, data["nome"], data["opcoes"])

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"✅ Painel **{data['nome']}** criado!", ephemeral=True
        )

    @app_commands.command(name="painel-frutas", description="🍎 Cria o painel de Farm de Frutas")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_frutas(self, interaction: discord.Interaction):
        await self._criar_painel(interaction, "frutas")

    @app_commands.command(name="painel-level", description="⭐ Cria o painel de Farm de Level")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_level(self, interaction: discord.Interaction):
        await self._criar_painel(interaction, "level")

    @app_commands.command(name="painel-materiais", description="🧪 Cria o painel de Farm de Materiais")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_materiais(self, interaction: discord.Interaction):
        await self._criar_painel(interaction, "materiais")

    @app_commands.command(name="painel-v4", description="⚙️ Cria o painel de V4 / Gear")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_v4(self, interaction: discord.Interaction):
        await self._criar_painel(interaction, "v4")

    @app_commands.command(name="painel-money", description="💵 Cria o painel de Farm de Money")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_money(self, interaction: discord.Interaction):
        await self._criar_painel(interaction, "money")

    @app_commands.command(name="painel-fragmentos", description="💎 Cria o painel de Farm de Fragments")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_fragmentos(self, interaction: discord.Interaction):
        await self._criar_painel(interaction, "fragmentos")


async def setup(bot: commands.Bot):
    await bot.add_cog(Services(bot))
