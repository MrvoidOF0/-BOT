"""
🌑 VOID Store Bot - Sistema de Boas-Vindas
Envia embed personalizado para cada novo membro que entra no servidor.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

from utils.permissions import PermissionChecker
from utils.logger import logger
from config import config


# ====================================
# CONFIGURAÇÃO
# ====================================

# Cole aqui o ID do canal onde as boas-vindas serão enviadas
# Você também pode configurar via /welcome-configurar
CANAL_BOAS_VINDAS_ID: Optional[int] = None  # Ex: 1234567890123456789


# ====================================
# COG
# ====================================

class Welcome(commands.Cog):
    """Sistema de boas-vindas automático"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    # ====================================
    # LISTENER PRINCIPAL
    # ====================================

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Disparado automaticamente sempre que um novo membro
        entra no servidor.
        """

        # Buscar canal configurado
        channel_id = await self._get_welcome_channel()

        if not channel_id:
            logger.warning(
                f"Welcome channel not configured. "
                f"New member: {member} | Use /welcome-configurar to set it up."
            )
            return

        channel = member.guild.get_channel(channel_id)

        if not channel:
            logger.warning(f"Welcome channel {channel_id} not found in guild.")
            return

        # Criar embed de boas-vindas
        embed = self._criar_embed(member)

        try:
            await channel.send(
                content=member.mention,
                embed=embed
            )

            logger.info(f"Welcome message sent for {member} in {channel.name}")

            # Registrar no banco
            await self.db.create_log(
                "welcome",
                member.id,
                "sent",
                f"Channel: {channel_id} | Guild: {member.guild.id}"
            )

        except discord.Forbidden:
            logger.error(
                f"No permission to send welcome message in channel {channel_id}"
            )
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")

    # ====================================
    # CRIAR EMBED
    # ====================================

    def _criar_embed(self, member: discord.Member) -> discord.Embed:
        """
        Cria o embed de boas-vindas com a foto de perfil
        e a mensagem personalizada da VOID Store.
        """

        embed = discord.Embed(
            description=(
                f"👋 Bem-vindo(a) à **𝐕𝐎𝐈𝐃 𝐒𝐭𝐨𝐫𝐞**!\n\n"
                f"🛒 Tudo para deixar sua experiência no **Blox Fruits** mais fácil, rápida e segura.\n\n"
                f"📦 Confira nossos serviços, estoque, preços e promoções e, quando quiser, faça seu pedido!\n\n"
                f"🔔 Fique de olho nas novidades e aproveite sua estadia por aqui. 🖤\n\n"
                f"**boas compras! ⚡**"
            ),
            color=0x000000,
            timestamp=discord.utils.utcnow()
        )

        # Nome do membro como título
        embed.set_author(
            name=f"{member.display_name} entrou na VOID Store!",
            icon_url=member.display_avatar.url
        )

        # Foto de perfil grande (thumbnail)
        embed.set_thumbnail(url=member.display_avatar.url)

        # Foto de perfil como imagem principal (opcional — escolha um ou outro)
        # embed.set_image(url=member.display_avatar.url)

        # Informações do membro
        embed.add_field(
            name="👤 Membro",
            value=member.mention,
            inline=True
        )

        embed.add_field(
            name="📅 Conta criada em",
            value=member.created_at.strftime("%d/%m/%Y"),
            inline=True
        )

        embed.add_field(
            name="👥 Membro nº",
            value=f"`#{member.guild.member_count}`",
            inline=True
        )

        embed.set_footer(
            text="🌑 VOID Store | Boas-vindas!",
            icon_url=member.guild.icon.url if member.guild.icon else None
        )

        return embed

    # ====================================
    # HELPERS
    # ====================================

    async def _get_welcome_channel(self) -> Optional[int]:
        """
        Busca o ID do canal de boas-vindas.
        Prioridade: banco de dados → constante local → config
        """

        # 1. Tentar banco de dados (configurado via /welcome-configurar)
        db_value = await self.db.get_config("welcome_channel_id")
        if db_value:
            try:
                return int(db_value)
            except ValueError:
                pass

        # 2. Constante local deste arquivo
        if CANAL_BOAS_VINDAS_ID:
            return CANAL_BOAS_VINDAS_ID

        # 3. LOG_CHANNEL_ID como fallback
        if config.LOG_CHANNEL_ID:
            return config.LOG_CHANNEL_ID

        return None

    # ====================================
    # COMANDOS
    # ====================================

    @app_commands.command(
        name="welcome-configurar",
        description="👋 Configura o canal de boas-vindas"
    )
    @app_commands.describe(
        canal="Canal onde as boas-vindas serão enviadas"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def welcome_configurar(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel
    ):
        """Define o canal de boas-vindas via comando"""

        if not await PermissionChecker.check_interaction_permissions(
            interaction, require_admin=True
        ):
            return

        await self.db.set_config("welcome_channel_id", str(canal.id))

        embed = discord.Embed(
            title="✅ Canal de Boas-Vindas Configurado",
            description=(
                f"Novos membros receberão a mensagem de boas-vindas em:\n"
                f"{canal.mention}"
            ),
            color=0x00ff00
        )
        embed.set_footer(text="🌑 VOID Store")

        await interaction.response.send_message(embed=embed, ephemeral=True)

        logger.info(f"Welcome channel set to {canal.id} by {interaction.user}")

    @app_commands.command(
        name="welcome-testar",
        description="👋 Testa a mensagem de boas-vindas"
    )
    @app_commands.describe(
        membro="Membro para simular a entrada (padrão: você mesmo)"
    )
    async def welcome_testar(
        self,
        interaction: discord.Interaction,
        membro: Optional[discord.Member] = None
    ):
        """Envia uma mensagem de boas-vindas de teste"""

        if not await PermissionChecker.check_interaction_permissions(
            interaction, require_staff=True
        ):
            return

        target = membro or interaction.user

        embed = self._criar_embed(target)

        await interaction.response.send_message(
            content=f"👋 **Prévia da mensagem de boas-vindas para** {target.mention}:",
            embed=embed,
            ephemeral=True
        )

    @app_commands.command(
        name="welcome-info",
        description="👋 Mostra o canal de boas-vindas configurado"
    )
    async def welcome_info(self, interaction: discord.Interaction):
        """Mostra onde as boas-vindas estão sendo enviadas"""

        if not await PermissionChecker.check_interaction_permissions(
            interaction, require_staff=True
        ):
            return

        channel_id = await self._get_welcome_channel()

        if not channel_id:
            await interaction.response.send_message(
                "⚠️ Canal de boas-vindas não configurado.\n"
                "Use `/welcome-configurar canal:#seu-canal` para definir.",
                ephemeral=True
            )
            return

        channel = interaction.guild.get_channel(channel_id)
        channel_mention = channel.mention if channel else f"ID: `{channel_id}` (canal não encontrado)"

        embed = discord.Embed(
            title="👋 Configuração de Boas-Vindas",
            description=f"**Canal atual:** {channel_mention}",
            color=0x000000
        )
        embed.set_footer(text="🌑 VOID Store")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
