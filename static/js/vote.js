let myChart = null;
let currentQueue = [];

// --- Main Game Actions ---
function startVote() {
    const ticket = document.getElementById('jiraTicket').value;
    const isPublic = document.getElementById('publicVote').checked;
    if (!ticket) return alert("Please enter a Jira Ticket ID");

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
    navigator.clipboard.writeText(currentRoomId).then(() => {
        showToast("📋 Room ID copied to clipboard!", "success");
    }).catch(err => {
        console.error(err);
        showToast("❌ Failed to copy Room ID", "danger");
    });
}

function checkConsensus(participants) {
    // Extract just the values that are numbers (ignore ?, coffee, etc)
    const votes = participants
        .map(p => p.display_value)
        .filter(v => v !== null && !isNaN(v));

    // If we have more than 1 vote and they are all identical
    if (votes.length > 1 && votes.every(v => v === votes[0])) {
        triggerConfetti();
    }
}

function triggerConfetti() {
    // Fire a burst of confetti
    confetti({
        particleCount: 150,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#0d6efd', '#ffc107', '#198754'] // Bootstrap Blue, Yellow, Green
    });
}

function showToast(message, type = 'primary') {
    const toastEl = document.getElementById('mainToast');
    const msgEl = document.getElementById('toastMessage');

    // 1. Set the message text
    msgEl.innerText = message;

    // 2. Set the color (supports 'primary', 'success', 'danger', 'warning')
    // We reset the class list and re-add the necessary Bootstrap classes
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;

    // 3. Show the toast
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}

// --- Main UI Update Logic ---
function updateUI(state) {
    // 1. Header Info
    let headerText = state.active ? `Voting on: ${state.ticket_key}` : "Waiting for session...";
    
    // NEW: Add lock icon if the vote is private
    if (state.active && !state.is_public) {
        headerText += " 🔒";
    }

    document.getElementById('currentTicketDisplay').innerText = headerText;
    
    // Define Admin Status
    const amIAdmin = (socket.id === state.admin_sid);
    
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

    // 3. Admin Buttons
    const revealBtn = document.querySelector('button[onclick="revealVote()"]');
    const resetBtn = document.querySelector('button[onclick="resetVote()"]');
    
    if (state.active) {
        revealBtn.disabled = false; 
        revealBtn.title = "Reveal results";

        resetBtn.disabled = !amIAdmin;
        resetBtn.title = amIAdmin ? "" : "Only the starter can reset";
    } else {
        revealBtn.disabled = true; 
        resetBtn.disabled = false; 
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

        // --- VISIBILITY CHANGE START ---
        // If revealed AND votes are NOT public, hide the value for EVERYONE.
        // We only check state.is_public. We do NOT check amIAdmin.
        if (state.revealed && !state.is_public && p.role !== 'observer' && p.display_value) {
            badgeContent = "🔒"; 
            badgeClass = "bg-secondary";
        } 
        // --- VISIBILITY CHANGE END ---
        else if (p.role === 'observer') {
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

        const animationClass = state.revealed ? 'vote-reveal-container flip-in' : '';

        li.innerHTML = `
            <span>
                ${p.name} 
                ${p.role === 'observer' ? '<small class="text-muted ms-1">(Observer)</small>' : ''}
            </span>
            <span class="${animationClass}">
                <span class="badge ${badgeClass} rounded-pill">
                    ${badgeContent}
                </span>
            </span>
        `;
        list.appendChild(li);
    });

    // 5. Consensus Check
    // We allow confetti even if hidden, as the graph will show 100% consensus anyway
    if (state.revealed && !window.wasRevealed) {
        checkConsensus(state.participants);
        window.wasRevealed = true; 
    } else if (!state.revealed) {
        window.wasRevealed = false;
    }

    // 6. Chart Logic
    const chartContainer = document.getElementById('chartContainer');
    const placeholder = document.getElementById('chartPlaceholder');
    
    // --- CHART CHANGE: Always render if revealed, ignoring privacy ---
    if (state.revealed && Object.keys(state.distribution).length > 0) {
        placeholder.style.display = 'none';
        renderChart(state.distribution);
    } else {
        if(myChart) myChart.destroy();
        placeholder.style.display = 'block';
        placeholder.innerText = "Waiting for reveal...";
    }

    // 7. Queue Logic (Unchanged)
    const queueSection = document.getElementById('queueSection');
    const queueList = document.getElementById('queueList');
    const manageBtn = document.querySelector('button[onclick="openQueueModal()"]');

    currentQueue = state.queue || [];
    manageBtn.style.display = 'inline-block';

    if (state.queue && state.queue.length > 0) {
        queueSection.style.display = 'block';
        queueList.innerHTML = '';
        state.queue.forEach(ticket => {
            const btn = document.createElement('button');
            btn.className = "btn btn-sm btn-white border shadow-sm text-primary fw-bold";
            btn.innerText = ticket;
            btn.onclick = () => startFromQueue(ticket);
            btn.title = "Click to start voting on this ticket";

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
    if (!rawText) return;

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
