# 🏠 Home Task Assignment System

Sistema de reparto de tareas del hogar que permite gestionar habitantes y tareas, con asignación aleatoria automática de responsabilidades.

**Última actualización:** 25 Marzo 2026 - Modo oscuro añadido 🌙

## ✨ Características

- 👥 **Gestión de Personas**: CRUD completo de habitantes del hogar
- 📋 **Gestión de Tareas**: CRUD de tareas con puntos de esfuerzo
- 🎲 **Asignación Automática**: Distribución equitativa de tareas
- 📊 **Estadísticas**: Vista general del estado del sistema
- 🐳 **Docker Ready**: Contenedor listo para desplegar
- ☸️ **Kubernetes**: Helm chart incluido

## 🚀 Inicio Rápido

### Con Docker Compose

```bash
# Clonar el repositorio
git clone https://github.com/bender-916/home-tasks.git
cd home-tasks

# Levantar con Docker Compose
docker-compose up --build

# Abrir en el navegador
open http://localhost:5000
```

### Con Docker directamente

```bash
# Construir la imagen
docker build -f docker/Dockerfile -t home-tasks:latest .

# Ejecutar el contenedor
docker run -d -p 5000:5000 -v home-tasks-data:/data --name home-tasks home-tasks:latest
```

### Con Kubernetes (Helm)

```bash
# Construir y cargar la imagen
docker build -f docker/Dockerfile -t home-tasks:latest .

# Instalar con Helm
helm install home-tasks ./k8s/helm/home-tasks --namespace home-tasks --create-namespace

# Port-forward para pruebas
kubectl port-forward -n home-tasks svc/home-tasks 8080:80
```

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (SPA)                        │
│              Alpine.js + Tailwind CSS                    │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  Backend (Flask)                         │
│              REST API + SQLite                          │
└─────────────────────────────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
home-tasks/
├── backend/
│   ├── app/
│   │   ├── __init__.py      # Application factory
│   │   ├── config.py        # Configuración
│   │   ├── models/          # Modelos SQLAlchemy
│   │   ├── routes/          # Endpoints API
│   │   └── utils/           # Utilidades
│   ├── tests/               # Tests unitarios
│   ├── requirements.txt
│   └── wsgi.py
├── frontend/
│   └── index.html           # SPA con Alpine.js
├── docker/
│   ├── Dockerfile
│   └── .dockerignore
├── k8s/helm/home-tasks/     # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
├── docker-compose.yaml
└── README.md
```

## 🔌 API Endpoints

### Personas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/persons` | Listar todas las personas |
| GET | `/api/persons/{id}` | Obtener persona por ID |
| POST | `/api/persons` | Crear nueva persona |
| PUT | `/api/persons/{id}` | Actualizar persona |
| DELETE | `/api/persons/{id}` | Eliminar persona |

### Tareas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/tasks` | Listar todas las tareas |
| GET | `/api/tasks/{id}` | Obtener tarea por ID |
| POST | `/api/tasks` | Crear nueva tarea |
| PUT | `/api/tasks/{id}` | Actualizar tarea |
| DELETE | `/api/tasks/{id}` | Eliminar tarea |

### Asignaciones

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/assignments` | Listar todas las asignaciones |
| GET | `/api/assignments/current` | Asignaciones activas |
| POST | `/api/assignments/generate` | Generar nuevas asignaciones |
| POST | `/api/assignments/{id}/complete` | Marcar como completada |
| DELETE | `/api/assignments/{id}` | Eliminar asignación |

### Utilidad

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/stats` | Estadísticas del sistema |

## 🧪 Tests

```bash
# Ejecutar tests
cd backend
pip install -r requirements.txt
pytest tests/ -v

# Con coverage
pytest tests/ -v --cov=app --cov-report=html
```

## ⚙️ Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Entorno de ejecución | `production` |
| `SECRET_KEY` | Clave secreta Flask | `dev-secret-key` |
| `DATABASE_PATH` | Ruta de la BD SQLite | `/data/home_tasks.db` |

## 📊 Algoritmo de Asignación

El sistema distribuye tareas de forma equitativa:

1. Obtiene personas y tareas activas
2. Baraja tareas para aleatoriedad
3. Asigna cada tarea a la persona con menor esfuerzo acumulado
4. Considera `effort_points` para distribución balanceada

## 🛠️ Tecnologías

- **Backend**: Python 3.11, Flask 3.0, SQLAlchemy, Gunicorn
- **Frontend**: Alpine.js 3.x, Tailwind CSS (CDN)
- **Database**: SQLite con WAL mode
- **Container**: Docker (multi-stage build)
- **Orchestration**: Kubernetes + Helm 3

## 📝 Licencia

MIT License

---

**Hecho con ❤️ para organizar tareas del hogar**
