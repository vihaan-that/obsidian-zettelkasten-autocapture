// options.js
document.addEventListener('DOMContentLoaded', async () => {
  // Load saved settings
  const settings = await chrome.storage.sync.get(['downloadFolder', 'contributor']);
  if (settings.downloadFolder) {
    document.getElementById('downloadFolder').value = settings.downloadFolder;
  }
  if (settings.contributor) {
    document.getElementById('contributor').value = settings.contributor;
  }

  document.getElementById('saveButton').addEventListener('click', async () => {
    const downloadFolder = document.getElementById('downloadFolder').value.trim();
    const contributor = document.getElementById('contributor').value.trim();
    const statusEl = document.getElementById('status');

    if (!downloadFolder) {
      statusEl.className = 'status error';
      statusEl.textContent = 'Error: Download folder is required';
      return;
    }

    await chrome.storage.sync.set({ downloadFolder, contributor });
    statusEl.className = 'status success';
    statusEl.textContent = 'Settings saved!';
  });
});
