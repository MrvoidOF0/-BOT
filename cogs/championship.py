"""
🌑 VOID Store Bot - Cog de Campeonato PvP
Inscrições limitadas a 10 participantes com persistência pós-reinício.
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime

from utils.permissions import PermissionChecker
from utils.logger import logger
from config import config

# Lock assíncrono para prevenir race conditions no limite de 10 vagas
CHAMPIONSHIP_LOCK = asyncio.Lock()


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
        label="Fruta principal",
        placeholder="Ex: Dough, Dragon, Portal...",
        required=True,
        max_length=50
    )
    level = discord.ui.TextInput(
        label="Nível no Blox Fruits",
        placeholder="Ex: 2550",
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
                level=self.level.value.strip()
            )


# ====================================
# COG CHAMPIONSHIP
# ====================================

class Championship(commands.Cog):
    """Sistema do Campeonato PvP da VOID Store"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    async def cog_load(self):
        """Garante a criação da tabela no banco de dados ao carregar a Cog"""
        await self._init_db()

    async def _init_db(self):
        """Cria a tabela de inscrições se não existir"""
        try:
            # Compatível com SQLite / PostgreSQL via bot.db
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
            if hasattr(self.db, "execute"):
                await self.db.execute(query)
            elif hasattr(self.db, "conn"):
                async with self.db.conn.cursor() as cursor:
                    await cursor.execute(query)
                await self.db.conn.commit()
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
            modal = ChampionshipModal()
            await interaction.response.send_modal(modal)

    # ====================================
    # PROCESSAMENTO DA INSCRIÇÃO
    # ====================================

    async def processar_inscricao(self, interaction: discord.Interaction, roblox_nick: str, fruta: str, level: str):
        user = interaction.user

        async with CHAMPIONSHIP_LOCK:
            # 1. Verificar se já está inscrito
            inscrito = await self._buscar_inscricao_usuario(user.id)
            if inscrito:
                await interaction.followup.send(
                    f"⚠️ Você já está inscrito neste campeonato como **Participante #{inscrito['slot_number']}/10**.",
                    ephemeral=True
                )
                return

            # 2. Verificar total de vagas preenchidas
            total_inscritos = await self._contar_inscritos()
            if total_inscritos >= 10:
                await interaction.followup.send(
                    "❌ As **10 vagas** do campeonato já foram preenchidas!",
                    ephemeral=True
                )
                return

            # 3. Registrar a vaga
            slot_number = total_inscritos + 1
            created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            sucesso = await self._salvar_inscricao(
                user_id=user.id,
                username=str(user),
                roblox_nick=roblox_nick,
                fruta=fruta,
                level=level,
                slot_number=slot_number,
                created_at=created_at
            )

            if sucesso:
                embed_sucesso = discord.Embed(
                    title="🎟️ Inscrição Confirmada!",
                    description=(
                        f"Parabéns {user.mention}, sua vaga no **Campeonato PvP VOID Store** está garantida!\n\n"
                        f"📌 **Posição:** Participante `#{slot_number}/10`\n"
                        f"🎮 **Nick Roblox:** `{roblox_nick}`\n"
                        f"🍎 **Fruta:** `{fruta}`\n"
                        f"⭐ **Nível:** `{level}`"
                    ),
                    color=0x10B981,
                    timestamp=discord.utils.utcnow()
                )
                embed_sucesso.set_footer(text="🌑 VOID Store • Boa sorte no torneio!")
                await interaction.followup.send(embed=embed_sucesso, ephemeral=True)

                logger.info(f"Campeonato: {user} registrado como participante #{slot_number}")
            else:
                await interaction.followup.send(
                    "❌ Ocorreu um erro ao processar sua inscrição. Tente novamente.",
                    ephemeral=True
                )

    # ====================================
    # OPERAÇÕES DE BANCO DE DADOS
    # ====================================

    async def _buscar_inscricao_usuario(self, user_id: int):
        try:
            query = "SELECT * FROM championship_registrations WHERE user_id = ?;"
            if hasattr(self.db, "fetchone"):
                return await self.db.fetchone(query, (user_id,))
            elif hasattr(self.db, "conn"):
                async with self.db.conn.cursor() as cursor:
                    await cursor.execute(query, (user_id,))
                    row = await cursor.fetchone()
                    if row:
                        return {"slot_number": row[6]}
        except Exception as e:
            logger.error(f"Erro ao buscar inscrito: {e}")
        return None

    async def _contar_inscritos(self) -> int:
        try:
            query = "SELECT COUNT(*) FROM championship_registrations WHERE status = 'CONFIRMED';"
            if hasattr(self.db, "fetchone"):
                res = await self.db.fetchone(query)
                return res[0] if res else 0
            elif hasattr(self.db, "conn"):
                async with self.db.conn.cursor() as cursor:
                    await cursor.execute(query)
                    res = await cursor.fetchone()
                    return res[0] if res else 0
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
            elif hasattr(self.db, "conn"):
                async with self.db.conn.cursor() as cursor:
                    await cursor.execute(query, params)
                await self.db.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar inscrição: {e}")
            return False

    async def _obter_todos_inscritos(self):
        try:
            query = "SELECT slot_number, user_id, username, roblox_nick, fruta, level FROM championship_registrations ORDER BY slot_number ASC;"
            if hasattr(self.db, "fetchall"):
                return await self.db.fetchall(query)
            elif hasattr(self.db, "conn"):
                async with self.db.conn.cursor() as cursor:
                    await cursor.execute(query)
                    return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Erro ao buscar todos os inscritos: {e}")
        return []

    # ====================================
    # COMANDOS SLASH
    # ====================================

    @app_commands.command(name="campeonato", description="🏆 Publica o painel do Campeonato PvP da VOID Store")
    @app_commands.checks.has_permissions(administrator=True)
    async def publicar_campeonato(self, interaction: discord.Interaction):
        # Texto exato fornecido
        embed_text = (
            "[**🌑**](https://discord.com/assets/8f162e8dbd1bfd6c.svg) **VOID STORE | CAMPEONATO PVP**\n\n"
            "[⚔️](https://discord.com/assets/fa2c28d64be33d41.svg) **10 JOGADORES. 1 CAMPEÃO.**  A arena da **VOID Store** está aberta.\n"
            "Prepare sua melhor build, enfrente seus adversários e lute pelo título de [**🏆**](https://discord.com/assets/f11aff9f1c8c5f19.svg) **Campeão VOID**.  \n\n"
            "> [👥](https://discord.com/assets/be8706c9515e4e6e.svg) **10 VAGAS** [⚔️](https://discord.com/assets/fa2c28d64be33d41.svg) **1V1** [🏁](https://discord.com/assets/e5333cf49e7d6d2b.svg) **ELIMINAÇÃO** [🏆](https://discord.com/assets/f11aff9f1c8c5f19.svg) **PREMIAÇÃO** [🎥](https://discord.com/assets/c64b52fae182324d.svg) **PARTIDAS REGISTRADAS** \n\n"
            "[📋](https://discord.com/assets/2a9a2a207078420b.svg) COMO FUNCIONA **2 preliminares → Quartas → Semifinais → Final**  [🔥](https://discord.com/assets/a7bd71d6389d0dfe.svg) Quartas e semifinais: **MD3**\n"
            "[👑](https://discord.com/assets/b09a9a54f8e34d23.svg) Grande final: **MD5**  [🎁](https://discord.com/assets/949f113339307625.svg) PREMIAÇÃO  [🥇](https://discord.com/assets/08b871e132a77f8b.svg) **1º Lugar:** 2 controls + benefício na VOID [🥈](https://discord.com/assets/e60f28f718ca79b5.svg) **2º Lugar:** 1 tiger [🥉](https://discord.com/assets/21d7244670423a9b.svg) **3º Lugar:** 1 dough  [🎟️](https://discord.com/assets/dde8a9804160342c.svg) INSCRIÇÕES Garanta sua vaga no botão abaixo.  [⚠️](https://discord.com/assets/fb6fd920c79bd504.svg) **Vagas limitadas: apenas 10 participantes.**  ━━━━━━━━━━━━━━━━━━━━  [🌑](https://discord.com/assets/8f162e8dbd1bfd6c.svg) **VOID STORE** *Onde a batalha começa e apenas um chega ao topo.*"
        )

        embed = discord.Embed(
            description=embed_text,
            color=0x4F46E5,
            timestamp=discord.utils.utcnow()
        )

        view = discord.ui.View(timeout=None)
        btn_registrar = discord.ui.Button(
            label="Registrar-se",
            style=discord.ButtonStyle.blurple,
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
        for idx, user_id, username, roblox_nick, fruta, level in inscritos:
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
