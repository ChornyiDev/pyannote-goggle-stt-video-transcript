import logging
import os
from logging.handlers import RotatingFileHandler

# Створюємо каталог для логів, якщо його немає
if not os.path.exists('logs'):
    os.makedirs('logs')

# Налаштування логгера
logger = logging.getLogger('pyannote-api')
logger.setLevel(logging.INFO)

# Створюємо обробник, який буде записувати логи у файл
# RotatingFileHandler автоматично керуватиме розміром файлу
file_handler = RotatingFileHandler('logs/app.log', maxBytes=5*1024*1024, backupCount=2)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Створюємо обробник для виводу логів у консоль
stream_handler = logging.StreamHandler()
stream_formatter = logging.Formatter('%(levelname)s: %(message)s')
stream_handler.setFormatter(stream_formatter)

# Додаємо обробники до логгера
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
