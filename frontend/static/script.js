// Login Form Submission
document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const response = await fetch("/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
    });

    if (response.ok) {
        const data = await response.json();
        localStorage.setItem("access_token", data.access_token); // Store the token
        window.location.href = "/dashboard"; // Redirect to dashboard
    } else {
        alert("Login failed");
    }
});

// Register Form Submission
document.getElementById("registerForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const response = await fetch("/users/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
    });

    if (response.ok) {
        window.location.href = "/login";
    } else {
        alert("Registration failed");
    }
});

// Dashboard: Fetch and Display Tasks
document.addEventListener("DOMContentLoaded", async () => {
    const taskList = document.getElementById("taskList");
    if (taskList) {
        const token = localStorage.getItem("access_token"); // Get the token
        if (!token) {
            window.location.href = "/login"; // Redirect to login if no token
            return;
        }

        const response = await fetch("/tasks/", {
            headers: {
                "Authorization": `Bearer ${token}` // Include the token in the request
            }
        });

        if (response.ok) {
            const tasks = await response.json();
            tasks.forEach(task => {
                const li = document.createElement("li");
                li.textContent = `${task.title}: ${task.description}`;
                taskList.appendChild(li);
            });
        } else {
            alert("Failed to fetch tasks");
        }
    }
});

// Dashboard: Add Task Form Submission
document.getElementById("taskForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("title").value;
    const description = document.getElementById("description").value;
    const token = localStorage.getItem("access_token"); // Get the token

    if (!token) {
        window.location.href = "/login"; // Redirect to login if no token
        return;
    }

    const response = await fetch("/tasks/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}` // Include the token in the request
        },
        body: JSON.stringify({ title, description, user_id: 1 }), // Replace with dynamic user ID
    });

    if (response.ok) {
        window.location.reload();
    } else {
        alert("Failed to add task");
    }
});