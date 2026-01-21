let currentQueue = [];

function updateQueueUI(state) {
    const queueSection = document.getElementById('queueSection');
    const queueList = document.getElementById('queueList');
    const manageBtn = document.querySelector('button[onclick="openQueueModal()"]');

    currentQueue = state.queue || [];
    if (manageBtn) manageBtn.style.display = 'inline-block';

    const modalList = document.getElementById('modalQueueList');
    if (modalList && document.getElementById('queueModal') && document.getElementById('queueModal').classList.contains('show')) {
        renderModalQueueList(currentQueue);
    }

    if (state.queue && state.queue.length > 0) {
        if (queueSection) queueSection.style.display = 'block';
        if (queueList) {
            queueList.innerHTML = '';
            state.queue.forEach(ticket => {
                const btn = document.createElement('button');
                btn.className = "btn btn-sm btn-white border shadow-sm text-primary fw-bold";
                btn.innerText = ticket;
                btn.onclick = () => startFromQueue(ticket);
                btn.title = "Click to start voting on this ticket";

                queueList.appendChild(btn);
            });
        }
    } else {
        if (queueSection) queueSection.style.display = 'none';
    }
}

function openQueueModal() {
    // Just render current state and show
    renderModalQueueList(currentQueue);

    // Clear the input
    const input = document.getElementById('queueAddInput');
    if (input) input.value = '';

    const modalEl = document.getElementById('queueModal');
    if (modalEl) {
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}

function renderModalQueueList(queue) {
    const list = document.getElementById('modalQueueList');
    const emptyMsg = document.getElementById('emptyQueueMsg');

    if (!list || !emptyMsg) return;

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
    if (!input) return;

    const rawText = input.value;
    if (!rawText.trim()) return;

    // Split by newline or comma to handle bulk paste
    const tickets = rawText.split(/[\n,]+/)
        .map(t => t.trim())
        .filter(t => t.length > 0);

    if (socket) {
        socket.emit('queue_add', {
            room_id: currentRoomId,
            tickets: tickets
        });
    }

    input.value = ''; // Clear input immediately for UX
    input.focus();
}

function removeQueueItem(ticket) {
    if (socket) {
        socket.emit('queue_remove', {
            room_id: currentRoomId,
            ticket: ticket
        });
    }
    // No need to manually remove from DOM, the 'state_update' event will do it
}

function startFromQueue(ticketKey) {
    // Fill the input and start
    const ticketInput = document.getElementById('jiraTicket');
    if (ticketInput) ticketInput.value = ticketKey;
    if (typeof startVote === 'function') {
        startVote();
    }
}
