import subprocess
import shlex
import logging
import os

# Налаштування логера для виводу в консоль
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_ffmpeg_conversion(input_file):
    """
    Тестує конвертацію одного файлу за допомогою ffmpeg.
    """
    if not os.path.exists(input_file):
        logging.error(f"Вхідний файл не знайдено: {input_file}")
        return

    output_file = f"{os.path.splitext(input_file)[0]}.wav"
    logging.info(f"Починаю конвертацію '{input_file}' в '{output_file}'")

    # Використовується той самий метод, що і в додатку
    command = (
        f"ffmpeg -nostdin -i {shlex.quote(input_file)} "
        f"-ac 1 -ar 16000 "
        f"{shlex.quote(output_file)} -y"
    )
    logging.info(f"Виконую команду: {command}")

    try:
        process = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True, # Захоплюється вивід для аналізу
            text=True
        )
        logging.info("Команда успішно виконана!")
        if process.stdout:
            logging.info(f"STDOUT:\n{process.stdout}")
        if process.stderr:
            # ffmpeg часто пише прогрес в stderr, тому це не завжди помилка
            logging.warning(f"STDERR:\n{process.stderr}")
        
        if os.path.exists(output_file):
            logging.info(f"Успіх! Вихідний файл '{output_file}' створено.")
        else:
            logging.error("Помилка! Файл не було створено, хоча команда не повернула помилку.")

    except subprocess.CalledProcessError as e:
        logging.error(f"Команда завершилась з помилкою! Код повернення: {e.returncode}")
        logging.error(f"STDOUT:\n{e.stdout}")
        logging.error(f"STDERR:\n{e.stderr}")
    except Exception as e:
        logging.error(f"Виникла несподівана помилка: {e}")

if __name__ == "__main__":
    # Файл для тестування
    test_file = "1180170c-35cb-47e4-9189-17686986eb7a---Upwork Meeting Jul 11 2025 Recording.mp4"
    test_ffmpeg_conversion(test_file)
