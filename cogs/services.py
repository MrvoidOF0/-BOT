"""
🌑 VOID Store Bot - Cog de Atendimento e Gerenciamento de Serviços/Tickets
Inclui fechamento automático e exclusão do canal de atendimento.
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils.logger import setup_logger

logger = setup_logger("Services")


# ====================================
# VIEW DO CANAL DE ATENDIMENTO
# ====================================

class TicketControlView(discord.ui.View):
    """View contendo os botões dentro do canal do cliente (Encerrar e Gerar PIX)"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Encerrar Canal",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="ticket:close"
    )
    async def btn_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        # Alerta do início do processo de encerramento
        embed_closing = discord.Embed(
            title="🔒 Encerramento de Atendimento",
            description="Este canal será **excluído** permanentemente em **5 segundos**...",
            color=0xEF4444
        )
        embed_closing.set_footer(text="🌑 VOID Store • Canal sendo encerrado")
        await interaction.followup.send(embed=embed_closing)

        # Aguarda 5 segundos antes de deletar o canal
        await asyncio.sleep(5)

        try:
            await interaction.channel.delete(reason=f"Atendimento encerrado por {interaction.user}")
            logger.info(f"Canal {interaction.channel.name} deletado com sucesso por {interaction.user}.")
        except discord.Forbidden:
            logger.error(f"Permissão insuficiente para deletar o canal {interaction.channel.name}.")
        except Exception as e:
            logger.error(f"Erro ao deletar canal {interaction.channel.name}: {e}")

    @discord.ui.button(
        label="Gerar Pagamento PIX",
        style=discord.ButtonStyle.success,
        emoji="💳",
        custom_id="ticket:gerar_pix"
    )
    async def btn_pix(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Redireciona a chamada para a cog do PIX ou executa o comando pix-gerar
        cog_pix = interaction.client.get_cog("Pix")
        if cog_pix:
            await cog_pix.pix_gerar(interaction)
        else:
            await interaction.response.send_message(
                "❌ O módulo de PIX não foi carregado corretamente.",
                ephemeral=True
            )


# ====================================
# COG SERVICES / TICKETS
# ====================================

class Services(commands.Cog):
    """Gerenciamento de canais de atendimento e tickets da VOID Store"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        """Registra a View persistente ao iniciar a cog"""
        self.bot.add_view(TicketControlView())

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Intercepta interações de componentes para garantir que os botões persistentes funcionem"""
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id", "")

        if custom_id == "ticket:close":
            # Delegação tratada diretamente no botão da View
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Services(bot))
