// Get references to the input field and result display area
const searchInput = document.getElementById("searchInput");
const searchResults = document.getElementById("searchResults");

// Function to find the closest string from the array
function findClosestString(query) {
    if (!query) {
        return "";
    }

    // Send the user's query to the server using an AJAX request
    fetch(`/search?query=${query}`)
        .then(response => response.json())
        .then(data => {
            const closestMatch = data.closestMatch;
            // Display the closest match in the result area
            searchResults.textContent = `Closest Match: ${closestMatch}`;
        })
        .catch(error => {
            console.error("Error fetching data:", error);
        });
}

// Event listener for input changes
searchInput.addEventListener("input", () => {
    const inputValue = searchInput.value;
    findClosestString(inputValue);
});
