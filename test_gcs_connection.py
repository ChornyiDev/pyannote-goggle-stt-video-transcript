import os
from dotenv import load_dotenv
from google.cloud import storage
from google.api_core import exceptions

# Завантажуємо змінні середовища з файлу .env
load_dotenv()

def test_gcs_connection():
    """
    Перевіряє підключення до Google Cloud Storage та доступ до вказаного сховища.
    """
    print("--- Початок тесту підключення до GCS ---")

    # 1. Перевірка наявності змінної середовища
    bucket_name_full = os.getenv('FIREBASE_STORAGE_BUCKET')
    if not bucket_name_full:
        print("ПОМИЛКА: Змінна середовища FIREBASE_STORAGE_BUCKET не знайдена у файлі .env.")
        return

    print(f"Знайдено повну назву сховища: {bucket_name_full}")

    # 2. Використання повної назви сховища без змін
    parsed_bucket_name = bucket_name_full
    print(f"Спроба підключення до сховища з назвою: '{parsed_bucket_name}'")

    # 3. Перевірка облікових даних
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        print("ПОМИЛКА: Змінна середовища GOOGLE_APPLICATION_CREDENTIALS не знайдена.")
        print("Переконайтеся, що у файлі .env є рядок: GOOGLE_APPLICATION_CREDENTIALS=service_account.json")
        return
    
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not os.path.exists(credentials_path):
        print(f"ПОМИЛКА: Файл облікових даних '{credentials_path}' не знайдено.")
        return
    
    print(f"Використовую файл облікових даних: {credentials_path}")

    # 4. Спроба підключення
    try:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(parsed_bucket_name)
        print("\n✅ УСПІХ! Підключення до сховища успішне.")
        print(f"  ID Сховища: {bucket.id}")
        print(f"  Назва: {bucket.name}")
        print(f"  Розташування: {bucket.location}")
        print(f"  Час створення: {bucket.time_created}")

    except exceptions.NotFound:
        print(f"\n❌ ПОМИЛКА 404: Сховище з назвою '{parsed_bucket_name}' не знайдено.")
        print("  Перевірте, чи правильно вказана назва у FIREBASE_STORAGE_BUCKET у файлі .env.")
        print("  Також необхідно переконатися, що сервісний акаунт має дозвіл 'Storage Object Viewer' для цього сховища.")
    
    except exceptions.Forbidden:
        print(f"\n❌ ПОМИЛКА 403: Доступ до сховища '{parsed_bucket_name}' заборонено.")
        print("  Це означає, що облікові дані правильні, але у сервісного акаунта недостатньо прав.")
        print("  Необхідно перейти у Google Cloud Console -> IAM & Admin -> Service Accounts,")
        print("  знайти відповідний акаунт та надати йому роль 'Storage Admin' або принаймні 'Storage Object Admin'.")

    except Exception as e:
        print(f"\n❌ ВИНИКЛА ІНША ПОМИЛКА: {e}")

    print("\n--- Тест завершено ---")


if __name__ == "__main__":
    test_gcs_connection()
