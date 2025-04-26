import os
import sys
import json
import time
import requests
import threading
from pathlib import Path
from main import CryptoVault

class VaultSyncManager:
    def __init__(self, vault, sync_config_path=None):
        self.vault = vault
        self.sync_config_path = sync_config_path or os.path.join(vault.vault_path, "sync_config.json")
        self.sync_lock = threading.Lock()
        self.sync_interval = 60
        self.providers = {
            "s3": S3SyncProvider,
            "dropbox": DropboxSyncProvider,
            "local": LocalSyncProvider
        }
        self.load_config()
        
    def load_config(self):
        if os.path.exists(self.sync_config_path):
            with open(self.sync_config_path, "r") as f:
                self.config = json.load(f)
        else:
            self.config = {
                "enabled": False,
                "provider": "local",
                "settings": {},
                "last_sync": None,
                "sync_interval": 60
            }
            self.save_config()
            
    def save_config(self):
        with open(self.sync_config_path, "w") as f:
            json.dump(self.config, f, indent=2)
            
    def get_provider(self):
        provider_name = self.config.get("provider", "local")
        if provider_name not in self.providers:
            raise ValueError(f"Неизвестный провайдер: {provider_name}")
            
        provider_class = self.providers[provider_name]
        return provider_class(self.vault, self.config.get("settings", {}))
        
    def start_sync_thread(self):
        if not self.config.get("enabled", False):
            print("Синхронизация отключена")
            return False
            
        self.sync_thread = threading.Thread(target=self._sync_worker)
        self.sync_thread.daemon = True
        self.sync_thread.start()
        return True
        
    def _sync_worker(self):
        while True:
            try:
                with self.sync_lock:
                    self.sync()
                    self.config["last_sync"] = int(time.time())
                    self.save_config()
            except Exception as e:
                print(f"Ошибка синхронизации: {e}")
                
            time.sleep(self.config.get("sync_interval", 60))
            
    def sync(self):
        provider = self.get_provider()
        local_files = self._get_local_files()
        remote_files = provider.list_files()
        
        files_to_upload = [f for f in local_files if f not in remote_files]
        files_to_download = [f for f in remote_files if f not in local_files]
        
        for file_id in files_to_upload:
            print(f"Загрузка {file_id}...")
            file_path = os.path.join(self.vault.files_path, file_id)
            metadata_path = os.path.join(self.vault.metadata_path, file_id)
            
            provider.upload_file(file_id, file_path, metadata_path)
            
        for file_id in files_to_download:
            print(f"Скачивание {file_id}...")
            file_path = os.path.join(self.vault.files_path, file_id)
            metadata_path = os.path.join(self.vault.metadata_path, file_id)
            
            provider.download_file(file_id, file_path, metadata_path)
            
        return {
            "uploaded": len(files_to_upload),
            "downloaded": len(files_to_download),
            "total_remote": len(remote_files),
            "total_local": len(local_files)
        }
            
    def _get_local_files(self):
        return [f for f in os.listdir(self.vault.files_path) 
                if os.path.isfile(os.path.join(self.vault.files_path, f))]
                
    def configure(self, provider, settings):
        if provider not in self.providers:
            raise ValueError(f"Неизвестный провайдер: {provider}")
            
        self.config["provider"] = provider
        self.config["settings"] = settings
        self.config["enabled"] = True
        self.save_config()
        
        provider_instance = self.get_provider()
        provider_instance.validate_settings()
        
        return True
        
    def disable(self):
        self.config["enabled"] = False
        self.save_config()
        return True


class BaseSyncProvider:
    def __init__(self, vault, settings):
        self.vault = vault
        self.settings = settings
        
    def validate_settings(self):
        raise NotImplementedError()
        
    def list_files(self):
        raise NotImplementedError()
        
    def upload_file(self, file_id, file_path, metadata_path):
        raise NotImplementedError()
        
    def download_file(self, file_id, file_path, metadata_path):
        raise NotImplementedError()


class LocalSyncProvider(BaseSyncProvider):
    def validate_settings(self):
        sync_dir = self.settings.get("sync_dir")
        if not sync_dir:
            raise ValueError("Не указана директория для синхронизации")
            
        if not os.path.exists(sync_dir):
            os.makedirs(sync_dir)
            
        return True
        
    def list_files(self):
        sync_dir = self.settings.get("sync_dir")
        if not sync_dir or not os.path.exists(sync_dir):
            return []
            
        files_dir = os.path.join(sync_dir, "files")
        if not os.path.exists(files_dir):
            return []
            
        return [f for f in os.listdir(files_dir) if os.path.isfile(os.path.join(files_dir, f))]
        
    def upload_file(self, file_id, file_path, metadata_path):
        sync_dir = self.settings.get("sync_dir")
        if not sync_dir:
            raise ValueError("Не указана директория для синхронизации")
            
        files_dir = os.path.join(sync_dir, "files")
        metadata_dir = os.path.join(sync_dir, "metadata")
        
        os.makedirs(files_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)
        
        remote_file_path = os.path.join(files_dir, file_id)
        remote_metadata_path = os.path.join(metadata_dir, file_id)
        
        with open(file_path, "rb") as src, open(remote_file_path, "wb") as dst:
            dst.write(src.read())
            
        with open(metadata_path, "r") as src, open(remote_metadata_path, "w") as dst:
            dst.write(src.read())
        
    def download_file(self, file_id, file_path, metadata_path):
        sync_dir = self.settings.get("sync_dir")
        if not sync_dir:
            raise ValueError("Не указана директория для синхронизации")
            
        files_dir = os.path.join(sync_dir, "files")
        metadata_dir = os.path.join(sync_dir, "metadata")
        
        remote_file_path = os.path.join(files_dir, file_id)
        remote_metadata_path = os.path.join(metadata_dir, file_id)
        
        if not os.path.exists(remote_file_path) or not os.path.exists(remote_metadata_path):
            raise FileNotFoundError(f"Файл {file_id} не найден в удаленном хранилище")
            
        with open(remote_file_path, "rb") as src, open(file_path, "wb") as dst:
            dst.write(src.read())
            
        with open(remote_metadata_path, "r") as src, open(metadata_path, "w") as dst:
            dst.write(src.read())


class S3SyncProvider(BaseSyncProvider):
    def validate_settings(self):
        required = ["access_key", "secret_key", "bucket", "region"]
        for field in required:
            if field not in self.settings:
                raise ValueError(f"Отсутствует обязательное поле: {field}")
                
        try:
            import boto3
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=self.settings["access_key"],
                aws_secret_access_key=self.settings["secret_key"],
                region_name=self.settings["region"]
            )
            self.s3.head_bucket(Bucket=self.settings["bucket"])
        except ImportError:
            raise ImportError("Для синхронизации с S3 необходимо установить boto3")
        except Exception as e:
            raise ValueError(f"Ошибка подключения к S3: {e}")
            
        return True
        
    def list_files(self):
        try:
            import boto3
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=self.settings["access_key"],
                aws_secret_access_key=self.settings["secret_key"],
                region_name=self.settings["region"]
            )
            
            response = self.s3.list_objects_v2(
                Bucket=self.settings["bucket"],
                Prefix="files/"
            )
            
            if "Contents" not in response:
                return []
                
            return [os.path.basename(item["Key"]) for item in response["Contents"] 
                    if not item["Key"].endswith("/")]
        except Exception as e:
            print(f"Ошибка получения списка файлов из S3: {e}")
            return []
        
    def upload_file(self, file_id, file_path, metadata_path):
        try:
            import boto3
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=self.settings["access_key"],
                aws_secret_access_key=self.settings["secret_key"],
                region_name=self.settings["region"]
            )
            
            self.s3.upload_file(
                file_path,
                self.settings["bucket"],
                f"files/{file_id}"
            )
            
            self.s3.upload_file(
                metadata_path,
                self.settings["bucket"],
                f"metadata/{file_id}"
            )
        except Exception as e:
            raise Exception(f"Ошибка загрузки файла в S3: {e}")
        
    def download_file(self, file_id, file_path, metadata_path):
        try:
            import boto3
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=self.settings["access_key"],
                aws_secret_access_key=self.settings["secret_key"],
                region_name=self.settings["region"]
            )
            
            self.s3.download_file(
                self.settings["bucket"],
                f"files/{file_id}",
                file_path
            )
            
            self.s3.download_file(
                self.settings["bucket"],
                f"metadata/{file_id}",
                metadata_path
            )
        except Exception as e:
            raise Exception(f"Ошибка скачивания файла из S3: {e}")


class DropboxSyncProvider(BaseSyncProvider):
    def validate_settings(self):
        if "access_token" not in self.settings:
            raise ValueError("Отсутствует токен доступа")
            
        try:
            import dropbox
            dbx = dropbox.Dropbox(self.settings["access_token"])
            dbx.users_get_current_account()
        except ImportError:
            raise ImportError("Для синхронизации с Dropbox необходимо установить dropbox")
        except Exception as e:
            raise ValueError(f"Ошибка подключения к Dropbox: {e}")
            
        return True
        
    def list_files(self):
        try:
            import dropbox
            dbx = dropbox.Dropbox(self.settings["access_token"])
            
            result = dbx.files_list_folder("/files")
            files = [entry.name for entry in result.entries if isinstance(entry, dropbox.files.FileMetadata)]
            
            while result.has_more:
                result = dbx.files_list_folder_continue(result.cursor)
                files.extend([entry.name for entry in result.entries if isinstance(entry, dropbox.files.FileMetadata)])
                
            return files
        except Exception as e:
            print(f"Ошибка получения списка файлов из Dropbox: {e}")
            return []
        
    def upload_file(self, file_id, file_path, metadata_path):
        try:
            import dropbox
            dbx = dropbox.Dropbox(self.settings["access_token"])
            
            with open(file_path, "rb") as f:
                dbx.files_upload(f.read(), f"/files/{file_id}", mode=dropbox.files.WriteMode.overwrite)
                
            with open(metadata_path, "rb") as f:
                dbx.files_upload(f.read(), f"/metadata/{file_id}", mode=dropbox.files.WriteMode.overwrite)
        except Exception as e:
            raise Exception(f"Ошибка загрузки файла в Dropbox: {e}")
        
    def download_file(self, file_id, file_path, metadata_path):
        try:
            import dropbox
            dbx = dropbox.Dropbox(self.settings["access_token"])
            
            file_result = dbx.files_download_to_file(file_path, f"/files/{file_id}")
            metadata_result = dbx.files_download_to_file(metadata_path, f"/metadata/{file_id}")
        except Exception as e:
            raise Exception(f"Ошибка скачивания файла из Dropbox: {e}")


def main():
    import argparse
    from main import CryptoVault
    
    parser = argparse.ArgumentParser(description="Утилита синхронизации CryptoVault")
    parser.add_argument("--vault-path", help="Путь к хранилищу")
    
    subparsers = parser.add_subparsers(dest="command", help="Команды")
    subparsers.required = True
    
    sync_parser = subparsers.add_parser("sync", help="Запустить синхронизацию")
    
    config_parser = subparsers.add_parser("config", help="Настроить синхронизацию")
    config_parser.add_argument("provider", choices=["local", "s3", "dropbox"], help="Провайдер синхронизации")
    config_parser.add_argument("--settings", help="Настройки в формате JSON")
    
    disable_parser = subparsers.add_parser("disable", help="Отключить синхронизацию")
    
    status_parser = subparsers.add_parser("status", help="Показать статус синхронизации")
    
    args = parser.parse_args()
    vault = CryptoVault(args.vault_path)
    sync_manager = VaultSyncManager(vault)
    
    if args.command == "sync":
        try:
            result = sync_manager.sync()
            print(f"Синхронизация завершена:")
            print(f"  - Загружено: {result['uploaded']}")
            print(f"  - Скачано: {result['downloaded']}")
            print(f"  - Всего файлов (локально): {result['total_local']}")
            print(f"  - Всего файлов (удаленно): {result['total_remote']}")
        except Exception as e:
            print(f"Ошибка синхронизации: {e}")
            
    elif args.command == "config":
        try:
            settings = json.loads(args.settings) if args.settings else {}
            sync_manager.configure(args.provider, settings)
            print(f"Синхронизация настроена, провайдер: {args.provider}")
        except Exception as e:
            print(f"Ошибка настройки синхронизации: {e}")
            
    elif args.command == "disable":
        sync_manager.disable()
        print("Синхронизация отключена")
        
    elif args.command == "status":
        config = sync_manager.config
        print(f"Статус синхронизации:")
        print(f"  - Активна: {'Да' if config.get('enabled', False) else 'Нет'}")
        print(f"  - Провайдер: {config.get('provider', 'не настроен')}")
        
        if config.get("last_sync"):
            last_sync = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(config["last_sync"]))
            print(f"  - Последняя синхронизация: {last_sync}")
        else:
            print("  - Последняя синхронизация: никогда")
            
        print(f"  - Интервал синхронизации: {config.get('sync_interval', 60)} секунд")

if __name__ == "__main__":
    main() 