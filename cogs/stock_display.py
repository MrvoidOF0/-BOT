"""
🌑 VOID Store Bot - Exibição Automática de Estoque
"""
import discord
from discord.ext import commands

# ID do canal de estoque fixado
STOCK_CHANNEL_ID = 1549948220317106186


class BuyButton(discord.ui.View):
    def __init__(self, product_name: str):
        super().__init__(timeout=None)
        self.product_name = product_name

    @discord.ui.button(
        label="Comprar",
        style=discord.ButtonStyle.green,
        custom_id="btn_comprar_estoque",
        emoji="🛒"
    )
    async def buy_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🛒 Você iniciou a compra de **{self.product_name}**. Verifique seu carrinho!",
            ephemeral=True
        )


class StockDisplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # 1. Ignora bots
        if message.author.bot:
            return

        # 2. Filtra somente mensagens no canal #estoque
        if message.channel.id != STOCK_CHANNEL_ID:
            return

        # 3. Permissão: apenas administradores ou membros com gerência de mensagens
        if isinstance(message.author, discord.Member):
            perms = message.channel.permissions_for(message.author)
            if not (perms.administrator or perms.manage_messages):
                return

        # 4. Garante que há texto na mensagem
        content = message.content.strip() if message.content else ""
        if not content:
            return

        # 5. Apaga a mensagem original
        try:
            await message.delete()
        except Exception:
            pass

        # 6. Monta o Embed do Produto
        embed = discord.Embed(
            title="📦 NOVO ITEM EM ESTOQUE",
            description=content,
            color=discord.Color.from_rgb(15, 15, 15)
        )
        
        if message.guild and message.guild.icon:
            embed.set_author(name=message.guild.name, icon_url=message.guild.icon.url)
            
        embed.set_footer(text="🌑 VOID Store • Clique no botão abaixo para adquirir")

        # 7. Define o título do produto para o botão
        product_title = content.split("\n")[0]
        view = BuyButton(product_name=product_title)

        # 8. Publica o Embed com o botão
        await message.channel.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(StockDisplay(bot))
