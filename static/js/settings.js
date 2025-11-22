
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
        showToast('Please enter an API key', 'warning');
        return;
    }
    
    if (!apiKey.startsWith('AIza')) {
        showToast('Invalid API key format. Gemini keys start with "AIza"', 'error');
        return;
    }
    
    localStorage.setItem('gemini_api_key', apiKey);
    document.getElementById('apiStatus').innerHTML = '<span class="status-success">✓ API key saved successfully</span>';
    showToast('API key saved!', 'success');
}

async function testApiKey() {
    const apiKey = document.getElementById('apiKeyInput').value.trim();
    
    if (!apiKey) {
        showToast('Please enter an API key first', 'warning');
        return;
    }
    
    showToast('Testing API connection...', 'info');
    
    try {
        const response = await fetch('/api/test-gemini', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('apiStatus').innerHTML = '<span class="status-success">✓ API key is valid and working!</span>';
            showToast('API key is working!', 'success');
        } else {
            document.getElementById('apiStatus').innerHTML = '<span class="status-error">✗ API key test failed</span>';
            showToast(data.error || 'API key test failed', 'error');
        }
    } catch (error) {
        showToast('Error testing API key: ' + error.message, 'error');
    }
}

function clearApiKey() {
    if (!confirm('Are you sure you want to clear your API key?')) return;
    
    localStorage.removeItem('gemini_api_key');
    document.getElementById('apiKeyInput').value = '';
    document.getElementById('apiStatus').innerHTML = '<span class="status-warning">⚠ No API key configured</span>';
    showToast('API key cleared', 'info');
}

function toggleApiKeyVisibility() {
    const input = document.getElementById('apiKeyInput');
    if (input.type === 'password') {
        input.type = 'text';
    } else {
        input.type = 'password';
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    setTimeout(() => toast.classList.add('hidden'), 3000);
}
