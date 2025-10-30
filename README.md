# 🏃 Reporte Running - Análisis Inteligente de Sesiones

Aplicación web interactiva para análisis avanzado de datos de running, desarrollada en Python usando Streamlit, con machine learning e integración IA. Revisa el rendimiento deportivo, visualiza y agrupa sesiones, predice tiempos y ofrece reportes descargables.

## 🌐 Acceso rápido

**[▶️ Abre la app en Streamlit Cloud](https://reporte-running-adidas.streamlit.app/)**

*(La aplicación cargará en unos segundos la primera vez)*

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
- Importación directa de archivos ZIP de Adidas Running/Runtastic o Google Drive.
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

### Pasos de instalación

1. **Clona el repositorio:**

```bash
git clone https://github.com/Danielmr1/reporte_running_adidas.git
cd reporte_running_adidas
```

2. **Crea entorno virtual:**

```bash
python -m venv env
env\Scripts\activate
```

3. **Instala dependencias:**

```bash
pip install -r requirements.txt
```

4. **Configura secretos:**

```bash
cp .streamlit/secrets.example.toml .streamlit/secrets.toml
```

Edita `.streamlit/secrets.toml` con tus claves:

```toml
PERPLEXITY_API_KEY = "tu_clave_aqui"
SPREADSHEET_ID = "id_de_tu_hoja"
RANGE_NAME = "Hoja1!A1:B1"

[SERVICE_ACCOUNT_JSON]
type = "service_account"
project_id = "tu-proyecto"
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

5. **Ejecuta la aplicación:**

```bash
streamlit run main.py
```

La app estará disponible en: **http://localhost:8501**

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
    └── secrets.toml (⚠️ no disponible en GitHub por seguridad)
```

---

## 🔧 Descripción de módulos

| Módulo | Descripción |
|--------|-------------|
| **main.py** | Página principal, interfaz y orquestación de la app |
| **file_io.py** | Lectura y filtrado inteligente de archivos GPS/JSON |
| **visualization.py** | Generación de gráficos interactivos con Bokeh |
| **analisis_ia.py** | Integración y gestión de consultas IA/ML |

---

## 📊 Información de la aplicación

| Aspecto | Valor |
|--------|-------|
| **URL en producción** | https://reporte-running-adidas.streamlit.app/ |
| **Repositorio** | https://github.com/Danielmr1/reporte_running_adidas |
| **Límite IA diario** | 3 consultas |
| **Zona horaria** | Europe/London |
| **Ambiente** | Production |

---

## 🎯 Formato de datos esperado

**Archivo ZIP de Adidas Running/Runtastic:**

```
Sport-sessions/
└── GPS-data/
    ├── 2024-10-01_08-30-15-UTC_xxxxx.json
    ├── 2024-10-02_10-45-22-UTC_yyyyy.json
    └── ...
```

**Estructura de cada JSON:**

Array de objetos con: `timestamp`, `latitud`, `longitud`, `altitud`, `distancia`, `speed`, `duration`

---

## 📱 Vista de la aplicación

La app incluye las siguientes pestañas interactivas:

- **Tipos de sesión** - Clustering automático de entrenamientos
- **Distancia recorrida** - Visualización y estadísticas de kilómetros
- **Predicción 5K** - Predicción de tiempo para carrera de 5 kilómetros
- **Predicción 10K** - Predicción de tiempo para carrera de 10 kilómetros
- **Predicción Media Maratón** - Predicción para 21.1 km
- **Predicción Maratón** - Predicción para 42.2 km
- **Resumen** - Panel general de estadísticas
- **Análisis IA** - Asistente inteligente para preguntas sobre tu entrenamiento

---

## 🔐 Variables secretas

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `PERPLEXITY_API_KEY` | Clave API de Perplexity | `sk-xxx...` |
| `SPREADSHEET_ID` | ID de Google Sheet para contador de consultas | `1BxiMVs0XRA5nFMKe5...` |
| `RANGE_NAME` | Rango de celdas en la hoja | `Hoja1!A1:B1` |
| `SERVICE_ACCOUNT_JSON` | Credenciales de Google Service Account | *Objeto JSON completo* |

---

## 🔄 Actualizaciones en producción (Streamlit Cloud)

### ⚠️ Cambios en el código = Actualización automática

Cuando hagas cambios en GitHub (por ejemplo, cambiar el número de consultas de IA), Streamlit Cloud detecta automáticamente los cambios y redeploy sin que hagas nada manualmente.

**Flujo automático:**

```
1. Editas el archivo en GitHub
   └─ Opción A: Con el lápiz ✏️ (cambios rápidos)
      Opción B: En Codespace (cambios complejos)

2. Haces commit y push
   └─ El código se actualiza en GitHub

3. Streamlit Cloud detecta cambios
   └─ Automáticamente (cada 1-2 minutos)

4. Redeploy automático
   └─ Tu app se actualiza en 1-2 minutos

5. La app en producción tiene los cambios
   └─ https://reporte-running-adidas.streamlit.app/
```

---

### 📝 Cambios rápidos en GitHub (cambio mínimo: un número, una línea)

**Para cambios pequeños, edita directamente en GitHub:**

1. Ve a: https://github.com/Danielmr1/reporte_running_adidas
2. Abre el archivo (ej. `analisis_ia.py`)
3. Haz clic en el **lápiz ✏️** (botón editar)
4. Modifica el valor
5. Scroll down → Haz clic en **"Commit changes"**
6. ¡Listo! Streamlit Cloud redeploy automático en 1-2 minutos

**Ventajas:** Rápido, sin conflictos, sin necesidad de Codespace

---

### 🖥️ Cambios complejos en Codespace (múltiples cambios, testing local)

**Para cambios complejos, usa Codespace con testing local:**

```bash
# 1. Abre Codespace
# https://share.streamlit.io/ → En la aplicación → Menu → Edit with Codespaces

# 2. Descarga los cambios remotos (SIEMPRE primero)
git pull

# 3. Edita los archivos que necesites
# (Puedes hacer testing local: streamlit run main.py)

# 4. Guarda y sube los cambios
git add .
git commit -m "Describe tu cambio aquí"
git push

# ¡Listo! Streamlit Cloud detecta y redeploy automático
```

**Ventajas:** Testing local, múltiples cambios, mejor control

---

### ⚠️ Notas importantes sobre Codespace

- **Siempre comienza con `git pull`:** Codespace NO sincroniza automáticamente con GitHub. Si hiciste cambios en GitHub (o desde otra ventana), debes hacer `git pull` para tenerlos localmente.

- **Secuencia correcta:**
  ```bash
  git pull                    # Descargar cambios remotos
  # ... edita archivos ...
  git add .
  git commit -m "tu mensaje"
  git push                    # Subir cambios
  ```

- **Evita conflictos:** No olvides `git pull` antes de empezar a trabajar.

- **Ejemplo real:**
  ```bash
  @Danielmr1 ➜ /workspaces/reporte_running_adidas (main) $ git pull
  @Danielmr1 ➜ /workspaces/reporte_running_adidas (main) $ git add .
  @Danielmr1 ➜ /workspaces/reporte_running_adidas (main) $ git commit -m "Cambio número de consultas"
  @Danielmr1 ➜ /workspaces/reporte_running_adidas (main) $ git push
  ```

---


## 📎 Enlaces útiles

- 📚 [Documentación Streamlit](https://docs.streamlit.io)
- 🤖 [API Perplexity](https://docs.perplexity.ai)
- 🐍 [Documentación Python](https://docs.python.org)
- 📊 [Documentación Bokeh](https://docs.bokeh.org)
- 🔬 [Documentación scikit-learn](https://scikit-learn.org)

---

## 📝 Licencia

Distribuido bajo Licencia **GNU GPL**. Ver archivo `LICENSE` para detalles.

---

## 👤 Contacto

📧 [morales.124r@gmail.com](mailto:morales.124r@gmail.com)

---

## 🤝 Colaboraciones y reporte de bugs

Las contribuciones vía **Pull Request** son bienvenidas. 

Para reportar errores o sugerencias, abre un issue aquí:
[https://github.com/Danielmr1/reporte_running_adidas/issues](https://github.com/Danielmr1/reporte_running_adidas/issues)

---

## 🙏 Créditos

- **Adidas Running/Runtastic** - Datos de entrenamiento
- **Streamlit** - Framework web
- **Bokeh** - Visualizaciones interactivas
- **Perplexity AI** - Asistente IA
- **scikit-learn** - Machine Learning
- **Google Sheets API** - Contador de consultas

---

**¡Feliz entrenamiento y análisis! 🏃‍♂️**
