# 🏃 Reporte Running - Análisis Inteligente de Sesiones

Aplicación web interactiva para análisis avanzado de datos de running, desarrollada en Python usando Streamlit, con machine learning e integración IA. Revisa el rendimiento deportivo, visualiza y agrupa sesiones, predice tiempos y ofrece reportes descargables.

## 🚀 Acceso rápido

**[▶️ Abre la app en Streamlit Cloud](https://reporte-running-adidas.streamlit.app/)**

---

## 📋 Descripción

Esta aplicación permite cargar archivos GPS de entrenamiento, analizar tu progreso durante los últimos 12 meses, visualizar tus kilómetros recorridos, agrupar sesiones por tipo (KMeans) y predecir tiempos en distancias populares. Incluye un asistente IA para responder dudas sobre tu entrenamiento.

---

## 🚀 Características principales
- Análisis estadístico y visualización interactiva de sesiones de running.
- Clustering automático de tipos de sesiones.
- Predicción de tiempo en carreras 5K, 10k, media maratón y maratón.
- Reportes descargables en HTML con todos los análisis y gráficos.
- Panel resumen por mes con distancia y cantidad de sesiones.
- Integración de asistente IA para consultas personalizadas con límite diario.
- Importación directa de archivos ZIP de Adidas Running/Runtastic o Google Drive
- Filtros automáticos para calidad y continuidad de datos.


---

## 🛠️ Tecnologías
- **Python 3.11+**
- **Streamlit**
- **Pandas** / **NumPy**
- **scikit-learn** / **SciPy**
- **Bokeh**
- **Perplexity AI** (API)
- **Google Sheets API**
- **timezonefinder**, **pytz**

---

## 📦 Instalación
1. **Clona el repositorio:**
```bash
git clone https://github.com/Danielmr1/version_reporte_ia.git
cd version_reporte_ia
```
2. **Crea entorno virtual:**
```bash
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
```
3. **Instala dependencias:**
```bash
pip install -r requirements.txt
```
4. **Configura variables secretas en `.streamlit/secrets.toml`:**
```toml
PERPLEXITY_API_KEY = "tu_clave_aqui"
SPREADSHEET_ID = "id_de_tu_hoja"
RANGE_NAME = "Hoja1!A1:B1"
[SERVICE_ACCOUNT_JSON]
# credenciales de Google...
```
5. **Ejecuta la aplicación:**
```bash
streamlit run main.py
```

---

## 📁 Estructura del proyecto
```

├── README.md
├── .gitignore
├── requirements.txt
├── main.py
├── file_io.py
├── visualization.py
├── analisis_ia.py
└── .streamlit/
    ├── config.toml
    ├── secrets.example.toml
    └── secrets.toml (no disponible en GitHub por seguridad)


---

## 🔧 Principales módulos
### `main.py`: página principal, interfaz y orquestación
### `file_io.py`: lectura y filtrado inteligente de archivos GPS/JSON
### `visualization.py`: generación de gráficos Bokeh
### `analisis_ia.py`: integración y gestión de consultas IA/ML

---

## 🎯 Formato de datos esperado
- Archivo ZIP de Adidas Running/Runtastic con archivos JSON:
```
Sport-sessions/
└── GPS-data/
    ├── 2024-10-01_08-30-15-UTC_xxxxx.json
    └── ...
```
- Cada JSON debe ser un array con: timestamp, latitud, longitud, altitud, distancia, speed, duration

---

## 🎨 Vista de la aplicación
Incluye pestañas interactivas:
- Tipos de sesión
- Distancia recorrida
- Predicción 5K, 10k, media maratón y maratón (si hay datos)
- Resumen
- Análisis IA

---

## 🔐 Variables secretas
Tabla orientativa:
| Variable | Descripción |
|----------|-------------|
| PERPLEXITY_API_KEY | Clave API de Perplexity |
| SPREADSHEET_ID     | ID Google Sheet para contador |
| RANGE_NAME         | Rango de celdas (ej. "Hoja1!A1:B1") |
| SERVICE_ACCOUNT_JSON | Credenciales Google |

---

## 📝 Licencia
Distribuido bajo Licencia **GNU GPL**. Ver archivo LICENSE para detalles.

---

## 👤 Contacto
morales.124r@gmail.com

---

## 🤝 Colaboraciones/Bugs
Las contribuciones vía Pull Request son bienvenidas. Para reportar errores, abre un issue en [https://github.com/Danielmr1/version_reporte_ia](https://github.com/Danielmr1/reporte_running_adidas).

---

## 🙏 Créditos
- Adidas Running/Runtastic, Streamlit, Bokeh, Perplexity AI

---

**¡Feliz entrenamiento y análisis! 🏃‍♂️**
