import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault
from config.config import BOT_TOKEN
from handlers.message_handlers import (
    cmd_start, cmd_help, cmd_history, 
    cmd_clear_history, cmd_create_summary,
    cmd_group_members, cmd_join_group, cmd_leave_group,
    cmd_remove_member, cmd_roll, cmd_campaign, cmd_delete_campaign,
    cmd_stats, handle_message
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
        self.dp.message.register(cmd_delete_campaign, Command("delete_campaign"))
        self.dp.message.register(cmd_group_members, Command("group"))
        self.dp.message.register(cmd_join_group, Command("join"))
        self.dp.message.register(cmd_leave_group, Command("leave"))
        self.dp.message.register(cmd_remove_member, Command("remove_member"))
        self.dp.message.register(cmd_roll, Command("roll"))
        self.dp.message.register(cmd_stats, Command("stats"))
        self.dp.message.register(handle_message)

    async def _setup_commands(self):
        commands = [
            BotCommand(command="help", description="Показать список команд"),
            BotCommand(command="history", description="Показать историю диалога"),
            BotCommand(command="clear", description="Очистить историю диалога"),
            BotCommand(command="create_summary", description="Создать краткое саммари"),
            BotCommand(command="roll", description="Бросить кубики"),
            BotCommand(command="campaign", description="Управление описанием кампании"),
            BotCommand(command="delete_campaign", description="Удалить описание кампании"),
            BotCommand(command="group", description="Показать состав группы"),
            BotCommand(command="join", description="Присоединиться к группе"),
            BotCommand(command="leave", description="Покинуть группу"),
            BotCommand(command="remove_member", description="Удалить участника из группы"),
            BotCommand(command="stats", description="Показать статистику использования")
        ]
        await self.bot.set_my_commands(commands, scope=BotCommandScopeDefault())

    async def start(self):
        await self._setup_commands()
        await self.dp.start_polling(self.bot)

def main():
    bot = TelegramBot()
    asyncio.run(bot.start())

if __name__ == "__main__":
    main() 