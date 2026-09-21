"""
🌑 VOID Store Bot - Sistema Oficial de Loja, Vendas e Carrinho Privado
"""
import io
import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands

# ID DO CANAL DE LOGS/TRANSCRIPTS DA VOID STORE
TICKET_LOGS_CHANNEL_ID = 1549933790309257226


class CloseCartView(discord.ui.View):
    """View dos botões de ação dentro do carrinho privado (Chamar Humano e Finalizar/Encerrar)."""
    def __init__(self, opener_user: discord.User, service_name: str):
        super().__init__(timeout=None)
        self.opener_user = opener_user
        self.service_name = service_name

    @discord.ui.button(label="Chamar Atendente Humano", style=discord.ButtonStyle.blurple, emoji="👤", custom_id="btn_cart_call_human")
    async def call_human(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        
        # Concede permissão de visualização e escrita para a equipe da VOID Store
        for role_id in [1550096907739857079, 1550097139093209139]:
            role = guild.get_role(role_id)
            if role:
                await interaction.channel.set_permissions(role, read_messages=True, send_messages=True, view_channel=True)

        button.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            "🔔 **Atendente humano solicitado!** Um membro da gerência entrará no chat em breve para processar seu pagamento."
        )

    @discord.ui.button(label="Encerrar / Finalizar Compra", style=discord.ButtonStyle.red, emoji="🔒", custom_id="btn_cart_close")
    async def close_cart(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 **Gerando transcript do atendimento e encerrando em 5 segundos...**")
        
        channel = interaction.channel
        category = channel.category
        guild = interaction.guild

        # 1. Coleta o histórico de mensagens para o transcript
        messages = []
        async for msg in channel.history(limit=1000, oldest_first=True):
            time_str = msg.created_at.strftime("%d/%m/%Y %H:%M:%S")
            content = msg.content if msg.content else "[Sem Texto / Anexo ou Embed]"
            messages.append(f"[{time_str}] {msg.author.name} ({msg.author.id}): {content}")

        transcript_text = f"=== TRANSCRIPT VOID STORE — CANAL: #{channel.name} ===\n\n" + "\n".join(messages)
        transcript_file = discord.File(
            fp=io.BytesIO(transcript_text.encode("utf-8")),
            filename=f"transcript-{channel.name}.txt"
        )

        # 2. Busca ESTRITAMENTE o canal de logs e IMPEDE vazamento em canais públicos
        log_channel = guild.get_channel(TICKET_LOGS_CHANNEL_ID)
        if not log_channel:
            try:
                log_channel = await guild.fetch_channel(TICKET_LOGS_CHANNEL_ID)
            except Exception as e:
                print(f"❌ [ERRO LOGS] Não foi possível acessar o canal de logs com ID {TICKET_LOGS_CHANNEL_ID}: {e}")

        if log_channel:
            embed_log = discord.Embed(
                title="📄 TRANSCRIPT DE ATENDIMENTO — COMPRA",
                color=discord.Color.from_rgb(15, 15, 15)
            )
            embed_log.add_field(name="👤 Cliente:", value=f"{self.opener_user.mention} (`{self.opener_user.id}`)", inline=True)
            embed_log.add_field(name="🛡️ Encerrado por:", value=f"{interaction.user.mention}", inline=True)
            embed_log.add_field(name="🛒 Serviço Selecionado:", value=f"`{self.service_name}`", inline=True)
            embed_log.add_field(name="💬 Canal Encerrado:", value=f"`#{channel.name}`", inline=False)
            embed_log.set_footer(text="🌑 VOID Store • Sistema de Registro de Tickets")

            await log_channel.send(embed=embed_log, file=transcript_file)
        else:
            print(f"⚠️ [AVISO] O transcript do canal #{channel.name} NÃO foi enviado pois o canal de logs é inacessível.")

        await asyncio.sleep(5)
        
        # 3. Elimina o canal privado e a categoria criada
        await channel.delete()
        if category and len(category.channels) == 0:
            await category.delete()


class ShopSelect(discord.ui.Select):
    """Menu suspenso com as opções de produtos e serviços disponíveis na loja."""
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Engrenagem V4",
                value="engrenagem_v4",
                description="Adquira sua Engrenagem V4 — R$ 11,90",
                emoji="⚙️"
            ),
            discord.SelectOption(
                label="Frutas (Estoque)",
                value="frutas",
                description="Frutas em estoque a partir de R$ 7,90",
                emoji="🍎"
            ),
            discord.SelectOption(
                label="Up de Levels",
                value="up_levels",
                description="Serviço de Level Up rápido — R$ 13,90",
                emoji="⬆️"
            ),
            discord.SelectOption(
                label="Fragmentos",
                value="fragmentos",
                description="Pacote de Fragmentos — R$ 12,00",
                emoji="💎"
            ),
            discord.SelectOption(
                label="Money / Beli",
                value="money_beli",
                description="Farm de Money/Beli — R$ 12,90",
                emoji="💰"
            ),
            discord.SelectOption(
                label="Farm de Materiais",
                value="farm_materiais",
                description="Coleta e Farm de Materiais — R$ 7,00",
                emoji="📦"
            ),
        ]
        super().__init__(
            placeholder="Selecione o serviço ou produto desejado...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="select_shop_product"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        selected_option = next(opt for opt in self.options if opt.value == selected_value)
        service_name = selected_option.label
        
        guild = interaction.guild
        user = interaction.user
        
        # Gera o nome único do carrinho privado usando o ID do usuário para evitar duplicidade
        clean_user_name = user.name.lower().replace(" ", "")
        channel_name = f"🛒-{selected_value}-{clean_user_name}"

        # Verifica se já existe um carrinho aberto para esse produto
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(
                f"❌ **Você já possui um carrinho aberto para este item!** Acesse {existing_channel.mention}.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Definição estrita das permissões (Apenas o cliente e o Bot enxergam a sala)
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

        # Criação da Categoria Privada
        category_name = f"🛒 │ CARRINHO - {user.name}"
        cart_category = await guild.create_category_channel(
            name=category_name,
            overwrites=overwrites
        )

        # Criação do Canal Privado de Atendimento
        cart_channel = await guild.create_text_channel(
            name=channel_name,
            category=cart_category,
            overwrites=overwrites,
            topic=f"Carrinho de Compra ({service_name}) - Cliente: {user.display_name}"
        )

        # Embed explicativo enviado DENTRO do canal privado criado
        embed = discord.Embed(
            title=f"🌑 VOID STORE — CARRINHO DE COMPRAS",
            description=(
                f"Olá {user.mention}, bem-vindo ao seu carrinho de compras!\n\n"
                f"🛒 **Produto Selecionado:** `{service_name}`\n\n"
                "📌 **Instruções para a Compra:**\n"
                "1. Informe a quantidade ou detalhes adicionais do seu pedido abaixo.\n"
                "2. Clique no botão **'Chamar Atendente Humano'** para receber o QR Code do PIX e finalizar o pagamento.\n"
                "3. Após a confirmação da equipe, seu produto/serviço será entregue com total rapidez."
            ),
            color=discord.Color.from_rgb(15, 15, 15)
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text="🌑 VOID Store • Atendimento Automático, Rápido e Seguro")

        close_view = CloseCartView(opener_user=user, service_name=service_name)
        await cart_channel.send(content=f"{user.mention}", embed=embed, view=close_view)

        # Resposta privada no canal da loja
        await interaction.followup.send(
            f"✅ **Categoria e carrinho privado criados com sucesso!** Acesse {cart_channel.mention} para concluir sua compra.",
            ephemeral=True
        )


class ShopSelectView(discord.ui.View):
    """View container que abriga a caixa de seleção da loja."""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ShopSelect())


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="loja-painel", description="Envia a tabela de preços e o painel oficial de compras da VOID Store")
    @app_commands.checks.has_permissions(administrator=True)
    async def loja_painel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            title="Seja bem-vindo à VOID Store!",
            description=(
                "Seu lugar ideal para adquirir serviços e itens para **Blox Fruits** com total segurança, rapidez e o melhor preço do mercado.\n\n"
                "═════════════════════════════════════\n"
                "📋 **TABELA DE PREÇOS & SERVIÇOS**\n"
                "═════════════════════════════════════\n\n"
                "⚙️ **Engrenagem V4** ➔ `R$ 11,90`\n"
                "🍎 **Frutas (Estoque)** ➔ `A partir de R$ 7,90`\n"
                "⬆️ **Up de Levels** ➔ `R$ 13,90`\n"
                "💎 **Fragmentos** ➔ `R$ 12,00`\n"
                "💰 **Money / Beli** ➔ `R$ 12,90`\n"
                "📦 **Farm de Materiais** ➔ `R$ 7,00`\n\n"
                "═════════════════════════════════════\n"
                "🚀 **COMO REALIZAR O SEU PEDIDO?**\n"
                "1️⃣ **Selecione o serviço** desejado no menu suspenso abaixo.\n"
                "2️⃣ Uma **categoria e canal 100% privados** serão criados automaticamente.\n"
                "3️⃣ Siga as instruções do chat para efetuar o pagamento via PIX."
            ),
            color=discord.Color.from_rgb(15, 15, 15)
        )
        if interaction.guild and interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.set_footer(text="🌑 VOID Store • Atendimento Automático, Rápido e Seguro")

        # Envia o painel no canal onde o comando foi acionado
        await interaction.channel.send(embed=embed, view=ShopSelectView())
        await interaction.followup.send("✅ Painel da loja enviado com sucesso!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Shop(bot))
