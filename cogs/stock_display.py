"""
🌑 VOID Store Bot - Exibição e Auto-Embed de Estoque (com Debug)
"""
import os
import discord
from discord.ext import commands
from utils.permissions import PermissionChecker

class BuyButton(discord.ui.View):
    def __init__(self, product_name: str):
        super().__init__(timeout=None)
        self.product_name = product_name

    @discord.ui.button(label="Comprar", style=discord.ButtonStyle.green, custom_id="btn_comprar_estoque", emoji="🛒")
    async def buy_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🛒 Você iniciou a compra de **{self.product_name}**. Verifique seus canais/carrinho!",
            ephemeral=True
        )

class StockDisplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignora bots
        if message.author.bot:
            return

        # Pega o ID configurado na Railway ou usa o ID direto do seu canal de estoque
        env_channel = os.getenv("STOCK_CHANNEL_ID")
        stock_channel_id = int(env_channel) if env_channel and env_channel.isdigit() else 1549948220317106186

        # Se a mensagem foi em outro canal, ignora
        if message.channel.id != stock_channel_id:
            return

        print(f"[DEBUG STOCK] Mensagem recebida no canal de estoque de: {message.author.name}")

        # Verifica se o conteúdo foi lido
        if not message.content:
            print("[DEBUG STOCK] ERRO: O conteúdo da mensagem veio vazio! Ative a MESSAGE CONTENT INTENT no Portal do Discord.")
            return

        # Verifica permissão
        if not PermissionChecker.has_authorized_role(message.author):
            print(f"[DEBUG STOCK] Usuário {message.author.name} não tem permissão para enviar no estoque.")
            return

        print("[DEBUG STOCK] Criando Embed e apagando mensagem original...")

        # Apaga a mensagem enviada pelo usuário
        try:
            await message.delete()
        except Exception as e:
            print(f"[DEBUG STOCK] Erro ao deletar mensagem: {e}")

        # Monta o Embed
        embed = discord.Embed(
            title="📦 NOVO ITEM EM ESTOQUE",
            description=message.content,
            color=discord.Color.from_rgb(15, 15, 15)
        )
        if message.guild and message.guild.icon:
            embed.set_author(name=message.guild.name, icon_url=message.guild.icon.url)
        embed.set_footer(text="🌑 VOID Store • Clique no botão abaixo para adquirir")

        product_title = message.content.split("\n")[0]
        view = BuyButton(product_name=product_title)

        await message.channel.send(embed=embed, view=view)
        print("[DEBUG STOCK] Embed enviado com sucesso!")

async def setup(bot):
    await bot.add_cog(StockDisplay(bot))
