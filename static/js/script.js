console.log("3D Conceptualization application loaded");

document.addEventListener('DOMContentLoaded', () => {
    const nameInput = document.getElementById('username');
    const continueBtn = document.getElementById('continueBtn');

    nameInput.addEventListener('input', () => {
        continueBtn.disabled = nameInput.value.trim() === '';
    });
});
