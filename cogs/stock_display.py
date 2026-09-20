"""
🌑 VOID Store Bot - Exibição Automática de Estoque
"""
import discord
from discord.ext import commands
from utils.permissions import PermissionChecker

# ID do canal de estoque definido diretamente no código
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
            f"🛒 Iniciaste a compra de **{self.product_name}**. Verifica as tuas mensagens privadas!",
            ephemeral=True
        )


class StockDisplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # 1. Ignorar mensagens do próprio bot ou de outros bots
        if message.author.bot:
            return

        # 2. Verificar se a mensagem foi enviada no canal correto (#estoque)
        if message.channel.id != STOCK_CHANNEL_ID:
            return

        # 3. Verificar permissões do autor
        if not PermissionChecker.has_authorized_role(message.author):
            return

        # 4. Validar se a mensagem tem texto
        content = message.content.strip() if message.content else ""
        if not content:
            return

        # 5. Apagar a mensagem original enviada pelo utilizador/admin
        try:
            await message.delete()
        except Exception as e:
            print(f"[ESTOQUE] Não foi possível apagar a mensagem original: {e}")

        # 6. Criar o Embed formatado
        embed = discord.Embed(
            title="📦 NOVO ITEM EM ESTOQUE",
            description=content,
            color=discord.Color.from_rgb(15, 15, 15)
        )
        
        if message.guild and message.guild.icon:
            embed.set_author(name=message.guild.name, icon_url=message.guild.icon.url)
            
        embed.set_footer(text="🌑 VOID Store • Clica no botão abaixo para adquirir")

        # 7. Obter a primeira linha como título do produto para o botão
        product_title = content.split("\n")[0]
        view = BuyButton(product_name=product_title)

        # 8. Enviar o Embed com o Botão
        await message.channel.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(StockDisplay(bot))
