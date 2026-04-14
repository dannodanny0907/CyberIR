/* File: login.js - Authentication form validation */
document.addEventListener('DOMContentLoaded', () => {
    // Show/hide password
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');
    
    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', () => {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            // using text toggle or eye emoji
            if (type === 'password') {
                togglePassword.innerText = '▼';
            } else {
                togglePassword.innerText = '●';
            }
        });
    }

    // Auto-focus email field on load
    const emailInput = document.getElementById('email');
    if (emailInput) {
        emailInput.focus();
    }

    // Clear error message when user starts typing
    const inputs = document.querySelectorAll('input');
    const errorBox = document.querySelector('.error-box');

    inputs.forEach(input => {
        input.addEventListener('input', () => {
            if (errorBox) {
                errorBox.style.display = 'none';
            }
        });
    });

    // Prevent double-click form submission
    const loginForm = document.getElementById('loginForm');
    const submitBtn = document.getElementById('submitBtn');

    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            // Check if form is valid first before disabling
            if (loginForm.checkValidity()) {
                submitBtn.disabled = true;
                submitBtn.innerText = 'Signing in...';
            }
        });
    }
});
