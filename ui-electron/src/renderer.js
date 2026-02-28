import { createClient } from '@supabase/supabase-js';
import './index.css';

// Initialize Supabase client
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

let supabase = null;
if (supabaseUrl && supabaseUrl !== "YOUR_SUPABASE_URL_HERE" && supabaseKey) {
  supabase = createClient(supabaseUrl, supabaseKey);
}

let friends = [];

async function fetchFriends() {
  if (!supabase) {
    console.warn("Supabase client not initialized. Check your .env file.");
    // Fallback if no .env configured
    friends = [
      { id: 0, name: 'song', device_id: 'friend-device' },
      { id: 1, name: 'ethan', device_id: 'panigale' },
    ];
    renderFriends();
    return;
  }

  try {
    const { data, error } = await supabase
      .from('Users')
      .select('*')
      .order('name');

    if (error) {
      console.error('Error fetching friends from Supabase:', error.message);
      return;
    }

    if (data) {
      friends = data;
      renderFriends();
    }
  } catch (err) {
    console.error('Unexpected error:', err);
  }
}

async function renderFriends() {
  const listContainer = document.getElementById('friends-list');
  if (!listContainer) return;

  // Identify device via Electron API (Async)
  const systemHostname = window.electronAPI ? await window.electronAPI.getHostname() : 'unknown';

  listContainer.innerHTML = '';

  friends.forEach(friend => {
    // Current user is identified by device_id matching system hostname
    const isMe = friend.device_id && friend.device_id === systemHostname;

    const li = document.createElement('li');
    li.className = `friend-card ${isMe ? 'current-user' : ''}`;

    // Use fallback avatar based on name
    const avatar = friend.name ? friend.name.charAt(0).toUpperCase() : '?';

    li.innerHTML = `
      <div class="friend-info">
        <div class="friend-avatar">${avatar}</div>
        <div class="friend-details">
          <span class="friend-name">
            ${friend.name || 'Unknown'}
            ${isMe ? '<span class="me-badge">(Me)</span>' : ''}
          </span>
          <span class="friend-status">
            <span class="status-dot active"></span>
            Online
          </span>
        </div>
      </div>
      <button 
        class="poke-btn" 
        data-id="${friend.id}"
        ${isMe ? 'disabled' : ''}
      >
        ${isMe ? 'You' : 'Poke'}
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
document.addEventListener('DOMContentLoaded', fetchFriends);
