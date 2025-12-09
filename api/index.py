from flask import Flask, request, send_file, jsonify
import os
import convertapi
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Mengambil API Secret dari Environment Variable Vercel
# Jika testing lokal (di laptop), ganti string kosong kedua dengan key Anda
convertapi.api_secret = os.environ.get('CONVERT_API_SECRET', '')

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
            
            # Kirim ke ConvertAPI
            # Parameter 'docx' adalah format tujuan
            result = convertapi.convert('docx', {
                'File': pdf_path
            }, from_format='pdf')
            
            # Simpan hasil download dari API ke folder tmp server
            saved_files = result.save_files(app.config['UPLOAD_FOLDER'])
            
            # Ambil path file hasil (biasanya file pertama di list)
            docx_path = saved_files[0]
            docx_filename = os.path.basename(docx_path)

            return send_file(docx_path, as_attachment=True, download_name=docx_filename)

        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
        finally:
            # Bersihkan file PDF asli untuk hemat ruang
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

# Route untuk cek status
@app.route('/api/hello')
def hello():
    return "API KullDConvert Siap!"
