import os
import tempfile
import unittest
import shutil
from main import CryptoVault

class TestCryptoVault(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.vault = CryptoVault(self.test_dir)
        self.test_file_content = b"This is a test file content for encryption testing"
        
        self.test_file = os.path.join(self.test_dir, "test_file.txt")
        with open(self.test_file, "wb") as f:
            f.write(self.test_file_content)
        
        self.password = "test_password"
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_encrypt_decrypt_file(self):
        file_id = self.vault.encrypt_file(self.test_file, self.password)
        
        self.assertTrue(os.path.exists(os.path.join(self.vault.files_path, file_id)))
        self.assertTrue(os.path.exists(os.path.join(self.vault.metadata_path, file_id)))
        
        output_file = os.path.join(self.test_dir, "decrypted_file.txt")
        result_path = self.vault.decrypt_file(file_id, self.password, output_file)
        
        self.assertEqual(result_path, output_file)
        
        with open(output_file, "rb") as f:
            decrypted_content = f.read()
        
        self.assertEqual(decrypted_content, self.test_file_content)
    
    def test_list_files(self):
        file_id1 = self.vault.encrypt_file(self.test_file, self.password)
        
        with open(os.path.join(self.test_dir, "test_file2.txt"), "wb") as f:
            f.write(b"Another test file")
        
        file_id2 = self.vault.encrypt_file(os.path.join(self.test_dir, "test_file2.txt"), self.password)
        
        files = self.vault.list_files()
        
        self.assertEqual(len(files), 2)
        self.assertIn(file_id1, [f["id"] for f in files])
        self.assertIn(file_id2, [f["id"] for f in files])
    
    def test_delete_file(self):
        file_id = self.vault.encrypt_file(self.test_file, self.password)
        
        self.assertTrue(os.path.exists(os.path.join(self.vault.files_path, file_id)))
        self.assertTrue(os.path.exists(os.path.join(self.vault.metadata_path, file_id)))
        
        self.vault.delete_file(file_id)
        
        self.assertFalse(os.path.exists(os.path.join(self.vault.files_path, file_id)))
        self.assertFalse(os.path.exists(os.path.join(self.vault.metadata_path, file_id)))
    
    def test_wrong_password(self):
        file_id = self.vault.encrypt_file(self.test_file, self.password)
        
        output_file = os.path.join(self.test_dir, "decrypted_file.txt")
        
        with self.assertRaises(ValueError):
            self.vault.decrypt_file(file_id, "wrong_password", output_file)
    
    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.vault.encrypt_file("non_existent_file.txt", self.password)
        
        with self.assertRaises(FileNotFoundError):
            self.vault.decrypt_file("non_existent_file_id", self.password)
    
    def test_file_metadata(self):
        file_id = self.vault.encrypt_file(self.test_file, self.password)
        
        metadata_path = os.path.join(self.vault.metadata_path, file_id)
        with open(metadata_path, "r") as f:
            metadata = eval(f.read())
        
        self.assertEqual(metadata["original_path"], self.test_file)
        self.assertEqual(metadata["original_filename"], os.path.basename(self.test_file))
        self.assertEqual(metadata["size"], len(self.test_file_content))
        self.assertIn("timestamp", metadata)
        self.assertIn("salt", metadata)

if __name__ == "__main__":
    unittest.main() 