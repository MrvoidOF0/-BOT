"""
🌑 VOID Store Bot - Sistema de Serviços com Fórum e Preços Específicos
Modal de informações do cliente antes de abrir o canal.
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio

from utils.permissions import PermissionChecker
from utils.constants import Emojis
from utils.logger import logger
from config import config


# ====================================
# MODAL DE INFORMAÇÕES DO CLIENTE
# ====================================

class ClientInfoModal(discord.ui.Modal):
    """
    Aparece ANTES de abrir o canal.
    Coleta informações do cliente sobre a conta no jogo.
    """

    nome_conta = discord.ui.TextInput(
        label="Nome da sua conta no jogo (IGN)",
        placeholder="Ex: VoidPlayer123",
        required=True,
        max_length=100
    )

    nivel_atual = discord.ui.TextInput(
        label="Seu nível atual no jogo",
        placeholder="Ex: 2400",
        required=True,
        max_length=20
    )

    fruta_atual = discord.ui.TextInput(
        label="Sua fruta atual (se aplicável)",
        placeholder="Ex: Dragon, Leopard, Kitsune... ou Nenhuma",
        required=False,
        max_length=100
    )

    senha_conta = discord.ui.TextInput(
        label="Senha da conta (OPCIONAL)",
        placeholder="Deixe vazio se não quiser informar agora",
        required=False,
        max_length=100
    )

    observacoes = discord.ui.TextInput(
        label="Observações adicionais",
        placeholder="Qualquer informação extra que queira passar",
        required=False,
        style=discord.TextStyle.long,
        max_length=500
    )

    def __init__(self, service_name: str, option_name: str, price: float, custom_id_suffix: str):
        super().__init__(title=f"Pedido: {service_name}")
        self.service_name = service_name
        self.option_name = option_name
        self.price = price
        self.custom_id_suffix = custom_id_suffix

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        cog = interaction.client.get_cog("Services")
        if cog:
            await cog.criar_canal_servico(
                interaction=interaction,
                service_name=self.service_name,
                option_name=self.option_name,
                price=self.price,
                nome_conta=self.nome_conta.value,
                nivel_atual=self.nivel_atual.value,
                fruta_atual=self.fruta_atual.value or "Não informado",
                senha_conta=self.senha_conta.value or "Não informado",
                observacoes=self.observacoes.value or "Nenhuma"
            )


# ====================================
# VIEW DE FECHAR CANAL DE SERVIÇO
# ====================================

class ServiceCloseView(discord.ui.View):
    """Botões dentro do canal de serviço"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Canal",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="void_service:close"
    )
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Services")
        if cog:
            await cog.fechar_canal_servico(interaction)

    @discord.ui.button(
        label="Gerar PIX",
        style=discord.ButtonStyle.green,
        emoji="💳",
        custom_id="void_service:pix"
    )
    async def gerar_pix(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão rápido para gerar o PIX do serviço"""
        if not PermissionChecker.is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas staff pode gerar PIX.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            "💳 Use `/pix-gerar` informando o valor e o cliente para gerar o PIX.",
            ephemeral=True
        )


# ====================================
# VIEWS DE CADA SERVIÇO
# ====================================

def criar_view_servico(service_id: str, service_name: str, opcoes: list) -> discord.ui.View:
    """
    Cria dinamicamente a view de um serviço com botões de preço.
    Cada botão abre o modal de informações do cliente.
    
    Args:
        service_id:   ID interno do serviço (ex: 'frutas')
        service_name: Nome exibido (ex: '🍎 Farm de Frutas')
        opcoes:       Lista de dicionários com 'nome' e 'preco'
    """
    view = discord.ui.View(timeout=None)

    for i, opcao in enumerate(opcoes):
        custom_id = f"service_{service_id}_{i}"

        btn = discord.ui.Button(
            label=f"{opcao['nome']} — R$ {opcao['preco']:.2f}",
            style=discord.ButtonStyle.blurple,
            custom_id=custom_id
        )

        # Capturar variáveis no closure
        def make_callback(sname, oname, oprice):
            async def callback(interaction: discord.Interaction):
                modal = ClientInfoModal(
                    service_name=sname,
                    option_name=oname,
                    price=oprice,
                    custom_id_suffix=custom_id
                )
                await interaction.response.send_modal(modal)
            return callback

        btn.callback = make_callback(service_name, opcao["nome"], opcao["preco"])
        view.add_item(btn)

    return view


# ====================================
# DADOS DOS SERVIÇOS E PREÇOS
# ====================================

SERVICOS = {
    "frutas": {
        "nome": "🍎 Farm de Frutas",
        "descricao": "Farm de frutas durante o tempo escolhido.",
        "cor": 0x9b59b6,
        "opcoes": [
            {"nome": "1 hora",   "preco": 3.00},
            {"nome": "2 horas",  "preco": 5.00},
            {"nome": "3 horas",  "preco": 7.00},
            {"nome": "5 horas",  "preco": 10.00},
            {"nome": "10 horas", "preco": 18.00},
        ]
    },
    "level": {
        "nome": "⭐ Farm de Level",
        "descricao": "Level up rápido e seguro no seu personagem.",
        "cor": 0x3498db,
        "opcoes": [
            {"nome": "+100 níveis",    "preco": 2.00},
            {"nome": "+300 níveis",    "preco": 5.00},
            {"nome": "+500 níveis",    "preco": 8.00},
            {"nome": "+1.000 níveis",  "preco": 14.00},
            {"nome": "Level Máximo",   "preco": 22.00},
        ]
    },
    "materiais": {
        "nome": "🧪 Farm de Materiais",
        "descricao": "Farm de materiais de todos os tipos.",
        "cor": 0x27ae60,
        "opcoes": [
            {"nome": "Comuns 100x",   "preco": 2.00},
            {"nome": "Incomuns 100x", "preco": 3.00},
            {"nome": "Raros 100x",    "preco": 5.00},
            {"nome": "Especiais 100x","preco": 7.00},
        ]
    },
    "v4": {
        "nome": "⚙️ V4 / Gear",
        "descricao": "Desbloqueie as engrenagens V4 do seu personagem.",
        "cor": 0xe74c3c,
        "opcoes": [
            {"nome": "Gear 1",                    "preco": 8.00},
            {"nome": "Gear 2",                    "preco": 8.00},
            {"nome": "Gear 3",                    "preco": 10.00},
            {"nome": "Gear 4",                    "preco": 12.00},
            {"nome": "V4 Completa (todas as Gears)","preco": 30.00},
        ]
    },
    "money": {
        "nome": "💵 Farm de Money",
        "descricao": "Farm de Beli (dinheiro) no Blox Fruits.",
        "cor": 0xf39c12,
        "opcoes": [
            {"nome": "5M Beli",  "preco": 4.00},
            {"nome": "10M Beli", "preco": 7.00},
            {"nome": "25M Beli", "preco": 15.00},
            {"nome": "50M Beli", "preco": 27.00},
        ]
    },
    "fragmentos": {
        "nome": "💎 Farm de Fragments",
        "descricao": "Farm de fragmentos para raças e upgrades.",
        "cor": 0x1abc9c,
        "opcoes": [
            {"nome": "5.000 Fragments",  "preco": 3.00},
            {"nome": "10.000 Fragments", "preco": 6.00},
            {"nome": "25.000 Fragments", "preco": 13.00},
            {"nome": "50.000 Fragments", "preco": 24.00},
        ]
    },
}


# ====================================
# COG PRINCIPAL
# ====================================

class Services(commands.Cog):
    """Sistema de serviços com fórum e preços específicos"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

        # Registrar views persistentes para cada serviço
        for service_id, data in SERVICOS.items():
            view = criar_view_servico(service_id, data["nome"], data["opcoes"])
            self.bot.add_view(view)

        # Registrar view de controle do canal
        self.bot.add_view(ServiceCloseView())

    # ====================================
    # COMANDOS PARA CRIAR PAINÉIS
    # ====================================

    @app_commands.command(
        name="painel-frutas",
        description="🍎 Cria o painel de Farm de Frutas no canal atual"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_frutas(self, interaction: discord.Interaction):
        await self._criar_painel(interaction, "frutas")

    @app_commands.command(
        name="painel-level",
        description="⭐ Cria o painel de Farm de Level no canal atual"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_level(self, interaction: discord.Interaction):
        await self._criar_painel(interaction, "level")

    @app_commands.command(
        name="painel-materiais",
        description="🧪 Cria o painel de Farm de Materiais no canal atual"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_materiais(self, interaction: discord.Interaction):
        await self._criar_painel(interaction, "materiais")

    @app_commands.command(
        name="painel-v4",
        description="⚙️ Cria o painel de V4 / Gear no canal atual"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_v4(self, interaction: discord.Interaction):
        await self._criar_painel(interaction, "v4")

    @app_commands.command(
        name="painel-money",
        description="💵 Cria o painel de Farm de Money no canal atual"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_money(self, interaction: discord.Interaction):
        await self._criar_painel(interaction, "money")

    @app_commands.command(
        name="painel-fragmentos",
        description="💎 Cria o painel de Farm de Fragments no canal atual"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_fragmentos(self, interaction: discord.Interaction):
        await self._criar_painel(interaction, "fragmentos")

    async def _criar_painel(self, interaction: discord.Interaction, service_id: str):
        """Cria o embed de preços com botões no canal atual"""

        data = SERVICOS[service_id]

        embed = discord.Embed(
            title=data["nome"],
            description=data["descricao"],
            color=data["cor"],
            timestamp=discord.utils.utcnow()
        )

        # Lista de preços
        precos_txt = ""
        for opcao in data["opcoes"]:
            precos_txt += f"➤ **{opcao['nome']}** — `R$ {opcao['preco']:.2f}`\n"

        embed.add_field(name="💰 Preços Disponíveis", value=precos_txt, inline=False)

        embed.add_field(
            name="📋 Como comprar",
            value=(
                "1. Clique no botão do valor desejado\n"
                "2. Preencha suas informações\n"
                "3. Um canal privado será aberto\n"
                "4. Realize o pagamento via PIX\n"
                "5. Receba seu serviço!"
            ),
            inline=False
        )

        embed.set_footer(text="🌑 VOID Store | Serviço rápido e seguro")

        view = criar_view_servico(service_id, data["nome"], data["opcoes"])

        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            f"✅ Painel de **{data['nome']}** criado!",
            ephemeral=True
        )

    # ====================================
    # CRIAR CANAL DO SERVIÇO
    # ====================================

    async def criar_canal_servico(
        self,
        interaction: discord.Interaction,
        service_name: str,
        option_name: str,
        price: float,
        nome_conta: str,
        nivel_atual: str,
        fruta_atual: str,
        senha_conta: str,
        observacoes: str
    ):
        """
        Cria o canal privado do serviço após o cliente
        preencher o modal de informações.
        """

        guild = interaction.guild
        user = interaction.user

        # Verificar categoria
        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            await interaction.followup.send(
                "❌ Categoria não configurada. Use `/setup`.", ephemeral=True
            )
            return

        category = guild.get_channel(category_id)
        if not category:
            await interaction.followup.send(
                "❌ Categoria não encontrada.", ephemeral=True
            )
            return

        # Verificar canal duplicado
        service_slug = service_name.lower().replace(" ", "-").replace("/", "").replace("🍎", "").replace("⭐", "").replace("🧪", "").replace("⚙️", "").replace("💵", "").replace("💎", "").strip()
        channel_name = f"servico-{service_slug[:20]}-{user.name}".lower()[:50]

        for ch in category.text_channels:
            if ch.name == channel_name:
                await interaction.followup.send(
                    f"⚠️ Você já possui um canal deste serviço aberto: {ch.mention}",
                    ephemeral=True
                )
                return

        try:
            # Permissões
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    attach_files=True
                ),
                guild.me: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    manage_channels=True,
                    manage_permissions=True
                )
            }

            if config.STAFF_ROLE_ID:
                staff_role = guild.get_role(config.STAFF_ROLE_ID)
                if staff_role:
                    overwrites[staff_role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True
                    )

            # Criar canal
            channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic=f"{service_name} | {option_name} | R$ {price:.2f} | {user}"
            )

            # Embed de boas-vindas
            embed = discord.Embed(
                title=f"🛒 Novo Pedido — {service_name}",
                description=f"Canal criado para {user.mention}",
                color=0x000000,
                timestamp=discord.utils.utcnow()
            )

            embed.add_field(
                name="📦 Serviço Solicitado",
                value=f"**{service_name}**\n{option_name}",
                inline=True
            )

            embed.add_field(
                name="💰 Valor",
                value=f"`R$ {price:.2f}`",
                inline=True
            )

            embed.add_field(name="\u200b", value="\u200b", inline=True)

            # Informações fornecidas pelo cliente
            embed.add_field(
                name="👤 Informações da Conta",
                value=(
                    f"**IGN:** `{nome_conta}`\n"
                    f"**Nível Atual:** `{nivel_atual}`\n"
                    f"**Fruta:** `{fruta_atual}`\n"
                    f"**Senha:** `{senha_conta if senha_conta != 'Não informado' else '🔒 Não informada'}`"
                ),
                inline=False
            )

            if observacoes and observacoes != "Nenhuma":
                embed.add_field(
                    name="📝 Observações",
                    value=observacoes,
                    inline=False
                )

            embed.add_field(
                name="📋 Próximos Passos",
                value=(
                    "1. ⏳ Aguarde um membro da equipe\n"
                    "2. 💳 Você receberá o código PIX\n"
                    "3. ✅ Após confirmação, o serviço será iniciado\n"
                    "4. 🎮 Receba seu serviço e avalie!"
                ),
                inline=False
            )

            embed.set_footer(text="🌑 VOID Store | Serviço rápido e seguro")

            # Mencionar staff e usuario
            staff_mention = f"<@&{config.STAFF_ROLE_ID}>" if config.STAFF_ROLE_ID else ""
            await channel.send(
                content=f"{user.mention} {staff_mention}",
                embed=embed,
                view=ServiceCloseView()
            )

            # Confirmar para o cliente
            await interaction.followup.send(
                f"✅ Seu canal de atendimento foi criado: {channel.mention}\n"
                f"Nossa equipe responderá em breve!",
                ephemeral=True
            )

            # Log
            await self.db.create_log(
                "service",
                user.id,
                "channel_created",
                f"Service: {service_name} | Option: {option_name} | Price: {price}"
            )

            logger.info(f"Service channel created: {service_name} | {option_name} | R${price} for {user}")

        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Sem permissão para criar canais.", ephemeral=True
            )
        except Exception as e:
            logger.error(f"Erro ao criar canal de serviço: {e}")
            await interaction.followup.send(
                "❌ Erro ao criar canal. Tente novamente.", ephemeral=True
            )

    # ====================================
    # FECHAR CANAL DO SERVIÇO
    # ====================================

    async def fechar_canal_servico(self, interaction: discord.Interaction):
        """Fecha e deleta o canal do serviço"""

        is_staff = PermissionChecker.is_staff(interaction.user)
        has_permission = interaction.channel.permissions_for(interaction.user).read_messages

        if not (is_staff or has_permission):
            await interaction.response.send_message(
                "❌ Você não pode fechar este canal.", ephemeral=True
            )
            return

        # Confirmação
        view = discord.ui.View()

        confirm_btn = discord.ui.Button(
            label="Confirmar Fechamento",
            style=discord.ButtonStyle.red,
            emoji="✅"
        )
        cancel_btn = discord.ui.Button(
            label="Cancelar",
            style=discord.ButtonStyle.gray,
            emoji="❌"
        )

        confirmado = False

        async def confirm_callback(i: discord.Interaction):
            nonlocal confirmado
            confirmado = True
            view.stop()
            await i.response.defer()

        async def cancel_callback(i: discord.Interaction):
            view.stop()
            await i.response.defer()

        confirm_btn.callback = confirm_callback
        cancel_btn.callback = cancel_callback

        view.add_item(confirm_btn)
        view.add_item(cancel_btn)

        await interaction.response.send_message(
            "⚠️ **Tem certeza que deseja fechar este canal?**",
            view=view,
            ephemeral=True
        )

        await view.wait()

        if confirmado:
            try:
                embed = discord.Embed(
                    title="🔒 Canal Fechado",
                    description=(
                        f"Canal fechado por {interaction.user.mention}.\n"
                        "Deletando em **5 segundos**..."
                    ),
                    color=0xff0000,
                    timestamp=discord.utils.utcnow()
                )

                await interaction.edit_original_response(
                    content="✅ Canal será fechado em instantes.",
                    view=None
                )

                await interaction.channel.send(embed=embed)

                await self.db.create_log(
                    "service",
                    interaction.user.id,
                    "channel_closed",
                    f"Channel: {interaction.channel.id}"
                )

                await asyncio.sleep(5)
                await interaction.channel.delete(
                    reason=f"Canal de serviço fechado por {interaction.user}"
                )

            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Erro ao fechar canal de serviço: {e}")
        else:
            await interaction.edit_original_response(
                content="❌ Fechamento cancelado.",
                view=None
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Services(bot))
