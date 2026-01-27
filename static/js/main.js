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

// static/js/main.js

// --- Konami Code Easter Egg ---
const konamiCode = [
    "ArrowUp", "ArrowUp", 
    "ArrowDown", "ArrowDown", 
    "ArrowLeft", "ArrowRight", 
    "ArrowLeft", "ArrowRight", 
    "b", "a"
];
let konamiIndex = 0;

document.addEventListener('keydown', (e) => {
    // 1. Check if the key matches the current step in the sequence
    if (e.key === konamiCode[konamiIndex]) {
        konamiIndex++; // Move to next step

        // 2. If sequence is complete, trigger the egg!
        if (konamiIndex === konamiCode.length) {
            activateBarrelRoll();
            konamiIndex = 0; // Reset
        }
    } else {
        konamiIndex = 0; // Mistake made, reset progress
    }
});

function activateBarrelRoll() {
    const body = document.body;
    
    // Add class to trigger animation
    body.classList.add('do-a-barrel-roll');
    
    // Send a toast notification for fun
    if (typeof showToast === 'function') {
        showToast("🎮 Cheat Code Activated!", "warning");
    }

    // Remove class after 1s so it can be triggered again
    setTimeout(() => {
        body.classList.remove('do-a-barrel-roll');
    }, 1000);
}