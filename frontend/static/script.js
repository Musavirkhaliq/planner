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
    const chartCanvas = document.getElementById("productivityChart");
    if (chartCanvas) {
        const response = await fetchWithAuth("/analytics/");
        if (response.ok) {
            const analytics = await response.json();
            // Using Chart.js (make sure to include its script in your HTML)
            new Chart(chartCanvas, {
                type: 'bar',
                data: {
                    labels: ['Total Tasks', 'Completed Tasks', 'Time Spent (hrs)'],
                    datasets: [{
                        label: 'Productivity Analytics',
                        data: [analytics.total_tasks, analytics.completed_tasks, analytics.total_time_spent],
                        backgroundColor: ['#007BFF', '#28a745', '#ffc107']
                    }]
                }
            });
        }
    }
});

// ---------- POMODORO TIMER -----------
let workTime = 25 * 60; // default 25 minutes (can be made configurable)
let breakTime = 5 * 60; // default 5 minutes break
let isWorking = true;

function startTimer(duration, display) {
    let timer = duration, minutes, seconds;
    const interval = setInterval(function () {
        minutes = parseInt(timer / 60, 10);
        seconds = parseInt(timer % 60, 10);
        display.textContent = (minutes < 10 ? "0" + minutes : minutes) + ":" + (seconds < 10 ? "0" + seconds : seconds);
        if (--timer < 0) {
            isWorking = !isWorking;
            timer = isWorking ? workTime : breakTime;
            alert(isWorking ? "Time to work!" : "Time for a break!");
        }
    }, 1000);
}

window.onload = function () {
    const display = document.querySelector('#time');
    if (display) {
        startTimer(workTime, display);
    }
};
// frontend/static/script.js

document.addEventListener("DOMContentLoaded", () => {
    initAuth();
    initTimeSlotForm();
    initBookingDatePicker();
    // Initially load bookings for today
    const today = new Date().toISOString().split("T")[0];
    document.getElementById("bookingDate").value = today;
    loadTimeSlotsByDate(today);
    // ... (other initializations, e.g., goals, pomodoro, analytics)
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
        loadTimeSlotsByDate(e.target.value);
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
  
  // Load time slots for the selected date.
  async function loadTimeSlotsByDate(date) {
    const token = localStorage.getItem("access_token");
    // Assuming the API supports filtering by date: /time_slots/?date=YYYY-MM-DD
    const response = await fetch(`/time_slots/?date=${date}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (response.ok) {
      const slots = await response.json();
      renderTimeSlotTable(slots);
    } else {
      alert("Failed to load time slots");
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
  
  // Update a single field (for example, the "done" status) of a booking.
  async function updateTimeSlotField(slotId, updatePayload) {
    const token = localStorage.getItem("access_token");
    const response = await fetch(`/time_slots/${slotId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(updatePayload),
    });
    if (!response.ok) {
      alert("Failed to update time slot");
    }
  }
  