from flask import Flask, request, send_file, jsonify
import os
import convertapi
from werkzeug.utils import secure_filename

# Setup agar Flask tahu lokasi folder 'public' ada di luar folder 'api'
# Kita gunakan path absolut agar Vercel tidak bingung
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
public_dir = os.path.join(base_dir, 'public')

app = Flask(__name__, static_folder=public_dir, static_url_path='/public')

# API Key Setup
convertapi.api_secret = os.environ.get('CONVERT_API_SECRET', '')
app.config['UPLOAD_FOLDER'] = '/tmp'

# --- BAGIAN PENTING: ROUTE HALAMAN DEPAN ---
# Ini yang akan memperbaiki error "Not Found"
@app.route('/')
def home():
    try:
        # Mengambil file index.html dari folder root
        index_path = os.path.join(base_dir, 'index.html')
        return send_file(index_path)
    except Exception as e:
        return f"Error loading index.html: {str(e)}", 500

# --- ROUTE API CONVERT ---
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
            
            # Proses ConvertAPI
            result = convertapi.convert('docx', { 'File': pdf_path }, from_format='pdf')
            saved_files = result.save_files(app.config['UPLOAD_FOLDER'])
            docx_path = saved_files[0]
            
            # Pastikan nama file output bersih
            download_name = filename.rsplit('.', 1)[0] + '.docx'
            
            return send_file(docx_path, as_attachment=True, download_name=download_name)

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Bersihkan file sampah
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

@app.route('/api/hello')
def hello():
    return "API KullDConvert Berjalan!"
