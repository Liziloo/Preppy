document.addEventListener('DOMContentLoaded', (event) => {

    document.querySelectorAll('.form-delete').forEach(form => {
        form.addEventListener('submit', function() {
            if (!confirm('Are you sure you want to delete this person?')) {
                event.preventDefault();
            }
        });
    });
});
