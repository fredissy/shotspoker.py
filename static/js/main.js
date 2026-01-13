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

// --- Actions ---
function logout() {
    // Hit the server route to clear the cookie
    window.location.href = '/logout';
}
