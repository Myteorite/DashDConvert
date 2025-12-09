from flask import Flask, request, send_file, jsonify
import os
import convertapi
import traceback
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- CONFIG ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.config['UPLOAD_FOLDER'] = '/tmp'

# --- 1. ROUTE HALAMAN DEPAN ---
@app.route('/')
def home():
    try:
        return send_file(os.path.join(PROJECT_ROOT, 'index.html'))
    except Exception as e:
        return f"Error loading HTML: {str(e)}", 500

# --- 2. ROUTE KONVERSI ---
@app.route('/api/convert', methods=['POST'])
def convert_file():
    # Cek apakah API Key sudah terpasang di Vercel
    api_secret = os.environ.get('CONVERT_API_SECRET')
    
    if not api_secret:
        print("CRITICAL: API Key Hilang!")
        # Ini akan mengirim pesan error JELAS ke layar HP/Laptop Anda
        return jsonify({'error': 'Sistem Error: API Key belum dipasang di Vercel Settings.'}), 500
    
    convertapi.api_secret = api_secret

    if 'file' not in request.files:
        return jsonify({'error': 'Tidak ada file yang diupload'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nama file kosong'}), 400

    pdf_path = None

    try:
        # Simpan file sementara
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_path)

        # Proses Konversi
        print(f"DEBUG: Memulai konversi untuk {filename}...")
        
        # Timeout diset 20 detik agar tidak hang selamanya
        result = convertapi.convert('docx', { 'File': pdf_path }, from_format='pdf', timeout=20)
        
        saved_files = result.save_files(app.config['UPLOAD_FOLDER'])
        docx_path = saved_files[0]
        
        print("DEBUG: Konversi Berhasil!")
        
        download_name = filename.rsplit('.', 1)[0] + '.docx'
        return send_file(docx_path, as_attachment=True, download_name=download_name)

    except convertapi.api.exception.ApiError as e:
        # Error dari pihak ConvertAPI (misal: kuota habis)
        print(f"API Error: {str(e)}")
        return jsonify({'error': f"Gagal Konversi: {str(e)}"}), 500

    except Exception as e:
        # Error coding lainnya
        print("--- ERROR TRACEBACK ---")
        traceback.print_exc()
        return jsonify({'error': f"Server Error: {str(e)}"}), 500
        
    finally:
        # Bersihkan file
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except:
                pass
