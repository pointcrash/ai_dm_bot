import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from config.config import BOT_TOKEN
from handlers.message_handlers import (
    cmd_start, cmd_help, cmd_history, 
    cmd_clear_history, cmd_create_summary, cmd_campaign,
    cmd_group_members, cmd_join_group, cmd_leave_group,
    cmd_remove_member, handle_message
)

class TelegramBot:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.dp = Dispatcher()
        self._setup_handlers()

    def _setup_handlers(self):
        self.dp.message.register(cmd_start, Command("start"))
        self.dp.message.register(cmd_help, Command("help"))
        self.dp.message.register(cmd_history, Command("history"))
        self.dp.message.register(cmd_clear_history, Command("clear"))
        self.dp.message.register(cmd_create_summary, Command("create_summary"))
        self.dp.message.register(cmd_campaign, Command("campaign"))
        self.dp.message.register(cmd_group_members, Command("group"))
        self.dp.message.register(cmd_join_group, Command("join"))
        self.dp.message.register(cmd_leave_group, Command("leave"))
        self.dp.message.register(cmd_remove_member, Command("remove_member"))
        self.dp.message.register(handle_message)

    async def start(self):
        await self.dp.start_polling(self.bot)

def main():
    bot = TelegramBot()
    asyncio.run(bot.start())

if __name__ == "__main__":
    main() 