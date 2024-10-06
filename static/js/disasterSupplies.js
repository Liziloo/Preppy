window.onload = function() {
    // Listen for when a disaster is toggled and toggle needed supplies
        document.querySelectorAll('.disaster').forEach(function(input) {
            input.addEventListener('change', function() {
                var data_supplies = input.dataset.supplies;
                supplies = data_supplies.split(', ');
                if (input.checked) {
                    document.querySelectorAll('.supply').forEach(function(checkbox) {
                        if (supplies.includes(checkbox.id)) {
                            checkbox.checked = input.checked;
                        };
                    });
                }
            // If an input is untoggled, check against other toggled inputs before untoggling supply
                else if (!input.checked) {
                    let other_supplies = "";
                    document.querySelectorAll('.disaster').forEach(function(input) {
                        if (input.checked) {
                            other_supplies = other_supplies.concat(", ", input.dataset.supplies);
                        };
                    });
                    document.querySelectorAll('.supply').forEach(function(checkbox) {
                        otherSuppliesArray = other_supplies.split(', ');
                        if (!otherSuppliesArray.includes(checkbox.id)) {
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
