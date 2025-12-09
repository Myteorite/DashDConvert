from flask import Flask, request, send_file, jsonify
import os
import traceback
from werkzeug.utils import secure_filename

app = Flask(__name__)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.config['UPLOAD_FOLDER'] = '/tmp'

@app.route('/')
def home():
    try:
        return send_file(os.path.join(PROJECT_ROOT, 'index.html'))
    except Exception as e:
        return f"Error loading HTML: {str(e)}", 500

@app.route('/api/convert', methods=['POST'])
def convert_file():
    try:
        # 1. Cek Import Library (Agar tidak crash kalau lupa requirements.txt)
        try:
            import convertapi
        except ImportError:
            return jsonify({'error': 'CRITICAL: Library convertapi belum diinstall! Cek requirements.txt'}), 500

        # 2. Cek API Key
        api_secret = os.environ.get('CONVERT_API_SECRET')
        if not api_secret:
            return jsonify({'error': 'CRITICAL: API Key (CONVERT_API_SECRET) belum dipasang di Vercel Settings!'}), 500
        
        convertapi.api_secret = api_secret

        # 3. Cek File Upload
        if 'file' not in request.files:
            return jsonify({'error': 'File tidak terdeteksi'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nama file kosong'}), 400

        # 4. Proses Simpan & Convert
        filename = secure_filename(file.filename)
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(pdf_path)

        # Gunakan timeout agar tidak hang
        result = convertapi.convert('docx', { 'File': pdf_path }, from_format='pdf', timeout=20)
        
        saved_files = result.save_files(app.config['UPLOAD_FOLDER'])
        docx_path = saved_files[0]
        
        # Kirim File
        download_name = filename.rsplit('.', 1)[0] + '.docx'
        return send_file(docx_path, as_attachment=True, download_name=download_name)

    except Exception as e:
        # Tangkap SEMUA error dan kirim sebagai pesan teks
        error_msg = str(e)
        print("ERROR:", error_msg)
        traceback.print_exc()
        # Perbaiki pesan jika error dari ConvertAPI
        if "Authentication failed" in error_msg:
            return jsonify({'error': 'API Key Salah! Cek token di Vercel Settings.'}), 500
        if "Seconds" in error_msg:
            return jsonify({'error': 'Waktu Habis! File mungkin terlalu besar.'}), 500
            
        return jsonify({'error': f"Sistem Error: {error_msg}"}), 500
