document.addEventListener("DOMContentLoaded", function() {
    setTimeout(function() {
        const alert = document.querySelector('.alert-success');
        if (alert) {
            alert.style.display = 'none';
        }
    }, 3000); // 3 segundos
});
