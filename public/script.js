const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('file-info');
const filenameSpan = document.getElementById('filename');
const removeBtn = document.getElementById('remove-btn');
const convertBtn = document.getElementById('convert-btn');
const statusContainer = document.getElementById('status-container');
const statusText = document.getElementById('status-text');

let currentFile = null;

// Handle Drag & Drop Events
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }

dropZone.addEventListener('dragover', () => dropZone.classList.add('dragover'));
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

dropZone.addEventListener('drop', (e) => {
    dropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    handleFiles(files);
});

fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

function handleFiles(files) {
    if (files.length > 0) {
        if (files[0].type === "application/pdf") {
            currentFile = files[0];
            showFileUI(currentFile.name);
        } else {
            alert("Mohon upload file PDF saja.");
        }
    }
}

function showFileUI(name) {
    filenameSpan.innerText = name;
    dropZone.style.display = 'none';
    fileInfo.style.display = 'flex';
    convertBtn.disabled = false;
}

removeBtn.addEventListener('click', () => {
    currentFile = null;
    fileInput.value = '';
    dropZone.style.display = 'block';
    fileInfo.style.display = 'none';
    convertBtn.disabled = true;
    statusContainer.style.display = 'none';
});

// Handle Conversion
convertBtn.addEventListener('click', async () => {
    if (!currentFile) return;

    // UI Updates
    convertBtn.disabled = true;
    convertBtn.innerHTML = 'Memproses...';
    statusContainer.style.display = 'block';
    statusText.innerText = "Mengupload dan Mengonversi...";

    const formData = new FormData();
    formData.append('file', currentFile);

    try {
        const response = await fetch('/api/convert', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            statusText.innerText = "Selesai! Mengunduh...";
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = currentFile.name.replace('.pdf', '.docx');
            document.body.appendChild(a);
            a.click();
            a.remove();
            
            // Reset UI
            setTimeout(() => {
                convertBtn.innerHTML = 'Konversi Lagi <i class="fa-solid fa-arrow-right"></i>';
                convertBtn.disabled = false;
                statusText.innerText = "Berhasil!";
            }, 1000);
        } else {
            throw new Error('Gagal konversi');
        }
    } catch (error) {
        console.error(error);
        statusText.innerText = "Terjadi kesalahan. Coba lagi.";
        statusText.style.color = "#ff4d4d";
        convertBtn.disabled = false;
        convertBtn.innerHTML = 'Coba Lagi';
    }
});
