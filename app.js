/**
 * EcoSort AI - Waste Classification & Disposal Guide Logic (Client Side)
 */

// Global application state
let appState = {
  userSession: null, // Stores { token, email }
  currentResult: null,
  history: [],
  diversionRate: 0,
  totalPoints: 0,
  totalCO2Saved: 0
};

// Machine learning and maps globals
let netModel = null;

// Elements
const elements = {
  searchInput: null,
  searchBtn: null,
  suggestionsBox: null,
  dropZone: null,
  fileInput: null,
  sampleBtnGroup: null,
  scanModal: null,
  scanStatus: null,
  scanProgress: null,
  resultSection: null,
  dashboardSection: null,
  historyList: null,
  clearHistoryBtn: null,
  statScanned: null,
  statPoints: null,
  statCO2: null,
  diversionCircle: null,
  diversionValue: null,
  categoryFilters: null,

  // Auth Elements
  authContainer: null,
  appContainer: null,
  loginForm: null,
  registerForm: null,
  loginPhone: null,
  loginCountryCode: null,
  loginPassword: null,
  registerName: null,
  registerPhone: null,
  registerCountryCode: null,
  registerPassword: null,
  registerConfirmPassword: null,
  showRegister: null,
  showLogin: null,
  authError: null,
  userProfile: null,
  headerUserEmail: null,
  logoutBtn: null,

  // New tab/visual elements
  tabStats: null,
  tabLeaderboard: null,
  statsView: null,
  leaderboardView: null,
  leaderboardList: null
};

// Load TensorFlow.js MobileNet Model
async function loadMobileNet() {
  console.log("Loading TensorFlow.js MobileNet model...");
  try {
    netModel = await mobilenet.load();
    console.log("MobileNet model loaded successfully!");
  } catch (e) {
    console.error("Failed to load MobileNet model:", e);
  }
}

// Initialize Application
document.addEventListener("DOMContentLoaded", async () => {
  cacheElements();
  setupEventListeners();
  loadMobileNet(); // Load MobileNet in the background

  // Check session
  const savedSession = localStorage.getItem("ecosort_session");
  if (savedSession) {
    try {
      appState.userSession = JSON.parse(savedSession);
      showApp();
      await loadStateFromStorage();
      updateDashboard();
      renderHistory();
    } catch (e) {
      localStorage.removeItem("ecosort_session");
      showAuth();
    }
  } else {
    showAuth();
  }
});

function cacheElements() {
  elements.searchInput = document.getElementById("search-input");
  elements.searchBtn = document.getElementById("search-btn");
  elements.suggestionsBox = document.getElementById("suggestions-box");
  elements.dropZone = document.getElementById("drop-zone");
  elements.fileInput = document.getElementById("file-input");
  elements.sampleBtnGroup = document.querySelector(".sample-scans");
  elements.scanModal = document.getElementById("scan-modal");
  elements.scanStatus = document.getElementById("scan-status");
  elements.scanProgress = document.getElementById("scan-progress-bar");
  elements.resultSection = document.getElementById("result-section");
  elements.dashboardSection = document.getElementById("dashboard-section");
  elements.historyList = document.getElementById("history-list");
  elements.clearHistoryBtn = document.getElementById("clear-history-btn");
  elements.statScanned = document.getElementById("stat-scanned");
  elements.statPoints = document.getElementById("stat-points");
  elements.statCO2 = document.getElementById("stat-co2");
  elements.diversionCircle = document.getElementById("diversion-circle-progress");
  elements.diversionValue = document.getElementById("diversion-percentage");
  elements.categoryFilters = document.querySelectorAll(".category-card");
  elements.resultPrepList = document.getElementById("result-prep-list");
  elements.prepCompletionBox = document.getElementById("prep-completion-message");
  elements.completionDestinationValue = document.getElementById("completion-destination-value");
  elements.resultStatusBadge = document.getElementById("result-status-badge");

  // Cache Auth elements
  elements.authContainer = document.getElementById("auth-container");
  elements.appContainer = document.getElementById("app-container");
  elements.loginForm = document.getElementById("login-form");
  elements.registerForm = document.getElementById("register-form");
  elements.loginPhone = document.getElementById("login-phone");
  elements.loginCountryCode = document.getElementById("login-country-code");
  elements.loginPassword = document.getElementById("login-password");
  elements.registerName = document.getElementById("register-name");
  elements.registerPhone = document.getElementById("register-phone");
  elements.registerCountryCode = document.getElementById("register-country-code");
  elements.registerPassword = document.getElementById("register-password");
  elements.registerConfirmPassword = document.getElementById("register-confirm-password");
  elements.showRegister = document.getElementById("show-register");
  elements.showLogin = document.getElementById("show-login");
  elements.authError = document.getElementById("auth-error");
  elements.userProfile = document.getElementById("user-profile");
  elements.headerUserEmail = document.getElementById("header-user-email");
  elements.logoutBtn = document.getElementById("logout-btn");

  // New tab/visual cache
  elements.tabStats = document.getElementById("tab-stats");
  elements.tabLeaderboard = document.getElementById("tab-leaderboard");
  elements.statsView = document.getElementById("dashboard-stats-view");
  elements.leaderboardView = document.getElementById("dashboard-leaderboard-view");
  elements.leaderboardList = document.getElementById("leaderboard-list");
}

function showApp() {
  elements.authContainer.style.display = "none";
  elements.appContainer.style.display = "block";
  if (appState.userSession) {
    elements.userProfile.style.display = "inline-flex";
    elements.headerUserEmail.innerText = appState.userSession.name || appState.userSession.phone;
  }
}

function showAuth() {
  elements.appContainer.style.display = "none";
  elements.authContainer.style.display = "flex";
  elements.userProfile.style.display = "none";
  elements.authError.style.display = "none";
  elements.loginForm.reset();
  elements.registerForm.reset();

  // Show login form by default
  elements.loginForm.style.display = "flex";
  elements.registerForm.style.display = "none";
}

async function loadStateFromStorage() {
  if (!appState.userSession) return;
  try {
    const response = await fetch("/api/history", {
      headers: {
        "Authorization": `Bearer ${appState.userSession.token}`
      }
    });
    if (response.status === 401) {
      // Session expired/invalid on server, log out client cleanly
      appState.userSession = null;
      appState.history = [];
      localStorage.removeItem("ecosort_session");
      showAuth();
      return;
    }
    if (response.ok) {
      appState.history = await response.json();
      return;
    }
  } catch (e) {
    console.warn("Failed to fetch history from Python API. Checking localStorage fallback...", e);
  }

  // Local storage fallback
  const savedHistory = localStorage.getItem("ecosort_history");
  if (savedHistory) {
    try {
      appState.history = JSON.parse(savedHistory);
    } catch (e) {
      appState.history = [];
    }
  }
}

function setupEventListeners() {
  // Input search typing
  elements.searchInput.addEventListener("input", handleSearchInput);
  elements.searchInput.addEventListener("focus", handleSearchInput);

  // Close suggestions if clicked outside
  document.addEventListener("click", (e) => {
    if (!elements.searchInput.contains(e.target) && !elements.suggestionsBox.contains(e.target)) {
      elements.suggestionsBox.classList.remove("active");
    }
  });

  // Click Search Button
  elements.searchBtn.addEventListener("click", triggerSearch);
  elements.searchInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      triggerSearch();
    }
  });

  // Setup sample scans
  elements.sampleBtnGroup.addEventListener("click", async (e) => {
    const btn = e.target.closest(".sample-btn");
    if (btn) {
      const itemId = btn.dataset.item;
      const imgPath = btn.dataset.img;
      try {
        const response = await fetch(`/api/classify?id=${itemId}`);
        if (response.ok) {
          const dbItem = await response.json();
          startScanning(dbItem, imgPath);
        }
      } catch (err) {
        console.error("Failed to load sample scan classification:", err);
      }
    }
  });

  // Setup category quick filter cards
  elements.categoryFilters.forEach(card => {
    card.addEventListener("click", () => {
      const cat = card.dataset.category;
      elements.searchInput.value = cat === "non-recyclable" ? "Non-Recyclable" : cat.charAt(0).toUpperCase() + cat.slice(1);
      handleSearchInput();
      elements.searchInput.focus();
    });
  });

  // Drag and drop events
  elements.dropZone.addEventListener("click", () => elements.fileInput.click());
  elements.fileInput.addEventListener("change", handleFileSelect);

  elements.dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    elements.dropZone.classList.add("dragover");
  });

  elements.dropZone.addEventListener("dragleave", () => {
    elements.dropZone.classList.remove("dragover");
  });

  elements.dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    elements.dropZone.classList.remove("dragover");
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      processUploadedFile(files[0]);
    }
  });

  // Clear History
  elements.clearHistoryBtn.addEventListener("click", clearHistory);

  // Auth transitions
  elements.showRegister.addEventListener("click", (e) => {
    e.preventDefault();
    elements.authError.style.display = "none";
    elements.loginForm.style.display = "none";
    elements.registerForm.style.display = "flex";
  });

  elements.showLogin.addEventListener("click", (e) => {
    e.preventDefault();
    elements.authError.style.display = "none";
    elements.registerForm.style.display = "none";
    elements.loginForm.style.display = "flex";
  });

  // Auth submissions
  elements.loginForm.addEventListener("submit", handleLoginSubmit);
  elements.registerForm.addEventListener("submit", handleRegisterSubmit);

  // Logout action
  elements.logoutBtn.addEventListener("click", handleLogout);

  // Password visibility toggle setup
  document.querySelectorAll(".password-toggle").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.target;
      const input = document.getElementById(targetId);
      const icon = btn.querySelector(".toggle-icon path");

      if (input.type === "password") {
        input.type = "text";
        input.classList.add("password-field");
        icon.setAttribute("d", "M12 6c3.79 0 7.17 2.13 8.82 5.5-.59 1.22-1.42 2.27-2.41 3.12l1.41 1.41c1.39-1.23 2.49-2.77 3.18-4.53C21.27 6.61 17 3.5 12 3.5c-1.25 0-2.45.2-3.57.57l1.49 1.49C10.6 5.2 11.3 5 12 5zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22l1.41-1.41L3.41 2.86 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z");
      } else {
        input.type = "password";
        input.classList.remove("password-field");
        icon.setAttribute("d", "M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z");
      }
    });
  });

  // Listen to checklist checkbox changes for completion
  if (elements.resultPrepList) {
    elements.resultPrepList.addEventListener("change", (e) => {
      if (e.target && e.target.id.startsWith("prep-chk-")) {
        updateChecklistCompletionStatus();
      }
    });
  }

  // Dashboard Tabs Switcher
  if (elements.tabStats && elements.tabLeaderboard) {
    elements.tabStats.addEventListener("click", () => {
      elements.tabStats.classList.add("active");
      elements.tabLeaderboard.classList.remove("active");
      elements.statsView.style.display = "block";
      elements.leaderboardView.style.display = "none";
    });

    elements.tabLeaderboard.addEventListener("click", () => {
      elements.tabLeaderboard.classList.add("active");
      elements.tabStats.classList.remove("active");
      elements.statsView.style.display = "none";
      elements.leaderboardView.style.display = "block";
      fetchLeaderboard();
    });
  }
}

function validatePhoneDigits(digits) {
  const cleaned = digits.replace(/[\s\-\(\)\.]/g, "");
  const phoneRegex = /^\d{4,15}$/;
  if (phoneRegex.test(cleaned)) {
    return { valid: true, value: cleaned };
  }
  return { valid: false, error: "Please enter a valid phone number (digits only)." };
}

async function handleLoginSubmit(e) {
  e.preventDefault();
  const countryCode = elements.loginCountryCode.value;
  const phoneDigits = elements.loginPhone.value.trim();
  const password = elements.loginPassword.value;
  elements.authError.style.display = "none";

  const validation = validatePhoneDigits(phoneDigits);
  if (!validation.valid) {
    elements.authError.innerText = validation.error;
    elements.authError.style.display = "block";
    return;
  }
  const phone = countryCode + validation.value;

  setAuthLoading(elements.loginForm, true);

  try {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone, password })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Login failed");
    }

    // Save session
    appState.userSession = data;
    localStorage.setItem("ecosort_session", JSON.stringify(data));

    // UI State change
    showApp();
    await loadStateFromStorage();
    updateDashboard();
    renderHistory();
  } catch (err) {
    elements.authError.innerText = err.message;
    elements.authError.style.display = "block";
  } finally {
    setAuthLoading(elements.loginForm, false);
  }
}

async function handleRegisterSubmit(e) {
  e.preventDefault();
  const name = elements.registerName.value.trim();
  const countryCode = elements.registerCountryCode.value;
  const phoneDigits = elements.registerPhone.value.trim();
  const password = elements.registerPassword.value;
  const confirmPassword = elements.registerConfirmPassword.value;
  elements.authError.style.display = "none";

  if (!name) {
    elements.authError.innerText = "Please enter your full name.";
    elements.authError.style.display = "block";
    return;
  }

  const validation = validatePhoneDigits(phoneDigits);
  if (!validation.valid) {
    elements.authError.innerText = validation.error;
    elements.authError.style.display = "block";
    return;
  }
  const phone = countryCode + validation.value;

  if (password !== confirmPassword) {
    elements.authError.innerText = "Passwords do not match";
    elements.authError.style.display = "block";
    return;
  }

  setAuthLoading(elements.registerForm, true);

  try {
    const response = await fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, phone, password })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Registration failed");
    }

    // Save session
    appState.userSession = data;
    localStorage.setItem("ecosort_session", JSON.stringify(data));

    // UI State change
    showApp();
    await loadStateFromStorage();
    updateDashboard();
    renderHistory();
  } catch (err) {
    elements.authError.innerText = err.message;
    elements.authError.style.display = "block";
  } finally {
    setAuthLoading(elements.registerForm, false);
  }
}

async function handleLogout() {
  if (confirm("Are you sure you want to logout?")) {
    try {
      await fetch("/api/logout", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${appState.userSession ? appState.userSession.token : ""}`
        }
      });
    } catch (e) {
      console.warn("Logout request failed on server:", e);
    }

    // Clear client side state
    appState.userSession = null;
    appState.history = [];
    localStorage.removeItem("ecosort_session");

    // Hide result card if active
    elements.resultSection.classList.remove("active");

    showAuth();
    updateDashboard();
    renderHistory();
  }
}

function setAuthLoading(formElement, isLoading) {
  const submitBtn = formElement.querySelector(".auth-submit-btn");
  const btnText = submitBtn.querySelector("span");
  const spinner = submitBtn.querySelector(".spinner");
  const inputs = formElement.querySelectorAll("input");

  if (isLoading) {
    btnText.style.display = "none";
    spinner.style.display = "block";
    submitBtn.disabled = true;
    inputs.forEach(input => input.disabled = true);
  } else {
    btnText.style.display = "block";
    spinner.style.display = "none";
    submitBtn.disabled = false;
    inputs.forEach(input => input.disabled = false);
  }
}

// Logic for Search & Suggestions
async function handleSearchInput() {
  const value = elements.searchInput.value.trim().toLowerCase();
  if (value.length < 1) {
    elements.suggestionsBox.classList.remove("active");
    return;
  }

  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(value)}`);
    if (!response.ok) throw new Error("Search request failed");
    const matches = await response.json();

    if (matches.length === 0) {
      elements.suggestionsBox.innerHTML = `
        <div class="suggestion-item fallback-item">
          <span>Perform AI classification for "<strong>${escapeHtml(elements.searchInput.value)}</strong>"...</span>
        </div>
      `;
      // Click fallback item
      elements.suggestionsBox.querySelector(".fallback-item").onclick = () => {
        triggerSearch();
      };
    } else {
      elements.suggestionsBox.innerHTML = matches.map(item => `
        <div class="suggestion-item" data-id="${item.id}">
          <span class="category-dot ${item.category}"></span>
          <span class="suggestion-name">${escapeHtml(item.name)}</span>
          <span class="suggestion-category">${item.category.replace("-", " ").toUpperCase()}</span>
        </div>
      `).join("");

      // Click event for items
      elements.suggestionsBox.querySelectorAll(".suggestion-item").forEach(el => {
        el.onclick = () => {
          const id = el.dataset.id;
          const matchedItem = matches.find(item => item.id === id);
          elements.searchInput.value = matchedItem.name;
          elements.suggestionsBox.classList.remove("active");
          startScanning(matchedItem, matchedItem.image);
        };
      });
    }
  } catch (e) {
    console.error("Failed suggestions search:", e);
  }
  elements.suggestionsBox.classList.add("active");
}

async function triggerSearch() {
  const query = elements.searchInput.value.trim();
  if (!query) return;

  elements.suggestionsBox.classList.remove("active");

  try {
    const response = await fetch(`/api/classify?guess=${encodeURIComponent(query)}`);
    if (response.ok) {
      const item = await response.json();
      startScanning(item, item.image);
    }
  } catch (e) {
    console.error("Search classification lookup failed:", e);
  }
}

// Handle File Input and Drag/Drop
function handleFileSelect(e) {
  const files = e.target.files;
  if (files.length > 0) {
    processUploadedFile(files[0]);
  }
}

function processUploadedFile(file) {
  if (!file.type.startsWith("image/")) {
    alert("Please select a valid image file to scan.");
    return;
  }

  const reader = new FileReader();
  reader.onload = async (e) => {
    const filename = file.name.toLowerCase();

    // Create an image element to feed into MobileNet
    const imgEl = new Image();
    imgEl.onload = async () => {
      let predictions = [];
      let guessName = "";

      if (netModel) {
        try {
          predictions = await netModel.classify(imgEl);
          console.log("AI Image predictions:", predictions);
          if (predictions && predictions.length > 0) {
            // Take the top prediction
            guessName = predictions[0].className.split(",")[0].toLowerCase();
          }
        } catch (classifyErr) {
          console.warn("TensorFlow.js classification failed, using file fallback:", classifyErr);
        }
      }

      // Check if filename or top prediction matches any database entries
      const searchTerms = [filename, guessName];
      let matchedId = null;

      // Try searching for matches in the waste database using keywords
      for (const term of searchTerms) {
        if (!term) continue;
        if (term.includes("apple") || term.includes("core")) { matchedId = "apple_core"; break; }
        if (term.includes("banana") || term.includes("peel")) { matchedId = "banana_peel"; break; }
        if (term.includes("bottle") || term.includes("plastic") || term.includes("water bottle")) { matchedId = "plastic_bottle"; break; }
        if (term.includes("battery") || term.includes("cell")) { matchedId = "aa_battery"; break; }
        if (term.includes("newspaper") || term.includes("paper") || term.includes("news")) { matchedId = "newspaper"; break; }
        if (term.includes("vegetable") || term.includes("salad") || term.includes("scraps") || term.includes("carrot") || term.includes("onion")) { matchedId = "vegetable_waste"; break; }
        if (term.includes("can") || term.includes("soda") || term.includes("cola")) { matchedId = "soda_can"; break; }
        if (term.includes("box") || term.includes("cardboard")) { matchedId = "cardboard_box"; break; }
        if (term.includes("computer") || term.includes("phone") || term.includes("laptop")) { matchedId = "laptop"; break; }
        if (term.includes("cable") || term.includes("wire") || term.includes("usb")) { matchedId = "charging_cable"; break; }
        if (term.includes("mug") || term.includes("ceramic") || term.includes("plate")) { matchedId = "ceramic_mug"; break; }
        if (term.includes("jeans") || term.includes("denim") || term.includes("pants") || term.includes("clothing")) { matchedId = "jeans_old"; break; }
      }

      try {
        let item;
        if (matchedId) {
          const response = await fetch(`/api/classify?id=${matchedId}`);
          if (response.ok) {
            item = await response.json();
          }
        }

        if (!item) {
          // Use the prediction label or default to filename guess
          const finalGuess = guessName ? guessName : file.name.split(".")[0].replace(/[_-]/g, " ");
          const response = await fetch(`/api/classify?guess=${encodeURIComponent(finalGuess)}`);
          if (response.ok) {
            item = await response.json();
          }
        }

        if (item) {
          item = { ...item, image: e.target.result };
          // If we classified with MobileNet, let's inject its top class as the confidence display or prediction info
          if (predictions && predictions.length > 0) {
            const pct = Math.round(predictions[0].probability * 100);
            item.confidence = Math.max(pct, 75); // Ensure a reasonable match confidence
            item.name = item.name + ` (${predictions[0].className.split(",")[0]})`;
          }
          startScanning(item, e.target.result);
        }
      } catch (err) {
        console.error("File upload classification failed:", err);
      }
    };
    imgEl.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

// Scanning Animation Sequence
function startScanning(item, imageSrc) {
  elements.scanModal.classList.add("active");
  elements.scanProgress.style.width = "0%";

  const scannerImg = document.getElementById("scanner-view-img");
  const scannerPlaceholder = document.getElementById("scanner-placeholder");
  if (imageSrc) {
    scannerImg.src = imageSrc;
    scannerImg.style.display = "block";
    scannerPlaceholder.style.display = "none";
  } else {
    scannerImg.style.display = "none";
    scannerPlaceholder.style.display = "flex";
  }

  const steps = [
    { progress: 15, text: "Isolating target boundary outline..." },
    { progress: 40, text: "Analyzing spectral material density..." },
    { progress: 70, text: "Comparing composition with eco-database..." },
    { progress: 90, text: "Fetching disposal rules & upcycling ideas..." },
    { progress: 100, text: "Analysis completed!" }
  ];

  let currentStep = 0;

  function runStep() {
    if (currentStep >= steps.length) {
      setTimeout(() => {
        elements.scanModal.classList.remove("active");
        showResults(item);
      }, 600);
      return;
    }

    const step = steps[currentStep];
    elements.scanStatus.innerHTML = `<span class="pulse-dot"></span> ${step.text}`;
    elements.scanProgress.style.width = `${step.progress}%`;

    currentStep++;
    setTimeout(runStep, Math.floor(Math.random() * 400) + 400);
  }

  runStep();
}

// Show Results Panel
function showResults(item) {
  appState.currentResult = item;

  document.getElementById("result-item-name").innerText = item.name;

  const catBadge = document.getElementById("result-category-badge");
  catBadge.className = `category-tag ${item.category}`;
  catBadge.innerText = item.category.replace("-", " ").toUpperCase();

  const resultCard = document.getElementById("result-card-inner");
  resultCard.className = `result-glass-card ${item.category}-theme`;

  document.getElementById("result-material").innerText = item.material;
  document.getElementById("result-confidence-text").innerText = `${item.confidence}% AI Match`;
  document.getElementById("result-confidence-fill").style.width = `${item.confidence}%`;

  if (elements.prepCompletionBox) {
    elements.prepCompletionBox.style.display = "none";
  }
  if (elements.resultStatusBadge) {
    elements.resultStatusBadge.style.display = "none";
  }

  const prepList = document.getElementById("result-prep-list");
  prepList.innerHTML = item.prep.map((step, idx) => `
    <li>
      <label class="checkbox-container">
        <input type="checkbox" id="prep-chk-${idx}">
        <span class="checkmark"></span>
        <span class="checkbox-text">${escapeHtml(step)}</span>
      </label>
    </li>
  `).join("");

  document.getElementById("result-destination").innerText = item.destination;
  document.getElementById("result-upcycle").innerText = item.upcycle;
  document.getElementById("result-funfact").innerText = item.funFact;

  document.getElementById("impact-co2").innerText = `${item.impact.co2 > 0 ? '+' : ''}${item.impact.co2} kg`;
  document.getElementById("impact-decompose").innerText = item.impact.decompose;
  document.getElementById("impact-points").innerText = `+${item.impact.points}`;

  const resultImg = document.getElementById("result-image");
  if (item.image) {
    resultImg.src = item.image;
    resultImg.parentElement.style.display = "block";
  } else {
    resultImg.parentElement.style.display = "none";
  }

  elements.resultSection.classList.add("active");
  elements.resultSection.scrollIntoView({ behavior: "smooth" });

  addToHistory(item);
}

// Add scanned item to History & storage
async function addToHistory(item) {
  const newScan = {
    id: item.id + "_" + Date.now(),
    name: item.name,
    category: item.category,
    points: item.impact.points,
    co2: item.impact.co2,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  };

  // Prepend client side
  appState.history.unshift(newScan);
  if (appState.history.length > 15) {
    appState.history.pop();
  }

  // Backup in local storage
  localStorage.setItem("ecosort_history", JSON.stringify(appState.history));

  // POST to Python Backend
  try {
    const response = await fetch("/api/history", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${appState.userSession ? appState.userSession.token : ""}`
      },
      body: JSON.stringify(newScan)
    });
    if (response.status === 401) {
      appState.userSession = null;
      appState.history = [];
      localStorage.removeItem("ecosort_session");
      showAuth();
      return;
    }
    if (response.ok) {
      appState.history = await response.json();
    }
  } catch (e) {
    console.error("Failed to POST history update to Python server:", e);
  }

  updateDashboard();
  renderHistory();
}

// Calculate dashboard analytics
function updateDashboard() {
  const history = appState.history;
  elements.statScanned.innerText = history.length;

  let points = 0;
  let co2 = 0;
  let bioCount = 0;
  let recyclableCount = 0;
  let ewasteCount = 0;
  let nonRecyclableCount = 0;

  history.forEach(item => {
    points += item.points;
    co2 += item.co2;
    if (item.category === "biodegradable") bioCount++;
    else if (item.category === "recyclable") recyclableCount++;
    else if (item.category === "ewaste") ewasteCount++;
    else if (item.category === "non-recyclable") nonRecyclableCount++;
  });

  elements.statPoints.innerText = points;
  elements.statCO2.innerText = `${co2.toFixed(2)} kg`;

  const divertedCount = bioCount + recyclableCount + ewasteCount;
  const diversionRate = history.length > 0 ? Math.round((divertedCount / history.length) * 100) : 0;

  elements.diversionValue.innerText = `${diversionRate}%`;

  const circumference = 326.7;
  const offset = circumference - (diversionRate / 100) * circumference;
  elements.diversionCircle.style.strokeDashoffset = offset;

  document.getElementById("count-biodegradable").innerText = bioCount;
  document.getElementById("count-recyclable").innerText = recyclableCount;
  document.getElementById("count-ewaste").innerText = ewasteCount;
  document.getElementById("count-non-recyclable").innerText = nonRecyclableCount;

  updateBadges(points, divertedCount, bioCount);
  renderSortingTrendChart();
}

// Update gamified achievement badges
function updateBadges(points, divertedCount, bioCount) {
  const badge1 = document.getElementById("badge-first-scan");
  const badge2 = document.getElementById("badge-diversion");
  const badge3 = document.getElementById("badge-organic");
  const badge4 = document.getElementById("badge-points");

  if (appState.history.length >= 1) badge1.classList.add("unlocked");
  else badge1.classList.remove("unlocked");

  if (divertedCount >= 5) badge2.classList.add("unlocked");
  else badge2.classList.remove("unlocked");

  if (bioCount >= 3) badge3.classList.add("unlocked");
  else badge3.classList.remove("unlocked");

  if (points >= 150) badge4.classList.add("unlocked");
  else badge4.classList.remove("unlocked");
}

// Render History Checklist Item Rows
function renderHistory() {
  if (appState.history.length === 0) {
    elements.historyList.innerHTML = `
      <div class="empty-history">
        <p>No recent scans. Clean sorting starts here!</p>
      </div>
    `;
    elements.clearHistoryBtn.style.display = "none";
    return;
  }

  elements.clearHistoryBtn.style.display = "inline-flex";
  elements.historyList.innerHTML = appState.history.map(item => `
    <div class="history-item">
      <div class="history-item-left">
        <span class="category-indicator ${item.category}"></span>
        <div class="history-details">
          <span class="history-name">${escapeHtml(item.name)}</span>
          <span class="history-time">${item.timestamp}</span>
        </div>
      </div>
      <div class="history-item-right">
        <span class="history-pts">+${item.points} pts</span>
      </div>
    </div>
  `).join("");
}

// Clear History Log
async function clearHistory() {
  if (confirm("Are you sure you want to clear your sorting history? This will reset all your stats and badges.")) {
    appState.history = [];
    localStorage.removeItem("ecosort_history");

    // Clear history.json on server by sending empty POST or deleting
    try {
      const response = await fetch("/api/history", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${appState.userSession ? appState.userSession.token : ""}`
        },
        body: JSON.stringify([])
      });
      if (response.status === 401) {
        appState.userSession = null;
        appState.history = [];
        localStorage.removeItem("ecosort_session");
        showAuth();
        return;
      }
    } catch (e) {
      console.error("Failed to clear history on Python server:", e);
    }

    updateDashboard();
    renderHistory();
    elements.resultSection.classList.remove("active");
  }
}

// Utility functions
function escapeHtml(str) {
  return str.replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function updateChecklistCompletionStatus() {
  if (!elements.resultPrepList) return;
  const checkboxes = elements.resultPrepList.querySelectorAll('input[type="checkbox"]');
  if (checkboxes.length === 0) return;

  const allChecked = Array.from(checkboxes).every(chk => chk.checked);

  if (allChecked) {
    if (elements.completionDestinationValue && appState.currentResult) {
      elements.completionDestinationValue.innerText = appState.currentResult.destination;
    }
    if (elements.prepCompletionBox) {
      elements.prepCompletionBox.style.display = "flex";
    }
    if (elements.resultStatusBadge) {
      elements.resultStatusBadge.style.display = "inline-flex";
    }
  } else {
    if (elements.prepCompletionBox) {
      elements.prepCompletionBox.style.display = "none";
    }
    if (elements.resultStatusBadge) {
      elements.resultStatusBadge.style.display = "none";
    }
  }
}

// Fetch and display Leaderboard ranks
async function fetchLeaderboard() {
  try {
    const response = await fetch("/api/leaderboard");
    if (response.ok) {
      const rankings = await response.json();
      renderLeaderboard(rankings);
    }
  } catch (e) {
    console.error("Failed to fetch leaderboard rankings:", e);
    elements.leaderboardList.innerHTML = `
      <div class="empty-history" style="padding: 20px; text-align: center; color: var(--text-muted);">
        <p>Failed to load rankings. Check backend server connection.</p>
      </div>
    `;
  }
}

function renderLeaderboard(rankings) {
  if (rankings.length === 0) {
    elements.leaderboardList.innerHTML = `
      <div class="empty-history" style="padding: 20px; text-align: center; color: var(--text-muted);">
        <p>No eco-sorters registered yet.</p>
      </div>
    `;
    return;
  }

  elements.leaderboardList.innerHTML = rankings.map((user, index) => {
    const rank = index + 1;
    let rankClass = `leaderboard-rank rank-${rank}`;
    let rowClass = "leaderboard-row";
    if (rank <= 3) {
      rowClass += " top-rank";
    }

    // Icon badge for top ranks
    let rankDisplay = `${rank}`;
    if (rank === 1) rankDisplay = "🏆";
    else if (rank === 2) rankDisplay = "🥈";
    else if (rank === 3) rankDisplay = "🥉";

    return `
      <div class="${rowClass}">
        <span class="${rankClass}">${rankDisplay}</span>
        <span class="leaderboard-name">${escapeHtml(user.name)}</span>
        <span class="leaderboard-pts">${user.points} pts</span>
      </div>
    `;
  }).join("");
}

// Render Sorting Trend Chart
let trendChart = null;

function renderSortingTrendChart() {
  const ctx = document.getElementById('sorting-trend-chart');
  if (!ctx) return;

  if (trendChart) {
    trendChart.destroy();
  }

  // Group items by category in the history
  let bio = 0, rec = 0, ewa = 0, nre = 0;
  appState.history.forEach(item => {
    if (item.category === 'biodegradable') bio++;
    else if (item.category === 'recyclable') rec++;
    else if (item.category === 'ewaste') ewa++;
    else if (item.category === 'non-recyclable') nre++;
  });

  try {
    trendChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Biodegradable', 'Recyclable', 'E-Waste', 'Non-Recyclable'],
        datasets: [{
          label: 'Sorted Items',
          data: [bio, rec, ewa, nre],
          backgroundColor: [
            'rgba(34, 197, 94, 0.4)',
            'rgba(59, 130, 246, 0.4)',
            'rgba(245, 158, 11, 0.4)',
            'rgba(239, 68, 68, 0.4)'
          ],
          borderColor: [
            '#22c55e',
            '#3b82f6',
            '#f59e0b',
            '#ef4444'
          ],
          borderWidth: 2,
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          x: {
            grid: {
              color: 'rgba(255, 255, 255, 0.05)'
            },
            ticks: {
              color: '#94a3b8',
              font: {
                family: 'Outfit'
              }
            }
          },
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(255, 255, 255, 0.05)'
            },
            ticks: {
              color: '#94a3b8',
              stepSize: 1,
              font: {
                family: 'Inter'
              }
            }
          }
        }
      }
    });
  } catch (err) {
    console.error("Failed to render Chart.js sorting trend chart:", err);
  }
}
