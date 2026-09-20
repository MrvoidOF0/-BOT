"""
🌑 VOID Store Bot - Painel Oficial /loja-painel
"""
import discord
from discord import app_commands
from discord.ext import commands


class ServiceSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Engrenagem V4",
                value="engrenagem_v4",
                description="R$ 29,90 • Desbloqueie a engrenagem V4",
                emoji="⚙️"
            ),
            discord.SelectOption(
                label="Frutas do Estoque",
                value="frutas",
                description="A partir de R$ 15,00 • Frutas físicas e permanentes",
                emoji="🍎"
            ),
            discord.SelectOption(
                label="Up de Levels",
                value="levels",
                description="R$ 19,90 • Serviço de subida de nível rápida",
                emoji="⬆️"
            ),
            discord.SelectOption(
                label="Fragmentos",
                value="fragmentos",
                description="R$ 12,00 • Pacotes de fragmentos",
                emoji="💎"
            ),
            discord.SelectOption(
                label="Money / Beli",
                value="money_beli",
                description="R$ 9,90 • Farm de Beli na sua conta",
                emoji="💰"
            ),
            discord.SelectOption(
                label="Farm de Materiais",
                value="farm_materiais",
                description="R$ 24,90 • Materiais raros e ossos",
                emoji="📦"
            ),
            discord.SelectOption(
                label="Dúvidas & Suporte Geral",
                value="suporte",
                description="Fale diretamente com a gerência",
                emoji="💬"
            )
        ]
        super().__init__(
            placeholder="🛒 Selecione o produto/serviço desejado...",
            min_values=1,
            max_values=1,
            custom_id="shop_panel_select",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        service_key = self.values[0]

        channel_name = f"🛒-{service_key.replace('_', '-')}-{user.name.lower()}"

        # 1. Verifica se já existe carrinho aberto
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(
                f"❌ **Você já possui um atendimento aberto nesta categoria!** Acesse {existing_channel.mention}.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # 2. Configuração de Permissões Totalmente Privadas
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
            user: discord.PermissionOverwrite(
                read_messages=True,
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                view_channel=True,
                send_messages=True,
                manage_channels=True
            )
        }

        # Concede acesso privado apenas aos cargos da Administração (VOID Store)
        for role_id in [1550096907739857079, 1550097139093209139]:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, view_channel=True, send_messages=True)

        # 3. Localiza a categoria "PEDIDOS"
        category = discord.utils.find(
            lambda c: "PEDIDOS" in c.name.upper() and isinstance(c, discord.CategoryChannel),
            guild.categories
        )

        # 4. Criação do Canal Privado
        cart_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Atendimento Privado: {user.display_name} | Item: {service_key.upper()}"
        )

        # 5. Embed do Carrinho Interno
        embed_ticket = discord.Embed(
            title="🌑 VOID STORE — CARRINHO DE COMPRAS",
            description=(
                f"Olá {user.mention}, bem-vindo ao seu atendimento privado!\n\n"
                f"📌 **Serviço Selecionado:** `{service_key.replace('_', ' ').upper()}`\n\n"
                f"**Como proceder:**\n"
                f"1️⃣ Envie o seu nick do Roblox no chat.\n"
                f"2️⃣ Aguarde a confirmação de disponibilidade da equipe.\n"
                f"3️⃣ O pagamento será realizado via **PIX** de forma rápida e segura.\n\n"
                f"🔒 *Apenas você e a gerência possuem acesso a este canal.*"
            ),
            color=discord.Color.from_rgb(15, 15, 15)
        )
        if guild.icon:
            embed_ticket.set_thumbnail(url=guild.icon.url)
        embed_ticket.set_footer(text="🌑 VOID Store • Sistema Automático de Vendas")

        class CloseCartView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="Cancelar / Fechar Carrinho", style=discord.ButtonStyle.red, emoji="🔒")
            async def close(self, inner_interaction: discord.Interaction, inner_button: discord.ui.Button):
                await inner_interaction.response.send_message("🔒 Encerrando o carrinho em 5 segundos...")
                import asyncio
                await asyncio.sleep(5)
                await inner_interaction.channel.delete()

        await cart_channel.send(content=f"{user.mention}", embed=embed_ticket, view=CloseCartView())

        await interaction.followup.send(
            f"✅ **Carrinho privado criado com sucesso!** Acesse {cart_channel.mention} para concluir sua compra.",
            ephemeral=True
        )


class ServicePanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ServiceSelect())


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="loja-painel", description="Envia o painel principal de compras e serviços da VOID Store")
    @commands.has_permissions(administrator=True)
    async def loja_painel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌑 𝐕𝐎𝐈𝐃 𝐒𝐭𝐨𝐫𝐞 — Loja Oficial & Atendimento",
            description=(
                "Seja bem-vindo à **VOID Store**! Seu lugar ideal para adquirir serviços e itens para **Blox Fruits** com total segurança, rapidez e o melhor preço do mercado.\n\n"
                "═══════════════════════════════════════\n"
                "📋 **TABELA DE PREÇOS & SERVIÇOS**\n"
                "═══════════════════════════════════════\n"
                "⚙️ **Engrenagem V4** ➔ `R$ 29,90`\n"
                "🍎 **Frutas (Estoque)** ➔ `A partir de R$ 15,00`\n"
                "⬆️ **Up de Levels** ➔ `R$ 19,90`\n"
                "💎 **Fragmentos** ➔ `R$ 12,00`\n"
                "💰 **Money / Beli** ➔ `R$ 9,90`\n"
                "📦 **Farm de Materiais** ➔ `R$ 24,90`\n\n"
                "═══════════════════════════════════════\n"
                "🚀 **COMO REALIZAR O SEU PEDIDO?**\n"
                "1️⃣ **Selecione o serviço** desejado no menu suspenso abaixo.\n"
                "2️⃣ Um **canal 100% privado** será aberto na categoria `PEDIDOS`.\n"
                "3️⃣ Siga as instruções do chat para efetuar o pagamento via **PIX**.\n"
                "═══════════════════════════════════════"
            ),
            color=discord.Color.from_rgb(15, 15, 15)
        )
        
        if interaction.guild and interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
            
        embed.set_footer(text="🌑 VOID Store • Atendimento Automático, Rápido e Seguro")

        await interaction.channel.send(embed=embed, view=ServicePanelView())
        await interaction.response.send_message("✅ Painel enviado com sucesso!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Shop(bot))
