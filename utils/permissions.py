"""
🌑 VOID Store Bot - Verificação de Permissões
"""

import discord
from discord import Member, Interaction
from typing import Optional, Union
from config import config

class PermissionChecker:
    """Classe para verificar permissões de usuários"""
    
    @staticmethod
    def is_admin(member: Member) -> bool:
        """
        Verifica se o membro é administrador
        
        Args:
            member: Membro a verificar
            
        Returns:
            True se for administrador
        """
        # Verificar permissão de administrador
        if member.guild_permissions.administrator:
            return True
        
        # Verificar cargo de admin configurado
        if config.ADMIN_ROLE_ID and member.get_role(config.ADMIN_ROLE_ID):
            return True
        
        return False
    
    @staticmethod
    def is_staff(member: Member) -> bool:
        """
        Verifica se o membro é staff
        
        Args:
            member: Membro a verificar
            
        Returns:
            True se for staff
        """
        # Admin é staff
        if PermissionChecker.is_admin(member):
            return True
        
        # Verificar cargo de staff configurado
        if config.STAFF_ROLE_ID and member.get_role(config.STAFF_ROLE_ID):
            return True
        
        return False
    
    @staticmethod
    def is_vip(member: Member) -> bool:
        """
        Verifica se o membro é VIP
        
        Args:
            member: Membro a verificar
            
        Returns:
            True se for VIP
        """
        if config.VIP_ROLE_ID and member.get_role(config.VIP_ROLE_ID):
            return True
        return False
    
    @staticmethod
    def is_booster(member: Member) -> bool:
        """
        Verifica se o membro é Booster
        
        Args:
            member: Membro a verificar
            
        Returns:
            True se for Booster
        """
        # Verificar cargo premium_subscriber (boost padrão do Discord)
        if member.premium_since is not None:
            return True
        
        # Verificar cargo de booster configurado
        if config.BOOSTER_ROLE_ID and member.get_role(config.BOOSTER_ROLE_ID):
            return True
        
        return False
    
    @staticmethod
    def can_moderate(member: Member) -> bool:
        """
        Verifica se o membro pode moderar
        
        Args:
            member: Membro a verificar
            
        Returns:
            True se puder moderar
        """
        return (
            member.guild_permissions.kick_members or
            member.guild_permissions.ban_members or
            PermissionChecker.is_staff(member)
        )
    
    @staticmethod
    async def check_interaction_permissions(
        interaction: Interaction,
        require_staff: bool = False,
        require_admin: bool = False,
        require_mod: bool = False
    ) -> bool:
        """
        Verifica permissões em uma interação
        
        Args:
            interaction: Interação do Discord
            require_staff: Requer cargo de staff
            require_admin: Requer cargo de admin
            require_mod: Requer permissões de moderação
            
        Returns:
            True se tiver permissão
        """
        member = interaction.user
        
        if require_admin:
            if not PermissionChecker.is_admin(member):
                await interaction.response.send_message(
                    "❌ Você não tem permissão para usar este comando. (Requer: Administrador)",
                    ephemeral=True
                )
                return False
        
        elif require_staff:
            if not PermissionChecker.is_staff(member):
                await interaction.response.send_message(
                    "❌ Você não tem permissão para usar este comando. (Requer: Staff)",
                    ephemeral=True
                )
                return False
        
        elif require_mod:
            if not PermissionChecker.can_moderate(member):
                await interaction.response.send_message(
                    "❌ Você não tem permissão para usar este comando. (Requer: Moderador)",
                    ephemeral=True
                )
                return False
        
        return True
    
    @staticmethod
    def get_highest_role_tier(member: Member) -> Optional[str]:
        """
        Retorna o tier mais alto do membro
        
        Args:
            member: Membro a verificar
            
        Returns:
            Nome do tier ou None
        """
        tiers = config.get_role_tiers()
        
        # Verificar do maior para o menor
        for tier_name in ['PRESTIGE', 'SUPREME', 'PREMIUM', 'PLUS', 'STARTER']:
            tier = tiers[tier_name]
            if tier['role_id'] and member.get_role(tier['role_id']):
                return tier_name
        
        return None
