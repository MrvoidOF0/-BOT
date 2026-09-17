"""
🌑 VOID Store Bot - Sistema Booster
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from utils.embeds import VoidEmbeds
from utils.permissions import PermissionChecker
from utils.constants import Emojis
from utils.logger import logger
from config import config


class Booster(commands.Cog):
    """Suporte e gerenciamento do cargo Booster"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    def _get_booster_role(self, guild: discord.Guild) -> Optional[discord.Role]:
        """Retorna o cargo Booster configurado"""
        if not config.BOOSTER_ROLE_ID:
            return None
        return guild.get_role(config.BOOSTER_ROLE_ID)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """
        Listener que detecta quando um membro faz ou cancela o boost.
        Atribui ou remove o cargo Booster automaticamente.
        """

        # Verificar mudança no status de boost
        boost_started = before.premium_since is None and after.premium_since is not None
        boost_ended = before.premium_since is not None and after.premium_since is None

        if not (boost_started or boost_ended):
            return

        booster_role = self._get_booster_role(after.guild)

        if boost_started:
            await self._handle_new_booster(after, booster_role)
        elif boost_ended:
            await self._handle_booster_removed(after, booster_role)

    async def _handle_new_booster(
        self,
        member: discord.Member,
        booster_role: Optional[discord.Role]
    ):
        """Processa um novo booster"""

        logger.info(f"New booster detected: {member}")

        # Adicionar cargo configurado
        if booster_role and not member.get_role(booster_role.id):
            try:
                await member.add_roles(
                    booster_role,
                    reason="VOID Store: Server Boost detectado"
                )
                logger.info(f"Booster role added to {member}")
            except discord.Forbidden:
                logger.error(f"No permission to add booster role to {member}")

        # Notificar por DM
        try:
            embed = VoidEmbeds.success(
                "Obrigado pelo Boost! 🚀",
                f"Você está dando boost no servidor da VOID Store!\n\n"
                f"**Seus Benefícios:**\n"
                f"• 5% OFF em todos os serviços\n"
                f"• Prioridade no atendimento\n"
                f"• Acesso antecipado a promoções\n"
                f"• 1 benefício surpresa por mês\n"
                f"• Participação em sorteios exclusivos\n"
                f"• Prioridade em pedidos"
            )
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

        # Log
        await self.db.create_log(
            "booster",
            member.id,
            "boost_started",
            f"Member: {member.id}"
        )

        # Enviar log no servidor
        await self._send_booster_log(
            member.guild,
            f"{Emojis.BOOSTER} **Novo Booster!**",
            f"{member.mention} começou a dar boost no servidor!\nBenefícios Booster ativados automaticamente."
        )

    async def _handle_booster_removed(
        self,
        member: discord.Member,
        booster_role: Optional[discord.Role]
    ):
        """Processa a remoção de boost"""

        logger.info(f"Boost removed: {member}")

        # Remover cargo configurado
        if booster_role and member.get_role(booster_role.id):
            try:
                await member.remove_roles(
                    booster_role,
                    reason="VOID Store: Server Boost encerrado"
                )
                logger.info(f"Booster role removed from {member}")
            except discord.Forbidden:
                logger.error(f"No permission to remove booster role from {member}")

        # Log
        await self.db.create_log(
            "booster",
            member.id,
            "boost_ended",
            f"Member: {member.id}"
        )

    async def _send_booster_log(self, guild: discord.Guild, title: str, description: str):
        """Envia log de booster"""
        log_channel_id = config.LOG_CHANNEL_ID
        if not log_channel_id:
            return

        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = VoidEmbeds.default(title, description)
        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending booster log: {e}")

    booster_group = app_commands.Group(
        name="booster",
        description="🚀 Informações e gerenciamento do cargo Booster"
    )

    @booster_group.command(
        name="info",
        description="🚀 Exibe os benefícios do cargo Booster"
    )
    async def booster_info(self, interaction: discord.Interaction):
        """Exibe os benefícios do Booster"""

        embed = VoidEmbeds.default(
            f"{Emojis.BOOSTER} Benefícios Booster — VOID Store",
            "Benefícios exclusivos para quem apoia o servidor com Nitro Boost!"
        )

        embed.add_field(
            name="Como Ativar",
            value="Dê boost no servidor da VOID Store com Nitro!",
            inline=False
        )

        embed.add_field(
            name="Benefícios",
            value=(
                f"• 5% OFF em todos os serviços\n"
                f"• Prioridade no atendimento\n"
                f"• Acesso antecipado a promoções\n"
                f"• 1 benefício surpresa por mês\n"
                f"• Cargo Booster exclusivo\n"
                f"• Participação em sorteios exclusivos\n"
                f"• Prioridade em pedidos"
            ),
            inline=False
        )

        embed.add_field(
            name="Observação",
            value="O cargo Booster é atribuído **automaticamente** ao dar boost.",
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @booster_group.command(
        name="listar",
        description="🚀 Lista todos os Boosters do servidor"
    )
    async def list_boosters(self, interaction: discord.Interaction):
        """Lista membros Boosters"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        boosters = [m for m in interaction.guild.members if m.premium_since is not None]

        if not boosters:
            await interaction.response.send_message(
                f"{Emojis.INFO} Nenhum membro está dando boost no momento.",
                ephemeral=True
            )
            return

        member_list = "\n".join(
            f"• {m.mention} (desde {m.premium_since.strftime('%d/%m/%Y')})"
            for m in boosters[:20]
        )

        if len(boosters) > 20:
            member_list += f"\n... e mais {len(boosters) - 20} boosters."

        embed = VoidEmbeds.default(
            f"{Emojis.BOOSTER} Boosters Ativos",
            member_list
        )
        embed.set_footer(text=f"🌑 VOID Store | Total: {len(boosters)} Boosters")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Booster(bot))
