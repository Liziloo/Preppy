document.addEventListener('DOMContentLoaded', () => {

    document.querySelectorAll('.form-delete').forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!confirm('Are you sure you want to delete this person?')) {
                event.preventDefault();
            }
        });
    });

    document.querySelector('.btn-print').addEventListener('click', function() {
        window.print();
    });

    document.querySelectorAll('.btn-edit').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            const firstName = this.getAttribute('data-first-name');
            const lastName = this.getAttribute('data-last-name');
            const patient = this.getAttribute('data-patient');
            const phone = this.getAttribute('data-phone');
            const address = this.getAttribute('data-address');

            openEditModal(id, firstName, lastName, patient, phone, address);
        });
    });
});


function openEditModal(id, firstName, lastName, patient, phone, address) {
    document.getElementById('editPerson_id').value = id;
    document.getElementById('editFirst_name').value = firstName;
    document.getElementById('editLast_name').value = lastName;
    document.getElementById('editPatient').value = patient;
    document.getElementById('editPhone').value = phone;
    document.getElementById('editAddress').value = address;
    document.getElementById('editModal').style.display = 'block';
}
