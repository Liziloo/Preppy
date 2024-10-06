document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function() {
            const taskUuid = this.dataset.taskUuid;

            deleteTask(taskUuid);
        });
    });

    document.querySelector('.btn-print').addEventListener('click', function() {
        window.print();
    });
});



function deleteTask(taskUuid) {
    if (!confirm('Are you sure you want to delete this item?')) {
        return;
    }
    event.preventDefault();

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    fetch('/delete_task', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            task_uuid: taskUuid
        }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = '/customtasks';
            }
        });
}
