from flask import Flask, request, send_file, jsonify
import os
import convertapi
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Ganti '' dengan API Key ConvertAPI Anda jika testing lokal
convertapi.api_secret = os.environ.get('CONVERT_API_SECRET', '')

app.config['UPLOAD_FOLDER'] = '/tmp'

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
            
            return send_file(docx_path, as_attachment=True, download_name=filename.replace('.pdf', '.docx'))

        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

@app.route('/api/hello')
def hello():
    return "API Ready"
