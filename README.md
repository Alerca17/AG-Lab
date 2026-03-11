# AG Lab — Algoritmos Genéticos

Plataforma con dos algoritmos genéticos visuales, backend en FastAPI y frontend HTML estático servido desde el mismo servidor.

## Estructura

```
ag-lab/
├── main.py              ← API unificada (Mochila + Sensores + archivos estáticos)
├── requirements.txt
├── Procfile             ← comando de arranque para Railway
└── static/
    ├── menu.html        ← Página principal (punto de entrada)
    ├── index.html       ← Problema 1: Mochila
    └── sensores.html    ← Problema 2: Sensores de Calidad del Aire
```

---

## Endpoints de la API

| Método | Ruta                     | Descripción                        |
|--------|--------------------------|------------------------------------|
| GET    | `/api/health`            | Health check                       |
| GET    | `/mochila/items`         | Objetos del problema               |
| POST   | `/mochila/run`           | Ejecuta AG mochila completo        |
| POST   | `/mochila/step`          | Avanza una generación (mochila)    |
| GET    | `/sensores/ubicaciones`  | Ubicaciones disponibles            |
| POST   | `/sensores/run`          | Ejecuta AG sensores completo       |
| POST   | `/sensores/step`         | Avanza una generación (sensores)   |
| GET    | `/docs`                  | Swagger UI (documentación)         |

---

## Ejecutar en local

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Abrir: http://localhost:8000/menu.html

---

## Desplegar en Railway

1. Sube la carpeta `ag-lab/` a un repositorio GitHub
2. En Railway: **New Project → Deploy from GitHub repo**
3. Railway detecta el `Procfile` automáticamente
4. Sin variables de entorno necesarias
5. La app queda en: `https://tu-app.railway.app/menu.html`
