import os
import json
import base64
from flask import Flask, request, jsonify
from main import CryptoVault
import tempfile

app = Flask(__name__)
vault = CryptoVault()

@app.route('/api/files', methods=['GET'])
def list_files():
    files = vault.list_files()
    return jsonify({'files': files})

@app.route('/api/files', methods=['POST'])
def encrypt_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    password = request.form.get('password')
    
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp_file_path = temp.name
            file.save(temp_file_path)
        
        file_id = vault.encrypt_file(temp_file_path, password)
        return jsonify({'file_id': file_id, 'message': 'File encrypted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.route('/api/files/<file_id>', methods=['GET'])
def decrypt_file(file_id):
    password = request.args.get('password')
    
    if not password:
        return jsonify({'error': 'Password is required'}), 400
    
    try:
        temp_output = tempfile.NamedTemporaryFile(delete=False)
        temp_output.close()
        
        output_path = vault.decrypt_file(file_id, password, temp_output.name)
        
        with open(output_path, 'rb') as f:
            file_data = f.read()
        
        os.remove(output_path)
        
        metadata_path = os.path.join(vault.metadata_path, file_id)
        with open(metadata_path, 'r') as f:
            metadata = eval(f.read())
        
        return jsonify({
            'file_id': file_id,
            'filename': metadata['original_filename'],
            'data': base64.b64encode(file_data).decode('utf-8'),
            'size': len(file_data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    try:
        vault.delete_file(file_id)
        return jsonify({'message': f'File {file_id} deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'vault_path': vault.vault_path,
        'files_count': len(os.listdir(vault.files_path)) if os.path.exists(vault.files_path) else 0
    })

def start_api(host='0.0.0.0', port=5000, debug=False):
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    start_api(debug=True) 