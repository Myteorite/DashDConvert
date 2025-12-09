// DOM ELEMENTS
const inputFormat = document.getElementById('inputFormat');
const outputFormat = document.getElementById('outputFormat');
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('drop-zone');
const filePreview = document.getElementById('file-preview');
const filenameSpan = document.getElementById('filename');
const convertBtn = document.getElementById('convertBtn');
const instructionText = document.getElementById('instruction-text');
const errorMsg = document.getElementById('errorMsg');
const btnText = document.getElementById('btnText');
const loader = document.getElementById('loader');
const historyList = document.getElementById('historyList');

let currentFile = null;

// --- LOGIC RIWAYAT ---

function loadHistory() {
    const history = JSON.parse(localStorage.getItem('convertHistory')) || [];
    historyList.innerHTML = '';

    if (history.length === 0) {
        historyList.innerHTML = '<li class="history-item" style="justify-content:center; color: #64748b;">Belum ada riwayat.</li>';
        return;
    }

    // Tampilkan riwayat (Terbaru di atas)
    history.slice().reverse().forEach(item => {
        const li = document.createElement('li');
        li.className = 'history-item';
        
        // Logika Link: Jika URL ada (dari sesi ini), pakai itu. Jika tidak, matikan tombol.
        // Catatan: Blob URL akan mati saat refresh, jadi kita cek validitas sederhana
        let downloadLink = item.fileUrl ? item.fileUrl : '#';
        let disabledClass = item.fileUrl ? '' : 'style="opacity:0.5; cursor:not-allowed; border-color: gray; color: gray;" title="Link Kadaluarsa (Refresh)"';
        let clickAction = item.fileUrl ? '' : 'onclick="alert(\'Link kadaluarsa setelah halaman direfresh.\'); return false;"';

        li.innerHTML = `
            <div class="history-info">
                <div class="history-date">${item.date}</div>
                <span class="history-name" title="${item.fileName}">${item.fileName}</span>
                <span class="history-badge">${item.type}</span>
            </div>
            <a href="${downloadLink}" download="${item.downloadName}" class="btn-download-mini" ${disabledClass} ${clickAction}>
                <i class="fa-solid fa-download"></i>
            </a>
        `;
        historyList.appendChild(li);
    });
}

// UPDATE: Menambahkan parameter fileUrl dan downloadName
function saveHistory(fileName, downloadName, type, fileUrl) {
    const history = JSON.parse(localStorage.getItem('convertHistory')) || [];
    const now = new Date();
    const dateStr = now.toLocaleDateString('id-ID') + ' ' + now.toLocaleTimeString('id-ID', {hour: '2-digit', minute:'2-digit'});
    
    const newItem = {
        fileName: fileName,
        downloadName: downloadName,
        type: type,
        date: dateStr,
        fileUrl: fileUrl // Menyimpan Blob URL
    };

    // Simpan maks 10 riwayat
    history.push(newItem);
    if (history.length > 10) history.shift();

    localStorage.setItem('convertHistory', JSON.stringify(history));
    loadHistory();
}

window.clearHistory = function() {
    if(confirm('Hapus semua riwayat?')) {
        localStorage.removeItem('convertHistory');
        loadHistory();
    }
}

// --- LOGIC KONVERSI & UI ---

function updateOptions() {
    const val = inputFormat.value;
    outputFormat.innerHTML = ''; 

    if (val === 'pdf') {
        addOption('docx', 'Word (.docx)');
        addOption('pptx', 'PowerPoint (.pptx)');
        addOption('jpg', 'Gambar (.jpg) -> ZIP');
    } else if (val === 'docx') {
        addOption('pdf', 'PDF (.pdf)');
        addOption('jpg', 'Gambar (.jpg) -> ZIP');
    } else if (val === 'pptx') {
        addOption('pdf', 'PDF (.pdf)');
        addOption('jpg', 'Gambar (.jpg) -> ZIP');
    } else if (val === 'jpg') {
        addOption('pdf', 'PDF (.pdf)');
        addOption('docx', 'Word (.docx)');
    }
    updateInstruction();
}

function addOption(value, text) {
    const opt = document.createElement('option');
    opt.value = value;
    opt.innerText = text;
    outputFormat.appendChild(opt);
}

function updateInstruction() {
    instructionText.innerText = `Upload .${inputFormat.value} untuk diubah ke .${outputFormat.value}`;
    fileInput.accept = `.${inputFormat.value}`;
    fileInput.value = ''; 
    resetFile();
}

window.resetFile = function() {
    currentFile = null;
    dropZone.style.display = 'block';
    filePreview.style.display = 'none';
    convertBtn.disabled = true;
    errorMsg.style.display = 'none';
}

inputFormat.addEventListener('change', updateOptions);
outputFormat.addEventListener('change', updateInstruction);

fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
    dropZone.addEventListener(evt, (e) => { e.preventDefault(); e.stopPropagation(); });
});
dropZone.addEventListener('dragover', () => dropZone.classList.add('dragover'));
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    dropZone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

function handleFiles(files) {
    if(files.length > 0) {
        const file = files[0];
        const ext = file.name.split('.').pop().toLowerCase();
        if(ext !== inputFormat.value) {
            showError(`Format salah! Harap upload file .${inputFormat.value}`);
            return;
        }
        currentFile = file;
        filenameSpan.innerText = file.name;
        dropZone.style.display = 'none';
        filePreview.style.display = 'flex';
        convertBtn.disabled = false;
        errorMsg.style.display = 'none';
    }
}

function showError(msg) {
    errorMsg.innerText = msg;
    errorMsg.style.display = 'block';
}

convertBtn.addEventListener('click', async () => {
    if(!currentFile) return;

    convertBtn.disabled = true;
    btnText.style.display = 'none';
    loader.style.display = 'block';
    errorMsg.style.display = 'none';

    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('target_format', outputFormat.value);

    try {
        const response = await fetch('/api/convert', { method: 'POST', body: formData });

        if(response.ok) {
            const blob = await response.blob();
            // Membuat URL permanen sementara (selama tab tidak ditutup/refresh)
            const url = window.URL.createObjectURL(blob);
            
            // Tentukan ekstensi download
            let downloadExt = outputFormat.value;
            if (outputFormat.value === 'jpg' || outputFormat.value === 'png') {
                downloadExt = 'zip';
            }
            
            const finalFileName = currentFile.name.replace(/\.[^/.]+$/, "") + '.' + downloadExt;

            // Trigger Download Otomatis
            const a = document.createElement('a');
            a.href = url;
            a.download = finalFileName;
            document.body.appendChild(a);
            a.click();
            a.remove();
            
            // --- SIMPAN KE RIWAYAT DENGAN URL ---
            saveHistory(
                currentFile.name, 
                finalFileName,
                `${inputFormat.value.toUpperCase()} ➝ ${outputFormat.value.toUpperCase()}`,
                url 
            );

            btnText.innerText = "Selesai! Download dimulai.";
            btnText.style.display = 'block';
            loader.style.display = 'none';
            setTimeout(() => {
                btnText.innerText = "Konversi Lagi";
                convertBtn.disabled = false;
                resetFile();
            }, 3000);
        } else {
            const errData = await response.json();
            throw new Error(errData.error || "Gagal menghubungi server");
        }
    } catch (error) {
        console.error(error);
        btnText.style.display = 'block';
        loader.style.display = 'none';
        convertBtn.disabled = false;
        showError(error.message);
    }
});

// Bersihkan history lama saat reload karena URL Blob akan mati
// Opsional: aktifkan baris di bawah jika ingin history hilang saat refresh agar user tidak bingung
// localStorage.removeItem('convertHistory'); 

// INIT
updateOptions();
loadHistory();
