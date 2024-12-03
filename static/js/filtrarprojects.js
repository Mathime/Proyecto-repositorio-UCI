
function filterProjects() {
    var input = document.getElementById("searchInput"); 
    var filter = input.value.toLowerCase();  
    console.log("Filtro de búsqueda: ", filter);  

    var projects = document.querySelectorAll(".project-item"); 
    console.log("Proyectos encontrados: ", projects.length);  

    projects.forEach(function(project) {
        var projectName = project.getAttribute("data-name");  
        console.log("Nombre del proyecto: ", projectName);  
        if (projectName.indexOf(filter) > -1) {  
            project.style.display = "block";  
            console.log("Proyecto mostrado: ", projectName);
        } else {
            project.style.display = "none";  
            console.log("Proyecto oculto: ", projectName);
        }
    });
}
