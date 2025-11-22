let currentTab = 'text';
let extractedText = '';
let generatedCards = [];

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupFileUpload();
    setupGenerateButton();
    loadDecks();
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
    
    const genType = document.querySelector('input[name="genType"]:checked').value;
    const numCards = parseInt(document.getElementById('numCards').value) || 10;
    
    showLoading(true);
    document.getElementById('summaryResult').classList.add('hidden');
    document.getElementById('cardsPreview').classList.add('hidden');
    
    try {
        const response = await fetch('/api/process-text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                action: genType,
                num_cards: numCards,
                num_questions: numCards
            })
        });
        
        const data = await response.json();
        
        if (genType === 'summary') {
            document.getElementById('summaryContent').textContent = data.summary;
            document.getElementById('summaryResult').classList.remove('hidden');
        } else if (genType === 'flashcards') {
            generatedCards = data.flashcards;
            displayCardsPreview(generatedCards);
        } else if (genType === 'multiple_choice') {
            generatedCards = data.questions;
            displayCardsPreview(generatedCards);
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
    
    container.innerHTML = cards.map((card, index) => `
        <div class="card-preview">
            <strong>#${index + 1}</strong><br>
            <strong>Q:</strong> ${escapeHtml(card.question)}<br>
            <strong>A:</strong> ${escapeHtml(card.answer)}
            ${card.choices ? `<br><strong>Choices:</strong> ${card.choices.map(escapeHtml).join(', ')}` : ''}
        </div>
    `).join('');
    
    document.getElementById('cardsPreview').classList.remove('hidden');
    document.getElementById('saveCardsBtn').onclick = saveCards;
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
        
        const deckData = await deckResponse.json();
        const deckId = deckData.id;
        
        for (const card of generatedCards) {
            await fetch(`/api/decks/${deckId}/cards`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: card.question,
                    answer: card.answer,
                    choices: card.choices || null
                })
            });
        }
        
        showToast(`Deck "${deckName}" created with ${generatedCards.length} cards!`, 'success');
        
        document.getElementById('textInput').value = '';
        document.getElementById('deckName').value = '';
        document.getElementById('cardsPreview').classList.add('hidden');
        extractedText = '';
        generatedCards = [];
        
        loadDecks();
    } catch (error) {
        showToast('Error saving cards: ' + error.message, 'error');
    }
}

async function loadDecks() {
    try {
        const response = await fetch('/api/decks');
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
