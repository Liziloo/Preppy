document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function(event) {
            const supplyUuid = this.dataset.supplyUuid;

            deleteSupply(supplyUuid, event);
        });
    });
});



function deleteSupply(supplyUuid, event) {
    event.preventDefault();

    const sourcePage = 'gobag.html';

    if (!confirm('Are you sure you want to delete this item?')) {
        return;
    }

    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    fetch('/delete_supply', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            supply_uuid: supplyUuid,
            source: sourcePage
        }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = '/gobag';
            }
        });
}
