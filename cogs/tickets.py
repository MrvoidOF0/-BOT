import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils.permissions import PermissionChecker
from config import config

class PersistentCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Canal", style=discord.ButtonStyle.red, emoji="🔒", custom_id="svc:fechar")
    async def fechar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # RESPOSTA IMEDIATA: Isso mata o erro de "não respondeu a tempo"
        await interaction.response.defer(ephemeral=True)
        cog = interaction.client.get_cog("Tickets")
        if cog: await cog.processar_fechamento(interaction)

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.bot.add_view(PersistentCloseView())

    async def processar_fechamento(self, interaction: discord.Interaction):
        # Apenas staff autorizado ou dono do ticket
        dono_id = 0
        if interaction.channel.topic:
            try: dono_id = int("".join(filter(str.isdigit, interaction.channel.topic)))
            except: pass

        if not PermissionChecker.is_authorized(interaction.user) and interaction.user.id != dono_id:
            return await interaction.followup.send("❌ Você não tem permissão para fechar.", ephemeral=True)

        # Confirmação com botões que expiram (segurança)
        view = discord.ui.View(timeout=30)
        btn_sim = discord.ui.Button(label="Confirmar", style=discord.ButtonStyle.danger)
        btn_nao = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.secondary)

        async def sim(i: discord.Interaction):
            await i.response.edit_message(content="✅ Deletando em 5 segundos...", view=None)
            await i.channel.send("🔒 **Canal encerrado.**")
            await asyncio.sleep(5)
            await i.channel.delete()

        async def nao(i: discord.Interaction):
            await i.response.edit_message(content="❌ Cancelado.", view=None)

        btn_sim.callback = sim
        btn_nao.callback = nao
        view.add_item(btn_sim)
        view.add_item(btn_nao)

        await interaction.followup.send("⚠️ **Deseja fechar o ticket?**", view=view, ephemeral=True)

    @app_commands.command(name="ticket-panel", description="🎫 Painel de Suporte")
    async def ticket_panel(self, interaction: discord.Interaction):
        if not await PermissionChecker.check_interaction_permissions(interaction): return
        embed = discord.Embed(title="🌑 VOID Store | Suporte", description="Clique abaixo para abrir um suporte.", color=0x000000)
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Abrir Suporte", style=discord.ButtonStyle.blurple, custom_id="panel:suporte"))
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Enviado!", ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component: return
        cid = interaction.data.get("custom_id", "")
        
        if cid == "panel:suporte":
            await interaction.response.defer(ephemeral=True)
            cat = interaction.guild.get_channel(config.TICKET_CATEGORY_ID)
            ch = await cat.create_text_channel(name=f"💬-suporte-{interaction.user.name}", topic=f"Dono: {interaction.user.id}")
            view = PersistentCloseView()
            await ch.send(f"{interaction.user.mention} Como podemos ajudar?", view=view)
            await interaction.followup.send(f"✅ Aberto em {ch.mention}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
