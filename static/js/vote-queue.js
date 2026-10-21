let currentQueue = [];
let currentQueueUrls = {};

function createQueueTicketLabel(ticket) {
    const url = currentQueueUrls[ticket];
    const hasUrl = typeof url === 'string' && /^https?:\/\//.test(url);
    const label = document.createElement(hasUrl ? 'a' : 'span');
    label.textContent = ticket;
    label.className = 'text-break';
    if (hasUrl) {
        label.href = url;
        label.target = '_blank';
        label.rel = 'noopener noreferrer';
        label.title = 'Open Jira ticket in a new tab';
    }
    return label;
}

function updateQueueUI(state) {
    const queueSection = document.getElementById('queueSection');
    const queueList = document.getElementById('queueList');
    const manageBtn = document.querySelector('button[onclick="openQueueModal()"]');

    currentQueue = state.queue || [];
    currentQueueUrls = state.queue_urls || {};
    if (manageBtn) manageBtn.style.display = 'inline-block';

    const modalList = document.getElementById('modalQueueList');
    const queueModal = document.getElementById('queueModal');
    if (modalList && queueModal && queueModal.classList.contains('show')) {
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

                const label = createQueueTicketLabel(ticket);
                if (label.tagName === 'A') {
                    const group = document.createElement('div');
                    group.className = 'btn-group flex-shrink-0';
                    label.className = btn.className;
                    btn.textContent = 'Start';
                    btn.setAttribute('aria-label', `Start voting on ${ticket}`);
                    group.append(label, btn);
                    queueList.appendChild(group);
                } else {
                    queueList.appendChild(btn);
                }
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
        if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
            console.error('Bootstrap Modal is not available. Cannot open queue modal.');
            return;
        }
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
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'btn btn-sm btn-outline-danger border-0 flex-shrink-0';
        removeBtn.textContent = '\u00d7';
        removeBtn.title = `Remove ${ticket} from queue`;
        removeBtn.setAttribute('aria-label', removeBtn.title);
        removeBtn.onclick = () => removeQueueItem(ticket);
        li.append(createQueueTicketLabel(ticket), removeBtn);
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
    if (ticketInput) ticketInput.value = currentQueueUrls[ticketKey] || ticketKey;
    if (typeof startVote === 'function') {
        startVote();
    }
}
