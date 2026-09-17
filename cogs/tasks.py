"""
🌑 VOID Store Bot - Sistema Interno de Tarefas da Equipe
"""

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal
from datetime import datetime

from database.models import Task
from utils.embeds import VoidEmbeds
from utils.permissions import PermissionChecker
from utils.constants import TaskStatus, TaskPriority, Emojis
from utils.logger import logger


class Tasks(commands.Cog):
    """Sistema de gestão de tarefas internas para equipe"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = bot.db

    task_group = app_commands.Group(
        name="tarefa",
        description="📋 Sistema de tarefas internas para a equipe"
    )

    @task_group.command(name="criar", description="📋 Cria uma nova tarefa interna")
    @app_commands.describe(
        nome="Nome ou título da tarefa",
        prioridade="Nível de prioridade",
        descricao="Descrição detalhada da tarefa",
        responsavel="Membro da equipe responsável",
        prazo="Prazo de entrega (ex: DD/MM/AAAA)"
    )
    async def create_task(
        self,
        interaction: discord.Interaction,
        nome: str,
        prioridade: Literal["baixa", "media", "alta"],
        descricao: Optional[str] = None,
        responsavel: Optional[discord.Member] = None,
        prazo: Optional[str] = None
    ):
        """Cria uma tarefa interna"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        await interaction.response.defer()

        # Validar prioridade
        priority_map = {
            "baixa": TaskPriority.LOW,
            "media": TaskPriority.MEDIUM,
            "alta": TaskPriority.HIGH
        }
        mapped_priority = priority_map[prioridade]

        # Validar prazo se fornecido
        parsed_deadline = None
        if prazo:
            try:
                parsed_deadline = datetime.strptime(prazo, "%d/%m/%Y")
            except ValueError:
                await interaction.followup.send(
                    f"{Emojis.ERROR} Formato de data inválido. Use o padrão `DD/MM/AAAA` (ex: 25/12/2025).",
                    ephemeral=True
                )
                return

        # Criar modelo
        task = Task(
            name=nome,
            description=descricao,
            assignee_id=responsavel.id if responsavel else None,
            assignee_name=str(responsavel) if responsavel else None,
            priority=mapped_priority,
            status=TaskStatus.PENDING,
            deadline=parsed_deadline,
            notes=None
        )

        created_task = await self.db.create_task(task)

        if not created_task:
            await interaction.followup.send(
                f"{Emojis.ERROR} Erro ao registrar a tarefa no banco de dados.",
                ephemeral=True
            )
            return

        # Sincronizar com Google Sheets se ativado
        sheets_cog = self.bot.get_cog("Sheets")
        if sheets_cog:
            await sheets_cog.sync_task(created_task)

        # Montar embed
        embed = VoidEmbeds.task_created(
            created_task.id,
            created_task.name,
            created_task.priority,
            responsavel
        )

        if descricao:
            embed.add_field(name="Descrição", value=descricao, inline=False)
        if parsed_deadline:
            embed.add_field(name="Prazo", value=prazo, inline=True)

        await interaction.followup.send(embed=embed)

        # Log
        await self.db.create_log(
            "task",
            interaction.user.id,
            "created",
            f"ID: {created_task.id} | Name: {nome} | Priority: {mapped_priority}"
        )

        logger.info(f"Task #{created_task.id} created by {interaction.user}")

    @task_group.command(name="listar", description="📋 Lista tarefas registradas")
    @app_commands.describe(
        status="Filtrar por status da tarefa"
    )
    async def list_tasks(
        self,
        interaction: discord.Interaction,
        status: Optional[Literal["pendente", "andamento", "concluida", "cancelada"]] = None
    ):
        """Lista todas as tarefas"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        await interaction.response.defer(ephemeral=True)

        status_filter_map = {
            "pendente": TaskStatus.PENDING,
            "andamento": TaskStatus.IN_PROGRESS,
            "concluida": TaskStatus.COMPLETED,
            "cancelada": TaskStatus.CANCELLED
        }

        db_status = status_filter_map.get(status) if status else None
        tasks = await self.db.get_all_tasks(status=db_status)

        if not tasks:
            await interaction.followup.send(
                f"{Emojis.INFO} Nenhuma tarefa encontrada com os filtros selecionados.",
                ephemeral=True
            )
            return

        embed = VoidEmbeds.default(
            "📋 Lista de Tarefas da Equipe",
            f"Filtro ativo: **{status.upper() if status else 'TODAS'}**"
        )

        for t in tasks[:15]:
            p_emoji = (
                Emojis.HIGH_PRIORITY if t.priority == TaskPriority.HIGH
                else Emojis.MEDIUM_PRIORITY if t.priority == TaskPriority.MEDIUM
                else Emojis.LOW_PRIORITY
            )
            s_emoji = (
                Emojis.PENDING if t.status == TaskStatus.PENDING
                else Emojis.IN_PROGRESS if t.status == TaskStatus.IN_PROGRESS
                else Emojis.COMPLETED if t.status == TaskStatus.COMPLETED
                else Emojis.CANCELLED
            )

            responsavel_txt = f"<@{t.assignee_id}>" if t.assignee_id else "Não atribuído"
            embed.add_field(
                name=f"#{t.id} - {t.name}",
                value=(
                    f"**Prioridade:** {p_emoji} {t.priority.title()} | **Status:** {s_emoji} {t.status.title()}\n"
                    f"**Responsável:** {responsavel_txt}"
                ),
                inline=False
            )

        if len(tasks) > 15:
            embed.set_footer(text=f"🌑 VOID Store | Exibindo 15 de {len(tasks)} tarefas")

        await interaction.followup.send(embed=embed, ephemeral=True)

    @task_group.command(name="concluir", description="✅ Marca uma tarefa como concluída")
    @app_commands.describe(tarefa_id="ID numérico da tarefa")
    async def complete_task(self, interaction: discord.Interaction, tarefa_id: int):
        """Conclui uma tarefa"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        await interaction.response.defer()

        task = await self.db.get_task(tarefa_id)
        if not task:
            await interaction.followup.send(
                f"{Emojis.ERROR} Tarefa `#{tarefa_id}` não encontrada.",
                ephemeral=True
            )
            return

        success = await self.db.update_task_status(tarefa_id, TaskStatus.COMPLETED)

        if success:
            embed = VoidEmbeds.success(
                "Tarefa Concluída",
                f"A tarefa **#{tarefa_id} - {task.name}** foi marcada como **CONCLUÍDA** por {interaction.user.mention}."
            )
            await interaction.followup.send(embed=embed)

            # Sincronizar Google Sheets
            task.status = TaskStatus.COMPLETED
            sheets_cog = self.bot.get_cog("Sheets")
            if sheets_cog:
                await sheets_cog.sync_task(task)

            await self.db.create_log(
                "task",
                interaction.user.id,
                "completed",
                f"Task ID: {tarefa_id}"
            )
        else:
            await interaction.followup.send(
                f"{Emojis.ERROR} Erro ao atualizar status da tarefa.",
                ephemeral=True
            )

    @task_group.command(name="cancelar", description="🔴 Cancela uma tarefa")
    @app_commands.describe(tarefa_id="ID numérico da tarefa")
    async def cancel_task(self, interaction: discord.Interaction, tarefa_id: int):
        """Cancela uma tarefa"""

        if not await PermissionChecker.check_interaction_permissions(interaction, require_staff=True):
            return

        await interaction.response.defer()

        task = await self.db.get_task(tarefa_id)
        if not task:
            await interaction.followup.send(
                f"{Emojis.ERROR} Tarefa `#{tarefa_id}` não encontrada.",
                ephemeral=True
            )
            return

        success = await self.db.update_task_status(tarefa_id, TaskStatus.CANCELLED)

        if success:
            embed = VoidEmbeds.warning(
                "Tarefa Cancelada",
                f"A tarefa **#{tarefa_id} - {task.name}** foi cancelada por {interaction.user.mention}."
            )
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(
                f"{Emojis.ERROR} Erro ao cancelar tarefa.",
                ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Tasks(bot))
