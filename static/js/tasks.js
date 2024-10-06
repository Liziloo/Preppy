window.onload = function() {
    // Listen for when a disaster is toggled and toggle associated tasks
        document.querySelectorAll('.disaster').forEach(function(input) {
            input.addEventListener('change', function() {
                var data_tasks = input.dataset.tasks;
                tasks = data_tasks.split(', ');
                if (input.checked) {
                    document.querySelectorAll('.task').forEach(function(checkbox) {
                        if (tasks.includes(checkbox.id)) {
                            checkbox.checked = input.checked;
                        };
                    });
                }
            // If an input is untoggled, check against other toggled inputs before untoggling task
                else if (!input.checked) {
                    let other_tasks = "";
                    document.querySelectorAll('.disaster').forEach(function(input) {
                        if (input.checked) {
                            other_tasks = other_tasks.concat(", ", input.dataset.tasks);
                        };
                    });
                    document.querySelectorAll('.task').forEach(function(checkbox) {
                        otherTasksArray = other_tasks.split(', ');
                        if (!otherTasksArray.includes(checkbox.id)) {
                            checkbox.checked = false;
                        }
                    })
                };
            });
        })
    // When the page loads, trigger a change for disasters that are pre-checked
        let event = new Event('change');
        document.querySelectorAll('.disaster:checked').forEach(function(checkbox) {
            checkbox.dispatchEvent(event);
        });
    };
