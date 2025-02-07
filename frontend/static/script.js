// frontend/static/script.js

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
            return await response.json();
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
    const data = await submitForm(e, "/token", { username: email, password: password }, false);
    if (data && data.access_token) {
        localStorage.setItem("access_token", data.access_token);
        window.location.href = "/dashboard";
    }
});

// Register Form Submission
document.getElementById("registerForm")?.addEventListener("submit", async (e) => {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const data = await submitForm(e, "/users/", { email, password });
    if (data) window.location.href = "/login";
});

// ---------- DASHBOARD FUNCTIONS -----------
async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/login";
        return;
    }
    options.headers = {
        ...(options.headers || {}),
        "Authorization": `Bearer ${token}`
    };
    return await fetch(url, options);
}

// Time Slot Booking
async function bookTimeSlot() {
    const task = document.getElementById("task").value;
    const startTime = document.getElementById("startTime").value;
    const endTime = document.getElementById("endTime").value;
    // Create a description from the task
    const description = task;
    const response = await fetchWithAuth("/time_slots/", {
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
  initAuth();
  initTimeSlotForm();
  initBookingDatePicker();
  // Initially load bookings for today
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("bookingDate").value = today;
  loadTimeSlotsByDate(today);
  fetchAnalytics(today, today);
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
            fetchAnalytics(selectedDate, selectedDate);
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
  
        const payload = {
          start_time: `${bookingDate}T${startTime}`,
          end_time: `${bookingDate}T${endTime}`,
          description: task,
          date: bookingDate  // assuming the API accepts a date field
        };
  
        const response = await fetch("/time_slots/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        });
  
        if (response.ok) {
          timeSlotForm.reset();
          // Reapply the selected date (if the reset clears it)
          document.getElementById("bookingDate").value = bookingDate;
          loadTimeSlotsByDate(bookingDate);
        } else {
          alert("Failed to add time slot");
        }
      });
    }
  }

  
  // Render the time slot table rows.
  function renderTimeSlotTable(slots) {
    const tableBody = document.querySelector("#timeSlotTable tbody");
    tableBody.innerHTML = "";
  
    slots.forEach((slot) => {
      // Calculate total allotted minutes from start and end times.
      const start = new Date(slot.start_time);
      const end = new Date(slot.end_time);
      const allottedMinutes = Math.round((end - start) / 60000); // convert ms to minutes
  
      // Use the stored "report" (in minutes) if available; otherwise default to 0.
      const reportedMinutes = slot.report_minutes || 0;
      const progressPercent = Math.min(
        100,
        Math.round((reportedMinutes / allottedMinutes) * 100)
      );
      const ratingStars = "★".repeat(Math.max(1, Math.round(progressPercent / 20)));
  
      const tr = document.createElement("tr");
      tr.setAttribute("data-slot-id", slot.id);
  
      // TIME (formatted as e.g., 06:00AM-07:00AM)
      const timeTd = document.createElement("td");
      timeTd.textContent = `${start.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })} - ${end.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })}`;
      tr.appendChild(timeTd);
  
      // DONE? (checkbox – optionally update on click)
      const doneTd = document.createElement("td");
      const doneCheckbox = document.createElement("input");
      doneCheckbox.type = "checkbox";
      doneCheckbox.checked = slot.done || false;
      doneCheckbox.addEventListener("change", () => {
        updateTimeSlotField(slot.id, { done: doneCheckbox.checked });
      });
      doneTd.appendChild(doneCheckbox);
      tr.appendChild(doneTd);
  
      // TO-DO LIST (Task description)
      const descTd = document.createElement("td");
      descTd.textContent = slot.description;
      tr.appendChild(descTd);
  
      // REPORT (Min) – input for minutes reported
      const reportTd = document.createElement("td");
      const reportInput = document.createElement("input");
      reportInput.type = "number";
      reportInput.min = 0;
      reportInput.value = reportedMinutes;
      reportInput.className = "form-control form-control-sm";
      reportInput.style.width = "80px";
      // Update the booking when the report input loses focus
      reportInput.addEventListener("change", () => {
        updateTimeSlotReport(slot.id, parseInt(reportInput.value), allottedMinutes);
      });
      reportTd.appendChild(reportInput);
      tr.appendChild(reportTd);
  
      // PROGRESS – a Bootstrap progress bar
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
  
      // RATING – display star icons
      const ratingTd = document.createElement("td");
      ratingTd.textContent = ratingStars;
      tr.appendChild(ratingTd);
  
      tableBody.appendChild(tr);
    });
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
    const response = await fetch(`/time_slots/${slotId}`, {
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

/**
 * Reads the user-specified times from input fields (in minutes)
 * and updates the global workTime and breakTime values (in seconds).
 */
function updateTimerDurationsFromInputs() {
  const workInput = document.getElementById("workTime");
  const breakInput = document.getElementById("breakTime");

  // Parse the input values (if provided) or use defaults.
  const workMinutes = workInput && workInput.value ? parseInt(workInput.value, 10) : 25;
  const breakMinutes = breakInput && breakInput.value ? parseInt(breakInput.value, 10) : 5;

  workTime = workMinutes * 60;
  breakTime = breakMinutes * 60;
}

/**
 * Starts the Pomodoro timer for a given session.
 * @param {number} duration - Duration of the current session in seconds.
 * @param {HTMLElement} display - Element to display the remaining time.
 * @param {HTMLElement} progressBar - Element to show progress.
 */
function startTimer(duration, display, progressBar) {
  let remainingTime = duration;
  clearInterval(timerInterval);

  timerInterval = setInterval(() => {
    // Format minutes and seconds for display.
    const minutes = Math.floor(remainingTime / 60);
    const seconds = remainingTime % 60;
    display.textContent = `${minutes < 10 ? "0" + minutes : minutes}:${seconds < 10 ? "0" + seconds : seconds}`;

    // Update progress bar based on elapsed time.
    const progress = ((duration - remainingTime) / duration) * 100;
    progressBar.style.width = `${progress}%`;

    // When the timer runs out, switch modes and restart.
    if (remainingTime <= 0) {
      clearInterval(timerInterval);
      isWorking = !isWorking;
      // Set the new session duration based on the mode.
      remainingTime = isWorking ? workTime : breakTime;
      alert(isWorking ? "Time to work!" : "Time for a break!");
      // Start the next session.
      startTimer(remainingTime, display, progressBar);
    }
    remainingTime--;
  }, 1000);
}

/**
 * Resets the Pomodoro timer display and progress.
 * Also updates the work and break durations from user inputs.
 * @param {HTMLElement} display - Timer display element.
 * @param {HTMLElement} progressBar - Progress bar element.
 */
function resetTimer(display, progressBar) {
  clearInterval(timerInterval);
  isWorking = true;
  updateTimerDurationsFromInputs();
  // Reset display to the new work time.
  const minutes = Math.floor(workTime / 60);
  const seconds = workTime % 60;
  display.textContent = `${minutes < 10 ? "0" + minutes : minutes}:${seconds < 10 ? "0" + seconds : seconds}`;
  progressBar.style.width = "0%";
}

// --------------------------
// INITIALIZATION
// --------------------------
document.addEventListener("DOMContentLoaded", () => {
  // Get references to DOM elements.
  const display = document.querySelector("#time");
  const progressBar = document.querySelector("#progress");
  const startBtn = document.getElementById("startBtn");
  const resetBtn = document.getElementById("resetBtn");

  // If user inputs exist, update durations immediately.
  updateTimerDurationsFromInputs();
  
  // Display the initial work time.
  const minutes = Math.floor(workTime / 60);
  const seconds = workTime % 60;
  if (display) {
    display.textContent = `${minutes < 10 ? "0" + minutes : minutes}:${seconds < 10 ? "0" + seconds : seconds}`;
  }

  // Start button: update times from inputs and start the timer.
  if (startBtn && display && progressBar) {
    startBtn.addEventListener("click", () => {
      updateTimerDurationsFromInputs();
      // Start with workTime if beginning a new session.
      startTimer(workTime, display, progressBar);
    });
  }

  // Reset button: clear the timer and update the display.
  if (resetBtn && display && progressBar) {
    resetBtn.addEventListener("click", () => {
      resetTimer(display, progressBar);
    });
  }
});


async function loadTimeSlotsByDate(date) {
  const token = localStorage.getItem("access_token");
  const response = await fetch(`/time_slots/by_date/?date=${date}`, {
      headers: { Authorization: `Bearer ${token}` },
  });
  if (response.ok) {
      const slots = await response.json();
      renderTimeSlotTable(slots);
  } else {
      alert("Failed to load time slots");
  }
}


async function fetchAnalytics(startDate, endDate) {
  const token = localStorage.getItem("access_token");
  const response = await fetch(`/analytics/?start=${startDate}&end=${endDate}`, {
      headers: { Authorization: `Bearer ${token}` },
  });
  if (response.ok) {
      const analytics = await response.json();
      updateAnalyticsChart(analytics);
  } else {
      alert("Failed to fetch analytics");
  }
}

function updateAnalyticsChart(analytics) {
  const chartCanvas = document.getElementById("productivityChart");
  if (chartCanvas) {
      new Chart(chartCanvas, {
          type: 'bar',
          data: {
              labels: ['Total Tasks', 'Completed Tasks', 'Time Spent (hrs)', 'Total Time Slots', 'Completed Time Slots'],
              datasets: [{
                  label: 'Productivity Analytics',
                  data: [
                      analytics.total_tasks,
                      analytics.completed_tasks,
                      analytics.total_time_spent,
                      analytics.total_time_slots,
                      analytics.completed_time_slots
                  ],
                  backgroundColor: ['#007BFF', '#28a745', '#ffc107', '#17a2b8', '#6c757d']
              }]
          }
      });
  }
}


