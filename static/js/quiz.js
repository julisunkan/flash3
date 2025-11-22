const DECK_ID = parseInt(window.location.pathname.split('/')[2]);
let cards = [];
let currentQuestionIndex = 0;
let score = 0;
let userAnswers = [];

document.addEventListener('DOMContentLoaded', () => {
    loadQuiz();
});

async function loadQuiz() {
    try {
        const response = await fetch(`/api/decks/${DECK_ID}/cards`);
        cards = await response.json();
        
        if (cards.length === 0) {
            document.getElementById('noCards').classList.remove('hidden');
        } else {
            cards = shuffleArray(cards);
            document.getElementById('questionCard').classList.remove('hidden');
            showQuestion(0);
        }
        
        updateProgress();
    } catch (error) {
        showMessage('Error loading quiz: ' + error.message, 'error');
    }
}

function showQuestion(index) {
    if (index >= cards.length) {
        showResults();
        return;
    }
    
    currentQuestionIndex = index;
    const card = cards[index];
    
    document.getElementById('questionNumber').textContent = `Question ${index + 1} of ${cards.length}`;
    document.getElementById('questionText').textContent = card.question;
    document.getElementById('feedback').classList.add('hidden');
    
    const mcqChoices = document.getElementById('mcqChoices');
    const openAnswer = document.getElementById('openAnswer');
    
    if (card.choices) {
        try {
            const choices = JSON.parse(card.choices);
            
            // Validate that choices is an array
            if (!Array.isArray(choices) || choices.length === 0) {
                throw new Error('Invalid choices format');
            }
            
            const shuffledChoices = shuffleArray([...choices]);
            
            mcqChoices.innerHTML = shuffledChoices.map((choice, i) => `
                <button class="choice-btn" onclick="selectChoice('${escapeHtml(choice)}', '${escapeHtml(card.answer)}')" data-choice="${escapeHtml(choice)}">
                    ${String.fromCharCode(65 + i)}) ${escapeHtml(choice)}
                </button>
            `).join('');
            
            mcqChoices.classList.remove('hidden');
            openAnswer.classList.add('hidden');
        } catch (e) {
            // If choices parsing fails, treat as open answer question
            console.warn('Invalid choices format for card:', card.id, e);
            document.getElementById('userAnswer').value = '';
            openAnswer.classList.remove('hidden');
            mcqChoices.classList.add('hidden');
        }
    } else {
        document.getElementById('userAnswer').value = '';
        openAnswer.classList.remove('hidden');
        mcqChoices.classList.add('hidden');
    }
    
    updateProgress();
}

function selectChoice(selected, correct) {
    const isCorrect = selected === correct;
    
    if (isCorrect) {
        score++;
    }
    
    userAnswers.push({
        question: cards[currentQuestionIndex].question,
        userAnswer: selected,
        correctAnswer: correct,
        isCorrect: isCorrect
    });
    
    const buttons = document.querySelectorAll('.choice-btn');
    buttons.forEach(btn => {
        btn.disabled = true;
        const choice = btn.dataset.choice;
        
        if (choice === correct) {
            btn.classList.add('correct');
        } else if (choice === selected && !isCorrect) {
            btn.classList.add('incorrect');
        }
    });
    
    showFeedback(isCorrect, correct);
    
    setTimeout(() => {
        showQuestion(currentQuestionIndex + 1);
    }, 2000);
}

function checkAnswer() {
    const userAnswer = document.getElementById('userAnswer').value.trim();
    const correctAnswer = cards[currentQuestionIndex].answer;
    
    if (!userAnswer) {
        showMessage('Please enter an answer', 'warning');
        return;
    }
    
    const isCorrect = userAnswer.toLowerCase().includes(correctAnswer.toLowerCase().substring(0, 5)) ||
                      correctAnswer.toLowerCase().includes(userAnswer.toLowerCase().substring(0, 5));
    
    if (isCorrect) {
        score++;
    }
    
    userAnswers.push({
        question: cards[currentQuestionIndex].question,
        userAnswer: userAnswer,
        correctAnswer: correctAnswer,
        isCorrect: isCorrect
    });
    
    showFeedback(isCorrect, correctAnswer);
    
    setTimeout(() => {
        showQuestion(currentQuestionIndex + 1);
    }, 3000);
}

function showFeedback(isCorrect, correctAnswer) {
    const feedback = document.getElementById('feedback');
    
    if (isCorrect) {
        feedback.innerHTML = `
            <div class="feedback correct">
                <h3>✅ Correct!</h3>
                <p>Great job!</p>
            </div>
        `;
    } else {
        feedback.innerHTML = `
            <div class="feedback incorrect">
                <h3>❌ Incorrect</h3>
                <div class="feedback-answer">
                    <strong>Correct answer:</strong> ${escapeHtml(correctAnswer)}
                </div>
            </div>
        `;
    }
    
    feedback.classList.remove('hidden');
}

async function showResults() {
    document.getElementById('questionCard').classList.add('hidden');
    
    const percentage = Math.round((score / cards.length) * 100);
    
    document.getElementById('scorePercent').textContent = percentage + '%';
    document.getElementById('scoreText').textContent = `You got ${score} out of ${cards.length} correct!`;
    
    const details = document.getElementById('resultDetails');
    details.innerHTML = `
        <div style="text-align: left; max-width: 600px; margin: 20px auto;">
            ${userAnswers.map((answer, i) => `
                <div style="margin-bottom: 20px; padding: 15px; background: ${answer.isCorrect ? '#f0fdf4' : '#fef2f2'}; border-radius: 8px;">
                    <strong>Q${i + 1}:</strong> ${escapeHtml(answer.question)}<br>
                    <strong>Your answer:</strong> ${escapeHtml(answer.userAnswer)}<br>
                    ${!answer.isCorrect ? `<strong>Correct answer:</strong> ${escapeHtml(answer.correctAnswer)}<br>` : ''}
                    <strong>Result:</strong> ${answer.isCorrect ? '✅ Correct' : '❌ Incorrect'}
                </div>
            `).join('')}
        </div>
    `;
    
    document.getElementById('results').classList.remove('hidden');
    
    try {
        const response = await fetch('/api/quiz-results', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                deck_id: DECK_ID,
                score: score,
                total: cards.length
            })
        });
        
        const data = await response.json();
        
        if (data.badges_earned && data.badges_earned.length > 0) {
            setTimeout(() => showBadgeModal(data.badges_earned), 1000);
        }
    } catch (error) {
        console.error('Error saving quiz results:', error);
    }
}

function restartQuiz() {
    currentQuestionIndex = 0;
    score = 0;
    userAnswers = [];
    cards = shuffleArray(cards);
    
    document.getElementById('results').classList.add('hidden');
    document.getElementById('questionCard').classList.remove('hidden');
    
    showQuestion(0);
}

function updateProgress() {
    const total = cards.length;
    const current = Math.min(currentQuestionIndex, total);
    const percentage = total > 0 ? (current / total) * 100 : 0;
    
    document.getElementById('progressFill').style.width = percentage + '%';
    document.getElementById('progressText').textContent = `Question ${current} / ${total}`;
}

function shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
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

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
