// intialize geocoder and map
let coordinates = [];
let geocoder;
let map;
let pinData = [];

// Load the map centered on user's state
async function initMap() {
    const {Geocoder} = await google.maps.importLibrary("geocoding");
    geocoder = new google.maps.Geocoder();
    const {
        AdvancedMarkerElement,
        PinElement
    } = await google.maps.importLibrary("marker");
    const {
        Map
    } = await google.maps.importLibrary("maps");
    const state = await getUserState();
    const location = await geocodeState(state);
    const map = new Map(document.getElementById("evac_map"), {
        zoom: 7,
        center: location,
        mapId: "EvacMap",
    });

    // Here's the search box
    initSearch();

    // Load saved pins
    loadSaved(map);

    // Add click event listener and capture all added markers
    addPin(map);
}


// Add address autocomplete
async function initSearch() {
    await google.maps.importLibrary("places");
    const input = document.getElementById('address-search');
    const autocomplete = new google.maps.places.Autocomplete(input);

    autocomplete.addListener('place_changed', () => {
        const place = autocomplete.getPlace();
        if (!place.geometry) {
            window.alert("No map details available.");
            return;
        }
        const location = place.geometry.location;
        map.setCenter(location);
        if (place.types.includes('street_address') || place.types.includes('premise')) {
            map.setZoom(18);
        } else if (place.types.includes('locality')) {
            map.setZoom(12);
        } else {
            map.setZoom(12);
        }
    });
}



// Add listener to save button to trigger saving coordinates to database
document.addEventListener('DOMContentLoaded', (event) => {
    document.querySelector('#save').addEventListener('click', function() {
        event.preventDefault();
        fetch('/save_coords', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(coordinates)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Locations saved successfully!')
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
    });
});

// Create function to update html table of user's meetup locations
function updateTable() {
    let table = document.getElementById('address-table');
    table.innerHTML = '';
    if (pinData.length > 0) {
        pinData.forEach((data, index) => {
            let row = table.insertRow();
            let cell1 = row.insertCell(0);
            let cell2 = row.insertCell(1);
            let cell3 = row.insertCell(2);
            cell1.innerText = index + 1;
            cell2.innerText = data[3];
            cell3.innerText = data[2];
        });
    }
}

// Function to add pins from saved coordinates in db
function loadSaved(map) {
    for (let pin of pins) {
        let latitude = pin.latitude
        let longitude = pin.longitude
        let title = pin.title;

        // Add each pin's readable location to table
        geocodeLocs(latitude, longitude, title)


        // Put pins on the map
        const marker = new google.maps.marker.AdvancedMarkerElement({
            position: {
                lat: latitude,
                lng: longitude
            },
            map: map,
            title: title,
            gmpDraggable: true,
        });

        // Add listener for contextmenu in order to delete pins
        deletePin(marker);

        // Add coordinates to coordinates variable so that they aren't deleted fromd db accidentally
        coordinates.push([latitude, longitude, title]);

        // Listen for coordinates of new pin location if dragged
        dragPin(marker);

        // Add event listener for double click so user can change title
        retitle(marker);
    }
}


// Function to add new pin when user clicks
function addPin(map) {
    map.addListener('click', (event) => {
        const marker = new google.maps.marker.AdvancedMarkerElement({
            position: event.latLng,
            map: map,
            gmpDraggable: true,
        });

        // Capture coordinates
        let latitude = event.latLng.lat();
        let longitude = event.latLng.lng();
        let title = "";
        coordinates.push([latitude, longitude]);
        geocodeLocs(latitude, longitude, title);

        // Add listener to allow user to delete pins
        deletePin(marker);

        // Capture location of dragged pins
        dragPin(marker);

        // Add event listener for double click so user can change title
        retitle(marker);
    });
}

// Function to pull street addresses from pins
function geocodeLocs(latitude, longitude, title) {
    geocoder.geocode({
        location: {
            lat: latitude,
            lng: longitude
        }
    }, (results, status) => {
        if (status === 'OK') {
            if (results[0]) {
                let street_number = '';
                let street = '';
                let city = '';
                let state = '';
                let country = '';
                results[0].address_components.forEach(component => {
                    if (component.types.includes('street_number')) {
                        street_number = component.long_name;
                    }
                    if (component.types.includes('route')) {
                        street = component.long_name;
                    }
                    if (component.types.includes('locality')) {
                        city = component.long_name;
                    }
                    if (component.types.includes('administrative_area_level_1')) {
                        state = component.long_name;
                    }
                    if (component.types.includes('country')) {
                        country = component.long_name;
                    }
                });
                let address = '';
                if (street_number) address += street_number;
                if (street) address += (address ? ' ' : '') + street;
                if (city) address += (address ? ', ' : '') + city;
                if (state) address += (address ? ', ' : '') + country;
                let pinIndex = pinData.findIndex(pin => pin[2] === address);
                if (pinIndex !== -1) {
                    pinData[pinIndex][2] = address;
                } else {
                    pinData.push([latitude, longitude, address, title]);
                }
                updateTable();
            } else {
                console.log('No results found');
            }
        } else {
            console.log('Geocoder failed due to: ' + status);
        }
    });
}

// Function to enable retitling of pins
function retitle(marker) {
    marker.addEventListener('dblclick', () => {
        let latitude = marker.position.Fg;
        let longitude = marker.position.Gg;
        let pinIndex = pinData.findIndex(pin => pin[3] === marker.title);
        let newTitle = prompt("Enter a name for your meet-up location:");
        if (newTitle && (typeof newTitle === "string")) {
            pinData[pinIndex][3] = newTitle;
            updateTable();

            marker.title = newTitle;
            let index = coordinates.findIndex(coord => coord[0] === latitude && coord[1] === longitude);
            if (index !== -1) {
                coordinates[index][2] = newTitle;
            };
        }
    });
}


// Function to add dragging functionality to pins and save new location
function dragPin(marker) {
    marker.addListener('dragstart', () => {
        const position = marker.position;
        let latitude = position.lat;
        let longitude = position.lng;
        let pinIndex = pinData.findIndex(pin => pin[0] === latitude && pin[1] === longitude);
        if (pinIndex !== -1) {
            pinData.splice(pinIndex, 1);
        }
        coordinates = coordinates.filter(coord => coord[0] !== latitude && coord[1] !== longitude);
    })
    marker.addListener('dragend', () => {
        const position = marker.position;
        const title = marker.title;
        let latitude = position.lat;
        let longitude = position.lng;
        coordinates.push([latitude, longitude, title]);
        geocodeLocs(latitude, longitude, title);
    });
}

// Function to delete pin from db and map when user right-clicks
function deletePin(marker) {
    marker.addEventListener('contextmenu', () => {
        const position = marker.position;
        let latitude = position.lat;
        let longitude = position.lng;
        let pinIndex = pinData.findIndex(pin => pin[0] === latitude && pin[1] === longitude);
        if (pinIndex !== -1) {
            pinData.splice(pinIndex, 1);
        }
        coordinates = coordinates.filter(coord => coord[0] !== latitude && coord[1] !== longitude);
        updateTable();
        marker.setMap(null);
    });
}


// Get the user's state
async function getUserState() {
    const response = await fetch('/user_state');
    const data = await response.json();
    return data.state;
}

// Get coordinates for user's state
async function geocodeState(state) {
    return new Promise((resolve, reject) => {
        geocoder.geocode({
            address: state
        }, (results, status) => {
            if (status === 'OK') {
                resolve(results[0].geometry.location);
            } else {
                reject('Geocode was not successful for the following reason: ' + status);
            }
        });
    });
}
