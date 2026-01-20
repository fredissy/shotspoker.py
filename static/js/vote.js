let myChart = null;
let currentQueue = [];
let timerInterval = null;
let currentDeckRendered = false;

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

function startTimer(seconds) {
    socket.emit('start_timer', { room_id: currentRoomId, duration: seconds });
}

function stopTimer() {
    socket.emit('stop_timer', { room_id: currentRoomId });
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

    if (state.participants) {
        const me = state.participants.find(p => p.name === myName);
        if (me) {
            myRole = me.role;
            // Sync the toggle switch visually (in case change came from server)
            const switchEl = document.getElementById('roleSwitch');
            if (switchEl) switchEl.checked = (myRole === 'observer');
        }
    }

    // 1. Header Info
    let headerText = state.active ? `Voting on: ${state.ticket_key}` : "Waiting for session...";
    
    // NEW: Add lock icon if the vote is private
    if (state.active && !state.is_public) {
        headerText += " 🔒";
    }

    document.getElementById('currentTicketDisplay').innerText = headerText;
    const cardsContainer = document.getElementById('cardsContainer');
    
    // Define Admin Status
    const amIAdmin = (socket.id === state.admin_sid);


    // 1. Cards rendering :
    if (!currentDeckRendered && state.deck) {
        cardsContainer.innerHTML = ''; // Clear just in case
        
        state.deck.forEach(val => {
            // Create the card div
            const card = document.createElement('div');
            card.className = 'card p-3 card-select shadow-sm user-select-none';
            card.innerText = val;
            
            // Add click handler (Need to wrap value in quotes if string)
            card.onclick = () => castVote(val);
            
            cardsContainer.appendChild(card);
        });
        currentDeckRendered = true;
    }
    
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
    const startBtn = document.getElementById('startVoteBtn');
    
    if (state.active) {
        revealBtn.disabled = false; 
        revealBtn.title = "Reveal results";

        resetBtn.disabled = !amIAdmin;
        resetBtn.title = amIAdmin ? "" : "Only the starter can reset";
        startBtn.disabled = !state.revealed;
    } else {
        revealBtn.disabled = true; 
        resetBtn.disabled = false; 
        startBtn.disabled = false;
    }

    // 4. Participants List
    const list = document.getElementById('votersList');
    list.innerHTML = '';
    const participants = state.participants || [];
    
    participants.forEach(p => {
        const li = document.createElement('li');

        const opacity = p.status === 'offline' ? '0.5' : '1';
        li.style.opacity = opacity;

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
                <span class="fs-5 me-2" role="img">${p.avatar}</span>
                <span class="fw-bold">${p.name}</span>
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
    const statsRow = document.getElementById('statsRow');
    const statAvg = document.getElementById('statAverage');
    const statAgree = document.getElementById('statAgreement');

    if (state.stats) {
        statsRow.style.display = 'flex';
        
        // Handle Average (might be null if only '?' or 'coffee' were voted)
        statAvg.innerText = (state.stats.average !== null) ? state.stats.average : '-';
        
        // Handle Agreement
        statAgree.innerText = state.stats.agreement + '%';
    } else {
        statsRow.style.display = 'none';
    }
    
    // --- CHART CHANGE: Always render if revealed, ignoring privacy ---
    if (state.revealed && Object.keys(state.distribution).length > 0) {
        placeholder.style.display = 'none';
        renderChart(state.distribution);
    } else {
        if(myChart) myChart.destroy();
        myChart = null;
        placeholder.style.display = 'block';
        placeholder.innerText = "Waiting for reveal...";
    }

    // 7. Queue Logic (Unchanged)
    const queueSection = document.getElementById('queueSection');
    const queueList = document.getElementById('queueList');
    const manageBtn = document.querySelector('button[onclick="openQueueModal()"]');

    currentQueue = state.queue || [];
    manageBtn.style.display = 'inline-block';

    const modalList = document.getElementById('modalQueueList');
    if (modalList && document.getElementById('queueModal').classList.contains('show')) {
        renderModalQueueList(currentQueue);
    }

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

    // 8. Timer :
    const timerEl = document.getElementById('timerDisplay');
    if (timerInterval) clearInterval(timerInterval);
    if (state.timer_end) {
        timerEl.style.display = 'inline-block';
        
        // Start a local countdown loop
        timerInterval = setInterval(() => {
            // Get client's current time (in seconds, matching Python's time.time())
            const now = Date.now() / 1000; 
            const diff = state.timer_end - now;

            if (diff <= 0) {
                timerEl.innerText = "0:00";
                clearInterval(timerInterval);
                // Optional: Play a "Ding" sound here if you kept the audio file
            } else {
                // Format MM:SS
                const m = Math.floor(diff / 60);
                const s = Math.floor(diff % 60);
                timerEl.innerText = `${m}:${s.toString().padStart(2, '0')}`;
            }
        }, 100); // Update every 100ms for smoothness
    } else {
        timerEl.style.display = 'none';
        timerEl.innerText = "00:00";
    }
}


function renderChart(distribution) {
    const ctx = document.getElementById('resultsChart').getContext('2d');
    const labels = Object.keys(distribution);
    const data = Object.values(distribution);

    if (myChart) {
        // --- FIX: Update existing chart instead of destroying it ---
        myChart.data.labels = labels;
        myChart.data.datasets[0].data = data;
        
        // 'none' mode prevents the animation from re-playing, 
        // making the update instant and stable.
        myChart.update('none'); 
    } else {
        // Create it for the first time (with animation)
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
            },
            options: {
                animation: {
                    duration: 500 // Only animate on creation
                }
            }
        });
    }
}

function openQueueModal() {
    // Just render current state and show
    renderModalQueueList(currentQueue);
    
    // Clear the input
    document.getElementById('queueAddInput').value = '';
    const modal = new bootstrap.Modal(document.getElementById('queueModal'));
    modal.show();
}

function renderModalQueueList(queue) {
    const list = document.getElementById('modalQueueList');
    const emptyMsg = document.getElementById('emptyQueueMsg');
    list.innerHTML = '';
    
    if (!queue || queue.length === 0) {
        emptyMsg.style.display = 'block';
        return;
    }
    emptyMsg.style.display = 'none';
    
    queue.forEach(ticket => {
        const li = document.createElement('li');
        li.className = "list-group-item d-flex justify-content-between align-items-center p-2";
        li.innerHTML = `
            <span>${ticket}</span>
            <button class="btn btn-sm btn-outline-danger border-0" onclick="removeQueueItem('${ticket}')">
                <i class="bi bi-trash"></i> ✕
            </button>
        `;
        list.appendChild(li);
    });
}

function addQueueItems() {
    const input = document.getElementById('queueAddInput');
    const rawText = input.value;
    if (!rawText.trim()) return;

    // Split by newline or comma to handle bulk paste
    const tickets = rawText.split(/[\n,]+/)
        .map(t => t.trim())
        .filter(t => t.length > 0);

    socket.emit('queue_add', {
        room_id: currentRoomId,
        tickets: tickets
    });

    input.value = ''; // Clear input immediately for UX
    input.focus();
}

function removeQueueItem(ticket) {
    socket.emit('queue_remove', {
        room_id: currentRoomId,
        ticket: ticket
    });
    // No need to manually remove from DOM, the 'state_update' event will do it
}

function startFromQueue(ticketKey) {
    // Fill the input and start
    document.getElementById('jiraTicket').value = ticketKey;
    startVote();
}

// static/js/vote.js

function openHistoryModal() {
    const modal = new bootstrap.Modal(document.getElementById('historyModal'));
    const tbody = document.getElementById('historyTableBody');
    const loading = document.getElementById('historyLoading');

    tbody.innerHTML = ''; 
    loading.style.display = 'block';
    modal.show();

    fetch(`/history?room_id=${currentRoomId}&json=true`)
        .then(res => res.json())
        .then(data => {
            loading.style.display = 'none';
            
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No history yet.</td></tr>';
                return;
            }

            data.forEach(row => {
                // 1. Format Breakdown (e.g. "5, 5, 8" -> "5 (x2), 8")
                const counts = {};
                row.votes.forEach(v => { counts[v] = (counts[v] || 0) + 1; });
                
                // Sort keys numerically if possible, otherwise alphabetically
                const sortedKeys = Object.keys(counts).sort((a,b) => {
                     return (parseFloat(a) || a) - (parseFloat(b) || b);
                });

                const breakdownHtml = sortedKeys.map(k => {
                    const count = counts[k];
                    // Create a small badge for each vote group
                    return `<span class="badge bg-light text-dark border me-1">
                                ${k} ${count > 1 ? `<span class="text-secondary small">x${count}</span>` : ''}
                            </span>`;
                }).join('');

                // 2. Format Type Icon
                const typeIcon = row.type === 'Public' ? '🔓' : '🔒';
                
                // 3. Render Row
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><small class="text-muted">${row.timestamp}</small></td>
                    <td class="fw-bold text-primary">${row.ticket_key}</td>
                    <td>${typeIcon} <small>${row.type}</small></td>
                    <td><span class="badge bg-success" style="font-size: 0.9em;">${row.average || '-'}</span></td>
                    <td>${breakdownHtml}</td>
                `;
                tbody.appendChild(tr);
            });
        })
        .catch(err => {
            console.error(err);
            loading.style.display = 'none';
            tbody.innerHTML = '<tr><td colspan="5" class="text-danger text-center">Failed to load history.</td></tr>';
        });
}

function toggleRole() {
    const isObserver = document.getElementById('roleSwitch').checked;
    const newRole = isObserver ? 'observer' : 'voter';
    
    myRole = newRole;
    
    socket.emit('switch_role', {
        room_id: currentRoomId,
        role: newRole
    });
}