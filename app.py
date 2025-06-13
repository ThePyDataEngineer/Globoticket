# Globoticket/app.py

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv # Para cargar variables desde el archivo .env


# --- Ruta para servir la página principal del frontend ---
@app.route('/')
def index():
    """Sirve la página principal index.html."""
    return render_template('index.html')


# --- Inicio: Depuración de Carga de Variable de Entorno ---
# Determinar la ruta absoluta al archivo .env que debería estar en el mismo directorio que app.py
# __file__ es la ruta al script actual (app.py)
# os.path.dirname(__file__) es el directorio donde reside app.py
# os.path.join une las partes para formar una ruta completa al archivo .env
env_path_debug = os.path.join(os.path.dirname(__file__), '.env')

print(f"DEBUG: Ruta absoluta del script (app.py): {os.path.abspath(__file__)}")
print(f"DEBUG: Directorio del script (donde se busca .env): {os.path.abspath(os.path.dirname(__file__))}")
print(f"DEBUG: Ruta completa esperada para .env: {env_path_debug}")

# Verificar si el archivo .env existe en la ruta calculada
if os.path.exists(env_path_debug):
    print(f"DEBUG: Archivo .env ENCONTRADO en: {env_path_debug}")
    # Cargar el archivo .env.
    # verbose=True: mostrará información en consola sobre qué variables se cargan.
    # override=True: si la variable ya existe en el entorno, la del .env la reemplazará. Útil para asegurar que se usa la del .env.
    loaded_correctly = load_dotenv(dotenv_path=env_path_debug, verbose=True, override=True)
    if loaded_correctly:
        print("DEBUG: load_dotenv() reportó éxito al cargar .env.")
    else:
        # Esto puede ocurrir si .env está vacío o solo tiene comentarios, o si load_dotenv() no lo procesa por alguna razón.
        print("DEBUG: load_dotenv() reportó que NO se cargó .env (podría estar vacío o tener problemas).")
else:
    print(f"DEBUG: Archivo .env NO ENCONTRADO en la ruta: {env_path_debug}")

# Ahora, intentar obtener la variable de entorno después del intento de carga
# Esta es la forma estándar de obtener la variable, ya sea que provenga del entorno del sistema o de .env
TICKETMASTER_API_KEY_FROM_ENV = os.getenv('TICKETMASTER_API_KEY')

# Imprimir el valor obtenido para verificar
print(f"DEBUG: Valor obtenido para TICKETMASTER_API_KEY (vía os.getenv): '{TICKETMASTER_API_KEY_FROM_ENV}'") # Comillas para ver si es None o string vacío

# Asignar a la variable que usará la aplicación
TICKETMASTER_API_KEY = TICKETMASTER_API_KEY_FROM_ENV
# --- Fin: Depuración de Carga de Variable de Entorno ---


# --- Configuración Inicial de la Aplicación Flask ---
app = Flask(__name__)
# Habilita CORS para todas las rutas. Para producción, restringir a orígenes específicos.
CORS(app, resources={r"/api/*": {"origins": "*"}}) # Permitir todos los orígenes por ahora para simplificar pruebas

# Advertencia si, después de todos los intentos, la API Key no está disponible
if not TICKETMASTER_API_KEY:
    print("¡ADVERTENCIA CRÍTICA! La variable TICKETMASTER_API_KEY NO está configurada después de los intentos de carga.")
    # Considerar salir si es crítico para la operación, o manejarlo en el endpoint.
    # exit("Error: API Key de Ticketmaster es indispensable y no fue encontrada.")


# --- Constantes de la API de Ticketmaster ---
TICKETMASTER_API_URL_BASE = "https://app.ticketmaster.com/discovery/v2/events.json"


# --- Definición del Endpoint de la API ---
@app.route('/api/events', methods=['GET'])
def get_events():
    """
    Endpoint para obtener eventos de Ticketmaster basados en una ciudad.
    Espera un parámetro de consulta 'city'.
    Ejemplo: /api/events?city=London
    """
    city_name = request.args.get('city')

    if not city_name:
        return jsonify({"error": "El parámetro 'city' es requerido."}), 400

    # Verificar si la API Key está disponible ANTES de intentar usarla
    if not TICKETMASTER_API_KEY:
        app.logger.error("Intento de llamar a Ticketmaster API sin API Key configurada.")
        return jsonify({"error": "Configuración del servidor incorrecta: API Key de Ticketmaster no disponible."}), 500

    params = {
        'apikey': TICKETMASTER_API_KEY,
        'city': city_name,
        'size': 20,
        'sort': 'date,asc',
        # 'countryCode': 'US' # Descomentar y ajustar si se quiere limitar a un país
    }

    app.logger.info(f"Realizando solicitud a Ticketmaster para la ciudad: {city_name} con API Key: ...{TICKETMASTER_API_KEY[-4:] if TICKETMASTER_API_KEY and len(TICKETMASTER_API_KEY) > 4 else ' (clave no mostrable)'}") # Log sin mostrar toda la clave

    try:
        response = requests.get(TICKETMASTER_API_URL_BASE, params=params, timeout=10) # Añadido timeout
        response.raise_for_status()
        data = response.json()
        
        events_list = []
        if '_embedded' in data and 'events' in data['_embedded']:
            for event_data in data['_embedded']['events']:
                name = event_data.get('name', 'Nombre no disponible')
                
                start_info = event_data.get('dates', {}).get('start', {})
                local_date = start_info.get('localDate', 'Fecha no disponible')
                local_time = start_info.get('localTime', '')
                date_time_str = f"{local_date} {local_time}".strip()

                venue_name = 'Lugar no disponible'
                event_embedded_venues = event_data.get('_embedded', {}).get('venues')
                if event_embedded_venues and isinstance(event_embedded_venues, list) and len(event_embedded_venues) > 0:
                    venue_name = event_embedded_venues[0].get('name', 'Lugar no disponible')
                
                url = event_data.get('url', '#')
                
                image_url = 'URL de imagen no disponible'
                images_list = event_data.get('images')
                if images_list and isinstance(images_list, list):
                    for img in images_list:
                        if img.get('ratio') == '16_9' and img.get('width', 0) > 200:
                            image_url = img.get('url')
                            break
                    if image_url == 'URL de imagen no disponible' and images_list:
                        image_url = images_list[0].get('url', 'URL de imagen no disponible')

                events_list.append({
                    'name': name,
                    'dateTime': date_time_str,
                    'venue': venue_name,
                    'url': url,
                    'imageUrl': image_url
                })
        
        if not events_list and data.get('page', {}).get('totalElements', 0) == 0:
             return jsonify({"message": f"No se encontraron eventos para '{city_name}'."}), 200

        return jsonify(events_list), 200

    except requests.exceptions.HTTPError as http_err:
        error_message = f"Error HTTP al contactar Ticketmaster: {http_err}"
        status_code = http_err.response.status_code if http_err.response is not None else 500
        # Intentar obtener más detalles del error de Ticketmaster
        try:
            error_details = http_err.response.json()
            if 'fault' in error_details and 'faultstring' in error_details['fault']:
                 error_message = f"Error de API Ticketmaster ({status_code}): {error_details['fault']['faultstring']}"
            elif 'errors' in error_details and isinstance(error_details['errors'], list) and error_details['errors']:
                 error_message = f"Error de API Ticketmaster ({status_code}): {error_details['errors'][0].get('detail', str(http_err))}"
        except ValueError:
            pass # Mantener el error_message original si la respuesta de error no es JSON
        except AttributeError: # Si http_err.response es None
             pass
        app.logger.error(f"HTTPError al llamar a Ticketmaster: {error_message} (Status: {status_code})")
        return jsonify({"error": error_message, "status_code_from_ticketmaster": status_code}), status_code
    
    except requests.exceptions.ConnectionError as conn_err:
        app.logger.error(f"ConnectionError al llamar a Ticketmaster: {conn_err}")
        return jsonify({"error": f"Error de conexión con Ticketmaster: {conn_err}"}), 503
    
    except requests.exceptions.Timeout as timeout_err:
        app.logger.error(f"Timeout al llamar a Ticketmaster: {timeout_err}")
        return jsonify({"error": f"Timeout al contactar Ticketmaster: {timeout_err}"}), 504
        
    except requests.exceptions.RequestException as req_err:
        app.logger.error(f"RequestException al llamar a Ticketmaster: {req_err}")
        return jsonify({"error": f"Error en la solicitud a Ticketmaster: {req_err}"}), 500

    except Exception as e:
        app.logger.error(f"Error inesperado en el endpoint /api/events: {e}", exc_info=True)
        return jsonify({"error": "Ocurrió un error interno inesperado en el servidor."}), 500

# --- Punto de Entrada para Ejecutar la Aplicación ---
if __name__ == '__main__':
    # Asegurarse de que las bibliotecas requeridas estén instaladas
    try:
        import flask_cors
        import dotenv
    except ImportError as e:
        print(f"ERROR DE IMPORTACIÓN: Falta una biblioteca esencial ({e.name}).")
        print("Asegúrese de haber activado su entorno virtual y ejecutado:")
        print("pip install Flask flask-cors requests python-dotenv")
        exit(1)

    print("Iniciando servidor Flask...")
    # debug=True es útil para desarrollo. NO USAR en PRODUCCIÓN.
    # host='0.0.0.0' hace que sea accesible desde otras máquinas en la red.
    app.run(host='0.0.0.0', port=5000, debug=True)