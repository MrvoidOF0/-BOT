"""
🌑 VOID Store Bot - Tickets e Fechamento Universal
"""
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils.permissions import PermissionChecker
from config import config

class PersistentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Canal", style=discord.ButtonStyle.red, emoji="🔒", custom_id="svc:fechar")
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        cog = interaction.client.get_cog("Tickets")
        if cog: await cog.processar_fechamento(interaction)

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        # Registra o ouvidor assim que liga
        self.bot.add_view(PersistentView())

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component: return
        cid = interaction.data.get("custom_id", "")

        if cid == "panel:suporte":
            await interaction.response.defer(ephemeral=True)
            await self.abrir_suporte(interaction)

        if cid == "canal:pix":
            if not PermissionChecker.is_authorized(interaction.user):
                return await interaction.response.send_message("❌ Apenas staff.", ephemeral=True)
            await interaction.response.send_message("💳 Use `/pix-gerar` para cobrar o cliente.", ephemeral=True)

    async def abrir_suporte(self, interaction: discord.Interaction):
        cat = interaction.guild.get_channel(config.TICKET_CATEGORY_ID)
        ch = await cat.create_text_channel(name=f"💬-suporte-{interaction.user.name}", topic=f"Dono: {interaction.user.id}")
        await ch.send(f"{interaction.user.mention} Como podemos ajudar?", view=PersistentView())
        await interaction.followup.send(f"✅ Aberto em {ch.mention}", ephemeral=True)

    async def processar_fechamento(self, interaction: discord.Interaction):
        dono_id = 0
        if interaction.channel.topic:
            try: dono_id = int("".join(filter(str.isdigit, interaction.channel.topic)))
            except: pass

        if not PermissionChecker.is_authorized(interaction.user) and interaction.user.id != dono_id:
            return await interaction.followup.send("❌ Sem permissão.", ephemeral=True)

        view = discord.ui.View(timeout=30)
        btn_sim = discord.ui.Button(label="Confirmar", style=discord.ButtonStyle.danger)
        btn_nao = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.secondary)

        async def sim(i):
            await i.response.edit_message(content="✅ Deletando em 5 segundos...", view=None)
            await i.channel.send("🔒 **Ticket encerrado.**")
            await asyncio.sleep(5)
            await i.channel.delete()

        async def nao(i): await i.response.edit_message(content="❌ Cancelado.", view=None)

        btn_sim.callback = sim
        btn_nao.callback = nao
        view.add_item(btn_sim)
        view.add_item(btn_nao)
        await interaction.followup.send("⚠️ Fechar ticket?", view=view, ephemeral=True)

    @app_commands.command(name="ticket-panel", description="🎫 Painel de Suporte")
    async def ticket_panel(self, interaction: discord.Interaction):
        if not await PermissionChecker.check_interaction_permissions(interaction): return
        embed = discord.Embed(title="🌑 VOID Store | Atendimento", description="Clique abaixo para abrir um suporte.", color=0x000000)
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Suporte", style=discord.ButtonStyle.blurple, custom_id="panel:suporte"))
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Enviado!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
