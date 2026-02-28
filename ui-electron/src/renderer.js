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
    // Fallback to mock data if no .env configured
    friends = [
      { id: 1, name: 'Alice Chen', status: 'Working on frontend', state: 'active', avatar: 'AC' },
      { id: 2, name: 'Bob Smith', status: 'Distracted (YouTube)', state: 'idle', avatar: 'BS' },
      { id: 3, name: 'Charlie Davis', status: 'Offline', state: 'offline', avatar: 'CD' },
      { id: 4, name: 'Diana Prince', status: 'Deep work', state: 'active', avatar: 'DP' },
    ];
    renderFriends();
    return;
  }

  try {
    const { data, error } = await supabase
      .from('friends')
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

function renderFriends() {
  const listContainer = document.getElementById('friends-list');
  if (!listContainer) return;

  listContainer.innerHTML = '';

  friends.forEach(friend => {
    const li = document.createElement('li');
    li.className = 'friend-card';

    const canPoke = friend.state !== 'offline';
    // Use fallback avatar if not provided in DB
    const avatar = friend.avatar || friend.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();

    li.innerHTML = `
      <div class="friend-info">
        <div class="friend-avatar">${avatar}</div>
        <div class="friend-details">
          <span class="friend-name">${friend.name || 'Unknown'}</span>
          <span class="friend-status">
            <span class="status-dot ${friend.state || 'offline'}"></span>
            ${friend.status || 'Offline'}
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
document.addEventListener('DOMContentLoaded', fetchFriends);
