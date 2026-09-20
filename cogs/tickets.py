"""
🌑 VOID Store Bot - Sistema de Tickets Totalmente Privados
"""
import discord
from discord import app_commands
from discord.ext import commands


class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Comprar Produtos",
                value="comprar",
                description="Abra um carrinho privado para efetuar compras",
                emoji="🛒"
            ),
            discord.SelectOption(
                label="Dúvidas & Suporte",
                value="suporte",
                description="Atendimento privado com a administração",
                emoji="💬"
            ),
            discord.SelectOption(
                label="Resgatar VIP / Boost",
                value="vip",
                description="Resgate as suas recompensas de VIP ou Impulso",
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

        prefix_map = {
            "comprar": "🛒-carrinho",
            "suporte": "💬-suporte",
            "vip": "💎-resgate"
        }
        prefix = prefix_map.get(category_type, "ticket")
        channel_name = f"{prefix}-{user.name.lower()}"

        # 1. Verifica se já existe um canal aberto para este utilizador
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(
                f"❌ **Já tens um atendimento aberto!** Acede a {existing_channel.mention} para continuar.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # 2. PERMISSÕES ESTRITAMENTE PRIVADAS
        overwrites = {
            # Bloqueia a visualização para todos no servidor
            guild.default_role: discord.PermissionOverwrite(
                read_messages=False,
                view_channel=False
            ),
            # Permite acesso exclusivo ao utilizador
            user: discord.PermissionOverwrite(
                read_messages=True,
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True
            ),
            # Permite ao Bot gerir o canal
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                view_channel=True,
                send_messages=True,
                manage_channels=True
            )
        }

        # Concede acesso privado aos cargos da gerência (VOID Store)
        for role_id in [1550096907739857079, 1550097139093209139]:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    read_messages=True,
                    view_channel=True,
                    send_messages=True
                )

        # 3. Localizar categoria "PEDIDOS"
        category = discord.utils.find(
            lambda c: "PEDIDOS" in c.name.upper() and isinstance(c, discord.CategoryChannel),
            guild.categories
        )

        # 4. Criação do canal privado
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"Atendimento Privado: {user.display_name} | Tipo: {category_type.upper()}"
        )

        # 5. Embed enviado no canal privado
        embed_ticket = discord.Embed(
            title=f"🌑 VOID STORE — ATENDIMENTO PRIVADO ({category_type.upper()})",
            description=(
                f"Olá {user.mention}, o teu canal privado foi criado com sucesso!\n\n"
                f"📌 **Instruções:**\n"
                f"• Detalha o teu pedido ou questão neste chat.\n"
                f"• Apenas tu e a equipa da **VOID Store** têm acesso a este canal.\n"
                f"• Clica no botão abaixo quando quiseres fechar o atendimento."
            ),
            color=discord.Color.from_rgb(15, 15, 15)
        )
        if guild.icon:
            embed_ticket.set_thumbnail(url=guild.icon.url)
        embed_ticket.set_footer(text="🌑 VOID Store • Canal 100% Privado")

        class CloseTicketView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)

            @discord.ui.button(label="Fechar Atendimento", style=discord.ButtonStyle.red, emoji="🔒")
            async def close(self, inner_interaction: discord.Interaction, inner_button: discord.ui.Button):
                await inner_interaction.response.send_message("🔒 A fechar canal privado em 5 segundos...")
                import asyncio
                await asyncio.sleep(5)
                await inner_interaction.channel.delete()

        await ticket_channel.send(content=f"{user.mention}", embed=embed_ticket, view=CloseTicketView())

        await interaction.followup.send(
            f"✅ **Canal privado criado!** Acede a {ticket_channel.mention} para seres atendido.",
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
                "🛒 Comprar Produtos   ➔ Abertura de carrinho privado\n"
                "💬 Dúvidas & Suporte  ➔ Chat privado com a gerência\n"
                "💎 Resgatar VIP       ➔ Resgate de vantagens privado\n"
                "```\n"
                "⚙️ *Atendimento 100% privado e seguro.*"
            ),
            color=discord.Color.from_rgb(15, 15, 15)
        )
        if interaction.guild and interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.set_footer(text="🌑 VOID Store • Selecione abaixo para abrir o seu ticket")

        await interaction.channel.send(embed=embed, view=TicketPanelView())
        await interaction.response.send_message("✅ Painel de Tickets enviado com sucesso!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Tickets(bot))
