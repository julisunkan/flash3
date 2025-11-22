let currentTab = 'text';
let extractedText = '';
let generatedCards = [];

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupFileUpload();
    setupGenerateButton();
    loadDecks();
});

// Reload decks when page becomes visible (e.g., after navigating back)
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        loadDecks();
    }
});

// Reload decks when window gains focus
window.addEventListener('focus', () => {
    loadDecks();
});

// Reload decks when navigating back using browser history
window.addEventListener('pageshow', (event) => {
    // If page is restored from bfcache, reload decks
    if (event.persisted) {
        loadDecks();
    }
});

function setupTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            tab.classList.add('active');
            const tabId = tab.dataset.tab;
            document.getElementById(`${tabId}-tab`).classList.add('active');
            currentTab = tabId;
        });
    });
}

function setupFileUpload() {
    const pdfInput = document.getElementById('pdfInput');
    pdfInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        document.getElementById('fileName').textContent = `Selected: ${file.name}`;
        
        const formData = new FormData();
        formData.append('file', file);
        
        showLoading(true);
        
        try {
            const response = await fetch('/api/upload-pdf', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                extractedText = data.text;
                showToast('PDF processed successfully! Text extracted: ' + data.text.length + ' characters', 'success');
            } else {
                showToast(data.error || 'Error processing PDF', 'error');
            }
        } catch (error) {
            showToast('Error uploading PDF: ' + error.message, 'error');
        } finally {
            showLoading(false);
        }
    });
}

function setupGenerateButton() {
    document.getElementById('generateBtn').addEventListener('click', generateContent);
}

async function generateContent() {
    let text = '';
    
    if (currentTab === 'text') {
        text = document.getElementById('textInput').value.trim();
    } else if (currentTab === 'pdf') {
        text = extractedText;
    }
    
    if (!text) {
        showToast('Please provide some text or upload a PDF', 'warning');
        return;
    }
    
    if (text.length < 50) {
        showToast('Text is too short. Please provide at least 50 characters (current: ' + text.length + ')', 'warning');
        return;
    }
    
    const genType = document.querySelector('input[name="genType"]:checked').value;
    const numCards = parseInt(document.getElementById('numCards').value) || 10;
    
    showLoading(true);
    document.getElementById('summaryResult').classList.add('hidden');
    document.getElementById('cardsPreview').classList.add('hidden');
    
    try {
        const apiKey = localStorage.getItem('gemini_api_key');
        
        const response = await fetch('/api/process-text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                action: genType,
                num_cards: numCards,
                num_questions: numCards,
                api_key: apiKey
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showToast(data.error || 'Error generating content', 'error');
            return;
        }
        
        if (genType === 'summary') {
            if (data.summary) {
                // Format summary with paragraphs
                const formattedSummary = data.summary.split('\n\n').map(para => 
                    `<p class="summary-paragraph">${escapeHtml(para)}</p>`
                ).join('');
                document.getElementById('summaryContent').innerHTML = formattedSummary;
                document.getElementById('summaryResult').classList.remove('hidden');
            }
        } else if (genType === 'flashcards') {
            if (data.flashcards && Array.isArray(data.flashcards)) {
                generatedCards = data.flashcards;
                displayCardsPreview(generatedCards);
            }
        } else if (genType === 'multiple_choice') {
            if (data.questions && Array.isArray(data.questions)) {
                generatedCards = data.questions;
                displayCardsPreview(generatedCards);
            }
        }
        
        showToast('Content generated successfully!', 'success');
    } catch (error) {
        showToast('Error generating content: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

function displayCardsPreview(cards) {
    const container = document.getElementById('cardsContainer');
    
    if (!cards || !Array.isArray(cards) || cards.length === 0) {
        container.innerHTML = '<p class="empty-state">No cards generated. Please try again.</p>';
        return;
    }
    
    container.innerHTML = cards.map((card, index) => {
        if (card.choices && Array.isArray(card.choices)) {
            // Multiple Choice Card
            return `
                <div class="card-preview-enhanced multiple-choice-card">
                    <div class="card-number">Question #${index + 1}</div>
                    <div class="card-question">
                        <div class="question-label">Question</div>
                        <div class="question-text">${escapeHtml(card.question || 'No question')}</div>
                    </div>
                    <div class="card-choices">
                        <div class="choices-label">Answer Choices</div>
                        <div class="choices-list">
                            ${card.choices.map((choice, i) => `
                                <div class="choice-item ${choice === card.answer ? 'correct-answer' : ''}">
                                    <span class="choice-letter">${String.fromCharCode(65 + i)}</span>
                                    <span class="choice-text">${escapeHtml(choice)}</span>
                                    ${choice === card.answer ? '<span class="correct-badge">✓ Correct</span>' : ''}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        } else {
            // Q&A Flashcard
            return `
                <div class="card-preview-enhanced flashcard">
                    <div class="card-number">Card #${index + 1}</div>
                    <div class="card-question">
                        <div class="question-label">Question</div>
                        <div class="question-text">${escapeHtml(card.question || 'No question')}</div>
                    </div>
                    <div class="card-answer">
                        <div class="answer-label">Answer</div>
                        <div class="answer-text">${escapeHtml(card.answer || 'No answer')}</div>
                    </div>
                </div>
            `;
        }
    }).join('');
    
    document.getElementById('cardsPreview').classList.remove('hidden');
    document.getElementById('saveCardsBtn').onclick = saveCards;
    document.getElementById('exportPdfBtn').onclick = exportPdf;
}

// Prevent concurrent PDF exports
let isExportingPdf = false;

async function exportPdf() {
    if (generatedCards.length === 0) {
        showToast('No cards to export', 'warning');
        return;
    }
    
    // Prevent concurrent exports
    if (isExportingPdf) {
        showToast('Export already in progress', 'warning');
        return;
    }
    
    const deckName = document.getElementById('deckName').value.trim() || 'Flashcards';
    const exportBtn = document.getElementById('exportPdfBtn');
    
    // Disable button and show loading state
    const originalText = exportBtn.textContent;
    exportBtn.disabled = true;
    exportBtn.textContent = '📄 Exporting...';
    isExportingPdf = true;
    
    try {
        const response = await fetch('/api/export-cards-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cards: generatedCards,
                deck_name: deckName
            })
        });
        
        // Check if response is OK before processing
        if (!response.ok) {
            // Only parse JSON for error responses
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const data = await response.json();
                showToast(data.error || 'Error exporting PDF', 'error');
            } else {
                showToast('Error exporting PDF', 'error');
            }
            return;
        }
        
        // For successful responses, treat as binary blob
        const blob = await response.blob();
        
        // Verify we got a non-empty blob
        if (blob.size === 0) {
            showToast('Received empty PDF from server', 'error');
            return;
        }
        
        // Verify content type from headers (more reliable than blob.type)
        const contentType = response.headers.get('content-type');
        if (contentType && !contentType.includes('application/pdf')) {
            showToast('Invalid PDF format received', 'error');
            return;
        }
        
        // Download the PDF
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${deckName.replace(/\s+/g, '_')}_flashcards.pdf`;
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast('PDF exported successfully!', 'success');
    } catch (error) {
        showToast('Error exporting PDF: ' + error.message, 'error');
    } finally {
        // Re-enable button and restore text
        exportBtn.disabled = false;
        exportBtn.textContent = originalText;
        isExportingPdf = false;
    }
}

async function saveCards() {
    const deckName = document.getElementById('deckName').value.trim();
    
    if (!deckName) {
        showToast('Please enter a deck name', 'warning');
        return;
    }
    
    if (generatedCards.length === 0) {
        showToast('No cards to save', 'warning');
        return;
    }
    
    try {
        const deckResponse = await fetch('/api/decks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: deckName })
        });
        
        if (!deckResponse.ok) {
            throw new Error('Failed to create deck');
        }
        
        const deckData = await deckResponse.json();
        const deckId = deckData.id;
        
        let savedCount = 0;
        for (const card of generatedCards) {
            const cardResponse = await fetch(`/api/decks/${deckId}/cards`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: card.question,
                    answer: card.answer,
                    choices: card.choices || null
                })
            });
            
            if (cardResponse.ok) {
                savedCount++;
            }
        }
        
        showToast(`Deck "${deckName}" created with ${savedCount} cards!`, 'success');
        
        document.getElementById('textInput').value = '';
        document.getElementById('deckName').value = '';
        document.getElementById('cardsPreview').classList.add('hidden');
        extractedText = '';
        generatedCards = [];
        
        await loadDecks();
        
        // Navigate to the newly created deck
        setTimeout(() => {
            location.href = `/deck/${deckId}`;
        }, 1000);
    } catch (error) {
        showToast('Error saving cards: ' + error.message, 'error');
    }
}

async function loadDecks() {
    try {
        // Add cache busting parameter to force fresh data
        const response = await fetch('/api/decks?_t=' + Date.now(), {
            cache: 'no-store'
        });
        const decks = await response.json();
        
        const container = document.getElementById('decksList');
        
        if (decks.length === 0) {
            container.innerHTML = '<p class="empty-state">No decks created yet. Generate some flashcards to get started!</p>';
            return;
        }
        
        container.innerHTML = decks.map(deck => `
            <div class="deck-card" onclick="location.href='/deck/${deck.id}'">
                <h3>${escapeHtml(deck.name)}</h3>
                <p>${escapeHtml(deck.description || 'No description')}</p>
                <div class="deck-meta">
                    <span>📚 ${deck.card_count} cards</span>
                    <span>📅 ${new Date(deck.created_at).toLocaleDateString()}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        showToast('Error loading decks: ' + error.message, 'error');
    }
}

function showLoading(show) {
    const loading = document.getElementById('loading');
    const btn = document.getElementById('generateBtn');
    
    if (show) {
        loading.classList.remove('hidden');
        btn.disabled = true;
    } else {
        loading.classList.add('hidden');
        btn.disabled = false;
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    setTimeout(() => toast.classList.add('hidden'), 3000);
}

function closeBadgeModal() {
    document.getElementById('badgeModal').classList.add('hidden');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
        .then(reg => console.log('Service Worker registered'))
        .catch(err => console.log('Service Worker registration failed:', err));
}
