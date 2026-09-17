"""
🌑 VOID Store Bot - Sistema de Cargos Automáticos por Compras
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


class Roles(commands.Cog):
    """Sistema de progressão de cargos baseado em valor gasto"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    # ====================================
    # LÓGICA PRINCIPAL
    # ====================================

    async def check_user_tier(self, member: discord.Member) -> Optional[str]:
        """
        Verifica e atualiza o cargo de progressão do cliente.
        
        Este método é chamado automaticamente toda vez que um pedido
        é marcado como CONCLUÍDO pelo sistema de pedidos.

        Args:
            member: Membro do Discord a verificar

        Returns:
            Nome do novo cargo ou None se não houve mudança
        """

        # 1. Buscar dados do usuário no banco
        user = await self.db.get_user(member.id)
        if not user:
            logger.warning(f"check_user_tier: User {member} not found in database.")
            return None

        total_spent = user.total_spent

        # 2. Definir os tiers (do MAIOR para o MENOR para comparação)
        tiers = config.get_role_tiers()
        ordered_tiers = [
            tiers["PRESTIGE"],
            tiers["SUPREME"],
            tiers["PREMIUM"],
            tiers["PLUS"],
            tiers["STARTER"],
        ]

        # 3. Descobrir qual tier o usuário merece agora
        deserved_tier = None
        for tier in ordered_tiers:
            if total_spent >= tier["threshold"]:
                deserved_tier = tier
                break

        if not deserved_tier:
            logger.info(f"User {member} doesn't qualify for any tier yet. Total: {total_spent}")
            return None

        # 4. Verificar se o usuário já tem esse cargo
        role_id = deserved_tier["role_id"]
        if not role_id:
            logger.warning(f"Tier {deserved_tier['name']} has no role_id configured.")
            return None

        role = member.guild.get_role(role_id)
        if not role:
            logger.warning(f"Role {role_id} not found in guild.")
            return None

        if member.get_role(role_id):
            logger.info(f"User {member} already has role {role['name']}. No changes.")
            return None

        # 5. Remover cargos de tier inferiores para manter organização
        old_role_name = await self._remove_lower_tier_roles(member, deserved_tier, tiers)

        # 6. Adicionar o novo cargo
        try:
            await member.add_roles(role, reason=f"VOID Store: Tier {deserved_tier['name']} atingido")
            logger.info(f"Role {role.name} added to {member}")
        except discord.Forbidden:
            logger.error(f"No permission to add role {role.name} to {member}")
            return None
        except Exception as e:
            logger.error(f"Error adding role to {member}: {e}")
            return None

        # 7. Registrar log no banco
        await self.db.create_log(
            "role",
            member.id,
            "tier_updated",
            f"New: {deserved_tier['name']} | Spent: {total_spent}"
        )

        # 8. Notificar o usuário por DM
        await self._notify_user(member, old_role_name, deserved_tier, total_spent)

        # 9. Enviar log no canal do servidor
        await self._send_role_log(
            member.guild,
            member,
            old_role_name,
            deserved_tier["name"],
            total_spent
        )

        return deserved_tier["name"]

    async def _remove_lower_tier_roles(
        self,
        member: discord.Member,
        new_tier: dict,
        all_tiers: dict
    ) -> Optional[str]:
        """
        Remove cargos de tiers inferiores ao novo cargo.
        
        Garante que um cliente só tenha UM cargo de progressão.
        NUNCA remove cargos administrativos ou de staff.

        Args:
            member: Membro do Discord
            new_tier: Tier que será atribuído
            all_tiers: Dicionário com todos os tiers

        Returns:
            Nome do cargo anterior (se havia) ou None
        """

        old_role_name = None

        for tier_name, tier_data in all_tiers.items():
            # Pular o tier que será adicionado
            if tier_data["name"] == new_tier["name"]:
                continue

            role_id = tier_data["role_id"]
            if not role_id:
                continue

            # Verificar se o membro tem este cargo
            existing_role = member.get_role(role_id)
            if not existing_role:
                continue

            # Verificar se o cargo está abaixo da posição do bot (segurança)
            bot_member = member.guild.get_member(self.bot.user.id)
            if bot_member and existing_role.position >= bot_member.top_role.position:
                logger.warning(
                    f"Cannot remove role {existing_role.name} - "
                    f"it's above or equal to bot's highest role."
                )
                continue

            # Guardar nome do cargo antigo
            old_role_name = tier_data["name"]

            # Remover cargo
            try:
                await member.remove_roles(
                    existing_role,
                    reason=f"VOID Store: Substituído por {new_tier['name']}"
                )
                logger.info(f"Removed role {existing_role.name} from {member}")
            except discord.Forbidden:
                logger.error(f"No permission to remove role {existing_role.name}")
            except Exception as e:
                logger.error(f"Error removing role {existing_role.name}: {e}")

        return old_role_name

    async def _notify_user(
        self,
        member: discord.Member,
        old_role: Optional[str],
        new_tier: dict,
        total_spent: float
    ):
        """Notifica o usuário por DM sobre a atualização de cargo"""

        try:
            embed = VoidEmbeds.role_updated(
                member,
                old_role,
                f"{new_tier['emoji']} {new_tier['name']}",
                total_spent
            )
            embed.add_field(
                name="Desconto Conquistado",
                value=f"🏷️ {new_tier['discount']}% OFF em suas próximas compras!",
                inline=False
            )
            await member.send(embed=embed)
        except discord.Forbidden:
            # Usuário com DMs fechadas
            logger.info(f"Could not send DM to {member} (DMs disabled)")
        except Exception as e:
            logger.error(f"Error sending DM to {member}: {e}")

    async def _send_role_log(
        self,
        guild: discord.Guild,
        member: discord.Member,
        old_role: Optional[str],
        new_role: str,
        total_spent: float
    ):
        """Envia log de atualização de cargo no servidor"""

        log_channel_id = config.LOG_CHANNEL_ID
        if not log_channel_id:
            return

        log_channel = guild.get_channel(log_channel_id)
        if not log_channel:
            return

        description = (
            f"**Usuário:** {member.mention}\n"
            f"**Total Gasto:** {format_currency(total_spent)}\n"
        )

        if old_role:
            description += f"**Cargo Anterior:** {old_role}\n"

        description += f"**Novo Cargo:** {new_role}"

        embed = VoidEmbeds.default(
            f"{Emojis.CROWN} Cargo de Progressão Atualizado",
            description
        )

        try:
            await log_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Error sending role log: {e}")

    # ====================================
    # SLASH COMMANDS
    # ====================================

    # Grupo de comandos /cliente
    cliente_group = app_commands.Group(
        name="cliente",
        description="👤 Gerenciamento de clientes da VOID Store"
    )

    @cliente_group.command(
        name="adicionar-gasto",
        description="💰 Adiciona valor ao histórico de gastos do cliente"
    )
    @app_commands.describe(
        membro="O cliente",
        valor="Valor a adicionar (ex: 50.00)",
        motivo="Motivo do ajuste"
    )
    async def add_spent(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        valor: float,
        motivo: Optional[str] = "Ajuste manual"
    ):
        """Adiciona gasto manualmente a um cliente"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        if valor <= 0:
            await interaction.response.send_message(
                f"{Emojis.ERROR} O valor deve ser maior que zero.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        # Criar usuário se não existir
        user = await self.db.get_user(membro.id)
        if not user:
            await self.db.create_user(membro.id, str(membro))

        # Atualizar gasto
        success = await self.db.update_user_spent(membro.id, valor)

        if not success:
            await interaction.followup.send(
                f"{Emojis.ERROR} Erro ao atualizar gasto.",
                ephemeral=True
            )
            return

        # Buscar dados atualizados
        updated_user = await self.db.get_user(membro.id)

        # Verificar novo tier
        new_tier = await self.check_user_tier(membro)

        # Construir resposta
        embed = VoidEmbeds.success(
            "Gasto Adicionado",
            f"**Cliente:** {membro.mention}\n"
            f"**Valor Adicionado:** {format_currency(valor)}\n"
            f"**Total Acumulado:** {format_currency(updated_user.total_spent)}\n"
            f"**Motivo:** {motivo}"
        )

        if new_tier:
            embed.add_field(
                name=f"{Emojis.CROWN} Novo Cargo",
                value=f"Cliente atingiu o nível **{new_tier}**!",
                inline=False
            )

        await interaction.followup.send(embed=embed)

        # Log no banco
        await self.db.create_log(
            "purchase",
            interaction.user.id,
            "manual_add",
            f"Client: {membro.id} | Amount: {valor} | Reason: {motivo}"
        )

        logger.info(f"Manual spend added: {membro} + {valor} by {interaction.user}")

    @cliente_group.command(
        name="consultar",
        description="🔍 Consulta o perfil completo de um cliente"
    )
    @app_commands.describe(membro="O cliente a consultar")
    async def check_client(
        self,
        interaction: discord.Interaction,
        membro: discord.Member
    ):
        """Exibe o perfil de compras do cliente"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        await interaction.response.defer(ephemeral=True)

        user = await self.db.get_user(membro.id)

        if not user:
            await interaction.followup.send(
                f"{Emojis.ERROR} Este cliente não possui histórico de compras.",
                ephemeral=True
            )
            return

        # Descobrir tier atual
        tiers = config.get_role_tiers()
        current_tier = None
        next_tier = None

        ordered_tiers = [
            ("PRESTIGE", tiers["PRESTIGE"]),
            ("SUPREME", tiers["SUPREME"]),
            ("PREMIUM", tiers["PREMIUM"]),
            ("PLUS", tiers["PLUS"]),
            ("STARTER", tiers["STARTER"]),
        ]

        for i, (tier_key, tier_data) in enumerate(ordered_tiers):
            if user.total_spent >= tier_data["threshold"]:
                current_tier = tier_data
                # Próximo tier é o anterior na lista (maior valor)
                if i > 0:
                    next_tier = None  # Já tem o máximo abaixo dele verificado
                break
            else:
                next_tier = tier_data

        # Calcular quanto falta para o próximo tier
        missing = None
        if next_tier:
            missing = next_tier["threshold"] - user.total_spent

        # Buscar pedidos do cliente
        orders = await self.db.get_orders_by_client(membro.id)
        completed_orders = [o for o in orders if o.status == "completed"]

        # Montar embed
        embed = VoidEmbeds.default(
            f"Perfil do Cliente — {membro.name}",
            f"Informações completas de {membro.mention}"
        )

        embed.set_thumbnail(url=membro.display_avatar.url)

        embed.add_field(
            name="Total Gasto",
            value=format_currency(user.total_spent),
            inline=True
        )

        embed.add_field(
            name="Pedidos Concluídos",
            value=str(len(completed_orders)),
            inline=True
        )

        embed.add_field(
            name="Membro Desde",
            value=membro.joined_at.strftime("%d/%m/%Y") if membro.joined_at else "N/A",
            inline=True
        )

        if current_tier:
            embed.add_field(
                name="Cargo Atual",
                value=f"{current_tier['emoji']} {current_tier['name']} ({current_tier['discount']}% OFF)",
                inline=True
            )
        else:
            embed.add_field(
                name="Cargo Atual",
                value="Sem cargo de progressão",
                inline=True
            )

        if next_tier and missing:
            embed.add_field(
                name="Próximo Nível",
                value=f"{next_tier['emoji']} {next_tier['name']} (falta {format_currency(missing)})",
                inline=True
            )
        elif current_tier and current_tier["name"] == "Prestige":
            embed.add_field(
                name="Próximo Nível",
                value="🏆 Nível máximo atingido!",
                inline=True
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @cliente_group.command(
        name="resetar-gasto",
        description="🔄 Reseta o total gasto de um cliente para zero"
    )
    @app_commands.describe(
        membro="O cliente",
        motivo="Motivo do reset"
    )
    async def reset_spent(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        motivo: Optional[str] = "Reset administrativo"
    ):
        """Reseta os gastos de um cliente — apenas admins"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_admin=True):
            return

        await interaction.response.defer()

        success = await self.db.reset_user_spent(membro.id)

        if success:
            embed = VoidEmbeds.success(
                "Gasto Resetado",
                f"**Cliente:** {membro.mention}\n"
                f"**Ação:** Total gasto resetado para **R$ 0,00**\n"
                f"**Motivo:** {motivo}\n"
                f"**Executado por:** {interaction.user.mention}"
            )
            await interaction.followup.send(embed=embed)

            await self.db.create_log(
                "purchase",
                interaction.user.id,
                "reset",
                f"Client: {membro.id} | Reason: {motivo}"
            )

            logger.info(f"Spent reset for {membro} by {interaction.user}")
        else:
            await interaction.followup.send(
                f"{Emojis.ERROR} Erro ao resetar gasto.",
                ephemeral=True
            )

    @cliente_group.command(
        name="remover-gasto",
        description="➖ Remove um valor específico do histórico de gastos"
    )
    @app_commands.describe(
        membro="O cliente",
        valor="Valor a remover (ex: 20.00)",
        motivo="Motivo da remoção"
    )
    async def remove_spent(
        self,
        interaction: discord.Interaction,
        membro: discord.Member,
        valor: float,
        motivo: Optional[str] = "Ajuste administrativo"
    ):
        """Remove valor dos gastos de um cliente"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_admin=True):
            return

        if valor <= 0:
            await interaction.response.send_message(
                f"{Emojis.ERROR} O valor deve ser maior que zero.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        # Verificar se tem saldo suficiente
        user = await self.db.get_user(membro.id)
        if not user:
            await interaction.followup.send(
                f"{Emojis.ERROR} Cliente não encontrado.",
                ephemeral=True
            )
            return

        if user.total_spent < valor:
            await interaction.followup.send(
                f"{Emojis.ERROR} O cliente tem apenas {format_currency(user.total_spent)} registrado. "
                f"Não é possível remover {format_currency(valor)}.",
                ephemeral=True
            )
            return

        # Usar valor negativo para subtração
        success = await self.db.update_user_spent(membro.id, -valor)

        if success:
            updated_user = await self.db.get_user(membro.id)

            embed = VoidEmbeds.success(
                "Gasto Removido",
                f"**Cliente:** {membro.mention}\n"
                f"**Valor Removido:** {format_currency(valor)}\n"
                f"**Novo Total:** {format_currency(updated_user.total_spent)}\n"
                f"**Motivo:** {motivo}"
            )
            await interaction.followup.send(embed=embed)

            await self.db.create_log(
                "purchase",
                interaction.user.id,
                "removed",
                f"Client: {membro.id} | Amount: -{valor} | Reason: {motivo}"
            )

            logger.info(f"Spend removed: {membro} - {valor} by {interaction.user}")
        else:
            await interaction.followup.send(
                f"{Emojis.ERROR} Erro ao remover gasto.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Roles(bot))
