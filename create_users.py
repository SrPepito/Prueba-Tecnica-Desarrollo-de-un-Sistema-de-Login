# create_users.py
from passlib.hash import bcrypt
import json
import uuid

# Define usuarios iniciales: aquí pones las contraseñas en claro que quieras
raw_users = [
    {"id": str(uuid.uuid4()), "username": "admin",      "password": "adminpass",    "nombre": "Administrador", "email": "admin@ejemplo.com", "role": "admin"},
    {"id": str(uuid.uuid4()), "username": "super1",     "password": "superpass",    "nombre": "Supervisor Uno","email": "super1@ejemplo.com","role": "supervisor"},
    {"id": str(uuid.uuid4()), "username": "usuario1",   "password": "userpass",     "nombre": "Usuario Uno",    "email": "user1@ejemplo.com", "role": "usuario"}
]

# Hasheamos las contraseñas y guardamos en usuarios.json
for u in raw_users:
    # bcrypt.hash produce un hash seguro
    u["password"] = bcrypt.hash(u["password"])

with open("usuarios.json", "w", encoding="utf-8") as f:
    json.dump(raw_users, f, indent=2, ensure_ascii=False)

print("usuarios.json generado con", len(raw_users), "usuarios.")