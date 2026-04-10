// popup.js
document.addEventListener('DOMContentLoaded', async () => {
  // Get current tab info
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  document.getElementById('pageUrl').value = tab.url;
  document.getElementById('pageTitle').value = tab.title;

  // Get selected text from content script
  chrome.tabs.sendMessage(tab.id, { action: 'getSelectedText' }, (response) => {
    if (response && response.selectedText) {
      const preview = response.selectedText.substring(0, 200);
      document.getElementById('selectedTextPreview').textContent = preview + (preview.length < response.selectedText.length ? '...' : '');
      document.getElementById('selectedTextPreview').dataset.fullText = response.selectedText;
    }
  });

  // Save button handler
  document.getElementById('saveButton').addEventListener('click', async () => {
    const button = document.getElementById('saveButton');
    const statusEl = document.getElementById('status');

    button.disabled = true;
    button.textContent = 'Saving...';
    statusEl.className = 'status';
    statusEl.textContent = '';

    try {
      const selectedText = document.getElementById('selectedTextPreview').dataset.fullText || '';
      const pageUrl = document.getElementById('pageUrl').value;
      const pageTitle = document.getElementById('pageTitle').value;
      const includeScreenshot = document.getElementById('includeScreenshot').checked;
      const userNotes = document.getElementById('userNotes').value;
      const userTags = document.getElementById('userTags').value;

      // Request screenshot if needed
      let screenshotData = null;
      if (includeScreenshot) {
        screenshotData = await chrome.tabs.captureVisibleTab(tab.windowId, { format: 'png' });
      }

      // Send to background to save file
      await chrome.runtime.sendMessage({
        action: 'saveClip',
        selectedText,
        pageUrl,
        pageTitle,
        screenshotData,
        userNotes,
        userTags
      });

      statusEl.className = 'status success';
      statusEl.textContent = '✓ Saved to Research Log';

      setTimeout(() => window.close(), 1500);
    } catch (error) {
      statusEl.className = 'status error';
      statusEl.textContent = '✗ Error: ' + error.message;
      button.disabled = false;
      button.textContent = 'Save to Research Log';
    }
  });
});
