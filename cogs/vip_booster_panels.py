"""
🌑 VOID Store Bot - Painéis de VIP e Booster com Tickets
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio

from utils.permissions import PermissionChecker
from utils.logger import logger
from config import config


# ====================================
# MODAL DE COMPRA VIP
# ====================================

class VipCompraModal(discord.ui.Modal, title="Assinar Plano VIP"):
    """Modal de informações para compra do VIP"""

    nome_discord = discord.ui.TextInput(
        label="Seu nome no Discord",
        placeholder="Ex: João Silva",
        required=True,
        max_length=100
    )

    forma_pagamento = discord.ui.TextInput(
        label="Forma de pagamento preferida",
        placeholder="Ex: PIX",
        required=True,
        max_length=50
    )

    observacoes = discord.ui.TextInput(
        label="Alguma dúvida ou observação?",
        placeholder="Opcional — pergunte o que quiser",
        required=False,
        style=discord.TextStyle.long,
        max_length=300
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cog = interaction.client.get_cog("VipBoosterPanels")
        if cog:
            await cog.criar_canal_vip(
                interaction,
                self.nome_discord.value,
                self.forma_pagamento.value,
                self.observacoes.value or "Nenhuma"
            )


# ====================================
# MODAL DE COMPRA BOOSTER
# ====================================

class BoosterInfoModal(discord.ui.Modal, title="Boost — Tirar Dúvidas"):
    """Modal para canal de suporte sobre boost"""

    duvida = discord.ui.TextInput(
        label="Qual é sua dúvida sobre o Booster?",
        placeholder="Ex: Quais são os benefícios? Como funciona?",
        required=True,
        style=discord.TextStyle.long,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cog = interaction.client.get_cog("VipBoosterPanels")
        if cog:
            await cog.criar_canal_booster(interaction, self.duvida.value)


# ====================================
# VIEW DO PAINEL VIP
# ====================================

class VipPanelView(discord.ui.View):
    """Botões do painel VIP"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Assinar VIP — R$ 19,99/mês",
        style=discord.ButtonStyle.blurple,
        emoji="💎",
        custom_id="vip_panel:subscribe"
    )
    async def assinar_vip(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = VipCompraModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="Saber Mais",
        style=discord.ButtonStyle.gray,
        emoji="ℹ️",
        custom_id="vip_panel:info"
    )
    async def saber_mais(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="💎 Tudo sobre o VIP — VOID Store",
            description=(
                "O plano VIP é mensal e oferece os melhores benefícios da loja.\n\n"
                "**Renova todo mês por apenas R$ 19,99.**"
            ),
            color=0x9b59b6
        )
        embed.add_field(
            name="✨ Benefícios Completos",
            value=(
                "• 10% OFF em todos os serviços\n"
                "• 2× prioridade no atendimento\n"
                "• 1 pedido prioritário por mês\n"
                "• 2 promoções exclusivas por mês\n"
                "• 24h de acesso antecipado\n"
                "• Cargo VIP exclusivo no servidor\n"
                "• Convites para Eventos VIP\n"
                "• Canal exclusivo para VIPs"
            ),
            inline=False
        )
        embed.add_field(
            name="💰 Preço",
            value="`R$ 19,99 por mês`\nPagamento via PIX",
            inline=True
        )
        embed.add_field(
            name="🔄 Renovação",
            value="Mensal\nSem fidelidade",
            inline=True
        )
        embed.set_footer(text="🌑 VOID Store | Cancele quando quiser")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ====================================
# VIEW DO PAINEL BOOSTER
# ====================================

class BoosterPanelView(discord.ui.View):
    """Botões do painel Booster"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Ativar Benefícios Booster",
        style=discord.ButtonStyle.blurple,
        emoji="🚀",
        custom_id="booster_panel:activate"
    )
    async def ativar_booster(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Verifica se o usuário já é booster e abre canal"""
        cog = interaction.client.get_cog("VipBoosterPanels")
        if cog:
            await cog.verificar_e_ativar_booster(interaction)

    @discord.ui.button(
        label="Tirar Dúvidas",
        style=discord.ButtonStyle.gray,
        emoji="💬",
        custom_id="booster_panel:info"
    )
    async def tirar_duvidas(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = BoosterInfoModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="Benefícios Detalhados",
        style=discord.ButtonStyle.green,
        emoji="ℹ️",
        custom_id="booster_panel:benefits"
    )
    async def ver_beneficios(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🚀 Benefícios Booster — VOID Store",
            description=(
                "Ao dar **Boost** no servidor você ativa automaticamente\n"
                "os benefícios Booster da VOID Store!"
            ),
            color=0xf47fff
        )
        embed.add_field(
            name="🎁 O que você ganha",
            value=(
                "• 5% OFF em todos os serviços\n"
                "• Prioridade no atendimento\n"
                "• Acesso antecipado a promoções\n"
                "• 1 benefício surpresa por mês\n"
                "• Cargo Booster exclusivo\n"
                "• Participação em sorteios exclusivos\n"
                "• Prioridade em pedidos"
            ),
            inline=False
        )
        embed.add_field(
            name="⚡ Como ativar",
            value=(
                "1. Dê **Boost** no servidor\n"
                "2. Clique em **Ativar Benefícios Booster**\n"
                "3. Pronto! Seu cargo é dado automaticamente"
            ),
            inline=False
        )
        embed.set_footer(text="🌑 VOID Store | Boost = Benefícios imediatos")
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ====================================
# VIEW DE CONTROLE DOS CANAIS
# ====================================

class VipBoosterControlView(discord.ui.View):
    """Botões dentro dos canais VIP e Booster"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Canal",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="vipbooster:close"
    )
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("VipBoosterPanels")
        if cog:
            await cog.fechar_canal(interaction)

    @discord.ui.button(
        label="Gerar PIX",
        style=discord.ButtonStyle.green,
        emoji="💳",
        custom_id="vipbooster:pix"
    )
    async def pix(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not PermissionChecker.is_staff(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas staff.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "💳 Use `/pix-gerar valor:19.99 cliente:@usuario descricao:VIP Mensal`",
            ephemeral=True
        )


# ====================================
# COG
# ====================================

class VipBoosterPanels(commands.Cog):
    """Painéis e canais de VIP e Booster"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.bot.add_view(VipPanelView())
        self.bot.add_view(BoosterPanelView())
        self.bot.add_view(VipBoosterControlView())

    # ====================================
    # COMANDOS DE PAINEL
    # ====================================

    @app_commands.command(name="painel-vip", description="💎 Cria o painel do canal VIP")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_vip(self, interaction: discord.Interaction):
        """Cria o embed do canal VIP com botão de assinar"""

        embed = discord.Embed(
            title="💎 VOID Store — Plano VIP",
            description=(
                "Bem-vindo ao canal **VIP** da VOID Store! 🌑\n\n"
                "O plano VIP oferece os melhores benefícios da loja\n"
                "por apenas **R$ 19,99 por mês**."
            ),
            color=0x9b59b6,
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="✨ Benefícios Inclusos",
            value=(
                "💰 **10% OFF** em todos os serviços\n"
                "🎯 **2× prioridade** no atendimento\n"
                "📦 **1 pedido prioritário** por mês\n"
                "🏷️ **2 promoções exclusivas** por mês\n"
                "⏰ **24h** de acesso antecipado\n"
                "👑 **Cargo VIP** exclusivo no servidor\n"
                "🎉 **Eventos VIP** exclusivos\n"
                "📢 **Canal VIP** exclusivo"
            ),
            inline=False
        )

        embed.add_field(
            name="💳 Investimento",
            value="**R$ 19,99 / mês**\nPagamento via PIX\nSem fidelidade — cancele quando quiser",
            inline=True
        )

        embed.add_field(
            name="🔄 Renovação",
            value="Mensal\nAviso antes do vencimento",
            inline=True
        )

        embed.add_field(
            name="✅ Como assinar",
            value=(
                "1. Clique em **Assinar VIP** abaixo\n"
                "2. Preencha suas informações\n"
                "3. Um canal privado será aberto\n"
                "4. Pague o PIX e receba o cargo!"
            ),
            inline=False
        )

        embed.set_footer(text="🌑 VOID Store | VIP = Experiência Premium")

        await interaction.channel.send(embed=embed, view=VipPanelView())
        await interaction.response.send_message("✅ Painel VIP criado!", ephemeral=True)

    @app_commands.command(name="painel-booster", description="🚀 Cria o painel do canal Booster")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_booster(self, interaction: discord.Interaction):
        """Cria o embed do canal Booster"""

        embed = discord.Embed(
            title="🚀 VOID Store — Benefícios Booster",
            description=(
                "Obrigado por apoiar o servidor com **Nitro Boost**! 💜\n\n"
                "Boosters ganham benefícios exclusivos na VOID Store\n"
                "**automaticamente** ao dar boost no servidor."
            ),
            color=0xf47fff,
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="🎁 Benefícios Automáticos",
            value=(
                "🏷️ **5% OFF** em todos os serviços\n"
                "🎯 **Prioridade** no atendimento\n"
                "⏰ **Acesso antecipado** a promoções\n"
                "🎁 **1 benefício surpresa** por mês\n"
                "👑 **Cargo Booster** exclusivo\n"
                "🎰 **Sorteios exclusivos** para boosters\n"
                "📦 **Prioridade** em pedidos"
            ),
            inline=False
        )

        embed.add_field(
            name="⚡ Como funciona",
            value=(
                "1. Dê **Boost** neste servidor\n"
                "2. Clique em **Ativar Benefícios**\n"
                "3. O cargo é verificado e concedido\n"
                "4. Aproveite todos os benefícios!"
            ),
            inline=False
        )

        embed.add_field(
            name="❓ Dúvidas?",
            value="Clique em **Tirar Dúvidas** para falar com a equipe.",
            inline=False
        )

        embed.set_footer(text="🌑 VOID Store | Boost = Benefícios imediatos e automáticos")

        await interaction.channel.send(embed=embed, view=BoosterPanelView())
        await interaction.response.send_message("✅ Painel Booster criado!", ephemeral=True)

    # ====================================
    # CRIAR CANAIS
    # ====================================

    async def criar_canal_vip(
        self,
        interaction: discord.Interaction,
        nome: str,
        forma_pag: str,
        obs: str
    ):
        """Cria canal privado para assinatura VIP"""

        guild = interaction.guild
        user = interaction.user

        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            await interaction.followup.send(
                "❌ Categoria não configurada.", ephemeral=True
            )
            return

        category = guild.get_channel(category_id)
        if not category:
            await interaction.followup.send("❌ Categoria não encontrada.", ephemeral=True)
            return

        channel_name = f"vip-{user.name}".lower()[:50]

        for ch in category.text_channels:
            if ch.name == channel_name:
                await interaction.followup.send(
                    f"⚠️ Você já tem um canal VIP aberto: {ch.mention}",
                    ephemeral=True
                )
                return

        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
            }

            if config.STAFF_ROLE_ID:
                role = guild.get_role(config.STAFF_ROLE_ID)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            for role_id in config.AUTHORIZED_ROLE_IDS:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic=f"Assinatura VIP | Cliente: {user}"
            )

            embed = discord.Embed(
                title="💎 Nova Assinatura VIP",
                description=f"Canal criado para {user.mention}",
                color=0x9b59b6,
                timestamp=discord.utils.utcnow()
            )

            embed.add_field(
                name="👤 Dados do Cliente",
                value=(
                    f"**Discord:** {user.mention}\n"
                    f"**Nome:** {nome}\n"
                    f"**Pagamento:** {forma_pag}"
                ),
                inline=True
            )

            embed.add_field(
                name="💰 Valor",
                value="`R$ 19,99/mês`",
                inline=True
            )

            if obs and obs != "Nenhuma":
                embed.add_field(name="💬 Observações", value=obs, inline=False)

            embed.add_field(
                name="📋 Próximos Passos",
                value=(
                    "1. ⏳ Aguarde a equipe\n"
                    "2. 💳 Receba o PIX de R$ 19,99\n"
                    "3. ✅ Pague e envie o comprovante\n"
                    "4. 💎 Receba o cargo VIP!"
                ),
                inline=False
            )

            embed.set_footer(text="🌑 VOID Store | Bem-vindo ao VIP!")

            staff_mention = f"<@&{config.STAFF_ROLE_ID}>" if config.STAFF_ROLE_ID else ""
            await channel.send(
                content=f"{user.mention} {staff_mention}",
                embed=embed,
                view=VipBoosterControlView()
            )

            await interaction.followup.send(
                f"✅ Canal VIP criado: {channel.mention}\nAgora aguarde nossa equipe!",
                ephemeral=True
            )

            await self.db.create_log(
                "vip", user.id, "buy_channel_created",
                f"Channel: {channel.id}"
            )

            logger.info(f"VIP channel created for {user}")

        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão para criar canais.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro ao criar canal VIP: {e}")
            await interaction.followup.send("❌ Erro ao criar canal.", ephemeral=True)

    async def verificar_e_ativar_booster(self, interaction: discord.Interaction):
        """Verifica se o usuário é booster e abre canal"""

        user = interaction.user

        # Verificar se é booster
        if user.premium_since is None:
            await interaction.response.send_message(
                "❌ **Você não está dando boost neste servidor.**\n\n"
                "Para ativar os benefícios Booster, você precisa dar **Boost** no servidor primeiro.\n"
                "Após dar boost, clique novamente neste botão.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            await interaction.followup.send("❌ Categoria não configurada.", ephemeral=True)
            return

        category = guild.get_channel(category_id)
        if not category:
            await interaction.followup.send("❌ Categoria não encontrada.", ephemeral=True)
            return

        channel_name = f"booster-{user.name}".lower()[:50]

        for ch in category.text_channels:
            if ch.name == channel_name:
                await interaction.followup.send(
                    f"⚠️ Você já tem um canal Booster aberto: {ch.mention}",
                    ephemeral=True
                )
                return

        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
            }

            if config.STAFF_ROLE_ID:
                role = guild.get_role(config.STAFF_ROLE_ID)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            for role_id in config.AUTHORIZED_ROLE_IDS:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic=f"Ativação Booster | Cliente: {user}"
            )

            embed = discord.Embed(
                title="🚀 Ativação de Benefícios Booster",
                description=f"{user.mention} está dando boost e quer ativar os benefícios!",
                color=0xf47fff,
                timestamp=discord.utils.utcnow()
            )

            embed.add_field(
                name="✅ Boost Confirmado",
                value=f"Boosting desde: `{user.premium_since.strftime('%d/%m/%Y')}`",
                inline=False
            )

            embed.add_field(
                name="🎁 Benefícios a Ativar",
                value=(
                    "• 5% OFF em todos os serviços\n"
                    "• Prioridade no atendimento\n"
                    "• Cargo Booster exclusivo\n"
                    "• Acesso antecipado a promoções\n"
                    "• Sorteios exclusivos"
                ),
                inline=False
            )

            embed.add_field(
                name="📋 Próximos Passos",
                value=(
                    "1. ⏳ Aguarde a equipe\n"
                    "2. 🚀 O cargo será verificado e concedido\n"
                    "3. 🎉 Aproveite os benefícios!"
                ),
                inline=False
            )

            embed.set_footer(text="🌑 VOID Store | Obrigado pelo Boost! 💜")

            staff_mention = f"<@&{config.STAFF_ROLE_ID}>" if config.STAFF_ROLE_ID else ""
            await channel.send(
                content=f"{user.mention} {staff_mention}",
                embed=embed,
                view=VipBoosterControlView()
            )

            await interaction.followup.send(
                f"✅ Canal criado: {channel.mention}\n"
                f"A equipe confirmará e ativará seu cargo Booster em breve!",
                ephemeral=True
            )

            await self.db.create_log(
                "booster", user.id, "activation_channel_created",
                f"Channel: {channel.id}"
            )

            logger.info(f"Booster activation channel created for {user}")

        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão para criar canais.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro ao criar canal booster: {e}")

    async def criar_canal_booster(self, interaction: discord.Interaction, duvida: str):
        """Cria canal de suporte para dúvidas sobre booster"""

        guild = interaction.guild
        user = interaction.user

        category_id = config.TICKET_CATEGORY_ID
        if not category_id:
            await interaction.followup.send("❌ Categoria não configurada.", ephemeral=True)
            return

        category = guild.get_channel(category_id)
        if not category:
            await interaction.followup.send("❌ Categoria não encontrada.", ephemeral=True)
            return

        channel_name = f"duvida-booster-{user.name}".lower()[:50]

        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
            }

            if config.STAFF_ROLE_ID:
                role = guild.get_role(config.STAFF_ROLE_ID)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            channel = await category.create_text_channel(
                name=channel_name,
                overwrites=overwrites
            )

            embed = discord.Embed(
                title="🚀 Dúvida sobre Booster",
                description=f"{user.mention} tem uma dúvida sobre o sistema Booster.",
                color=0xf47fff,
                timestamp=discord.utils.utcnow()
            )

            embed.add_field(name="❓ Dúvida", value=duvida, inline=False)
            embed.set_footer(text="🌑 VOID Store | A equipe responderá em breve")

            staff_mention = f"<@&{config.STAFF_ROLE_ID}>" if config.STAFF_ROLE_ID else ""
            await channel.send(
                content=f"{user.mention} {staff_mention}",
                embed=embed,
                view=VipBoosterControlView()
            )

            await interaction.followup.send(
                f"✅ Canal criado: {channel.mention}", ephemeral=True
            )

        except Exception as e:
            logger.error(f"Erro ao criar canal booster dúvida: {e}")

    # ====================================
    # FECHAR CANAL
    # ====================================

    async def fechar_canal(self, interaction: discord.Interaction):
        """Fecha qualquer canal VIP/Booster"""

        is_staff = PermissionChecker.is_staff(interaction.user)
        is_creator = interaction.channel.permissions_for(interaction.user).read_messages

        if not (is_staff or is_creator):
            await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
            return

        view = discord.ui.View()
        confirm = discord.ui.Button(label="Confirmar", style=discord.ButtonStyle.red)
        cancel = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.gray)
        confirmado = False

        async def c1(i: discord.Interaction):
            nonlocal confirmado
            confirmado = True
            view.stop()
            await i.response.defer()

        async def c2(i: discord.Interaction):
            view.stop()
            await i.response.defer()

        confirm.callback = c1
        cancel.callback = c2
        view.add_item(confirm)
        view.add_item(cancel)

        await interaction.response.send_message(
            "⚠️ Fechar este canal?", view=view, ephemeral=True
        )
        await view.wait()

        if confirmado:
            try:
                await interaction.edit_original_response(content="✅ Fechando...", view=None)
                embed = discord.Embed(
                    description=f"🔒 Canal fechado por {interaction.user.mention}. Deletando em 5s...",
                    color=0xff0000
                )
                await interaction.channel.send(embed=embed)
                await asyncio.sleep(5)
                await interaction.channel.delete()
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Erro ao fechar canal: {e}")
        else:
            await interaction.edit_original_response(content="❌ Cancelado.", view=None)


async def setup(bot: commands.Bot):
    await bot.add_cog(VipBoosterPanels(bot))
