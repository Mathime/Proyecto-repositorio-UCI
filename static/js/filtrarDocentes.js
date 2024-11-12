function filtrarDocentes() {
    const input = document.getElementById("buscarDocente");
    const filter = input.value.toLowerCase();
    const table = document.getElementById("tablaDocentes");
    const tr = table.getElementsByTagName("tr");

    for (let i = 1; i < tr.length; i++) {
        let td = tr[i].getElementsByTagName("td");
        let mostrar = false;
        for (let j = 0; j < td.length; j++) {
            if (td[j] && td[j].innerText.toLowerCase().includes(filter)) {
                mostrar = true;
                break;
            }
        }
        tr[i].style.display = mostrar ? "" : "none";
    }
}
