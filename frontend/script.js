// const input = document.getElementById("username");
// const goButton = document.getElementById("goButton");

// function goToNextPage() {
//   const name = input.value.trim();
//   if (name === "") {
//     alert("Please enter your name 🙂");
//     return;
//   }

//   // Save to localStorage so next page can read it
//   localStorage.setItem("cc_user_name", name);

//   // Go to the next page
//   window.location.href = "dashboard.html"; // <-- make sure this file exists
// }

// input.addEventListener("keypress", e => {
//   if (e.key === "Enter") {
//     goToNextPage();
//   }
// });

// goButton.addEventListener("click", goToNextPage);

// Get the elements

/* Robust event wiring for the username input + arrow button.
   Paste this into script.js or directly before </body>. */
/* script.js — consolidated user navigation + index init
   Place this file in your project and include it in index.html.
   Assumes index.html has:
     <input id="username"> and a button <button id="goButton"> (or matching classes)
*/
/* script.js — consolidated user navigation + index init
   Place this file in your project and include it in index.html.
   Assumes index.html has:
     <input id="username"> and a button <button id="goButton"> (or matching classes)
*/

(function () {
  // Utility to safely read/set localStorage (some browsers block it in incognito)
  function safeSet(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { console.warn("localStorage write failed", e); }
  }
  function safeGet(key) {
    try { return localStorage.getItem(key); } catch (e) { console.warn("localStorage read failed", e); return null; }
  }

  // Run when DOM is ready
  document.addEventListener("DOMContentLoaded", () => {
    // --- 0. Quick redirect if user is already logged in ---
    if (safeGet("cc_logged_in") === "1") {
      // If you want auto-redirect behavior, uncomment next line:
      window.location.href = "dashboard.html";
      return;
    }

    // --- 1. Find the main controls on the index page (username + go button) ---
    const input = document.getElementById('username') || document.querySelector('.name-input');
    const goButton = document.getElementById('goButton') || document.querySelector('.arrow-button');

    if (!input || !goButton) {
      // Not necessarily an error — some pages (dashboard.html) won't have these elements.
      console.log("Index input or goButton not found. script.js will still run for other pages.");
      // Still wire history button below (dashboard) if present — continue.
    }

    // Prefill stored name if available
    const storedName = safeGet('cc_user_name');
    if (storedName && input) input.value = storedName;

    // Handler used for both click and Enter
    function proceedFromIndex() {
      const name = input ? (input.value || "").trim() : "";
      if (!name) {
        alert("Please enter your name 🙂");
        if (input) input.focus();
        return;
      }

      safeSet('cc_user_name', name);
      safeSet('cc_seen_intro', '1');

      // If you want the visitor to be fully "logged in" after entering name (auto-login),
      // uncomment the line below. For a real app, prefer a proper server login flow.
      // safeSet('cc_logged_in', '1');

      // Navigate to dashboard
      window.location.href = 'dashboard.html';
    }

    // Wire index controls (if present)
    if (goButton && input) {
      // Ensure button does not submit a form by default
      if (goButton.getAttribute('type') !== 'button') goButton.setAttribute('type', 'button');

      goButton.addEventListener('click', (ev) => {
        ev.preventDefault();
        proceedFromIndex();
      });

      input.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter') {
          ev.preventDefault();
          proceedFromIndex();
        }
      });
    }

    // --------- Dashboard/page-specific wiring ----------
    // Show greeting if dashboard element exists
    const greetingEl = document.getElementById('greetingText') || document.querySelector('.greeting-text');
    if (greetingEl) {
      const name = safeGet('cc_user_name') || 'there';
      greetingEl.textContent = `Hi ${name}! What would you like to do today?`;
    }

    // Wire "Check History" button(s)
    const historyBtn = document.getElementById('checkHistoryBtn') || document.querySelector('.check-history');
    if (historyBtn) {
      historyBtn.addEventListener('click', (ev) => {
        ev.preventDefault();
        // Option A: Open Streamlit app that contains your history tab (quick)
        // window.open('http://localhost:8501', '_blank');

        // Option B: Open your frontend history page which calls the backend API
        window.location.href = 'history.html';
      });
    }

    // Optional: Wire logout if present
    const logoutBtn = document.getElementById('logoutBtn') || document.querySelector('.logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', (ev) => {
        ev.preventDefault();
        try {
          localStorage.removeItem('cc_logged_in');
          localStorage.removeItem('cc_user_email');
          // keep the stored name so they don't have to retype it next time
          window.location.href = 'index.html';
        } catch (e) {
          console.warn("Logout failed", e);
          window.location.href = 'index.html';
        }
      });
    }

    // Helpful console message
    console.log("script.js initialized.");
  });
})();
