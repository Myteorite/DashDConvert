const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('file-info');
const filenameSpan = document.getElementById('filename');
const removeBtn = document.getElementById('remove-btn');
const convertBtn = document.getElementById('convert-btn');
const statusContainer = document.getElementById('status-container');
const statusText = document.getElementById('status-text');

let currentFile = null;

// Handle Drag & Drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});
function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }

dropZone.addEventListener('dragover', () => dropZone.classList.add('dragover'));
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    dropZone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

function handleFiles(files) {
    if (files.length > 0 && files[0].type === "application/pdf") {
        currentFile = files[0];
        filenameSpan.innerText = currentFile.name;
        dropZone.style.display = 'none';
        fileInfo.style.display = 'flex';
        convertBtn.disabled = false;
    } else {
        alert("Hanya file PDF yang diperbolehkan.");
    }
}

removeBtn.addEventListener('click', () => {
    currentFile = null;
    fileInput.value = '';
    dropZone.style.display = 'block';
    fileInfo.style.display = 'none';
    convertBtn.disabled = true;
    statusContainer.style.display = 'none';
});

convertBtn.addEventListener('click', async () => {
    if (!currentFile) return;

    convertBtn.disabled = true;
    convertBtn.innerHTML = 'Sedang Memproses...';
    statusContainer.style.display = 'block';
    statusText.innerText = "Mengupload dan Mengonversi...";
    statusText.style.color = "#f8fafc";

    const formData = new FormData();
    formData.append('file', currentFile);

    try {
        const response = await fetch('/api/convert', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            statusText.innerText = "Berhasil! Mengunduh...";
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = currentFile.name.replace('.pdf', '.docx');
            document.body.appendChild(a);
            a.click();
            a.remove();

            convertBtn.innerHTML = 'Selesai!';
            setTimeout(() => {
                convertBtn.innerHTML = 'Konversi Lagi <i class="fa-solid fa-arrow-right"></i>';
                convertBtn.disabled = false;
            }, 2000);
        } else {
            const data = await response.json();
            throw new Error(data.error || 'Gagal konversi');
        }
    } catch (error) {
        console.error(error);
        statusText.innerText = "Error: " + error.message;
        statusText.style.color = "#ff4d4d";
        convertBtn.innerHTML = 'Coba Lagi';
        convertBtn.disabled = false;
    }
});
