import './index.css';

// Mock data for friends
const friends = [
  { id: 1, name: 'Alice Chen', status: 'Working on frontend', state: 'active', avatar: 'AC' },
  { id: 2, name: 'Bob Smith', status: 'Distracted (YouTube)', state: 'idle', avatar: 'BS' },
  { id: 3, name: 'Charlie Davis', status: 'Offline', state: 'offline', avatar: 'CD' },
  { id: 4, name: 'Diana Prince', status: 'Deep work', state: 'active', avatar: 'DP' },
];

function renderFriends() {
  const listContainer = document.getElementById('friends-list');
  if (!listContainer) return;

  listContainer.innerHTML = '';

  friends.forEach(friend => {
    const li = document.createElement('li');
    li.className = 'friend-card';

    const canPoke = friend.state !== 'offline';

    li.innerHTML = `
      <div class="friend-info">
        <div class="friend-avatar">${friend.avatar}</div>
        <div class="friend-details">
          <span class="friend-name">${friend.name}</span>
          <span class="friend-status">
            <span class="status-dot ${friend.state}"></span>
            ${friend.status}
          </span>
        </div>
      </div>
      <button 
        class="poke-btn" 
        data-id="${friend.id}"
        ${!canPoke ? 'disabled' : ''}
      >
        Poke
      </button>
    `;

    listContainer.appendChild(li);
  });

  // Attach event listeners to buttons
  document.querySelectorAll('.poke-btn').forEach(btn => {
    btn.addEventListener('click', handlePoke);
  });
}

function handlePoke(event) {
  const btn = event.currentTarget;
  if (btn.disabled || btn.classList.contains('poked')) return;

  const friendId = btn.getAttribute('data-id');
  const friendName = friends.find(f => f.id == friendId)?.name || 'Friend';

  // Add haptic-like visual feedback
  btn.classList.add('poked');
  btn.innerHTML = 'Poked!';

  console.log(`Poked ${friendName}! (ID: ${friendId})`);
  // Here we would typically trigger an IPC call to the main process
  // window.electronAPI.pokeFriend(friendId);

  // Reset after 3 seconds
  setTimeout(() => {
    btn.classList.remove('poked');
    btn.innerHTML = 'Poke';
  }, 3000);
}

// Initialize
document.addEventListener('DOMContentLoaded', renderFriends);
