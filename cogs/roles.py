import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils.permissions import PermissionChecker
from config import config

class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ID_NOVATO = 1550097372732723360

    @app_commands.command(name="cargo-novato-geral", description="👥 Dá o cargo de Novato para TODOS os membros do servidor")
    async def cargo_novato_geral(self, interaction: discord.Interaction):
        """Comando Mass-Role para aplicar o cargo de novato em todos"""
        
        if not await PermissionChecker.check(interaction): return

        # Resposta inicial (defer) pois o processo pode demorar
        await interaction.response.send_message("⏳ Iniciando atribuição de cargo global... Isso pode demorar alguns minutos.", ephemeral=True)

        role = interaction.guild.get_role(self.ID_NOVATO)
        if not role:
            return await interaction.edit_original_response(content="❌ Erro: Cargo de Novato não encontrado no servidor.")

        sucesso = 0
        falha = 0
        ja_tinham = 0

        # Pegar todos os membros (precisa da Intent de Members ativa no portal do dev)
        for member in interaction.guild.members:
            if member.bot: continue # Ignorar bots
            
            if role in member.roles:
                ja_tinham += 1
                continue
                
            try:
                await member.add_roles(role, reason="Atribuição Global VOID Store")
                sucesso += 1
                # Evitar Rate Limit do Discord (limite de velocidade)
                if sucesso % 5 == 0:
                    await asyncio.sleep(1) 
            except:
                falha += 1

        embed = discord.Embed(
            title="✅ Processo Concluído",
            description=f"O cargo {role.mention} foi processado para todo o servidor.",
            color=0x00ff00
        )
        embed.add_field(name="📦 Atribuídos agora", value=f"`{sucesso}`", inline=True)
        embed.add_field(name="👥 Já possuíam", value=f"`{ja_tinham}`", inline=True)
        embed.add_field(name="❌ Falhas (Sem permissão)", value=f"`{falha}`", inline=True)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Roles(bot))
