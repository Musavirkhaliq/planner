// Momentum module for handling user progress, achievements, and leaderboard
const momentum = {
    // Cache DOM elements
    elements: {
        currentLevel: document.getElementById('current-level'),
        levelTitle: document.getElementById('level-title'),
        levelProgress: document.getElementById('level-progress'),
        profileLevel: document.getElementById('profile-level'),
        profileLevelTitle: document.getElementById('profile-level-title'),
        profileLevelProgress: document.getElementById('profile-level-progress'),
        levelProgressText: document.getElementById('level-progress-text'),
        totalPoints: document.getElementById('total-points'),
        profileTotalPoints: document.getElementById('profile-total-points'),
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
        const { current_level, next_level, total_points, points_to_next_level, completion_percentage } = data;
        
        // Store the current level data for possible use elsewhere
        this.currentLevel = current_level;
        this.nextLevel = next_level;
        
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
            // Show formatted points_to_next_level or "Max Level" if at max level
            const pointsText = next_level 
                ? `${points_to_next_level.toLocaleString()} points to next level`
                : `Highest level achieved! (${total_points.toLocaleString()} total points)`;
            this.elements.levelProgressText.textContent = pointsText;
        }
        
        if (this.elements.profileLevelProgress) {
            this.elements.profileLevelProgress.style.width = `${completion_percentage}%`;
        }
        
        if (this.elements.profileLevel) {
            this.elements.profileLevel.textContent = current_level.level_number;
        }
        
        if (this.elements.profileLevelTitle) {
            this.elements.profileLevelTitle.textContent = current_level.title;
        }
        
        if (this.elements.totalPoints) {
            this.elements.totalPoints.textContent = total_points.toLocaleString();
        }
        
        // Directly update the profile-total-points element, even if it's not in the elements object
        const profileTotalPoints = document.getElementById('profile-total-points');
        if (profileTotalPoints) {
            profileTotalPoints.textContent = total_points.toLocaleString();
        }
        
        // Check if this is an update with a level up from previous state
        if (this.previousLevel && current_level.level_number > this.previousLevel) {
            this.showLevelUpNotification(current_level);
        }
        
        // Store current level number for comparison in next update
        this.previousLevel = current_level.level_number;
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

        const achievementHTML = achievements.map(achievement => {
            // Calculate progress percentage
            const progressPercent = Math.min(100, Math.round((achievement.progress / achievement.achievement.criteria_value) * 100));
            
            // Determine status classes
            const isCompleted = achievement.completed;
            const statusClass = isCompleted ? 'completed' : 
                               (progressPercent > 75) ? 'almost' : 
                               (progressPercent > 25) ? 'in-progress' : '';
            
            return `
                <div class="col-md-12">
                    <div class="achievement-card ${statusClass}" 
                         data-completed="${isCompleted}" 
                         data-achievement-id="${achievement.achievement.id}">
                        <div class="achievement-icon-wrapper ${isCompleted ? 'pulsing' : ''}">
                            <i class="fas fa-${achievement.achievement.icon_name} fa-2x"></i>
                        </div>
                        <h6 class="achievement-title">${achievement.achievement.name}</h6>
                        <p class="achievement-description">${achievement.achievement.description}</p>
                        <div class="achievement-progress">
                            <div class="progress" style="height: 8px;">
                                <div class="progress-bar ${isCompleted ? 'bg-success' : 'bg-primary'}" 
                                     role="progressbar" 
                                     style="width: ${progressPercent}%"
                                     aria-valuenow="${progressPercent}" 
                                     aria-valuemin="0" 
                                     aria-valuemax="100">
                                </div>
                            </div>
                            <div class="progress-text">
                                <small class="text-muted">${achievement.progress} / ${achievement.achievement.criteria_value}</small>
                                <small class="completion-percentage ${isCompleted ? 'text-success' : ''}">${progressPercent}%</small>
                            </div>
                        </div>
                        ${isCompleted ? '<div class="completion-badge"><i class="fas fa-check-circle"></i></div>' : ''}
                    </div>
                </div>
            `;
        }).join('');

        this.elements.achievementsContainer.innerHTML = achievementHTML || '<p class="text-muted">No achievements found</p>';
        
        // Update achievement count in dropdown
        const completedCount = achievements.filter(a => a.completed).length;
        const achievementCountElements = document.querySelectorAll('#achievements-count');
        achievementCountElements.forEach(el => {
            if (el) el.textContent = completedCount;
        });
        
        // Add animation for newly completed achievements (if applicable)
        if (this.previousAchievements) {
            const newlyCompleted = achievements.filter(a => 
                a.completed && 
                !this.previousAchievements.find(pa => pa.achievement.id === a.achievement.id && pa.completed)
            );
            
            if (newlyCompleted.length > 0) {
                setTimeout(() => {
                    newlyCompleted.forEach(achievement => {
                        const card = document.querySelector(`[data-achievement-id="${achievement.achievement.id}"]`);
                        if (card) {
                            card.classList.add('newly-completed');
                            this.showAchievementNotification(achievement);
                        }
                    });
                }, 500);
            }
        }
        
        // Store current achievements for future comparison
        this.previousAchievements = [...achievements];
    },

    // Add new method to show achievement notification
    showAchievementNotification(achievement) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'achievement-notification';
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="fas fa-${achievement.achievement.icon_name}"></i>
            </div>
            <div class="notification-content">
                <h5>Achievement Unlocked!</h5>
                <p>${achievement.achievement.name}</p>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(notification);
        
        // Show with animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 500);
        }, 5000);
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

        const currentUser = this.getCurrentUsername();
        
        const leaderboardHTML = leaderboard.map((entry, index) => {
            const position = index + 1;
            const isCurrentUser = entry.username === currentUser;
            const positionClass = position <= 3 ? `top-${position}` : '';
            
            return `
                <div class="leaderboard-entry ${positionClass} ${isCurrentUser ? 'current-user' : ''}" data-position="${position}">
                    <div class="leaderboard-rank">
                        ${this.getLeaderboardRankIcon(position)}
                    </div>
                    <div class="leaderboard-user">
                        <div class="user-avatar">
                            <span>${entry.username.charAt(0).toUpperCase()}</span>
                        </div>
                        <div class="user-info">
                            <h6>${entry.username}</h6>
                            <div class="user-level">
                                <div class="mini-level-badge">${entry.level}</div>
                                <div class="streak-indicator">
                                    ${entry.has_streak ? '<i class="fas fa-fire text-danger"></i>' : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="leaderboard-points">
                        <span class="points-value">${entry.points.toLocaleString()}</span>
                        <small class="text-muted">pts</small>
                    </div>
                </div>
            `;
        }).join('');

        // Add header for the leaderboard
        const headerHTML = `
            <div class="leaderboard-header">
                <div class="leaderboard-rank">Rank</div>
                <div class="leaderboard-user">User</div>
                <div class="leaderboard-points">Points</div>
            </div>
        `;

        // Add empty state if no entries
        const emptyHTML = `
            <div class="leaderboard-empty">
                <div class="empty-icon">
                    <i class="fas fa-trophy"></i>
                </div>
                <p>No leaderboard data available yet. Complete tasks to earn points and appear here!</p>
            </div>
        `;

        this.elements.leaderboardContainer.innerHTML = 
            leaderboard.length > 0 
                ? headerHTML + leaderboardHTML
                : emptyHTML;
                
        // Add animation for entries with a slight delay between each
        const entries = document.querySelectorAll('.leaderboard-entry');
        entries.forEach((entry, index) => {
            setTimeout(() => {
                entry.classList.add('animate');
            }, index * 100);
        });
        
        // Update leaderboard rank in dropdown if current user is in the leaderboard
        const currentUserEntry = leaderboard.find(entry => entry.username === currentUser);
        const rankElements = document.querySelectorAll('#leaderboard-rank');
        rankElements.forEach(el => {
            if (el) {
                if (currentUserEntry) {
                    const position = leaderboard.indexOf(currentUserEntry) + 1;
                    el.textContent = position;
                } else {
                    el.textContent = '-';
                }
            }
        });
    },

    // Helper to get current username from token
    getCurrentUsername() {
        const token = localStorage.getItem('access_token');
        if (token) {
            const payload = parseJwt(token);
            return payload.username;
        }
        return '';
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
    },

    // Add method to show level up notification
    showLevelUpNotification(level) {
        // Create level up notification
        const notification = document.createElement('div');
        notification.className = 'level-up-notification';
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="fas fa-level-up-alt"></i>
            </div>
            <div class="notification-content">
                <h5>Level Up!</h5>
                <p>You've reached level ${level.level_number}: ${level.title}</p>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(notification);
        
        // Animate level badge
        const levelBadges = document.querySelectorAll('.level-badge');
        levelBadges.forEach(badge => {
            badge.classList.add('level-up');
            setTimeout(() => badge.classList.remove('level-up'), 2000);
        });
        
        // Show notification with animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 500);
        }, 5000);
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