import traceback
from pathlib import Path
from aiogram.types import Message
from aiogram.types import FSInputFile
from services.openai_service import OpenAIService
from services.group_service import GroupService
from services.character_service import CharacterService
from services.campaign_service import CampaignService
from services.rag_service import RAGManager, get_or_create_rag_manager, get_context
from services.voice_service import VoiceService
from services.chat_settings_service import ChatSettingsService
from config.hard_messages import START_MESSAGE, CLEAR_HISTORY_MESSAGE, HELP_MESSAGE
from datetime import datetime
import random
import os

from utils.utils import get_path_to_simple_history_file

# Инициализируем сервисы
openai_service = OpenAIService()
group_service = GroupService()
character_service = CharacterService()
campaign_service = CampaignService()
voice_service = VoiceService()
chat_settings_service = ChatSettingsService()

# Словарь для хранения состояния редактирования описания кампании
campaign_edit_states = {}

async def cmd_start(message: Message) -> None:
    """Обработчик команды /start"""
    await message.answer(START_MESSAGE)

async def cmd_help(message: Message) -> None:
    """Обработчик команды /help"""
    await message.answer(HELP_MESSAGE)

async def cmd_stats(message: Message) -> None:
    """Показать статистику использования"""
    try:
        user_id = message.from_user.id
        stats = openai_service.usage_service.get_formatted_usage_stats(user_id)
        await message.answer(stats)
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при получении статистики: {str(e)}")

async def cmd_campaign(message: Message) -> None:
    """Показать или изменить описание кампании"""
    chat_id = message.chat.id
    args = message.text.split(maxsplit=1)
    
    try:
        # Если есть аргументы, обновляем описание
        if len(args) > 1:
            description = args[1]
            campaign = campaign_service.get_campaign(chat_id)
            campaign = campaign_service.update_campaign(chat_id, description=description)
            await message.answer("✅ Описание кампании обновлено!")
            return
            
        # Иначе показываем текущее описание
        campaign = campaign_service.get_campaign(chat_id)
        if not campaign.description:
            await message.answer("❌ Описание кампании еще не задано. Используйте /campaign для установки описания.")
        else:
            await message.answer(f"📜 Описание кампании:\n\n{campaign.description}")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при работе с описанием кампании: {str(e)}")

async def handle_message(message: Message) -> None:
    """Обработчик обычных сообщений"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Проверяем наличие текста или голосового сообщения
    if not message.text and not message.voice:
        await message.answer(f"❌ Я умею обрабатывать только текстовые или голосовые сообщения")
        return
    
    # Игнорируем пересланные сообщения и ответы на сообщения
    if message.forward_from or message.reply_to_message:
        return
        
    # Игнорируем сообщения, начинающиеся с точки или слеша
    if message.text and message.text.startswith(('.', '/', '!', '?')):
        return
        
    # Игнорируем сообщения старше 5 секунд
    message_time = message.date.timestamp()
    current_time = datetime.now().timestamp()
    if current_time - message_time > 5:
        return

    try:
        # Обновляем информацию о пользователе
        openai_service.usage_service.update_user_info(
            user_id=user_id,
            first_name=message.from_user.first_name,
            username=message.from_user.username
        )

        # Получаем текст сообщения (из текста или голосового сообщения)
        user_message = message.text
        if message.voice:
            user_message = await voice_service.transcribe_voice(message.voice)
            # Отправляем расшифровку голосового сообщения
            await message.answer(f"🎤 Расшифровка: {user_message}")


        # Отправляем "печатает..." статус
        await message.bot.send_chat_action(chat_id=chat_id, action="typing")

        # Получаем ответ от OpenAI с учетом истории диалога
        response = await openai_service.get_response(
            user_id=user_id,
            user_message=user_message,
            chat_id=chat_id if message.chat.type != "private" else None
        )

        # Записываем в файл истории новую пару сообщений
        openai_service.history_service.add_couple_of_messages_to_simple_dialog_history(
            chat_id=chat_id,
            user_content=user_message,
            ai_response_content=response,
        )

        # Проверяем, включен ли режим голосовых ответов
        if chat_settings_service.is_voice_enabled(chat_id):
            # Отправляем "говорит..." статус
            await message.bot.send_chat_action(chat_id=chat_id, action="record_voice")

            # Преобразуем ответ в голосовое сообщение
            audio_path = await voice_service.text_to_speech(response)

            # Отправляем "загружает голосовое сообщение..." статус
            await message.bot.send_chat_action(chat_id=chat_id, action="upload_voice")
            
            try:
                # Отправляем голосовое сообщение
                voice = FSInputFile(audio_path)
                await message.answer_voice(voice)
            finally:
                # Удаляем временный аудиофайл
                if os.path.exists(audio_path):
                    os.remove(audio_path)
        else:
            # Отправляем текстовый ответ
            await message.answer(response)
        
    except Exception as e:
        traceback.print_exc()
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

async def cmd_history(message: Message) -> None:
    """Показать историю диалога"""
    try:
        chat_id = message.chat.id
        history = openai_service.history_service.get_formatted_history(chat_id)
        
        # Разбиваем историю на части по 4000 символов
        chunk_size = 4000
        for i in range(0, len(history), chunk_size):
            chunk = history[i:i + chunk_size]
            await message.answer(chunk)
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при получении истории: {str(e)}")

async def cmd_clear_history(message: Message) -> None:
    """Очистить историю диалога"""
    try:
        chat_id = message.chat.id
        openai_service.history_service.clear_history(chat_id)
        await message.answer(CLEAR_HISTORY_MESSAGE)
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при очистке истории: {str(e)}")

async def cmd_create_summary(message: Message) -> None:
    """Создать краткое саммари текущего диалога"""
    try:
        chat_id = message.chat.id
        # Получаем историю чата
        history = openai_service.history_service.get_chat_history(chat_id)
        
        if not history.messages:
            await message.answer("История диалога пуста, нечего обобщать.")
            return
            
        # Отправляем "печатает..." статус
        await message.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # Создаем саммари
        history._create_summary()
        
        # Отправляем результат
        await message.answer(f"✅ Саммари создано:\n\n{history.summary}")
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при создании саммари: {str(e)}")

async def cmd_group_members(message: Message) -> None:
    """Показать текущий состав группы"""
    try:
        members = group_service.get_formatted_members(message.chat.id)
        await message.answer(members)
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при получении состава группы: {str(e)}")

async def cmd_join_group(message: Message) -> None:
    """Добавить активного персонажа в группу"""
    try:
        active_character = character_service.get_active_character(message.from_user.id)
        
        if not active_character:
            await message.answer("❌ У вас нет активного персонажа. Сначала создайте и активируйте персонажа.")
            return
            
        if group_service.add_member(message.chat.id, message.from_user.id, active_character):
            await message.answer(f"✅ {active_character['name']} присоединился к группе!")
        else:
            await message.answer(f"❌ {active_character['name']} уже состоит в группе.")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при присоединении к группе: {str(e)}")

async def cmd_leave_group(message: Message) -> None:
    """Удалить активного персонажа из группы"""
    try:
        active_character = character_service.get_active_character(message.from_user.id)
        
        if not active_character:
            await message.answer("❌ У вас нет активного персонажа.")
            return
            
        if group_service.remove_member(message.chat.id, active_character['name']):
            await message.answer(f"✅ {active_character['name']} покинул группу.")
        else:
            await message.answer(f"❌ {active_character['name']} не состоит в группе.")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при выходе из группы: {str(e)}")

async def cmd_remove_member(message: Message) -> None:
    """Удалить участника из группы"""
    try:
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
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при удалении участника: {str(e)}")

async def cmd_roll(message: Message) -> None:
    """Бросок кубиков в формате /roll ndm или /roll для броска 1d20"""
    try:
        # Получаем аргументы команды
        args = message.text.split()
        
        # Если аргументов нет, используем 1d20 по умолчанию
        if len(args) == 1:
            num_dice = 1
            sides = 20
        else:
            # Парсим аргументы
            dice_str = args[1].lower()
            if 'd' not in dice_str:
                await message.answer("❌ Неверный формат. Используйте формат: <количество>d<грани>")
                return
                
            num_dice, sides = dice_str.split('d')
            try:
                num_dice = int(num_dice)
                sides = int(sides)
            except ValueError:
                await message.answer("❌ Количество кубиков и грани должны быть числами")
                return
                
            if num_dice < 1 or sides < 2:
                await message.answer("❌ Количество кубиков должно быть больше 0, а количество граней больше 1")
                return
            
        # Бросаем кубики
        rolls = [random.randint(1, sides) for _ in range(num_dice)]
        total = sum(rolls)
        
        # Формируем результат броска
        result = f"🎲 Бросок {num_dice}d{sides}:\n"
        result += f"Результаты: {', '.join(map(str, rolls))}\n"
        result += f"Сумма: {total}"
        
        # Отправляем результат пользователю
        await message.answer(result)
        
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Отправляем "печатает..." статус
        await message.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # Получаем ответ от OpenAI с учетом истории диалога
        response = await openai_service.get_response(
            user_id=user_id,
            user_message=result,
            chat_id=chat_id if message.chat.type != "private" else None
        )

        # TODO: Заменить старые вызов АИ на новый через РАГ
        
        # Проверяем, включен ли режим голосовых ответов
        if chat_settings_service.is_voice_enabled(chat_id):
            # Отправляем "говорит..." статус
            await message.bot.send_chat_action(chat_id=chat_id, action="record_voice")

            # Преобразуем ответ в голосовое сообщение
            audio_path = await voice_service.text_to_speech(response)

            # Отправляем "загружает голосовое сообщение..." статус
            await message.bot.send_chat_action(chat_id=chat_id, action="upload_voice")
            
            try:
                # Отправляем голосовое сообщение
                voice = FSInputFile(audio_path)
                await message.answer_voice(voice)
            finally:
                # Удаляем временный аудиофайл
                if os.path.exists(audio_path):
                    os.remove(audio_path)
        else:
            # Отправляем текстовый ответ
            await message.answer(response)
        
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при броске кубиков: {str(e)}")

async def cmd_delete_campaign(message: Message) -> None:
    """Удалить описание кампании"""
    chat_id = message.chat.id
    
    try:
        if campaign_service.delete_campaign(chat_id):
            await message.answer("✅ Описание кампании удалено!")
        else:
            await message.answer("❌ Произошла ошибка при удалении описания кампании.")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при удалении описания кампании: {str(e)}")

async def cmd_toggle_voice(message: Message) -> None:
    """Переключает режим голосовых ответов"""
    try:
        chat_id = message.chat.id
        is_enabled = chat_settings_service.toggle_voice(chat_id)
        status = "включен" if is_enabled else "выключен"
        await message.answer(f"✅ Режим голосовых ответов {status}")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка при переключении режима голосовых ответов: {str(e)}") 