// Add these state variables at the top of your script
let activeTaskId = null;
let taskTimers = {};
let currentTaskStartTime = null;

// Modify the timeSlotForm submit handler
document.getElementById('timeSlotForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const startTime = document.getElementById('startTime').value;
    const endTime = document.getElementById('endTime').value;
    const task = document.getElementById('task').value;
    
    // Generate unique ID for the task
    const taskId = 'task-' + Date.now();
    
    // Calculate duration in minutes
    const start = new Date(`2000/01/01 ${startTime}`);
    const end = new Date(`2000/01/01 ${endTime}`);
    const durationMinutes = Math.round((end - start) / 60000);
    
    addTimeSlot(taskId, startTime, endTime, task, durationMinutes);
    this.reset();
});

function addTimeSlot(taskId, startTime, endTime, task, durationMinutes) {
    const tbody = document.querySelector('#timeSlotTable tbody');
    const row = document.createElement('tr');
    row.setAttribute('data-task-id', taskId);
    
    row.innerHTML = `
        <td>${startTime} - ${endTime}</td>
        <td>
            <div class="form-check">
                <input class="form-check-input task-checkbox" type="checkbox" value="">
            </div>
        </td>
        <td>${task}</td>
        <td class="task-report">0/${durationMinutes}</td>
        <td>
            <span class="progress-badge not-started">Not Started</span>
        </td>
        <td>
            <div class="rating-stars">
                <i class="far fa-star"></i>
                <i class="far fa-star"></i>
                <i class="far fa-star"></i>
                <i class="far fa-star"></i>
                <i class="far fa-star"></i>
            </div>
        </td>
        <td>
            <button class="btn btn-sm btn-success start-task-btn">
                <i class="fas fa-play"></i>
            </button>
            <button class="btn btn-sm btn-warning pause-task-btn" style="display: none;">
                <i class="fas fa-pause"></i>
            </button>
        </td>
    `;
    
    tbody.appendChild(row);
    initializeTaskControls(taskId, durationMinutes);
}

function initializeTaskControls(taskId, durationMinutes) {
    const row = document.querySelector(`tr[data-task-id="${taskId}"]`);
    const startBtn = row.querySelector('.start-task-btn');
    const pauseBtn = row.querySelector('.pause-task-btn');
    const checkbox = row.querySelector('.task-checkbox');
    
    // Initialize timer state
    taskTimers[taskId] = {
        elapsed: 0,
        duration: durationMinutes,
        interval: null
    };
    
    startBtn.addEventListener('click', () => startTask(taskId));
    pauseBtn.addEventListener('click', () => pauseTask(taskId));
    checkbox.addEventListener('change', () => completeTask(taskId));
}

function startTask(taskId) {
    // If another task is running, pause it first
    if (activeTaskId && activeTaskId !== taskId) {
        pauseTask(activeTaskId);
    }
    
    activeTaskId = taskId;
    const row = document.querySelector(`tr[data-task-id="${taskId}"]`);
    const startBtn = row.querySelector('.start-task-btn');
    const pauseBtn = row.querySelector('.pause-task-btn');
    
    // Update UI
    startBtn.style.display = 'none';
    pauseBtn.style.display = 'inline-block';
    row.querySelector('.progress-badge').className = 'progress-badge in-progress';
    row.querySelector('.progress-badge').textContent = 'In Progress';
    
    // Start Pomodoro timer
    const workTime = document.getElementById('workTime').value;
    startPomodoro(workTime);
    
    // Start task timer
    currentTaskStartTime = Date.now();
    taskTimers[taskId].interval = setInterval(() => updateTaskTimer(taskId), 60000); // Update every minute
}

function pauseTask(taskId) {
    const row = document.querySelector(`tr[data-task-id="${taskId}"]`);
    const startBtn = row.querySelector('.start-task-btn');
    const pauseBtn = row.querySelector('.pause-task-btn');
    
    // Update UI
    startBtn.style.display = 'inline-block';
    pauseBtn.style.display = 'none';
    
    // Stop timers
    clearInterval(taskTimers[taskId].interval);
    resetPomodoro();
    
    // Update elapsed time
    if (currentTaskStartTime) {
        const additionalMinutes = Math.floor((Date.now() - currentTaskStartTime) / 60000);
        taskTimers[taskId].elapsed += additionalMinutes;
        currentTaskStartTime = null;
    }
    
    // Update report
    updateTaskReport(taskId);
}

function completeTask(taskId) {
    const row = document.querySelector(`tr[data-task-id="${taskId}"]`);
    const checkbox = row.querySelector('.task-checkbox');
    
    if (checkbox.checked) {
        // If task was running, pause it first
        if (activeTaskId === taskId) {
            pauseTask(taskId);
        }
        
        // Update UI
        row.querySelector('.progress-badge').className = 'progress-badge completed';
        row.querySelector('.progress-badge').textContent = 'Completed';
        row.querySelector('.start-task-btn').disabled = true;
        row.querySelector('.pause-task-btn').disabled = true;
        
        // Save completion data
        saveTaskCompletion(taskId);
    }
}

function updateTaskTimer(taskId) {
    if (currentTaskStartTime) {
        const elapsedMinutes = Math.floor((Date.now() - currentTaskStartTime) / 60000);
        taskTimers[taskId].elapsed = elapsedMinutes;
        updateTaskReport(taskId);
    }
}

function updateTaskReport(taskId) {
    const row = document.querySelector(`tr[data-task-id="${taskId}"]`);
    const reportCell = row.querySelector('.task-report');
    reportCell.textContent = `${taskTimers[taskId].elapsed}/${taskTimers[taskId].duration}`;
}

function saveTaskCompletion(taskId) {
    const row = document.querySelector(`tr[data-task-id="${taskId}"]`);
    const taskData = {
        taskId: taskId,
        elapsed: taskTimers[taskId].elapsed,
        duration: taskTimers[taskId].duration,
        completed: true,
        timestamp: new Date().toISOString()
    };
    
    // Here you would typically send this data to your backend
    console.log('Saving task completion:', taskData);
    // fetch('/api/tasks/complete', {
    //     method: 'POST',
    //     headers: {
    //         'Content-Type': 'application/json'
    //     },
    //     body: JSON.stringify(taskData)
    // });
}

// Modify the existing Pomodoro timer functions
function startPomodoro(minutes) {
    // Your existing startTimer logic
    document.getElementById('startBtn').click();
}

function resetPomodoro() {
    // Your existing resetTimer logic
    document.getElementById('resetBtn').click();
}