// Initialize the map
var map = L.map('map').setView([4.8156, 7.0498], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap'
}).addTo(map);

var routeLayer = L.layerGroup().addTo(map);

let currentSearchOrigin = null;
let currentSearchDest = null;
let currentSearchMode = null;

document.addEventListener('DOMContentLoaded', function() {

    // 1. Fetch landmarks to populate dropdowns
    console.log("Attempting to fetch landmarks from API...");
    fetch('/api/landmarks')
        .then(response => {
            if (!response.ok) throw new Error("API Route failed with status: " + response.status);
            return response.json();
        })
        .then(data => {
            console.log("Landmarks retrieved successfully:", data);
            const originSelect = document.getElementById('origin');
            const destSelect = document.getElementById('destination');

            originSelect.innerHTML = '<option value="">Select starting point...</option>';
            destSelect.innerHTML = '<option value="">Select destination...</option>';

            data.forEach(landmark => {
                const optionHTML = `<option value="${landmark.id}">${landmark.landmark_name}</option>`;
                originSelect.insertAdjacentHTML('beforeend', optionHTML);
                destSelect.insertAdjacentHTML('beforeend', optionHTML);
            });
        })
        .catch(error => {
            console.error('CRITICAL ERROR fetching landmarks:', error);
            alert("Failed to load landmarks. Please check the console for details.");
        });

    // 2. Fetch and display saved routes on page load
    fetchSavedRoutes();

    // 3. Handle Form Submission
    document.getElementById('routingForm').addEventListener('submit', function(e) {
        e.preventDefault();

        const originId = document.getElementById('origin').value;
        const destId = document.getElementById('destination').value;
        const mode = document.querySelector('input[name="mode"]:checked').value;

        if (!originId || !destId) {
            alert("Please select both an Origin and a Destination.");
            return;
        }
        if (originId === destId) {
            alert("Origin and Destination cannot be the same.");
            return;
        }

        currentSearchOrigin = originId;
        currentSearchDest = destId;
        currentSearchMode = mode;

        const payload = { origin: originId, destination: destId, mode: mode };

        const submitBtn = e.target.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerText;
        submitBtn.innerText = "Calculating Route...";
        submitBtn.disabled = true;

        fetch('/api/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) throw new Error("No valid route found or server error.");
            return response.json();
        })
        .then(data => {
            displayResults(data);
            drawRouteOnMap(data.route);
        })
        .catch(error => {
            alert(error.message);
        })
        .finally(() => {
            submitBtn.innerText = originalBtnText;
            submitBtn.disabled = false;
        });
    });

    // 4. Handle saving a route
    document.getElementById('saveRouteBtn').addEventListener('click', function() {
        if (!currentSearchOrigin || !currentSearchDest || !currentSearchMode) return;

        fetch('/api/save_route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                origin: currentSearchOrigin,
                destination: currentSearchDest,
                mode: currentSearchMode
            })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            fetchSavedRoutes(); // Refresh the saved routes list
        })
        .catch(error => console.error('Error saving route:', error));
    });
});

// --- UI AND VISUALIZATION LOGIC ---
function displayResults(data) {
    document.getElementById('resultsContainer').classList.remove('hidden');
    document.getElementById('displayCost').innerText = data.total_cost;
    document.getElementById('displayTime').innerText = data.total_time;

    const instructionsList = document.getElementById('instructionsList');
    instructionsList.innerHTML = '';

    data.route.forEach((leg, index) => {
        const li = document.createElement('li');
        li.className = "flex items-start";

        // 1. Safely grab the mode and standardize it to lowercase
        // We add fallbacks just in case the backend key changed or returned null
        const rawMode = leg.transport_mode || leg.vehicle || leg.mode || 'Taxi'; 
        const mode = rawMode.toString().toLowerCase().trim();

        // 2. Cleanly assign colors based on the standardized string
        let modeColor = 'bg-gray-100 text-gray-800'; // Default gray for unknowns
        
        if (mode === 'bus') {
            modeColor = 'bg-blue-100 text-blue-800';
        } else if (mode === 'keke') {
            modeColor = 'bg-yellow-100 text-yellow-800';
        } else if (mode === 'taxi') {
            modeColor = 'bg-red-100 text-red-800'; 
        }

        // 3. Capitalize the first letter for a clean UI display
        const displayMode = mode.charAt(0).toUpperCase() + mode.slice(1);

        li.innerHTML = `
            <span class="flex-shrink-0 h-6 w-6 flex items-center justify-center rounded-full bg-blue-600 text-white text-xs font-bold mr-3 mt-0.5">${index + 1}</span>
            <div>
                Board a <span class="px-2 py-0.5 rounded text-xs font-bold ${modeColor}">${displayMode}</span>
                at <strong>${leg.start_name}</strong> to <strong>${leg.end_name}</strong>.
                <p class="text-xs text-gray-500 mt-1">Cost: ₦${leg.cost} | Time: ${leg.travel_time} mins</p>
            </div>
        `;
        instructionsList.appendChild(li);
    });
}


function drawRouteOnMap(routeLegs) {
    routeLayer.clearLayers();

    let pathCoordinates = [];

    routeLegs.forEach((leg, index) => {
        const startLatLng = [leg.start_lat, leg.start_lng];
        const endLatLng   = [leg.end_lat,   leg.end_lng];

        L.marker(startLatLng).addTo(routeLayer)
            .bindPopup(`<b>${leg.start_name}</b>`);

        if (index === routeLegs.length - 1) {
            L.marker(endLatLng).addTo(routeLayer)
                .bindPopup(`<b>${leg.end_name}</b> (Destination)`);
        }

        pathCoordinates.push(startLatLng);
        if (index === routeLegs.length - 1) {
            pathCoordinates.push(endLatLng);
        }
    });

    var polyline = L.polyline(pathCoordinates, {
        color: '#2563eb',
        weight: 5,
        opacity: 0.8,
        dashArray: '10, 10'
    }).addTo(routeLayer);

    map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
}

// FIX: fetchSavedRoutes no longer touches noSavedRoutesMsg as a child
// of savedRoutesContainer — it's now a sibling in the HTML, so clearing
// innerHTML on the container won't destroy it.
function fetchSavedRoutes() {
    console.log("Attempting to fetch saved routes...");

    fetch('/api/saved_routes')
    .then(response => {
        if (!response.ok) throw new Error("HTTP error " + response.status);
        return response.json();
    })
    .then(data => {
        console.log("Backend response payload:", data);

        const container = document.getElementById('savedRoutesContainer');
        const emptyMsg  = document.getElementById('noSavedRoutesMsg');

        if (!container) return;

        // Clear only the chips, not the sibling empty message
        container.innerHTML = '';

        if (data.error) {
            console.error("Server returned an error:", data.error);
            if (emptyMsg) emptyMsg.style.display = 'block';
            return;
        }

        if (!Array.isArray(data) || data.length === 0) {
            if (emptyMsg) emptyMsg.style.display = 'block';
            return;
        }

        // We have routes — hide the empty message
        if (emptyMsg) emptyMsg.style.display = 'none';

        data.forEach(route => {
            const chip = document.createElement('button');

            // Use themed badge colours that match economic / express pills
            const badgeClass = route.optimization_mode === 'economic'
                ? 'bg-green-100 text-green-800'
                : 'bg-orange-100 text-orange-800';

            // Use .saved-chip (CSS-var-aware) instead of raw Tailwind bg colours
            chip.className = "saved-chip flex flex-col items-start rounded-xl p-3 anim-in";
            chip.innerHTML = `
                <span class="text-sm font-semibold txt-primary">${route.origin_name} &rarr; ${route.destination_name}</span>
                <span class="text-xs font-bold px-2 py-0.5 mt-1.5 rounded-full ${badgeClass} capitalize">${route.optimization_mode} Mode</span>
            `;

            chip.addEventListener('click', () => {
                document.getElementById('origin').value      = route.origin_id;
                document.getElementById('destination').value = route.destination_id;

                // Select the matching radio button
                const radio = document.querySelector(`input[name="mode"][value="${route.optimization_mode}"]`);
                if (radio) {
                    radio.checked = true;
                    // Also update the pill highlight
                    document.getElementById('pill-economic').classList.remove('sel-economic');
                    document.getElementById('pill-express').classList.remove('sel-express');
                    document.getElementById('pill-' + route.optimization_mode)
                            .classList.add(route.optimization_mode === 'economic' ? 'sel-economic' : 'sel-express');
                }

                // Trigger the search
                document.getElementById('routingForm')
                        .dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));

                window.scrollTo({ top: 0, behavior: 'smooth' });
            });

            container.appendChild(chip);
        });
    })
    .catch(error => console.error('Network or Parsing Error fetching saved routes:', error));
}