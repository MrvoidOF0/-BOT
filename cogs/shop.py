"""
🌑 VOID Store Bot - Sistema de Loja de Elite
"""
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils.permissions import PermissionChecker
from config import config

PRODUTOS = {
    "v4": {"nome": "Engrenagem V4", "emoji": "⚙️", "cor": 0x2b2d31},
    "frutas": {"nome": "Frutas", "emoji": "🍎", "cor": 0x9b59b6},
    "levels": {"nome": "Levels", "emoji": "⬆️", "cor": 0x3498db},
    "fragmentos": {"nome": "Fragmentos", "emoji": "💎", "cor": 0xe74c3c},
    "money": {"nome": "Money / Beli", "emoji": "💰", "cor": 0xf39c12},
    "materiais": {"nome": "Farm de Materiais", "emoji": "📦", "cor": 0x27ae60},
}

class NickModal(discord.ui.Modal, title="Finalizar Pedido"):
    nick = discord.ui.TextInput(label="Qual o seu Nick no jogo?", placeholder="Ex: mrvoid157", required=False)

    def __init__(self, pid: str):
        super().__init__()
        self.pid = pid

    async def on_submit(self, interaction: discord.Interaction):
        # Resposta imediata para evitar erro de timeout
        await interaction.response.defer(ephemeral=True)
        cog = interaction.client.get_cog("Shop")
        if cog:
            await cog.abrir_canal(interaction, self.pid, self.nick.value or "Não informado")

class Shop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component: return
        cid = interaction.data.get("custom_id", "")
        if cid.startswith("shop:"):
            await interaction.response.send_modal(NickModal(cid.replace("shop:", "")))

    @app_commands.command(name="loja-painel", description="🛒 Envia o painel de compras oficial")
    async def loja_painel(self, interaction: discord.Interaction):
        if not await PermissionChecker.check_interaction_permissions(interaction): return

        embed = discord.Embed(
            title="🌑 𝐕𝐎𝐈𝐃 𝐒𝐭𝐨𝐫𝐞 | Loja Oficial",
            description=(
                "Seja bem-vindo à nossa loja oficial! 🛒\n\n"
                "Para realizar um pedido, clique no botão do serviço desejado abaixo.\n"
                "Um canal de atendimento exclusivo será aberto para você.\n\n"
                "🚀 **Como funciona:**\n"
                "1️⃣ Clique no botão do produto\n"
                "2️⃣ Informe seu nick no formulário\n"
                "3️⃣ Combine os detalhes no ticket\n"
                "4️⃣ Realize o pagamento via PIX\n\n"
                "💳 **Tabela de Preços**\n"
                "⚙️ **Engrenagem V4** — R$ 29,90\n"
                "🍎 **Frutas** — R$ 15,00\n"
                "⬆️ **Levels** — R$ 19,90\n"
                "💎 **Fragmentos** — R$ 12,00\n"
                "💰 **Money / Beli** — R$ 9,90\n"
                "📦 **Farm de Materiais** — R$ 24,90"
            ),
            color=0x000000
        )
        embed.set_footer(text="🌑 VOID Store | Atendimento Rápido e Seguro")
        
        view = discord.ui.View(timeout=None)
        for pid, p in PRODUTOS.items():
            view.add_item(discord.ui.Button(label=p["nome"], style=discord.ButtonStyle.blurple, emoji=p["emoji"], custom_id=f"shop:{pid}"))
        
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel enviado!", ephemeral=True)

    async def abrir_canal(self, interaction: discord.Interaction, pid: str, nick: str):
        guild = interaction.guild
        user = interaction.user
        p = PRODUTOS[pid]
        
        cat = guild.get_channel(config.TICKET_CATEGORY_ID)
        ch_name = f"🛒-{pid}-{user.name}".lower()[:50]

        for ch in cat.text_channels:
            if ch.name == ch_name:
                return await interaction.followup.send(f"⚠️ Você já tem um ticket aberto: {ch.mention}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        for rid in PermissionChecker.CARGOS_ADM:
            role = guild.get_role(rid)
            if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await cat.create_text_channel(name=ch_name, overwrites=overwrites, topic=f"Dono: {user.id}")

        embed = discord.Embed(title=f"{p['emoji']} Novo Pedido — {p['nome']}", color=p['cor'])
        embed.add_field(name="🎮 Nick", value=f"`{nick}`", inline=True)
        embed.add_field(name="📦 Produto", value=p['nome'], inline=True)
        embed.add_field(name="💬 Instrução", value="Aguarde um staff te atender. Diga o que deseja e peça o PIX.", inline=False)
        
        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(label="Fechar Canal", style=discord.ButtonStyle.red, emoji="🔒", custom_id="svc:fechar"))
        view.add_item(discord.ui.Button(label="Gerar PIX", style=discord.ButtonStyle.green, emoji="💳", custom_id="canal:pix"))

        await channel.send(content=f"{user.mention} | <@&{PermissionChecker.CARGOS_ADM[0]}>", embed=embed, view=view)
        await interaction.followup.send(f"✅ Ticket aberto: {channel.mention}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))
