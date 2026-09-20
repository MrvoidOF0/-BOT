"""
🌑 VOID Store Bot - Sistema de Permissões
"""

import discord
from discord import Interaction, Member

class PermissionChecker:
    # IDs DOS CARGOS QUE PODEM USAR O BOT (Além de Administradores)
    CARGOS_MESTRES = [1550096907739857079, 1550097139093209139]

    @staticmethod
    def is_authorized(member: Member) -> bool:
        """Verifica se o membro é ADMIN ou tem um dos cargos da lista"""
        # Se for Administrador do servidor, sempre retorna VERDADEIRO
        if member.guild_permissions.administrator:
            return True
            
        # Verifica se tem um dos cargos específicos
        for role in member.roles:
            if role.id in PermissionChecker.CARGOS_MESTRES:
                return True
        return False

    @staticmethod
    async def check_interaction_permissions(interaction: Interaction) -> bool:
        """Verifica a permissão e avisa se for negado"""
        if PermissionChecker.is_authorized(interaction.user):
            return True
        
        # Se não for autorizado, o bot avisa e cancela o comando
        await interaction.response.send_message(
            "❌ **Acesso Negado.** Você não tem permissão para usar os comandos da VOID Store.",
            ephemeral=True
        )
        return False
