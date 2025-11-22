
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadBadges();
});

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('totalStudied').textContent = stats.total_studied || 0;
        document.getElementById('dueToday').textContent = stats.due_today || 0;
        document.getElementById('avgRetention').textContent = stats.average_retention || '0.0';
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadBadges() {
    try {
        const response = await fetch('/api/badges');
        const badges = await response.json();
        
        const container = document.getElementById('badgesList');
        
        if (badges.length === 0) {
            container.innerHTML = '<p class="empty-state">No badges earned yet. Keep studying!</p>';
            return;
        }
        
        container.innerHTML = badges.map(badge => `
            <div class="badge-card">
                <div class="badge-icon">🏆</div>
                <div class="badge-name">${escapeHtml(badge.name)}</div>
                <div class="badge-date">${new Date(badge.earned_at).toLocaleDateString()}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading badges:', error);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
