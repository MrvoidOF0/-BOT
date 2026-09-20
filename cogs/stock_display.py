"""
🌑 VOID Store Bot - Exibição e Auto-Embed de Estoque
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
        # Pega o ID do canal do arquivo .env
        env_channel_id = os.getenv("STOCK_CHANNEL_ID")
        self.stock_channel_id = int(env_channel_id) if env_channel_id and env_channel_id.isdigit() else None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignora bots e verifica se o ID do canal foi configurado
        if message.author.bot or not self.stock_channel_id:
            return

        # Verifica se a mensagem foi enviada no canal correto
        if message.channel.id != self.stock_channel_id:
            return

        # Valida permissões do autor da mensagem
        if not PermissionChecker.has_authorized_role(message.author):
            return

        content = message.content.strip()
        if not content:
            return

        # Apaga a mensagem digitada pelo admin/gerente
        try:
            await message.delete()
        except discord.HTTPException:
            pass

        # Monta o Embed do Produto
        embed = discord.Embed(
            title="📦 NOVO ITEM EM ESTOQUE",
            description=content,
            color=discord.Color.from_rgb(15, 15, 15)
        )
        if message.guild and message.guild.icon:
            embed.set_author(name=message.guild.name, icon_url=message.guild.icon.url)
        embed.set_footer(text="🌑 VOID Store • Clique no botão abaixo para adquirir")

        # Nome do produto para o botão (primeira linha do texto)
        product_title = content.split("\n")[0]
        view = BuyButton(product_name=product_title)

        await message.channel.send(embed=embed, view=view)


# Função obrigatória para o discord.py carregar o cog
async def setup(bot):
    await bot.add_cog(StockDisplay(bot))
