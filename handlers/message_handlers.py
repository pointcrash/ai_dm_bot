from aiogram.types import Message
from aiogram.filters import Command
from services.openai_service import OpenAIService
from services.campaign_service import CampaignService
from services.group_service import GroupService
from services.character_service import CharacterService
from config.hard_messages import START_MESSAGE, CLEAR_HISTORY_MESSAGE, HELP_MESSAGE, CAMPAIGN_MESSAGE
from datetime import datetime

# Инициализируем сервисы
openai_service = OpenAIService()
campaign_service = CampaignService()
group_service = GroupService()
character_service = CharacterService()

# Словарь для хранения состояния настройки кампании
campaign_states = {}

async def cmd_start(message: Message):
    await message.answer(START_MESSAGE)

async def cmd_help(message: Message):
    await message.answer(HELP_MESSAGE)

async def cmd_campaign(message: Message):
    user_id = message.from_user.id
    campaign_states[user_id] = "theme"
    await message.answer("🎭 Какую тематику вы хотите для своей кампании? (героическое фэнтези, темное фэнтези, комедия и т.д.)")

async def handle_message(message: Message):
    user_id = message.from_user.id
    
    # Игнорируем сообщения, начинающиеся с точки
    if message.text.startswith('.'):
        return
        
    # Игнорируем сообщения старше 5 секунд
    message_time = message.date.timestamp()
    current_time = datetime.now().timestamp()
    if current_time - message_time > 5:
        return
    
    # Проверяем, находится ли пользователь в процессе настройки кампании
    if user_id in campaign_states:
        state = campaign_states[user_id]
        
        if state == "theme":
            campaign_service.update_campaign(user_id, theme=message.text)
            campaign_states[user_id] = "world"
            await message.answer("🌍 Какой мир или сеттинг вы предпочитаете? (Forgotten Realms, Darksun или оригинальный мир)")
            
        elif state == "world":
            campaign_service.update_campaign(user_id, world=message.text)
            campaign_states[user_id] = "characters"
            await message.answer("👥 Опишите персонажей, которых вы хотите видеть в партии (классы, расы, предыстории)")
            
        elif state == "characters":
            campaign_service.update_campaign(user_id, characters=[message.text])
            campaign_states[user_id] = "game_structure"
            await message.answer("⏰ Какова будет структура игры? (частота и длительность сессий)")
            
        elif state == "game_structure":
            campaign_service.update_campaign(user_id, game_structure=message.text)
            campaign_states[user_id] = "additional_elements"
            await message.answer("✨ Какие дополнительные элементы вы хотели бы включить? (магия, политика, подземелья и т.д.)")
            
        elif state == "additional_elements":
            campaign_service.update_campaign(user_id, additional_elements=[message.text])
            del campaign_states[user_id]  # Завершаем настройку
            
            # Показываем итоговые настройки
            settings = campaign_service.get_formatted_settings(user_id)
            await message.answer(f"✅ Настройки кампании сохранены!\n\n{settings}")
        return

    try:
        # Отправляем "печатает..." статус
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        # Получаем ответ от OpenAI с учетом истории диалога
        response = await openai_service.get_response(
            user_id=message.from_user.id,
            user_message=message.text,
            chat_id=message.chat.id if message.chat.type != "private" else None
        )
        
        # Отправляем ответ пользователю
        await message.answer(response)
        
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

async def cmd_history(message: Message):
    chat_id = message.chat.id
    history = openai_service.history_service.get_formatted_history(chat_id)
    
    # Разбиваем историю на части по 4000 символов
    chunk_size = 4000
    for i in range(0, len(history), chunk_size):
        chunk = history[i:i + chunk_size]
        await message.answer(chunk)

async def cmd_clear_history(message: Message):
    chat_id = message.chat.id
    openai_service.history_service.clear_history(chat_id)
    await message.answer(CLEAR_HISTORY_MESSAGE)

async def cmd_create_summary(message: Message):
    try:
        chat_id = message.chat.id
        # Получаем историю чата
        history = openai_service.history_service.get_chat_history(chat_id)
        
        if not history.messages:
            await message.answer("История диалога пуста, нечего обобщать.")
            return
            
        # Отправляем "печатает..." статус
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        # Создаем саммари
        history._create_summary()
        
        # Отправляем результат
        await message.answer(f"✅ Саммари создано:\n\n{history.summary}")
        
    except Exception as e:
        await message.answer(f"Произошла ошибка при создании саммари: {str(e)}")

async def cmd_group_members(message: Message):
    """Показать текущий состав группы"""
    members = group_service.get_formatted_members(message.chat.id)
    await message.answer(members)

async def cmd_join_group(message: Message):
    """Добавить активного персонажа в группу"""
    active_character = character_service.get_active_character(message.from_user.id)
    
    if not active_character:
        await message.answer("❌ У вас нет активного персонажа. Сначала создайте и активируйте персонажа.")
        return
        
    if group_service.add_member(message.chat.id, message.from_user.id, active_character):
        await message.answer(f"✅ {active_character['name']} присоединился к группе!")
    else:
        await message.answer(f"❌ {active_character['name']} уже состоит в группе.")

async def cmd_leave_group(message: Message):
    """Удалить активного персонажа из группы"""
    active_character = character_service.get_active_character(message.from_user.id)
    
    if not active_character:
        await message.answer("❌ У вас нет активного персонажа.")
        return
        
    if group_service.remove_member(message.chat.id, active_character['name']):
        await message.answer(f"✅ {active_character['name']} покинул группу.")
    else:
        await message.answer(f"❌ {active_character['name']} не состоит в группе.")

async def cmd_remove_member(message: Message):
    """Удалить участника из группы"""
    # Получаем имя персонажа из сообщения
    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ Использование: /remove_member <имя_персонажа>")
        return
        
    character_name = args[1]
    if group_service.remove_member(message.chat.id, character_name):
        await message.answer(f"✅ {character_name} удален из группы.")
    else:
        await message.answer(f"❌ Персонаж {character_name} не найден в группе.") 