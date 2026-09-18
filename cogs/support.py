"""
🌑 VOID Store Bot - Canal de Suporte Dedicado
Ticket de suporte separado de compras e serviços.
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio

from utils.permissions import PermissionChecker
from utils.logger import logger
from config import config


# ====================================
# MODAL DE SUPORTE
# ====================================

class SuporteModal(discord.ui.Modal, title="Abrir Ticket de Suporte"):

    assunto = discord.ui.TextInput(
        label="Assunto do suporte",
        placeholder="Ex: Problema com entrega, Dúvida sobre serviço...",
        required=True,
        max_length=100
    )

    descricao = discord.ui.TextInput(
        label="Descreva seu problema ou dúvida",
        placeholder="Explique com detalhes o que aconteceu ou o que precisa",
        required=True,
        style=discord.TextStyle.long,
        max_length=1000
    )

    pedido_id = discord.ui.TextInput(
        label="ID do pedido (se relacionado)",
        placeholder="Ex: VOID-0001 ou deixe vazio",
        required=False,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cog = interaction.client.get_cog("Support")
        if cog:
            await cog.criar_canal_suporte(
                interaction,
                self.assunto.value,
                self.descricao.value,
                self.pedido_id.value or "Não informado"
            )


# ====================================
# VIEW DO PAINEL DE SUPORTE
# ====================================

class SupportPanelView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Abrir Ticket de Suporte",
        style=discord.ButtonStyle.blurple,
        emoji="💬",
        custom_id="support_panel:open"
    )
    async def abrir_suporte(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = SuporteModal()
        await interaction.response.send_modal(modal)


# ====================================
# VIEW DE CONTROLE DO TICKET DE SUPORTE
# ====================================

class SupportControlView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Ticket",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="support:close"
    )
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = interaction.client.get_cog("Support")
        if cog:
            await cog.fechar_ticket_suporte(interaction)

    @discord.ui.button(
        label="Assumir",
        style=discord.ButtonStyle.green,
        emoji="🙋",
        custom_id="support:claim"
    )
    async def assumir(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not PermissionChecker.is_staff(interaction.user):
            await interaction.response.send_message("❌ Apenas staff.", ephemeral=True)
            return
        embed = discord.Embed(
            description=f"✅ {interaction.user.mention} assumiu este ticket.",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed)


# ====================================
# COG
# ====================================

class Support(commands.Cog):
    """Sistema de suporte dedicado"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.bot.add_view(SupportPanelView())
        self.bot.add_view(SupportControlView())

    @app_commands.command(name="painel-suporte", description="💬 Cria o painel de suporte dedicado")
    @app_commands.checks.has_permissions(administrator=True)
    async def painel_suporte(self, interaction: discord.Interaction):
        """Cria o embed do canal de suporte"""

        embed = discord.Embed(
            title="💬 VOID Store — Suporte",
            description=(
                "Precisa de ajuda? Estamos aqui! 🌑\n\n"
                "Clique no botão abaixo para abrir um **ticket de suporte privado**.\n"
                "Nossa equipe responderá o mais rápido possível."
            ),
            color=0x5865f2,
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="📋 Quando usar o suporte",
            value=(
                "• Problemas com pedidos ou entregas\n"
                "• Dúvidas sobre serviços\n"
                "• Reclamações ou sugestões\n"
                "• Qualquer outro assunto"
            ),
            inline=False
        )

        embed.add_field(
            name="⏱️ Tempo de resposta",
            value="Geralmente em até **30 minutos** durante horário ativo.",
            inline=False
        )

        embed.set_footer(text="🌑 VOID Store | Suporte rápido e eficiente")

        await interaction.channel.send(embed=embed, view=SupportPanelView())
        await interaction.response.send_message("✅ Painel de suporte criado!", ephemeral=True)

    async def criar_canal_suporte(
        self,
        interaction: discord.Interaction,
        assunto: str,
        descricao: str,
        pedido_id: str
    ):
        """Cria canal privado de suporte"""

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

        channel_name = f"suporte-{user.name}".lower()[:50]

        for ch in category.text_channels:
            if ch.name == channel_name:
                await interaction.followup.send(
                    f"⚠️ Você já tem um ticket de suporte aberto: {ch.mention}",
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
                topic=f"Suporte | {assunto} | {user}"
            )

            embed = discord.Embed(
                title="💬 Ticket de Suporte",
                description=f"Suporte aberto por {user.mention}",
                color=0x5865f2,
                timestamp=discord.utils.utcnow()
            )

            embed.add_field(name="📌 Assunto", value=assunto, inline=False)
            embed.add_field(name="📝 Descrição", value=descricao, inline=False)

            if pedido_id != "Não informado":
                embed.add_field(name="🆔 ID do Pedido", value=f"`{pedido_id}`", inline=True)

            embed.add_field(
                name="⏱️ Próximos Passos",
                value="Aguarde a equipe. Responderemos em breve!",
                inline=False
            )

            embed.set_footer(text="🌑 VOID Store | Suporte dedicado")

            staff_mention = f"<@&{config.STAFF_ROLE_ID}>" if config.STAFF_ROLE_ID else ""
            await channel.send(
                content=f"{user.mention} {staff_mention}",
                embed=embed,
                view=SupportControlView()
            )

            await interaction.followup.send(
                f"✅ Ticket de suporte criado: {channel.mention}",
                ephemeral=True
            )

            await self.db.create_log(
                "support", user.id, "ticket_created",
                f"Subject: {assunto} | Channel: {channel.id}"
            )

            logger.info(f"Support ticket created for {user}: {assunto}")

        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão para criar canais.", ephemeral=True)
        except Exception as e:
            logger.error(f"Erro ao criar ticket de suporte: {e}")
            await interaction.followup.send("❌ Erro ao criar ticket.", ephemeral=True)

    async def fechar_ticket_suporte(self, interaction: discord.Interaction):
        """Fecha ticket de suporte"""

        is_staff = PermissionChecker.is_staff(interaction.user)
        is_creator = interaction.channel.topic and str(interaction.user) in interaction.channel.topic

        if not (is_staff or is_creator):
            await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)
            return

        view = discord.ui.View()
        confirm = discord.ui.Button(label="Confirmar", style=discord.ButtonStyle.red)
        cancel = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.gray)
        confirmado = False

        async def c1(i):
            nonlocal confirmado
            confirmado = True
            view.stop()
            await i.response.defer()

        async def c2(i):
            view.stop()
            await i.response.defer()

        confirm.callback = c1
        cancel.callback = c2
        view.add_item(confirm)
        view.add_item(cancel)

        await interaction.response.send_message(
            "⚠️ Fechar este ticket de suporte?",
            view=view,
            ephemeral=True
        )
        await view.wait()

        if confirmado:
            try:
                await interaction.edit_original_response(content="✅ Fechando...", view=None)
                embed = discord.Embed(
                    description=f"🔒 Ticket fechado por {interaction.user.mention}. Deletando em 5s...",
                    color=0xff0000
                )
                await interaction.channel.send(embed=embed)
                await self.db.create_log(
                    "support", interaction.user.id, "ticket_closed",
                    f"Channel: {interaction.channel.id}"
                )
                await asyncio.sleep(5)
                await interaction.channel.delete()
            except discord.NotFound:
                pass
            except Exception as e:
                logger.error(f"Erro ao fechar suporte: {e}")
        else:
            await interaction.edit_original_response(content="❌ Cancelado.", view=None)


async def setup(bot: commands.Bot):
    await bot.add_cog(Support(bot))
