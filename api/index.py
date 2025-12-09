from flask import Flask, request, send_file, jsonify
import os
import convertapi
import traceback
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- SETUP PATH ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.config['UPLOAD_FOLDER'] = '/tmp'

# --- SETUP API KEY (DENGAN LOGGING) ---
api_secret = os.environ.get('CONVERT_API_SECRET')
if api_secret:
    print(f"DEBUG: API Key ditemukan (berakhir dengan ...{api_secret[-4:]})")
    convertapi.api_secret = api_secret
else:
    print("CRITICAL ERROR: API Key TIDAK DITEMUKAN di Environment Variables!")

# --- ROUTE UTAMA ---
@app.route('/')
def home():
    try:
        return send_file(os.path.join(PROJECT_ROOT, 'index.html'))
    except Exception as e:
        return f"<h1>System Error:</h1><p>{str(e)}</p>", 500

# --- ROUTE CONVERT (YANG SERING ERROR) ---
@app.route('/api/convert', methods=['POST'])
def convert_file():
    print("DEBUG: Memulai request konversi...") # Log awal
    
    if 'file' not in request.files:
        print("ERROR: Tidak ada file yang diupload")
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    pdf_path = None # Inisialisasi variabel

    if file:
        try:
            # 1. Simpan File Sementara
            filename = secure_filename(file.filename)
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(pdf_path)
            print(f"DEBUG: File berhasil disimpan di {pdf_path}")

            # 2. Cek API Key sebelum lanjut
            if not convertapi.api_secret:
                raise ValueError("API Key ConvertAPI belum dipasang di Vercel!")

            # 3. Proses Konversi (Bagian Rawan Error)
            print("DEBUG: Mengirim ke ConvertAPI...")
            
            # Kita set timeout 60 detik agar library tidak panic duluan
            result = convertapi.convert('docx', { 
                'File': pdf_path 
            }, from_format='pdf', timeout=60)
            
            print("DEBUG: Konversi sukses, mengunduh hasil...")
            
            # 4. Simpan Hasil
            saved_files = result.save_files(app.config['UPLOAD_FOLDER'])
            docx_path = saved_files[0]
            
            print(f"DEBUG: Hasil disimpan di {docx_path}")
            
            download_name = filename.rsplit('.', 1)[0] + '.docx'
            return send_file(docx_path, as_attachment=True, download_name=download_name)

        except convertapi.api.exception.ApiError as e:
            # Error spesifik dari ConvertAPI (misal: kuota habis / auth gagal)
            error_msg = f"ConvertAPI Error: {str(e)}"
            print(f"ERROR LOG: {error_msg}")
            return jsonify({'error': error_msg}), 500

        except Exception as e:
            # Error Python umum (Print Traceback Lengkap ke Logs Vercel)
            print("--- FULL ERROR TRACEBACK ---")
            traceback.print_exc()
            print("----------------------------")
            return jsonify({'error': f"Server Crash: {str(e)}"}), 500
            
        finally:
            # Bersihkan sampah
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except:
                    pass
