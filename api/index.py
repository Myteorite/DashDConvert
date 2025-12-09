from flask import Flask, request, send_file, jsonify, send_from_directory
import os
import convertapi
from werkzeug.utils import secure_filename

# Setup Path Folder
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
public_dir = os.path.join(base_dir, 'public')

app = Flask(__name__)

# API Key
convertapi.api_secret = os.environ.get('CONVERT_API_SECRET', '')
app.config['UPLOAD_FOLDER'] = '/tmp'

# --- 1. ROUTE UNTUK HALAMAN UTAMA ---
@app.route('/')
def home():
    try:
        return send_file(os.path.join(base_dir, 'index.html'))
    except Exception as e:
        return f"Error: {str(e)}", 500

# --- 2. ROUTE KHUSUS FILE STATIS (CSS/JS) ---
# Ini adalah "Tukang Pos" yang memperbaiki tampilan web Anda
@app.route('/public/<path:filename>')
def serve_static(filename):
    return send_from_directory(public_dir, filename)

# --- 3. ROUTE API CONVERT ---
@app.route('/api/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

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
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
