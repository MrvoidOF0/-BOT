"""
🌑 VOID Store Bot - Sistema do Painel de Tickets/Suporte
"""
import discord
from discord.ext import commands


class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Comprar Produtos",
                value="comprar",
                description="Abra um ticket para adquirir produtos do estoque",
                emoji="🛒"
            ),
            discord.SelectOption(
                label="Dúvidas & Suporte",
                value="suporte",
                description="Tire dúvidas sobre os nossos serviços e entregas",
                emoji="💬"
            ),
            discord.SelectOption(
                label="Resgatar VIP / Boost",
                value="vip",
                description="Resgate as suas recompensas de VIPS ou Impulsos",
                emoji="💎"
            ),
        ]
        super().__init__(
            placeholder="🌑 Selecione a categoria do seu atendimento...",
            min_values=1,
            max_values=1,
            custom_id="ticket_panel_select",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        category_type = self.values[0]

        # Nome limpo e padronizado para o canal
        prefix_map = {
            "comprar": "🛒-carrinho",
            "suporte": "💬-suporte",
            "vip": "💎-resgate"
        }
        prefix = prefix_map.get(category_type, "ticket")
        channel_name = f"{prefix}-{user.name.lower()}"

        # 1. Verifica se o cliente já possui um canal aberto nesta categoria
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(
                f"❌ **Já tens um atendimento aberto!** Acede a {existing_channel.mention} para continuar.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # 2. Configuração de Permissões
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        # Cargos da gerência
        for role_id in [1550096907739857079, 1550097139093209139]:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        # 3. Localizar categoria "PEDIDOS"
        category = discord.utils.find(lambda c: "PEDIDOS" in c.name.upper() and isinstance(c, discord.CategoryChannel), guild.categories)

        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Atendimento de {user.display_name} | Categoria: {category_type.upper()}"
        )

        # 4. Embed Interno do Canal Criado
        embed_ticket = discord.Embed(
            title=f"🌑 VOID STORE — ATENDIMENTO ({category_type.upper()})",
            description=(
                f"Olá {user.mention}, o teu atendimento foi iniciado com sucesso!\n\n"
                f"📌 **Instruções:**\n"
                f"• Escreve detalhadamente o que precisas ou o item que desejas comprar.\n"
                f"• Um membro da gerência atenderá a tua solicitação em breve.\n"
                f"• Para encerrar este atendimento, clica no botão abaixo."
            ),
            color=discord.Color.from_rgb(20, 20, 20)
        )
        embed_ticket.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed_ticket.set_footer(text="🌑 VOID Store • Sistema de Vendas & Suporte")

        # Botão para fechar o ticket dentro do canal
        class CloseTicketView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="Fechar Atendimento", style=discord.ButtonStyle.red, emoji="🔒")
            async def close(self, inner_interaction: discord.Interaction, inner_button: discord.ui.Button):
                await inner_interaction.response.send_message("🔒 Encerrando o atendimento em 5 segundos...")
                import asyncio
                await asyncio.sleep(5)
                await inner_interaction.channel.delete()

        await ticket_channel.send(content=f"{user.mention}", embed=embed_ticket, view=CloseTicketView())

        await interaction.followup.send(
            f"✅ **Atendimento criado!** Clica em {ticket_channel.mention} para seres atendido.",
            ephemeral=True
        )


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup-ticket", description="Envia o painel principal de tickets/carrinhos")
    @commands.has_permissions(administrator=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌑 Central de Atendimento — VOID Store",
            description=(
                "Seja bem-vindo à **VOID Store**!\n\n"
                "Para efetuar compras, tirar dúvidas ou resgatar benefícios, selecione a opção desejada no **menu abaixo** para abrir um canal privado.\n\n"
                "```\n"
                "🛒 Comprar Produtos   ➔ Abertura de carrinho direto\n"
                "💬 Dúvidas & Suporte  ➔ Falar com a administração\n"
                "💎 Resgatar VIP       ➔ Resgate de vantagens\n"
                "```\n"
                "⚙️ *Atendimento rápido e automatizado.*"
            ),
            color=discord.Color.from_rgb(15, 15, 15)
        )
        
        if interaction.guild and interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
            
        embed.set_image(url="https://media.discordapp.net/attachments/1549930891588141157/1549948220317106186/banner.png")  # Opcional: Adiciona banner visual
        embed.set_footer(text="🌑 VOID Store • Selecione abaixo para abrir o seu ticket")

        await interaction.channel.send(embed=embed, view=TicketPanelView())
        await interaction.response.send_message("✅ Painel de Tickets enviado com sucesso!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Tickets(bot))
