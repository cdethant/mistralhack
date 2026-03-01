import { createClient } from '@supabase/supabase-js';
import './index.css';

const AVATAR_COLORS = ['avatar-emerald', 'avatar-indigo', 'avatar-rose', 'avatar-amber', 'avatar-cyan'];

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

  friends.forEach((friend, i) => {
    // Current user is identified by device_id matching system hostname
    const isMe = friend.device_id && friend.device_id === systemHostname;
    if (isMe) currentUser = friend;

    const li = document.createElement('li');
    li.className = `friend-card ${isMe ? 'current-user' : ''}`;

    // Use fallback avatar based on name
    const avatar = friend.name ? friend.name.charAt(0).toUpperCase() : '?';

    li.innerHTML = `
      <div class="friend-info">
        <div class="friend-avatar ${AVATAR_COLORS[i % AVATAR_COLORS.length]}">${avatar}</div>
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

        // Trigger sidecar focus analysis + ElevenLabs roast if off-task
        if (window.electronAPI && window.electronAPI.callSidecar) {
          console.log('[Roast] Calling sidecar /poke...');
          window.electronAPI.callSidecar('/poke', 'POST').then((result) => {
            console.log('[Roast] Sidecar result:', result);
            if (!result.ok) {
              console.warn('[Sidecar] Poke call failed:', result.error);
              return;
            }
            const { is_focused, roast, audio_b64 } = result.data || {};
            console.log('[Roast] is_focused:', is_focused, '| roast:', roast);
            if (!is_focused && roast && roast !== 'null') {
              console.log('[Roast] Showing LLM roast overlay:', roast);
              window.electronAPI.showRoastOverlay({ roast, audio_b64 });
            } else {
              console.log('[Roast] Null roast — showing fallback overlay for:', senderName);
              window.electronAPI.showRoastOverlay({ roast: `${senderName} just poked you for no reason`, audio_b64: null });
            }
          });
        } else {
          console.warn('[Roast] window.electronAPI.callSidecar not available');
        }
      }
    )
    .subscribe();
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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  if (window.location.hash === '#roast') {
    initRoastOverlay();
  } else {
    fetchFriends();
  }
});

// DevTools test helper — run: window.testRoastOverlay('your message here')
window.testRoastOverlay = (roast = 'Stop looking at twitter and do some work!', audio_b64 = '') => {
  console.log('[Roast] Manual test triggered');
  if (window.electronAPI && window.electronAPI.showRoastOverlay) {
    window.electronAPI.showRoastOverlay({ roast, audio_b64 });
  } else {
    // Fallback if not in Electron or testing overlay directly
    if (window.location.hash === '#roast') {
      window.dispatchEvent(new CustomEvent('test-play-roast', { detail: { roast, audio_b64 } }));
    }
  }
};

function initRoastOverlay() {
  document.body.innerHTML = '';
  document.body.style.background = 'transparent';
  document.documentElement.style.background = 'transparent';

  const container = document.createElement('div');
  container.id = 'roast-overlay-container';

  const circle = document.createElement('div');
  circle.className = 'dj-circle';

  const textContainer = document.createElement('div');
  textContainer.className = 'roast-overlay-text';
  textContainer.textContent = '...';

  container.appendChild(circle);
  container.appendChild(textContainer);
  document.body.appendChild(container);

  const startAudioAnimation = (audioB64) => {
    const audio = new Audio("data:audio/mpeg;base64," + audioB64);

    // Web Audio API
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaElementSource(audio);
    const analyser = audioCtx.createAnalyser();

    analyser.fftSize = 256;
    source.connect(analyser);
    analyser.connect(audioCtx.destination);

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const animate = () => {
      if (audio.paused || audio.ended) return;

      requestAnimationFrame(animate);
      analyser.getByteFrequencyData(dataArray);

      let sum = 0;
      for (let i = 0; i < bufferLength; i++) {
        sum += dataArray[i];
      }
      const average = sum / bufferLength;

      // Pulse scale between 1 and 1.3 based on volume
      const scale = 1 + (average / 256) * 0.4;
      circle.style.transform = `scale(${scale})`;
      circle.style.boxShadow = `0 0 ${80 * scale}px rgba(59, 130, 246, ${0.6 * scale})`;
    };

    // Must resume AudioContext in some browsers but we are bypassing user interaction here
    // as taking over screen needs audio to just play
    audio.play().catch(e => console.error("Audio play failed:", e));

    // Wait until audio starts playing to begin animation
    audio.onplay = () => {
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
      animate();
    };

    audio.onended = () => {
      setTimeout(() => {
        if (window.electronAPI && window.electronAPI.closeRoastOverlay) {
          window.electronAPI.closeRoastOverlay();
        }
      }, 1500);
    };
  };

  if (window.electronAPI && window.electronAPI.onPlayRoast) {
    window.electronAPI.onPlayRoast(({ roast, audio_b64 }) => {
      textContainer.textContent = roast || 'Get back to work!';
      if (audio_b64) {
        startAudioAnimation(audio_b64);
      } else {
        // Fallback animation if no audio
        circle.style.animation = 'pulse-idle 1s infinite alternate ease-in-out';
        setTimeout(() => {
          if (window.electronAPI && window.electronAPI.closeRoastOverlay) {
            window.electronAPI.closeRoastOverlay();
          }
        }, 4000);
      }
    });
  }

  window.addEventListener('test-play-roast', (e) => {
    const { roast, audio_b64 } = e.detail;
    textContainer.textContent = roast || 'Get back to work!';
    if (audio_b64) {
      startAudioAnimation(audio_b64);
    } else {
      circle.style.animation = 'pulse-idle 1s infinite alternate ease-in-out';
    }
  });
}
