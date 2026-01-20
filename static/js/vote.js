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

// 3. Animation Logic
function createFloatingEmoji(emoji) {
    const container = document.getElementById('reactionContainer');
    const el = document.createElement('div');
    el.innerText = emoji;
    
    // Randomize starting position (horizontal)
    const randomLeft = Math.floor(Math.random() * 80) + 10; // Keep within 10-90% width
    
    // Randomize size slightly
    const size = Math.floor(Math.random() * 20) + 20; // 20px to 40px

    // Apply styles
    el.style.position = 'absolute';
    el.style.left = randomLeft + '%';
    el.style.bottom = '60px'; // Start above the toolbar
    el.style.fontSize = size + 'px';
    el.style.opacity = '1';
    el.style.pointerEvents = 'none';
    el.style.transition = 'transform 3s ease-in, opacity 3s ease-in';
    
    container.appendChild(el);

    // Trigger animation in next frame
    requestAnimationFrame(() => {
        // Float up by random amount (200px to 500px)
        const floatDistance = Math.floor(Math.random() * 300) + 200;
        // Random slight rotation
        const rotate = Math.floor(Math.random() * 60) - 30;
        
        el.style.transform = `translateY(-${floatDistance}px) rotate(${rotate}deg)`;
        el.style.opacity = '0';
    });

    // Cleanup after animation
    setTimeout(() => {
        el.remove();
    }, 3000);
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
