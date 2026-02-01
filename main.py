import os
import logging
import time
from telebot import TeleBot, types
from transformers import pipeline, set_seed
import torch

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота (замените на свой из @BotFather)
TOKEN = ""

# Инициализация бота
bot = TeleBot(TOKEN)

# Глобальная переменная для пайплайна
text_generator = None

def load_model():
    """Загрузка модели с обработкой ошибок"""
    global text_generator
    try:
        logger.info("Загрузка модели rugpt3medium_based_on_gpt2...")
        
        device = 0 if torch.cuda.is_available() else -1
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        
        text_generator = pipeline(
            "text-generation",
            model="ai-forever/rugpt3medium_based_on_gpt2",
            device=device,
            torch_dtype=torch_dtype,
            max_length=150,
            truncation=True
        )
        logger.info("Модель успешно загружена!")
        return True
    except Exception as e:
        logger.error(f"Ошибка загрузки модели: {e}")
        return False

model_loaded = load_model()

# Клавиатура главного меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("🎁 Помоги выбрать подарок"))
    return markup

# Клавиатура выбора бюджета
def budget_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    budgets = ["💰 До 1000₽", "💰 2500-3000₽", "💰 5000-15000₽", "💰 50000-150000₽"]
    markup.add(*[types.KeyboardButton(text) for text in budgets])
    markup.add(types.KeyboardButton("🔙 Назад"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Привет! 😊 Я — бот-помощник по подбору подарков.\n"
        "Расскажу идеи подарков под любой бюджет!\n\n"
        "Нажми кнопку ниже, чтобы начать:",
        reply_markup=main_menu()
    )

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    text = message.text
    
    if text == "🎁 Помоги выбрать подарок":
        bot.send_message(
            message.chat.id,
            "Выбери подходящий бюджет:",
            reply_markup=budget_menu()
        )
    
    elif text in ["💰 До 1000₽", "💰 2500-3000₽", "💰 5000-15000₽", "💰 50000-150000₽"]:
        budget_map = {
            "💰 До 1000₽": "1000",
            "💰 2500-3000₽": "3000",
            "💰 5000-15000₽": "15000",
            "💰 50000-150000₽": "150000"
        }
        budget = budget_map[text]
        
        # Отправляем сообщение "думаем" БЕЗ клавиатуры
        thinking_msg = bot.send_message(
            message.chat.id,
            "✨ Генерирую идею подарка...\nЭто может занять 15-30 секунд",
            reply_markup=types.ReplyKeyboardRemove()  # Убираем клавиатуру
        )
        
        try:
            if not model_loaded:
                raise Exception("Модель не загружена")
            
            # Формируем промпт
            prompt = (
                f"Предложи оригинальный и практичный подарок для взрослого человека с бюджетом до {budget} рублей. "
                f"Назови 1-2 конкретных варианта с кратким описанием."
            )
            
            set_seed(int(time.time()))  # Уникальное семя для разнообразия
            result = text_generator(
                prompt,
                max_length=150,
                num_return_sequences=1,
                temperature=0.85,
                top_k=50,
                top_p=0.95,
                do_sample=True
            )
            
            # Обработка результата
            generated_text = result[0]['generated_text']
            idea = generated_text.replace(prompt, "").strip()
            
            # Очистка текста от артефактов
            idea = idea.split('\n')[0].split('  ')[0].strip()
            if not idea or len(idea) < 10:
                idea = "Качественный термос с индивидуальной гравировкой — практичный и личный подарок, который будет радовать каждый день."
            
            response = (
                f"🎁 Идея подарка (бюджет до {budget}₽):\n\n"
                f"{idea}\n\n"
                f"💡 Совет: уточните у получателя предпочтения перед покупкой!"
            )
            
            # УДАЛЯЕМ сообщение "думаем" (НЕ редактируем!)
            try:
                bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=thinking_msg.message_id
                )
            except Exception as e:
                logger.warning(f"Не удалось удалить сообщение: {e}")
            
            # Отправляем результат с обычной клавиатурой
            bot.send_message(
                message.chat.id,
                response,
                reply_markup=main_menu()
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации: {e}")
            
            # Удаляем сообщение "думаем"
            try:
                bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=thinking_msg.message_id
                )
            except:
                pass
            
            # Отправляем ошибку с клавиатурой
            fallback_gifts = {
                "1000": "• Подарочный сертификат на кофе\n• Набор ароматических свечей\n• Красивый ежедневник",
                "3000": "• Беспроводная колонка\n• Набор для выращивания растений\n• Подписка на онлайн-кинотеатр на 3 месяца",
                "15000": "• Умная лампа Philips Hue\n• Качественный рюкзак от известного бренда\n• Набор для барбекю премиум-класса",
                "150000": "• Планшет среднего класса\n• Профессиональная кофемашина\n• Сертификат на мастер-класс по кулинарии/керамике"
            }
            
            budget_key = budget_map[text]
            bot.send_message(
                message.chat.id,
                f"⚠️ Не удалось сгенерировать идею (ошибка: {str(e)[:50]}).\n\n"
                f"Вот готовые варианты для бюджета до {budget}₽:\n\n"
                f"{fallback_gifts.get(budget_key, fallback_gifts['1000'])}\n\n"
                f"Попробуйте снова через минуту.",
                reply_markup=main_menu()
            )
    
    elif text == "🔙 Назад":
        bot.send_message(
            message.chat.id,
            "Выбери действие:",
            reply_markup=main_menu()
        )
    
    else:
        bot.send_message(
            message.chat.id,
            "Не понимаю эту команду 😅\nИспользуй кнопки меню:",
            reply_markup=main_menu()
        )

if __name__ == '__main__':
    if TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("❌ Установите TELEGRAM_BOT_TOKEN в переменных окружения!")
        exit(1)
    
    logger.info("="*60)
    logger.info("БОТ ЗАПУЩЕН! Важные замечания:")
    logger.info("• Первый запуск модели займёт 20-40 секунд")
    logger.info("• Требуется минимум 2 ГБ ОЗУ")
    logger.info("• Для продакшена используйте сервер с 4+ ГБ ОЗУ")
    logger.info("="*60)
    
    bot.polling(none_stop=True, interval=0, timeout=20)