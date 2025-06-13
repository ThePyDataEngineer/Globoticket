// Globoticket/static/js/script.js

document.addEventListener('DOMContentLoaded', () => {
    // Asegura que el DOM esté completamente cargado antes de ejecutar el script

    const cityInput = document.getElementById('cityInput');
    const searchButton = document.getElementById('searchButton');
    const eventList = document.getElementById('eventList');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessageDiv = document.getElementById('errorMessage');

    // Función para mostrar el indicador de carga
    const showLoading = () => {
        loadingIndicator.style.display = 'block';
        errorMessageDiv.style.display = 'none'; // Ocultar mensajes de error previos
        eventList.innerHTML = ''; // Limpiar resultados anteriores
    };

    // Función para ocultar el indicador de carga
    const hideLoading = () => {
        loadingIndicator.style.display = 'none';
    };

    // Función para mostrar mensajes de error
    const showError = (message) => {
        hideLoading(); // Ocultar carga si estaba visible
        errorMessageDiv.textContent = message;
        errorMessageDiv.style.display = 'block';
        eventList.innerHTML = ''; // Asegurar que no haya resultados si hay error
    };

    // Función para renderizar los eventos en la lista
    const renderEvents = (events) => {
        hideLoading();
        errorMessageDiv.style.display = 'none'; // Ocultar mensajes de error previos
        eventList.innerHTML = ''; // Limpiar resultados anteriores antes de añadir nuevos

        if (!events || events.length === 0) {
            // Esto puede ser manejado por el backend o aquí si el backend devuelve un array vacío
            // El backend ya devuelve un mensaje para "No se encontraron eventos" con un status 200,
            // pero podríamos tener un manejo específico aquí si la respuesta es un array vacío.
            // Por ahora, asumimos que el backend maneja el mensaje de "no encontrados".
            // Si el backend devuelve un array vacío y status 200, podríamos mostrar "No hay eventos para mostrar."
            // Sin embargo, si el backend devuelve un objeto con "message", eso se manejará como error/info.
            errorMessageDiv.textContent = 'No se encontraron eventos para la ciudad especificada.';
            errorMessageDiv.style.display = 'block';
            return;
        }

        events.forEach(event => {
            const listItem = document.createElement('li');

            // Contenedor para la imagen
            const imageContainer = document.createElement('div');
            imageContainer.classList.add('event-image-container'); // Para posible estilizado
            const img = document.createElement('img');
            img.src = event.imageUrl || 'https://via.placeholder.com/150x100?text=No+Image'; // Placeholder si no hay imagen
            img.alt = event.name || 'Imagen del evento';
            imageContainer.appendChild(img);

            // Contenedor para los detalles del evento
            const detailsContainer = document.createElement('div');
            detailsContainer.classList.add('event-details');

            const eventName = document.createElement('h3');
            eventName.textContent = event.name || 'Nombre no disponible';

            const eventDateTime = document.createElement('p');
            eventDateTime.innerHTML = `<strong>Fecha y Hora:</strong> ${event.dateTime || 'No especificada'}`;

            const eventVenue = document.createElement('p');
            eventVenue.innerHTML = `<strong>Lugar:</strong> ${event.venue || 'No especificado'}`;
            
            detailsContainer.appendChild(eventName);
            detailsContainer.appendChild(eventDateTime);
            detailsContainer.appendChild(eventVenue);

            if (event.url && event.url !== '#') {
                const eventLink = document.createElement('a');
                eventLink.href = event.url;
                eventLink.textContent = 'Más Información / Comprar Entradas';
                eventLink.target = '_blank'; // Abrir en nueva pestaña
                eventLink.rel = 'noopener noreferrer';
                detailsContainer.appendChild(eventLink);
            }

            listItem.appendChild(imageContainer);
            listItem.appendChild(detailsContainer);
            eventList.appendChild(listItem);
        });
    };

    // Event listener para el botón de búsqueda
    searchButton.addEventListener('click', async () => {
        const city = cityInput.value.trim();

        if (!city) {
            showError('Por favor, ingrese el nombre de una ciudad.');
            cityInput.focus(); // Poner foco en el input
            return;
        }

        showLoading();

        try {
            // Construir la URL del backend. Asegurarse que el puerto coincida con el de Flask.
            // Si Flask corre en localhost:5000, la URL base para la API es http://localhost:5000
            // El endpoint es /api/events
            const response = await fetch(`/api/events?city=${encodeURIComponent(city)}`);

            if (!response.ok) {
                // Si la respuesta del backend NO es ok (ej. 400, 404, 500)
                const errorData = await response.json().catch(() => null); // Intentar parsear el JSON del error
                const detail = errorData && errorData.error ? errorData.error : `Error del servidor: ${response.status} ${response.statusText}`;
                throw new Error(detail);
            }

            const data = await response.json();

            // Verificar si 'data' es un array (lista de eventos) o un objeto con un mensaje (ej. "No se encontraron eventos")
            if (Array.isArray(data)) {
                renderEvents(data);
            } else if (data && data.message) { // Caso donde el backend envía un mensaje (ej. "No se encontraron eventos")
                hideLoading();
                errorMessageDiv.textContent = data.message;
                errorMessageDiv.style.display = 'block';
                eventList.innerHTML = '';
            } else {
                // Respuesta inesperada del backend que no es un array ni un objeto con 'message'
                throw new Error('Respuesta inesperada del servidor.');
            }

        } catch (error) {
            console.error('Error al obtener eventos:', error);
            showError(`Ocurrió un error: ${error.message}`);
        }
    });

    // Opcional: permitir búsqueda al presionar Enter en el campo de texto
    cityInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault(); // Prevenir el comportamiento por defecto de Enter en un form (si lo hubiera)
            searchButton.click(); // Simular clic en el botón de búsqueda
        }
    });

});