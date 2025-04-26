import os
import sys
import argparse
import getpass
from tabulate import tabulate
from datetime import datetime
from main import CryptoVault

def get_size_str(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def encrypt_command(args):
    vault = CryptoVault(args.vault_path)
    password = args.password or getpass.getpass("Введите пароль для шифрования: ")
    
    try:
        file_id = vault.encrypt_file(args.file, password)
        print(f"✅ Файл успешно зашифрован")
        print(f"📝 ID файла: {file_id}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

def decrypt_command(args):
    vault = CryptoVault(args.vault_path)
    password = args.password or getpass.getpass("Введите пароль для расшифровки: ")
    
    try:
        output_path = vault.decrypt_file(args.file_id, password, args.output)
        print(f"✅ Файл успешно расшифрован и сохранен: {output_path}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

def list_command(args):
    vault = CryptoVault(args.vault_path)
    files = vault.list_files()
    
    if not files:
        print("📂 Хранилище пусто")
        return
    
    table_data = []
    for file in files:
        id_display = file["id"][:8] + "..." if not args.full_id else file["id"]
        timestamp = datetime.fromisoformat(file["timestamp"])
        date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        size_str = get_size_str(file["size"])
        
        table_data.append([id_display, file["filename"], date_str, size_str])
    
    print(tabulate(
        table_data,
        headers=["ID", "Имя файла", "Дата", "Размер"],
        tablefmt="fancy_grid"
    ))
    print(f"Всего файлов: {len(files)}")

def delete_command(args):
    vault = CryptoVault(args.vault_path)
    
    try:
        vault.delete_file(args.file_id)
        print(f"✅ Файл {args.file_id} успешно удален из хранилища")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

def info_command(args):
    vault = CryptoVault(args.vault_path)
    
    try:
        total_size = 0
        file_count = 0
        
        for file_id in os.listdir(vault.files_path):
            file_path = os.path.join(vault.files_path, file_id)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
                file_count += 1
        
        print("📊 Информация о хранилище:")
        print(f"📁 Путь: {vault.vault_path}")
        print(f"🔢 Количество файлов: {file_count}")
        print(f"💾 Общий размер: {get_size_str(total_size)}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="CryptoVault - безопасное хранилище файлов с шифрованием",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--vault-path", help="Путь к хранилищу")
    
    subparsers = parser.add_subparsers(dest="command", help="Команды")
    subparsers.required = True
    
    encrypt_parser = subparsers.add_parser("encrypt", help="Зашифровать файл")
    encrypt_parser.add_argument("file", help="Путь к файлу для шифрования")
    encrypt_parser.add_argument("-p", "--password", help="Пароль для шифрования (если не указан, будет запрошен)")
    encrypt_parser.set_defaults(func=encrypt_command)
    
    decrypt_parser = subparsers.add_parser("decrypt", help="Расшифровать файл")
    decrypt_parser.add_argument("file_id", help="ID файла для расшифровки")
    decrypt_parser.add_argument("-o", "--output", help="Путь для сохранения расшифрованного файла")
    decrypt_parser.add_argument("-p", "--password", help="Пароль для расшифровки (если не указан, будет запрошен)")
    decrypt_parser.set_defaults(func=decrypt_command)
    
    list_parser = subparsers.add_parser("list", help="Показать список файлов в хранилище")
    list_parser.add_argument("--full-id", action="store_true", help="Показывать полный ID файла")
    list_parser.set_defaults(func=list_command)
    
    delete_parser = subparsers.add_parser("delete", help="Удалить файл из хранилища")
    delete_parser.add_argument("file_id", help="ID файла для удаления")
    delete_parser.set_defaults(func=delete_command)
    
    info_parser = subparsers.add_parser("info", help="Показать информацию о хранилище")
    info_parser.set_defaults(func=info_command)
    
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main() 