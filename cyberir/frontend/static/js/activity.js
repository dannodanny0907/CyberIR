document.addEventListener('DOMContentLoaded', () => {
    // Optional: add basic client-side filtering if user wants a search feature later
    // For now we just implement the dropdown click stub to match UI
    const dropdown = document.querySelector('.filter-dropdown');
    
    if (dropdown) {
        dropdown.addEventListener('click', () => {
            console.log('Filter dropdown clicked');
            // Logic for showing a filter menu could go here
        });
    }

    // Optional: Make the back arrow navigate back to dashboard
    const backArrow = document.querySelector('.activity-title');
    if (backArrow) {
        backArrow.addEventListener('click', () => {
            window.location.href = '/dashboard';
        });
    }
});
