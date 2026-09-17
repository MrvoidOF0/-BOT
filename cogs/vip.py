"""
🌑 VOID Store Bot - Sistema VIP
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from utils.embeds import VoidEmbeds
from utils.permissions import PermissionChecker
from utils.constants import Emojis
from utils.helpers import format_currency
from utils.logger import logger
from config import config


class VIP(commands.Cog):
    """Sistema de cargo VIP separado da progressão de compras"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    def _get_vip_role(self, guild: discord.Guild) -> Optional[discord.Role]:
        """Retorna o cargo VIP configurado"""
        if not config.VIP_ROLE_ID:
            return None
        return guild.get_role(config.VIP_ROLE_ID)

    # ====================================
    # GRUPO DE COMANDOS /vip
    # ====================================

    vip_group = app_commands.Group(
        name="vip",
        description="💎 Gerenciamento do cargo VIP"
    )

    @vip_group.command(
        name="conceder",
        description="💎 Concede o cargo VIP a um usuário"
    )
    @app_commands.describe(
        membro="Usuário que receberá o VIP",
        motivo="Motivo da concessão"
    )
    async def grant_vip(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: Optional[str] = "Aquisição do plano VIP"
    ):
        """Concede o cargo VIP a um membro"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        vip_role = self._get_vip_role(interaction.guild)
        if not vip_role:
            await interaction.response.send_message(
                f"{Emojis.ERROR} Cargo VIP não configurado. Use `/setup` para configurar.",
                ephemeral=True
            )
            return

        # Verificar se já é VIP
        if membro.get_role(vip_role.id):
            await interaction.response.send_message(
                f"{Emojis.WARNING} {membro.mention} já possui o cargo VIP.",
                ephemeral=True
            )
            return

        try:
            await membro.add_roles(vip_role, reason=f"VOID Store VIP: {motivo}")

            embed = VoidEmbeds.success(
                "VIP Concedido",
                f"{membro.mention} recebeu o cargo **{Emojis.VIP} VIP**!\n"
                f"**Motivo:** {motivo}"
            )

            embed.add_field(
                name="Benefícios Ativos",
                value=(
                    "• 10% OFF em serviços selecionados\n"
                    "• 2× prioridade no atendimento\n"
                    "• 1 pedido prioritário por mês\n"
                    "• 2 promoções exclusivas por mês\n"
                    "• 24h de acesso antecipado\n"
                    "• Acesso a Eventos VIP"
                ),
                inline=False
            )

            await interaction.response.send_message(embed=embed)

            # Notificar usuário por DM
            try:
                dm_embed = VoidEmbeds.success(
                    "Bem-vindo ao VIP! 💎",
                    f"Você recebeu o cargo **VIP** na VOID Store!\n\n"
                    f"**Seus Benefícios:**\n"
                    f"• 10% OFF em serviços selecionados\n"
                    f"• 2× prioridade no atendimento\n"
                    f"• 1 pedido prioritário por mês\n"
                    f"• 2 promoções exclusivas por mês\n"
                    f"• 24h de acesso antecipado\n"
                    f"• Acesso a Eventos VIP"
                )
                await membro.send(embed=dm_embed)
            except discord.Forbidden:
                pass

            # Log
            await self.db.create_log(
                "vip",
                interaction.user.id,
                "granted",
                f"Target: {membro.id} | Reason: {motivo}"
            )

            logger.info(f"VIP granted to {membro} by {interaction.user}")

        except discord.Forbidden:
            await interaction.response.send_message(
                f"{Emojis.ERROR} Sem permissão para conceder o cargo VIP.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error granting VIP: {e}")
            await interaction.response.send_message(
                f"{Emojis.ERROR} Erro ao conceder VIP.",
                ephemeral=True
            )

    @vip_group.command(
        name="remover",
        description="💎 Remove o cargo VIP de um usuário"
    )
    @app_commands.describe(
        membro="Usuário que terá o VIP removido",
        motivo="Motivo da remoção"
    )
    async def remove_vip(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: Optional[str] = "Plano VIP encerrado"
    ):
        """Remove o cargo VIP de um membro"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        vip_role = self._get_vip_role(interaction.guild)
        if not vip_role:
            await interaction.response.send_message(
                f"{Emojis.ERROR} Cargo VIP não configurado.",
                ephemeral=True
            )
            return

        if not membro.get_role(vip_role.id):
            await interaction.response.send_message(
                f"{Emojis.WARNING} {membro.mention} não possui o cargo VIP.",
                ephemeral=True
            )
            return

        try:
            await membro.remove_roles(vip_role, reason=f"VOID Store VIP Removed: {motivo}")

            embed = VoidEmbeds.warning(
                "VIP Removido",
                f"O cargo VIP de {membro.mention} foi removido.\n"
                f"**Motivo:** {motivo}"
            )
            await interaction.response.send_message(embed=embed)

            await self.db.create_log(
                "vip",
                interaction.user.id,
                "removed",
                f"Target: {membro.id} | Reason: {motivo}"
            )

            logger.info(f"VIP removed from {membro} by {interaction.user}")

        except discord.Forbidden:
            await interaction.response.send_message(
                f"{Emojis.ERROR} Sem permissão para remover o cargo VIP.",
                ephemeral=True
            )

    @vip_group.command(
        name="info",
        description="💎 Exibe informações sobre o plano VIP"
    )
    async def vip_info(self, interaction: discord.Interaction):
        """Exibe as informações do plano VIP"""

        embed = VoidEmbeds.default(
            f"{Emojis.VIP} Plano VIP — VOID Store",
            "Acesso exclusivo aos melhores benefícios da VOID Store."
        )

        embed.add_field(
            name="Preço",
            value="💰 R$ 19,90",
            inline=True
        )

        embed.add_field(
            name="Tipo",
            value="Cargo independente",
            inline=True
        )

        embed.add_field(
            name="\u200b",
            value="\u200b",
            inline=True
        )

        embed.add_field(
            name="Benefícios Inclusos",
            value=(
                f"• 10% OFF em serviços selecionados\n"
                f"• 2× prioridade no atendimento\n"
                f"• 1 pedido prioritário por mês\n"
                f"• 2 promoções exclusivas por mês\n"
                f"• 24h de acesso antecipado\n"
                f"• Cargo VIP exclusivo\n"
                f"• Convites para Eventos VIP"
            ),
            inline=False
        )

        embed.add_field(
            name="Observação",
            value=(
                "O VIP é **independente** dos cargos de progressão "
                "(Starter, Plus, Premium, Supreme, Prestige).\n"
                "Ambos podem ser acumulados."
            ),
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    @vip_group.command(
        name="listar",
        description="💎 Lista todos os membros com cargo VIP"
    )
    async def list_vip(self, interaction: discord.Interaction):
        """Lista membros VIP ativos"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        vip_role = self._get_vip_role(interaction.guild)
        if not vip_role:
            await interaction.response.send_message(
                f"{Emojis.ERROR} Cargo VIP não configurado.",
                ephemeral=True
            )
            return

        members_with_vip = [m for m in interaction.guild.members if vip_role in m.roles]

        if not members_with_vip:
            await interaction.response.send_message(
                f"{Emojis.INFO} Nenhum membro possui o cargo VIP no momento.",
                ephemeral=True
            )
            return

        member_list = "\n".join(f"• {m.mention}" for m in members_with_vip[:20])
        if len(members_with_vip) > 20:
            member_list += f"\n... e mais {len(members_with_vip) - 20} membros."

        embed = VoidEmbeds.default(
            f"{Emojis.VIP} Membros VIP Ativos",
            member_list
        )
        embed.set_footer(text=f"🌑 VOID Store | Total: {len(members_with_vip)} VIPs")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(VIP(bot))
