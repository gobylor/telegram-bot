import asyncio
import structlog
from datetime import datetime
from telethon import TelegramClient, events
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import settings
from utils import safe_send_message, get_entity_info

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

class TelegramBot:
    def __init__(self):
        self.client = TelegramClient('telegram_session', settings.API_ID, settings.API_HASH)
        self.scheduler = AsyncIOScheduler()
        self.setup_handlers()

    def setup_handlers(self):
        """Setup message and command handlers."""
        @self.client.on(events.NewMessage(pattern='/start'))
        async def start_handler(event):
            """Handle /start command."""
            sender = await event.get_sender()
            sender_info = await get_entity_info(sender)
            logger.info("start_command_received", sender=sender_info)
            await event.respond(f"👋 你好！我是你的 Telegram 机器人。\n\n"
                              f"可用命令：\n"
                              f"/start - 显示此帮助信息\n"
                              f"/list - 列出所有对话\n"
                              f"/schedule - 设置定时消息，格式：\n"
                              f"  /schedule \"消息内容\" \"cron表达式\" \"ID\"\n\n"
                              f"例如：\n"
                              f"/schedule \"早上好！\" \"0 9 * * *\" \"123456789\"\n\n"
                              f"💡 使用 /list 查看所有可用的对话和其ID")

        @self.client.on(events.NewMessage(pattern='/list'))
        async def list_handler(event):
            """Handle /list command."""
            try:
                message = "📝 可用的对话列表：\n\n"
                async for dialog in self.client.iter_dialogs():
                    entity = dialog.entity
                    info = await get_entity_info(entity)
                    # 添加对话类型图标
                    icon = "👤" if info["type"] == "User" else "👥" if info["type"] == "Chat" else "📢"
                    message += f"{icon} {info['display_name']} (ID: {info['id']})\n"
                
                message += "\n💡 使用ID来设置定时消息，例如：\n"
                message += "/schedule \"早上好！\" \"0 9 * * *\" \"123456789\""
                
                await event.respond(message)
                
            except Exception as e:
                logger.error("list_command_failed", error=str(e))
                await event.respond("❌ 获取对话列表失败")

        @self.client.on(events.NewMessage(pattern='/schedule'))
        async def schedule_handler(event):
            """Handle /schedule command."""
            try:
                # 解析命令：/schedule "消息" "cron" "ID"
                parts = event.text.split('"')
                if len(parts) < 7:
                    await event.respond("❌ 格式错误！正确格式：\n"
                                     "/schedule \"消息内容\" \"cron表达式\" \"ID\"\n\n"
                                     "例如：\n"
                                     "/schedule \"早上好！\" \"0 9 * * *\" \"123456789\"\n\n"
                                     "💡 使用 /list 查看所有可用的对话和其ID")
                    return

                message = parts[1]
                schedule = parts[3]
                try:
                    target_id = int(parts[5].strip())
                except ValueError:
                    await event.respond("❌ ID 格式错误！ID 应该是一个数字。\n使用 /list 查看正确的ID")
                    return

                # 验证ID是否存在
                target_found = False
                target_info = None
                async for dialog in self.client.iter_dialogs():
                    entity = dialog.entity
                    info = await get_entity_info(entity)
                    if info['id'] == target_id:
                        target_found = True
                        target_info = info
                        break

                if not target_found:
                    await event.respond(f"❌ 找不到ID为 {target_id} 的对话\n"
                                     f"使用 /list 查看可用的对话列表")
                    return

                await self.schedule_message(target_id, message, schedule)
                await event.respond(f"✅ 成功设置定时消息！\n"
                                 f"📝 消息内容：{message}\n"
                                 f"⏰ 定时：{schedule}\n"
                                 f"👥 接收者：{target_info['display_name']}")
                
            except Exception as e:
                logger.error("schedule_command_failed", error=str(e))
                await event.respond("❌ 设置定时消息失败，请检查格式是否正确")

    async def schedule_message(self, recipient_id: int, message: str, schedule: str):
        """Schedule a recurring message."""
        self.scheduler.add_job(
            safe_send_message,
            CronTrigger.from_crontab(schedule),
            args=[self.client, recipient_id, message]
        )
        logger.info("message_scheduled", recipient_id=recipient_id, schedule=schedule)

    async def start(self):
        """Start the bot."""
        try:
            await self.client.start()
            logger.info("bot_started")
            
            self.scheduler.start()
            logger.info("scheduler_started")
            
            await self.client.run_until_disconnected()
        except Exception as e:
            logger.error("bot_startup_failed", error=str(e))
            raise

async def main():
    """Main entry point."""
    bot = TelegramBot()
    await bot.start()

if __name__ == '__main__':
    asyncio.run(main())
