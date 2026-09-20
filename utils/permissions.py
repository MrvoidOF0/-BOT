"""
🌑 VOID Store Bot - Sistema de Permissões Blindado
"""

import discord
from discord import Interaction, Member
from config import config

class PermissionChecker:
    # IDs DOS CARGOS QUE PODEM TUDO NO BOT
    CARGOS_AUTORIZADOS = [1550096907739857079, 1550097139093209139]

    @staticmethod
    def is_authorized(member: Member) -> bool:
        """Verifica se o membro tem um dos cargos mestres"""
        if member.guild_permissions.administrator:
            return True
            
        for role in member.roles:
            if role.id in PermissionChecker.CARGOS_AUTORIZADOS:
                return True
        return False

    @staticmethod
    async def check_interaction_permissions(interaction: Interaction, require_authorized: bool = True) -> bool:
        """Bloqueia a interação se não for um cargo autorizado"""
        if not PermissionChecker.is_authorized(interaction.user):
            await interaction.response.send_message(
                "❌ **Acesso Negado.** Somente a gerência da VOID Store pode usar este comando.",
                ephemeral=True
            )
            return False
        return True

    @staticmethod
    def is_staff(member: Member) -> bool:
        """Verificação simples para uso interno nos tickets"""
        return PermissionChecker.is_authorized(member)
