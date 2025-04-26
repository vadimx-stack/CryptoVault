# 🔐 CryptoVault

<div align="center">
  
![Python](https://img.shields.io/badge/Python-3.6%2B-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Cryptography](https://img.shields.io/badge/Cryptography-AES--256--GCM-red?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)

**Безопасное хранилище файлов с шифрованием и синхронизацией в облаке**

</div>

## 📋 Содержание

- [✨ Особенности](#-особенности)
- [🚀 Быстрый старт](#-быстрый-старт)
- [🔧 Установка](#-установка)
- [📝 Использование](#-использование)
  - [🖥️ Командная строка](#️-командная-строка)
  - [🌐 REST API](#-rest-api)
  - [☁️ Синхронизация](#️-синхронизация)
  - [📚 API для разработчиков](#-api-для-разработчиков)
- [🏗️ Архитектура](#️-архитектура)
- [🔒 Безопасность](#-безопасность)
- [📜 Лицензия](#-лицензия)

## ✨ Особенности

- **Надежное шифрование** — используются проверенные алгоритмы для защиты ваших данных
- **Метаданные файлов** — отслеживание информации о файлах без доступа к их содержимому
- **Удобный CLI интерфейс** — работа с хранилищем из командной строки
- **REST API** — легкая интеграция с другими приложениями
- **Облачная синхронизация** — поддержка S3, Dropbox и локальных хранилищ
- **Расширяемость** — возможность использования как библиотеки в ваших проектах

## 🚀 Быстрый старт

```bash
# Установка
pip install -r requirements.txt

# Шифрование файла
python cli.py encrypt /path/to/secret.txt

# Просмотр файлов в хранилище
python cli.py list

# Расшифровка
python cli.py decrypt <ID_файла> -o /path/to/output.txt
```

## 🔧 Установка

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Готово! Хранилище настроено и готово к использованию.

## 📝 Использование

### 🖥️ Командная строка

CryptoVault предоставляет удобный интерфейс командной строки для всех основных операций.

| Команда | Описание | Пример |
|---------|----------|--------|
| `encrypt` | Зашифровать файл | `python cli.py encrypt /path/to/file.txt` |
| `decrypt` | Расшифровать файл | `python cli.py decrypt <file_id> -o /path/to/output.txt` |
| `list` | Список файлов | `python cli.py list` |
| `delete` | Удалить файл | `python cli.py delete <file_id>` |
| `info` | Информация о хранилище | `python cli.py info` |

### 🌐 REST API

Запустите API сервер для доступа к функциям CryptoVault через HTTP:

```bash
python vault_api.py
```

| Эндпоинт | Метод | Описание |
|----------|-------|----------|
| `/api/files` | GET | Получить список файлов |
| `/api/files` | POST | Зашифровать файл |
| `/api/files/<file_id>` | GET | Расшифровать файл |
| `/api/files/<file_id>` | DELETE | Удалить файл |
| `/api/health` | GET | Статус сервера |

### ☁️ Синхронизация

CryptoVault поддерживает синхронизацию с различными облачными хранилищами:

```bash
# Локальное хранилище
python sync.py config local --settings '{"sync_dir": "/path/to/sync"}'

# Amazon S3
python sync.py config s3 --settings '{"access_key": "YOUR_KEY", "secret_key": "YOUR_SECRET", "bucket": "your-bucket", "region": "us-west-2"}'

# Dropbox
python sync.py config dropbox --settings '{"access_token": "YOUR_TOKEN"}'
```

Управление синхронизацией:

```bash
# Запуск синхронизации
python sync.py sync

# Проверка статуса
python sync.py status

# Отключение
python sync.py disable
```

### 📚 API для разработчиков

Используйте CryptoVault как библиотеку в своих проектах:

```python
from main import CryptoVault

# Инициализация хранилища
vault = CryptoVault()

# Шифрование файла
file_id = vault.encrypt_file("path/to/file.txt", "my_secure_password")

# Расшифровка
vault.decrypt_file(file_id, "my_secure_password", "path/to/output.txt")

# Получение списка файлов
files = vault.list_files()

# Удаление файла
vault.delete_file(file_id)
```

## 🏗️ Архитектура

Проект имеет модульную архитектуру:

```
cryptovault/
├── main.py        # Основной класс CryptoVault
├── cli.py         # Интерфейс командной строки
├── vault_api.py   # REST API сервер
├── sync.py        # Синхронизация с облачными сервисами
└── test_vault.py  # Модульные тесты
```

## 🔒 Безопасность

- **AES-256-GCM** — современный алгоритм шифрования с аутентификацией
- **PBKDF2** — защита паролей с использованием солей
- **Изоляция данных** — отдельное хранение метаданных и зашифрованных данных
- **Уникальные ключи** — для каждого файла генерируется свой ключ шифрования

## 📜 Лицензия

Распространяется под лицензией MIT. См. файл `LICENSE` для дополнительной информации. 