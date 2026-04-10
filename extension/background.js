// background.js
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'saveClip') {
    handleSaveClip(request)
      .then(() => sendResponse({ success: true }))
      .catch(error => sendResponse({ error: error.message }));
    return true; // indicate async response
  }
});

async function handleSaveClip(request) {
  // Get settings
  const settings = await chrome.storage.sync.get(['downloadFolder', 'contributor']);
  const downloadFolder = settings.downloadFolder;
  const contributor = settings.contributor || 'unknown';

  if (!downloadFolder) {
    throw new Error('Download folder not configured. Open extension options.');
  }

  const {
    selectedText,
    pageUrl,
    pageTitle,
    screenshotData,
    userNotes,
    userTags
  } = request;

  // Generate markdown content
  const timestamp = new Date().toISOString().split('T')[0];
  const summary = selectedText ? selectedText.substring(0, 120) : pageTitle.substring(0, 120);

  let tagsArray = ['web-clip'];
  if (userTags) {
    tagsArray.push(...userTags.split(',').map(t => t.trim()).filter(Boolean));
  }

  // Build frontmatter
  const frontmatter = `---
type: web-clip
date: ${timestamp}
contributor: "${contributor}"
url: "${pageUrl}"
summary: "${summary.replace(/"/g, '\\"')}"
tags:
${tagsArray.map(t => `  - "${t}"`).join('\n')}
---`;

  // Build content
  let content = frontmatter + '\n\n';
  content += `# ${pageTitle}\n\n`;
  content += `**Source:** [${pageUrl}](${pageUrl})\n\n`;

  if (selectedText) {
    content += `## Selected Text\n\n> ${selectedText.split('\n').join('\n> ')}\n\n`;
  }

  if (userNotes) {
    content += `## Notes\n\n${userNotes}\n\n`;
  }

  // Handle screenshot
  let screenshotFilename = '';
  if (screenshotData) {
    screenshotFilename = `web-clip-${timestamp}-${Date.now()}.png`;
    // Save screenshot via download API
    await downloadFile(screenshotData, downloadFolder + '/' + screenshotFilename);
    content += `## Screenshot\n\n![Screenshot](${screenshotFilename})\n`;
  }

  // Generate filename
  const filename = `web-clip-${timestamp}-${sanitizeFilename(pageTitle.substring(0, 30))}.md`;
  const fullPath = downloadFolder + '/' + filename;

  // Save markdown file
  await downloadFile(content, fullPath);
}

function downloadFile(content, path) {
  return new Promise((resolve, reject) => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const filename = path.split('/').pop();

    chrome.downloads.download({
      url: url,
      filename: filename,
      saveAs: false
    }, (downloadId) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve();
      }
      URL.revokeObjectURL(url);
    });
  });
}

function sanitizeFilename(str) {
  return str.replace(/[^a-z0-9]+/gi, '-').toLowerCase();
}
