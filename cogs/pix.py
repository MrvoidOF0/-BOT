"""
🌑 VOID Store Bot - Sistema PIX Corrigido
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime

from utils.embeds import VoidEmbeds
from utils.permissions import PermissionChecker
from utils.helpers import format_currency
from utils.logger import logger


class Pix(commands.Cog):
    """Sistema de pagamento PIX"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    async def _get_pix(self) -> dict:
        """Busca os dados do PIX no banco de dados"""
        return {
            "key":  await self.db.get_config("pix_key")  or "",
            "name": await self.db.get_config("pix_name") or "",
            "city": await self.db.get_config("pix_city") or "",
            "bank": await self.db.get_config("pix_bank") or "",
        }

    def _txid(self) -> str:
        return f"VOID{datetime.now().strftime('%Y%m%d%H%M%S')}"

    @app_commands.command(name="pix-configurar", description="💳 Configura sua chave PIX")
    @app_commands.describe(
        chave="Sua chave PIX (email, CPF, telefone ou chave aleatória)",
        nome="Seu nome completo (como no banco)",
        cidade="Sua cidade (como no banco)",
        banco="Seu banco (ex: Nubank, Inter)"
    )
    async def pix_configurar(
        self,
        interaction: discord.Interaction,
        chave: str,
        nome: str,
        cidade: str,
        banco: str
    ):
        if not await PermissionChecker.check_interaction_permissions(interaction, require_admin=True):
            return

        await self.db.set_config("pix_key",  chave.strip())
        await self.db.set_config("pix_name", nome.strip())
        await self.db.set_config("pix_city", cidade.strip())
        await self.db.set_config("pix_bank", banco.strip())

        embed = VoidEmbeds.success(
            "PIX Configurado",
            f"🔑 **Chave:** `{chave}`\n"
            f"👤 **Titular:** {nome}\n"
            f"🏙️ **Cidade:** {cidade}\n"
            f"🏦 **Banco:** {banco}"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"PIX configured by {interaction.user}")

    @app_commands.command(name="pix-gerar", description="💳 Gera cobrança PIX para o cliente")
    @app_commands.describe(
        valor="Valor a cobrar (ex: 29.90)",
        cliente="O membro que vai pagar",
        descricao="Descrição do serviço (opcional)"
    )
    async def pix_gerar(
        self,
        interaction: discord.Interaction,
        valor: float,
        cliente: discord.Member,
        descricao: Optional[str] = None
    ):
        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        pix = await self._get_pix()

        if not pix["key"]:
            await interaction.response.send_message(
                "❌ **PIX não configurado!**\n"
                "Use `/pix-configurar chave:... nome:... cidade:... banco:...` primeiro.",
                ephemeral=True
            )
            return

        if valor <= 0:
            await interaction.response.send_message(
                "❌ O valor deve ser maior que R$ 0,00.", ephemeral=True
            )
            return

        txid = self._txid()

        embed = discord.Embed(
            title="💳 Pagamento via PIX",
            description=f"Olá {cliente.mention}! Segue abaixo os dados para pagamento:",
            color=0x00c853,
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="🔑 Chave PIX (Copia e Cola)",
            value=f"```{pix['key']}```",
            inline=False
        )

        embed.add_field(
            name="💰 Valor Exato",
            value=f"`R$ {valor:.2f}`",
            inline=True
        )

        embed.add_field(
            name="🆔 ID do Pagamento",
            value=f"`{txid}`",
            inline=True
        )

        embed.add_field(
            name="👤 Recebedor",
            value=f"{pix['name']} — {pix['bank']}",
            inline=True
        )

        embed.add_field(
            name="📱 Como pagar",
            value=(
                "1. Abra o app do seu banco\n"
                "2. Vá em **PIX → Copia e Cola**\n"
                f"3. Cole: `{pix['key']}`\n"
                f"4. Confirme o valor: **R$ {valor:.2f}**\n"
                "5. Pague e envie o **comprovante aqui**"
            ),
            inline=False
        )

        embed.add_field(
            name="📦 Serviço",
            value=descricao or "Serviço VOID Store",
            inline=False
        )

        embed.set_footer(text=f"🌑 VOID Store | ID: {txid}")

        await interaction.response.send_message(embed=embed)

        await self.db.create_log(
            "pix", interaction.user.id, "generated",
            f"TXID: {txid} | Amount: {valor} | Client: {cliente.id}"
        )

        logger.info(f"PIX generated: R${valor} | TXID: {txid} | For: {cliente}")

    @app_commands.command(name="pix-confirmar", description="✅ Confirma pagamento PIX recebido")
    @app_commands.describe(
        cliente="Quem pagou",
        valor="Valor que foi pago",
        txid="ID do pagamento (opcional)"
    )
    async def pix_confirmar(
        self,
        interaction: discord.Interaction,
        cliente: discord.Member,
        valor: float,
        txid: Optional[str] = None
    ):
        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        await interaction.response.defer()

        user = await self.db.get_user(cliente.id)
        if not user:
            await self.db.create_user(cliente.id, str(cliente))

        await self.db.update_user_spent(cliente.id, valor)

        roles_cog = self.bot.get_cog("Roles")
        novo_tier = None
        if roles_cog:
            novo_tier = await roles_cog.check_user_tier(cliente)

        updated = await self.db.get_user(cliente.id)

        embed = VoidEmbeds.success(
            "Pagamento Confirmado! ✅",
            f"💰 **Valor:** {format_currency(valor)}\n"
            f"👤 **Cliente:** {cliente.mention}\n"
            f"🆔 **TXID:** `{txid or 'N/A'}`\n"
            f"✅ **Confirmado por:** {interaction.user.mention}\n"
            f"📊 **Total acumulado:** {format_currency(updated.total_spent)}"
        )

        if novo_tier:
            embed.add_field(
                name="🎉 Novo Cargo!",
                value=f"Cliente atingiu o nível **{novo_tier}**!",
                inline=False
            )

        await interaction.followup.send(embed=embed)

        try:
            dm = VoidEmbeds.success(
                "Pagamento Confirmado! ✅",
                f"Seu pagamento de **{format_currency(valor)}** foi confirmado!\n"
                f"Obrigado pela confiança na VOID Store! 🌑"
            )
            await cliente.send(embed=dm)
        except discord.Forbidden:
            pass

        await self.db.create_log(
            "pix", interaction.user.id, "confirmed",
            f"TXID: {txid} | Amount: {valor} | Client: {cliente.id}"
        )

    @app_commands.command(name="pix-info", description="ℹ️ Mostra sua chave PIX configurada")
    async def pix_info(self, interaction: discord.Interaction):
        if not await PermissionChecker.check_interaction_permissions(interaction, require_admin=True):
            return

        pix = await self._get_pix()

        if not pix["key"]:
            await interaction.response.send_message(
                "⚠️ PIX ainda não configurado.\nUse `/pix-configurar`.",
                ephemeral=True
            )
            return

        embed = discord.Embed(title="💳 PIX Configurado", color=0x000000)
        embed.add_field(name="🔑 Chave",  value=f"`{pix['key']}`",  inline=False)
        embed.add_field(name="👤 Titular", value=pix["name"],         inline=True)
        embed.add_field(name="🏙️ Cidade", value=pix["city"],         inline=True)
        embed.add_field(name="🏦 Banco",   value=pix["bank"],         inline=True)
        embed.set_footer(text="🌑 VOID Store | Visível apenas para admins")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Pix(bot))
