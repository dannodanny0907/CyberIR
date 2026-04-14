/* File: users.js - Admin controls for managing user states and creation */
document.addEventListener('DOMContentLoaded', () => {
    const modalOverlay = document.getElementById('userModalOverlay');
    const deleteModalOverlay = document.getElementById('deleteModalOverlay');
    const userForm = document.getElementById('userForm');
    const roleSelect = document.getElementById('role');
    const privGroup = document.getElementById('privilegesGroup');
    const privCheck = document.getElementById('adminPrivileges');
    const modalTitle = document.getElementById('modalTitle');
    const modalError = document.getElementById('modalError');
    const pwInput = document.getElementById('pw');
    const confirmPwInput = document.getElementById('confirmPw');
    const confirmGroup = document.getElementById('confirmPasswordGroup');
    const pwHelp = document.getElementById('pwHelp');
    
    let isEditMode = false;
    let deleteTargetId = null;

    const openModal = () => {
        modalOverlay.style.display = 'flex';
        modalError.style.display = 'none';
        modalError.textContent = '';
    };

    const closeModal = () => {
        modalOverlay.style.display = 'none';
    };

    roleSelect.addEventListener('change', () => {
        if (roleSelect.value === 'Analyst') {
            privGroup.style.display = 'flex';
        } else {
            privGroup.style.display = 'none';
            privCheck.checked = false;
        }
    });

    document.getElementById('addUserBtn').addEventListener('click', () => {
        isEditMode = false;
        userForm.reset();
        document.getElementById('userId').value = '';
        modalTitle.textContent = 'Add New User';
        pwInput.required = true;
        confirmPwInput.required = true;
        confirmGroup.style.display = 'block';
        pwHelp.textContent = 'Minimum 8 characters.';
        roleSelect.disabled = false;
        document.getElementById('email').readOnly = false;
        roleSelect.dispatchEvent(new Event('change'));
        openModal();
    });

    document.querySelectorAll('.editUserBtn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            isEditMode = true;
            userForm.reset();
            const ds = e.target.dataset;
            document.getElementById('userId').value = ds.userId;
            document.getElementById('fullName').value = ds.fullName;
            document.getElementById('email').value = ds.email;
            document.getElementById('phone').value = ds.phone;
            
            if (ds.userId === "1") {
                roleSelect.innerHTML = `<option value="Admin">Admin</option>`;
                roleSelect.value = "Admin";
                roleSelect.disabled = true;
                document.getElementById('email').readOnly = true;
            } else {
                roleSelect.innerHTML = `
                    <option value="Analyst">Analyst</option>
                    <option value="Viewer">Viewer</option>
                `;
                roleSelect.disabled = false;
                document.getElementById('email').readOnly = false;
                roleSelect.value = ds.role;
            }
            
            roleSelect.dispatchEvent(new Event('change'));
            privCheck.checked = (ds.privileges === 'True');
            
            modalTitle.textContent = 'Edit User';
            pwInput.required = false;
            confirmPwInput.required = false;
            confirmGroup.style.display = 'none';
            pwHelp.textContent = 'Leave blank to keep current password.';
            
            openModal();
        });
    });

    userForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const pwd = pwInput.value;
        const confirmPw = confirmPwInput.value;

        if (!isEditMode || pwd !== '') {
            if (pwd.length < 8) {
                modalError.textContent = 'Password must be at least 8 characters.';
                modalError.style.display = 'block';
                return;
            }
            if (!isEditMode && pwd !== confirmPw) {
                modalError.textContent = 'Passwords do not match.';
                modalError.style.display = 'block';
                return;
            }
        }

        const data = {
            full_name: document.getElementById('fullName').value,
            email: document.getElementById('email').value,
            phone_number: document.getElementById('phone').value,
            role: roleSelect.disabled ? "Admin" : roleSelect.value,
            has_admin_privileges: privCheck.checked,
            password: pwd,
            confirm_password: confirmPw
        };

        const userId = document.getElementById('userId').value;
        const url = isEditMode ? `/users/edit/${userId}` : '/users/add';

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            
            if (result.success) {
                window.location.reload();
            } else {
                modalError.textContent = result.message;
                modalError.style.display = 'block';
            }
        } catch (error) {
            modalError.textContent = 'An error occurred server-side.';
            modalError.style.display = 'block';
        }
    });

    // Close Modal Events
    document.getElementById('modalClose').addEventListener('click', closeModal);
    document.getElementById('modalCancel').addEventListener('click', closeModal);
    
    // Toggle Status
    document.querySelectorAll('.toggleBtn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const userId = e.target.dataset.userId;
            try {
                const response = await fetch(`/users/toggle-status/${userId}`, { method: 'POST' });
                const result = await response.json();
                if (result.success) {
                    window.location.reload();
                } else {
                    alert(result.message);
                }
            } catch (err) {
                alert('Toggling status failed.');
            }
        });
    });

    // Delete Modal
    document.querySelectorAll('.deleteBtn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            deleteTargetId = e.target.dataset.userId;
            document.getElementById('deleteUserName').textContent = e.target.dataset.userName;
            deleteModalOverlay.style.display = 'flex';
        });
    });

    const closeDeleteModal = () => {
        deleteModalOverlay.style.display = 'none';
        deleteTargetId = null;
    };

    document.getElementById('deleteModalClose').addEventListener('click', closeDeleteModal);
    document.getElementById('deleteModalCancel').addEventListener('click', closeDeleteModal);

    document.getElementById('deleteModalConfirm').addEventListener('click', async () => {
        if (!deleteTargetId) return;
        try {
            const response = await fetch(`/users/delete/${deleteTargetId}`, { method: 'POST' });
            const result = await response.json();
            if (result.success) {
                window.location.reload();
            } else {
                alert(result.message);
                closeDeleteModal();
            }
        } catch (err) {
            alert('Delete failed.');
            closeDeleteModal();
        }
    });

    // Outer click to close modals
    window.addEventListener('click', (e) => {
        if (e.target === modalOverlay) closeModal();
        if (e.target === deleteModalOverlay) closeDeleteModal();
    });

    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
            closeDeleteModal();
        }
    });
});
