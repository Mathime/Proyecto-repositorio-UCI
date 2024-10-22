document.getElementById('rol-select').addEventListener('change', function () {
    var matriculaField = document.getElementById('matricula-field');
    var matriculaInput = matriculaField.querySelector('input[name="matricula"]');

    if (this.value === 'Docente') {
        matriculaField.style.display = 'none';  // Oculta el campo de matrícula
        matriculaInput.removeAttribute('required');  // Elimina el "required" para Docentes
    } else {
        matriculaField.style.display = 'block';  // Muestra el campo de matrícula
        matriculaInput.setAttribute('required', 'true');  // Añade el "required" para Estudiantes
    }
});
