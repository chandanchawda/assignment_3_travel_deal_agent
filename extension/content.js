// Content script — extracts visible text from the current page
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "extractPageContent") {
    const text = document.body.innerText.substring(0, 5000);
    const title = document.title;
    const url = window.location.href;
    sendResponse({ text, title, url });
  }
  return true;
});
