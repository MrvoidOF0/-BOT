"""
🌑 VOID Store Bot - Arquivo Principal
═══════════════════════════════════════════════════════════════

Bot de gerenciamento completo para VOID Store
Desenvolvido com discord.py 2.x

Author: VOID Store Development Team
Version: 1.0.0
"""

import discord
from discord.ext import commands
import asyncio
import sys
from pathlib import Path

# Imports locais
from config import config
from database.database import Database
from utils.logger import setup_logger
from utils.constants import Colors, Emojis

# Configurar logger
logger = setup_logger("VOID")

class VoidBot(commands.Bot):
    """Bot principal da VOID Store"""
    
    def __init__(self):
        # Configurar intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        # Inicializar bot
        super().__init__(
            command_prefix=config.PREFIX,
            intents=intents,
            help_command=None  # Vamos criar nosso próprio /help
        )
        
        # Database
        self.db = Database()
        
        # Status de inicialização
        self.ready = False
        
        logger.info("🌑 VOID Store Bot initialized")
    
    async def setup_hook(self):
        """
        Hook executado antes do bot conectar ao Discord.
        Usado para carregar cogs e preparar o bot.
        """
        logger.info("Starting setup hook...")
        
        # Conectar ao banco de dados
        try:
            await self.db.connect()
            logger.info("✅ Database connected")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            sys.exit(1)
        
        # Carregar cogs
        await self.load_cogs()
        
        # Sincronizar comandos slash (guild-specific para testes rápidos)
        if config.GUILD_ID:
            guild = discord.Object(id=config.GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info(f"✅ Commands synced to guild {config.GUILD_ID}")
        else:
            await self.tree.sync()
            logger.info("✅ Commands synced globally")
    
    async def load_cogs(self):
        """Carrega todos os cogs do diretório cogs/"""
        cogs_dir = Path("cogs")
        
        if not cogs_dir.exists():
            logger.warning("⚠️ Cogs directory not found")
            return
        
        # Lista de cogs para carregar
        cog_files = [
            "tickets",
            "orders",
            "roles",
            "vip",
            "booster",
            "tasks",
            "inventory",
            "moderation",
            "logs",
            "sheets",
            "setup",
            "help",
            "error_handler"
        ]
        
        loaded = 0
        failed = 0
        
        for cog_file in cog_files:
            try:
                await self.load_extension(f"cogs.{cog_file}")
                logger.info(f"✅ Loaded cog: {cog_file}")
                loaded += 1
            except Exception as e:
                logger.error(f"❌ Failed to load cog {cog_file}: {e}")
                failed += 1
        
        logger.info(f"Cogs loaded: {loaded} | Failed: {failed}")
    
    async def on_ready(self):
        """Evento executado quando o bot está pronto"""
        if self.ready:
            return
        
        self.ready = True
        
        logger.info("═" * 50)
        logger.info(f"🌑 VOID Store Bot is ready!")
        logger.info(f"Bot: {self.user.name}#{self.user.discriminator}")
        logger.info(f"ID: {self.user.id}")
        logger.info(f"Servers: {len(self.guilds)}")
        logger.info(f"Users: {sum(g.member_count for g in self.guilds)}")
        logger.info("═" * 50)
        
        # Definir status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="🌑 VOID Store | /help"
            ),
            status=discord.Status.online
        )
    
    async def on_guild_join(self, guild: discord.Guild):
        """Evento quando o bot entra em um servidor"""
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
    
    async def on_guild_remove(self, guild: discord.Guild):
        """Evento quando o bot sai de um servidor"""
        logger.info(f"Left guild: {guild.name} (ID: {guild.id})")
    
    async def on_error(self, event: str, *args, **kwargs):
        """Evento de erro global"""
        logger.error(f"Error in event {event}", exc_info=sys.exc_info())
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Evento de erro de comandos prefixados"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        logger.error(f"Command error: {error}", exc_info=error)
    
    async def close(self):
        """Fecha o bot de forma limpa"""
        logger.info("Shutting down bot...")
        
        # Desconectar do banco
        await self.db.disconnect()
        
        # Fechar conexão do Discord
        await super().close()
        
        logger.info("Bot shutdown complete")

def main():
    """Função principal"""
    
    # Banner
    print("""
    ═══════════════════════════════════════════════════════════
    
    ██╗   ██╗ ██████╗ ██╗██████╗     ███████╗████████╗ ██████╗ ██████╗ ███████╗
    ██║   ██║██╔═══██╗██║██╔══██╗    ██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗██╔════╝
    ██║   ██║██║   ██║██║██║  ██║    ███████╗   ██║   ██║   ██║██████╔╝█████╗  
    ╚██╗ ██╔╝██║   ██║██║██║  ██║    ╚════██║   ██║   ██║   ██║██╔══██╗██╔══╝  
     ╚████╔╝ ╚██████╔╝██║██████╔╝    ███████║   ██║   ╚██████╔╝██║  ██║███████╗
      ╚═══╝   ╚═════╝ ╚═╝╚═════╝     ╚══════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝
    
    🌑 VOID Store Bot v1.0.0
    Sistema de Gerenciamento Completo
    
    ═══════════════════════════════════════════════════════════
    """)
    
    # Validar configurações
    logger.info("Validating configuration...")
    is_valid, errors = config.validate()
    
    if not is_valid:
        logger.error("❌ Configuration validation failed:")
        for error in errors:
            logger.error(f"  {error}")
        logger.error("\nPlease check your .env file and try again.")
        sys.exit(1)
    
    logger.info("✅ Configuration validated")
    
    # Criar e executar bot
    bot = VoidBot()
    
    try:
        bot.run(config.DISCORD_TOKEN, log_handler=None)
    except discord.LoginFailure:
        logger.error("❌ Invalid Discord token. Please check your .env file.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
