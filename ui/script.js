// ==================== CONFIGURATION ====================
const API_BASE_URL = 'http://127.0.0.1:8000';

// ==================== STATE MANAGEMENT ====================
let documents = [];
let chatHistory = [];
let totalChunks = 0;

// ==================== DOM ELEMENTS ====================
const elements = {
    uploadArea: document.getElementById('upload-area'),
    fileInput: document.getElementById('file-input'),
    browseBtn: document.getElementById('browse-btn'),
    uploadProgress: document.getElementById('upload-progress'),
    progressFill: document.getElementById('progress-fill'),
    progressText: document.getElementById('progress-text'),

    questionInput: document.getElementById('question-input'),
    askBtn: document.getElementById('ask-btn'),
    chatContainer: document.getElementById('chat-container'),
    emptyState: document.getElementById('empty-state'),
    messages: document.getElementById('messages'),

    documentList: document.getElementById('document-list'),
    historyList: document.getElementById('history-list'),
    clearHistoryBtn: document.getElementById('clear-history-btn'),

    docCount: document.getElementById('doc-count'),
    chunkCount: document.getElementById('chunk-count'),

    toastContainer: document.getElementById('toast-container'),
    loadingOverlay: document.getElementById('loading-overlay')
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    loadDocuments();
    loadHistory();
});

function initializeEventListeners() {
    // Upload events
    elements.uploadArea.addEventListener('click', () => elements.fileInput.click());
    elements.browseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        elements.fileInput.click();
    });
    elements.fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop
    elements.uploadArea.addEventListener('dragover', handleDragOver);
    elements.uploadArea.addEventListener('dragleave', handleDragLeave);
    elements.uploadArea.addEventListener('drop', handleDrop);

    // Question submission
    elements.askBtn.addEventListener('click', handleAskQuestion);
    elements.questionInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleAskQuestion();
    });

    // History
    elements.clearHistoryBtn.addEventListener('click', handleClearHistory);
}

// ==================== UPLOAD FUNCTIONALITY ====================
function handleDragOver(e) {
    e.preventDefault();
    elements.uploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    elements.uploadArea.classList.remove('drag-over');
    const files = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
    if (files.length > 0) {
        uploadFiles(files);
    } else {
        showToast('Please drop PDF files only', 'error');
    }
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
        uploadFiles(files);
    }
}

async function uploadFiles(files) {
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    // Show progress
    elements.uploadProgress.style.display = 'block';
    elements.progressFill.style.width = '0%';
    elements.progressText.textContent = `Uploading ${files.length} file(s)...`;

    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                elements.progressFill.style.width = `${progress}%`;
            }
        }, 200);

        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        clearInterval(progressInterval);
        elements.progressFill.style.width = '100%';

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const data = await response.json();

        // Update state
        totalChunks = data.total_chunks || 0;
        updateStats();

        showToast(data.message || 'Files uploaded successfully!', 'success');

        // Reload documents
        await loadDocuments();

        // Reset file input
        elements.fileInput.value = '';

    } catch (error) {
        console.error('Upload error:', error);
        showToast(error.message || 'Failed to upload files', 'error');
    } finally {
        setTimeout(() => {
            elements.uploadProgress.style.display = 'none';
        }, 1000);
    }
}

// ==================== QUESTION ANSWERING ====================
async function handleAskQuestion() {
    const question = elements.questionInput.value.trim();

    if (!question) {
        showToast('Please enter a question', 'warning');
        return;
    }

    if (documents.length === 0) {
        showToast('Please upload documents first', 'warning');
        return;
    }

    // Clear input
    elements.questionInput.value = '';

    // Hide empty state if visible
    if (elements.emptyState.style.display !== 'none') {
        elements.emptyState.style.display = 'none';
    }

    // Add question to chat
    addMessageToChat(question, 'question');

    // Show loading
    const loadingMsg = addLoadingMessage();

    try {
        const response = await fetch(`${API_BASE_URL}/ask?question=${encodeURIComponent(question)}`, {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to get answer');
        }

        const data = await response.json();

        // Remove loading message
        loadingMsg.remove();

        // Add answer to chat
        addMessageToChat(data.answer, 'answer', data.sources);

        // Reload history
        await loadHistory();

    } catch (error) {
        console.error('Ask error:', error);
        loadingMsg.remove();
        showToast(error.message || 'Failed to get answer', 'error');
    }
}

function addMessageToChat(content, type, sources = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';

    const messageContent = document.createElement('div');
    messageContent.className = `message-${type}`;

    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = type === 'question' ? 'Question' : 'Answer';

    const text = document.createElement('div');
    text.className = 'message-content';
    text.textContent = content;

    messageContent.appendChild(label);
    messageContent.appendChild(text);

    // Add sources if available
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';

        const sourcesTitle = document.createElement('div');
        sourcesTitle.className = 'message-sources-title';
        sourcesTitle.textContent = `📚 Sources (${sources.length})`;
        sourcesDiv.appendChild(sourcesTitle);

        sources.forEach(source => {
            const sourceItem = document.createElement('div');
            sourceItem.className = 'source-item';

            const sourceContent = document.createElement('div');
            sourceContent.textContent = source.content.substring(0, 150) + '...';

            const sourceMeta = document.createElement('div');
            sourceMeta.className = 'source-meta';
            sourceMeta.innerHTML = `
                <span>📄 ${source.metadata.source_file}</span>
                <span>📖 Page ${source.metadata.page}</span>
            `;

            sourceItem.appendChild(sourceContent);
            sourceItem.appendChild(sourceMeta);
            sourcesDiv.appendChild(sourceItem);
        });

        messageContent.appendChild(sourcesDiv);
    }

    messageDiv.appendChild(messageContent);
    elements.messages.appendChild(messageDiv);

    // Scroll to bottom
    elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
}

function addLoadingMessage() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message';
    loadingDiv.innerHTML = `
        <div class="message-answer">
            <div class="message-label">Answer</div>
            <div class="message-content">
                <div class="spinner" style="width: 20px; height: 20px; border-width: 2px;"></div>
                Thinking...
            </div>
        </div>
    `;
    elements.messages.appendChild(loadingDiv);
    elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
    return loadingDiv;
}

// ==================== DOCUMENT MANAGEMENT ====================
async function loadDocuments() {
    try {
        const response = await fetch(`${API_BASE_URL}/documents`);

        if (!response.ok) {
            throw new Error('Failed to load documents');
        }

        const data = await response.json();
        documents = data.documents || [];

        updateStats();
        renderDocumentList();

    } catch (error) {
        console.error('Load documents error:', error);
    }
}

function renderDocumentList() {
    if (documents.length === 0) {
        elements.documentList.innerHTML = '<p class="empty-message">No documents uploaded yet</p>';
        return;
    }

    elements.documentList.innerHTML = '';

    documents.forEach(doc => {
        const docItem = document.createElement('div');
        docItem.className = 'document-item';
        docItem.innerHTML = `
            <span class="document-name" title="${doc.filename}">📄 ${doc.filename}</span>
            <button class="btn-delete" data-id="${doc.id}" title="Delete document">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        `;

        const deleteBtn = docItem.querySelector('.btn-delete');
        deleteBtn.addEventListener('click', () => handleDeleteDocument(doc.id));

        elements.documentList.appendChild(docItem);
    });
}

async function handleDeleteDocument(docId) {
    if (!confirm('Are you sure you want to delete this document?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/documents/${docId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to delete document');
        }

        showToast('Document deleted successfully', 'success');
        await loadDocuments();

    } catch (error) {
        console.error('Delete error:', error);
        showToast(error.message || 'Failed to delete document', 'error');
    }
}

// ==================== HISTORY MANAGEMENT ====================
async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/history`);

        if (!response.ok) {
            throw new Error('Failed to load history');
        }

        const data = await response.json();
        chatHistory = data.history || [];

        renderHistory();

    } catch (error) {
        console.error('Load history error:', error);
    }
}

function renderHistory() {
    if (chatHistory.length === 0) {
        elements.historyList.innerHTML = '<p class="empty-message">No conversation history</p>';
        return;
    }

    elements.historyList.innerHTML = '';

    // Show most recent first
    const recentHistory = [...chatHistory].reverse().slice(0, 10);

    recentHistory.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';

        const timestamp = new Date(item.timestamp).toLocaleString();

        historyItem.innerHTML = `
            <div class="history-question">${item.question}</div>
            <div class="history-answer">${item.answer}</div>
            <div class="history-time">${timestamp}</div>
        `;

        elements.historyList.appendChild(historyItem);
    });
}

async function handleClearHistory() {
    if (!confirm('Are you sure you want to clear all chat history?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/clear-history`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Failed to clear history');
        }

        chatHistory = [];
        renderHistory();
        showToast('History cleared successfully', 'success');

    } catch (error) {
        console.error('Clear history error:', error);
        showToast(error.message || 'Failed to clear history', 'error');
    }
}

// ==================== STATS UPDATE ====================
function updateStats() {
    elements.docCount.textContent = documents.length;
    elements.chunkCount.textContent = totalChunks;
}

// ==================== TOAST NOTIFICATIONS ====================
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ==================== UTILITY FUNCTIONS ====================
function showLoading() {
    elements.loadingOverlay.style.display = 'flex';
}

function hideLoading() {
    elements.loadingOverlay.style.display = 'none';
}
