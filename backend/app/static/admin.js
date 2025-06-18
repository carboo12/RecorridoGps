// backend/app/static/admin.js
document.addEventListener('DOMContentLoaded', async function() {
    // Role check for admin page access (client-side, backend enforces actual API calls)
    const userRole = getUserRole(); // from script.js
    if (!['admin', 'dba', 'supervisor'].includes(userRole)) {
        document.body.innerHTML = '<h1>Access Denied</h1><p>You do not have permission to view this page.</p><p><a href="/">Go Home</a></p>';
        // Attempt to load script.js for logout function if possible, or just offer home link
        const scriptTag = document.createElement('script');
        scriptTag.src = "{{ url_for('static', filename='script.js') }}"; // This won't work directly in static JS
        // A better approach for non-Flask static JS is to assume script.js is loaded if this script runs
        // Or provide a direct logout link if possible: <a href="#" onclick="logout()">Logout (if script.js is loaded)</a>
        return;
    }

    const siteForm = document.getElementById('siteForm');
    const sitesList = document.getElementById('sitesList');
    const siteCoordinatesInput = document.getElementById('siteCoordinates');

    const checkpointForm = document.getElementById('checkpointForm');
    const checkpointsList = document.getElementById('checkpointsList');
    const checkpointSiteIdSelect = document.getElementById('checkpointSiteId');

    const accessPointForm = document.getElementById('accessPointForm');
    const accessPointsList = document.getElementById('accessPointsList');
    const accessPointSiteIdSelect = document.getElementById('accessPointSiteId');
    const accessPointDescriptionInput = document.getElementById('accessPointDescription');


    async function fetchSites() {
        try {
            const response = await fetchWithAuth('/api/sites');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const sites = await response.json();

            sitesList.innerHTML = '<h3>Existing Sites:</h3><ul>' +
                sites.map(site => `<li>ID: ${site.id}, Name: ${site.name}, Coord: ${site.coordinates || 'N/A'} (${site.description || 'No desc.'}) (${(site.access_points || []).length} access points)</li>`).join('') +
                '</ul>';

            const siteOptions = sites.map(site => `<option value="${site.id}">${site.name}</option>`).join('');
            if(checkpointSiteIdSelect) checkpointSiteIdSelect.innerHTML = siteOptions;
            if (accessPointSiteIdSelect) accessPointSiteIdSelect.innerHTML = siteOptions;

            if (sites.length > 0) {
                if(checkpointSiteIdSelect && checkpointSiteIdSelect.value) fetchCheckpoints();
                if (accessPointSiteIdSelect && accessPointSiteIdSelect.value) fetchAccessPoints();
            } else {
                if(checkpointsList) checkpointsList.innerHTML = "<p>No sites available. Create a site first.</p>";
                if (accessPointsList) accessPointsList.innerHTML = "<p>No sites available. Create a site first.</p>";
            }
        } catch (error) {
            if (error.message !== 'Unauthorized') {
                sitesList.innerHTML = `<p class="error">Error loading sites: ${error.message}</p>`;
            }
        }
    }

    if (siteForm) {
        siteForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const name = document.getElementById('siteName').value;
            const description = document.getElementById('siteDescription').value;
            const coordinates = siteCoordinatesInput.value;
            try {
                const response = await fetchWithAuth('/api/sites', {
                    method: 'POST',
                    body: JSON.stringify({ name, description, coordinates })
                });
                const result = await response.json();
                if (!response.ok) throw new Error(result.message || `HTTP error! status: ${response.status}`);
                alert('Site created: ' + result.message);
                siteForm.reset();
                fetchSites();
            } catch (error) {
                 if (error.message !== 'Unauthorized') {
                    alert('Error creating site: ' + error.message);
                }
            }
        });
    }

    async function fetchCheckpoints() {
        if(!checkpointSiteIdSelect) return;
        const siteId = checkpointSiteIdSelect.value;
        if (!siteId) {
            if(checkpointsList) checkpointsList.innerHTML = '<p>Select a site to see its checkpoints.</p>';
            return;
        }
        try {
            const response = await fetchWithAuth(`/api/sites/${siteId}/checkpoints`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const checkpoints = await response.json();
            if(checkpointsList) checkpointsList.innerHTML = '<h3>Checkpoints for Selected Site:</h3><ul>' +
                checkpoints.map(cp => `<li>ID: ${cp.id}, Name: ${cp.name} (${cp.description || 'No description'})</li>`).join('') +
                '</ul>';
            if (checkpoints.length === 0 && checkpointsList) {
                 checkpointsList.innerHTML += '<p>No checkpoints found for this site.</p>';
            }
        } catch (error) { // Corrected syntax error here
             if (error.message !== 'Unauthorized') {
                if(checkpointsList) checkpointsList.innerHTML = `<p class="error">Error loading checkpoints: ${error.message}</p>`;
            }
        }
    }
    if (checkpointSiteIdSelect) checkpointSiteIdSelect.addEventListener('change', fetchCheckpoints);

    if (checkpointForm) {
        checkpointForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const site_id = checkpointSiteIdSelect.value;
            const name = document.getElementById('checkpointName').value;
            const description = document.getElementById('checkpointDescription').value;
            if (!site_id) { alert('Please select a site.'); return; }
            try {
                const response = await fetchWithAuth(`/api/sites/${site_id}/checkpoints`, {
                    method: 'POST',
                    body: JSON.stringify({ name, description })
                });
                const result = await response.json();
                if (!response.ok) throw new Error(result.message || `HTTP error! status: ${response.status}`);
                alert('Checkpoint created: ' + result.message);
                checkpointForm.reset();
                fetchCheckpoints();
            } catch (error) {
                if (error.message !== 'Unauthorized') {
                    alert('Error creating checkpoint: ' + error.message);
                }
            }
        });
    }

    async function fetchAccessPoints() {
        if (!accessPointSiteIdSelect) return;
        const siteId = accessPointSiteIdSelect.value;
        if (!siteId) {
            if (accessPointsList) accessPointsList.innerHTML = '<p>Select a site to see access points.</p>';
            return;
        }
        try {
            const response = await fetchWithAuth(`/api/sites/${siteId}/access_points`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const accessPoints = await response.json();
            if (accessPointsList) accessPointsList.innerHTML = '<h3>Access Points for Selected Site:</h3><ul>' +
                accessPoints.map(ap => `<li>ID: ${ap.id}, Name: ${ap.name}, Coords: ${ap.coordinates} (${ap.description || 'No desc.'})</li>`).join('') +
                '</ul>';
            if (accessPoints.length === 0 && accessPointsList) {
                 accessPointsList.innerHTML += '<p>No access points found for this site.</p>';
            }
        } catch (error) {
             if (error.message !== 'Unauthorized') {
                if (accessPointsList) accessPointsList.innerHTML = `<p class="error">Error loading access points: ${error.message}</p>`;
            }
        }
    }
    if (accessPointSiteIdSelect) accessPointSiteIdSelect.addEventListener('change', fetchAccessPoints);

    if (accessPointForm) {
        accessPointForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const site_id = accessPointSiteIdSelect.value;
            const name = document.getElementById('accessPointName').value;
            const coordinates = document.getElementById('accessPointCoordinates').value;
            const description = accessPointDescriptionInput ? accessPointDescriptionInput.value : '';
            if (!site_id) { alert('Please select a site.'); return; }
            try {
                const response = await fetchWithAuth(`/api/sites/${site_id}/access_points`, {
                    method: 'POST',
                    body: JSON.stringify({ name, coordinates, description })
                });
                const result = await response.json();
                if (!response.ok) throw new Error(result.message || `HTTP error! status: ${response.status}`);
                alert('Access Point created: ' + result.message);
                accessPointForm.reset();
                fetchAccessPoints();
            } catch (error) {
                if (error.message !== 'Unauthorized') {
                    alert('Error creating access point: ' + error.message);
                }
            }
        });
    }

    await fetchSites();
});
