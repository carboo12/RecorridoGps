// backend/app/static/script.js
console.log("Main script.js loaded.");

function getAuthToken() {
    return localStorage.getItem('authToken');
}

function getUserId() {
    return localStorage.getItem('userId');
}

function getUserRole() {
    return localStorage.getItem('userRole');
}

function clearAuthData() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userId');
    localStorage.removeItem('userRole');
}

async function fetchWithAuth(url, options = {}) {
    const token = getAuthToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };
    if (token) {
        headers['x-access-token'] = token;
    }

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) { // Unauthorized or Token expired
        clearAuthData();
        alert('Session expired or invalid. Please login again.');
        window.location.href = '/login'; // Redirect to login
        throw new Error('Unauthorized'); // Prevent further processing
    }
    return response;
}

function logout() {
    clearAuthData();
    window.location.href = '/login';
}

// Basic UI update based on login status for shared elements (e.g., nav)
document.addEventListener('DOMContentLoaded', function() {
    const loginLink = document.getElementById('nav-login');
    const logoutLink = document.getElementById('nav-logout');
    const adminLink = document.getElementById('nav-admin'); // Assuming an id="nav-admin" on the admin nav link
    const roundsLink = document.getElementById('nav-rounds'); // Assuming id="nav-rounds"
    const signupLink = document.getElementById('nav-signup'); // Assuming id="nav-signup"
    const welcomeMsg = document.getElementById('welcome-message'); // For user greeting

    if (getAuthToken()) {
        if (loginLink) loginLink.style.display = 'none';
        if (signupLink) signupLink.style.display = 'none';
        if (logoutLink) logoutLink.style.display = 'inline'; // Show logout

        const userRole = getUserRole();
        if (adminLink && !['admin', 'dba', 'supervisor'].includes(userRole)) {
            adminLink.style.display = 'none'; // Hide admin link for non-privileged users
        }
         if (welcomeMsg && getUserId()) { // Assuming username is not stored, use ID or generic msg
            welcomeMsg.textContent = `Welcome, User ${getUserId()} (${userRole})!`;
        }

    } else {
        if (loginLink) loginLink.style.display = 'inline';
        if (signupLink) signupLink.style.display = 'inline';
        if (logoutLink) logoutLink.style.display = 'none';
        if (adminLink) adminLink.style.display = 'none'; // Hide admin if not logged in
        if (roundsLink) roundsLink.style.display = 'none'; // Hide rounds if not logged in
         if (welcomeMsg) welcomeMsg.textContent = 'Please log in.';
    }

    // Attach logout to button if it exists (now handled by onclick in nav directly)
    // const logoutButton = document.getElementById('logoutButton');
    // if (logoutButton) {
    //     logoutButton.addEventListener('click', logout);
    // }
});
