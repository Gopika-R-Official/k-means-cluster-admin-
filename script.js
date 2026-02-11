// static/script.js
document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('upload-form');
  const csvInput = document.getElementById('csv_file');
  const fileNameSpan = document.getElementById('file-name');

  if (csvInput && fileNameSpan) {
    csvInput.addEventListener('change', () => {
      if (csvInput.files.length > 0) {
        fileNameSpan.textContent = csvInput.files[0].name;
      } else {
        fileNameSpan.textContent = 'No file chosen';
      }
    });
  }

  if (uploadForm) {
    uploadForm.addEventListener('submit', (e) => {
      if (!csvInput || csvInput.files.length === 0) {
        e.preventDefault();
        alert('Please choose a CSV file before uploading.');
      }
    });
  }
});
