"""
🌑 VOID Store Bot - Sistema de Permissões Blindado
"""
import discord
from discord import Interaction, Member

class PermissionChecker:
    CARGOS_ADM = [1550096907739857079, 1550097139093209139]

    @staticmethod
    def is_authorized(member: Member) -> bool:
        """Verifica se é Admin ou possui os cargos autorizados."""
        if getattr(member, "guild_permissions", None) and member.guild_permissions.administrator:
            return True
        if hasattr(member, "roles"):
            return any(role.id in PermissionChecker.CARGOS_ADM for role in member.roles)
        return False

    @classmethod
    def has_authorized_role(cls, member: Member) -> bool:
        """Alias para verificações do evento on_message."""
        return cls.is_authorized(member)

    @staticmethod
    async def check_interaction_permissions(interaction: Interaction) -> bool:
        """Notifica e bloqueia comandos interativos não autorizados."""
        if PermissionChecker.is_authorized(interaction.user):
            return True
        
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ **Acesso Negado.** Somente a gerência da VOID Store pode usar este comando.",
                ephemeral=True
            )
        else:
            await interaction.followup.send(
                "❌ **Acesso Negado.** Somente a gerência da VOID Store pode usar este comando.",
                ephemeral=True
            )
        return False

    @classmethod
    async def check(cls, interaction: Interaction) -> bool:
        return await cls.check_interaction_permissions(interaction)

    @classmethod
    async def check_permissions(cls, interaction: Interaction) -> bool:
        return await cls.check_interaction_permissions(interaction)
