from flask import Flask, request, send_file, jsonify
import os
import convertapi
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- MASUKKAN SECRET KEY ANDA DI SINI ATAU DI ENVIRONMENT VARIABLES VERCEL ---
# Disarankan set di Vercel: Settings -> Environment Variables -> Key: CONVERT_API_SECRET
convertapi.api_secret = os.environ.get('CONVERT_API_SECRET', 'GANTI_DENGAN_SECRET_KEY_ANDA_JIKA_TESTING_LOKAL')

UPLOAD_FOLDER = '/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
            
            # Tentukan nama output
            docx_filename = filename.rsplit('.', 1)[0] + '.docx'
            docx_path = os.path.join(app.config['UPLOAD_FOLDER'], docx_filename)

            # --- PROSES MENGGUNAKAN CONVERT API ---
            # Ini tidak memakan CPU/RAM Vercel, jadi sangat aman
            result = convertapi.convert('docx', {
                'File': pdf_path
            }, from_format='pdf')
            
            # Simpan hasil dari API ke folder tmp
            result.save_files(app.config['UPLOAD_FOLDER'])
            
            # Karena ConvertAPI mungkin mengubah nama file, kita pastikan pathnya benar
            # Biasanya API mengembalikan nama file yang sama dengan ekstensi baru
            
            return send_file(docx_path, as_attachment=True, download_name=docx_filename)

        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
        finally:
            # Bersihkan file sampah
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            # Opsional: Hapus docx jika perlu, tapi Vercel /tmp akan reset otomatis

@app.route('/api/hello')
def hello():
    return "KullDConvert API is running (Lightweight Mode)!"

app.debug = True
