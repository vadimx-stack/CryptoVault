import os
import sys
import hashlib
import base64
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime

class CryptoVault:
    def __init__(self, vault_path=None):
        self.vault_path = vault_path or os.path.join(os.path.expanduser("~"), ".cryptovault")
        self.index_path = os.path.join(self.vault_path, "index.db")
        self.files_path = os.path.join(self.vault_path, "files")
        self.metadata_path = os.path.join(self.vault_path, "metadata")
        self.initialize_vault()
        
    def initialize_vault(self):
        for path in [self.vault_path, self.files_path, self.metadata_path]:
            if not os.path.exists(path):
                os.makedirs(path)
                
        if not os.path.exists(self.index_path):
            with open(self.index_path, "w") as f:
                f.write("{}")
                
    def generate_key(self, password, salt=None):
        if salt is None:
            salt = secrets.token_bytes(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def encrypt_file(self, file_path, password):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found")
            
        file_id = self.generate_file_id(file_path)
        key, salt = self.generate_key(password)
        fernet = Fernet(key)
        
        with open(file_path, "rb") as f:
            data = f.read()
            
        encrypted_data = fernet.encrypt(data)
        encrypted_path = os.path.join(self.files_path, file_id)
        
        with open(encrypted_path, "wb") as f:
            f.write(encrypted_data)
            
        self.save_metadata(file_id, file_path, salt)
        return file_id
    
    def decrypt_file(self, file_id, password, output_path=None):
        encrypted_path = os.path.join(self.files_path, file_id)
        metadata_path = os.path.join(self.metadata_path, file_id)
        
        if not os.path.exists(encrypted_path) or not os.path.exists(metadata_path):
            raise FileNotFoundError(f"File {file_id} not found in vault")
            
        with open(metadata_path, "r") as f:
            metadata = eval(f.read())
            
        salt = metadata["salt"]
        original_path = metadata["original_path"]
        
        key, _ = self.generate_key(password, salt=base64.b64decode(salt))
        fernet = Fernet(key)
        
        with open(encrypted_path, "rb") as f:
            encrypted_data = f.read()
            
        try:
            decrypted_data = fernet.decrypt(encrypted_data)
        except Exception:
            raise ValueError("Invalid password or corrupted file")
        
        output_path = output_path or original_path
        with open(output_path, "wb") as f:
            f.write(decrypted_data)
            
        return output_path
    
    def generate_file_id(self, file_path):
        filename = os.path.basename(file_path)
        timestamp = datetime.now().isoformat()
        random_suffix = secrets.token_hex(4)
        data = f"{filename}_{timestamp}_{random_suffix}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def save_metadata(self, file_id, original_path, salt):
        metadata = {
            "original_path": original_path,
            "original_filename": os.path.basename(original_path),
            "timestamp": datetime.now().isoformat(),
            "salt": base64.b64encode(salt).decode(),
            "size": os.path.getsize(original_path)
        }
        
        metadata_path = os.path.join(self.metadata_path, file_id)
        with open(metadata_path, "w") as f:
            f.write(str(metadata))
    
    def list_files(self):
        files = []
        for file_id in os.listdir(self.metadata_path):
            metadata_path = os.path.join(self.metadata_path, file_id)
            with open(metadata_path, "r") as f:
                metadata = eval(f.read())
            files.append({
                "id": file_id,
                "filename": metadata["original_filename"],
                "timestamp": metadata["timestamp"],
                "size": metadata["size"]
            })
        return files
    
    def delete_file(self, file_id):
        encrypted_path = os.path.join(self.files_path, file_id)
        metadata_path = os.path.join(self.metadata_path, file_id)
        
        if not os.path.exists(encrypted_path) or not os.path.exists(metadata_path):
            raise FileNotFoundError(f"File {file_id} not found in vault")
            
        os.remove(encrypted_path)
        os.remove(metadata_path)

def main():
    if len(sys.argv) < 2:
        print("Использование: python main.py [encrypt|decrypt|list|delete] [аргументы]")
        sys.exit(1)
        
    vault = CryptoVault()
    command = sys.argv[1]
    
    if command == "encrypt":
        if len(sys.argv) != 4:
            print("Использование: python main.py encrypt <путь_к_файлу> <пароль>")
            sys.exit(1)
            
        file_path = sys.argv[2]
        password = sys.argv[3]
        
        try:
            file_id = vault.encrypt_file(file_path, password)
            print(f"Файл зашифрован. ID: {file_id}")
        except Exception as e:
            print(f"Ошибка: {e}")
            
    elif command == "decrypt":
        if len(sys.argv) < 4:
            print("Использование: python main.py decrypt <file_id> <пароль> [путь_для_сохранения]")
            sys.exit(1)
            
        file_id = sys.argv[2]
        password = sys.argv[3]
        output_path = sys.argv[4] if len(sys.argv) > 4 else None
        
        try:
            path = vault.decrypt_file(file_id, password, output_path)
            print(f"Файл расшифрован и сохранен: {path}")
        except Exception as e:
            print(f"Ошибка: {e}")
            
    elif command == "list":
        files = vault.list_files()
        if not files:
            print("Хранилище пусто")
        else:
            print(f"{'ID':<10} | {'Имя файла':<30} | {'Дата':<25} | {'Размер':<10}")
            print("-" * 80)
            for file in files:
                id_short = file["id"][:8] + "..."
                date = file["timestamp"].split("T")[0]
                size = f"{file['size'] / 1024:.2f} KB"
                print(f"{id_short:<10} | {file['filename']:<30} | {date:<25} | {size:<10}")
                
    elif command == "delete":
        if len(sys.argv) != 3:
            print("Использование: python main.py delete <file_id>")
            sys.exit(1)
            
        file_id = sys.argv[2]
        
        try:
            vault.delete_file(file_id)
            print(f"Файл {file_id} удален из хранилища")
        except Exception as e:
            print(f"Ошибка: {e}")
            
    else:
        print(f"Неизвестная команда: {command}")
        print("Доступные команды: encrypt, decrypt, list, delete")
        sys.exit(1)

if __name__ == "__main__":
    main() 