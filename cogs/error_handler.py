"""
🌑 VOID Store Bot - Handler Global de Erros
"""

import discord
from discord import app_commands
from discord.ext import commands
import traceback
import sys

from utils.embeds import VoidEmbeds
from utils.constants import Emojis
from utils.logger import logger
from config import config


class ErrorHandler(commands.Cog):
    """
    Intercepta e trata todos os erros do bot de forma centralizada.
    Garante que o bot nunca quebre silenciosamente.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Registrar handler global de erros de slash commands
        self.bot.tree.on_error = self.on_app_command_error

    # ====================================
    # HANDLER DE SLASH COMMANDS
    # ====================================

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        """
        Trata todos os erros de slash commands.
        Chamado automaticamente pelo discord.py quando um slash command falha.
        """

        # Desempacotar erros encapsulados
        if isinstance(error, app_commands.CommandInvokeError):
            error = error.original

        # ====================================
        # ERROS DE PERMISSÃO
        # ====================================
        if isinstance(error, app_commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = VoidEmbeds.error(
                "Permissão Insuficiente",
                f"Você não tem as permissões necessárias para este comando.\n"
                f"**Necessário:** `{perms}`"
            )
            await self._respond(interaction, embed)
            return

        if isinstance(error, app_commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = VoidEmbeds.error(
                "Bot sem Permissão",
                f"Não tenho as permissões necessárias para executar esta ação.\n"
                f"**Faltando:** `{perms}`\n\n"
                f"Verifique as permissões do bot no servidor."
            )
            await self._respond(interaction, embed)
            return

        # ====================================
        # ERROS DE COOLDOWN
        # ====================================
        if isinstance(error, app_commands.CommandOnCooldown):
            embed = VoidEmbeds.warning(
                "Aguarde um Momento",
                f"Este comando está em cooldown.\n"
                f"**Tente novamente em:** `{error.retry_after:.1f}` segundos."
            )
            await self._respond(interaction, embed)
            return

        # ====================================
        # ERROS DE GUILD ONLY
        # ====================================
        if isinstance(error, app_commands.NoPrivateMessage):
            embed = VoidEmbeds.error(
                "Comando Indisponível",
                "Este comando só pode ser usado dentro de um servidor."
            )
            await self._respond(interaction, embed)
            return

        # ====================================
        # ERROS DE CHECK (PERMISSÕES CUSTOM)
        # ====================================
        if isinstance(error, app_commands.CheckFailure):
            embed = VoidEmbeds.error(
                "Acesso Negado",
                "Você não tem permissão para usar este comando."
            )
            await self._respond(interaction, embed)
            return

        # ====================================
        # ERROS DO DISCORD (FORBIDDEN, NOT FOUND)
        # ====================================
        if isinstance(error, discord.Forbidden):
            embed = VoidEmbeds.error(
                "Ação Bloqueada",
                "Não tenho permissão para executar esta ação.\n"
                "Verifique se o meu cargo está acima do alvo na hierarquia."
            )
            await self._respond(interaction, embed)
            return

        if isinstance(error, discord.NotFound):
            embed = VoidEmbeds.error(
                "Não Encontrado",
                "O recurso solicitado não foi encontrado no Discord."
            )
            await self._respond(interaction, embed)
            return

        if isinstance(error, discord.HTTPException):
            embed = VoidEmbeds.error(
                "Erro de Comunicação",
                f"Ocorreu um erro ao comunicar com o Discord.\n"
                f"**Código:** `{error.status}` — Tente novamente."
            )
            await self._respond(interaction, embed)
            return

        # ====================================
        # ERROS NÃO MAPEADOS (CRÍTICOS)
        # ====================================
        logger.error(
            f"Unhandled error in command '{interaction.command.name if interaction.command else 'unknown'}': "
            f"{type(error).__name__}: {error}",
            exc_info=error
        )

        # Notificar admin se configurado
        await self._notify_admin(interaction, error)

        embed = VoidEmbeds.error(
            "Erro Inesperado",
            "Ocorreu um erro interno. Nossa equipe foi notificada.\n"
            "Se o problema persistir, contate um administrador."
        )
        await self._respond(interaction, embed)

    # ====================================
    # HELPERS
    # ====================================

    async def _respond(self, interaction: discord.Interaction, embed: discord.Embed):
        """Responde à interação de forma segura, lidando com interações já respondidas"""
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")

    async def _notify_admin(self, interaction: discord.Interaction, error: Exception):
        """Envia notificação de erro crítico para o canal de logs"""
        try:
            log_channel_id = config.LOG_CHANNEL_ID
            if not log_channel_id or not interaction.guild:
                return

            log_channel = interaction.guild.get_channel(log_channel_id)
            if not log_channel:
                return

            tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            if len(tb) > 1800:
                tb = tb[-1800:]

            embed = VoidEmbeds.error(
                "🚨 Erro Crítico Detectado",
                f"**Comando:** `{interaction.command.name if interaction.command else 'N/A'}`\n"
                f"**Usuário:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"**Canal:** {interaction.channel.mention if interaction.channel else 'N/A'}\n"
                f"**Erro:** `{type(error).__name__}: {str(error)[:200]}`\n\n"
                f"```py\n{tb}\n```"
            )

            await log_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to notify admin about error: {e}")

    # ====================================
    # EVENTOS DE ERRO GLOBAIS
    # ====================================

    @commands.Cog.listener()
    async def on_error(self, event: str, *args, **kwargs):
        """Captura erros em eventos (listeners)"""
        exc_type, exc_value, exc_tb = sys.exc_info()
        logger.error(
            f"Error in event '{event}': {exc_type.__name__}: {exc_value}",
            exc_info=(exc_type, exc_value, exc_tb)
        )

    @commands.Cog.listener()
    async def on_guild_unavailable(self, guild: discord.Guild):
        """Log quando um servidor fica indisponível"""
        logger.warning(f"Guild unavailable: {guild.name} ({guild.id})")

    @commands.Cog.listener()
    async def on_disconnect(self):
        """Log quando o bot se desconecta"""
        logger.warning("Bot disconnected from Discord. Attempting reconnect...")

    @commands.Cog.listener()
    async def on_resumed(self):
        """Log quando o bot reconecta"""
        logger.info("Bot session resumed successfully.")


async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorHandler(bot))
