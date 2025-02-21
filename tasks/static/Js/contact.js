document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('contactForm');
    const messageTextarea = document.getElementById('message');
    const messageCount = document.getElementById('messageCount');

    // Validación del formulario
    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add('was-validated');
    });

    // Validación de nombre en tiempo real
    document.getElementById('name').addEventListener('input', function(e) {
        const nameRegex = /^[A-Za-zÁáÉéÍíÓóÚúÑñ\s]{2,50}$/;
        if (!nameRegex.test(e.target.value)) {
            e.target.setCustomValidity('Nombre inválido');
        } else {
            e.target.setCustomValidity('');
        }
    });

    // Validación de email en tiempo real
    document.getElementById('email').addEventListener('input', function(e) {
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(e.target.value)) {
            e.target.setCustomValidity('Email inválido');
        } else {
            e.target.setCustomValidity('');
        }
    });

    // Contador de caracteres para el mensaje
    messageTextarea.addEventListener('input', function(e) {
        const count = e.target.value.length;
        messageCount.textContent = count;
        
        if (count < 10 || count > 500) {
            e.target.setCustomValidity('El mensaje debe tener entre 10 y 500 caracteres');
        } else {
            e.target.setCustomValidity('');
        }
    });
});
