async function fetchTopUsers(timeframe, elementId) {
    try {
        const response = await fetch(`analytics/top-users/${timeframe}`);
        const data = await response.json();
        
        const listElement = document.getElementById(elementId);
        listElement.innerHTML = ""; // Clear previous entries

        if (data.error) {
            listElement.innerHTML = `<li class="list-group-item text-danger">${data.error}</li>`;
            return;
        }

        data.forEach(user => {
            const listItem = document.createElement("li");
            listItem.classList.add("list-group-item");
            listItem.innerHTML = `<strong>${user.username}</strong>: ${user.total_time} minutes`;
            listElement.appendChild(listItem);
        });

    } catch (error) {
        console.error("Error fetching top users:", error);
    }
}

// Load the leaderboard data on page load
document.addEventListener("DOMContentLoaded", function() {
    fetchTopUsers("daily", "top-users-daily");
    fetchTopUsers("weekly", "top-users-weekly");
    fetchTopUsers("monthly", "top-users-monthly");
});
