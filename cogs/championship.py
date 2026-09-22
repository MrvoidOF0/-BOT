"""
🌑 VOID Store Bot - Cog de Campeonato PvP
Sistema de Inscrições com Validação de Nível Mínimo (2750) e Bloqueio de Duplicidade.
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime

from utils.logger import setup_logger

logger = setup_logger("Championship")

# Lock assíncrono para evitar race conditions no limite de 10 vagas
CHAMPIONSHIP_LOCK = asyncio.Lock()

# ID do canal onde os logs de inscrição serão enviados
CHANNEL_LOG_ID = 1550272690311659550

# Configurações do Campeonato
MIN_LEVEL = 2750


# ====================================
# MODAL DE INSCRIÇÃO
# ====================================

class ChampionshipModal(discord.ui.Modal, title="🎟️ Inscrição - Campeonato VOID"):
    roblox_nick = discord.ui.TextInput(
        label="Nick do Roblox",
        placeholder="Ex: PlayerRoblox123",
        required=True,
        max_length=50
    )
    fruta = discord.ui.TextInput(
        label="Fruta Principal",
        placeholder="Ex: Dough, Dragon, Portal...",
        required=True,
        max_length=50
    )
    level = discord.ui.TextInput(
        label="Nível no Blox Fruits (Mínimo 2750)",
        placeholder="Ex: 2750",
        required=True,
        max_length=10
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cog = interaction.client.get_cog("Championship")
        if cog:
            await cog.processar_inscricao(
                interaction=interaction,
                roblox_nick=self.roblox_nick.value.strip(),
                fruta=self.fruta.value.strip(),
                level_str=self.level.value.strip()
            )


# ====================================
# COG CHAMPIONSHIP
# ====================================

class Championship(commands.Cog):
    """Sistema do Campeonato PvP da VOID Store"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    async def cog_load(self):
        """Cria a tabela no banco ao carregar a cog"""
        await self._init_db()

    async def _init_db(self):
        """Cria a tabela de inscrições"""
        query = """
        CREATE TABLE IF NOT EXISTS championship_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            roblox_nick TEXT NOT NULL,
            fruta TEXT NOT NULL,
            level TEXT NOT NULL,
            slot_number INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'CONFIRMED'
        );
        """
        try:
            if hasattr(self.db, "execute"):
                await self.db.execute(query)
        except Exception as e:
            logger.error(f"Erro ao inicializar tabela do campeonato: {e}")

    # ====================================
    # INTERCEPTADOR DE BOTÃO (Persistente)
    # ====================================

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")

        if custom_id == "champ:registrar":
            # Verificar se o usuário já se registrou antes mesmo de abrir o modal
            inscrito = await self._buscar_inscricao_usuario(interaction.user.id)
            if inscrito:
                slot_num = inscrito.get("slot_number") if isinstance(inscrito, dict) else inscrito[6]
                await interaction.response.send_message(
                    f"⚠️ **Você já está inscrito!**\nSua inscrição está confirmada como **Participante #{slot_num}/10** e não é possível se registrar novamente.",
                    ephemeral=True
                )
                return

            modal = ChampionshipModal()
            await interaction.response.send_modal(modal)

    # ====================================
    # PROCESSAMENTO DA INSCRIÇÃO
    # ====================================

    async def processar_inscricao(self, interaction: discord.Interaction, roblox_nick: str, fruta: str, level_str: str):
        user = interaction.user

        # 1. Validação de Nível Mínimo
        # Limpa qualquer caractere não numérico digitado (ex: "lvl 2750" -> 2750)
        digits_only = "".join(filter(str.isdigit, level_str))
        
        if not digits_only:
            await interaction.followup.send(
                "❌ **Nível inválido!** Por favor, insira apenas o número do seu nível no Blox Fruits.",
                ephemeral=True
            )
            return

        level_num = int(digits_only)

        if level_num < MIN_LEVEL:
            await interaction.followup.send(
                f"❌ **Inscrição recusada!** O nível mínimo exigido para participar do campeonato é **{MIN_LEVEL}**.\n"
                f"Seu nível informado foi: `{level_num}`.",
                ephemeral=True
            )
            return

        async with CHAMPIONSHIP_LOCK:
            # 2. Re-verificar se já está inscrito (Garantia anti-race condition)
            inscrito = await self._buscar_inscricao_usuario(user.id)
            if inscrito:
                slot_num = inscrito.get("slot_number") if isinstance(inscrito, dict) else inscrito[6]
                await interaction.followup.send(
                    f"⚠️ Você já está inscrito neste campeonato como **Participante #{slot_num}/10**.",
                    ephemeral=True
                )
                return

            # 3. Verificar total de vagas preenchidas
            total_inscritos = await self._contar_inscritos()
            if total_inscritos >= 10:
                await interaction.followup.send(
                    "❌ As **10 vagas** do campeonato já foram totalmente preenchidas!",
                    ephemeral=True
                )
                return

            # 4. Registrar a vaga
            slot_number = total_inscritos + 1
            created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            sucesso = await self._salvar_inscricao(
                user_id=user.id,
                username=str(user),
                roblox_nick=roblox_nick,
                fruta=fruta,
                level=str(level_num),
                slot_number=slot_number,
                created_at=created_at
            )

            if sucesso:
                # Confirmação privada ao usuário
                embed_sucesso = discord.Embed(
                    title="🎟️ INSCRIÇÃO CONFIRMADA!",
                    description=(
                        f"Parabéns {user.mention}, sua vaga no **Campeonato PvP VOID Store** está garantida!\n\n"
                        f"> 📌 **Posição:** Participante `#{slot_number}/10`\n"
                        f"> 🎮 **Roblox:** `{roblox_nick}`\n"
                        f"> 🍎 **Fruta:** `{fruta}`\n"
                        f"> ⭐ **Nível:** `{level_num}`"
                    ),
                    color=0x10B981,
                    timestamp=discord.utils.utcnow()
                )
                embed_sucesso.set_footer(text="🌑 VOID Store • Boa sorte na arena!")
                await interaction.followup.send(embed=embed_sucesso, ephemeral=True)

                # Notificação pública no canal de inscrições
                await self._notificar_canal_inscricao(
                    user=user,
                    roblox_nick=roblox_nick,
                    fruta=fruta,
                    level=str(level_num),
                    slot_number=slot_number
                )

                logger.info(f"Campeonato: {user} registrado como participante #{slot_number}")
            else:
                await interaction.followup.send(
                    "❌ Ocorreu um erro ao processar sua inscrição no banco de dados. Tente novamente.",
                    ephemeral=True
                )

    async def _notificar_canal_inscricao(self, user: discord.User, roblox_nick: str, fruta: str, level: str, slot_number: int):
        """Envia o log do participante registrado no canal de destino"""
        channel = self.bot.get_channel(CHANNEL_LOG_ID)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(CHANNEL_LOG_ID)
            except Exception as e:
                logger.error(f"Não foi possível encontrar o canal de inscrições ({CHANNEL_LOG_ID}): {e}")
                return

        embed_log = discord.Embed(
            title=f"📥 NOVA INSCRIÇÃO REGISTRADA [#{slot_number}/10]",
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )
        embed_log.add_field(name="👤 Discord", value=f"{user.mention} (`{user.id}`)", inline=False)
        embed_log.add_field(name="🎮 Nick Roblox", value=f"`{roblox_nick}`", inline=True)
        embed_log.add_field(name="🍎 Fruta Principal", value=f"`{fruta}`", inline=True)
        embed_log.add_field(name="⭐ Nível", value=f"`{level}`", inline=True)
        embed_log.set_thumbnail(url=user.display_avatar.url)
        embed_log.set_footer(text="🌑 VOID Store • Campeonato PvP")

        await channel.send(embed=embed_log)

    # ====================================
    # OPERAÇÕES DE BANCO DE DADOS
    # ====================================

    async def _buscar_inscricao_usuario(self, user_id: int):
        try:
            query = "SELECT * FROM championship_registrations WHERE user_id = ?;"
            if hasattr(self.db, "fetchone"):
                return await self.db.fetchone(query, (user_id,))
        except Exception as e:
            logger.error(f"Erro ao buscar inscrito: {e}")
        return None

    async def _contar_inscritos(self) -> int:
        try:
            query = "SELECT COUNT(*) FROM championship_registrations WHERE status = 'CONFIRMED';"
            if hasattr(self.db, "fetchone"):
                res = await self.db.fetchone(query)
                if res:
                    return res[0] if isinstance(res, (tuple, list)) else res.get("COUNT(*)", 0)
        except Exception as e:
            logger.error(f"Erro ao contar inscritos: {e}")
        return 0

    async def _salvar_inscricao(self, user_id: int, username: str, roblox_nick: str, fruta: str, level: str, slot_number: int, created_at: str) -> bool:
        try:
            query = """
            INSERT INTO championship_registrations (user_id, username, roblox_nick, fruta, level, slot_number, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """
            params = (user_id, username, roblox_nick, fruta, level, slot_number, created_at)

            if hasattr(self.db, "execute"):
                await self.db.execute(query, params)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar inscrição: {e}")
            return False

    async def _obter_todos_inscritos(self):
        try:
            query = "SELECT slot_number, user_id, username, roblox_nick, fruta, level FROM championship_registrations WHERE status = 'CONFIRMED' ORDER BY slot_number ASC;"
            if hasattr(self.db, "fetchall"):
                return await self.db.fetchall(query)
        except Exception as e:
            logger.error(f"Erro ao buscar inscritos: {e}")
        return []

    # ====================================
    # COMANDOS SLASH
    # ====================================

    @app_commands.command(name="campeonato", description="🏆 Publica o painel do Campeonato PvP da VOID Store")
    @app_commands.checks.has_permissions(administrator=True)
    async def publicar_campeonato(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌑 VOID STORE | CAMPEONATO PVP",
            description=(
                "⚔️ **10 JOGADORES. 1 CAMPEÃO.**\n"
                "A arena da **VOID Store** está oficialmente aberta!\n"
                "Prepare sua melhor build, enfrente seus adversários e lute pelo título de **🏆 Campeão VOID**.\n\n"
                "───\n\n"
                "### 📌 INFORMAÇÕES DO TORNEIO\n"
                "> 👥 **Vagas:** 10 Jogadores\n"
                "> ⭐ **Requisito:** Nível Mínimo 2750\n"
                "> ⚔️ **Formato:** PvP 1v1 (Eliminação Simples)\n"
                "> 🎥 **Transmissão:** Partidas Registradas\n\n"
                "### 📋 ESTRUTURA DAS PARTIDAS\n"
                "• **Preliminares:** 2 Partidas (1v1)\n"
                "• **Quartas de Final:** Melhor de 3 (MD3)\n"
                "• **Semifinais:** Melhor de 3 (MD3)\n"
                "• **Grande Final:** Melhor de 5 (MD5)\n\n"
                "### 🎁 PREMIAÇÕES EXCLUSIVAS\n"
                "🥇 **1º Lugar:** `2x Control` + Benefício na VOID\n"
                "🥈 **2º Lugar:** `1x Tiger`\n"
                "🥉 **3º Lugar:** `1x Dough`\n\n"
                "───\n\n"
                "### 🎟️ COMO SE INSCREVER\n"
                "Clique no botão abaixo **`🎟️ Registrar-se`**, preencha com seus dados do Roblox e garanta a sua vaga!\n\n"
                "⚠️ *Atenção: Apenas jogadores de nível 2750 ou superior podem participar.*"
            ),
            color=0x2B2D31
        )
        embed.set_footer(text="🌑 VOID STORE • Onde a batalha começa e apenas um chega ao topo.")

        view = discord.ui.View(timeout=None)
        btn_registrar = discord.ui.Button(
            label="Registrar-se",
            style=discord.ButtonStyle.primary,
            emoji="🎟️",
            custom_id="champ:registrar"
        )
        view.add_item(btn_registrar)

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel do Campeonato enviado com sucesso!", ephemeral=True)

    @app_commands.command(name="inscritos", description="📋 Lista todos os participantes inscritos no Campeonato")
    @app_commands.checks.has_permissions(administrator=True)
    async def listar_inscritos(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        inscritos = await self._obter_todos_inscritos()

        if not inscritos:
            await interaction.followup.send("⚠️ Nenhum jogador se inscreveu até o momento.", ephemeral=True)
            return

        linhas = []
        for row in inscritos:
            if isinstance(row, dict):
                idx, user_id, roblox_nick, fruta, level = row['slot_number'], row['user_id'], row['roblox_nick'], row['fruta'], row['level']
            else:
                idx, user_id, _, roblox_nick, fruta, level = row[0], row[1], row[2], row[3], row[4], row[5]

            linhas.append(f"`#{idx}` | <@{user_id}> | **Roblox:** `{roblox_nick}` | **Fruta:** `{fruta}` | **Nível:** `{level}`")

        embed = discord.Embed(
            title="🏆 Lista de Inscritos - Campeonato VOID",
            description="\n".join(linhas),
            color=0x3B82F6,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Total: {len(inscritos)}/10 inscritos")

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Championship(bot))
