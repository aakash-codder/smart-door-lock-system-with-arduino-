
// main.js - improved validation and error handling for OTP form

async function fetchOtp(){
  try{
    const res = await fetch('/get_otp');
    const data = await res.json();
    const otpEl = document.getElementById('otp');
    if(otpEl) otpEl.textContent = data.otp;
    const rem = document.getElementById('remaining');
    if(rem) rem.textContent = data.remaining;
  }catch(e){ console.error('fetchOtp error', e) }
}

let lastDoorLocked = undefined;
let unlockTimeout = null;

async function fetchStatus(){
  try{
    const res = await fetch('/status');
    const data = await res.json();
    const btEnabled = data.bluetooth_enabled;
    const doorLocked = data.door_locked;
    const btBtn = document.getElementById('bt-unlock');
    if(btBtn) btBtn.disabled = !btEnabled;
    const btState = document.getElementById('bt-state');
    if(btState) btState.textContent = 'State: ' + (btEnabled ? 'Enabled' : 'Disabled');
    const ds = document.getElementById('door-status');
    if(ds) ds.innerHTML = doorLocked ? '<span class="status-locked">Locked</span>' : '<span class="status-unlocked">Unlocked</span>';
    if (typeof lastDoorLocked !== 'undefined') {
      if (lastDoorLocked === true && doorLocked === false) {
        showUnlockAnimation();
      }
    }
    lastDoorLocked = doorLocked;
  }catch(e){ console.error('fetchStatus error', e) }
}

function showUnlockAnimation() {
  const badge = document.getElementById('unlock-badge');
  if (!badge) return;
  badge.classList.add('show');
  badge.classList.remove('pulse');
  void badge.offsetWidth;
  badge.classList.add('pulse');
  if (unlockTimeout) {
    clearTimeout(unlockTimeout);
  }
  unlockTimeout = setTimeout(() => {
    badge.classList.remove('show');
    badge.classList.remove('pulse');
    unlockTimeout = null;
  }, 2800);
}

// Helper: show message in result area with optional type
function showResult(msg, type='info'){
  const result = document.getElementById('result');
  if(!result) return;
  result.textContent = msg;
  result.style.color = (type === 'error') ? 'var(--danger)' : (type === 'success') ? 'var(--success)' : '';
}

async function postJson(url, obj){
  const res = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(obj)
  });
  // try to parse json safely
  let body = null;
  try{ body = await res.json(); }catch(e){ body = null; }
  return { ok: res.ok, status: res.status, body };
}

// init
document.addEventListener('DOMContentLoaded', ()=>{
  fetchOtp();
  fetchStatus();
  setInterval(fetchOtp, 1000);
  setInterval(fetchStatus, 1000);

  const btUnlock = document.getElementById('bt-unlock');
  if(btUnlock){
    btUnlock.addEventListener('click', async ()=>{
      try{
        await postJson('/unlock_bt', {});
      }catch(e){ console.error('bt-unlock error', e) }
      fetchStatus();
    });
  }

  const toggleBt = document.getElementById('toggle-bt');
  if(toggleBt){
    toggleBt.addEventListener('click', async ()=>{
      try{
        await postJson('/toggle_bt', {});
      }catch(e){ console.error('toggle-bt error', e) }
      fetchStatus();
    });
  }

  const otpForm = document.getElementById('otp-form');
  const verifyBtn = document.getElementById('verify-btn');
  if(otpForm){
    otpForm.addEventListener('submit', async (e)=>{
      e.preventDefault();
      const otpInput = document.getElementById('otp-input');
      if(!otpInput){ return showResult('OTP input not found', 'error'); }

      // Use built-in validity but show messages inside page
      if(!otpInput.checkValidity()){
        // show validation message
        showResult(otpInput.validationMessage || 'Please enter a valid 4-digit OTP', 'error');
        return;
      }

      const otpVal = otpInput.value.trim();
      if(verifyBtn) verifyBtn.disabled = true;
      showResult('Verifying...', 'info');
      try{
        const {ok, status, body} = await postJson('/verify_otp', {otp: otpVal});
        if(ok){
          showResult(body && body.message ? body.message : 'Unlocked', 'success');
        } else {
          const msg = body && body.message ? body.message : (status === 401 ? 'Wrong OTP' : 'Server error');
          showResult(msg, 'error');
        }
        fetchStatus();
      }catch(err){
        console.error('verify_otp error', err);
        showResult('Error contacting server', 'error');
      }finally{
        if(verifyBtn) verifyBtn.disabled = false;
      }
    });
  }

  const showCurrent = document.getElementById('show-current');
  if(showCurrent){
    showCurrent.addEventListener('click', async ()=>{
      try{
        const res = await fetch('/get_otp');
        const data = await res.json();
        showResult('Current OTP: ' + data.otp + ' (changes in ' + data.remaining + 's)');
      }catch(e){ console.error('show-current error', e); showResult('Error fetching OTP', 'error') }
    });
  }
});