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

    // Elements for Site Edit Modal
    const editSiteModal = document.getElementById('editSiteModal');
    const editSiteForm = document.getElementById('editSiteForm');
    const editSiteIdInput = document.getElementById('editSiteId');
    const editSiteNameInput = document.getElementById('editSiteName');
    const editSiteDescriptionInput = document.getElementById('editSiteDescription');
    const editSiteAddressInput = document.getElementById('editSiteAddress');
    const editSiteLatitudeInput = document.getElementById('editSiteLatitude');
    const editSiteLongitudeInput = document.getElementById('editSiteLongitude');

    // Elements for Edit Access Point Modal
    const editAccessPointModal = document.getElementById('editAccessPointModal');
    const editAccessPointForm = document.getElementById('editAccessPointForm');
    const editAccessPointIdInput = document.getElementById('editAccessPointId');
    const editAccessPointSiteIdModalInput = document.getElementById('editAccessPointSiteIdModal');
    const editAPPointNumberInput = document.getElementById('editAPPointNumber');
    const editAPNameInput = document.getElementById('editAPName');
    const editAPCoordinatesInput = document.getElementById('editAPCoordinates');
    const editAPDescriptionInput = document.getElementById('editAPDescription');


    async function fetchSites() {
        try {
            const response = await fetchWithAuth('/api/sites');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const sites = await response.json();

            if (sites.length === 0) {
                sitesList.innerHTML = '<h3>Existing Sites:</h3><p>No sites found.</p>';
            } else {
                const ul = document.createElement('ul');
                sites.forEach(site => {
                    const li = document.createElement('li');
                    li.innerHTML = `
                        <strong>ID:</strong> ${site.id}, <strong>Name:</strong> ${site.name}<br>
                        <strong>Address:</strong> ${site.address || 'N/A'}<br>
                        <strong>Lat/Lon:</strong> ${site.latitude !== null ? site.latitude : 'N/A'} / ${site.longitude !== null ? site.longitude : 'N/A'}<br>
                        <strong>Description:</strong> ${site.description || 'No description'}<br>
                        <strong>Registered:</strong> ${site.registration_date ? new Date(site.registration_date).toLocaleDateString() : 'N/A'} by ${site.registered_by_username || 'System/Unknown'}<br>
                        <strong>Access Points:</strong> ${(site.access_points || []).length}
                    `;
                    const editButton = document.createElement('button');
                    editButton.textContent = 'Edit';
                    editButton.className = 'edit-site-btn';
                    editButton.onclick = () => openSiteEditModal(site);

                    li.appendChild(editButton);
                    li.appendChild(document.createElement('hr'));
                    ul.appendChild(li);
                });
                sitesList.innerHTML = '<h3>Existing Sites:</h3>'; // Clear previous content (like "No sites found")
                sitesList.appendChild(ul);
            }

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
            const address = document.getElementById('siteAddress').value; // New field
            const latitude = document.getElementById('siteLatitude').value; // New field
            const longitude = document.getElementById('siteLongitude').value; // New field

            const payload = {
                name,
                description,
                address,
                latitude: latitude ? parseFloat(latitude) : null,
                longitude: longitude ? parseFloat(longitude) : null
            };

            try {
                const response = await fetchWithAuth('/api/sites', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });
                const result = await response.json();
                if (!response.ok) throw new Error(result.message || `HTTP error! status: ${response.status}`);
                alert('Site created: ' + (result.message || 'Success'));
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
        if (!accessPointSiteIdSelect || !accessPointSiteIdSelect.value) {
            if (accessPointsList) accessPointsList.innerHTML = '<p>Select a site first.</p>';
            return;
        }
        const siteId = accessPointSiteIdSelect.value;

        try {
            const response = await fetchWithAuth(`/api/sites/${siteId}/access_points`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const accessPoints = await response.json();

            if (!accessPointsList) return;
            accessPointsList.innerHTML = '';

            if (accessPoints.length === 0) {
                accessPointsList.innerHTML = '<h3>Access Points for Selected Site:</h3><p>No access points found for this site.</p>';
                return;
            }

            const ul = document.createElement('ul');
            accessPoints.forEach(ap => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <strong>Point #${ap.point_number}:</strong> ${ap.name} <br>
                    Coords: ${ap.coordinates || 'N/A'}, Desc: ${ap.description || 'N/A'} <br>
                `;

                const editButton = document.createElement('button');
                editButton.textContent = 'Edit';
                editButton.onclick = () => openEditAccessPointModal(ap);
                li.appendChild(editButton);

                const deleteButton = document.createElement('button');
                deleteButton.textContent = 'Delete';
                deleteButton.onclick = () => deleteAccessPoint(siteId, ap.id);
                li.appendChild(deleteButton);
                li.appendChild(document.createElement('hr'));
                ul.appendChild(li);
            });
            accessPointsList.innerHTML = '<h3>Access Points for Selected Site:</h3>';
            accessPointsList.appendChild(ul);

        } catch (error) {
            if (accessPointsList && error.message !== 'Unauthorized') {
                accessPointsList.innerHTML = `<p class="error">Error loading access points: ${error.message}</p>`;
            }
        }
    }
    if (accessPointSiteIdSelect) accessPointSiteIdSelect.addEventListener('change', fetchAccessPoints);

    if (accessPointForm) {
        accessPointForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const site_id = document.getElementById('accessPointSiteId').value;
            const point_number = document.getElementById('accessPointNumber').value;
            const name = document.getElementById('accessPointName').value;
            const coordinates = document.getElementById('accessPointCoordinates').value;
            const description = document.getElementById('accessPointDescription').value;

            if (!site_id) { alert('Please select a site.'); return; }
            if (!point_number) { alert('Please enter a point number.'); return; }

            const payload = { name, coordinates, description, point_number: parseInt(point_number) };
            try {
                const response = await fetchWithAuth(`/api/sites/${site_id}/access_points`, {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });
                const result = await response.json();
                if (!response.ok) throw new Error(result.message || `HTTP error! status: ${response.status}`);
                alert('Access Point created: ' + (result.message || 'Success'));
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

    // Function to open and pre-fill the site edit modal
    function openSiteEditModal(site) {
        editSiteIdInput.value = site.id;
        editSiteNameInput.value = site.name;
        editSiteDescriptionInput.value = site.description || '';
        editSiteAddressInput.value = site.address || '';
        editSiteLatitudeInput.value = site.latitude !== null ? site.latitude : '';
        editSiteLongitudeInput.value = site.longitude !== null ? site.longitude : '';
        if(editSiteModal) editSiteModal.style.display = 'block';
    }
    // Make it globally accessible if needed by inline onlick, but with dynamic buttons, it's fine in this scope.
    // window.openSiteEditModal = openSiteEditModal; // This was for site edit, not access point.

    // Event listener for the edit site form submission
    if (editSiteForm) { // This is for the SITE edit form
        editSiteForm.addEventListener('submit', async function(event) {
            // ... (existing site edit logic) ...
            event.preventDefault();
            const siteId = editSiteIdInput.value;
            const payload = {
                name: editSiteNameInput.value,
                description: editSiteDescriptionInput.value,
                address: editSiteAddressInput.value,
                latitude: editSiteLatitudeInput.value ? parseFloat(editSiteLatitudeInput.value) : null,
                longitude: editSiteLongitudeInput.value ? parseFloat(editSiteLongitudeInput.value) : null,
            };

            try {
                const response = await fetchWithAuth(`/api/sites/${siteId}`, {
                    method: 'PUT',
                    body: JSON.stringify(payload)
                });
                const result = await response.json();
                if (!response.ok) {
                    throw new Error(result.message || `Error updating site: ${response.status}`);
                }
                alert('Site updated successfully!');
                if(editSiteModal) editSiteModal.style.display = 'none';
                fetchSites(); // Refresh the sites list
            } catch (error) {
                if (error.message !== 'Unauthorized') {
                    alert(`Error: ${error.message}`);
                }
            }
        });
    }

    // Functions for Edit/Delete Access Point
    function openEditAccessPointModal(ap) {
        if(editAccessPointIdInput) editAccessPointIdInput.value = ap.id;
        if(editAccessPointSiteIdModalInput) editAccessPointSiteIdModalInput.value = ap.site_id;
        if(editAPPointNumberInput) editAPPointNumberInput.value = ap.point_number;
        if(editAPNameInput) editAPNameInput.value = ap.name;
        if(editAPCoordinatesInput) editAPCoordinatesInput.value = ap.coordinates || '';
        if(editAPDescriptionInput) editAPDescriptionInput.value = ap.description || '';
        if(editAccessPointModal) editAccessPointModal.style.display = 'block';
    }
    window.openEditAccessPointModal = openEditAccessPointModal;

    if (editAccessPointForm) {
        editAccessPointForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const accessPointId = editAccessPointIdInput.value;
            const siteId = editAccessPointSiteIdModalInput.value;

            const payload = {
                name: editAPNameInput.value,
                coordinates: editAPCoordinatesInput.value,
                description: editAPDescriptionInput.value,
                point_number: parseInt(editAPPointNumberInput.value)
            };

            try {
                const response = await fetchWithAuth(`/api/sites/${siteId}/access_points/${accessPointId}`, {
                    method: 'PUT',
                    body: JSON.stringify(payload)
                });
                const result = await response.json();
                if (!response.ok) {
                    throw new Error(result.message || `Error updating access point: ${response.status}`);
                }
                alert('Access Point updated successfully!');
                if(editAccessPointModal) editAccessPointModal.style.display = 'none';
                fetchAccessPoints();
            } catch (error) {
                if (error.message !== 'Unauthorized') {
                    alert(`Error: ${error.message}`);
                }
            }
        });
    }

    async function deleteAccessPoint(siteId, accessPointId) {
        if (!confirm(`Are you sure you want to delete Access Point ID ${accessPointId}?`)) {
            return;
        }
        try {
            const response = await fetchWithAuth(`/api/sites/${siteId}/access_points/${accessPointId}`, {
                method: 'DELETE'
            });
            if (!response.ok) {
                const result = await response.json().catch(() => ({}));
                throw new Error(result.message || `Error deleting access point: ${response.status}`);
            }
            alert('Access Point deleted successfully!');
            fetchAccessPoints();
        } catch (error) {
            if (error.message !== 'Unauthorized') {
                alert(`Error: ${error.message}`);
            }
        }
    }
    window.deleteAccessPoint = deleteAccessPoint;

    // Geolocation Button Functionality
    const getCreateAPLocationBtn = document.getElementById('getCreateAPLocationBtn');
    const getEditAPLocationBtn = document.getElementById('getEditAPLocationBtn');

    // Input fields for Create Access Point form (already defined or ensure they are)
    const accessPointLatitudeInput = document.getElementById('accessPointLatitude');
    const accessPointLongitudeInput = document.getElementById('accessPointLongitude');

    // editAPLatitudeInput and editAPLongitudeInput are already defined above with other Edit AP Modal elements

    function fillLocationInputs(latitude, longitude, formType) {
        if (formType === 'create') {
            if (accessPointLatitudeInput) accessPointLatitudeInput.value = latitude.toFixed(6);
            if (accessPointLongitudeInput) accessPointLongitudeInput.value = longitude.toFixed(6);
        } else if (formType === 'edit') {
            if (editAPLatitudeInput) editAPLatitudeInput.value = latitude.toFixed(6);
            if (editAPLongitudeInput) editAPLongitudeInput.value = longitude.toFixed(6);
        }
    }

    function handleLocationError(error, formType) {
        let message = "Error getting location: ";
        switch(error.code) {
            case error.PERMISSION_DENIED:
                message += "User denied the request for Geolocation.";
                break;
            case error.POSITION_UNAVAILABLE:
                message += "Location information is unavailable.";
                break;
            case error.TIMEOUT:
                message += "The request to get user location timed out.";
                break;
            case error.UNKNOWN_ERROR:
                message += "An unknown error occurred.";
                break;
        }
        alert(message);
    }

    function getCurrentLocationForAP(formType) {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    fillLocationInputs(position.coords.latitude, position.coords.longitude, formType);
                },
                (error) => {
                    handleLocationError(error, formType);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        } else {
            alert("Geolocation is not supported by this browser.");
        }
    }

    if (getCreateAPLocationBtn) {
        getCreateAPLocationBtn.addEventListener('click', function() {
            getCurrentLocationForAP('create');
        });
    }

    if (getEditAPLocationBtn) {
        getEditAPLocationBtn.addEventListener('click', function() {
            getCurrentLocationForAP('edit');
        });
    }
});
