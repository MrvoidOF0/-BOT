"""
🌑 VOID Store Bot - Sistema de Relatórios e Resumos
"""
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime

REPORTS_CHANNEL_ID = 1549934937002614935  # Atualize para o ID do canal #relatórios, se necessário


class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="gerar-relatorio",
        description="Gera um relatório instantâneo de status do servidor e atendimento"
    )
    @commands.has_permissions(administrator=True)
    async def gerar_relatorio(self, interaction: discord.Interaction):
        guild = interaction.guild

        total_members = guild.member_count
        categories = guild.categories
        
        # Encontra a categoria PEDIDOS para contar carrinhos abertos
        pedidos_cat = discord.utils.find(
            lambda c: "PEDIDOS" in c.name.upper(),
            categories
        )
        carrinhos_abertos = len(pedidos_cat.text_channels) if pedidos_cat else 0

        embed = discord.Embed(
            title="📊 RELATÓRIO DE STATUS — VOID STORE",
            description=f"Gerado em: `{datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}`",
            color=discord.Color.from_rgb(15, 15, 15)
        )
        
        embed.add_field(name="👥 Membros Totais:", value=f"`{total_members}`", inline=True)
        embed.add_field(name="🛒 Carrinhos Ativos:", value=f"`{carrinhos_abertos}`", inline=True)
        embed.add_field(name="🤖 Latência do Bot:", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.set_footer(text="🌑 VOID Store • Relatórios Automáticos de Gerência")

        await interaction.response.send_message(embed=embed)

    @staticmethod
    async def log_fechamento_ticket(
        guild: discord.Guild,
        cliente: discord.User,
        atendente: discord.User,
        servico: str
    ):
        """Método auxiliar para registar no canal de relatórios sempre que um ticket for concluído."""
        log_channel = discord.utils.get(guild.text_channels, name="relatórios")
        if not log_channel:
            log_channel = guild.get_channel(REPORTS_CHANNEL_ID)

        if log_channel:
            embed = discord.Embed(
                title="📈 NOVO ATENDIMENTO CONCLUÍDO",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 Cliente:", value=f"{cliente.mention}", inline=True)
            embed.add_field(name="🛡️ Atendido por:", value=f"{atendente.mention}", inline=True)
            embed.add_field(name="📦 Serviço:", value=f"`{servico}`", inline=True)
            embed.set_footer(text=f"VOID Store • {datetime.now().strftime('%d/%m/%Y %H:%M')}")

            await log_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Reports(bot))
