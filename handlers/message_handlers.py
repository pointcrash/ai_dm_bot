from aiogram.types import Message
from aiogram.filters import Command
from services.openai_service import OpenAIService
from services.campaign_service import CampaignService
from config.hard_messages import START_MESSAGE, CLEAR_HISTORY_MESSAGE, HELP_MESSAGE, CAMPAIGN_MESSAGE

# Инициализируем сервисы
openai_service = OpenAIService()
campaign_service = CampaignService()

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
        response = await openai_service.get_response(message.from_user.id, message.text)
        
        # Отправляем ответ пользователю
        await message.answer(response)
        
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

async def cmd_history(message: Message):
    history = openai_service.history_service.get_formatted_history(message.from_user.id)
    await message.answer(history)

async def cmd_clear_history(message: Message):
    openai_service.history_service.clear_history(message.from_user.id)
    await message.answer(CLEAR_HISTORY_MESSAGE)

async def cmd_create_summary(message: Message):
    try:
        # Получаем историю чата
        history = openai_service.history_service.get_chat_history(message.from_user.id)
        
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