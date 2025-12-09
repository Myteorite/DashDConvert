from flask import Flask, request, send_file, jsonify
import os
import traceback
import zipfile
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
        # 1. SETUP LIBRARY
        try:
            import convertapi
        except ImportError:
            return jsonify({'error': 'Library convertapi hilang!'}), 500

        api_secret = os.environ.get('CONVERT_API_SECRET')
        if not api_secret:
            return jsonify({'error': 'API Key belum dipasang di Vercel!'}), 500
        
        convertapi.api_secret = api_secret

        # 2. VALIDASI INPUT
        if 'file' not in request.files:
            return jsonify({'error': 'File tidak terbaca'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nama file kosong'}), 400

        target_format = request.form.get('target_format')
        if not target_format:
            return jsonify({'error': 'Format tujuan belum dipilih'}), 400

        # 3. SIMPAN FILE SEMENTARA
        filename = secure_filename(file.filename)
        source_ext = filename.rsplit('.', 1)[1].lower()
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # 4. PROSES KONVERSI
        print(f"DEBUG: Convert {source_ext} to {target_format}...")

        # -- FIX PDF KE PPTX --
        # PDF ke PPTX butuh waktu lama, kita set timeout lebih panjang
        # convertapi parameter untuk pdf ke pptx adalah 'pptx'
        try:
            result = convertapi.convert(
                target_format, 
                { 'File': file_path }, 
                from_format=source_ext, 
                timeout=60 # Naikkan timeout
            )
        except convertapi.api.exception.ApiError as e:
            return jsonify({'error': f"ConvertAPI Error: {str(e)}"}), 500

        # 5. HANDLING HASIL (ZIP LOGIC)
        saved_files = result.save_files(app.config['UPLOAD_FOLDER'])
        
        # JIKA HASILNYA BANYAK (PPT -> IMAGE) ATAU USER MINTA ZIP
        if len(saved_files) > 1 or target_format in ['jpg', 'png', 'jpeg']:
            
            zip_filename = filename.rsplit('.', 1)[0] + '-converted.zip'
            zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)

            print(f"DEBUG: Membuat ZIP {zip_filename} dari {len(saved_files)} files...")

            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for f in saved_files:
                    # Masukkan file ke dalam zip
                    zipf.write(f, os.path.basename(f))
            
            return send_file(zip_path, as_attachment=True, download_name=zip_filename)
        
        else:
            # JIKA HASIL CUMA 1 FILE (PDF -> WORD, DLL)
            output_path = saved_files[0]
            download_name = filename.rsplit('.', 1)[0] + '.' + target_format
            return send_file(output_path, as_attachment=True, download_name=download_name)

    except Exception as e:
        error_msg = str(e)
        print("CRITICAL ERROR:", error_msg)
        traceback.print_exc()
        
        if "Seconds" in error_msg:
            return jsonify({'error': 'Waktu Habis! Dokumen terlalu besar/kompleks untuk server gratis.'}), 500
            
        return jsonify({'error': f"Sistem Error: {error_msg}"}), 500
