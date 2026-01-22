let myChart = null;
let timerInterval = null;
let currentDeckRendered = false;
let wasRevealed = false;

function updateUI(state) {
    updateUserRole(state);
    updateHeader(state);
    renderCards(state);
    updateVotingInterface(state);
    updateAdminButtons(state);
    renderParticipants(state);

    // Consensus Check
    if (state.revealed && !wasRevealed) {
        checkConsensus(state.participants);
        wasRevealed = true;
    } else if (!state.revealed) {
        wasRevealed = false;
    }

    updateStatsAndChart(state);
    updateTimer(state);

    // Call queue update from vote-queue.js if available
    if (typeof updateQueueUI === 'function') {
        updateQueueUI(state);
    }
}

function updateUserRole(state) {
    if (state.participants) {
        const me = state.participants.find(p => p.name === myName);
        if (me) {
            myRole = me.role;
            // Sync the toggle switch visually (in case change came from server)
            const switchEl = document.getElementById('roleSwitch');
            if (switchEl) switchEl.checked = (myRole === 'observer');
        }
    }
}

function updateHeader(state) {
    // 1. Header Info
    let headerText = state.active ? `Voting on: ${state.ticket_key}` : "Waiting for session...";

    // NEW: Add lock icon if the vote is private
    if (state.active && !state.is_public) {
        headerText += " 🔒";
    }

    const currentTicketDisplay = document.getElementById('currentTicketDisplay');
    if (currentTicketDisplay) currentTicketDisplay.innerText = headerText;
}

function renderCards(state) {
    const cardsContainer = document.getElementById('cardsContainer');
    if (!cardsContainer) return;

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
}

function updateVotingInterface(state) {
    // 2. Voting Interface Visibility
    const votingInterface = document.getElementById('votingInterface');
    const observerMessage = document.getElementById('observerMessage');

    if (!votingInterface || !observerMessage) return;

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
}

function updateAdminButtons(state) {
    // 3. Admin Buttons
    const revealBtn = document.querySelector('button[onclick="revealVote()"]');
    const resetBtn = document.querySelector('button[onclick="resetVote()"]');
    const startBtn = document.getElementById('startVoteBtn');

    // Define Admin Status
    const amIAdmin = (socket && socket.id === state.admin_sid);

    if (revealBtn) {
        if (state.active) {
            revealBtn.disabled = state.revealed;
            revealBtn.title = state.revealed ? "Results are already visible" : "Reveal results";
        } else {
            revealBtn.disabled = true;
        }
    }

    if (resetBtn) {
        if (state.active) {
            resetBtn.disabled = !amIAdmin;
            resetBtn.title = amIAdmin ? "" : "Only the starter can reset";
        } else {
            resetBtn.disabled = false;
        }
    }

    if (startBtn) {
        if (state.active) {
            startBtn.disabled = !state.revealed;
        } else {
            startBtn.disabled = false;
        }
    }
}

function renderParticipants(state) {
    // 4. Participants List
    const list = document.getElementById('votersList');
    if (!list) return;

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
    if (typeof confetti === 'function') {
        confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#0d6efd', '#ffc107', '#198754'] // Bootstrap Blue, Yellow, Green
        });
    }
}

function updateStatsAndChart(state) {
    // 6. Chart Logic
    const placeholder = document.getElementById('chartPlaceholder');
    const statsRow = document.getElementById('statsRow');
    const statAvg = document.getElementById('statAverage');
    const statAgree = document.getElementById('statAgreement');

    if (state.stats && statsRow) {
        statsRow.style.display = 'flex';

        // Handle Average (might be null if only '?' or 'coffee' were voted)
        if (statAvg) statAvg.innerText = (state.stats.average !== null) ? state.stats.average : '-';

        // Handle Agreement
        if (statAgree) statAgree.innerText = state.stats.agreement + '%';
    } else {
        if (statsRow) statsRow.style.display = 'none';
    }

    if (state.revealed && state.distribution && Object.keys(state.distribution).length > 0) {
        if (placeholder) placeholder.style.display = 'none';
        renderChart(state.distribution);
    } else {
        if(myChart) myChart.destroy();
        myChart = null;
        if (placeholder) {
            placeholder.style.display = 'block';
            placeholder.innerText = "Waiting for reveal...";
        }
    }
}

function renderChart(distribution) {
    const ctxEl = document.getElementById('resultsChart');
    if (!ctxEl) return;
    const ctx = ctxEl.getContext('2d');

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
        if (typeof Chart !== 'undefined') {
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
}

function updateTimer(state) {
    const timerEl = document.getElementById('timerDisplay');
    if (!timerEl) return;

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

function showToast(message, type = 'primary') {
    const toastEl = document.getElementById('mainToast');
    const msgEl = document.getElementById('toastMessage');

    if (!toastEl || !msgEl) return;

    // 1. Set the message text
    msgEl.innerText = message;

    // 2. Set the color (supports 'primary', 'success', 'danger', 'warning')
    // We reset the class list and re-add the necessary Bootstrap classes
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;

    // 3. Show the toast
    if (typeof bootstrap !== 'undefined') {
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    }
}

function copyRoomId() {
    navigator.clipboard.writeText(currentRoomId).then(() => {
        showToast("📋 Room ID copied to clipboard!", "success");
    }).catch(err => {
        console.error(err);
        showToast("❌ Failed to copy Room ID", "danger");
    });
}

function openHistoryModal() {
    const modalEl = document.getElementById('historyModal');
    if (!modalEl) return;

    const tbody = document.getElementById('historyTableBody');
    const loading = document.getElementById('historyLoading');
    
    if (tbody) tbody.innerHTML = '';
    if (loading) loading.style.display = 'block';
    if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
        console.error('Bootstrap Modal is not available. Cannot open history modal.');
        return;
    }
    const modal = new bootstrap.Modal(modalEl);
    modal.show();

    fetch(`/history?room_id=${currentRoomId}&json=true`)
        .then(res => res.json())
        .then(data => {
            if (loading) loading.style.display = 'none';
            if (!tbody) return;

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
            if (loading) loading.style.display = 'none';
            if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-danger text-center">Failed to load history.</td></tr>';
        });
}
