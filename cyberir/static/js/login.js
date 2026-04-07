document.addEventListener('DOMContentLoaded', () => {
    const passwordInput = document.getElementById('password');
    const togglePasswordBtn = document.getElementById('togglePassword');
    const toggleIcon = document.getElementById('toggleIcon');
    const loginForm = document.getElementById('loginForm');
    const submitBtn = document.getElementById('submitBtn');
    const errorBox = document.getElementById('errorBox');
    const emailInput = document.getElementById('email');

    // Show/hide password
    if (togglePasswordBtn) {
        togglePasswordBtn.addEventListener('click', () => {
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                toggleIcon.textContent = '●';
            } else {
                passwordInput.type = 'password';
                toggleIcon.textContent = '▼';
            }
        });
    }

    // Prevent double submission
    if (loginForm) {
        loginForm.addEventListener('submit', () => {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Signing in...';
        });
    }

    // Clear error message when user starts typing
    const clearError = () => {
        if (errorBox) {
            errorBox.style.display = 'none';
        }
    };

    if (emailInput) {
        emailInput.addEventListener('input', clearError);
    }
    
    if (passwordInput) {
        passwordInput.addEventListener('input', clearError);
    }
});
