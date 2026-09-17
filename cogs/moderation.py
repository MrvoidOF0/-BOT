"""
🌑 VOID Store Bot - Sistema de Moderação
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import timedelta

from utils.embeds import VoidEmbeds
from utils.permissions import PermissionChecker
from utils.constants import Emojis
from utils.logger import logger
from config import config


class Moderation(commands.Cog):
    """Sistema de moderação completo"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    # ====================================
    # HELPERS
    # ====================================

    async def _send_mod_log(
        self,
        guild: discord.Guild,
        action: str,
        moderator: discord.Member,
        target: discord.Member,
        reason: str,
        extra: Optional[str] = None
    ):
        """Envia embed de log de moderação para o canal configurado"""

        log_channel_id = config.MOD_LOG_CHANNEL_ID or config.LOG_CHANNEL_ID
        if not log_channel_id:
            return

        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return

        description = (
            f"**Moderador:** {moderator.mention}\n"
            f"**Usuário:** {target.mention} (`{target.id}`)\n"
            f"**Motivo:** {reason}"
        )

        if extra:
            description += f"\n**Info:** {extra}"

        embed = VoidEmbeds.default(f"{action}", description)

        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending mod log: {e}")

    def _can_act_on(
        self,
        moderator: discord.Member,
        target: discord.Member
    ) -> tuple[bool, str]:
        """
        Verifica se o moderador pode agir sobre o alvo.
        Protege donos, admins e cargos mais altos.
        """

        if target.id == moderator.guild.owner_id:
            return False, "Você não pode moderar o dono do servidor."

        if target.top_role >= moderator.top_role:
            return False, "Você não pode moderar alguém com cargo igual ou superior ao seu."

        bot_member = moderator.guild.get_member(moderator.guild.me.id)
        if bot_member and target.top_role >= bot_member.top_role:
            return False, "Não tenho permissão para moderar este usuário (cargo acima do meu)."

        return True, ""

    # ====================================
    # COMANDOS DE MODERAÇÃO
    # ====================================

    @app_commands.command(name="ban", description="🔨 Bane um usuário do servidor")
    @app_commands.describe(
        membro="Membro a ser banido",
        motivo="Motivo do banimento",
        deletar_mensagens="Dias de mensagens a deletar (0-7)"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: Optional[str] = "Não especificado",
        deletar_mensagens: Optional[int] = 0
    ):
        """Bane um membro"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_mod=True):
            return

        can_act, error_msg = self._can_act_on(interaction.user, membro)
        if not can_act:
            await interaction.response.send_message(
                f"{Emojis.ERROR} {error_msg}",
                ephemeral=True
            )
            return

        # Garantir range de 0-7
        delete_days = max(0, min(7, deletar_mensagens or 0))

        await interaction.response.defer()

        # Tentar notificar o usuário antes de banir
        try:
            dm_embed = VoidEmbeds.error(
                "Você foi banido",
                f"Você foi banido do servidor **{interaction.guild.name}**.\n"
                f"**Motivo:** {motivo}"
            )
            await membro.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        try:
            await interaction.guild.ban(
                membro,
                reason=f"[VOID Store] {interaction.user} - {motivo}",
                delete_message_days=delete_days
            )

            embed = VoidEmbeds.success(
                f"{Emojis.BAN} Usuário Banido",
                f"**Usuário:** {membro.mention} (`{membro.id}`)\n"
                f"**Motivo:** {motivo}\n"
                f"**Moderador:** {interaction.user.mention}"
            )
            await interaction.followup.send(embed=embed)

            # Log
            await self._send_mod_log(
                interaction.guild,
                f"{Emojis.BAN} Banimento",
                interaction.user,
                membro,
                motivo
            )

            await self.db.create_log(
                "moderation",
                interaction.user.id,
                "ban",
                f"Target: {membro.id} | Reason: {motivo}"
            )

            logger.info(f"User {membro} banned by {interaction.user}: {motivo}")

        except discord.Forbidden:
            await interaction.followup.send(
                f"{Emojis.ERROR} Não tenho permissão para banir este usuário.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error banning user: {e}")
            await interaction.followup.send(
                f"{Emojis.ERROR} Erro ao executar banimento.",
                ephemeral=True
            )

    @app_commands.command(name="kick", description="👢 Expulsa um usuário do servidor")
    @app_commands.describe(
        membro="Membro a ser expulso",
        motivo="Motivo da expulsão"
    )
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: Optional[str] = "Não especificado"
    ):
        """Expulsa um membro"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_mod=True):
            return

        can_act, error_msg = self._can_act_on(interaction.user, membro)
        if not can_act:
            await interaction.response.send_message(
                f"{Emojis.ERROR} {error_msg}",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            dm_embed = VoidEmbeds.warning(
                "Você foi expulso",
                f"Você foi expulso do servidor **{interaction.guild.name}**.\n"
                f"**Motivo:** {motivo}"
            )
            await membro.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        try:
            await interaction.guild.kick(
                membro,
                reason=f"[VOID Store] {interaction.user} - {motivo}"
            )

            embed = VoidEmbeds.success(
                f"{Emojis.KICK} Usuário Expulso",
                f"**Usuário:** {membro.mention} (`{membro.id}`)\n"
                f"**Motivo:** {motivo}\n"
                f"**Moderador:** {interaction.user.mention}"
            )
            await interaction.followup.send(embed=embed)

            await self._send_mod_log(
                interaction.guild,
                f"{Emojis.KICK} Expulsão",
                interaction.user,
                membro,
                motivo
            )

            await self.db.create_log(
                "moderation",
                interaction.user.id,
                "kick",
                f"Target: {membro.id} | Reason: {motivo}"
            )

            logger.info(f"User {membro} kicked by {interaction.user}: {motivo}")

        except discord.Forbidden:
            await interaction.followup.send(
                f"{Emojis.ERROR} Não tenho permissão para expulsar este usuário.",
                ephemeral=True
            )

    @app_commands.command(name="timeout", description="⏰ Silencia temporariamente um usuário")
    @app_commands.describe(
        membro="Membro a ser silenciado",
        duracao="Duração em minutos (máx. 40320 = 28 dias)",
        motivo="Motivo do timeout"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        duracao: int,
        motivo: Optional[str] = "Não especificado"
    ):
        """Aplica timeout em um membro"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_mod=True):
            return

        can_act, error_msg = self._can_act_on(interaction.user, membro)
        if not can_act:
            await interaction.response.send_message(
                f"{Emojis.ERROR} {error_msg}",
                ephemeral=True
            )
            return

        if duracao <= 0 or duracao > 40320:
            await interaction.response.send_message(
                f"{Emojis.ERROR} Duração inválida. Use entre **1** e **40320** minutos (28 dias).",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            until = discord.utils.utcnow() + timedelta(minutes=duracao)
            await membro.timeout(until, reason=f"[VOID Store] {interaction.user} - {motivo}")

            horas = duracao // 60
            minutos = duracao % 60
            duracao_fmt = f"{horas}h {minutos}min" if horas > 0 else f"{minutos} min"

            embed = VoidEmbeds.success(
                f"{Emojis.TIMEOUT} Timeout Aplicado",
                f"**Usuário:** {membro.mention}\n"
                f"**Duração:** {duracao_fmt}\n"
                f"**Motivo:** {motivo}\n"
                f"**Moderador:** {interaction.user.mention}"
            )
            await interaction.followup.send(embed=embed)

            await self._send_mod_log(
                interaction.guild,
                f"{Emojis.TIMEOUT} Timeout",
                interaction.user,
                membro,
                motivo,
                extra=f"Duração: {duracao_fmt}"
            )

            await self.db.create_log(
                "moderation",
                interaction.user.id,
                "timeout",
                f"Target: {membro.id} | Duration: {duracao}min | Reason: {motivo}"
            )

            logger.info(f"Timeout applied to {membro} by {interaction.user}: {duracao}min")

        except discord.Forbidden:
            await interaction.followup.send(
                f"{Emojis.ERROR} Não tenho permissão para aplicar timeout.",
                ephemeral=True
            )

    @app_commands.command(name="untimeout", description="✅ Remove o timeout de um usuário")
    @app_commands.describe(
        membro="Membro que terá o timeout removido",
        motivo="Motivo da remoção"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: Optional[str] = "Timeout removido manualmente"
    ):
        """Remove timeout de um membro"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_mod=True):
            return

        await interaction.response.defer()

        try:
            await membro.timeout(None, reason=f"[VOID Store] {interaction.user} - {motivo}")

            embed = VoidEmbeds.success(
                f"{Emojis.SUCCESS} Timeout Removido",
                f"**Usuário:** {membro.mention}\n"
                f"**Motivo:** {motivo}\n"
                f"**Moderador:** {interaction.user.mention}"
            )
            await interaction.followup.send(embed=embed)

            await self._send_mod_log(
                interaction.guild,
                f"{Emojis.SUCCESS} Timeout Removido",
                interaction.user,
                membro,
                motivo
            )

            await self.db.create_log(
                "moderation",
                interaction.user.id,
                "untimeout",
                f"Target: {membro.id} | Reason: {motivo}"
            )

        except discord.Forbidden:
            await interaction.followup.send(
                f"{Emojis.ERROR} Não tenho permissão para remover timeout.",
                ephemeral=True
            )

    @app_commands.command(name="warn", description="⚠️ Emite um aviso formal para um usuário")
    @app_commands.describe(
        membro="Membro a ser advertido",
        motivo="Motivo do aviso"
    )
    async def warn(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: str
    ):
        """Emite um aviso formal"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_mod=True):
            return

        can_act, error_msg = self._can_act_on(interaction.user, membro)
        if not can_act:
            await interaction.response.send_message(
                f"{Emojis.ERROR} {error_msg}",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        # Notificar usuário por DM
        try:
            dm_embed = VoidEmbeds.warning(
                "Você recebeu um aviso",
                f"**Servidor:** {interaction.guild.name}\n"
                f"**Motivo:** {motivo}\n\n"
                f"Por favor, siga as regras do servidor."
            )
            await membro.send(embed=dm_embed)
            dm_sent = True
        except discord.Forbidden:
            dm_sent = False

        embed = VoidEmbeds.warning(
            f"{Emojis.WARN} Aviso Emitido",
            f"**Usuário:** {membro.mention}\n"
            f"**Motivo:** {motivo}\n"
            f"**Moderador:** {interaction.user.mention}\n"
            f"**DM Enviada:** {'Sim' if dm_sent else 'Não (DMs fechadas)'}"
        )
        await interaction.followup.send(embed=embed)

        await self._send_mod_log(
            interaction.guild,
            f"{Emojis.WARN} Aviso",
            interaction.user,
            membro,
            motivo
        )

        await self.db.create_log(
            "moderation",
            interaction.user.id,
            "warn",
            f"Target: {membro.id} | Reason: {motivo}"
        )

        logger.info(f"Warning issued to {membro} by {interaction.user}: {motivo}")

    @app_commands.command(name="clear", description="🧹 Apaga mensagens do canal")
    @app_commands.describe(
        quantidade="Número de mensagens a deletar (máx. 100)",
        membro="Filtrar mensagens de um membro específico"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(
        self,
        interaction: discord.Interaction,
        quantidade: int,
        membro: Optional[discord.Member] = None
    ):
        """Limpa mensagens do canal"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_mod=True):
            return

        if quantidade <= 0 or quantidade > 100:
            await interaction.response.send_message(
                f"{Emojis.ERROR} Informe um valor entre **1** e **100**.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        def check(msg):
            if membro:
                return msg.author.id == membro.id
            return True

        try:
            deleted = await interaction.channel.purge(
                limit=quantidade,
                check=check,
                reason=f"[VOID Store] Clear by {interaction.user}"
            )

            target_txt = f" de {membro.mention}" if membro else ""
            await interaction.followup.send(
                f"{Emojis.SUCCESS} **{len(deleted)}** mensagens{target_txt} deletadas.",
                ephemeral=True
            )

            await self.db.create_log(
                "moderation",
                interaction.user.id,
                "clear",
                f"Channel: {interaction.channel.id} | Count: {len(deleted)}"
            )

            logger.info(f"Cleared {len(deleted)} messages in {interaction.channel} by {interaction.user}")

        except discord.Forbidden:
            await interaction.followup.send(
                f"{Emojis.ERROR} Não tenho permissão para deletar mensagens.",
                ephemeral=True
            )

    # ====================================
    # HANDLER DE ERROS DOS COMANDOS
    # ====================================

    @ban.error
    @kick.error
    @timeout.error
    @untimeout.error
    @clear.error
    async def mod_error_handler(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError
    ):
        """Handler global de erros para comandos de moderação"""
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                f"{Emojis.ERROR} Você não tem a permissão necessária para usar este comando.",
                ephemeral=True
            )
        else:
            logger.error(f"Unhandled mod error: {error}", exc_info=error)
            await interaction.response.send_message(
                f"{Emojis.ERROR} Ocorreu um erro inesperado.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
