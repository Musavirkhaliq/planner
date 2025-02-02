document.addEventListener('DOMContentLoaded', function() {
    fetch('http://localhost:8000/tasks/')
        .then(response => response.json())
        .then(data => {
            const tbody = document.querySelector('#task-table tbody');
            data.forEach(task => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${task.time_slot}</td>
                    <td><input type="checkbox" ${task.is_over ? 'checked' : ''}></td>
                    <td>${task.to_do_list}</td>
                    <td>${task.report_min}</td>
                    <td>${task.progress}</td>
                    <td>${task.rating}</td>
                `;
                tbody.appendChild(row);
            });
        });
});