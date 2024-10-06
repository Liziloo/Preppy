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
            const bloodType = this.getAttribute('data-blood-type');
            const medications = this.getAttribute('data-medications');
            const allergies = this.getAttribute('data-allergies');
            const other = this.getAttribute('data-other');
            const insurance = this.getAttribute('data-insurance');
            const policy = this.getAttribute('data-policy');

            openEditModal(id, firstName, lastName, bloodType, medications, allergies, other, insurance, policy);
        });
    });
});

function openEditModal(id, firstName, lastName, bloodType, medications, allergies, other, insurance, policy) {
    document.getElementById('editPerson_id').value = id;
    document.getElementById('editFirst_name').value = firstName;
    document.getElementById('editLast_name').value = lastName;
    document.getElementById('editBlood-type').value = bloodType;
    document.getElementById('editMedications').value = medications;
    document.getElementById('editAllergies').value = allergies;
    document.getElementById('editOther').value = other;
    document.getElementById('editInsurance').value = insurance;
    document.getElementById('editPolicy').value = policy;
    document.getElementById('editModal').style.display = 'block';
}
