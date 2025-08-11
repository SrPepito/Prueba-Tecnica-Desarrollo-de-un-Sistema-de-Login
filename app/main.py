# --- Importaciones necesarias ---
import json  # Para leer y manipular archivos en formato JSON
from pathlib import Path  # Para manejar rutas de archivos de forma más segura y multiplataforma
from typing import Optional, Dict, Any  # Para añadir anotaciones de tipo y facilitar el autocompletado
from uuid import uuid4  # (Actualmente no se usa) Sirve para generar identificadores únicos
import os
import secrets
from dotenv import load_dotenv
from litestar import Litestar, Request, Response, get, post  # Framework web para crear rutas y manejar peticiones
from litestar.middleware.session.client_side import CookieBackendConfig  # Manejo de sesiones mediante cookies
from litestar.status_codes import HTTP_401_UNAUTHORIZED  # Código de estado HTTP para errores de autenticación
from passlib.hash import bcrypt  # Librería para hashear y verificar contraseñas

from litestar.static_files import StaticFilesConfig  # Permite servir archivos estáticos como HTML, CSS o JS

# --- Cargar .env ---
load_dotenv()

SESSION_SECRET_HEX = os.getenv("SESSION_SECRET")

if not SESSION_SECRET_HEX:
    # Si no está definida, se genera una temporal solo para desarrollo
    SESSION_SECRET_HEX = secrets.token_hex(32)
    print("⚠️ WARNING: No SESSION_SECRET en .env — usando temporal.")

secret_bytes = bytes.fromhex(SESSION_SECRET_HEX)

# --- Cargar usuarios desde un archivo JSON ---
# Definimos la ruta al archivo `usuarios.json` que contiene los datos de todos los usuarios.
# `Path(__file__).parent.parent` sube dos niveles desde este archivo para encontrar el JSON.
USERS_FILE = Path(__file__).parent.parent / "usuarios.json"

# Abrimos el archivo en modo lectura, con codificación UTF-8, y cargamos su contenido como una lista de diccionarios.
with open(USERS_FILE, "r", encoding="utf-8") as f:
    USERS = json.load(f)


# --- Funciones auxiliares ---

def find_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Busca un usuario en la lista USERS por su nombre de usuario.

    Parámetros:
        username (str): El nombre de usuario que se quiere buscar.

    Retorna:
        dict con la información del usuario si se encuentra.
        None si no existe un usuario con ese username.
    """
    for u in USERS:  # Recorre todos los usuarios cargados desde el JSON
        if u["username"] == username:  # Compara el username con el buscado
            return u  # Devuelve el usuario encontrado
    return None  # Si no se encuentra, retorna None


def filter_users_for_role(auth_user: Dict[str, Any]):
    """
    Filtra la lista de usuarios según el rol del usuario autenticado.
    Esto asegura que un usuario solo pueda ver información que le corresponde.

    Parámetros:
        auth_user (dict): El usuario autenticado (contiene al menos 'role' y 'id').

    Retorna:
        list de diccionarios con los usuarios que puede ver el usuario autenticado.
    """
    role = auth_user["role"]

    if role == "admin":
        # El administrador puede ver a todos los usuarios
        return USERS

    elif role == "supervisor":
        # El supervisor puede ver a todos, excepto a los administradores
        return [u for u in USERS if u["role"] != "admin"]

    else:  # Caso para un usuario normal
        # Solo puede ver su propia información
        return [u for u in USERS if u["id"] == auth_user["id"]]


# --- Rutas ---

@post("/api/login")
async def login(data: Dict[str, str], request: Request) -> Response:
    """
    Endpoint para iniciar sesión.

    Recibe:
        data (dict): Contiene 'username' y 'password' enviados por el cliente.
        request (Request): Objeto que contiene datos de la petición y la sesión.

    Retorna:
        - 200 OK con un mensaje y el rol del usuario si las credenciales son correctas.
        - 401 UNAUTHORIZED si el usuario no existe o la contraseña es incorrecta.
    """

    # Extraer datos enviados por el cliente
    username = data.get("username")
    password = data.get("password")

    # Buscar el usuario en la base de datos (en este caso el JSON)
    user = find_user_by_username(username)

    # Verificar si el usuario existe y si la contraseña es correcta
    if not user or not bcrypt.verify(password, user["password"]):
        return Response({"error": "Credenciales inválidas"}, status_code=HTTP_401_UNAUTHORIZED)

    # Guardar el ID del usuario en la sesión
    request.session["user_id"] = user["id"]

    # Retornar mensaje de éxito y el rol del usuario
    return Response({"message": "Login exitoso", "role": user["role"]})


@post("/api/logout")
async def logout(request: Request) -> Response:
    """
    Endpoint para cerrar sesión.

    Borra todos los datos almacenados en la sesión del usuario.
    """
    request.session.clear()
    return Response({"message": "Logout exitoso"})


@get("/api/me")
async def me(request: Request) -> Response:
    """
    Endpoint para obtener información del usuario autenticado.

    Requiere:
        Que exista un 'user_id' en la sesión.

    Retorna:
        - Información del usuario sin incluir la contraseña.
        - 401 si no hay sesión activa o el usuario no existe.
    """

    # Recuperar el ID del usuario desde la sesión
    user_id = request.session.get("user_id")
    if not user_id:
        return Response({"error": "No autenticado"}, status_code=HTTP_401_UNAUTHORIZED)

    # Buscar el usuario en la lista cargada desde el JSON
    user = next((u for u in USERS if u["id"] == user_id), None)
    if not user:
        return Response({"error": "Usuario no encontrado"}, status_code=HTTP_401_UNAUTHORIZED)

    # Excluir la contraseña antes de enviarla al cliente
    safe_user = {k: v for k, v in user.items() if k != "password"}
    return Response(safe_user)


@get("/api/users")
async def list_users(request: Request) -> Response:
    """
    Endpoint para listar usuarios.

    - Si es admin: ve todos.
    - Si es supervisor: ve todos excepto admins.
    - Si es usuario normal: solo ve su información.

    Requiere:
        Que exista un 'user_id' en la sesión.
    """

    # Verificar si hay sesión activa
    user_id = request.session.get("user_id")
    if not user_id:
        return Response({"error": "No autenticado"}, status_code=HTTP_401_UNAUTHORIZED)

    # Obtener los datos del usuario autenticado
    auth_user = next((u for u in USERS if u["id"] == user_id), None)
    if not auth_user:
        return Response({"error": "Usuario no encontrado"}, status_code=HTTP_401_UNAUTHORIZED)

    # Filtrar usuarios según el rol
    filtered = filter_users_for_role(auth_user)

    # Retornar lista segura (sin contraseñas)
    safe_list = [{k: v for k, v in u.items() if k != "password"} for u in filtered]
    return Response(safe_list)


# --- Configuración de la app ---

# Crear la aplicación principal de Litestar.
# Parámetros:
#   - route_handlers: Lista de funciones que manejan las rutas (endpoints de la API).
#   - middleware: Lista de middlewares activos (aquí se añade el de sesión).
#   - debug: Si está en True, activa el modo de depuración (útil en desarrollo).
#   - static_files_config: Configuración para servir archivos estáticos (HTML, CSS, JS, imágenes, etc.).

ENV = os.getenv("ENV", "development")

session_config = CookieBackendConfig(
    secret=secret_bytes,
    secure=(ENV == "production"),
    httponly=True
)


app = Litestar(
    route_handlers=[login, logout, me, list_users],
    middleware=[session_config.middleware],
    debug=(ENV != "production"),
    static_files_config=[
        StaticFilesConfig(
            directories=["static"],
            path="/static"
        )
    ]
)

