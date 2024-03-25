document.getElementById('getLocationBtn').addEventListener('click', getUserLocation);

async function getUserLocation() {
    if (navigator.geolocation) {
        try {
            const position = await getPosition();
            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;

            console.log('Latitude:', latitude);
            console.log('Longitude:', longitude);

            // Send an asynchronous request to Flask server without expecting a JSON response
            await fetch('/get_data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ latitude, longitude }),
            });

            console.log('Location sent successfully');

            window.location.href = '/bus_info'; // Change this to the desired URL


            // You can continue with any other processing or UI updates here
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
