# Aplicación Web con Login en Contenedores

Actividad de **Cloud Computing (USIL)**: aplicación web con inicio de sesión que valida usuarios contra PostgreSQL, desplegada con Docker Compose (proxy + app + base de datos) y publicada en la nube.

```
Usuario ──HTTPS──▶ [Nginx :80] ──HTTP──▶ [App Flask :8000] ──SQL──▶ [PostgreSQL :5432]
                   único puerto          red interna                 sin puerto público
                   público                                           + volumen db_data
```

| Componente | Imagen | Rol |
|---|---|---|
| proxy | `nginx:1.27-alpine` (oficial) | Proxy inverso, único punto de entrada (puerto 80) |
| app | `<usuario>/cloud-login-app:1.0.0` (propia) | Flask + Gunicorn: login, sesión, bienvenida |
| db | `postgres:17.2-alpine` (oficial) | Usuarios con contraseña hash bcrypt, volumen persistente |

## Usuarios de prueba (ficticios)

| Usuario | Contraseña | Nombre |
|---|---|---|
| `admin` | `Admin123!` | Administrador del Sistema |
| `mlopez` | `Maria2026!` | María López |

## Estructura

```
├── app/
│   ├── app.py              # Lógica: login, sesión, ruta protegida
│   ├── Dockerfile          # Imagen propia (linux/amd64)
│   ├── requirements.txt
│   ├── templates/          # login.html, bienvenida.html
│   └── static/style.css
├── db/init.sql             # Tabla usuarios + 2 usuarios con hash
├── nginx/nginx.conf        # Proxy inverso
├── docker-compose.yml
├── .env.example            # Plantilla (el .env real NO se sube)
└── .gitignore
```

---

## 1. Ejecutar en local (GitHub Codespaces)

```bash
cp .env.example .env
# Edita .env: pon tu usuario de Docker Hub, una clave de BD y un SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"   # para SECRET_KEY

docker compose up -d --build
docker compose ps
```

Abre la pestaña **Ports** de Codespaces → puerto **80** → abrir en navegador (Codespaces da la URL con HTTPS).

## 2. Publicar la imagen en Docker Hub

Crea un access token en Docker Hub (Account Settings → Personal access tokens) y:

```bash
docker login -u TU_USUARIO          # pega el token como contraseña
docker compose build                # construye para linux/amd64
docker push TU_USUARIO/cloud-login-app:1.0.0
```

## 3. Desplegar en la nube — Opción A (Blitz Cloud)

1. Crear la **base de datos administrada PostgreSQL 17** en el panel.
2. Crear una **app desde imagen Docker Hub**: `TU_USUARIO/cloud-login-app:1.0.0`.
3. Puerto de la app: **8000**.
4. Variables de entorno de la app:
   - `DATABASE_URL` → la define la plataforma al vincular la BD.
   - `SECRET_KEY` → una clave aleatoria.
   - `COOKIE_SECURE` → `true` (la plataforma sirve HTTPS).
5. Al arrancar, la app ejecuta `init.sql` automáticamente (crea la tabla y los usuarios; es idempotente).
6. Abrir la URL pública HTTPS que entrega la plataforma.

> En la Opción A no se usa Nginx en la nube: la plataforma entrega el HTTPS. La arquitectura de 3 contenedores se demuestra en local.

### Opción B (VM en AWS / Azure / GCP)

```bash
# En la VM (Ubuntu)
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
git clone https://github.com/TU_USUARIO/cloud-login-app.git && cd cloud-login-app
cp .env.example .env && nano .env
sudo docker compose pull && sudo docker compose up -d
```

Abrir solo el puerto 80 (y 443 si configuras certificado) en el firewall / grupo de seguridad.

---

## 4. Comandos para la demostración

```bash
docker compose ps                                   # 3 servicios corriendo
docker network inspect cloud-login-app_red_interna  # red interna
docker volume ls                                    # volumen db_data

# Contraseñas guardadas con hash
docker compose exec db psql -U appuser -d appdb -c "SELECT usuario, password_hash FROM usuarios;"

# La BD no es accesible desde fuera (debe fallar)
nc -zv localhost 5432

# Persistencia: recrear el contenedor de la BD y verificar que los usuarios siguen
docker compose rm -sf db
docker compose up -d db
docker compose exec db psql -U appuser -d appdb -c "SELECT usuario FROM usuarios;"
```

## 5. Medidas de seguridad

- Contraseñas con **bcrypt** (costo 12); nunca en texto plano.
- **Consultas parametrizadas** (`%s`) → protección contra SQL injection.
- Credenciales en **variables de entorno** (`.env` en `.gitignore` y `.dockerignore`).
- BD **sin puerto publicado**; solo la app la alcanza por la red interna.
- Solo el proxy expone puerto (80).
- Cookie de sesión `HttpOnly`, `SameSite=Lax`, `Secure` en producción; expira a los 30 min.
- Mensaje de error genérico (no revela si el usuario existe).
- `Cache-Control: no-store` en páginas → tras cerrar sesión no se ve la bienvenida desde caché.
- La app corre con un usuario sin privilegios dentro del contenedor.
- Imágenes con versión fija (no `latest`).

## 6. Limpieza

```bash
docker compose down        # detiene (conserva el volumen)
docker compose down -v     # borra también los datos
```
