// frontend/app.js
// The backend URL is now handled by the Nginx Reverse Proxy.
// All API calls are now relative (e.g., /api/events).

let currentMonth = new Date().getMonth();
let currentYear = new Date().getFullYear();
let selectedDate = new Date();
selectedDate.setHours(0,0,0,0);
let allEvents = [];

function changeMonth(offset) {
    currentMonth += offset;
    if (currentMonth < 0) {
        currentMonth = 11;
        currentYear--;
    } else if (currentMonth > 11) {
        currentMonth = 0;
        currentYear++;
    }
    renderCalendar();
}

function selectDate(year, month, day) {
    selectedDate = new Date(year, month, day);
    const infoEl = document.getElementById('selected-date-info');
    if (infoEl) infoEl.textContent = `Selected: ${selectedDate.toDateString()}`;
    renderCalendar();
}

function renderCalendar() {
    const monthYearEl = document.getElementById('calendar-month-year');
    const gridEl = document.getElementById('calendar-grid');
    
    if (!monthYearEl || !gridEl) return;

    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    monthYearEl.textContent = `${monthNames[currentMonth]} ${currentYear}`;
    
    gridEl.innerHTML = "";
    
    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    
    // Empty cells for first week
    for (let i = 0; i < firstDay; i++) {
        const div = document.createElement('div');
        gridEl.appendChild(div);
    }
    
    for (let day = 1; day <= daysInMonth; day++) {
        const div = document.createElement('div');
        const isSelected = selectedDate.getFullYear() === currentYear && selectedDate.getMonth() === currentMonth && selectedDate.getDate() === day;
        
        // Check if this day has events
        const hasEvents = allEvents.some(e => {
            if (!e.timestamp || !e.timestamp.seconds) return false;
            const d = new Date(e.timestamp.seconds * 1000);
            return d.getFullYear() === currentYear && d.getMonth() === currentMonth && d.getDate() === day;
        });

        div.className = `p-2 border rounded cursor-pointer hover:bg-blue-50 transition ${isSelected ? 'bg-blue-600 text-white font-bold hover:bg-blue-700' : 'bg-white'}`;
        if (hasEvents && !isSelected) {
            div.classList.add('border-blue-500', 'border-2');
        }
        
        div.textContent = day;
        div.onclick = () => selectDate(currentYear, currentMonth, day);
        gridEl.appendChild(div);
    }
}

async function loadEvents() {
    const listEl = document.getElementById('event-list');
    if (!listEl) return;
    
    listEl.innerHTML = '<p class="text-gray-500 italic">Loading events...</p>';

    try {
        // Simple relative path for Nginx to proxy
        const response = await fetch('/api/events');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        allEvents = await response.json();
        console.log("Events loaded:", allEvents.length);
        renderCalendar(); // Update calendar markers
        
        listEl.innerHTML = "";
        
        if (allEvents.length === 0) {
            listEl.innerHTML = '<p class="text-gray-500 italic text-center">No events scheduled. Enjoy your day!</p>';
        }

        allEvents.sort((a,b) => (b.timestamp?.seconds || 0) - (a.timestamp?.seconds || 0));

        allEvents.forEach(event => {
            const dateStr = event.timestamp?.seconds ? new Date(event.timestamp.seconds * 1000).toLocaleDateString() : 'Unknown Date';
            const div = document.createElement('div');
            div.className = "p-4 border-l-4 border-blue-500 bg-gray-50 rounded shadow-sm flex justify-between items-center";
            div.innerHTML = `
                <div>
                    <h3 class="font-bold text-gray-800">${event.title} <span class="text-xs text-gray-400 font-normal ml-2">${dateStr}</span></h3>
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

    // Capture the selected date from the calendar
    const payload = {
        title,
        description,
        timestamp: selectedDate.toISOString()
    };

    console.log("Creating event:", payload);

    try {
        const response = await fetch('/api/events', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            titleInput.value = "";
            descInput.value = "";
            loadEvents();
        } else {
            const err = await response.json().catch(() => ({ error: "Internal Server Error" }));
            alert("Error: " + (err.error || "Unknown error"));
        }
    } catch (error) {
        alert("Network error: " + error.message);
    }
}

async function deleteEvent(id) {
    if (!confirm("Are you sure?")) return;
    try {
        const response = await fetch(`/api/events/${id}`, { method: 'DELETE' });
        if (response.ok) loadEvents();
    } catch (error) { alert("Network error: " + error.message); }
}

// --- Chaos Management ---
async function injectLatency() { 
    try {
        await fetch('/api/chaos/latency?ms=2000', { method: 'POST' }); 
        alert("2s Latency Injected");
    } catch(e) { alert("Failed: " + e.message); }
}
async function injectErrors() { 
    try {
        await fetch('/api/chaos/error?rate=0.5', { method: 'POST' }); 
        alert("50% Error Rate Injected");
    } catch(e) { alert("Failed: " + e.message); }
}
async function resetChaos() { 
    try {
        await fetch('/api/chaos/reset', { method: 'POST' }); 
        alert("Chaos Reset");
    } catch(e) { alert("Failed: " + e.message); }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    renderCalendar();
    loadEvents();
});
