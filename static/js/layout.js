// Get flashed messages and display

document.addEventListener("DOMContentLoaded", function() {
    var flashMessagesDiv = document.getElementById("flashMessages");
    var messages = JSON.parse(flashMessagesDiv.getAttribute("data-messages"));

    if (messages && messages.length > 0) {
        messages.forEach(function(message) {
            var p = document.createElement("p");
            p.textContent = message;
            flashMessagesDiv.appendChild(p);
        });
        document.getElementById("flashModal").style.display = "block";
    }

    var closeButtons = document.querySelectorAll(".btn-close");

    closeButtons.forEach(function(button) {
        button.addEventListener("click", closeModal);
    });
});

function closeModal() {
    document.getElementById("flashModal").style.display = "none";
}
