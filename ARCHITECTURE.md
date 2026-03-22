# Documento de Arquitectura: Home Task Assignment System

**Versión:** 1.0  
**Fecha:** 2026-03-22  
**Autor:** Arquitecto de Software

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Stack Tecnológico](#2-stack-tecnológico)
3. [Estructura de Directorios](#3-estructura-de-directorios)
4. [Modelo de Datos](#4-modelo-de-datos)
5. [API Endpoints](#5-api-endpoints)
6. [Configuración Kubernetes](#6-configuración-kubernetes)
7. [Dockerfile](#7-dockerfile)
8. [Consideraciones de Seguridad](#8-consideraciones-de-seguridad)
9. [Optimización de Recursos](#9-optimización-de-recursos)
10. [Guía de Implementación](#10-guía-de-implementación)

---

## 1. Resumen Ejecutivo

### Propósito
Sistema de reparto de tareas del hogar que permite gestionar habitantes y tareas, con asignación aleatoria automática de responsabilidades.

### Objetivos de Diseño
- **Bajo consumo de recursos**: Entorno doméstico con hardware limitado
- **Simplicidad operativa**: Sin alta disponibilidad (HA), mantenibilidad sencilla
- **Persistencia ligera**: Base de datos embebida sin dependencias externas
- **Despliegue simple**: Un solo contenedor con Helm chart para Kubernetes

### Alcance Funcional
- Gestión CRUD de personas (habitantes)
- Gestión CRUD de tareas/habitaciones
- Algoritmo de asignación aleatoria equitativa
- Visualización de asignaciones actuales
- Persistencia de datos entre reinicios

---

## 2. Stack Tecnológico

### 2.1 Frontend

| Tecnología | Opción Seleccionada |
|------------|---------------------|
| Framework | **Alpine.js v3.x** + **Vanilla JS** |
| Estilos | **Tailwind CSS (CDN)** |
| Build | Sin build step |

#### Justificación
- **Alpine.js**: ~15KB minificado, sintaxis declarativa similar a Vue sin Virtual DOM
- **Sin Node.js/build**: Servido directamente por el backend como archivos estáticos
- **Tailwind CDN**: Sin dependencias de build, estilos utilitarios rápidos
- **Consumo estimado**: ~5-10MB RAM en cliente (browser)

#### Alternativas Descartadas
| Opción | Razón de Descarte |
|--------|-------------------|
| React/Vue/Angular | Demasiado pesado para uso simple, requiere build step |
| Svelte | Requiere compilación, añade complejidad |
| Vanilla JS puro | Más código a mantener, menos mantenible |

### 2.2 Backend

| Tecnología | Opción Seleccionada |
|------------|---------------------|
| Runtime | **Python 3.11+** |
| Framework | **Flask 3.x** |
| ORM | **SQLAlchemy** (con SQLite) |
| Servidor WSGI | **Gunicorn** (workers=1) |

#### Justificación
- **Python**: Amplio ecosistema, fácil mantenimiento, ideal para scripts domésticos
- **Flask**: Microframework minimalista, ~1MB footprint, extensibilidad bajo demanda
- **SQLAlchemy**: ORM maduro con soporte SQLite nativo
- **Gunicorn**: Servidor WSGI robusto con 1 worker suficiente para uso doméstico

#### Consumo de Recursos Estimado
```
Memoria base Flask:     ~25-40MB
SQLite en memoria:      ~5-10MB
Gunicorn overhead:      ~10-15MB
Total estimado:         ~50-70MB RAM
CPU:                    < 0.1 core idle, < 0.5 core bajo carga
```

#### Alternativas Descartadas
| Opción | Razón de Descarte |
|--------|-------------------|
| Node.js/Express | Mayor consumo de memoria base (~50-100MB) |
| Go/Gin | Curva de aprendizaje, overkill para uso doméstico |
| FastAPI | Más pesado que Flask, async no necesario para este uso |

### 2.3 Base de Datos

| Tecnología | Opción Seleccionada |
|------------|---------------------|
| Motor | **SQLite 3** |
| Ubicación | Archivo local (`/data/home_tasks.db`) |
| Modo | WAL (Write-Ahead Logging) |

#### Justificación
- **Sin servidor**: No requiere proceso separado, cero overhead
- **Persistencia en archivo**: Volumen montado en K8s para datos persistentes
- **WAL mode**: Mejor concurrencia de lectura/escritura
- **Tamaño**: Base de datos típica < 1MB

#### Alternativas Descartadas
| Opción | Razón de Descarte |
|--------|-------------------|
| PostgreSQL | Requiere contenedor separado, overhead innecesario |
| MySQL | Igual que PostgreSQL, más complejo |
| MongoDB | Overkill para datos relacionales simples |

### 2.4 Contenedor y Orquestación

| Tecnología | Opción Seleccionada |
|------------|---------------------|
| Runtime | **Docker** |
| Base Image | **python:3.11-slim-bookworm** (~120MB) |
| Orquestación | **Kubernetes** con **Helm 3** |

---

## 3. Estructura de Directorios

```
home-tasks/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Factory de la aplicación Flask
│   │   ├── config.py            # Configuración (env vars, defaults)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── models.py        # Modelos SQLAlchemy
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── persons.py       # Endpoints CRUD personas
│   │   │   ├── tasks.py         # Endpoints CRUD tareas
│   │   │   └── assignments.py   # Endpoints asignación
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── assignment_service.py  # Lógica de asignación
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── database.py      # Inicialización DB
│   ├── requirements.txt
│   ├── wsgi.py                  # Entry point para Gunicorn
│   └── tests/
│       ├── __init__.py
│       ├── test_persons.py
│       ├── test_tasks.py
│       └── test_assignments.py
├── frontend/
│   ├── index.html               # SPA principal
│   ├── css/
│   │   └── styles.css           # Estilos custom (mínimos)
│   └── js/
│       ├── app.js               # Inicialización Alpine.js
│       ├── api.js               # Cliente API HTTP
│       └── components/
│           ├── persons.js       # Componente gestión personas
│           ├── tasks.js         # Componente gestión tareas
│           └── assignments.js   # Componente visualización
├── k8s/
│   ├── base/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── kustomization.yaml
│   └── helm/
│       ├── home-tasks/
│       │   ├── Chart.yaml
│       │   ├── values.yaml
│       │   ├── templates/
│       │   │   ├── deployment.yaml
│       │   │   ├── service.yaml
│       │   │   ├── configmap.yaml
│       │   │   ├── pvc.yaml
│       │   │   └── _helpers.tpl
│       │   └── charts/          # Vacío, sin dependencias
│       └── values/
│           ├── dev.yaml
│           └── prod.yaml
├── docker/
│   ├── Dockerfile
│   └── .dockerignore
├── scripts/
│   ├── init-db.py               # Script inicialización DB
│   └── seed-data.py             # Datos de prueba (opcional)
├── docs/
│   └── ARCHITECTURE.md          # Este documento
├── .gitignore
├── README.md
├── docker-compose.yaml          # Para desarrollo local
└── Makefile                     # Comandos comunes
```

---

## 4. Modelo de Datos

### 4.1 Diagrama Entidad-Relación

```
┌─────────────────┐       ┌─────────────────┐
│     Person      │       │      Task       │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ name            │       │ name            │
│ color           │       │ description     │
│ is_active       │       │ room            │
│ created_at      │       │ effort_points   │
│ updated_at      │       │ is_active       │
└─────────────────┘       │ created_at      │
        │                 │ updated_at      │
        │                 └─────────────────┘
        │                         │
        │                         │
        ▼                         ▼
┌─────────────────────────────────────────┐
│             Assignment                   │
├─────────────────────────────────────────┤
│ id (PK)                                 │
│ person_id (FK → Person.id)              │
│ task_id (FK → Task.id)                  │
│ assigned_at                             │
│ completed_at (nullable)                 │
│ is_active                               │
│ created_at                              │
└─────────────────────────────────────────┘
```

### 4.2 Definición de Tablas

#### Tabla: `persons`

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Identificador único |
| `name` | VARCHAR(100) | NOT NULL, UNIQUE | Nombre de la persona |
| `color` | VARCHAR(7) | DEFAULT '#3B82F6' | Color hexadecimal para UI |
| `is_active` | BOOLEAN | DEFAULT TRUE | Persona activa/inactiva |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Fecha creación |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Última modificación |

#### Tabla: `tasks`

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Identificador único |
| `name` | VARCHAR(100) | NOT NULL | Nombre de la tarea |
| `description` | TEXT | NULLABLE | Descripción detallada |
| `room` | VARCHAR(50) | NULLABLE | Habitación asociada |
| `effort_points` | INTEGER | DEFAULT 1 | Peso para distribución equitativa |
| `is_active` | BOOLEAN | DEFAULT TRUE | Tarea activa/inactiva |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Fecha creación |
| `updated_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Última modificación |

#### Tabla: `assignments`

| Columna | Tipo | Restricciones | Descripción |
|---------|------|---------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Identificador único |
| `person_id` | INTEGER | NOT NULL, FK → persons(id) | Referencia a persona |
| `task_id` | INTEGER | NOT NULL, FK → tasks(id) | Referencia a tarea |
| `assigned_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Momento de asignación |
| `completed_at` | DATETIME | NULLABLE | Fecha completado (opcional) |
| `is_active` | BOOLEAN | DEFAULT TRUE | Asignación vigente |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | Fecha creación |

### 4.3 Índices Recomendados

```sql
CREATE INDEX idx_assignments_person ON assignments(person_id);
CREATE INDEX idx_assignments_task ON assignments(task_id);
CREATE INDEX idx_assignments_active ON assignments(is_active);
CREATE INDEX idx_persons_active ON persons(is_active);
CREATE INDEX idx_tasks_active ON tasks(is_active);
```

### 4.4 Restricciones de Integridad

```sql
-- Foreign Keys (activar en SQLite)
PRAGMA foreign_keys = ON;

-- Constraints
FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE
FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
```

---

## 5. API Endpoints

### 5.1 Resumen de Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| **Personas** |
| GET | `/api/persons` | Listar todas las personas |
| GET | `/api/persons/{id}` | Obtener persona por ID |
| POST | `/api/persons` | Crear nueva persona |
| PUT | `/api/persons/{id}` | Actualizar persona |
| DELETE | `/api/persons/{id}` | Eliminar persona |
| **Tareas** |
| GET | `/api/tasks` | Listar todas las tareas |
| GET | `/api/tasks/{id}` | Obtener tarea por ID |
| POST | `/api/tasks` | Crear nueva tarea |
| PUT | `/api/tasks/{id}` | Actualizar tarea |
| DELETE | `/api/tasks/{id}` | Eliminar tarea |
| **Asignaciones** |
| GET | `/api/assignments` | Listar asignaciones actuales |
| GET | `/api/assignments/current` | Asignaciones activas |
| POST | `/api/assignments/generate` | Generar nuevas asignaciones |
| DELETE | `/api/assignments/{id}` | Eliminar asignación |
| POST | `/api/assignments/{id}/complete` | Marcar como completada |
| **Utilidad** |
| GET | `/api/health` | Health check |
| GET | `/api/stats` | Estadísticas del sistema |

### 5.2 Detalle de Endpoints

#### 5.2.1 Personas

##### `GET /api/persons`
**Descripción:** Lista todas las personas

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Juan",
      "color": "#3B82F6",
      "is_active": true,
      "created_at": "2026-03-22T10:00:00Z",
      "updated_at": "2026-03-22T10:00:00Z"
    }
  ],
  "count": 1
}
```

##### `POST /api/persons`
**Descripción:** Crea una nueva persona

**Request Body:**
```json
{
  "name": "María",
  "color": "#EF4444"
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "María",
    "color": "#EF4444",
    "is_active": true,
    "created_at": "2026-03-22T11:00:00Z"
  }
}
```

**Response 400:**
```json
{
  "success": false,
  "error": "El nombre es requerido"
}
```

**Response 409:**
```json
{
  "success": false,
  "error": "Ya existe una persona con ese nombre"
}
```

##### `PUT /api/persons/{id}`
**Descripción:** Actualiza una persona existente

**Request Body:**
```json
{
  "name": "Juan Carlos",
  "color": "#10B981",
  "is_active": false
}
```

**Response 200:** Similar a POST

##### `DELETE /api/persons/{id}`
**Descripción:** Elimina una persona (y sus asignaciones)

**Response 204:** Sin contenido

**Response 404:**
```json
{
  "success": false,
  "error": "Persona no encontrada"
}
```

#### 5.2.2 Tareas

##### `GET /api/tasks`
**Descripción:** Lista todas las tareas

**Query Parameters:**
- `room` (opcional): Filtrar por habitación
- `is_active` (opcional): Filtrar por estado activo

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Lavar platos",
      "description": "Lavar todos los platos del día",
      "room": "Cocina",
      "effort_points": 2,
      "is_active": true
    }
  ],
  "count": 1
}
```

##### `POST /api/tasks`
**Descripción:** Crea una nueva tarea

**Request Body:**
```json
{
  "name": "Sacar basura",
  "description": "Sacar los contenedores",
  "room": "Cocina",
  "effort_points": 1
}
```

#### 5.2.3 Asignaciones

##### `GET /api/assignments/current`
**Descripción:** Obtiene las asignaciones activas actuales

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "person": {
        "id": 1,
        "name": "Juan",
        "color": "#3B82F6"
      },
      "task": {
        "id": 2,
        "name": "Sacar basura",
        "room": "Cocina",
        "effort_points": 1
      },
      "assigned_at": "2026-03-22T08:00:00Z",
      "is_active": true
    }
  ],
  "generated_at": "2026-03-22T08:00:00Z"
}
```

##### `POST /api/assignments/generate`
**Descripción:** Genera nuevas asignaciones aleatorias

**Algoritmo:**
1. Desactivar todas las asignaciones anteriores (`is_active = false`)
2. Obtener personas activas
3. Obtener tareas activas
4. Distribuir tareas equitativamente considerando `effort_points`
5. Crear nuevas asignaciones

**Request Body (opcional):**
```json
{
  "strategy": "balanced",  // "random" | "balanced" | "rotation"
  "clear_previous": true
}
```

**Response 201:**
```json
{
  "success": true,
  "data": {
    "assignments": [
      {
        "person_id": 1,
        "person_name": "Juan",
        "tasks": [
          {"id": 2, "name": "Sacar basura", "effort_points": 1}
        ],
        "total_effort": 1
      }
    ],
    "generated_at": "2026-03-22T08:00:00Z"
  },
  "message": "Asignaciones generadas exitosamente"
}
```

##### `POST /api/assignments/{id}/complete`
**Descripción:** Marca una asignación como completada

**Response 200:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "completed_at": "2026-03-22T18:00:00Z"
  }
}
```

#### 5.2.4 Utilidad

##### `GET /api/health`
**Descripción:** Health check para probes de Kubernetes

**Response 200:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-03-22T12:00:00Z"
}
```

##### `GET /api/stats`
**Descripción:** Estadísticas del sistema

**Response 200:**
```json
{
  "success": true,
  "data": {
    "persons": {
      "total": 4,
      "active": 4
    },
    "tasks": {
      "total": 10,
      "active": 8
    },
    "assignments": {
      "active": 8,
      "completed_today": 3
    }
  }
}
```

### 5.3 Códigos de Error HTTP

| Código | Descripción |
|--------|-------------|
| 200 | Operación exitosa |
| 201 | Recurso creado |
| 204 | Eliminación exitosa (sin contenido) |
| 400 | Error de validación en request |
| 404 | Recurso no encontrado |
| 409 | Conflicto (ej: nombre duplicado) |
| 500 | Error interno del servidor |

---

## 6. Configuración Kubernetes

### 6.1 Deployment YAML (base)

```yaml
# k8s/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: home-tasks
  labels:
    app: home-tasks
    version: v1
spec:
  replicas: 1
  strategy:
    type: Recreate  # Importante para SQLite (un solo pod a la vez)
  selector:
    matchLabels:
      app: home-tasks
  template:
    metadata:
      labels:
        app: home-tasks
    spec:
      # Nodo específico si se desea (opcional)
      # nodeSelector:
      #   kubernetes.io/hostname: home-server
      
      containers:
        - name: home-tasks
          image: home-tasks:latest
          imagePullPolicy: IfNotPresent
          
          ports:
            - name: http
              containerPort: 5000
              protocol: TCP
          
          env:
            - name: FLASK_ENV
              value: "production"
            - name: DATABASE_PATH
              value: "/data/home_tasks.db"
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: home-tasks-secret
                  key: secret-key
          
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "500m"
              memory: "128Mi"
          
          livenessProbe:
            httpGet:
              path: /api/health
              port: http
            initialDelaySeconds: 10
            periodSeconds: 30
            timeoutSeconds: 5
            failureThreshold: 3
          
          readinessProbe:
            httpGet:
              path: /api/health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          
          volumeMounts:
            - name: data
              mountPath: /data
              readOnly: false
      
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: home-tasks-pvc
      
      # Evitar evicción en nodos con presión de recursos
      priorityClassName: system-cluster-critical  # Omitir si no existe
```

### 6.2 Service YAML (base)

```yaml
# k8s/base/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: home-tasks
  labels:
    app: home-tasks
spec:
  type: ClusterIP
  ports:
    - name: http
      port: 80
      targetPort: http
      protocol: TCP
  selector:
    app: home-tasks
```

### 6.3 ConfigMap YAML

```yaml
# k8s/base/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: home-tasks-config
data:
  FLASK_ENV: "production"
  LOG_LEVEL: "INFO"
  DATABASE_PATH: "/data/home_tasks.db"
```

### 6.4 PersistentVolumeClaim

```yaml
# Para Helm chart - templates/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "home-tasks.fullname" . }}-pvc
  labels:
    {{- include "home-tasks.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size | default "1Gi" }}
  {{- if .Values.persistence.storageClass }}
  storageClassName: {{ .Values.persistence.storageClass }}
  {{- end }}
```

### 6.5 Helm Chart

#### Chart.yaml

```yaml
# k8s/helm/home-tasks/Chart.yaml
apiVersion: v2
name: home-tasks
description: Sistema de reparto de tareas del hogar
type: application
version: 1.0.0
appVersion: "1.0.0"
keywords:
  - home
  - tasks
  - family
maintainers:
  - name: Home Admin
    email: admin@home.local
```

#### values.yaml

```yaml
# k8s/helm/home-tasks/values.yaml
# Valores por defecto para home-tasks

replicaCount: 1

image:
  repository: home-tasks
  pullPolicy: IfNotPresent
  tag: "latest"

imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: false

podAnnotations: {}

podSecurityContext:
  fsGroup: 1000

securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL

service:
  type: ClusterIP
  port: 80
  targetPort: 5000

ingress:
  enabled: false
  className: ""
  annotations: {}
  hosts:
    - host: home-tasks.local
      paths:
        - path: /
          pathType: Prefix
  tls: []

resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 500m
    memory: 128Mi

persistence:
  enabled: true
  size: 1Gi
  storageClass: ""
  accessMode: ReadWriteOnce

config:
  flaskEnv: production
  logLevel: INFO

secrets:
  secretKey: "change-me-in-production"

nodeSelector: {}
tolerations: []
affinity: {}

# Para entorno doméstico, preferir nodo específico
# nodeSelector:
#   kubernetes.io/hostname: home-server
```

#### templates/_helpers.tpl

```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "home-tasks.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "home-tasks.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "home-tasks.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "home-tasks.labels" -}}
helm.sh/chart: {{ include "home-tasks.chart" . }}
{{ include "home-tasks.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "home-tasks.selectorLabels" -}}
app.kubernetes.io/name: {{ include "home-tasks.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

#### templates/deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "home-tasks.fullname" . }}
  labels:
    {{- include "home-tasks.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  strategy:
    type: Recreate
  selector:
    matchLabels:
      {{- include "home-tasks.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
      labels:
        {{- include "home-tasks.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.service.targetPort }}
              protocol: TCP
          envFrom:
            - configMapRef:
                name: {{ include "home-tasks.fullname" . }}-config
          env:
            - name: SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ include "home-tasks.fullname" . }}-secret
                  key: secret-key
          livenessProbe:
            httpGet:
              path: /api/health
              port: http
            initialDelaySeconds: 10
            periodSeconds: 30
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /api/health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          volumeMounts:
            - name: data
              mountPath: /data
      volumes:
        - name: data
        {{- if .Values.persistence.enabled }}
          persistentVolumeClaim:
            claimName: {{ include "home-tasks.fullname" . }}-pvc
        {{- else }}
          emptyDir: {}
        {{- end }}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

### 6.6 Resource Limits Recomendados

| Entorno | CPU Request | CPU Limit | Memory Request | Memory Limit |
|---------|-------------|-----------|----------------|--------------|
| **Desarrollo** | 25m | 250m | 32Mi | 64Mi |
| **Producción (Doméstico)** | 50m | 500m | 64Mi | 128Mi |
| **Alta Carga (Multi-familia)** | 100m | 1000m | 128Mi | 256Mi |

**Justificación:**
- SQLite no consume CPU en idle
- Flask con 1 worker maneja ~100 requests/segundo con estos límites
- Memoria suficiente para el ORM y datos en caché
- Picos de CPU durante generación de asignaciones (algoritmo simple)

---

## 7. Dockerfile

```dockerfile
# docker/Dockerfile
# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Instalar dependencias de build (si fueran necesarias)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (cache de Docker)
COPY backend/requirements.txt .

# Crear virtualenv y instalar dependencias
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim-bookworm AS runtime

# Argumentos de build
ARG APP_VERSION=1.0.0
ARG BUILD_DATE

# Labels OCI
LABEL org.opencontainers.image.title="Home Tasks" \
      org.opencontainers.image.description="Sistema de reparto de tareas del hogar" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}"

# Crear usuario no-root
RUN groupadd -g 1000 apptask && \
    useradd -r -u 1000 -g apptask -d /app -s /sbin/nologin apptask

WORKDIR /app

# Copiar virtualenv del builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar código de la aplicación
COPY --chown=apptask:apptask backend/app ./app
COPY --chown=apptask:apptask backend/wsgi.py .
COPY --chown=apptask:apptask frontend ./frontend

# Crear directorio de datos
RUN mkdir -p /data && chown apptask:apptask /data

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=wsgi.py \
    DATABASE_PATH=/data/home_tasks.db \
    FLASK_ENV=production

# Exponer puerto
EXPOSE 5000

# Cambiar a usuario no-root
USER apptask

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# Comando de inicio
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]
```

### 7.1 .dockerignore

```
# docker/.dockerignore
__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
.env
.venv
venv/
ENV/
.git
.gitignore
.dockerignore
Dockerfile
docker-compose*.yaml
README.md
docs/
tests/
*.md
.idea/
.vscode/
*.swp
*.swo
*~
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
```

### 7.2 requirements.txt

```
# backend/requirements.txt
# Core
Flask==3.0.0
Werkzeug==3.0.1

# Database
SQLAlchemy==2.0.23

# WSGI Server
gunicorn==21.2.0

# Utils
python-dotenv==1.0.0

# Development (opcional, separar en requirements-dev.txt)
pytest==7.4.3
pytest-cov==4.1.0
```

---

## 8. Consideraciones de Seguridad

### 8.1 Seguridad de la Aplicación

| Aspecto | Medida | Implementación |
|---------|--------|----------------|
| **Autenticación** | No requerida | Sistema doméstico, red privada |
| **Autorización** | N/A | Sin roles/permisos |
| **Input Validation** | Validar todos los inputs | Pydantic/WTForms |
| **SQL Injection** | Usar ORM | SQLAlchemy con parámetros bind |
| **XSS** | Escape de outputs | Jinja2 auto-escape |
| **CSRF** | No requerido | Sin formularios POST directos |
| **CORS** | Configurar orígenes permitidos | Flask-CORS si es necesario |
| **Headers de Seguridad** | Headers HTTP | Flask-Talisman (opcional) |

### 8.2 Seguridad del Contenedor

```dockerfile
# Mejoras de seguridad en Dockerfile
# 1. Usuario no-root (ya implementado)
USER apptask

# 2. Read-only root filesystem (en K8s)
securityContext:
  readOnlyRootFilesystem: true

# 3. Sin capacidades innecesarias
securityContext:
  capabilities:
    drop:
      - ALL

# 4. Evitar escalación de privilegios
securityContext:
  allowPrivilegeEscalation: false
```

### 8.3 Seguridad de Kubernetes

| Aspecto | Configuración |
|---------|---------------|
| **Network Policies** | Restringir tráfico entrante/saliente |
| **Pod Security Standards** | Aplicar perfil `restricted` |
| **RBAC** | ServiceAccount con permisos mínimos |
| **Secrets** | Montar como volúmenes, no env vars |

### 8.4 Recomendaciones de Red

```
# Para uso doméstico, se recomienda:
# 1. Exponer solo via Ingress con TLS
# 2. Usar cert-manager para certificados auto-firmados
# 3. Limitar acceso por IP si es posible (red de casa)
# 4. No exponer directamente a Internet
```

---

## 9. Optimización de Recursos

### 9.1 Optimización de Memoria

| Técnica | Implementación | Ahorro Estimado |
|---------|----------------|-----------------|
| **Multi-stage build** | Dockerfile separado | ~200MB imagen |
| **Slim base image** | `python:3.11-slim` | ~400MB vs full |
| **Single Gunicorn worker** | `--workers 1` | ~30-50MB RAM |
| **SQLite WAL mode** | Config DB | Mejor concurrencia |
| **Lazy loading** | Cargar datos bajo demanda | Menor uso pico |

### 9.2 Optimización de CPU

| Técnica | Implementación |
|---------|----------------|
| **Gunicorn threads** | `--threads 2` para I/O concurrente |
| **Connection pooling** | SQLAlchemy pool_size=5 |
| **Índices DB** | Ver sección 4.3 |
| **Cache de consultas** | Opcional con Flask-Caching |

### 9.3 Optimización de Disco

| Aspecto | Recomendación |
|---------|---------------|
| **Tamaño DB** | Esperar < 10MB con uso normal |
| **Logs** | Rotar logs, no persistir en contenedor |
| **PVC** | 1GB suficiente para años de datos |

### 9.4 Monitoreo de Recursos

```yaml
# Prometheus ServiceMonitor (opcional)
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: home-tasks
spec:
  selector:
    matchLabels:
      app: home-tasks
  endpoints:
    - port: http
      path: /metrics  # Requiere Flask prometheus exporter
```

### 9.5 Estimación de Costos

| Recurso | Consumo | Costo (aprox. doméstico) |
|---------|---------|--------------------------|
| CPU | 50-100m | Despreciable |
| Memoria | 64-128Mi | Despreciable |
| Disco | 1GB PVC | Despreciable |
| **Total mensual** | | < $1 (cloud) o $0 (on-prem) |

---

## 10. Guía de Implementación

### 10.1 Prerrequisitos

- Docker instalado (para build local)
- Cluster Kubernetes funcionando (k3s, minikube, o similar)
- Helm 3 instalado
- kubectl configurado

### 10.2 Pasos de Implementación

#### Paso 1: Clonar/Crear Estructura

```bash
# Crear estructura de directorios
mkdir -p home-tasks/{backend,frontend,k8s,docker,scripts,docs}
mkdir -p home-tasks/backend/app/{models,routes,services,utils}
mkdir -p home-tasks/frontend/{css,js/components}
mkdir -p home-tasks/k8s/{base,helm/home-tasks/templates}
```

#### Paso 2: Implementar Backend

1. Crear `requirements.txt` con dependencias
2. Implementar modelos en `app/models/models.py`
3. Implementar rutas en `app/routes/`
4. Implementar servicio de asignación en `app/services/`
5. Crear `wsgi.py` como entry point

#### Paso 3: Implementar Frontend

1. Crear `index.html` con estructura base
2. Incluir Alpine.js y Tailwind via CDN
3. Implementar componentes en `js/components/`
4. Implementar cliente API en `js/api.js`

#### Paso 4: Crear Dockerfile

```bash
# Build de la imagen
cd home-tasks
docker build -f docker/Dockerfile -t home-tasks:latest .
```

#### Paso 5: Desplegar con Helm

```bash
# Instalar el chart
helm install home-tasks ./k8s/helm/home-tasks \
  --namespace home-tasks \
  --create-namespace

# Verificar despliegue
kubectl get pods -n home-tasks
kubectl logs -n home-tasks -l app=home-tasks
```

#### Paso 6: Configurar Acceso

```bash
# Opción A: Port-forward para pruebas
kubectl port-forward -n home-tasks svc/home-tasks 8080:80

# Opción B: Ingress para acceso permanente
# Habilitar ingress en values.yaml y aplicar
helm upgrade home-tasks ./k8s/helm/home-tasks \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=tareas.casa.local
```

### 10.3 Comandos Útiles

```bash
# Desarrollo local con Docker Compose
docker-compose up --build

# Ver logs en producción
kubectl logs -n home-tasks -f deployment/home-tasks

# Escalar (no recomendado con SQLite)
kubectl scale -n home-tasks deployment/home-tasks --replicas=1

# Backup de base de datos
kubectl exec -n home-tasks deployment/home-tasks -- \
  sqlite3 /data/home_tasks.db ".backup /data/backup.db"

# Restaurar backup
kubectl cp backup.db home-tasks/deployment/home-tasks:/data/restore.db
```

### 10.4 Troubleshooting

| Problema | Síntoma | Solución |
|----------|---------|----------|
| Pod no inicia | CrashLoopBackOff | Verificar PVC montado, permisos |
| DB locked | Errores de escritura | Verificar solo 1 réplica, WAL mode |
| Sin acceso | Timeout conexión | Verificar Service, NetworkPolicy |
| Memoria alta | OOMKilled | Aumentar limits, revisar leaks |

---

## Apéndice A: Algoritmo de Asignación

### Pseudocódigo

```python
def generate_assignments(persons, tasks):
    """
    Distribuye tareas entre personas de forma equitativa.
    
    Algoritmo:
    1. Calcular esfuerzo total de tareas
    2. Calcular esfuerzo objetivo por persona
    3. Barajar tareas para aleatoriedad
    4. Asignar tareas a persona con menor esfuerzo acumulado
    """
    
    active_persons = [p for p in persons if p.is_active]
    active_tasks = [t for t in tasks if t.is_active]
    
    if not active_persons or not active_tasks:
        return []
    
    # Barajar para aleatoriedad
    random.shuffle(active_tasks)
    
    # Inicializar contadores de esfuerzo por persona
    effort_tracking = {p.id: 0 for p in active_persons}
    assignments = []
    
    for task in active_tasks:
        # Encontrar persona con menor esfuerzo
        min_person_id = min(effort_tracking, key=effort_tracking.get)
        
        # Crear asignación
        assignments.append(Assignment(
            person_id=min_person_id,
            task_id=task.id,
            assigned_at=datetime.now()
        ))
        
        # Actualizar esfuerzo
        effort_tracking[min_person_id] += task.effort_points
    
    return assignments
```

### Complejidad

- **Temporal:** O(n * m) donde n = personas, m = tareas
- **Espacial:** O(n + m) para tracking y resultado

---

## Apéndice B: Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENTE (Browser)                        │
│                   Alpine.js + Tailwind                       │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/WebSocket
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    Ingress Controller                     │ │
│  │                   (nginx-traefik)                        │ │
│  └─────────────────────────┬───────────────────────────────┘ │
│                            │                                  │
│  ┌─────────────────────────▼───────────────────────────────┐ │
│  │                  Service (ClusterIP)                      │ │
│  │                    home-tasks:80                          │ │
│  └─────────────────────────┬───────────────────────────────┘ │
│                            │                                  │
│  ┌─────────────────────────▼───────────────────────────────┐ │
│  │                   Deployment (replicas: 1)                │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │                       Pod                            │ │ │
│  │  │  ┌───────────────────────────────────────────────┐  │ │ │
│  │  │  │  Container: home-tasks                         │  │ │ │
│  │  │  │  ┌─────────────────────────────────────────┐  │  │ │ │
│  │  │  │  │  Gunicorn (1 worker, 2 threads)         │  │  │ │ │
│  │  │  │  │         │                               │  │  │ │ │
│  │  │  │  │         ▼                               │  │  │ │ │
│  │  │  │  │  ┌─────────────────────────────────┐   │  │  │ │ │
│  │  │  │  │  │        Flask Application        │   │  │  │ │ │
│  │  │  │  │  │  ┌───────────┬───────────────┐  │   │  │  │ │ │
│  │  │  │  │  │  │   API     │   Static      │  │   │  │  │ │ │
│  │  │  │  │  │  │  Routes   │   Files       │  │   │  │  │ │ │
│  │  │  │  │  │  └───────────┴───────────────┘  │   │  │  │ │ │
│  │  │  │  │  └─────────────────────────────────┘   │  │  │ │ │
│  │  │  │  └─────────────────────────────────────────┘  │ │ │
│  │  │  │                      │                         │ │ │
│  │  │  │                      ▼                         │ │ │
│  │  │  │  ┌─────────────────────────────────────────┐  │ │ │
│  │  │  │  │         SQLAlchemy ORM                   │  │ │ │
│  │  │  │  └───────────────────┬─────────────────────┘  │ │ │
│  │  │  └──────────────────────┼────────────────────────┘ │ │
│  │  │                         │                          │ │
│  │  │  ┌──────────────────────▼────────────────────────┐ │ │
│  │  │  │         Volume: /data                         │ │ │
│  │  │  │  ┌─────────────────────────────────────────┐  │ │ │
│  │  │  │  │        SQLite Database                   │  │ │ │
│  │  │  │  │        home_tasks.db                     │  │ │ │
│  │  │  │  └─────────────────────────────────────────┘  │ │ │
│  │  │  └───────────────────────────────────────────────┘ │ │
│  │  └─────────────────────────────────────────────────────┘ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │                    PVC: home-tasks-pvc                 │   │
│  │                    (1Gi, ReadWriteOnce)               │   │
│  └───────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

---

## Apéndice C: Checklist de Implementación

### Backend
- [ ] Configurar Flask application factory
- [ ] Implementar modelos SQLAlchemy
- [ ] Crear endpoints CRUD para personas
- [ ] Crear endpoints CRUD para tareas
- [ ] Implementar algoritmo de asignación
- [ ] Configurar base de datos SQLite con WAL
- [ ] Añadir validación de inputs
- [ ] Implementar health check endpoint
- [ ] Escribir tests unitarios

### Frontend
- [ ] Crear estructura HTML base
- [ ] Integrar Alpine.js
- [ ] Implementar gestión de personas
- [ ] Implementar gestión de tareas
- [ ] Implementar visualización de asignaciones
- [ ] Implementar botón "Asignar"
- [ ] Añadir estilos responsive

### DevOps
- [ ] Crear Dockerfile multi-stage
- [ ] Configurar .dockerignore
- [ ] Crear docker-compose para desarrollo
- [ ] Crear Helm chart
- [ ] Configurar PVC para persistencia
- [ ] Configurar probes de salud
- [ ] Documentar despliegue

### Documentación
- [ ] README con instrucciones
- [ ] Comentarios en código
- [ ] API documentation (OpenAPI opcional)
- [ ] Guía de troubleshooting

---

## Historial de Versiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0.0 | 2026-03-22 | Versión inicial del documento de arquitectura |

---

**Fin del Documento**