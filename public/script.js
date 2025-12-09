const fileInput = document.getElementById('fileInput');
const convertBtn = document.getElementById('convert-btn');
const statusText = document.getElementById('status-text');

let currentFile = null;

// Saat user memilih file
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        currentFile = e.target.files[0];
        if (currentFile.type === "application/pdf") {
            statusText.innerText = "File terpilih: " + currentFile.name;
            convertBtn.disabled = false;
        } else {
            alert("Harap pilih file PDF saja.");
            fileInput.value = ''; // Reset
            convertBtn.disabled = true;
        }
    }
});

// Saat tombol ditekan
convertBtn.addEventListener('click', async () => {
    if (!currentFile) return;

    convertBtn.disabled = true;
    convertBtn.innerText = "Sedang Memproses...";
    statusText.innerText = "Mengupload dan Mengonversi... Mohon tunggu.";

    const formData = new FormData();
    formData.append('file', currentFile);

    try {
        const response = await fetch('/api/convert', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            statusText.innerText = "Sukses! Mengunduh file...";
            
            // Proses download otomatis
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = currentFile.name.replace('.pdf', '.docx');
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            // Reset UI
            statusText.innerText = "Selesai. File telah diunduh.";
            convertBtn.innerText = "Konversi File Lain";
            convertBtn.disabled = false;
            fileInput.value = ''; // Reset input
        } else {
            const errData = await response.json();
            throw new Error(errData.error || 'Gagal konversi');
        }
    } catch (error) {
        console.error(error);
        statusText.innerText = "Error: " + error.message;
        convertBtn.disabled = false;
        convertBtn.innerText = "Coba Lagi";
    }
});
