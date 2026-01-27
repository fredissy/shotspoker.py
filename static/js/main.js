const socket = io(); // Connects automatically

// --- Socket Listeners ---
socket.on('connect', () => {
    console.log("Connected to server via WebSocket");
    // No need to emit 'join_room_request'. 
    // The server checks our Cookie and joins us automatically!
});

socket.on('state_update', (state) => {
    updateUI(state); // Defined in vote.js
});

socket.on('notification', (data) => {
    console.log(data.msg);
});

socket.on('room_closed', (data) => {
    // alert(data.msg || "The room has been closed.");
    window.location.href = '/';
});

// --- Actions ---
function logout() {
    // Hit the server route to clear the cookie
    window.location.href = '/logout';
}

function sendReaction(emoji) {
    socket.emit('send_reaction', {
        room_id: currentRoomId,
        emoji: emoji
    });
    
    // Optional: Add a localized burst immediately for instant feedback
    // createFloatingEmoji(emoji, true);
}

// 2. Receive Listener
socket.on('trigger_reaction', (data) => {
    createFloatingEmoji(data.emoji);
});

(function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
})();

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}