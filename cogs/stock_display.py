"""
🌑 VOID Store Bot - Exibição Automática de Estoque e Carrinho Privado
"""
import discord
from discord.ext import commands

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

        channel_name = f"🛒-carrinho-{user.name.lower()}"

        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(
                f"❌ **Você já possui um carrinho aberto!** Acesse {existing_channel.mention} para concluir sua compra.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Permissões do canal privado
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
            user: discord.PermissionOverwrite(read_messages=True, view_channel=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, view_channel=True, send_messages=True, manage_channels=True)
        }

        for role_id in [1550096907739857079, 1550097139093209139]:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, view_channel=True, send_messages=True)

        category = discord.utils.find(lambda c: "PEDIDOS" in c.name.upper() and isinstance(c, discord.CategoryChannel), guild.categories)

        cart_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Carrinho Privado de {user.display_name} | Item: {self.product_name}"
        )

        embed_cart = discord.Embed(
            title="🛒 CARRINHO PRIVADO — VOID STORE",
            description=(
                f"Olá {user.mention}, seu carrinho privado foi criado com sucesso!\n\n"
                f"📦 **Produto Selecionado:**\n`{self.product_name}`\n\n"
                f"Aguarde um atendente ou envie mensagem para finalizar."
            ),
            color=discord.Color.from_rgb(15, 15, 15)
        )
        embed_cart.set_footer(text="🌑 VOID Store • Compra Segura e Privada")

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

        await interaction.followup.send(
            f"✅ **Carrinho privado criado!** Clique em {cart_channel.mention} para prosseguir.",
            ephemeral=True
        )


class StockDisplay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.id != STOCK_CHANNEL_ID:
            return

        # Verifica se o membro tem permissão
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
