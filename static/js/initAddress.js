
// Create variable for autocomplete data
let autocompletes = new Map();

async function initAddress() {
    // Request needed libraries.
    //@ts-ignore
    await google.maps.importLibrary("places");

    document.querySelectorAll('.address').forEach(function(input) {
        let options = {
            componentRestrictions: {
                country: ['us']
            },
            fields: ['address_components'],
            types: ['address'],
        };
        let autocomplete = new google.maps.places.Autocomplete(input, options);
        autocompletes.set(input, autocomplete);
    });
}
