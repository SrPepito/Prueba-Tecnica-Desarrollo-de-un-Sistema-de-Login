# 📌 Proyecto de Gestión con Litestar

Aplicación web construida con [Litestar](https://litestar.dev/) que incluye un sistema de autenticación de usuarios y panel de administración con tablas de datos.  
La app está desplegada en [Render](https://render.com/) y utiliza HTML, CSS y JavaScript para la parte de frontend.

## 🔗 Demo en línea

[![Abrir Demo](https://img.shields.io/badge/Login%20Demo-Click%20Aquí-blue?style=for-the-badge)](https://prueba-tecnica-sistema-login.onrender.com/static/login.html)


## 🚀 Características

- **Login seguro** con `bcrypt` y `passlib`.
- **Backend con Litestar** y API REST.
- **Frontend HTML/CSS/JS** con AJAX para consumir la API.
- **Carga en Render** usando `Procfile`.
- **Variables de entorno** para configuración segura.
- Gestión de rutas estáticas para `login.html` y `app.html`.

## ⚙️ Instalación y uso local

1. **Clonar repositorio**
   ```bash
   git clone https://github.com/usuario/proyecto.git o Descargar Proyecto en su Defecto
   cd proyecto

2. **Crear entorno virtual**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Linux / Mac
   .venv\Scripts\activate     # En Windows

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt

4. **Configurar variables de entorno**
   ```bash
   SESSION_SECRET=clave_secreta
   ENV=dev

5. **Para ejecutar en local**
   ```bash
   uvicorn app.main:app --reload
