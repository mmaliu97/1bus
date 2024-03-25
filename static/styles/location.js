document.getElementById('getLocationBtn').addEventListener('click', getUserLocation);

async function getUserLocation() {
    if (navigator.geolocation) {
        try {
            const position = await getPosition();
            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;
            console.log("hello what the fuckl")
            // Send an asynchronous request to Flask server
            const response = await fetch('/get_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json', // Change content type to JSON
                },

                
                body: JSON.stringify({ latitude, longitude }), // Send data as JSON
            });

            console.log('Server Response:', response);

            const data = await response.json();

            if (data.success) {
                console.log('Data received:', data.data);
                // You can further process the data or update the UI here
            } else {
                console.error('Error:', data.error);
            }
        } catch (error) {
            console.error('Error getting location:', error);
        }
    } else {
        alert('Geolocation is not supported by your browser.');
    }
}


function getPosition() {
    return new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject);
    });
}



// function showPosition(position) {
//     console.log('Latitude:', position.coords.latitude);
//     console.log('Longitude:', position.coords.longitude);
// }

function showError(error) {
    switch(error.code) {
        case error.PERMISSION_DENIED:
            alert('User denied the request for Geolocation.');
            break;
        case error.POSITION_UNAVAILABLE:
            alert('Location information is unavailable.');
            break;
        case error.TIMEOUT:
            alert('The request to get user location timed out.');
            break;
        case error.UNKNOWN_ERROR:
            alert('An unknown error occurred.');
            break;
    }
}
