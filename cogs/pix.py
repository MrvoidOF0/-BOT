"""
🌑 VOID Store Bot - Sistema de Pagamento PIX
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime

from utils.embeds import VoidEmbeds
from utils.permissions import PermissionChecker
from utils.constants import Emojis
from utils.helpers import format_currency
from utils.logger import logger


class Pix(commands.Cog):
    """Sistema de pagamento PIX"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    # ====================================
    # HELPER: BUSCAR DADOS DO PIX
    # ====================================

    async def _get_pix_data(self) -> dict:
        """
        Busca os dados do PIX salvos no banco.
        Retorna um dicionário com os dados ou valores vazios.
        """
        return {
            "key":  await self.db.get_config("pix_key")  or "",
            "name": await self.db.get_config("pix_name") or "",
            "city": await self.db.get_config("pix_city") or "",
            "bank": await self.db.get_config("pix_bank") or "",
        }

    def _gerar_txid(self) -> str:
        """
        Gera um ID único para identificar o pagamento.
        Formato: VOID + data e hora atual
        Exemplo: VOID20241215143022
        """
        return f"VOID{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def _gerar_codigo_pix(self, chave: str, valor: float, txid: str) -> str:
        """
        Monta o texto do código PIX copia e cola.

        IMPORTANTE:
        Este é o código que o cliente vai copiar e colar
        no aplicativo do banco dele para pagar.
        A chave PIX é o que direciona o pagamento para VOCÊ.

        Args:
            chave: Sua chave PIX (email, cpf, telefone...)
            valor: Valor em reais que o cliente vai pagar
            txid:  Código único deste pagamento específico
        """
        return (
            f"**Chave PIX:** `{chave}`\n\n"
            f"💰 **Valor exato:** `R$ {valor:.2f}`\n"
            f"🆔 **ID do pagamento:** `{txid}`\n\n"
            f"📱 **Como pagar:**\n"
            f"1. Abra o aplicativo do seu banco\n"
            f"2. Vá em **PIX → Copia e Cola**\n"
            f"3. Cole a chave acima\n"
            f"4. Confirme que o valor é **R$ {valor:.2f}**\n"
            f"5. Finalize o pagamento\n"
            f"6. Tire **print do comprovante** e envie aqui"
        )

    # ====================================
    # COMANDOS
    # ====================================

    @app_commands.command(
        name="pix-configurar",
        description="💳 Configura os dados do PIX da loja (apenas admin)"
    )
    @app_commands.describe(
        chave="Sua chave PIX: email, CPF, telefone ou chave aleatória",
        nome="Seu nome completo como está cadastrado no banco",
        cidade="Sua cidade como está cadastrada no banco",
        banco="Nome do seu banco (ex: Nubank, Inter, Itaú)"
    )
    async def pix_configurar(
        self,
        interaction: discord.Interaction,
        chave: str,
        nome: str,
        cidade: str,
        banco: str
    ):
        """
        Configura sua chave PIX no bot.
        Só precisa fazer isso UMA VEZ.
        """

        if not await PermissionChecker.check_interaction_permissions(
            interaction, require_admin=True
        ):
            return

        # Salvar cada dado no banco
        await self.db.set_config("pix_key",  chave)
        await self.db.set_config("pix_name", nome)
        await self.db.set_config("pix_city", cidade)
        await self.db.set_config("pix_bank", banco)

        embed = VoidEmbeds.success(
            "PIX Configurado com Sucesso",
            f"Os dados do PIX foram salvos!\n\n"
            f"🔑 **Chave PIX:** `{chave}`\n"
            f"👤 **Titular:** {nome}\n"
            f"🏙️ **Cidade:** {cidade}\n"
            f"🏦 **Banco:** {banco}\n\n"
            f"ℹ️ Agora você pode usar `/pix-gerar` dentro dos canais de compra."
        )

        # Resposta visível apenas para o admin
        await interaction.response.send_message(embed=embed, ephemeral=True)

        logger.info(f"PIX configured by {interaction.user}")

    # ──────────────────────────────────────

    @app_commands.command(
        name="pix-gerar",
        description="💳 Gera a cobrança PIX para o cliente pagar"
    )
    @app_commands.describe(
        valor="Valor que o cliente vai pagar (ex: 29.90)",
        cliente="O membro do Discord que vai pagar",
        descricao="Descrição do produto/serviço (opcional)"
    )
    async def pix_gerar(
        self,
        interaction: discord.Interaction,
        valor: float,
        cliente: discord.Member,
        descricao: Optional[str] = None
    ):
        """
        Envia a cobrança PIX no canal atual.
        Use dentro do canal de compra do cliente.
        """

        if not await PermissionChecker.check_interaction_permissions(
            interaction, require_staff=True
        ):
            return

        # Verificar se o PIX está configurado
        pix = await self._get_pix_data()

        if not pix["key"]:
            await interaction.response.send_message(
                f"{Emojis.ERROR} **PIX não configurado!**\n"
                f"Peça a um administrador para usar:\n"
                f"`/pix-configurar chave:... nome:... cidade:... banco:...`",
                ephemeral=True
            )
            return

        if valor <= 0:
            await interaction.response.send_message(
                f"{Emojis.ERROR} O valor deve ser maior que R$ 0,00.",
                ephemeral=True
            )
            return

        # Gerar ID único do pagamento
        txid = self._gerar_txid()

        # Montar texto do PIX
        pix_texto = self._gerar_codigo_pix(pix["key"], valor, txid)

        # Criar embed que será enviado no canal
        embed = discord.Embed(
            title="💳 Pagamento via PIX",
            description=(
                f"{cliente.mention}, sua cobrança foi gerada!\n\n"
                f"{pix_texto}"
            ),
            color=0x00c853,  # Verde
            timestamp=discord.utils.utcnow()
        )

        # Informações do recebedor (você)
        embed.add_field(
            name="👤 Dados do Recebedor",
            value=(
                f"**Nome:** {pix['name']}\n"
                f"**Banco:** {pix['bank']}\n"
                f"**Cidade:** {pix['city']}"
            ),
            inline=True
        )

        # Informações do pagamento
        embed.add_field(
            name="📋 Detalhes do Pedido",
            value=(
                f"**Produto:** {descricao or 'VOID Store'}\n"
                f"**Valor:** {format_currency(valor)}\n"
                f"**ID:** `{txid}`"
            ),
            inline=True
        )

        embed.add_field(
            name="⚠️ Atenção",
            value=(
                f"• Pague **exatamente** {format_currency(valor)}\n"
                f"• Envie o comprovante **neste canal**\n"
                f"• O serviço será iniciado após confirmação\n"
                f"• **Não feche** este canal antes de pagar"
            ),
            inline=False
        )

        embed.set_footer(text=f"🌑 VOID Store | ID: {txid}")

        # Salvar pagamento pendente no banco
        await self.db.create_log(
            "pix",
            interaction.user.id,
            "generated",
            f"TXID: {txid} | Amount: {valor} | Client: {cliente.id}"
        )

        # Enviar no canal de forma pública (todos do canal veem)
        await interaction.response.send_message(embed=embed)

        logger.info(f"PIX generated: R${valor} | TXID: {txid} | Client: {cliente} | Staff: {interaction.user}")

    # ──────────────────────────────────────

    @app_commands.command(
        name="pix-confirmar",
        description="✅ Confirma que o pagamento PIX foi recebido"
    )
    @app_commands.describe(
        cliente="O membro que realizou o pagamento",
        valor="Valor que foi pago",
        txid="ID do pagamento (VOID...)"
    )
    async def pix_confirmar(
        self,
        interaction: discord.Interaction,
        cliente: discord.Member,
        valor: float,
        txid: Optional[str] = None
    ):
        """
        Confirma o recebimento do pagamento.
        Isso registra a compra no histórico do cliente
        e atualiza o cargo de progressão automaticamente.
        """

        if not await PermissionChecker.check_interaction_permissions(
            interaction, require_staff=True
        ):
            return

        await interaction.response.defer()

        # Garantir que o cliente existe no banco
        user = await self.db.get_user(cliente.id)
        if not user:
            await self.db.create_user(cliente.id, str(cliente))

        # Adicionar o valor ao histórico de compras do cliente
        await self.db.update_user_spent(cliente.id, valor)

        # Verificar se o cliente subiu de tier e atualizar cargo
        roles_cog = self.bot.get_cog("Roles")
        novo_tier = None
        if roles_cog:
            novo_tier = await roles_cog.check_user_tier(cliente)

        # Buscar total atualizado
        updated_user = await self.db.get_user(cliente.id)

        # Montar embed de confirmação
        embed = VoidEmbeds.success(
            "Pagamento Confirmado! ✅",
            f"O pagamento de {cliente.mention} foi **confirmado e registrado**!\n\n"
            f"💰 **Valor pago:** {format_currency(valor)}\n"
            f"🆔 **TXID:** `{txid or 'Não informado'}`\n"
            f"👤 **Cliente:** {cliente.mention}\n"
            f"✅ **Confirmado por:** {interaction.user.mention}\n"
            f"📊 **Total acumulado:** {format_currency(updated_user.total_spent)}"
        )

        # Se subiu de tier, avisar
        if novo_tier:
            embed.add_field(
                name=f"{Emojis.CROWN} Novo Cargo Desbloqueado!",
                value=f"O cliente atingiu o nível **{novo_tier}**! Cargo atribuído automaticamente.",
                inline=False
            )

        await interaction.followup.send(embed=embed)

        # Notificar o cliente por DM
        try:
            dm_embed = VoidEmbeds.success(
                "Pagamento Confirmado! ✅",
                f"Seu pagamento de **{format_currency(valor)}** foi confirmado!\n\n"
                f"Em breve seu pedido será processado. Obrigado pela confiança! 🌑"
            )
            await cliente.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        # Registrar log
        await self.db.create_log(
            "pix",
            interaction.user.id,
            "confirmed",
            f"TXID: {txid} | Amount: {valor} | Client: {cliente.id}"
        )

        logger.info(f"PIX confirmed: R${valor} | Client: {cliente} | Staff: {interaction.user}")

    # ──────────────────────────────────────

    @app_commands.command(
        name="pix-info",
        description="ℹ️ Mostra sua chave PIX configurada"
    )
    async def pix_info(self, interaction: discord.Interaction):
        """
        Mostra os dados do PIX configurado.
        Útil para verificar se está tudo certo.
        """

        if not await PermissionChecker.check_interaction_permissions(
            interaction, require_admin=True
        ):
            return

        pix = await self._get_pix_data()

        if not pix["key"]:
            await interaction.response.send_message(
                f"{Emojis.WARNING} **PIX ainda não configurado.**\n"
                f"Use `/pix-configurar` para configurar.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="💳 Dados do PIX Configurado",
            description="Estes são os dados salvos no bot:",
            color=0x000000
        )

        embed.add_field(name="🔑 Chave PIX",  value=f"`{pix['key']}`",  inline=False)
        embed.add_field(name="👤 Titular",    value=pix["name"],         inline=True)
        embed.add_field(name="🏙️ Cidade",    value=pix["city"],         inline=True)
        embed.add_field(name="🏦 Banco",      value=pix["bank"],         inline=True)

        embed.set_footer(text="🌑 VOID Store | Visível apenas para administradores")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Pix(bot))
