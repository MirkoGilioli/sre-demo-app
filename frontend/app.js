let backendUrl = localStorage.getItem('backend_url');

// If on localhost and no URL is saved, default to the local backend port
if (!backendUrl && window.location.hostname === 'localhost') {
    backendUrl = 'http://localhost:8081/';
} else {
    backendUrl = backendUrl || "";
}

const statusEl = document.getElementById('status');
const backendUrlInput = document.getElementById('backend-url');
backendUrlInput.value = backendUrl;

function saveConfig() {
    let url = backendUrlInput.value.trim();
    if (!url) {
        statusEl.textContent = "Error: Backend URL cannot be empty.";
        statusEl.className = "mt-2 text-sm text-red-500";
        return;
    }

    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'http://' + url;
    }

    if (!url.endsWith('/')) {
        url += '/';
    }

    backendUrl = url;
    backendUrlInput.value = url;
    localStorage.setItem('backend_url', url);
    statusEl.textContent = "Backend URL saved: " + url;
    statusEl.className = "mt-2 text-sm text-green-600";
    console.log("Configuration updated. New Backend URL:", backendUrl);
    loadEvents();
}

async function loadEvents() {
    if (!backendUrl) {
        statusEl.textContent = "Please set the Backend URL (e.g., http://localhost:8081/).";
        statusEl.className = "mt-2 text-sm text-red-500";
        return;
    }

    console.log("Fetching events from:", backendUrl + 'api/events');
    const listEl = document.getElementById('event-list');
    listEl.innerHTML = '<p class="text-gray-500 italic">Loading events...</p>';

    try {
        const response = await fetch(backendUrl + 'api/events');
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.error || `HTTP error! status: ${response.status}`);
        }
        
        const events = await response.json();
        console.log("Events loaded:", events.length);
        listEl.innerHTML = "";
        
        if (events.length === 0) {
            listEl.innerHTML = '<p class="text-gray-500 italic text-center">No events scheduled. Enjoy your day!</p>';
        }

        events.sort((a,b) => (b.timestamp?.seconds || 0) - (a.timestamp?.seconds || 0));

        events.forEach(event => {
            const div = document.createElement('div');
            div.className = "p-4 border-l-4 border-blue-500 bg-gray-50 rounded shadow-sm flex justify-between items-center";
            div.innerHTML = `
                <div>
                    <h3 class="font-bold text-gray-800">${event.title}</h3>
                    <p class="text-sm text-gray-600">${event.description || ''}</p>
                </div>
                <button onclick="deleteEvent('${event.id}')" class="text-red-500 hover:text-red-700 font-bold p-2">Delete</button>
            `;
            listEl.appendChild(div);
        });
    } catch (error) {
        console.error("Load failed:", error);
        listEl.innerHTML = `<p class="text-red-500 italic">Error loading events: ${error.message}</p>`;
    }
}

async function handleAddEvent() {
    const titleInput = document.getElementById('event-title');
    const descInput = document.getElementById('event-desc');
    const title = titleInput.value.trim();
    const description = descInput.value.trim();

    if (!title) return alert("Title is required");

    console.log("Creating event:", { title, description });

    try {
        const response = await fetch(backendUrl + 'api/events', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description })
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log("Event created successfully:", result);
            titleInput.value = "";
            descInput.value = "";
            loadEvents();
        } else {
            const err = await response.json().catch(() => ({ error: "Internal Server Error" }));
            console.error("Create failed:", err);
            alert("Error creating event: " + (err.error || "Unknown error"));
        }
    } catch (error) {
        console.error("Network error during creation:", error);
        alert("Network error: " + error.message);
    }
}

async function deleteEvent(id) {
    if (!confirm("Are you sure?")) return;
    try {
        const response = await fetch(backendUrl + `api/events/${id}`, { method: 'DELETE' });
        if (response.ok) {
            loadEvents();
        } else {
            alert("Delete failed");
        }
    } catch (error) {
        alert("Network error: " + error.message);
    }
}

// --- Chaos Management ---

async function injectLatency() {
    try {
        const response = await fetch(backendUrl + 'api/chaos/latency?ms=2000', { method: 'POST' });
        const data = await response.json();
        alert(data.status);
    } catch (error) { alert("Failed to trigger chaos: " + error.message); }
}

async function injectErrors() {
    try {
        const response = await fetch(backendUrl + 'api/chaos/error?rate=0.5', { method: 'POST' });
        const data = await response.json();
        alert(data.status);
    } catch (error) { alert("Failed to trigger chaos: " + error.message); }
}

async function resetChaos() {
    try {
        const response = await fetch(backendUrl + 'api/chaos/reset', { method: 'POST' });
        const data = await response.json();
        alert(data.status);
    } catch (error) { alert("Failed to reset chaos: " + error.message); }
}

// Init
if (backendUrl) {
    loadEvents();
}
