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
        # 1. Cek Library & API Key
        try:
            import convertapi
        except ImportError:
            return jsonify({'error': 'Library convertapi hilang! Cek requirements.txt'}), 500

        api_secret = os.environ.get('CONVERT_API_SECRET')
        if not api_secret:
            return jsonify({'error': 'API Key belum dipasang di Vercel!'}), 500
        
        convertapi.api_secret = api_secret

        # 2. Cek File
        if 'file' not in request.files:
            return jsonify({'error': 'File tidak terbaca oleh server'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nama file kosong'}), 400

        # 3. Ambil Format Target dari Frontend (misal: 'pdf', 'docx', 'pptx')
        target_format = request.form.get('target_format')
        if not target_format:
            return jsonify({'error': 'Format tujuan tidak dipilih'}), 400

        # 4. Simpan File Sementara
        filename = secure_filename(file.filename)
        source_ext = filename.rsplit('.', 1)[1].lower() # ambil ekstensi asli (misal: pdf)
        
        # Validasi sederhana
        if source_ext == target_format:
             return jsonify({'error': 'Format asal dan tujuan sama!'}), 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # 5. Proses Konversi Dinamis
        print(f"DEBUG: Mengubah {source_ext} ke {target_format}...")
        
        result = convertapi.convert(
            target_format, 
            { 'File': file_path }, 
            from_format=source_ext, 
            timeout=30
        )
        
        saved_files = result.save_files(app.config['UPLOAD_FOLDER'])
        output_path = saved_files[0]
        
        # 6. Kirim Balik
        download_name = filename.rsplit('.', 1)[0] + '.' + target_format
        return send_file(output_path, as_attachment=True, download_name=download_name)

    except Exception as e:
        error_msg = str(e)
        print("ERROR:", error_msg)
        traceback.print_exc()
        
        if "Authentication failed" in error_msg:
            return jsonify({'error': 'API Key Salah/Expired.'}), 500
        if "Seconds" in error_msg:
            return jsonify({'error': 'Timeout! File terlalu besar untuk server gratis.'}), 500
            
        return jsonify({'error': f"Sistem Error: {error_msg}"}), 500
