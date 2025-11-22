const DECK_ID = parseInt(window.location.pathname.split('/')[2]);
let cards = [];
let currentCardIndex = 0;
let isFlipped = false;

document.addEventListener('DOMContentLoaded', () => {
    loadCards();
    setupKeyboardShortcuts();
});

async function loadCards() {
    try {
        const response = await fetch(`/api/decks/${DECK_ID}/due-cards`);
        cards = await response.json();
        
        if (cards.length === 0) {
            document.getElementById('noCards').classList.remove('hidden');
        } else {
            document.getElementById('flashcard').classList.remove('hidden');
            showCard(0);
        }
        
        updateProgress();
    } catch (error) {
        showMessage('Error loading cards: ' + error.message, 'error');
    }
}

function showCard(index) {
    if (index >= cards.length) {
        document.getElementById('flashcard').classList.add('hidden');
        document.getElementById('noCards').classList.remove('hidden');
        document.getElementById('noCards').innerHTML = `
            <h2>🎉 Study Session Complete!</h2>
            <p>Great work! You've reviewed all due cards.</p>
            <button onclick="location.href='/deck/${DECK_ID}'" class="primary-btn">Back to Deck</button>
        `;
        return;
    }
    
    const card = cards[index];
    currentCardIndex = index;
    isFlipped = false;
    
    document.getElementById('questionText').textContent = card.question;
    document.getElementById('answerText').textContent = card.answer;
    document.getElementById('cardInner').classList.remove('flipped');
    
    updateProgress();
}

function flipCard() {
    isFlipped = !isFlipped;
    const cardInner = document.getElementById('cardInner');
    
    if (isFlipped) {
        cardInner.classList.add('flipped');
    } else {
        cardInner.classList.remove('flipped');
    }
}

async function rateCard(quality) {
    const card = cards[currentCardIndex];
    
    try {
        const response = await fetch(`/api/study/${card.id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quality })
        });
        
        const data = await response.json();
        
        if (data.badges_earned && data.badges_earned.length > 0) {
            showBadgeModal(data.badges_earned);
        }
        
        showCard(currentCardIndex + 1);
    } catch (error) {
        showMessage('Error recording study session: ' + error.message, 'error');
    }
}

function updateProgress() {
    const total = cards.length;
    const current = Math.min(currentCardIndex + 1, total);
    const percentage = total > 0 ? (currentCardIndex / total) * 100 : 0;
    
    document.getElementById('progressFill').style.width = percentage + '%';
    document.getElementById('progressText').textContent = `${currentCardIndex} / ${total}`;
}

function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if (cards.length === 0) return;
        
        if (e.code === 'Space') {
            e.preventDefault();
            flipCard();
        } else if (e.key === '1' && isFlipped) {
            rateCard(0);
        } else if (e.key === '2' && isFlipped) {
            rateCard(3);
        } else if (e.key === '3' && isFlipped) {
            rateCard(4);
        } else if (e.key === '4' && isFlipped) {
            rateCard(5);
        }
    });
}

function speakText(side) {
    if (!('speechSynthesis' in window)) {
        showMessage('Text-to-speech not supported in this browser', 'error');
        return;
    }
    
    const text = side === 'question' 
        ? document.getElementById('questionText').textContent
        : document.getElementById('answerText').textContent;
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;
    
    speechSynthesis.cancel();
    speechSynthesis.speak(utterance);
}

function showBadgeModal(badges) {
    const modal = document.getElementById('badgeModal');
    const info = document.getElementById('badgeInfo');
    
    info.innerHTML = badges.map(badge => `
        <div style="margin: 20px 0; font-size: 1.2rem;">
            <strong>${badge}</strong>
        </div>
    `).join('');
    
    modal.classList.remove('hidden');
}

function closeBadgeModal() {
    document.getElementById('badgeModal').classList.add('hidden');
}

function showMessage(message, type = 'info') {
    const container = document.querySelector('main') || document.body;
    
    // Remove existing messages
    const existingMessages = container.querySelectorAll('.inline-message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `inline-message ${type}`;
    
    const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : type === 'warning' ? '⚠' : 'ℹ';
    messageDiv.innerHTML = `<span style="font-size: 1.2rem;">${icon}</span><span>${message}</span>`;
    
    // Insert at the top of the container
    container.insertBefore(messageDiv, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageDiv.style.opacity = '0';
        messageDiv.style.transform = 'translateY(-10px)';
        setTimeout(() => messageDiv.remove(), 300);
    }, 5000);
}
