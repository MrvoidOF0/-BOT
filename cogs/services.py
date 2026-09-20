"""
🌑 VOID Store Bot - Serviços (Reescrito)
Abordagem: sem Views persistentes complexas.
Tudo via on_interaction para máxima compatibilidade.
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
        "cor": 0x9b59b6,
        "instrucao": (
            "**Informe qual fruta e por quantas horas:**\n\n"
            "• 1 hora — R$ 3,00\n"
            "• 2 horas — R$ 5,00\n"
            "• 3 horas — R$ 7,00\n"
            "• 5 horas — R$ 10,00\n"
            "• 10 horas — R$ 18,00"
        ),
        "opcoes": ["1 hora", "2 horas", "3 horas", "5 horas", "10 horas"],
        "precos": [3.00, 5.00, 7.00, 10.00, 18.00],
    },
    "level": {
        "nome": "⭐ Farm de Level",
        "cor": 0x3498db,
        "instrucao": (
            "**Informe seu nível atual e qual pacote deseja:**\n\n"
            "• +100 níveis — R$ 2,00\n"
            "• +300 níveis — R$ 5,00\n"
            "• +500 níveis — R$ 8,00\n"
            "• +1.000 níveis — R$ 14,00\n"
            "• Level Máximo — R$ 22,00"
        ),
        "opcoes": ["+100 níveis", "+300 níveis", "+500 níveis", "+1.000 níveis", "Level Máximo"],
        "precos": [2.00, 5.00, 8.00, 14.00, 22.00],
    },
    "materiais": {
        "nome": "🧪 Farm de Materiais",
        "cor": 0x27ae60,
        "instrucao": (
            "**Informe qual tipo de material deseja (100 unidades):**\n\n"
            "• Comuns 100x — R$ 2,00\n"
            "• Incomuns 100x — R$ 3,00\n"
            "• Raros 100x — R$ 5,00\n"
            "• Especiais 100x — R$ 7,00"
        ),
        "opcoes": ["Comuns 100x", "Incomuns 100x", "Raros 100x", "Especiais 100x"],
        "precos": [2.00, 3.00, 5.00, 7.00],
    },
    "v4": {
        "nome": "⚙️ V4 / Gear",
        "cor": 0xe74c3c,
        "instrucao": (
            "**Informe qual Gear deseja desbloquear:**\n\n"
            "• Gear 1 — R$ 8,00\n"
            "• Gear 2 — R$ 8,00\n"
            "• Gear 3 — R$ 10,00\n"
            "• Gear 4 — R$ 12,00\n"
            "• V4 Completa — R$ 30,00"
        ),
        "opcoes": ["Gear 1", "Gear 2", "Gear 3", "Gear 4", "V4 Completa"],
        "precos": [8.00, 8.00, 10.00, 12.00, 30.00],
    },
    "money": {
        "nome": "💵 Farm de Money",
        "cor": 0xf39c12,
        "instrucao": (
            "**Informe qual quantidade de Beli deseja:**\n\n"
            "• 5M Beli — R$ 4,00\n"
            "• 10M Beli — R$ 7,00\n"
            "• 25M Beli — R$ 15,00\n"
            "• 50M Beli — R$ 27,00"
        ),
        "opcoes": ["5M Beli", "10M Beli", "25M Beli", "50M Beli"],
        "precos": [4.00, 7.00, 15.00, 27.00],
    },
    "fragmentos": {
        "nome": "💎 Farm de Fragments",
        "cor": 0x1abc9c,
        "instrucao": (
            "**Informe qual quantidade de Fragments deseja:**\n\n"
            "• 5.000 Fragments — R$ 3,00\n"
            "• 10.000 Fragments — R$ 6,00\n"
            "• 25.000 Fragments — R$ 13,00\n"
            "• 50.000 Fragments — R$ 24,00"
        ),
        "opcoes": ["5.000 Fragments", "10.000 Fragments", "25.000 Fragments", "50.000 Fragments"],
        "precos": [3.00, 6.00, 13.00, 24.00],
    },
}


# ====================================
# MODAL DE NICK
# ====================================

class NickModal(discord.ui.Modal, title="Informação da Conta"):
    nick = discord.ui.TextInput(
        label="Nick da sua conta no jogo (opcional)",
        placeholder="Ex: VoidPlayer123 — deixe vazio se quiser informar depois",
        required=False,
        max_length=100
    )

    def __init__(self, service_id: str, opcao_index: int):
        super().__init__()
        self.service_id = service_id
        self.opcao_index = opcao_index

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cog = interaction.client.get_cog("Services")
        if cog:
            await cog.criar_canal(
                interaction,
                self.service_id,
                self.opcao_index,
                self.nick.value.strip() or "Não informado"
            )


# ====================================
# COG
# ====================================

class Services(commands.Cog):
    """Sistema de serviços"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    # ====================================
    # INTERCEPTAR TODOS OS BOTÕES
    # ====================================

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """
        Intercepta TODOS os cliques de botão.
        Identifica pelo custom_id e roteia para a função correta.
        Isso elimina o problema de Views persistentes que param
        de funcionar após reinício.
        """

        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")

        # ── Botões de serviço: svc:frutas:0 ──
        if custom_id.startswith("svc:"):
            parts = custom_id.split(":")
            if len(parts) == 3:
                service_id = parts[1]
                opcao_index = int(parts[2])
                modal = NickModal(service_id, opcao_index)
                await interaction.response.send_modal(modal)
            return

        # ── Fechar canal de serviço ──
        if custom_id == "svc:fechar":
            await self.handle_fechar(interaction)
            return

        # ── Fechar qualquer ticket (tickets.py) ──
        if custom_id == "ticket:fechar":
            cog = self.bot.get_cog("Tickets")
            if cog:
                await cog.handle_fechar(interaction)
            return

        # ── Assumir ticket ──
        if custom_id == "ticket:assumir":
            cog = self.bot.get_cog("Tickets")
            if cog:
                await cog.handle_assumir(interaction)
            return

        # ── Adicionar usuário ao ticket ──
        if custom_id == "ticket:adicionar":
            cog = self.bot.get_cog("Tickets")
            if cog:
                await cog.handle_adicionar(interaction)
            return

        # ── Remover usuário do ticket ──
        if custom_id == "ticket:remover":
            cog = self.bot.get_cog("Tickets")
            if cog:
                await cog.handle_remover(interaction)
            return

        # ── Abrir ticket pelo painel ──
        if custom_id.startswith("panel:"):
            tipo = custom_id.replace("panel:", "")
            cog = self.bot.get_cog("Tickets")
            if cog:
                await cog.abrir_ticket(interaction, tipo)
            return

        # ── Stock: botão comprar ──
        if custom_id == "stock:comprar":
            cog = self.bot.get_cog("StockDisplay")
            if cog:
                await cog.handle_comprar(interaction)
            return

        # ── VIP: assinar ──
        if custom_id == "vip:assinar":
            cog = self.bot.get_cog("VipBoosterPanels")
            if cog:
                await cog.handle_vip_assinar(interaction)
            return

        # ── Booster: ativar ──
        if custom_id == "booster:ativar":
            cog = self.bot.get_cog("VipBoosterPanels")
            if cog:
                await cog.handle_booster_ativar(interaction)
            return

        # ── Booster: dúvidas ──
        if custom_id == "booster:duvidas":
            cog = self.bot.get_cog("VipBoosterPanels")
            if cog:
                await cog.handle_booster_duvidas(interaction)
            return

        # ── Suporte: abrir ──
        if custom_id == "suporte:abrir":
            cog = self.bot.get_cog("Support")
            if cog:
                await cog.handle_abrir(interaction)
            return

        # ── Fechar canal genérico (vip/booster/suporte) ──
        if custom_id == "canal:fechar":
            await self.handle_fechar(interaction)
            return

        # ── PIX rápido ──
        if custom_id == "canal:pix":
            if not PermissionChecker.is_staff(interaction.user):
                await interaction.response.send_message(
                    "❌ Apenas staff.", ephemeral=True
                )
                return
            await interaction.response.send_message(
                "💳 Use `/pix-gerar valor:XX.XX cliente:@usuario`",
                ephemeral=True
            )
            return

    # ====================================
    # CRIAR CANAL DE SERVIÇO
    # ====================================

    async def criar_canal(
        self,
        interaction: discord.Interaction,
        service_id: str,
        opcao_index: int,
        nick: str
    ):
        data = SERVICOS.get(service_id)
        if not data:
            await interaction.followup.send("❌ Serviço não encontrado.", ephemeral=True)
            return

        opcao = data["opcoes"][opcao_index]
        preco = data["precos"][opcao_index]
        guild = interaction.guild
        user = interaction.user

        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            await interaction.followup.send(
                "❌ Categoria não configurada. Avise um admin.", ephemeral=True
            )
            return

        category = guild.get_channel(category_id)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send("❌ Categoria inválida.", ephemeral=True)
            return

        channel_name = f"{service_id}-{user.name}".lower()[:50]

        for ch in category.text_channels:
            if ch.name == channel_name:
                await interaction.followup.send(
                    f"⚠️ Você já tem um canal deste serviço aberto: {ch.mention}",
                    ephemeral=True
                )
                return

        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True, manage_permissions=True),
            }

            if config.STAFF_ROLE_ID:
                r = guild.get_role(config.STAFF_ROLE_ID)
                if r:
                    overwrites[r] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            for rid in config.AUTHORIZED_ROLE_IDS:
                r = guild.get_role(rid)
                if r:
                    overwrites[r] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic=f"{data['nome']} | {opcao} | {user.id}"
            )

            embed = discord.Embed(
                title=data["nome"],
                color=data["cor"],
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.add_field(name="👤 Cliente", value=user.mention, inline=True)
            embed.add_field(name="🎮 Nick no Jogo", value=f"`{nick}`", inline=True)
            embed.add_field(name="📦 Opção", value=f"`{opcao}`", inline=True)
            embed.add_field(name="💰 Valor", value=f"`R$ {preco:.2f}`", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name="💬 Próximo passo", value=data["instrucao"], inline=False)
            embed.set_footer(text="🌑 VOID Store | Atendimento rápido e seguro")

            # Botões usando custom_id simples e fixo
            view = discord.ui.View()

            btn_fechar = discord.ui.Button(
                label="Fechar Canal",
                style=discord.ButtonStyle.red,
                emoji="🔒",
                custom_id="svc:fechar"
            )
            btn_pix = discord.ui.Button(
                label="Gerar PIX",
                style=discord.ButtonStyle.green,
                emoji="💳",
                custom_id="canal:pix"
            )

            view.add_item(btn_fechar)
            view.add_item(btn_pix)

            staff_mention = f"<@&{config.STAFF_ROLE_ID}>" if config.STAFF_ROLE_ID else ""

            await channel.send(
                content=f"{user.mention} {staff_mention}",
                embed=embed,
                view=view
            )

            await interaction.followup.send(
                f"✅ Canal criado: {channel.mention}\nNossa equipe responderá em breve!",
                ephemeral=True
            )

            await self.db.create_log(
                "service", user.id, "channel_created",
                f"Service: {service_id} | Option: {opcao} | Price: {preco}"
            )
            logger.info(f"Service channel: {channel.name} | {user} | {service_id} | {opcao}")

        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão para criar canais.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro criar canal serviço: {e}")
            await interaction.followup.send("❌ Erro ao criar canal.", ephemeral=True)

    # ====================================
    # FECHAR CANAL (genérico)
    # ====================================

    async def handle_fechar(self, interaction: discord.Interaction):
        """Fecha qualquer canal criado pelo bot"""

        is_staff = PermissionChecker.is_staff(interaction.user)
        topic = interaction.channel.topic or ""
        user_id_in_topic = str(interaction.user.id) in topic

        # Verificar se o usuário tem acesso ao canal (é dono)
        perms = interaction.channel.permissions_for(interaction.user)
        can_read = perms.read_messages

        if not (is_staff or user_id_in_topic or can_read):
            await interaction.response.send_message(
                "❌ Você não pode fechar este canal.", ephemeral=True
            )
            return

        # Pedir confirmação com botões inline simples
        embed_confirm = discord.Embed(
            description="⚠️ **Tem certeza que deseja fechar este canal?**",
            color=0xff0000
        )

        view = discord.ui.View()
        btn_sim = discord.ui.Button(label="Sim, fechar", style=discord.ButtonStyle.red)
        btn_nao = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.gray)

        confirmado = False

        async def sim_cb(i: discord.Interaction):
            nonlocal confirmado
            confirmado = True
            view.stop()
            await i.response.defer()

        async def nao_cb(i: discord.Interaction):
            view.stop()
            await i.response.defer()

        btn_sim.callback = sim_cb
        btn_nao.callback = nao_cb
        view.add_item(btn_sim)
        view.add_item(btn_nao)

        await interaction.response.send_message(
            embed=embed_confirm, view=view, ephemeral=True
        )

        await view.wait()

        if not confirmado:
            await interaction.edit_original_response(
                content="❌ Fechamento cancelado.", embed=None, view=None
            )
            return

        # Executar fechamento
        try:
            await interaction.edit_original_response(
                content="✅ Fechando...", embed=None, view=None
            )

            embed_aviso = discord.Embed(
                description=f"🔒 Canal fechado por {interaction.user.mention}. Deletando em **5 segundos**...",
                color=0xff0000
            )
            await interaction.channel.send(embed=embed_aviso)

            await self.db.create_log(
                "canal", interaction.user.id, "fechado",
                f"Channel: {interaction.channel.id}"
            )

            await asyncio.sleep(5)
            await interaction.channel.delete(reason=f"Fechado por {interaction.user}")

        except discord.NotFound:
            pass
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Sem permissão para deletar o canal.", ephemeral=True
            )
        except Exception as e:
            logger.error(f"Erro ao fechar canal: {e}")

    # ====================================
    # COMANDOS DE PAINEL
    # ====================================

    async def _painel(self, interaction: discord.Interaction, service_id: str):
        data = SERVICOS[service_id]

        precos_txt = "\n".join(
            f"• **{op}** — `R$ {pr:.2f}`"
            for op, pr in zip(data["opcoes"], data["precos"])
        )

        embed = discord.Embed(
            title=data["nome"],
            description=(
                f"Escolha a opção desejada clicando no botão abaixo.\n"
                f"Você informará seu nick e um canal privado será aberto.\n\n"
                f"**💰 Preços:**\n{precos_txt}"
            ),
            color=data["cor"],
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text="🌑 VOID Store | Serviço rápido e seguro")

        # Botões com custom_id: svc:service_id:index
        view = discord.ui.View()
        for i, opcao in enumerate(data["opcoes"]):
            btn = discord.ui.Button(
                label=opcao,
                style=discord.ButtonStyle.blurple,
                custom_id=f"svc:{service_id}:{i}"
            )
            view.add_item(btn)

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"✅ Painel **{data['nome']}** criado!", ephemeral=True
        )

    @app_commands.command(name="painel-frutas", description="🍎 Cria o painel de Farm de Frutas")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_frutas(self, interaction: discord.Interaction):
        await self._painel(interaction, "frutas")

    @app_commands.command(name="painel-level", description="⭐ Cria o painel de Farm de Level")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_level(self, interaction: discord.Interaction):
        await self._painel(interaction, "level")

    @app_commands.command(name="painel-materiais", description="🧪 Cria o painel de Farm de Materiais")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_materiais(self, interaction: discord.Interaction):
        await self._painel(interaction, "materiais")

    @app_commands.command(name="painel-v4", description="⚙️ Cria o painel de V4 / Gear")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_v4(self, interaction: discord.Interaction):
        await self._painel(interaction, "v4")

    @app_commands.command(name="painel-money", description="💵 Cria o painel de Farm de Money")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_money(self, interaction: discord.Interaction):
        await self._painel(interaction, "money")

    @app_commands.command(name="painel-fragmentos", description="💎 Cria o painel de Farm de Fragments")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_fragmentos(self, interaction: discord.Interaction):
        await self._painel(interaction, "fragmentos")


async def setup(bot: commands.Bot):
    await bot.add_cog(Services(bot))
