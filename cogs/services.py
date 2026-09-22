"""
🌑 VOID Store Bot - Serviços (Design Aprimorado)
Abordagem: Sem Views persistentes complexas (interceptado por custom_id).
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio
import io

from utils.permissions import PermissionChecker
from utils.logger import logger
from config import config

# ====================================
# DADOS DOS SERVIÇOS E CONFIGURAÇÃO VISUAL
# ====================================

SERVICOS = {
    "frutas": {
        "nome": "🍎 Farm de Frutas",
        "cor": 0xA855F7,  # Roxo vibrante
        "banner": "",  # Opcional: Adicione imagem/banner se desejar
        "instrucao": (
            "> **Informe os detalhes do seu pedido:**\n"
            "Qual fruta você deseja focar e por quantas horas prefere o farm?"
        ),
        "opcoes": ["1 hora", "2 horas", "3 horas", "5 horas", "10 horas"],
        "precos": [3.00, 5.00, 7.00, 10.00, 18.00],
    },
    "level": {
        "nome": "⭐ Farm de Level",
        "cor": 0x3B82F6,  # Azul royal
        "instrucao": (
            "> **Informe os detalhes do seu pedido:**\n"
            "Qual o seu nível atual e qual o pacote escolhido?"
        ),
        "opcoes": ["+100 níveis", "+300 níveis", "+500 níveis", "+1.000 níveis", "Level Máximo"],
        "precos": [2.00, 5.00, 8.00, 14.00, 22.00],
    },
    "materiais": {
        "nome": "🧪 Farm de Materiais",
        "cor": 0x10B981,  # Verde esmeralda
        "instrucao": (
            "> **Informe os detalhes do seu pedido:**\n"
            "Qual tipo de material você precisa no momento?"
        ),
        "opcoes": ["Comuns 100x", "Incomuns 100x", "Raros 100x", "Especiais 100x"],
        "precos": [2.00, 3.00, 5.00, 7.00],
    },
    "v4": {
        "nome": "⚙️ Desbloqueio V4 & Gears",
        "cor": 0xEF4444,  # Vermelho carmesim
        "instrucao": (
            "> **Informe os detalhes do seu pedido:**\n"
            "Qual Gear ou etapa da V4 você deseja que a equipe realize?"
        ),
        "opcoes": ["Gear 1", "Gear 2", "Gear 3", "Gear 4", "V4 Completa"],
        "precos": [8.00, 8.00, 10.00, 12.00, 30.00],
    },
    "money": {
        "nome": "💵 Farm de Money (Beli)",
        "cor": 0xF59E0B,  # Âmbar/Dourado
        "instrucao": (
            "> **Informe os detalhes do seu pedido:**\n"
            "Confirme a quantia necessária para iniciar a entrega."
        ),
        "opcoes": ["5M Beli", "10M Beli", "25M Beli", "50M Beli"],
        "precos": [4.00, 7.00, 15.00, 27.00],
    },
    "fragmentos": {
        "nome": "💎 Farm de Fragments",
        "cor": 0x06B6D4,  # Ciano reluzente
        "instrucao": (
            "> **Informe os detalhes do seu pedido:**\n"
            "Qual pacote de Fragments você deseja adquirir?"
        ),
        "opcoes": ["5.000 Fragments", "10.000 Fragments", "25.000 Fragments", "50.000 Fragments"],
        "precos": [3.00, 6.00, 13.00, 24.00],
    },
}


# ====================================
# MODAL DE NICK
# ====================================

class NickModal(discord.ui.Modal, title="🌑 VOID Store — Informações"):
    nick = discord.ui.TextInput(
        label="Nick no jogo (Roblox/Game)",
        placeholder="Ex: VoidPlayer123 — Deixe em branco se quiser informar depois",
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
    """Sistema de gerenciamento e exibição de serviços"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    # ====================================
    # LISTENER INTERCEPTADOR DE INTERAÇÕES
    # ====================================

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
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

        # ── Fechar qualquer ticket ──
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

        # ── Stock ──
        if custom_id == "stock:comprar":
            cog = self.bot.get_cog("StockDisplay")
            if cog:
                await cog.handle_comprar(interaction)
            return

        # ── VIP / Booster ──
        if custom_id == "vip:assinar":
            cog = self.bot.get_cog("VipBoosterPanels")
            if cog:
                await cog.handle_vip_assinar(interaction)
            return

        if custom_id == "booster:ativar":
            cog = self.bot.get_cog("VipBoosterPanels")
            if cog:
                await cog.handle_booster_ativar(interaction)
            return

        if custom_id == "booster:duvidas":
            cog = self.bot.get_cog("VipBoosterPanels")
            if cog:
                await cog.handle_booster_duvidas(interaction)
            return

        # ── Suporte ──
        if custom_id == "suporte:abrir":
            cog = self.bot.get_cog("Support")
            if cog:
                await cog.handle_abrir(interaction)
            return

        # ── Fechar canal genérico ──
        if custom_id == "canal:fechar":
            await self.handle_fechar(interaction)
            return

        # ── PIX rápido ──
        if custom_id == "canal:pix":
            if not PermissionChecker.is_staff(interaction.user):
                await interaction.response.send_message("❌ Apenas staff pode usar este recurso.", ephemeral=True)
                return
            await interaction.response.send_message("💳 **Comando PIX:** `/pix-gerar valor:XX.XX cliente:@usuario`", ephemeral=True)
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
            await interaction.followup.send("❌ Categoria de atendimento não configurada.", ephemeral=True)
            return

        category = guild.get_channel(category_id)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send("❌ Categoria de atendimento inválida.", ephemeral=True)
            return

        channel_name = f"{service_id}-{user.name}".lower()[:50]

        for ch in category.text_channels:
            if ch.name == channel_name:
                await interaction.followup.send(
                    f"⚠️ Você já possui um atendimento em andamento para este serviço: {ch.mention}",
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

            # --- EMBED DO CANAL PRIVADO ---
            embed = discord.Embed(
                title=f"🛒 {data['nome']}",
                description="Seu canal de atendimento exclusivo foi aberto! Confira as informações do seu pedido abaixo e aguarde a equipe.",
                color=data["cor"],
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=user.display_avatar.url)

            embed.add_field(name="👤 **Cliente**", value=user.mention, inline=True)
            embed.add_field(name="🎮 **Nick no Jogo**", value=f"`{nick}`", inline=True)
            embed.add_field(name="📦 **Pacote Selecionado**", value=f"`{opcao}`", inline=True)
            embed.add_field(name="💰 **Valor Total**", value=f"`R$ {preco:.2f}`", inline=True)
            embed.add_field(name="⚡ **Status**", value="`Aguardando Staff`", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True) # Espaçador

            embed.add_field(name="📝 **Instruções ao Cliente**", value=data["instrucao"], inline=False)
            embed.set_footer(text="🌑 VOID Store • Atendimento Seguro e Qualificado", icon_url=guild.icon.url if guild.icon else None)

            view = discord.ui.View()
            btn_fechar = discord.ui.Button(
                label="Encerrar Canal",
                style=discord.ButtonStyle.red,
                emoji="🔒",
                custom_id="svc:fechar"
            )
            btn_pix = discord.ui.Button(
                label="Gerar Pagamento PIX",
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
                f"✅ **Atendimento criado:** {channel.mention}\nSiga para o canal para concluir seu pedido!",
                ephemeral=True
            )

            await self.db.create_log(
                "service", user.id, "channel_created",
                f"Service: {service_id} | Option: {opcao} | Price: {preco}"
            )
            logger.info(f"Service channel: {channel.name} | {user} | {service_id} | {opcao}")

        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão de administrador/canal no servidor.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro ao criar canal de serviço: {e}")
            await interaction.followup.send("❌ Ocorreu um erro interno ao criar seu canal.", ephemeral=True)

    # ====================================
    # FECHAR CANAL (genérico com Transcript)
    # ====================================

    async def handle_fechar(self, interaction: discord.Interaction):
        """Fecha o canal e gera histórico para registro"""

        is_staff = PermissionChecker.is_staff(interaction.user)
        topic = interaction.channel.topic or ""
        user_id_in_topic = str(interaction.user.id) in topic

        perms = interaction.channel.permissions_for(interaction.user)
        can_read = perms.read_messages

        if not (is_staff or user_id_in_topic or can_read):
            await interaction.response.send_message(
                "❌ Você não tem permissão para fechar este atendimento.", ephemeral=True
            )
            return

        embed_confirm = discord.Embed(
            title="⚠️ Confirmação de Encerramento",
            description="Tem certeza de que deseja fechar este canal?\nEsta ação **não poderá ser desfeita**.",
            color=0xEF4444
        )

        view = discord.ui.View()
        btn_sim = discord.ui.Button(label="Sim, encerrar", style=discord.ButtonStyle.red, emoji="✅")
        btn_nao = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.secondary, emoji="✖️")

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

        await interaction.response.send_message(embed=embed_confirm, view=view, ephemeral=True)
        await view.wait()

        if not confirmado:
            await interaction.edit_original_response(
                content="❌ Ação de encerramento cancelada.", embed=None, view=None
            )
            return

        try:
            await interaction.edit_original_response(
                content="⏳ Gerando relatório do atendimento e finalizando...", embed=None, view=None
            )

            channel = interaction.channel
            guild = interaction.guild

            # 1. Compilar Histórico
            messages = []
            async for msg in channel.history(limit=1000, oldest_first=True):
                time_str = msg.created_at.strftime("%d/%m/%Y %H:%M:%S")
                content = msg.content if msg.content else "[Sem texto / Embed ou Imagem]"
                messages.append(f"[{time_str}] {msg.author.name} ({msg.author.id}): {content}")

            transcript_text = f"=== HISTÓRICO VOID STORE - CANAL #{channel.name} ===\n\n" + "\n".join(messages)
            transcript_file = discord.File(
                fp=io.BytesIO(transcript_text.encode("utf-8")),
                filename=f"transcript-{channel.name}.txt"
            )

            # 2. Enviar para Logs
            log_channel_id = getattr(config, "TICKET_LOGS_CHANNEL_ID", 1549933790309257226)
            log_channel = guild.get_channel(log_channel_id)

            if not log_channel:
                try:
                    log_channel = await guild.fetch_channel(log_channel_id)
                except Exception:
                    pass

            if log_channel:
                embed_log = discord.Embed(
                    title="📜 Registros de Atendimento Finalizado",
                    color=0x1F2937,
                    timestamp=discord.utils.utcnow()
                )
                embed_log.add_field(name="💬 **Canal**", value=f"`#{channel.name}`", inline=True)
                embed_log.add_field(name="🔒 **Encerrado por**", value=f"{interaction.user.mention}", inline=True)
                embed_log.set_footer(text="🌑 VOID Store • Sistema de Logs Autônomo")

                await log_channel.send(embed=embed_log, file=transcript_file)

            embed_aviso = discord.Embed(
                description=f"🔒 Atendimento finalizado por {interaction.user.mention}.\nO canal será exluído em **5 segundos**...",
                color=0xEF4444
            )
            await channel.send(embed=embed_aviso)

            await self.db.create_log(
                "canal", interaction.user.id, "fechado",
                f"Channel: {channel.id}"
            )

            await asyncio.sleep(5)
            await channel.delete(reason=f"Encerrado por {interaction.user}")

        except discord.NotFound:
            pass
        except discord.Forbidden:
            await interaction.followup.send("❌ Permissão insuficiente para apagar o canal.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro ao fechar canal: {e}")

    # ====================================
    # GERAR PAINÉIS DE SERVIÇO
    # ====================================

    async def _painel(self, interaction: discord.Interaction, service_id: str):
        data = SERVICOS[service_id]

        precos_txt = "\n".join(
            f"🔹 **{op}** ➔ `R$ {pr:.2f}`"
            for op, pr in zip(data["opcoes"], data["precos"])
        )

        # --- EMBED DO PAINEL PÚBLICO ---
        embed = discord.Embed(
            title=f"🌑 VOID Store | {data['nome']}",
            description=(
                f"Obtenha os melhores pacotes com a maior rapidez e segurança do mercado.\n\n"
                f"### 💸 Tabela de Valores\n{precos_txt}\n\n"
                f"> 💡 **Como comprar?**\n"
                f"> Clique no botão abaixo correspondente ao pacote desejado para abrir um canal de compra exclusivo."
            ),
            color=data["cor"],
            timestamp=discord.utils.utcnow()
        )
        
        if "banner" in data:
            embed.set_image(url=data["banner"])

        embed.set_footer(
            text="🌑 VOID Store • Qualidade e Agilidade Garantidas",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )

        view = discord.ui.View()
        for i, opcao in enumerate(data["opcoes"]):
            btn = discord.ui.Button(
                label=opcao,
                style=discord.ButtonStyle.primary,
                custom_id=f"svc:{service_id}:{i}"
            )
            view.add_item(btn)

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"✅ Painel **{data['nome']}** gerado com sucesso!", ephemeral=True
        )

    # ====================================
    # COMANDOS SLASH DOS PAINÉIS
    # ====================================

    @app_commands.command(name="painel-frutas", description="🍎 Exibe o painel de Farm de Frutas")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_frutas(self, interaction: discord.Interaction):
        await self._painel(interaction, "frutas")

    @app_commands.command(name="painel-level", description="⭐ Exibe o painel de Farm de Level")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_level(self, interaction: discord.Interaction):
        await self._painel(interaction, "level")

    @app_commands.command(name="painel-materiais", description="🧪 Exibe o painel de Farm de Materiais")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_materiais(self, interaction: discord.Interaction):
        await self._painel(interaction, "materiais")

    @app_commands.command(name="painel-v4", description="⚙️ Exibe o painel de V4 / Gear")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_v4(self, interaction: discord.Interaction):
        await self._painel(interaction, "v4")

    @app_commands.command(name="painel-money", description="💵 Exibe o painel de Farm de Money")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_money(self, interaction: discord.Interaction):
        await self._painel(interaction, "money")

    @app_commands.command(name="painel-fragmentos", description="💎 Exibe o painel de Farm de Fragments")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_fragmentos(self, interaction: discord.Interaction):
        await self._painel(interaction, "fragmentos")


async def setup(bot: commands.Bot):
    await bot.add_cog(Services(bot))
