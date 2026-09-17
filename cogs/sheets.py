"""
🌑 VOID Store Bot - Integração Google Sheets
═══════════════════════════════════════════════════════════════
Gerencia a sincronização segura com planilhas Google.
Se não configurado ou desabilitado via .env, o bot continua 
funcionando 100% com banco SQLite/PostgreSQL sem falhas.
"""

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime
from typing import Optional

from utils.embeds import VoidEmbeds
from utils.permissions import PermissionChecker
from utils.constants import Emojis
from utils.logger import logger
from config import config

# Importação condicional de gspread
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False


class Sheets(commands.Cog):
    """Sincronizador assíncrono com Google Sheets"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db
        self.client: Optional[gspread.Client] = None
        self.spreadsheet = None
        self.is_active = False

        if config.GOOGLE_SHEETS_ENABLED and GSPREAD_AVAILABLE:
            self.bot.loop.create_task(self._initialize_sheets())
        else:
            logger.info("Google Sheets integration is disabled or dependencies not loaded.")

    async def _initialize_sheets(self):
        """Inicializa a conexão com o Google Sheets em background"""
        await self.bot.wait_until_ready()

        creds_dict = config.get_google_credentials()
        if not creds_dict or not config.GOOGLE_SHEET_ID:
            logger.warning("Google Sheets enabled, but credentials or Sheet ID missing in .env.")
            return

        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(config.GOOGLE_SHEET_ID)

            # Garantir abas
            await self._ensure_worksheets()
            self.is_active = True
            logger.info("✅ Google Sheets successfully connected and synchronized.")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Sheets: {e}")
            self.is_active = False

    async def _ensure_worksheets(self):
        """Garante que as abas necessárias existem com seus cabeçalhos"""
        required_sheets = {
            "CLIENTES": ["Discord ID", "Nome", "Valor Gasto", "Cargo Atual", "Último Pedido"],
            "PEDIDOS": ["ID", "Cliente", "Produto", "Valor", "Responsável", "Status", "Data"],
            "TAREFAS": ["ID", "Tarefa", "Responsável", "Prioridade", "Status", "Prazo", "Observação"],
            "ESTOQUE": ["Produto", "Categoria", "Quantidade", "Preço", "Status", "Última Atualização"]
        }

        loop = asyncio.get_running_loop()

        def _setup_sync():
            existing = [ws.title for ws in self.spreadsheet.worksheets()]
            for title, headers in required_sheets.items():
                if title not in existing:
                    ws = self.spreadsheet.add_worksheet(title=title, rows=100, cols=len(headers))
                    ws.append_row(headers)
                    logger.info(f"Created worksheet: {title}")

        await loop.run_in_executor(None, _setup_sync)

    # ====================================
    # MÉTODOS DE SINCRONIZAÇÃO
    # ====================================

    async def sync_order(self, order):
        """Sincroniza um pedido com a aba PEDIDOS"""
        if not self.is_active or not self.spreadsheet:
            return

        loop = asyncio.get_running_loop()

        def _append():
            try:
                ws = self.spreadsheet.worksheet("PEDIDOS")
                row = [
                    order.order_id,
                    order.client_name,
                    order.product,
                    f"R$ {order.value:.2f}",
                    order.responsible_name or "N/A",
                    order.status.upper(),
                    order.created_at.strftime("%d/%m/%Y %H:%M")
                ]
                ws.append_row(row)
            except Exception as e:
                logger.error(f"Sheets error on sync_order: {e}")

        await loop.run_in_executor(None, _append)

    async def sync_task(self, task):
        """Sincroniza uma tarefa com a aba TAREFAS"""
        if not self.is_active or not self.spreadsheet:
            return

        loop = asyncio.get_running_loop()

        def _append():
            try:
                ws = self.spreadsheet.worksheet("TAREFAS")
                row = [
                    f"#{task.id}",
                    task.name,
                    task.assignee_name or "Não atribuído",
                    task.priority.upper(),
                    task.status.upper(),
                    task.deadline.strftime("%d/%m/%Y") if task.deadline else "N/A",
                    task.description or ""
                ]
                ws.append_row(row)
            except Exception as e:
                logger.error(f"Sheets error on sync_task: {e}")

        await loop.run_in_executor(None, _append)

    async def sync_inventory(self, item):
        """Sincroniza ou atualiza um item na aba ESTOQUE"""
        if not self.is_active or not self.spreadsheet:
            return

        loop = asyncio.get_running_loop()

        def _update():
            try:
                ws = self.spreadsheet.worksheet("ESTOQUE")
                row = [
                    item.name,
                    item.category,
                    item.quantity,
                    f"R$ {item.price:.2f}",
                    item.status.upper(),
                    datetime.now().strftime("%d/%m/%Y %H:%M")
                ]
                # Busca pelo nome
                cell = ws.find(item.name)
                if cell:
                    ws.update(f"A{cell.row}:F{cell.row}", [row])
                else:
                    ws.append_row(row)
            except Exception as e:
                logger.error(f"Sheets error on sync_inventory: {e}")

        await loop.run_in_executor(None, _update)

    @app_commands.command(name="sheets-status", description="📊 Verifica o status da integração com o Google Sheets")
    async def sheets_status(self, interaction: discord.Interaction):
        """Comando para verificar se o Google Sheets está online"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        if self.is_active:
            embed = VoidEmbeds.success(
                "Google Sheets Conectado",
                f"A planilha está **ativa** e sincronizando dados em tempo real.\n"
                f"**ID da Planilha:** `{config.GOOGLE_SHEET_ID[:10]}...`"
            )
        else:
            embed = VoidEmbeds.warning(
                "Google Sheets Desconectado / Inativo",
                "A sincronização em nuvem está desabilitada no momento.\n"
                "O bot está operando normalmente salvando tudo no banco local."
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Sheets(bot))
