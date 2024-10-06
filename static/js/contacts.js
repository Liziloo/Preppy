document.addEventListener('DOMContentLoaded', () => {

    document.querySelectorAll('.btn-edit').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            const firstName = this.getAttribute('data-first-name');
            const lastName = this.getAttribute('data-last-name');
            const phone = this.getAttribute('data-phone');
            const email = this.getAttribute('data-email');
            const address = this.getAttribute('data-address');

            openEditModal(id, firstName, lastName, phone, email, address);
        });
    });
});


function openEditModal(id, firstName, lastName, phone, email, address) {
    document.getElementById('editPerson_id').value = id;
    document.getElementById('editFirst_name').value = firstName;
    document.getElementById('editLast_name').value = lastName;
    document.getElementById('editPhone').value = phone;
    document.getElementById('editEmail').value = email;
    document.getElementById('editAddress').value = address;
    document.getElementById('editModal').style.display = 'block';
}

