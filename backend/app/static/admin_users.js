document.addEventListener('DOMContentLoaded', function() {
    // Client-side role check
    const userRole = getUserRole(); // From script.js
    if (!['admin', 'dba'].includes(userRole)) {
        document.body.innerHTML = '<h1>Access Denied</h1><p>You do not have permission to view this page.</p><p><a href="/">Go Home</a></p>';
        return;
    }

    const usersTableBody = document.querySelector('#usersTable tbody');
    const editUserModal = document.getElementById('editUserModal');
    const editUserForm = document.getElementById('editUserForm');
    const editUserIdInput = document.getElementById('editUserId');
    const editUsernameInput = document.getElementById('editUsername');
    const editUserRoleSelect = document.getElementById('editUserRole');

    async function fetchUsers() {
        try {
            const response = await fetchWithAuth('/api/users'); // Uses GET /api/users
            if (!response.ok) {
                throw new Error(`Failed to fetch users: ${response.status}`);
            }
            const users = await response.json();
            populateUsersTable(users);
        } catch (error) {
            if (error.message !== 'Unauthorized') { // fetchWithAuth handles this
                usersTableBody.innerHTML = `<tr><td colspan="5" class="error">Error loading users: ${error.message}</td></tr>`;
            }
        }
    }

    function populateUsersTable(users) {
        usersTableBody.innerHTML = ''; // Clear existing rows
        if (users.length === 0) {
            usersTableBody.innerHTML = '<tr><td colspan="5">No users found.</td></tr>';
            return;
        }

        users.forEach(user => {
            const row = usersTableBody.insertRow();
            row.insertCell().textContent = user.id;
            row.insertCell().textContent = user.username;
            row.insertCell().textContent = user.role;
            row.insertCell().textContent = user.is_active ? 'Active' : 'Disabled';

            const actionsCell = row.insertCell();
            const editButton = document.createElement('button');
            editButton.textContent = 'Edit';
            editButton.onclick = () => openEditModal(user);
            actionsCell.appendChild(editButton);

            const toggleStatusButton = document.createElement('button');
            toggleStatusButton.textContent = user.is_active ? 'Disable' : 'Enable';
            toggleStatusButton.onclick = () => toggleUserStatus(user.id, !user.is_active);
            actionsCell.appendChild(toggleStatusButton);
        });
    }

    function openEditModal(user) {
        editUserIdInput.value = user.id;
        editUsernameInput.value = user.username;
        editUserRoleSelect.value = user.role; // Assumes role names in select match API response
        editUserModal.style.display = 'block';
    }

    editUserForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const userId = editUserIdInput.value;
        const username = editUsernameInput.value;
        const role = editUserRoleSelect.value;

        const payload = { username, role };

        try {
            const response = await fetchWithAuth(`/api/users/${userId}`, {
                method: 'PUT',
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.message || `Error updating user: ${response.status}`);
            }
            alert('User updated successfully!');
            editUserModal.style.display = 'none';
            fetchUsers(); // Refresh table
        } catch (error) {
             if (error.message !== 'Unauthorized') {
                alert(`Error: ${error.message}`);
            }
        }
    });

    async function toggleUserStatus(userId, newStatus) {
        const action = newStatus ? 'enable' : 'disable';
        if (!confirm(`Are you sure you want to ${action} this user?`)) {
            return;
        }
        try {
            const response = await fetchWithAuth(`/api/users/${userId}`, {
                method: 'PUT',
                body: JSON.stringify({ is_active: newStatus })
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.message || `Error updating user status: ${response.status}`);
            }
            alert(`User ${action}d successfully!`);
            fetchUsers(); // Refresh table
        } catch (error) {
            if (error.message !== 'Unauthorized') {
                alert(`Error: ${error.message}`);
            }
        }
    }

    fetchUsers(); // Initial load
});
