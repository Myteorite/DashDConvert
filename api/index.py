from flask import Flask, request, send_file, jsonify
import os
import convertapi
from werkzeug.utils import secure_filename

app = Flask(__name__)

# KUNCI UTAMA: Mengambil path folder root project
# Ini memastikan Python bisa menemukan index.html di mana pun dia berada
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# API Key
convertapi.api_secret = os.environ.get('CONVERT_API_SECRET', '')
app.config['UPLOAD_FOLDER'] = '/tmp'

# --- 1. ROUTE UTAMA ---
@app.route('/')
def home():
    try:
        # Langsung ambil index.html dari root
        return send_file(os.path.join(PROJECT_ROOT, 'index.html'))
    except Exception as e:
        return f"<h1>Error System:</h1><p>{str(e)}</p>", 500

# --- 2. ROUTE CONVERT (Tetap Sama) ---
@app.route('/api/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files: return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'No selected file'}), 400

    if file:
        try:
            filename = secure_filename(file.filename)
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(pdf_path)
            
            result = convertapi.convert('docx', { 'File': pdf_path }, from_format='pdf')
            saved_files = result.save_files(app.config['UPLOAD_FOLDER'])
            docx_path = saved_files[0]
            
            download_name = filename.rsplit('.', 1)[0] + '.docx'
            return send_file(docx_path, as_attachment=True, download_name=download_name)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if os.path.exists(pdf_path): os.remove(pdf_path)
