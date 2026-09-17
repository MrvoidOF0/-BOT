"""
🌑 VOID Store Bot - Funções Auxiliares
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Union
import discord
from discord import Member, User, Role

def format_currency(value: float) -> str:
    """
    Formata um valor para moeda brasileira
    
    Args:
        value: Valor numérico
        
    Returns:
        String formatada (ex: "R$ 19,90")
    """
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def parse_currency(text: str) -> Optional[float]:
    """
    Converte texto de moeda para float
    
    Args:
        text: Texto contendo valor (ex: "R$ 19,90" ou "19.90")
        
    Returns:
        Valor float ou None se inválido
    """
    # Remover símbolos e espaços
    cleaned = re.sub(r'[R$\s]', '', text)
    
    # Substituir vírgula por ponto
    cleaned = cleaned.replace(',', '.')
    
    try:
        return float(cleaned)
    except ValueError:
        return None

def format_datetime(dt: datetime, include_time: bool = True) -> str:
    """
    Formata uma data/hora para exibição
    
    Args:
        dt: Objeto datetime
        include_time: Se deve incluir o horário
        
    Returns:
        String formatada
    """
    if include_time:
        return dt.strftime("%d/%m/%Y às %H:%M:%S")
    return dt.strftime("%d/%m/%Y")

def parse_time_string(time_str: str) -> Optional[timedelta]:
    """
    Converte string de tempo para timedelta
    
    Args:
        time_str: String como "1h", "30m", "1d"
        
    Returns:
        Timedelta ou None se inválido
    """
    pattern = r'^(\d+)([smhd])$'
    match = re.match(pattern, time_str.lower())
    
    if not match:
        return None
    
    value, unit = match.groups()
    value = int(value)
    
    units = {
        's': 'seconds',
        'm': 'minutes',
        'h': 'hours',
        'd': 'days'
    }
    
    return timedelta(**{units[unit]: value})

def get_user_mention(user: Union[Member, User, int]) -> str:
    """
    Retorna a menção de um usuário
    
    Args:
        user: Member, User ou ID
        
    Returns:
        String de menção
    """
    if isinstance(user, (Member, User)):
        return user.mention
    return f"<@{user}>"

def get_role_mention(role: Union[Role, int]) -> str:
    """
    Retorna a menção de um cargo
    
    Args:
        role: Role ou ID
        
    Returns:
        String de menção
    """
    if isinstance(role, Role):
        return role.mention
    return f"<@&{role}>"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Trunca texto adicionando sufixo
    
    Args:
        text: Texto original
        max_length: Comprimento máximo
        suffix: Sufixo a adicionar
        
    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def generate_order_id(current_count: int) -> str:
    """
    Gera ID único de pedido
    
    Args:
        current_count: Contagem atual de pedidos
        
    Returns:
        ID formatado (ex: "VOID-0001")
    """
    return f"VOID-{current_count + 1:04d}"

def get_percentage_emoji(percentage: int) -> str:
    """
    Retorna emoji baseado em porcentagem
    
    Args:
        percentage: Porcentagem (0-100)
        
    Returns:
        Emoji representativo
    """
    if percentage >= 75:
        return "🟢"
    elif percentage >= 50:
        return "🟡"
    elif percentage >= 25:
        return "🟠"
    else:
        return "🔴"

def validate_discord_id(discord_id: str) -> bool:
    """
    Valida se um ID do Discord é válido
    
    Args:
        discord_id: ID para validar
        
    Returns:
        True se válido
    """
    return discord_id.isdigit() and len(discord_id) >= 17 and len(discord_id) <= 20

async def safe_send(
    destination: Union[discord.TextChannel, discord.User, discord.Member],
    content: str = None,
    embed: discord.Embed = None,
    view: discord.ui.View = None
) -> Optional[discord.Message]:
    """
    Envia mensagem com tratamento de erro
    
    Args:
        destination: Canal ou usuário
        content: Conteúdo da mensagem
        embed: Embed
        view: View com botões
        
    Returns:
        Mensagem enviada ou None se falhou
    """
    try:
        return await destination.send(content=content, embed=embed, view=view)
    except discord.Forbidden:
        return None
    except discord.HTTPException:
        return None

def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Divide lista em chunks menores
    
    Args:
        lst: Lista original
        chunk_size: Tamanho de cada chunk
        
    Returns:
        Lista de chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
