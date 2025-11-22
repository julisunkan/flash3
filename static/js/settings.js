
document.addEventListener('DOMContentLoaded', () => {
    loadApiKey();
});

function loadApiKey() {
    const apiKey = localStorage.getItem('gemini_api_key');
    if (apiKey) {
        document.getElementById('apiKeyInput').value = apiKey;
        document.getElementById('apiStatus').innerHTML = '<span class="status-success">✓ API key configured</span>';
    } else {
        document.getElementById('apiStatus').innerHTML = '<span class="status-warning">⚠ No API key configured</span>';
    }
}

function saveApiKey() {
    const apiKey = document.getElementById('apiKeyInput').value.trim();
    
    if (!apiKey) {
        showMessage('Please enter an API key', 'warning');
        return;
    }
    
    if (!apiKey.startsWith('AIza')) {
        showMessage('Invalid API key format. Gemini keys start with "AIza"', 'error');
        return;
    }
    
    localStorage.setItem('gemini_api_key', apiKey);
    document.getElementById('apiStatus').innerHTML = '<span class="status-success">✓ API key saved successfully</span>';
    showMessage('API key saved!', 'success');
}

async function testApiKey() {
    const apiKey = document.getElementById('apiKeyInput').value.trim();
    
    if (!apiKey) {
        showMessage('Please enter an API key first', 'warning');
        return;
    }
    
    showMessage('Testing API connection...', 'info');
    
    try {
        const response = await fetch('/api/test-gemini', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('apiStatus').innerHTML = '<span class="status-success">✓ API key is valid and working!</span>';
            showMessage('API key is working!', 'success');
        } else {
            document.getElementById('apiStatus').innerHTML = '<span class="status-error">✗ API key test failed</span>';
            showMessage(data.error || 'API key test failed', 'error');
        }
    } catch (error) {
        showMessage('Error testing API key: ' + error.message, 'error');
    }
}

let pendingClearApiKey = false;

function clearApiKey() {
    const container = document.querySelector('.settings-section') || document.querySelector('main');
    
    // Remove existing confirmation messages
    const existingConfirm = container.querySelectorAll('.inline-message.confirm');
    existingConfirm.forEach(msg => msg.remove());
    
    pendingClearApiKey = true;
    
    // Create confirmation message
    const confirmDiv = document.createElement('div');
    confirmDiv.className = 'inline-message confirm warning';
    confirmDiv.innerHTML = `
        <span style="font-size: 1.2rem;">⚠</span>
        <span>Are you sure you want to clear your API key?</span>
        <div style="display: flex; gap: 10px; margin-left: auto;">
            <button onclick="cancelClearApiKey()" style="padding: 6px 16px; background: #6b7280; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">Cancel</button>
            <button onclick="confirmClearApiKey()" style="padding: 6px 16px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600;">Clear</button>
        </div>
    `;
    
    // Insert at the top of the container
    container.insertBefore(confirmDiv, container.firstChild);
    
    // Scroll to top to show the message
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function cancelClearApiKey() {
    pendingClearApiKey = false;
    const container = document.querySelector('.settings-section') || document.querySelector('main');
    const confirmMsg = container.querySelector('.inline-message.confirm');
    if (confirmMsg) {
        confirmMsg.style.opacity = '0';
        confirmMsg.style.transform = 'translateY(-10px)';
        setTimeout(() => confirmMsg.remove(), 300);
    }
}

function confirmClearApiKey() {
    if (!pendingClearApiKey) return;
    
    pendingClearApiKey = false;
    
    // Remove confirmation message
    const container = document.querySelector('.settings-section') || document.querySelector('main');
    const confirmMsg = container.querySelector('.inline-message.confirm');
    if (confirmMsg) confirmMsg.remove();
    
    localStorage.removeItem('gemini_api_key');
    document.getElementById('apiKeyInput').value = '';
    document.getElementById('apiStatus').innerHTML = '<span class="status-warning">⚠ No API key configured</span>';
    showMessage('API key cleared', 'info');
}

function toggleApiKeyVisibility() {
    const input = document.getElementById('apiKeyInput');
    if (input.type === 'password') {
        input.type = 'text';
    } else {
        input.type = 'password';
    }
}

function showMessage(message, type = 'info') {
    const container = document.querySelector('.settings-section') || document.querySelector('main');
    
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
