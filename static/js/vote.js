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
    const statusMessage = document.getElementById('statusMessage');
    if (statusMessage) statusMessage.innerText = '';
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
