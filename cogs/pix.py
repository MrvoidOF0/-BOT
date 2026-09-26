"""
🌑 VOID Store Bot - Cog de Pagamento PIX (Nubank / Manual)
Permite configurar os dados do PIX e exibe as informações de pagamento para o cliente.
"""

import discord
from discord import app_commands
from discord.ext import commands
from utils.logger import setup_logger

logger = setup_logger("PIX")


class Pix(commands.Cog):
    """Sistema de Pagamentos PIX via Nubank / Chave Manual"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    async def cog_load(self):
        """Cria a tabela no banco de dados ao carregar a cog"""
        await self._init_db()

    async def _init_db(self):
        """Inicializa a tabela para guardar a configuração do PIX"""
        query = """
        CREATE TABLE IF NOT EXISTS pix_config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            chave_pix TEXT NOT NULL,
            titular TEXT NOT NULL,
            copia_cola TEXT
        );
        """
        try:
            if hasattr(self.db, "execute"):
                await self.db.execute(query)
        except Exception as e:
            logger.error(f"Erro ao inicializar a tabela pix_config: {e}")

    # ====================================
    # MÉTODOS DE BANCO DE DADOS
    # ====================================

    async def _salvar_config_pix(self, chave: str, titular: str, copia_cola: str = "") -> bool:
        """Guarda ou atualiza a chave PIX no banco de dados"""
        query = """
        INSERT INTO pix_config (id, chave_pix, titular, copia_cola)
        VALUES (1, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            chave_pix = excluded.chave_pix,
            titular = excluded.titular,
            copia_cola = excluded.copia_cola;
        """
        try:
            if hasattr(self.db, "execute"):
                await self.db.execute(query, (chave, titular, copia_cola))
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar configuracao do PIX: {e}")
            return False

    async def _obter_config_pix(self):
        """Procura as configurações atuais do PIX"""
        query = "SELECT chave_pix, titular, copia_cola FROM pix_config WHERE id = 1;"
        try:
            if hasattr(self.db, "fetchone"):
                return await self.db.fetchone(query)
        except Exception as e:
            logger.error(f"Erro ao buscar configuracao do PIX: {e}")
        return None

    # ====================================
    # COMANDOS SLASH
    # ====================================

    @app_commands.command(
        name="pix-configurar",
        description="⚙️ Configura os dados da conta Nubank/PIX para recebimentos (Apenas Admins)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        chave="Tua chave PIX (CPF, E-mail, Telemóvel ou Aleatória)",
        titular="Nome completo do titular da conta Nubank",
        copia_cola="Código Copia e Cola estático do Nubank (Opcional)"
    )
    async def pix_configurar(
        self,
        interaction: discord.Interaction,
        chave: str,
        titular: str,
        copia_cola: str = ""
    ):
        await interaction.response.defer(ephemeral=True)

        sucesso = await self._salvar_config_pix(chave, titular, copia_cola)

        if sucesso:
            embed = discord.Embed(
                title="✅ PIX Configurado com Sucesso!",
                description=(
                    "As informações de pagamento foram guardadas no bot:\n\n"
                    f"> 🔑 **Chave PIX:** `{chave}`\n"
                    f"> 👤 **Titular:** `{titular}`\n"
                    f"> 📋 **Copia e Cola:** `{copia_cola if copia_cola else 'Não informado'}`"
                ),
                color=0x820AD1
            )
            embed.set_footer(text="🌑 VOID Store • Configuração PIX Nubank")
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(
                "❌ Ocorreu um erro ao guardar as configurações do PIX no banco de dados.",
                ephemeral=True
            )

    @app_commands.command(
        name="pix-gerar",
        description="💳 Exibe as informações e a chave PIX para o cliente realizar o pagamento"
    )
    async def pix_gerar(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        config = await self._obter_config_pix()

        if not config:
            await interaction.followup.send(
                "⚠️ **O PIX ainda não foi configurado pela administração!**\n"
                "Usa o comando `/pix-configurar` para guardar os dados da conta Nubank.",
                ephemeral=True
            )
            return

        # Trata o formato de retorno do banco de dados (dict ou tuple)
        if isinstance(config, dict):
            chave = config.get("chave_pix")
            titular = config.get("titular")
            copia_cola = config.get("copia_cola", "")
        else:
            chave, titular, copia_cola = config[0], config[1], config[2]

        embed = discord.Embed(
            title="💳 PAGAMENTO VIA NUBANK (PIX)",
            description=(
                "Para concluir a tua compra, realiza o pagamento via PIX utilizando os dados abaixo:\n\n"
                f"> 🔑 **Chave PIX:** `{chave}`\n"
                f"> 👤 **Titular:** `{titular}`\n"
                "> 🏦 **Banco:** Nu Pagamentos S.A. (Nubank)\n\n"
                "📌 **Instruções:**\n"
                "1. Realiza a transferência no valor do teu pedido.\n"
                "2. Envia o **comprovativo de pagamento** neste canal.\n"
                "3. Aguarda que a nossa equipa confirme e entregue o teu produto!"
            ),
            color=0x820AD1
        )

        if copia_cola and copia_cola.strip():
            embed.add_field(
                name="📋 PIX Copia e Cola",
                value=f"```\n{copia_cola}\n```",
                inline=False
            )

        embed.set_thumbnail(url="https://i.imgur.com/39A8E7n.png")  # Ícone roxo/estilizado
        embed.set_footer(text="🌑 VOID Store • Aguardando comprovativo de pagamento")

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Pix(bot))
