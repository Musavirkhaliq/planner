// frontend/static/script.js

// Add this function at the beginning of the file
function parseJwt(token) {
    try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));

        return JSON.parse(jsonPayload);
    } catch(e) {
        return null;
    }
}

function isTokenExpired(token) {
    if (!token) return true;
    
    const decodedToken = parseJwt(token);
    if (!decodedToken) return true;

    const currentTime = Date.now() / 1000;
    return decodedToken.exp < currentTime;
}

// Add this function to check auth state
function checkAuthState() {
    const token = localStorage.getItem('access_token');
    const currentPath = window.location.pathname;
    const publicPaths = ['/login', '/register', '/verify-email'];
    
    if (isTokenExpired(token)) {
        localStorage.removeItem('access_token');
        
        // Only redirect if not already on a public path
        if (!publicPaths.some(path => currentPath.startsWith(path))) {
            window.location.href = '/login';
        }
        return false;
    }
    return true;
}

// Add this immediately after existing DOMContentLoaded listeners
document.addEventListener('DOMContentLoaded', () => {
    checkAuthState();
});

// Add visibility change handler to check token on tab focus
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        checkAuthState();
    }
});

// Check auth state every 5 minutes
setInterval(checkAuthState, 5 * 60 * 1000);

// ---------- LOGIN & REGISTER FUNCTIONS -----------
async function submitForm(e, url, formData, isJson = true) {
    e.preventDefault();
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: isJson ? { "Content-Type": "application/json" } : { "Content-Type": "application/x-www-form-urlencoded" },
            body: isJson ? JSON.stringify(formData) : new URLSearchParams(formData)
        });
        if (response.ok) {
             let result = await response.json();
             if (result.message) {
                if (result.message === "verify_email") {
                    window.location.href = `/verify-email?email=${result.email}`;
                }
             }
             return result;
        } else {
            const errorData = await response.json();
            alert(`Error: ${errorData.detail || "Unknown error"}`);
        }
    } catch (error) {
        console.error("Error during form submission:", error);
        alert("An error occurred. Please try again.");
    }
}

// Login Form Submission
document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const data = await submitForm(e, "/api/auth/token", { username: email, password: password }, false);
    if (data && data.access_token) {
        localStorage.setItem("access_token", data.access_token);
        window.location.href = "/dashboard";
    }
});

// Register Form Submission
document.getElementById("registerForm")?.addEventListener("submit", async (e) => {
    const email = document.getElementById("email").value;
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const data = await submitForm(e, "/api/users/", { email, username, password });
    if (data) {
        // Redirect to email verification page
        window.location.href = `/verify-email?email=${encodeURIComponent(email)}`;
    }
});

// ---------- DASHBOARD FUNCTIONS -----------
async function fetchWithAuth(url, options = {}) {
    if (!checkAuthState()) return;
    
    const token = localStorage.getItem("access_token");
    options.headers = {
        ...(options.headers || {}),
        "Authorization": `Bearer ${token}`
    };
    return await fetch(`/api${url}`, options);
}

// Time Slot Booking
async function bookTimeSlot() {
    const task = document.getElementById("task").value;
    const startTime = document.getElementById("startTime").value;
    const endTime = document.getElementById("endTime").value;
    // Create a description from the task
    const description = task;
    const response = await fetchWithAuth("/api/time_slots/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ start_time: startTime, end_time: endTime, description })
    });
    if (response && response.ok) {
        window.location.reload();
    } else {
        alert("Failed to book time slot");
    }
}

// Goals & Breakdown: add a goal
async function addGoal() {
    const goal = document.getElementById("goal").value;
    if (!goal) return;
    const response = await fetchWithAuth("/goals/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: goal, description: "" })
    });
    if (response && response.ok) {
        window.location.reload();
    } else {
        alert("Failed to add goal");
    }
}
//on clicking done insert the  data

document.addEventListener("DOMContentLoaded", () => {
  const checkboxes = document.querySelectorAll('.doneCheckbox');

  checkboxes.forEach(checkbox => {
      checkbox.addEventListener('click', async (event) => {
          const row = event.target.closest('tr');
          const time = row.cells[0].textContent;
          const done = event.target.checked;
          const task = row.cells[2].textContent;
          const report = row.cells[3].querySelector('.reportInput').value;
          const progress = row.cells[4].querySelector('progress').value;
          const rating = row.cells[5].querySelector('.ratingInput').value;

          if (done) {
              const taskData = {
                  time,
                  task,
                  report,
                  progress,
                  rating
              };

              // Send data to server
              const response = await fetchWithAuth('/tasks/', {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/json'
                  },
                  body: JSON.stringify(taskData)
              });

              if (response.ok) {
                  alert('Task marked as done and report submitted successfully!');
                  // Optionally, refresh the dashboard or update the UI
              } else {
                  alert('Failed to submit report');
              }
          }
      });
  });

  async function fetchWithAuth(url, options = {}) {
      // Add authentication headers if needed
      const token = localStorage.getItem('token');
      if (token) {
          options.headers = {
              ...options.headers,
              'Authorization': `Bearer ${token}`
          };
      }
      const response = await fetch(url, options);
      return response;
  }
});


// Load Tasks for the To-Do List
document.addEventListener("DOMContentLoaded", async () => {
    // Load tasks into the taskList element if present
    const taskList = document.getElementById("taskList");
    if (taskList) {
        const response = await fetchWithAuth("/tasks/");
        if (response.ok) {
            const tasks = await response.json();
            tasks.forEach(task => {
                const li = document.createElement("li");
                li.textContent = `${task.title}: ${task.description} - Time Spent: ${task.time_spent} hours`;
                taskList.appendChild(li);
            });
        } else {
            alert("Failed to fetch tasks");
        }
    }

    // Load Analytics Chart if canvas present

});


// frontend/static/script.js

document.addEventListener("DOMContentLoaded", () => {
  if (document.querySelector('.hours')) {
    initAuth();
    initTimeSlotForm();
    initBookingDatePicker();
    // Initially load bookings for today
    const today = new Date().toISOString().split("T")[0];
    document.getElementById("bookingDate").value = today;
    loadTimeSlotsByDate(today);
    // fetchAnalytics(today, today);
  }
});
  
  // ---------- AUTH FUNCTIONS ----------
  function initAuth() {
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
      });
    }
  }
  
  // ---------- TIME SLOT BOOKING FUNCTIONS ----------
  
  // Initialize date picker to reload table when a new date is chosen.
  function initBookingDatePicker() {
    const bookingDateInput = document.getElementById("bookingDate");
    if (bookingDateInput) {
        bookingDateInput.addEventListener("change", (e) => {
            const selectedDate = e.target.value;
            loadTimeSlotsByDate(selectedDate);
            // fetchAnalytics(selectedDate, selectedDate);
        });
    }
}
  
  // Submit the new time slot form.
  function initTimeSlotForm() {
    const timeSlotForm = document.getElementById("timeSlotForm");
    if (timeSlotForm) {
        timeSlotForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const startTime = document.getElementById("startTime").value;
            const endTime = document.getElementById("endTime").value;
            const task = document.getElementById("task").value;
            const bookingDate = document.getElementById("bookingDate").value;
            const token = localStorage.getItem("access_token");

            if (!token) {
                alert("Please log in to book time slots");
                window.location.href = "/login";
                return;
            }

            const payload = {
                start_time: `${bookingDate}T${startTime}`,
                end_time: `${bookingDate}T${endTime}`,
                description: task,
                date: bookingDate
            };

            const isEditing = timeSlotForm.dataset.editingId;
            // Ensure URL ends with trailing slash and use window.location.origin
            const baseUrl = window.location.origin;
            const apiPath = isEditing 
                ? `/api/time_slots/${timeSlotForm.dataset.editingId}/`
                : '/api/time_slots/';
            const url = `${baseUrl}${apiPath}`;
            const method = isEditing ? "PUT" : "POST";

            try {
                console.log('Sending request to:', url); // Debug log
                console.log('Payload:', payload); // Debug log

                const response = await fetch(url, {
                    method: method,
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`,
                    },
                    credentials: 'include', // Include cookies if needed
                    body: JSON.stringify(payload),
                    redirect: 'follow', // Handle redirects automatically
                });

                // Check if the response was redirected
                if (response.redirected) {
                    console.log('Request was redirected to:', response.url);
                }

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
                }

                const result = await response.json();
                console.log('Success:', result);

                // Reset form and update table
                timeSlotForm.reset();
                delete timeSlotForm.dataset.editingId;
                
                // Reset submit button
                const submitBtn = timeSlotForm.querySelector('button[type="submit"]');
                submitBtn.innerHTML = '<i class="fas fa-plus me-2"></i>Add';
                submitBtn.classList.remove('btn-success');
                submitBtn.classList.add('btn-primary');
                
                // Reapply the selected date and reload table
                document.getElementById("bookingDate").value = bookingDate;
                await loadTimeSlotsByDate(bookingDate);
                
                // Update analytics
                fetchTodayAnalytics();

            } catch (error) {
                console.error('Error details:', error);
                
                if (error.message.includes('Failed to fetch')) {
                    alert('Connection error. Please try again.');
                } else {
                    alert(`Failed to save time slot: ${error.message}`);
                }
            }
        });
    }
}
  
  // Render the time slot table rows.
  // Render the time slot table rows with edit and delete functionality
function renderTimeSlotTable(slots) {
  const tableBody = document.querySelector("#timeSlotTable tbody");
  tableBody.innerHTML = "";

  slots.forEach((slot) => {
      const start = new Date(slot.start_time);
      const end = new Date(slot.end_time);
      const allottedMinutes = Math.round((end - start) / 60000);
      const reportedMinutes = slot.report_minutes || 0;
      const progressPercent = Math.min(100, Math.round((reportedMinutes / allottedMinutes) * 100));
      const ratingStars = "★".repeat(Math.max(1, Math.round(progressPercent / 20)));

      const tr = document.createElement("tr");
      tr.setAttribute("data-slot-id", slot.id);

      // TIME
      const timeTd = document.createElement("td");
      timeTd.textContent = `${start.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} - ${end.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
      tr.appendChild(timeTd);

      // STATUS
      const statusTd = document.createElement("td");
      const statusSelect = document.createElement("select");
      statusSelect.className = "statusSelect form-select form-select-sm";
      statusSelect.innerHTML = `
          <option value="completed" ${slot.status === 'completed' ? 'selected' : ''}>Completed</option>
          <option value="in_progress" ${slot.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
          <option value="not_started" ${slot.status === 'not_started' ? 'selected' : ''}>Not Started</option>
      `;
      statusSelect.addEventListener("change", async () => {
          const newStatus = statusSelect.value;
          await updateTimeSlotField(slot.id, { status: newStatus });
      });
      statusTd.appendChild(statusSelect);
      tr.appendChild(statusTd);

      // TASK
      const descTd = document.createElement("td");
      descTd.textContent = slot.description;
      tr.appendChild(descTd);

      // REPORT
      const reportTd = document.createElement("td");
      const reportInput = document.createElement("input");
      reportInput.type = "number";
      reportInput.min = 0;
      reportInput.value = reportedMinutes;
      reportInput.className = "form-control form-control-sm";
      reportInput.style.width = "80px";
      reportInput.addEventListener("change", () => {
          updateTimeSlotReport(slot.id, parseInt(reportInput.value), allottedMinutes);
      });
      reportTd.appendChild(reportInput);
      tr.appendChild(reportTd);

      // PROGRESS
      const progressTd = document.createElement("td");
      const progressDiv = document.createElement("div");
      progressDiv.className = "progress";
      const progressBar = document.createElement("div");
      progressBar.className = "progress-bar";
      progressBar.style.width = `${progressPercent}%`;
      progressBar.textContent = `${progressPercent}%`;
      progressDiv.appendChild(progressBar);
      progressTd.appendChild(progressDiv);
      tr.appendChild(progressTd);

      // RATING
      const ratingTd = document.createElement("td");
      ratingTd.textContent = ratingStars;
      tr.appendChild(ratingTd);

      // ACTIONS
      const actionsTd = document.createElement("td");
      actionsTd.className = "text-end";
      actionsTd.innerHTML = `
          <div class="btn-group btn-group-sm">
              <button class="btn btn-outline-primary edit-slot" title="Edit">
                  <i class="fas fa-edit"></i>
              </button>
              <button class="btn btn-outline-danger delete-slot" title="Delete">
                  <i class="fas fa-trash-alt"></i>
              </button>
          </div>
      `;

      // Add event listeners for edit and delete
      const editBtn = actionsTd.querySelector('.edit-slot');
      const deleteBtn = actionsTd.querySelector('.delete-slot');

      editBtn.addEventListener('click', () => handleEdit(slot));
      deleteBtn.addEventListener('click', () => handleDelete(slot.id));

      tr.appendChild(actionsTd);
      tableBody.appendChild(tr);
  });
}


// Handle edit functionality
// Handle edit functionality
async function handleEdit(slot) {
  // Convert ISO datetime to date and time parts
  const startDateTime = new Date(slot.start_time);
  const endDateTime = new Date(slot.end_time);
  
  // Set form values
  document.getElementById('bookingDate').value = startDateTime.toISOString().split('T')[0];
  document.getElementById('startTime').value = startDateTime.toTimeString().slice(0, 5);
  document.getElementById('endTime').value = endDateTime.toTimeString().slice(0, 5);
  document.getElementById('task').value = slot.description;

  // Change form submit button
  const submitBtn = document.querySelector('#timeSlotForm button[type="submit"]');
  submitBtn.innerHTML = '<i class="fas fa-save me-2"></i>Update';
  submitBtn.classList.remove('btn-primary');
  submitBtn.classList.add('btn-success');
  
  // Store the slot ID being edited
  timeSlotForm.dataset.editingId = slot.id;
  
  // Scroll to form
  timeSlotForm.scrollIntoView({ behavior: 'smooth' });
}

// Handle delete functionality
async function handleDelete(slotId) {
  if (!confirm('Are you sure you want to delete this time slot?')) {
      return;
  }

  const token = localStorage.getItem('access_token');
  try {
      const response = await fetch(`/api/time_slots/${slotId}`, {
          method: 'DELETE',
          headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
          }
      });

      if (response.status === 204) {  // No Content response
          // Find and remove the row with animation
          const row = document.querySelector(`tr[data-slot-id="${slotId}"]`);
          if (row) {
              row.style.transition = 'opacity 0.3s';
              row.style.opacity = '0';
              setTimeout(() => {
                  row.remove();
                  // Update analytics after successful deletion
                  fetchTodayAnalytics();
              }, 300);
          }
      } else {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to delete time slot');
      }
  } catch (error) {
      console.error('Error deleting time slot:', error);
      alert(error.message || 'Failed to delete time slot. Please try again.');
  }
}


async function updateTimeSlotField(slotId, data) {
  const token = localStorage.getItem("access_token");
  try {
      const response = await fetch(`/api/time_slots/${slotId}`, {
          method: "PATCH",
          headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(data),
      });
      if (!response.ok) {
          alert("Failed to update time slot status");
      }
  } catch (error) {
      console.error("Error updating time slot status:", error);
      alert("An error occurred. Please try again.");
  }
}

  
  // When the report minutes input changes, update the booking.
  async function updateTimeSlotReport(slotId, reportMinutes, allottedMinutes) {
    const token = localStorage.getItem("access_token");
    // Calculate progress & rating on the front end for immediate feedback.
    const progressPercent = Math.min(
      100,
      Math.round((reportMinutes / allottedMinutes) * 100)
    );
    // Build star rating: use at least 1 star.
    const ratingStars = "★".repeat(Math.max(1, Math.round(progressPercent / 20)));
  
    // Find the row in the table and update its progress bar and rating cells.
    const row = document.querySelector(`tr[data-slot-id="${slotId}"]`);
    if (row) {
      const progressBar = row.children[4].querySelector(".progress-bar");
      progressBar.style.width = `${progressPercent}%`;
      progressBar.textContent = `${progressPercent}%`;
      row.children[5].textContent = ratingStars;
    }
  
    // Send the updated report value to the back‑end.
    // (Assuming your back‑end supports PATCH updates for time slot bookings.)
    const response = await fetch(`/api/time_slots/${slotId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ report_minutes: reportMinutes }),
    });
    if (!response.ok) {
      alert("Failed to update report minutes");
    }
  }
  
// --------------------------
// POMODORO TIMER FUNCTIONS
// --------------------------
let workTime = 25 * 60; // default work time in seconds
let breakTime = 5 * 60; // default break time in seconds
let timerInterval;
let isWorking = true;
let lastTimestamp;
let ws;

// WebSocket setup
function initializeWebSocket() {
  ws = new WebSocket('wss://your-websocket-server.com'); //  WebSocket server

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    syncTimerState(data);
  };

  ws.onclose = () => {
    // Attempt to reconnect
    setTimeout(initializeWebSocket, 1000);
  };
}

// Timer state management
function saveTimerState(remainingTime, isWorking, isActive) {
  const state = {
    remainingTime,
    isWorking,
    isActive,
    timestamp: Date.now()
  };
  localStorage.setItem('pomodoroState', JSON.stringify(state));
  
  // Broadcast state to other clients if WebSocket is connected
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(state));
  }
}

function loadTimerState() {
  const savedState = localStorage.getItem('pomodoroState');
  if (savedState) {
    const state = JSON.parse(savedState);
    const elapsedTime = Math.floor((Date.now() - state.timestamp) / 1000);
    
    // Adjust remaining time based on elapsed time since last save
    if (state.isActive) {
      state.remainingTime = Math.max(0, state.remainingTime - elapsedTime);
    }
    
    return state;
  }
  return null;
}

function syncTimerState(state) {
  isWorking = state.isWorking;
  if (state.isActive) {
    const display = document.querySelector("#time");
    const progressBar = document.querySelector("#progress");
    if (display && progressBar) {
      startTimer(state.remainingTime, display, progressBar);
    }
  }
}

function updateTimerDurationsFromInputs() {
  const workInput = document.getElementById("workTime");
  const breakInput = document.getElementById("breakTime");

  const workMinutes = workInput && workInput.value ? parseInt(workInput.value, 10) : 25;
  const breakMinutes = breakInput && breakInput.value ? parseInt(breakInput.value, 10) : 5;

  workTime = workMinutes * 60;
  breakTime = breakMinutes * 60;
  
  // Save new durations to localStorage
  localStorage.setItem('pomodoroSettings', JSON.stringify({ workTime, breakTime }));
}

function loadSettings() {
  const savedSettings = localStorage.getItem('pomodoroSettings');
  if (savedSettings) {
    const settings = JSON.parse(savedSettings);
    workTime = settings.workTime;
    breakTime = settings.breakTime;
    
    // Update input fields
    const workInput = document.getElementById("workTime");
    const breakInput = document.getElementById("breakTime");
    if (workInput) workInput.value = Math.floor(workTime / 60);
    if (breakInput) breakInput.value = Math.floor(breakTime / 60);
  }
}

function startTimer(duration, display, progressBar) {
  let remainingTime = duration;
  clearInterval(timerInterval);

  const updateDisplay = () => {
    const minutes = Math.floor(remainingTime / 60);
    const seconds = remainingTime % 60;
    display.textContent = `${minutes < 10 ? "0" + minutes : minutes}:${seconds < 10 ? "0" + seconds : seconds}`;

    const progress = ((duration - remainingTime) / duration) * 100;
    progressBar.style.width = `${progress}%`;
    
    // Save state every second
    saveTimerState(remainingTime, isWorking, true);
  };

  updateDisplay();
  timerInterval = setInterval(() => {
    if (remainingTime <= 0) {
      clearInterval(timerInterval);
      isWorking = !isWorking;
      remainingTime = isWorking ? workTime : breakTime;
      alert(isWorking ? "Time to work!" : "Time for a break!");
      startTimer(remainingTime, display, progressBar);
    } else {
      remainingTime--;
      updateDisplay();
    }
  }, 1000);
}

function resetTimer(display, progressBar) {
  clearInterval(timerInterval);
  isWorking = true;
  updateTimerDurationsFromInputs();
  
  const minutes = Math.floor(workTime / 60);
  const seconds = workTime % 60;
  display.textContent = `${minutes < 10 ? "0" + minutes : minutes}:${seconds < 10 ? "0" + seconds : seconds}`;
  progressBar.style.width = "0%";
  
  // Clear saved state
  localStorage.removeItem('pomodoroState');
  // Broadcast reset to other clients
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'reset' }));
  }
}

// Handle visibility change
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) {
    // Reload and sync state when tab becomes visible
    const state = loadTimerState();
    if (state) {
      syncTimerState(state);
    }
  }
});

// --------------------------
// INITIALIZATION
// --------------------------
document.addEventListener("DOMContentLoaded", () => {
  const display = document.querySelector("#time");
  const progressBar = document.querySelector("#progress");
  const startBtn = document.getElementById("startBtn");
  const resetBtn = document.getElementById("resetBtn");

  // Initialize WebSocket connection
  initializeWebSocket();
  
  // Load saved settings
  loadSettings();
  
  // Load and apply saved timer state
  const savedState = loadTimerState();
  if (savedState) {
    isWorking = savedState.isWorking;
    if (savedState.isActive && savedState.remainingTime > 0) {
      startTimer(savedState.remainingTime, display, progressBar);
    } else {
      const currentTime = isWorking ? workTime : breakTime;
      const minutes = Math.floor(currentTime / 60);
      const seconds = currentTime % 60;
      display.textContent = `${minutes < 10 ? "0" + minutes : minutes}:${seconds < 10 ? "0" + seconds : seconds}`;
    }
  } else {
    updateTimerDurationsFromInputs();
    const minutes = Math.floor(workTime / 60);
    const seconds = workTime % 60;
    if (display) {
      display.textContent = `${minutes < 10 ? "0" + minutes : minutes}:${seconds < 10 ? "0" + seconds : seconds}`;
    }
  }

  if (startBtn && display && progressBar) {
    startBtn.addEventListener("click", () => {
      updateTimerDurationsFromInputs();
      startTimer(workTime, display, progressBar);
    });
  }

  if (resetBtn && display && progressBar) {
    resetBtn.addEventListener("click", () => {
      resetTimer(display, progressBar);
    });
  }
});

async function loadTimeSlotsByDate(date) {
  const token = localStorage.getItem("access_token");
  try {
      const baseUrl = window.location.origin;
      const response = await fetch(`${baseUrl}/api/time_slots/?date=${date}`, {
          headers: { 
              Authorization: `Bearer ${token}`,
              'Accept': 'application/json'
          },
          credentials: 'include',
          redirect: 'follow'
      });
      
      if (response.ok) {
          const slots = await response.json();
          renderTimeSlotTable(slots); // Render the table with status
      } else {
          const error = await response.json().catch(() => ({}));
          alert(`Failed to load time slots: ${error.detail || 'Unknown error'}`);
      }
  } catch (error) {
      console.error("Error loading time slots:", error);
      alert("Failed to load time slots. Please check your connection and try again.");
  }
}

// Initialize date picker and load today's slots
document.addEventListener("DOMContentLoaded", () => {
  const today = new Date().toISOString().split('T')[0];
  const dateInput = document.getElementById("bookingDate");
  if (dateInput) {
      dateInput.value = today;
      loadTimeSlotsByDate(today);
      
      // Add event listener for date changes
      dateInput.addEventListener("change", (e) => {
          loadTimeSlotsByDate(e.target.value);
      });
  }
});

// Update digital clock
// check if the element exists
if (document.querySelector('.hours')) {
  function updateDigitalClock() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');

    document.querySelector('.hours').textContent = hours;
    document.querySelector('.minutes').textContent = minutes;
    document.querySelector('.seconds').textContent = seconds;
  }

  // Update clock every second
  setInterval(updateDigitalClock, 1000);
  updateDigitalClock(); // Initial update

  // Minimize/Maximize functionality with localStorage and responsive behavior
  const minimizeBtn = document.querySelector('.minimize-btn');
  const timerSection = document.querySelector('.timer-section');

  function checkWindowSize() {
    // Consider devices below 768px as mobile
    const isMobile = window.innerWidth < 768;
    
    // Get stored preference, defaulting to minimized on mobile
    const storedState = localStorage.getItem('timerSectionMinimized');
    const shouldMinimize = storedState === null ? isMobile : storedState === 'true';
    
    timerSection.style.display = shouldMinimize ? 'none' : 'block';
    minimizeBtn.innerHTML = shouldMinimize ? 
        '<i class="fas fa-plus"></i>' : '<i class="fas fa-minus"></i>';
        
    // Store initial state
    localStorage.setItem('timerSectionMinimized', shouldMinimize);
  }

  // Check on load
  checkWindowSize();

  // Check on resize
  let resizeTimeout;
  window.addEventListener('resize', () => {
    // Debounce the resize event
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(checkWindowSize, 250);
  });

  minimizeBtn.addEventListener('click', () => {
    const willMinimize = timerSection.style.display !== 'none';
    timerSection.style.display = willMinimize ? 'none' : 'block';
    minimizeBtn.innerHTML = willMinimize ? 
        '<i class="fas fa-plus"></i>' : '<i class="fas fa-minus"></i>';
    // Save state to localStorage
    localStorage.setItem('timerSectionMinimized', willMinimize);
  });
}




// for analytics



let completionTrendChart = null;
let timeDistributionChart = null;
let statusDistributionChart = null;

// Fetch overview analytics data
async function fetchOverviewAnalytics() {
  const token = localStorage.getItem("access_token");
  try {
    const response = await fetch("/analytics/overview", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      throw new Error("Failed to fetch overview analytics data");
    }
    const data = await response.json();
    document.getElementById("totalSlots").textContent = data.total_slots;
    document.getElementById("completedSlots").textContent = data.completed_slots;
    document.getElementById("inProgressSlots").textContent = data.in_progress_slots;
    document.getElementById("notStartedSlots").textContent = data.not_started_slots;
    document.getElementById("totalMinutes").textContent = data.total_minutes_reported;
    document.getElementById("avgMinutes").textContent = Math.round(data.average_minutes_per_slot);
    document.getElementById("completionRate").textContent = `${data.completion_rate}%`;

    updateStatusDistributionChart(data);
  } catch (error) {
    console.error("Error fetching overview analytics:", error);
  }
}

// Fetch today's analytics data
async function fetchTodayAnalytics() {
  const token = localStorage.getItem("access_token");
  try {
    const response = await fetch("/analytics/today", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      throw new Error("Failed to fetch today's analytics");
    }
    const data = await response.json();
    document.getElementById("todayTotalSlots").textContent = data.total_slots;
    document.getElementById("todayCompletedSlots").textContent = data.completed_slots;
    document.getElementById("todayTotalMinutes").textContent = data.total_minutes;
    document.getElementById("todayCompletionRate").textContent = `${data.completion_rate}%`;
  } catch (error) {
    console.error("Error fetching today's analytics:", error);
  }
}

// Update status distribution pie chart (Overview)
function updateStatusDistributionChart(data) {
  const ctx = document.getElementById("statusDistributionChart").getContext("2d");
  const chartData = {
    labels: ["Completed", "In Progress", "Not Started"],
    datasets: [
      {
        data: [data.completed_slots, data.in_progress_slots, data.not_started_slots],
        backgroundColor: [
          "rgba(34, 197, 94, 0.7)", // green
          "rgba(59, 130, 246, 0.7)", // blue
          "rgba(239, 68, 68, 0.7)"   // red
        ],
        borderColor: [
          "rgba(34, 197, 94, 1)",
          "rgba(59, 130, 246, 1)",
          "rgba(239, 68, 68, 1)"
        ],
        borderWidth: 1,
      },
    ],
  };

  if (statusDistributionChart) {
    statusDistributionChart.destroy();
  }
  statusDistributionChart = new Chart(ctx, {
    type: "pie",
    data: chartData,
    options: {
      responsive: true,
      plugins: {
        legend: { position: "top" },
        title: { display: true, text: "Slot Status Distribution" },
      },
    },
  });
}

// Fetch range analytics data and update additional analytics for the selected date range
async function fetchRangeAnalytics() {
  const startDate = document.getElementById("startDate").value;
  const endDate = document.getElementById("endDate").value;
  if (!startDate || !endDate) {
    alert("Please select both start and end dates");
    return;
  }
  const token = localStorage.getItem("access_token");
  try {
    const response = await fetch(
      `/analytics/range?start_date=${startDate}&end_date=${endDate}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!response.ok) {
      throw new Error("Failed to fetch range analytics data");
    }
    const data = await response.json();
    // Update range charts with daily analytics data
    updateCompletionTrendChart(data.daily_analytics);
    updateTimeDistributionChart(data.daily_analytics);
    updateRangeSummary(data.daily_analytics);
    updateRangeStatusChart(data.daily_analytics);
  } catch (error) {
    console.error("Error fetching range analytics:", error);
  }
}

// Update completion trend chart
function updateCompletionTrendChart(dailyData) {
  const labels = dailyData.map((day) => moment(day.date).format("MMM D"));
  const completionRates = dailyData.map((day) => day.completion_rate);
  if (completionTrendChart) {
    completionTrendChart.destroy();
  }
  completionTrendChart = new Chart(
    document.getElementById("completionTrendChart"),
    {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Completion Rate (%)",
            data: completionRates,
            borderColor: "rgb(59, 130, 246)",
            tension: 0.1,
            fill: true,
            backgroundColor: "rgba(59, 130, 246, 0.1)",
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "top" },
          title: { display: true, text: "Daily Completion Rate Trend" },
        },
        scales: {
          y: { beginAtZero: true, max: 100 },
        },
      },
    }
  );
}

// Update time distribution bar chart
function updateTimeDistributionChart(dailyData) {
  const labels = dailyData.map((day) => moment(day.date).format("MMM D"));
  const minutes = dailyData.map((day) => day.total_minutes);
  if (timeDistributionChart) {
    timeDistributionChart.destroy();
  }
  timeDistributionChart = new Chart(
    document.getElementById("timeDistributionChart"),
    {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Total Minutes",
            data: minutes,
            backgroundColor: "rgba(59, 130, 246, 0.5)",
            borderColor: "rgb(59, 130, 246)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "top" },
          title: { display: true, text: "Daily Time Distribution" },
        },
        scales: {
          y: { beginAtZero: true },
        },
      },
    }
  );
}

// Update Range Analytics Summary cards
function updateRangeSummary(dailyData) {
  const totalSlots = dailyData.reduce((sum, day) => sum + (day.total_slots || 0), 0);
  const completedSlots = dailyData.reduce((sum, day) => sum + (day.completed_slots || 0), 0);
  const totalMinutes = dailyData.reduce((sum, day) => sum + (day.total_minutes || 0), 0);
  const avgCompletionRate = dailyData.length > 0
    ? dailyData.reduce((sum, day) => sum + (day.completion_rate || 0), 0) / dailyData.length
    : 0;

  document.getElementById("rangeTotalSlots").textContent = totalSlots;
  document.getElementById("rangeCompletedSlots").textContent = completedSlots;
  document.getElementById("rangeTotalMinutes").textContent = totalMinutes;
  document.getElementById("rangeAvgCompletionRate").textContent = `${Math.round(avgCompletionRate)}%`;
}

// Update range status distribution doughnut chart
function updateRangeStatusChart(dailyData) {
  const completedSlots = dailyData.reduce((sum, day) => sum + (day.completed_slots || 0), 0);
  const inProgressSlots = dailyData.reduce((sum, day) => sum + (day.in_progress_slots || 0), 0);
  const notStartedSlots = dailyData.reduce((sum, day) => sum + (day.not_started_slots || 0), 0);

  const ctx = document.getElementById("rangeStatusChart").getContext("2d");
  const chartData = {
    labels: ["Completed", "In Progress", "Not Started"],
    datasets: [
      {
        data: [completedSlots, inProgressSlots, notStartedSlots],
        backgroundColor: [
          "rgba(34, 197, 94, 0.7)",
          "rgba(59, 130, 246, 0.7)",
          "rgba(239, 68, 68, 0.7)"
        ],
        borderColor: [
          "rgba(34, 197, 94, 1)",
          "rgba(59, 130, 246, 1)",
          "rgba(239, 68, 68, 1)"
        ],
        borderWidth: 1,
      }
    ]
  };
  if (window.rangeStatusChart) {
    window.rangeStatusChart.destroy();
  }
  window.rangeStatusChart = new Chart(ctx, {
    type: "doughnut",
    data: chartData,
    options: {
      responsive: true,
      plugins: {
        legend: { position: "top" },
        title: { display: true, text: "Range Slot Status Distribution" }
      }
    }
  });
}

// Initialize page
document.addEventListener("DOMContentLoaded", () => {
  fetchOverviewAnalytics();
  fetchTodayAnalytics();
  
  // Set default date range to last 7 days
  const endDate = new Date();
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - 7);
  document.getElementById("startDate").value = startDate.toISOString().split("T")[0];
  document.getElementById("endDate").value = endDate.toISOString().split("T")[0];
  fetchRangeAnalytics();
});



// verify email
// verify email
const sendOtpSection = document.getElementById('sendOtpSection');
const verifyOtpSection = document.getElementById('verifyOtpSection');
const sendOtpBtn = document.getElementById('sendOtpBtn');
const resendOtpBtn = document.getElementById('resendOtpBtn');
const verifyOtpForm = document.getElementById('verifyOtpForm');
const errorMessage = document.getElementById('errorMessage');

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('d-none');
    setTimeout(() => {
        errorMessage.classList.add('d-none');
    }, 5000);
}

async function sendVerificationEmail() {
    this.classList.add('loading');

    try {
        const response = await fetch('/api/auth/send-verification?email=' + encodeURIComponent(email), {
            method: 'POST'
        });

        if (response.ok) {
            sendOtpSection.classList.add('d-none');
            verifyOtpSection.classList.remove('d-none');
        } else {
            const error = await response.json();
            if (response.status === 429) {
                showError('Too many attempts. Please try again in an hour.');
            } else {
                showError(error.detail || 'Failed to send verification email');
            }
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to send verification email');
    } finally {
        this.classList.remove('loading');
    }
}

sendOtpBtn.addEventListener('click', sendVerificationEmail);
resendOtpBtn.addEventListener('click', sendVerificationEmail);

verifyOtpForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const otp = document.getElementById('otp').value;

    e.target.querySelector('button[type="submit"]').classList.add('loading');

    const formData = new FormData();
    formData.append('email', email);
    formData.append('otp', otp);

    try {
        const response = await fetch('/api/auth/verify-otp', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            window.location.href = '/dashboard';
        } else {
            const error = await response.json();
            showError(error.detail || 'Invalid or expired verification code');
        }
    } catch (error) {
        console.error('Error:', error);
        showError('Failed to verify code');
    } finally {
        e.target.querySelector('button[type="submit"]').classList.remove('loading');
    }
});
