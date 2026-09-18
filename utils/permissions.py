"""
🌑 VOID Store Bot - Verificação de Permissões
"""

import discord
from discord import Interaction, Member
from typing import Optional
from config import config


class PermissionChecker:
    """Verificação de permissões do bot"""

    # ====================================
    # VERIFICAÇÃO DE CARGOS AUTORIZADOS
    # ====================================

    @staticmethod
    def has_authorized_role(member: Member) -> bool:
        """
        Verifica se o membro possui um dos cargos autorizados
        a usar os comandos do bot.
        
        Cargos autorizados:
        1550096907739857079
        1550097139093209139
        1550097169170563203
        """
        # Admins sempre passam
        if member.guild_permissions.administrator:
            return True
        
        # Verificar cargos autorizados
        member_role_ids = [role.id for role in member.roles]
        for role_id in config.AUTHORIZED_ROLE_IDS:
            if role_id in member_role_ids:
                return True
        
        return False

    @staticmethod
    def is_admin(member: Member) -> bool:
        if member.guild_permissions.administrator:
            return True
        if config.ADMIN_ROLE_ID and member.get_role(config.ADMIN_ROLE_ID):
            return True
        return False

    @staticmethod
    def is_staff(member: Member) -> bool:
        if PermissionChecker.is_admin(member):
            return True
        if config.STAFF_ROLE_ID and member.get_role(config.STAFF_ROLE_ID):
            return True
        # Verificar cargos autorizados
        if PermissionChecker.has_authorized_role(member):
            return True
        return False

    @staticmethod
    def is_vip(member: Member) -> bool:
        if config.VIP_ROLE_ID and member.get_role(config.VIP_ROLE_ID):
            return True
        return False

    @staticmethod
    def is_booster(member: Member) -> bool:
        if member.premium_since is not None:
            return True
        if config.BOOSTER_ROLE_ID and member.get_role(config.BOOSTER_ROLE_ID):
            return True
        return False

    @staticmethod
    async def check_interaction_permissions(
        interaction: Interaction,
        require_staff: bool = False,
        require_admin: bool = False,
        require_mod: bool = False,
        require_authorized: bool = False
    ) -> bool:
        """
        Verificação central de permissões para interações.
        Sempre verifica se o usuário tem cargo autorizado.
        """
        member = interaction.user

        # Verificação base: cargo autorizado (para todos os comandos)
        if require_authorized or require_staff or require_admin or require_mod:
            if not PermissionChecker.has_authorized_role(member):
                await interaction.response.send_message(
                    "❌ Você não tem permissão para usar este comando.",
                    ephemeral=True
                )
                return False

        if require_admin:
            if not PermissionChecker.is_admin(member):
                await interaction.response.send_message(
                    "❌ Este comando requer cargo de **Administrador**.",
                    ephemeral=True
                )
                return False

        elif require_staff:
            if not PermissionChecker.is_staff(member):
                await interaction.response.send_message(
                    "❌ Este comando requer cargo de **Staff**.",
                    ephemeral=True
                )
                return False

        elif require_mod:
            if not (member.guild_permissions.kick_members or PermissionChecker.is_staff(member)):
                await interaction.response.send_message(
                    "❌ Este comando requer permissões de **Moderador**.",
                    ephemeral=True
                )
                return False

        return True
