"""
🌑 VOID Store Bot - Sistema de Logs de Eventos do Servidor
"""

import discord
from discord.ext import commands
from datetime import datetime

from utils.embeds import VoidEmbeds
from utils.constants import Emojis, Colors
from utils.logger import logger
from config import config


class Logs(commands.Cog):
    """Registra eventos do servidor em canais de log dedicados"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    # ====================================
    # HELPER
    # ====================================

    async def _send_log(
        self,
        guild: discord.Guild,
        embed: discord.Embed,
        channel_id: int = None
    ):
        """
        Envia um embed para o canal de log.
        Usa o canal específico se fornecido, senão usa o canal geral.
        """
        target_id = channel_id or config.LOG_CHANNEL_ID
        if not target_id:
            return

        channel = guild.get_channel(target_id)
        if not channel:
            return

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"No permission to send log in channel {target_id}")
        except Exception as e:
            logger.error(f"Error sending log: {e}")

    # ====================================
    # EVENTOS DE MEMBROS
    # ====================================

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Log quando um membro entra no servidor"""

        embed = VoidEmbeds.default(
            f"👋 Membro Entrou",
            f"**Usuário:** {member.mention} (`{member.id}`)\n"
            f"**Conta Criada Em:** {member.created_at.strftime('%d/%m/%Y')}\n"
            f"**Total de Membros:** {member.guild.member_count}"
        )

        await self._send_log(member.guild, embed)
        await self.db.create_log("member", member.id, "join", f"Guild: {member.guild.id}")
        logger.info(f"Member joined: {member} | Guild: {member.guild.name}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Log quando um membro sai do servidor"""

        roles_str = ", ".join(r.name for r in member.roles[1:]) or "Nenhum"

        embed = VoidEmbeds.warning(
            f"🚪 Membro Saiu",
            f"**Usuário:** {member.mention} (`{member.id}`)\n"
            f"**Cargos que possuía:** {roles_str}\n"
            f"**Total de Membros:** {member.guild.member_count}"
        )

        await self._send_log(member.guild, embed)
        await self.db.create_log("member", member.id, "leave", f"Guild: {member.guild.id}")
        logger.info(f"Member left: {member} | Guild: {member.guild.name}")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Log quando cargos de um membro são alterados"""

        if before.roles == after.roles:
            return

        added = [r for r in after.roles if r not in before.roles]
        removed = [r for r in before.roles if r not in after.roles]

        if not added and not removed:
            return

        description = f"**Usuário:** {after.mention} (`{after.id}`)\n"

        if added:
            description += f"**Cargos Adicionados:** {', '.join(r.mention for r in added)}\n"
        if removed:
            description += f"**Cargos Removidos:** {', '.join(r.mention for r in removed)}"

        embed = VoidEmbeds.default("🔄 Cargos Alterados", description)
        await self._send_log(after.guild, embed)

    # ====================================
    # EVENTOS DE MENSAGENS
    # ====================================

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Log quando uma mensagem é deletada"""

        if message.author.bot:
            return
        if not message.guild:
            return

        content = message.content or "*Nenhum conteúdo de texto*"
        if len(content) > 1000:
            content = content[:1000] + "..."

        embed = VoidEmbeds.default(
            "🗑️ Mensagem Deletada",
            f"**Autor:** {message.author.mention} (`{message.author.id}`)\n"
            f"**Canal:** {message.channel.mention}\n"
            f"**Conteúdo:**\n```{content}```"
        )

        await self._send_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Log quando uma mensagem é editada"""

        if before.author.bot:
            return
        if not before.guild:
            return
        if before.content == after.content:
            return

        before_content = before.content or "*Vazio*"
        after_content = after.content or "*Vazio*"

        if len(before_content) > 500:
            before_content = before_content[:500] + "..."
        if len(after_content) > 500:
            after_content = after_content[:500] + "..."

        embed = VoidEmbeds.default(
            "✏️ Mensagem Editada",
            f"**Autor:** {before.author.mention}\n"
            f"**Canal:** {before.channel.mention}\n"
            f"**Antes:** ```{before_content}```\n"
            f"**Depois:** ```{after_content}```"
        )

        await self._send_log(before.guild, embed)

    # ====================================
    # EVENTOS DE CANAIS
    # ====================================

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        """Log quando um canal é criado"""

        embed = VoidEmbeds.success(
            "📁 Canal Criado",
            f"**Nome:** {channel.mention}\n"
            f"**Tipo:** {str(channel.type).replace('_', ' ').title()}\n"
            f"**ID:** `{channel.id}`"
        )

        await self._send_log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """Log quando um canal é deletado"""

        embed = VoidEmbeds.warning(
            "🗑️ Canal Deletado",
            f"**Nome:** #{channel.name}\n"
            f"**Tipo:** {str(channel.type).replace('_', ' ').title()}\n"
            f"**ID:** `{channel.id}`"
        )

        await self._send_log(channel.guild, embed)

    # ====================================
    # EVENTOS DE VOICE
    # ====================================

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        """Log de movimentações em canais de voz"""

        if before.channel == after.channel:
            return

        if before.channel is None and after.channel is not None:
            action = f"Entrou em **{after.channel.name}**"
        elif before.channel is not None and after.channel is None:
            action = f"Saiu de **{before.channel.name}**"
        else:
            action = f"Moveu de **{before.channel.name}** → **{after.channel.name}**"

        embed = VoidEmbeds.default(
            "🔊 Movimentação de Voz",
            f"**Usuário:** {member.mention}\n"
            f"**Ação:** {action}"
        )

        await self._send_log(member.guild, embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Logs(bot))
