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
let currentUser = null;

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
    if (isMe) currentUser = friend;

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

  // Setup Realtime listener once we know who the current user is
  if (currentUser && supabase) {
    setupRealtimeListener(currentUser.id);
  }
}

function setupRealtimeListener(userId) {
  console.log('Setting up Realtime listener for user:', userId);
  supabase
    .channel('public:Pokes')
    .on(
      'postgres_changes',
      {
        event: 'INSERT',
        schema: 'public',
        table: 'Pokes',
        filter: `receiver_id=eq.${userId}`
      },
      (payload) => {
        console.log('Poke received!', payload);
        const senderId = payload.new.sender_id;
        const senderName = friends.find(f => f.id == senderId)?.name || 'Someone';

        if (window.electronAPI && window.electronAPI.triggerPokeNotification) {
          window.electronAPI.triggerPokeNotification(senderName);
        }

        showPokeUIIndicator(senderName);

        // Trigger sidecar focus analysis + ElevenLabs roast if off-task
        if (window.electronAPI && window.electronAPI.callSidecar) {
          console.log('[Roast] Calling sidecar /poke...');
          window.electronAPI.callSidecar('/poke', 'POST').then((result) => {
            console.log('[Roast] Sidecar result:', result);
            if (!result.ok) {
              console.warn('[Sidecar] Poke call failed:', result.error);
              return;
            }
            const { is_focused, roast } = result.data || {};
            console.log('[Roast] is_focused:', is_focused, '| roast:', roast);
            if (!is_focused && roast && roast !== 'null') {
              console.log('[Roast] Showing LLM roast popup:', roast);
              showLLMRoastPopup(roast);
            } else {
              console.log('[Roast] Null roast — showing fallback popup for:', senderName);
              showLLMRoastPopup(`${senderName} just poked you for no reason`);
            }
          });
        } else {
          console.warn('[Roast] window.electronAPI.callSidecar not available');
        }
      }
    )
    .subscribe();
}

function showPokeUIIndicator(senderName) {
  let notif = document.getElementById('poke-notification');

  if (!notif) {
    notif = document.createElement('div');
    notif.id = 'poke-notification';
    document.body.appendChild(notif);
  }

  const avatarChar = senderName.charAt(0).toUpperCase();
  notif.innerHTML = `
    <div class="poke-notif-avatar">${avatarChar}</div>
    <div class="poke-notif-text">${senderName} poked you!</div>
  `;

  // Show
  notif.classList.add('show');

  // Hide after 4 seconds
  setTimeout(() => {
    notif.classList.remove('show');
  }, 4000);
}

function handlePoke(event) {
  const btn = event.currentTarget;
  if (btn.disabled || btn.classList.contains('poked')) return;

  const friendId = btn.getAttribute('data-id');
  const friendName = friends.find(f => f.id == friendId)?.name || 'Friend';

  // Add haptic-like visual feedback
  btn.classList.add('poked');
  btn.innerHTML = 'Poked!';

  console.log(`Poking ${friendName}! (ID: ${friendId})`);

  if (supabase && currentUser) {
    supabase.from('Pokes').insert([
      { sender_id: currentUser.id, receiver_id: friendId }
    ]).then(({ error }) => {
      if (error) console.error('Error sending poke:', error);
    });
  }

  // Reset after 3 seconds
  setTimeout(() => {
    btn.classList.remove('poked');
    btn.innerHTML = 'Poke';
  }, 3000);
}

function showLLMRoastPopup(roastText) {
  console.log('[Roast] showLLMRoastPopup called with:', roastText);
  let popup = document.getElementById('llm-roast-popup');

  if (!popup) {
    console.log('[Roast] Creating popup DOM element');
    popup = document.createElement('div');
    popup.id = 'llm-roast-popup';

    const label = document.createElement('span');
    label.className = 'roast-label';
    label.textContent = 'new poke: ';

    const content = document.createElement('span');
    content.className = 'roast-content';

    const cursor = document.createElement('span');
    cursor.className = 'roast-cursor';
    cursor.textContent = '|';

    popup.appendChild(label);
    popup.appendChild(content);
    popup.appendChild(cursor);
    document.body.appendChild(popup);
  }

  // Reset
  const content = popup.querySelector('.roast-content');
  const cursor = popup.querySelector('.roast-cursor');
  content.textContent = '';
  cursor.style.opacity = '1';

  // Clear any existing dismiss timer
  if (popup._dismissTimer) clearTimeout(popup._dismissTimer);
  if (popup._streamInterval) clearInterval(popup._streamInterval);

  // Show
  console.log('[Roast] Adding .show class to popup');
  popup.classList.add('show');
  console.log('[Roast] Popup classes after show:', popup.className, '| computed opacity:', getComputedStyle(popup).opacity);

  // Stream text in character by character
  let i = 0;
  const speed = 28; // ms per character
  popup._streamInterval = setInterval(() => {
    if (i < roastText.length) {
      content.textContent += roastText[i];
      i++;
    } else {
      clearInterval(popup._streamInterval);
      // Blink cursor briefly then hide
      setTimeout(() => { cursor.style.opacity = '0'; }, 800);
      // Auto-dismiss after reading time (min 4s, +40ms per char)
      const readTime = Math.max(4000, roastText.length * 40);
      popup._dismissTimer = setTimeout(() => {
        popup.classList.remove('show');
      }, readTime);
    }
  }, speed);
}

// Initialize
document.addEventListener('DOMContentLoaded', fetchFriends);

// DevTools test helper — run: window.testRoastPopup('your message here')
window.testRoastPopup = (text = 'test poke: your message here') => {
  console.log('[Roast] Manual test triggered');
  showLLMRoastPopup(text);
};
