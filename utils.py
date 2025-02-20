import structlog
from tenacity import retry, stop_after_attempt, wait_fixed
from typing import Optional, Union, Dict
from telethon.tl.types import User, Chat, Channel

logger = structlog.get_logger()

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
async def safe_send_message(client, recipient_id: int, message: str) -> Optional[bool]:
    """
    Safely send a message with retry mechanism.
    
    Args:
        client: TelegramClient instance
        recipient_id: Telegram ID of the recipient
        message: Message to send
        
    Returns:
        Optional[bool]: True if successful, False if failed, None if all retries exhausted
    """
    try:
        await client.send_message(recipient_id, message)
        return True
    except Exception as e:
        logger.error("message_send_failed", error=str(e), recipient_id=recipient_id)
        raise

async def get_entity_info(entity: Union[User, Chat, Channel]) -> Dict:
    """
    Extract relevant information from a Telegram entity.
    
    Args:
        entity: Telegram entity (User, Chat, or Channel)
        
    Returns:
        dict: Entity information including id, type, name, and username
    """
    entity_type = entity.__class__.__name__
    info = {
        "id": entity.id,
        "type": entity_type,
        "username": None,
    }
    
    if isinstance(entity, User):
        # 用户信息
        info["name"] = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
        info["username"] = entity.username
        info["display_name"] = (f"{info['name']}" + 
                              (f" (@{entity.username})" if entity.username else "") +
                              f" [ID: {entity.id}]")
    else:
        # 群组或频道信息
        info["name"] = entity.title
        info["username"] = getattr(entity, 'username', None)
        info["display_name"] = (f"{entity.title}" +
                              (f" (@{entity.username})" if getattr(entity, 'username', None) else "") +
                              f" [ID: {entity.id}]")
    
    return info
