document.addEventListener('DOMContentLoaded', function() {
    // Display the modal
    var eventModal = new bootstrap.Modal(document.getElementById('eventModal'));
    var calendarEl = document.getElementById('calendar');

    // Color events according to person
    const colorMap = {};
    events.forEach(event => {
        event.color = getPersonColor(event.person_id, colorMap);
    });

    var calendar = new FullCalendar.Calendar(calendarEl, {
        dayHeaderFormat: {
            weekday: 'short'
        },
        headerToolbar: {
            left: false,
            center: false,
            right: false,
        },
        schedulerLicenseKey: 'GPL-My-Project-Is-Open-Source',
        initialView: 'timeGridWeek',
        firstDay: 0,
        events: events,
        dateClick: function(info) {
            // Format the date
            var startDate = new Date(info.startStr);
            var endDate = new Date(info.endStr);

            var startFormatted = startDate.toISOString().split('T')[0];
            var startTime = startDate.toTimeString().split(' ')[0].substring(0, 5);
            var endFormatted = endDate.toISOString().split('T')[0];
            var endTime = endDate.toTimeString().split(' ')[0].substring(0, 5);

            // Fill in existing info
            document.getElementById('eventStartDay').value = startFormatted;
            document.getElementById('eventStartTime').value = startTime;
            document.getElementById('eventEndDay').value = endFormatted;
            document.getElementById('eventEndTime').value = endTime;
            document.getElementById('eventTitle').value = '';
            document.getElementById('eventAddress').value = '';
            document.getElementById('eventDescription').value = '';
            eventModal.show();

            eventModal.show();
        },
        select: function(info) {
            var startDate = new Date(info.startStr);
            var endDate = new Date(info.endStr);

            var startFormatted = startDate.toISOString().split('T')[0];
            var startTime = startDate.toTimeString().split(' ')[0].substring(0, 5);
            var endFormatted = endDate.toISOString().split('T')[0];
            var endTime = endDate.toTimeString().split(' ')[0].substring(0, 5);

            // Fill in existing info
            document.getElementById('eventStartDay').value = startFormatted;
            document.getElementById('eventStartTime').value = startTime;
            document.getElementById('eventEndDay').value = endFormatted;
            document.getElementById('eventEndTime').value = endTime;
            document.getElementById('eventTitle').value = '';
            document.getElementById('eventAddress').value = '';
            document.getElementById('eventDescription').value = '';
            eventModal.show();
        },

        // Allow editing events when clicked
        eventClick: function(info) {
            var startDate = new Date(info.event._instance.range.start);
            var endDate = new Date(info.event._instance.range.end);

            startDate.setHours(startDate.getHours() + 4);
            endDate.setHours(endDate.getHours() + 4);

            var startFormatted = startDate.toISOString().split('T')[0];
            var startTime = startDate.toTimeString().split(' ')[0].substring(0, 5);
            var endFormatted = endDate.toISOString().split('T')[0];
            var endTime = endDate.toTimeString().split(' ')[0].substring(0, 5);

            // Fill in existing info
            document.getElementById('eventStartDay').value = startFormatted;
            document.getElementById('eventStartTime').value = startTime;
            document.getElementById('eventEndDay').value = endFormatted;
            document.getElementById('eventEndTime').value = endTime;
            document.getElementById('eventTitle').value = info.event.title;
            document.getElementById('eventAddress').value = info.event.extendedProps.address;
            document.getElementById('eventPerson').value = info.event.extendedProps.person_id;
            document.getElementById('eventDescription').value = info.event.extendedProps.description;
            document.getElementById('eventId').value = info.event.extendedProps.eventId;
            document.getElementById('deleteEvent').value = info.event.extendedProps.eventId;
            eventModal.show();
        },

        selectable: true,
        validRange: {
            start: '2024-08-11',
            end: '2024-08-18'
        },
    });

    calendar.render();

});

// Generate colors for every person in the calendar
function getPersonColor(personId, colorMap) {
    if (!colorMap[personId]) {
        const color = generateRandomColor();
        colorMap[personId] = color;
    }
    return colorMap[personId];
}

function generateRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}
