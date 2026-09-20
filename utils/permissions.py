import discord
from discord import Interaction, Member

class PermissionChecker:
    # IDs MESTRES DA VOID STORE
    CARGOS_ADM = [1550096907739857079, 1550097139093209139]

    @staticmethod
    def is_authorized(member: Member) -> bool:
        """Verifica se o membro é dono ou tem o cargo autorizado"""
        if member.guild_permissions.administrator:
            return True
        return any(role.id in PermissionChecker.CARGOS_ADM for role in member.roles)

    @staticmethod
    async def check_interaction_permissions(interaction: Interaction) -> bool:
        """Bloqueia na hora se não for autorizado"""
        if not PermissionChecker.is_authorized(interaction.user):
            await interaction.response.send_message(
                "❌ **Acesso Negado.** Você não tem permissão para usar este bot.",
                ephemeral=True
            )
            return False
        return True
