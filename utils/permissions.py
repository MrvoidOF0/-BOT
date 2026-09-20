"""
🌑 VOID Store Bot - Permissões Auxiliares
"""
import discord
from discord import Interaction, Member

class PermissionChecker:
    CARGOS_ADM = [1550096907739857079, 1550097139093209139]

    @staticmethod
    def is_authorized(member: Member) -> bool:
        if getattr(member, "guild_permissions", None) and member.guild_permissions.administrator:
            return True
        if hasattr(member, "roles"):
            return any(role.id in PermissionChecker.CARGOS_ADM for role in member.roles)
        return False

    @classmethod
    def has_authorized_role(cls, member: Member) -> bool:
        return cls.is_authorized(member)
