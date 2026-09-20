"""
🌑 VOID Store Bot - Sistema Modular de Transcripts e Ticket Logs
"""
import io
import discord
from discord.ext import commands

# ID do canal onde os transcripts serão gravados (preencha ou o bot buscará pelo nome 'ticket-logs')
TICKET_LOGS_CHANNEL_ID = 1550272633663398019


class TicketLogger:
    @staticmethod
    async def generate_and_send_transcript(
        guild: discord.Guild,
        channel: discord.TextChannel,
        closed_by: discord.User,
        opener_user: discord.User = None,
        service_name: str = "Atendimento Geral"
    ):
        """Coleta o histórico do canal, gera o arquivo .txt e envia para o canal #ticket-logs."""
        
        # 1. Coleta do histórico de mensagens
        messages = []
        async for msg in channel.history(limit=1000, oldest_first=True):
            time_str = msg.created_at.strftime("%d/%m/%Y %H:%M:%S")
            content = msg.content if msg.content else "[Sem Texto / Anexo ou Embed]"
            attachments = f" | Anexos: {[a.url for a in msg.attachments]}" if msg.attachments else ""
            messages.append(f"[{time_str}] {msg.author.name} ({msg.author.id}): {content}{attachments}")

        if not messages:
            messages.append("Nenhuma mensagem foi enviada neste ticket.")

        transcript_text = f"=== TRANSCRIPT VOID STORE — CANAL: #{channel.name} ===\n\n" + "\n".join(messages)
        
        transcript_file = discord.File(
            fp=io.BytesIO(transcript_text.encode("utf-8")),
            filename=f"transcript-{channel.name}.txt"
        )

        # 2. Busca o canal de logs pelo nome 'ticket-logs' ou pelo ID configurado
        log_channel = discord.utils.get(guild.text_channels, name="ticket-logs")
        if not log_channel:
            log_channel = guild.get_channel(TICKET_LOGS_CHANNEL_ID)

        # 3. Envio do registro
        if log_channel:
            embed_log = discord.Embed(
                title="📄 TRANSCRIPT DE ATENDIMENTO",
                color=discord.Color.from_rgb(15, 15, 15)
            )
            embed_log.add_field(
                name="👤 Cliente:",
                value=f"{opener_user.mention} (`{opener_user.id}`)" if opener_user else "Não identificado",
                inline=True
            )
            embed_log.add_field(
                name="🛡️ Encerrado por:",
                value=f"{closed_by.mention} (`{closed_by.id}`)",
                inline=True
            )
            embed_log.add_field(
                name="📦 Serviço/Assunto:",
                value=f"`{service_name}`",
                inline=True
            )
            embed_log.add_field(
                name="💬 Canal Encerrado:",
                value=f"`#{channel.name}`",
                inline=False
            )
            embed_log.set_footer(text="🌑 VOID Store • Sistema de Ticket Logs")

            await log_channel.send(embed=embed_log, file=transcript_file)


class TicketLogsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """Backup passivo caso um canal de ticket seja apagado manualmente sem usar o botão."""
        if isinstance(channel, discord.TextChannel) and ("carrinho" in channel.name or "suporte" in channel.name):
            log_channel = discord.utils.get(channel.guild.text_channels, name="ticket-logs")
            if log_channel:
                embed = discord.Embed(
                    title="⚠️ CANAL REMOVIDO MANUALMENTE",
                    description=f"O canal `{channel.name}` foi apagado da categoria sem o processo padrão de fechar ticket.",
                    color=discord.Color.red()
                )
                await log_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(TicketLogsCog(bot))
