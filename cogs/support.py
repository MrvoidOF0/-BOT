"""
🌑 VOID Store Bot - Sistema de Suporte Integrado (IA Groq + Atendimento Humano via Select Menu)
"""
import io
import os
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from groq import Groq

# ID CORRETO DO CANAL DE LOGS DO SEU SERVIDOR
TICKET_LOGS_CHANNEL_ID = 1549933790309257226

# Inicialização do Cliente Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

SYSTEM_PROMPT = """
# SYSTEM PROMPT — IA DE ATENDIMENTO | VOID STORE
Você é a IA oficial de atendimento da VOID Store. Atenda com clareza, objetividade e sem inventar dados.
"""

class CloseSupportView(discord.ui.View):
    """View interna do Ticket de Suporte/Carrinho (Botões de Encerrar e Chamar Humano)."""
    def __init__(self, opener_user: discord.User, mode_label: str):
        super().__init__(timeout=None)
        self.opener_user = opener_user
        self.mode_label = mode_label

    @discord.ui.button(label="Chamar Atendente Humano", style=discord.ButtonStyle.blurple, emoji="👤", custom_id="btn_call_human")
    async def call_human(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        for role_id in [1550096907739857079, 1550097139093209139]:
            role = guild.get_role(role_id)
            if role:
                await interaction.channel.set_permissions(role, read_messages=True, send_messages=True, view_channel=True)

        button.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(
            "🔔 **Atendente humano solicitado!** Um membro da gerência da VOID Store entrará no chat em breve."
        )

    @discord.ui.button(label="Encerrar Atendimento", style=discord.ButtonStyle.red, emoji="🔒", custom_id="btn_close_support")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 **A gerar transcript e a encerrar atendimento em 5 segundos...**")
        
        channel = interaction.channel
        category = channel.category
        guild = interaction.guild

        # 1. Coleta o histórico de mensagens para o transcript dentro do canal privado
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

        # 2. Busca estritamente o canal de logs e IMPEDE envio em canais incorretos
        log_channel = guild.get_channel(TICKET_LOGS_CHANNEL_ID)
        
        if not log_channel:
            try:
                log_channel = await guild.fetch_channel(TICKET_LOGS_CHANNEL_ID)
            except Exception as e:
                print(f"❌ [ERRO LOGS] Não foi possível acessar o canal de logs ({TICKET_LOGS_CHANNEL_ID}): {e}")

        if log_channel:
            embed_log = discord.Embed(
                title="📄 TRANSCRIPT DE ATENDIMENTO",
                color=discord.Color.from_rgb(15, 15, 15)
            )
            embed_log.add_field(name="👤 Cliente:", value=f"{self.opener_user.mention} (`{self.opener_user.id}`)", inline=True)
            embed_log.add_field(name="🛡️ Encerrado por:", value=f"{interaction.user.mention}", inline=True)
            embed_log.add_field(name="🏷️ Serviço:", value=f"`{self.mode_label}`", inline=True)
            embed_log.add_field(name="💬 Canal Encerrado:", value=f"`#{channel.name}`", inline=False)
            embed_log.set_footer(text="🌑 VOID Store • Sistema de Registro de Tickets")

            await log_channel.send(embed=embed_log, file=transcript_file)
        else:
            print(f"⚠️ [CRÍTICO] O transcript do ticket #{channel.name} NÃO foi enviado porque o canal {TICKET_LOGS_CHANNEL_ID} é inacessível.")

        await asyncio.sleep(5)
        
        # 3. Elimina o canal do ticket e a categoria privada criada
        await channel.delete()
        if category and len(category.channels) == 0:
            await category.delete()


class SupportSelect(discord.ui.Select):
    """Menu suspenso (Dropdown) para escolha do tipo de atendimento."""
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Atendimento por IA (Instantâneo)",
                value="ai",
                description="Tire dúvidas gerais, preços e informações com a IA da loja.",
                emoji="🤖"
            ),
            discord.SelectOption(
                label="Atendimento Humano (Gerência)",
                value="human",
                description="Fale com a equipe para pagamentos, problemas ou entregas.",
                emoji="💬"
            )
        ]
        super().__init__(
            placeholder="Selecione a categoria do seu atendimento...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="select_support_category"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        is_ai = selected_value == "ai"
        
        guild = interaction.guild
        user = interaction.user
        mode_label = "Atendimento por IA (Groq)" if is_ai else "Atendimento Humano"
        prefix = "ia" if is_ai else "suporte"
        channel_name = f"💬-{prefix}-{user.name.lower()}"

        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(
                f"❌ **Já possui um atendimento de suporte aberto!** Acesse {existing_channel.mention}.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

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

        if not is_ai:
            for role_id in [1550096907739857079, 1550097139093209139]:
                role = guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, view_channel=True, send_messages=True)

        category_name = f"🔒 │ SUPORTE {'IA' if is_ai else 'HUMANO'} - {user.name}"
        ticket_category = await guild.create_category_channel(
            name=category_name,
            overwrites=overwrites
        )

        support_channel = await guild.create_text_channel(
            name=channel_name,
            category=ticket_category,
            overwrites=overwrites,
            topic=f"Atendimento Suporte ({mode_label}): {user.display_name}"
        )

        embed = discord.Embed(
            title=f"🌑 VOID STORE — SUPORTE ({'IA' if is_ai else 'HUMANO'})",
            description=(
                f"Olá {user.mention}, bem-vindo ao seu atendimento!\n\n"
                f"📌 **Modalidade Selecionada:** `{mode_label}`\n\n"
                + (
                    "🤖 **A nossa IA de Suporte está pronta!** Envie a sua dúvida no chat abaixo para ser respondido instantaneamente.\n"
                    "*(Caso precise falar com a gerência, clique no botão 'Chamar Atendente Humano' abaixo).*"
                    if is_ai else
                    "👤 **A nossa equipe foi acionada.** Explique a sua dúvida ou problema detalhadamente no chat e aguarde um atendente."
                )
            ),
            color=discord.Color.from_rgb(15, 15, 15)
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.set_footer(text="🌑 VOID Store • Central de Atendimento ao Cliente")

        close_view = CloseSupportView(opener_user=user, mode_label=mode_label)
        await support_channel.send(content=f"{user.mention}", embed=embed, view=close_view)

        await interaction.followup.send(
            f"✅ **Categoria e carrinho privado criados com sucesso!** Acesse {support_channel.mention} para concluir sua compra.",
            ephemeral=True
        )


class SupportSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SupportSelect())


class Support(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Restringe estritamente para responder SOMENTE nos canais de ticket IA
        if not message.channel.name.startswith("💬-ia-"):
            return

        if not groq_client:
            return

        async with message.channel.typing():
            try:
                chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]
                async for msg in message.channel.history(limit=8, oldest_first=True):
                    role = "assistant" if msg.author.bot else "user"
                    if msg.content:
                        chat_history.append({"role": role, "content": msg.content})

                def call_groq():
                    return groq_client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=chat_history,
                        temperature=0.6,
                        max_tokens=400
                    )

                loop = asyncio.get_event_loop()
                completion = await loop.run_in_executor(None, call_groq)

                ai_response = completion.choices[0].message.content
                await message.reply(ai_response, mention_author=False)

            except Exception as e:
                print(f"❌ [Groq Error Log]: {e}")

    @app_commands.command(name="suporte-painel", description="Envia o painel oficial de suporte com Menu Suspenso")
    @app_commands.checks.has_permissions(administrator=True)
    async def suporte_painel(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed = discord.Embed(
            title="Central de Atendimento — VOID Store",
            description=(
                "Seja bem-vindo à **VOID Store**!\n\n"
                "Para efetuar compras, tirar dúvidas ou resgatar benefícios, selecione a opção desejada no **menu abaixo** para abrir um canal privado.\n\n"
                "⚙️ *Atendimento 100% privado e seguro.*"
            ),
            color=discord.Color.from_rgb(15, 15, 15)
        )
        if interaction.guild and interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.set_footer(text="🌑 VOID Store • Selecione abaixo para abrir o seu ticket")

        await interaction.channel.send(embed=embed, view=SupportSelectView())
        await interaction.followup.send("✅ Painel enviado com sucesso!", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Support(bot))
