"""
🌑 VOID Store Bot - Exibição Automática de Estoque com Sistema de Carrinho
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
        guild = interaction.guild
        user = interaction.user

        # Nome padronizado para o canal de carrinho do usuário
        channel_name = f"🛒-carrinho-{user.name.lower()}"

        # 1. Verifica se o usuário já possui um carrinho aberto
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(
                f"❌ **Você já possui um carrinho aberto!** Acesse {existing_channel.mention} para concluir sua compra.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # 2. Permissões do novo canal privado
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        # Adiciona permissão para os cargos da gerência, se existirem no servidor
        for role_id in [1550096907739857079, 1550097139093209139]:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # 3. Tenta encontrar a categoria "PEDIDOS" ou cria o canal na raiz
        category = discord.utils.find(lambda c: "PEDIDOS" in c.name.upper() and isinstance(c, discord.CategoryChannel), guild.categories)

        cart_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Carrinho de {user.display_name} | Produto: {self.product_name}"
        )

        # 4. Envia o Embed de confirmação dentro do novo canal de carrinho
        embed_cart = discord.Embed(
            title="🛒 CARRINHO DE COMPRAS - VOID STORE",
            description=(
                f"Olá {user.mention}, seu carrinho foi criado com sucesso!\n\n"
                f"📦 **Produto Selecionado:**\n`{self.product_name}`\n\n"
                f"Clique nos botões abaixo ou aguarde um atendente para finalizar seu pagamento via PIX."
            ),
            color=discord.Color.from_rgb(15, 15, 15)
        )
        embed_cart.set_footer(text="🌑 VOID Store • Sistema de Vendas")

        # Botão para fechar o carrinho dentro do canal
        class CloseCartView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="Cancelar / Fechar Carrinho", style=discord.ButtonStyle.red, emoji="🔒")
            async def close(self, inner_interaction: discord.Interaction, inner_button: discord.ui.Button):
                await inner_interaction.response.send_message("🔒 Fechando carrinho em 5 segundos...")
                import asyncio
                await asyncio.sleep(5)
                await inner_interaction.channel.delete()

        await cart_channel.send(content=f"{user.mention}", embed=embed_cart, view=CloseCartView())

        # 5. Avisa o cliente no canal do estoque com o link do canal criado
        await interaction.followup.send(
            f"✅ **Carrinho criado com sucesso!** Clique em {cart_channel.mention} para continuar a compra.",
            ephemeral=True
        )


class StockDisplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.id != STOCK_CHANNEL_ID:
            return

        # Verifica permissão de administrador
        if isinstance(message.author, discord.Member):
            perms = message.channel.permissions_for(message.author)
            if not (perms.administrator or perms.manage_messages):
                return

        content = message.content.strip() if message.content else ""
        if not content:
            return

        try:
            await message.delete()
        except Exception:
            pass

        embed = discord.Embed(
            title="📦 NOVO ITEM EM ESTOQUE",
            description=content,
            color=discord.Color.from_rgb(15, 15, 15)
        )
        if message.guild and message.guild.icon:
            embed.set_author(name=message.guild.name, icon_url=message.guild.icon.url)
        embed.set_footer(text="🌑 VOID Store • Clique no botão abaixo para adquirir")

        product_title = content.split("\n")[0]
        view = BuyButton(product_name=product_title)

        await message.channel.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(StockDisplay(bot))
