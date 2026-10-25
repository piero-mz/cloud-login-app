// Botón para mostrar u ocultar la contraseña
document.querySelectorAll(".ver-clave").forEach((boton) => {
  const input = document.getElementById(boton.getAttribute("aria-controls"));
  boton.addEventListener("click", () => {
    const visible = input.type === "text";
    input.type = visible ? "password" : "text";
    boton.textContent = visible ? "Mostrar" : "Ocultar";
    boton.setAttribute("aria-pressed", String(!visible));
    input.focus();
  });
});
