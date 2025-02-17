// Momentum module for handling user progress, achievements, and leaderboard
const momentum = {
    // Cache DOM elements
    elements: {
        currentLevel: document.getElementById('current-level'),
        levelTitle: document.getElementById('level-title'),
        levelProgress: document.getElementById('level-progress'),
        levelProgressText: document.getElementById('level-progress-text'),
        totalPoints: document.getElementById('total-points'),
        weeklyPoints: document.getElementById('weekly-points'),
        monthlyPoints: document.getElementById('monthly-points'),
        leaderboardRank: document.getElementById('leaderboard-rank'),
        streaksContainer: document.getElementById('streaks-container'),
        achievementsContainer: document.getElementById('achievements-container'),
        leaderboardContainer: document.getElementById('leaderboard-container')
    },

    // Initialize momentum module
    init() {
        if (!checkAuthState()) return;
        this.loadUserProgress();
        this.loadStreaks();
        this.loadAchievements();
        this.loadLeaderboard('weekly');
        this.setupEventListeners();
    },

    // Setup event listeners
    setupEventListeners() {
        // Achievement category filters
        document.querySelectorAll('[data-category]').forEach(button => {
            button.addEventListener('click', (e) => {
                document.querySelectorAll('[data-category]').forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
                this.loadAchievements(e.target.dataset.category);
            });
        });

        // Leaderboard timeframe filters
        document.querySelectorAll('[data-timeframe]').forEach(button => {
            button.addEventListener('click', (e) => {
                document.querySelectorAll('[data-timeframe]').forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
                this.loadLeaderboard(e.target.dataset.timeframe);
            });
        });
    },

    // Load user progress data
    async loadUserProgress() {
        try {
            const response = await fetchWithAuth('/momentum/progress');
            if (response.ok) {
                const data = await response.json();
                this.updateProgressUI(data);
            }
        } catch (error) {
            console.error('Error loading user progress:', error);
        }
    },

    // Update progress UI elements
    updateProgressUI(data) {
        const { current_level, total_points, points_to_next_level, completion_percentage } = data;
        
        if (this.elements.currentLevel) {
            this.elements.currentLevel.textContent = current_level.level_number;
        }
        if (this.elements.levelTitle) {
            this.elements.levelTitle.textContent = current_level.title;
        }
        if (this.elements.levelProgress) {
            this.elements.levelProgress.style.width = `${completion_percentage}%`;
        }
        if (this.elements.levelProgressText) {
            this.elements.levelProgressText.textContent = `${points_to_next_level} points to next level`;
        }
        if (this.elements.totalPoints) {
            this.elements.totalPoints.textContent = total_points.toLocaleString();
        }
    },

    // Load user streaks
    async loadStreaks() {
        try {
            const response = await fetchWithAuth('/momentum/streaks');
            if (response.ok) {
                const streaks = await response.json();
                this.updateStreaksUI(streaks);
            }
        } catch (error) {
            console.error('Error loading streaks:', error);
        }
    },

    // Update streaks UI
    updateStreaksUI(streaks) {
        if (!this.elements.streaksContainer) return;

        const streakHTML = streaks.map(streak => `
            <div class="streak-item d-flex align-items-center mb-3">
                <div class="streak-icon me-3">
                    <i class="fas fa-fire text-danger"></i>
                </div>
                <div class="flex-grow-1">
                    <h6 class="mb-0">${this.formatStreakType(streak.streak_type)}</h6>
                    <small class="text-muted">${streak.current_count} day${streak.current_count !== 1 ? 's' : ''}</small>
                </div>
                <div class="streak-record text-end">
                    <small class="text-muted">Best: ${streak.longest_count} days</small>
                </div>
            </div>
        `).join('');

        this.elements.streaksContainer.innerHTML = streakHTML || '<p class="text-muted mb-0">No active streaks</p>';
    },

    // Format streak type for display
    formatStreakType(type) {
        return type.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    },

    // Load achievements
    async loadAchievements(category = 'all') {
        try {
            const url = category === 'all' 
                ? '/momentum/achievements' 
                : `/momentum/achievements?category=${category}`;
            const response = await fetchWithAuth(url);
            if (response.ok) {
                const achievements = await response.json();
                this.updateAchievementsUI(achievements);
            }
        } catch (error) {
            console.error('Error loading achievements:', error);
        }
    },

    // Update achievements UI
    updateAchievementsUI(achievements) {
        if (!this.elements.achievementsContainer) return;

        const achievementHTML = achievements.map(achievement => `
            <div class="col-md-4 col-lg-3">
                <div class="card h-100 ${achievement.completed ? 'border-success' : 'border-light'}">
                    <div class="card-body text-center">
                        <div class="achievement-icon mb-3">
                            <i class="fas fa-${achievement.achievement.icon_name} fa-2x ${achievement.completed ? 'text-success' : 'text-muted'}"></i>
                        </div>
                        <h6 class="card-title">${achievement.achievement.name}</h6>
                        <p class="card-text small text-muted">${achievement.achievement.description}</p>
                        <div class="progress" style="height: 5px;">
                            <div class="progress-bar bg-success" role="progressbar" 
                                style="width: ${(achievement.progress / achievement.achievement.criteria_value) * 100}%">
                            </div>
                        </div>
                        <small class="text-muted mt-2 d-block">
                            ${achievement.progress} / ${achievement.achievement.criteria_value}
                        </small>
                    </div>
                </div>
            </div>
        `).join('');

        this.elements.achievementsContainer.innerHTML = achievementHTML || '<p class="text-muted">No achievements found</p>';
    },

    // Load leaderboard
    async loadLeaderboard(timeframe = 'weekly') {
        try {
            const response = await fetchWithAuth(`/momentum/leaderboard?timeframe=${timeframe}`);
            if (response.ok) {
                const leaderboard = await response.json();
                this.updateLeaderboardUI(leaderboard);
            }
        } catch (error) {
            console.error('Error loading leaderboard:', error);
        }
    },

    // Update leaderboard UI
    updateLeaderboardUI(leaderboard) {
        if (!this.elements.leaderboardContainer) return;

        const leaderboardHTML = leaderboard.map((entry, index) => `
            <div class="leaderboard-item d-flex align-items-center mb-3 ${index < 3 ? 'top-three' : ''}">
                <div class="rank me-3">
                    ${this.getLeaderboardRankIcon(index + 1)}
                </div>
                <div class="flex-grow-1">
                    <h6 class="mb-0">${entry.username}</h6>
                    <small class="text-muted">Level ${entry.level}</small>
                </div>
                <div class="points text-end">
                    <span class="h6 mb-0">${entry.points.toLocaleString()}</span>
                    <small class="text-muted d-block">points</small>
                </div>
            </div>
        `).join('');

        this.elements.leaderboardContainer.innerHTML = leaderboardHTML || '<p class="text-muted">No leaderboard data</p>';
    },

    // Get rank icon for leaderboard
    getLeaderboardRankIcon(rank) {
        switch (rank) {
            case 1:
                return '<i class="fas fa-crown text-warning fa-lg"></i>';
            case 2:
                return '<i class="fas fa-medal text-secondary fa-lg"></i>';
            case 3:
                return '<i class="fas fa-award text-bronze fa-lg"></i>';
            default:
                return `<span class="text-muted">#${rank}</span>`;
        }
    }
};

// Initialize momentum module when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Update username in navbar from the token
    const username = document.getElementById('username');
    if (username) {
        const token = localStorage.getItem('access_token');
        if (token) {
            const payload = parseJwt(token);
            username.textContent = payload.username;
        }
    }

    // Initialize momentum module
    momentum.init();
}); 