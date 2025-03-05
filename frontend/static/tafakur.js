/**
 * Tafakur - Daily Reflection Module
 */

// Main Tafakur module
const tafakur = {
    // Cache DOM elements
    elements: {
        // Form elements
        form: document.getElementById('reflection-form'),
        dateInput: document.getElementById('reflection-date'),
        dateDisplay: document.getElementById('reflection-date-display'),
        moodInput: document.getElementById('mood-input'),
        moodButtons: document.querySelectorAll('.mood-btn'),
        highlightsInput: document.getElementById('highlights'),
        challengesInput: document.getElementById('challenges'),
        gratitudeInput: document.getElementById('gratitude'),
        lessonsInput: document.getElementById('lessons'),
        tomorrowGoalsInput: document.getElementById('tomorrow-goals'),
        tagsInput: document.getElementById('tags'),
        privateCheck: document.getElementById('privateCheck'),
        saveButton: document.getElementById('save-reflection'),
        
        // Visualization elements
        streakBadge: document.getElementById('streak-badge'),
        streakCount: document.querySelector('.streak-count'),
        streakProgress: document.getElementById('streak-progress'),
        longestStreak: document.getElementById('longest-streak'),
        moodChart: document.getElementById('moodChart'),
        tagCloud: document.getElementById('tag-cloud'),
        reflectionHistory: document.getElementById('reflection-history'),
        emptyHistory: document.getElementById('empty-history')
    },
    
    // State
    state: {
        currentReflection: null,
        reflections: [],
        streak: { current: 0, longest: 0, lastDate: null },
        chart: null,
        moodColors: {
            'Great': '#22c55e',
            'Good': '#3b82f6',
            'Okay': '#f59e0b',
            'Down': '#f97316',
            'Stressed': '#ef4444'
        }
    },
    
    // Initialize the module
    init() {
        if (!checkAuthState()) return;
        
        this.setDefaultDate();
        this.setupEventListeners();
        this.loadCurrentStreak();
        this.loadTodayReflection();
        this.loadReflectionHistory();
        this.initMoodChart();
    },
    
    // Set default date to today
    setDefaultDate() {
        const today = new Date();
        const formattedDate = today.toISOString().split('T')[0];
        
        if (this.elements.dateInput) {
            this.elements.dateInput.value = formattedDate;
        }
        
        this.updateDateDisplay(today);
    },
    
    // Format date for display
    formatDateForDisplay(date) {
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        return date.toLocaleDateString(undefined, options);
    },
    
    // Update the date display
    updateDateDisplay(date) {
        const isToday = new Date().toDateString() === date.toDateString();
        const displayText = isToday ? "Today's Reflection" : this.formatDateForDisplay(date);
        
        if (this.elements.dateDisplay) {
            this.elements.dateDisplay.textContent = displayText;
        }
    },
    
    // Setup event listeners
    setupEventListeners() {
        // Date selector change
        if (this.elements.dateInput) {
            this.elements.dateInput.addEventListener('change', (e) => {
                const selectedDate = new Date(e.target.value);
                this.updateDateDisplay(selectedDate);
                this.loadReflectionForDate(e.target.value);
            });
        }
        
        // Mood button selection
        this.elements.moodButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.elements.moodButtons.forEach(btn => btn.classList.remove('selected'));
                button.classList.add('selected');
                this.elements.moodInput.value = button.dataset.mood;
            });
        });
        
        // Save button
        if (this.elements.saveButton) {
            this.elements.saveButton.addEventListener('click', () => this.saveReflection());
        }
    },
    
    // Load reflection for a specific date
    async loadReflectionForDate(dateStr) {
        try {
            const response = await fetchWithAuth(`/api/tafakur/reflections/date/${dateStr}`);
            
            if (response.ok) {
                const reflection = await response.json();
                if (reflection) {
                    this.populateForm(reflection);
                    this.state.currentReflection = reflection;
                } else {
                    this.clearForm();
                    this.state.currentReflection = null;
                }
            } else {
                this.clearForm();
                this.state.currentReflection = null;
            }
        } catch (error) {
            console.error('Error loading reflection:', error);
        }
    },
    
    // Load today's reflection
    async loadTodayReflection() {
        try {
            const response = await fetchWithAuth('/api/tafakur/reflections/today');
            
            if (response.ok) {
                const reflection = await response.json();
                if (reflection) {
                    this.populateForm(reflection);
                    this.state.currentReflection = reflection;
                }
            }
        } catch (error) {
            console.error('Error loading today reflection:', error);
        }
    },
    
    // Populate form with reflection data
    populateForm(reflection) {
        if (!reflection) return;
        
        // Set the mood
        this.elements.moodInput.value = reflection.mood || '';
        this.elements.moodButtons.forEach(btn => {
            if (btn.dataset.mood === reflection.mood) {
                btn.classList.add('selected');
            } else {
                btn.classList.remove('selected');
            }
        });
        
        // Set text fields
        this.elements.highlightsInput.value = reflection.highlights || '';
        this.elements.challengesInput.value = reflection.challenges || '';
        this.elements.gratitudeInput.value = reflection.gratitude || '';
        this.elements.lessonsInput.value = reflection.lessons || '';
        this.elements.tomorrowGoalsInput.value = reflection.tomorrow_goals || '';
        
        // Set tags
        if (reflection.tags && reflection.tags.length > 0) {
            const tagStrings = reflection.tags.map(tag => tag.tag_name);
            this.elements.tagsInput.value = tagStrings.join(', ');
        } else {
            this.elements.tagsInput.value = '';
        }
        
        // Set privacy
        this.elements.privateCheck.checked = reflection.private;
    },
    
    // Clear the form
    clearForm() {
        this.elements.moodInput.value = '';
        this.elements.moodButtons.forEach(btn => btn.classList.remove('selected'));
        
        this.elements.highlightsInput.value = '';
        this.elements.challengesInput.value = '';
        this.elements.gratitudeInput.value = '';
        this.elements.lessonsInput.value = '';
        this.elements.tomorrowGoalsInput.value = '';
        this.elements.tagsInput.value = '';
        this.elements.privateCheck.checked = true;
    },
    
    // Save reflection
    async saveReflection() {
        // Validate that at least one field is filled
        if (!this.validateForm()) {
            alert('Please fill at least one field in your reflection.');
            return;
        }
        
        // Prepare data
        const reflectionDate = this.elements.dateInput.value;
        const data = {
            reflection_date: reflectionDate,
            mood: this.elements.moodInput.value,
            highlights: this.elements.highlightsInput.value,
            challenges: this.elements.challengesInput.value,
            gratitude: this.elements.gratitudeInput.value,
            lessons: this.elements.lessonsInput.value,
            tomorrow_goals: this.elements.tomorrowGoalsInput.value,
            private: this.elements.privateCheck.checked,
            tags: this.elements.tagsInput.value.split(',')
                .map(tag => tag.trim())
                .filter(tag => tag.length > 0)
        };
        
        try {
            const response = await fetchWithAuth('/api/tafakur/reflections', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                const savedReflection = await response.json();
                this.state.currentReflection = savedReflection;
                this.showSaveConfirmation();
                
                // Refresh the page data
                this.loadCurrentStreak();
                this.loadReflectionHistory();
            } else {
                const errorData = await response.json();
                alert(`Error saving reflection: ${errorData.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error saving reflection:', error);
            alert('An error occurred while saving your reflection. Please try again.');
        }
    },
    
    // Validate form
    validateForm() {
        // Check if at least one field is filled
        return this.elements.moodInput.value ||
            this.elements.highlightsInput.value ||
            this.elements.challengesInput.value ||
            this.elements.gratitudeInput.value ||
            this.elements.lessonsInput.value ||
            this.elements.tomorrowGoalsInput.value;
    },
    
    // Show save confirmation
    showSaveConfirmation() {
        const saveButton = this.elements.saveButton;
        const originalText = saveButton.innerHTML;
        
        saveButton.innerHTML = '<i class="fas fa-check me-2"></i>Saved!';
        saveButton.classList.add('btn-success');
        saveButton.disabled = true;
        
        setTimeout(() => {
            saveButton.innerHTML = originalText;
            saveButton.classList.remove('btn-success');
            saveButton.disabled = false;
        }, 2000);
    },
    
    // Load user's streak information
    async loadCurrentStreak() {
        try {
            const response = await fetchWithAuth('/api/tafakur/streak');
            
            if (response.ok) {
                const streakData = await response.json();
                this.updateStreakUI(streakData);
            }
        } catch (error) {
            console.error('Error loading streak data:', error);
        }
    },
    
    // Update streak UI elements
    updateStreakUI(streakData) {
        const { current_streak, longest_streak } = streakData;
        
        // Update state
        this.state.streak.current = current_streak;
        this.state.streak.longest = longest_streak;
        
        // Update streak badge
        if (this.elements.streakCount) {
            this.elements.streakCount.textContent = current_streak;
        }
        
        // Update streak progress
        if (this.elements.streakProgress) {
            // Calculate percentage (max 100%)
            const percentage = Math.min(100, (current_streak / 7) * 100);
            this.elements.streakProgress.style.width = `${percentage}%`;
            this.elements.streakProgress.textContent = `${current_streak} day${current_streak !== 1 ? 's' : ''}`;
        }
        
        // Update longest streak text
        if (this.elements.longestStreak) {
            this.elements.longestStreak.textContent = `Longest: ${longest_streak} day${longest_streak !== 1 ? 's' : ''}`;
        }
        
        // Add pulse animation if streak >= 3
        if (current_streak >= 3 && this.elements.streakBadge) {
            this.elements.streakBadge.classList.add('pulse');
        } else if (this.elements.streakBadge) {
            this.elements.streakBadge.classList.remove('pulse');
        }
    },
    
    // Load reflection history
    async loadReflectionHistory() {
        try {
            const response = await fetchWithAuth('/api/tafakur/reflections?limit=10');
            
            if (response.ok) {
                const reflections = await response.json();
                this.state.reflections = reflections;
                this.updateHistoryUI(reflections);
                this.updateTagCloud(reflections);
                this.updateMoodChart(reflections);
            }
        } catch (error) {
            console.error('Error loading reflection history:', error);
        }
    },
    
    // Update history UI
    updateHistoryUI(reflections) {
        if (!this.elements.reflectionHistory) return;
        
        if (reflections.length === 0) {
            if (this.elements.emptyHistory) {
                this.elements.emptyHistory.style.display = 'block';
            }
            return;
        }
        
        if (this.elements.emptyHistory) {
            this.elements.emptyHistory.style.display = 'none';
        }
        
        const historyHTML = reflections.map(reflection => {
            const date = new Date(reflection.reflection_date);
            const formattedDate = date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
            
            // Get a preview text from the first non-empty field
            const previewText = reflection.highlights || 
                                reflection.gratitude || 
                                reflection.lessons || 
                                reflection.challenges || 
                                reflection.tomorrow_goals || 
                                'No content';
            
            const preview = previewText.length > 120 ? previewText.substring(0, 120) + '...' : previewText;
            
            return `
                <div class="reflection-history-item" data-date="${reflection.reflection_date}">
                    <div class="d-flex justify-content-between">
                        <div class="date">${formattedDate}</div>
                        ${reflection.mood ? `<div class="mood"><i class="fas fa-${getMoodIcon(reflection.mood)}"></i> ${reflection.mood}</div>` : ''}
                    </div>
                    <div class="preview">${preview}</div>
                </div>
            `;
        }).join('');
        
        this.elements.reflectionHistory.innerHTML = historyHTML;
        
        // Add click handlers
        const historyItems = document.querySelectorAll('.reflection-history-item');
        historyItems.forEach(item => {
            item.addEventListener('click', () => {
                const date = item.dataset.date;
                this.elements.dateInput.value = date;
                this.updateDateDisplay(new Date(date));
                this.loadReflectionForDate(date);
            });
        });
    },
    
    // Update tag cloud
    updateTagCloud(reflections) {
        if (!this.elements.tagCloud) return;
        
        // Extract all tags
        const tags = [];
        reflections.forEach(reflection => {
            if (reflection.tags && reflection.tags.length > 0) {
                reflection.tags.forEach(tag => {
                    tags.push(tag.tag_name);
                });
            }
        });
        
        // Count tag frequencies
        const tagCounts = {};
        tags.forEach(tag => {
            tagCounts[tag] = (tagCounts[tag] || 0) + 1;
        });
        
        // Convert to array and sort by frequency
        const sortedTags = Object.entries(tagCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 15); // Show top 15 tags
        
        if (sortedTags.length === 0) {
            this.elements.tagCloud.innerHTML = '<div class="text-muted text-center">No tags yet</div>';
            return;
        }
        
        // Find max count to determine font size
        const maxCount = Math.max(...sortedTags.map(tag => tag[1]));
        
        // Generate HTML
        const tagHTML = sortedTags.map(([tag, count]) => {
            // Determine size class (1-5)
            const sizeClass = Math.ceil((count / maxCount) * 5);
            return `<div class="tag size-${sizeClass}">${tag}</div>`;
        }).join('');
        
        this.elements.tagCloud.innerHTML = tagHTML;
    },
    
    // Initialize mood chart
    initMoodChart() {
        if (!this.elements.moodChart) return;
        
        const ctx = this.elements.moodChart.getContext('2d');
        
        this.state.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Mood',
                    data: [],
                    borderColor: 'rgba(79, 70, 229, 0.8)',
                    backgroundColor: 'rgba(79, 70, 229, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: [],
                    pointBorderColor: 'white',
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 5,
                        ticks: {
                            stepSize: 1,
                            callback: function(value) {
                                const labels = ['', 'Stressed', 'Down', 'Okay', 'Good', 'Great'];
                                return labels[value] || '';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    },
    
    // Update mood chart with reflection data
    updateMoodChart(reflections) {
        if (!this.state.chart) return;
        
        // Map moods to numeric values
        const moodValues = {
            'Stressed': 1,
            'Down': 2,
            'Okay': 3,
            'Good': 4,
            'Great': 5
        };
        
        // Extract dates and moods
        const processedData = reflections
            .filter(r => r.mood)
            .map(r => ({
                date: new Date(r.reflection_date),
                mood: r.mood,
                value: moodValues[r.mood] || 3
            }))
            .sort((a, b) => a.date - b.date);
        
        if (processedData.length === 0) return;
        
        // Format dates for display
        const labels = processedData.map(item => {
            return item.date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
        });
        
        // Get mood values
        const data = processedData.map(item => item.value);
        
        // Get colors for points
        const pointColors = processedData.map(item => this.state.moodColors[item.mood] || 'grey');
        
        // Update chart
        this.state.chart.data.labels = labels;
        this.state.chart.data.datasets[0].data = data;
        this.state.chart.data.datasets[0].pointBackgroundColor = pointColors;
        this.state.chart.update();
    }
};

// Helper function to get mood icon
function getMoodIcon(mood) {
    switch(mood) {
        case 'Great': return 'laugh';
        case 'Good': return 'smile';
        case 'Okay': return 'meh';
        case 'Down': return 'frown';
        case 'Stressed': return 'tired';
        default: return 'question';
    }
}

// Initialize module when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    tafakur.init();
}); 