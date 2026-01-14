function createRoom() {
    const name = document.getElementById('joinName').value;
    const role = document.querySelector('input[name="role"]:checked').value;
    const deckType = document.getElementById('deckType').value;
    
    performLogin({ action: 'create',
        name: name,
        role: role,
        deck_type: deckType
    });
}

function joinRoom() {
    const name = document.getElementById('joinName').value;
    const rId = document.getElementById('roomIdInput').value;
    const role = document.querySelector('input[name="role"]:checked').value;
    
    performLogin({ action: 'join',
        name: name,
        role: role,
        room_id: rId
    });
}

function performLogin(data) {
    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
        } else if (data.redirect) {
            // Success! The server tells us where to go.
            window.location.href = data.redirect;
        }
    })
    .catch(err => showError("Connection error"));
}

function showError(msg) {
    const el = document.getElementById('loginError');
    el.innerText = msg;
    el.style.display = 'block';
}