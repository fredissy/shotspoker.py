let myChart = null;
let currentQueue = [];

// --- Main Game Actions ---
function startVote() {
    const ticket = document.getElementById('jiraTicket').value;
    const isPublic = document.getElementById('publicVote').checked;
    if(!ticket) return alert("Please enter a Jira Ticket ID");
    
    socket.emit('start_vote', { 
        room_id: currentRoomId, 
        ticket_key: ticket, 
        is_public: isPublic 
    });
}

function castVote(value) {
    socket.emit('cast_vote', { 
        room_id: currentRoomId,
        vote_value: value 
    });
    
    // NEW: Visual Logic (Highlight selected, deselect others)
    const cards = document.querySelectorAll('.card-select');
    cards.forEach(card => {
        // Clear previous selection
        card.classList.remove('card-selected');
        
        // Apply selection to the clicked card
        // (We compare the card's text "1", "2" etc with the vote value)
        if (card.innerText.trim() == value) {
            card.classList.add('card-selected');
        }
    });
}

function revealVote() {
    socket.emit('reveal_vote', { room_id: currentRoomId });
}

function resetVote() {
    socket.emit('reset', { room_id: currentRoomId });
    document.getElementById('jiraTicket').value = '';
    document.getElementById('statusMessage').innerText = '';
}

function copyRoomId() {
    navigator.clipboard.writeText(currentRoomId);
    alert("Room ID copied to clipboard!");
}

// --- Main UI Update Logic ---
function updateUI(state) {
    // 1. Header Info
    document.getElementById('currentTicketDisplay').innerText = 
        state.active ? `Voting on: ${state.ticket_key}` : "Waiting for session...";
    
    // 2. Voting Interface Visibility
    const votingInterface = document.getElementById('votingInterface');
    const observerMessage = document.getElementById('observerMessage');

    if (state.active && !state.revealed) {
        if (myRole === 'voter') {
            votingInterface.style.display = 'flex';
            observerMessage.style.display = 'none';
        } else {
            votingInterface.style.display = 'none';
            observerMessage.style.display = 'block';
        }
    } else {
        votingInterface.style.display = 'none';
        observerMessage.style.display = 'none';

        document.querySelectorAll('.card-select').forEach(c => c.classList.remove('card-selected'));
    }

    // 3. Admin Buttons (Security Check)
    const revealBtn = document.querySelector('button[onclick="revealVote()"]');
    const resetBtn = document.querySelector('button[onclick="resetVote()"]');
    const amIAdmin = (socket.id === state.admin_sid);
    
if (state.active) {
        // CHANGED: Anyone can reveal, but Reset might still be restricted to Admin
        revealBtn.disabled = false; 
        revealBtn.title = "Reveal results";

        resetBtn.disabled = !amIAdmin;
        resetBtn.title = amIAdmin ? "" : "Only the starter can reset";
        
    } else {
        revealBtn.disabled = true; 
        resetBtn.disabled = false; // Anyone can start a new vote/reset when inactive
    }

    // 4. Participants List
    const list = document.getElementById('votersList');
    list.innerHTML = '';
    const participants = state.participants || [];
    
    participants.forEach(p => {
        const li = document.createElement('li');
        li.className = "list-group-item d-flex justify-content-between align-items-center";
        
        let badgeClass = 'bg-secondary';
        let badgeContent = p.display_value || 'Waiting';

        if (p.role === 'observer') {
            badgeClass = 'bg-info text-dark';
            badgeContent = '👀'; 
        } else if (p.display_value === '✅') {
            badgeClass = 'bg-success'; 
        } else if (p.is_min) {
            badgeClass = 'bg-primary'; 
        } else if (p.is_max) {
            badgeClass = 'bg-danger'; 
        } else if (p.display_value !== null) {
            badgeClass = 'bg-dark';
        }

        li.innerHTML = `
            <span>
                ${p.name} 
                ${p.role === 'observer' ? '<small class="text-muted ms-1">(Observer)</small>' : ''}
            </span>
            <span class="badge ${badgeClass} rounded-pill">
                ${badgeContent}
            </span>
        `;
        list.appendChild(li);
    });

    // 5. Chart Logic
    const chartContainer = document.getElementById('chartContainer');
    const placeholder = document.getElementById('chartPlaceholder');
    
    if (state.revealed && Object.keys(state.distribution).length > 0) {
        placeholder.style.display = 'none';
        renderChart(state.distribution);
    } else {
        if(myChart) myChart.destroy();
        placeholder.style.display = 'block';
    }

    // 6. Update Queue Display
    const queueSection = document.getElementById('queueSection');
    const queueList = document.getElementById('queueList');
    const manageBtn = document.querySelector('button[onclick="openQueueModal()"]');

    currentQueue = state.queue || [];

    // Only Admin can see the "Manage Queue" button
    manageBtn.style.display ='inline-block'

    if (state.queue && state.queue.length > 0) {
        queueSection.style.display = 'block';
        queueList.innerHTML = '';
        
        state.queue.forEach(ticket => {
            // Create a clickable badge/chip
            const btn = document.createElement('button');
            btn.className = "btn btn-sm btn-white border shadow-sm text-primary fw-bold";
            btn.innerText = ticket;
            
            // Only admin can click to start
            if (socket.id === state.admin_sid) {
                btn.onclick = () => startFromQueue(ticket);
                btn.title = "Click to start voting on this ticket";
            } else {
                btn.disabled = true;
                btn.className += " opacity-75"; // visually indicate read-only
            }
            
            queueList.appendChild(btn);
        });
    } else {
        queueSection.style.display = 'none';
    }
}

function renderChart(distribution) {
    const ctx = document.getElementById('resultsChart').getContext('2d');
    const labels = Object.keys(distribution).map(k => `Vote ${k}`);
    const data = Object.values(distribution);

    if (myChart) myChart.destroy();

    myChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                label: 'Votes',
                data: data,
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'
                ]
            }]
        }
    });
}

function openQueueModal() {
    const textValue = currentQueue.join('\n');
    document.getElementById('queueInput').value = textValue;

    const modal = new bootstrap.Modal(document.getElementById('queueModal'));
    modal.show();
}

function saveQueue() {
    const rawText = document.getElementById('queueInput').value;
    if(!rawText) return;

    const list = rawText.split(/[\n,]+/).map(t => t.trim()).filter(t => t.length > 0);
    
    socket.emit('update_queue', { 
        room_id: currentRoomId, 
        queue_list: list 
    });
    
    // Hide modal manually or find the instance
    const el = document.getElementById('queueModal');
    const modal = bootstrap.Modal.getInstance(el);
    modal.hide();
}

function startFromQueue(ticketKey) {
    // Fill the input and start
    document.getElementById('jiraTicket').value = ticketKey;
    startVote();
}
