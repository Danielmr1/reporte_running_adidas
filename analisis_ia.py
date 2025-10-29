import streamlit as st
import requests
import pandas as pd
import re
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime

# =========================================
def resumen_texto_para_perplexity_avanzado(resumen, df_sesion):
    if resumen is None or not isinstance(resumen, pd.DataFrame):
        return "Resumen detallado de clusters: No hay datos de resumen."
    if "tipo_sesion" not in resumen.columns or resumen.empty:
        return "Resumen detallado de clusters: No hay clusters con datos."

    lineas = []
    for tipo in resumen["tipo_sesion"]:
        data_cluster = df_sesion[df_sesion["tipo_sesion"] == tipo]
        if data_cluster.empty:
            continue
        dist_media = data_cluster["distancia"].mean()
        ritmo_medio = data_cluster["ritmo"].mean()
        count = len(data_cluster)
        linea = (
            f"Cluster '{tipo}': {count} sesiones, "
            f"distancia media {dist_media:.1f} km, "
            f"ritmo medio {ritmo_medio:.2f} min/km."
        )
        lineas.append(linea)

    if not lineas:
        return "Resumen detallado de clusters: No hay clusters con datos."

    texto = "Resumen detallado de clusters o tipos de sesion:\n" + "\n".join(lineas)
    return texto

def generar_contexto_completo(df_sesion, resumen_clusters=None, resumen_prediccion=None, df_intervalos_prediccion=None):
    partes = []

    # 🔹 Información de filtrado y calidad de los datos
    info_filtrado = (
        "Filtrado de sesiones aplicado:\n"
        "- Solo sesiones de los últimos 12 meses.\n"
        "- Se descartaron sesiones menores a 200 metros.\n"
        "- Se verificó que todas las sesiones sean constantes, "
        "con diferencias entre timestamps menores a 16 segundos (tolerancia 5%)."
    )
    partes.append(info_filtrado)

    # 1) Resumen clusters
    try:
        if resumen_clusters is not None:
            texto_clusters = resumen_texto_para_perplexity_avanzado(resumen_clusters, df_sesion)
        else:
            texto_clusters = "Resumen de clusters: no ejecutado."
    except Exception as e:
        texto_clusters = f"Resumen de clusters: error al generar ({e})."
    partes.append(texto_clusters)

    # 2) Kilómetros por mes
    try:
        texto_km_mes = resumen_kilometros_por_mes_textual(df_sesion)
    except Exception as e:
        texto_km_mes = f"Kilómetros por mes: error al generar ({e})."
    partes.append(texto_km_mes)

    # 3) Resumen detallado de sesiones
    try:
        texto_sesiones = resumen_ia_detallado_sesiones(df_sesion)
    except Exception as e:
        texto_sesiones = f"Resumen detallado de sesiones: error al generar ({e})."
    partes.append(texto_sesiones)

    # 4) Resumen de predicción
    try:
        texto_pred = ""
        if resumen_prediccion:
            texto_pred = resumen_texto_para_prediccion(resumen_prediccion, df_intervalos_prediccion)
    except Exception as e:
        texto_pred = f"Resumen de predicción: error al generar ({e})."
    partes.append(texto_pred)

    contexto_completo = "\n\n".join(partes)
    return contexto_completo


def resumen_kilometros_por_mes_textual(df_sesion):
    return st.session_state.get("resumen_km", "No hay resumen disponible. Ejecuta primero tab_kilometros_por_mes(df_sesion).")

def resumen_texto_para_prediccion(resumen_prediccion, df_intervalos=None):
    if not resumen_prediccion:
        return "No hay resumen de predicción disponible."
    texto = f"Resumen de la predicción: {resumen_prediccion}\n"

    if df_intervalos is not None and not df_intervalos.empty:
        ritmo_min = df_intervalos["ritmo_intervalo"].min()
        ritmo_max = df_intervalos["ritmo_intervalo"].max()
        ritmo_prom = df_intervalos["ritmo_intervalo"].mean()
        num_intervalos = len(df_intervalos)

        texto += (
            f"Se analizaron {num_intervalos} intervalos.\n"
            f"Ritmo mínimo: {ritmo_min:.2f} min/km.\n"
            f"Ritmo máximo: {ritmo_max:.2f} min/km.\n"
            f"Ritmo promedio: {ritmo_prom:.2f} min/km.\n"
        )
    return texto

def resumen_ia_detallado_sesiones(df_sesion):
    if df_sesion is None or df_sesion.empty:
        return "No hay sesiones registradas para generar resumen."

    resumen = []
    total_sesiones = len(df_sesion)
    resumen.append(f"Analizadas {total_sesiones} sesiones registradas.")

    dist_mean = df_sesion["distancia"].mean()
    dist_min = df_sesion["distancia"].min()
    dist_max = df_sesion["distancia"].max()
    resumen.append(f"Distancia promedio: {dist_mean:.2f} km, mínimo: {dist_min:.2f} km, máximo: {dist_max:.2f} km.")

    tiempo_mean = df_sesion["tiempo"].mean()
    tiempo_min = df_sesion["tiempo"].min()
    tiempo_max = df_sesion["tiempo"].max()
    resumen.append(f"Tiempo promedio: {tiempo_mean:.1f} min, mínimo: {tiempo_min:.1f} min, máximo: {tiempo_max:.1f} min.")

    ritmo_mean = df_sesion["ritmo"].mean()
    ritmo_min = df_sesion["ritmo"].min()
    ritmo_max = df_sesion["ritmo"].max()
    resumen.append(f"Ritmo promedio de todas las sesiones: {ritmo_mean:.2f} min/km, mínimo: {ritmo_min:.2f} min/km, máximo: {ritmo_max:.2f} min/km.")

    bins = [0, 5, 10, 15, 21, 42, float('inf')]
    labels = ["0-5km", "5-10km", "10-15km", "15-21km (Media Maratón)", "21-42km (Entre media y maratón)", "Maratón+"]
    df_sesion["rango_distancia"] = pd.cut(df_sesion["distancia"], bins=bins, labels=labels, right=False)
    conteo_rangos = df_sesion["rango_distancia"].value_counts().sort_index()
    sesiones_rangos = ", ".join([f"{label}: {conteo_rangos.get(label, 0)}" for label in labels])
    resumen.append(f"Sesiones por rango de distancia: {sesiones_rangos}.")

    df_sesion['fecha'] = pd.to_datetime(df_sesion['fecha'], errors='coerce')
    num_dias = df_sesion['fecha'].dt.date.nunique()
    fecha_min = df_sesion['fecha'].min().strftime('%Y-%m-%d')
    fecha_max = df_sesion['fecha'].max().strftime('%Y-%m-%d')
    resumen.append(f"Las sesiones cubren un período desde {fecha_min} hasta {fecha_max}, con {num_dias} días únicos de entrenamiento.")

    df_sorted = df_sesion.sort_values("fecha")
    if len(df_sorted) > 1 and "ritmo" in df_sesion.columns:
        cambio_ritmo = df_sorted["ritmo"].iloc[-1] - df_sorted["ritmo"].iloc[0]
        if cambio_ritmo < -0.1:
            resumen.append("Se observa mejora en el ritmo a lo largo del tiempo.")
        elif cambio_ritmo > 0.1:
            resumen.append("Se observa empeoramiento en el ritmo a lo largo del tiempo.")
        else:
            resumen.append("El ritmo se mantiene estable a lo largo del tiempo.")

    return "\n".join(resumen)

# =========================================
# Funciones IA
def analizar_con_perplexity(texto_resumen, pregunta):
    api_key = st.secrets.get("PERPLEXITY_API_KEY", None)
    if not api_key:
        st.error("Falta la clave PERPLEXITY_API_KEY en Streamlit secrets.")
        return None
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    prompt = (
        "Eres un asistente experto en análisis de rendimiento deportivo para corredores. "
        f"Contexto detallado:\n{texto_resumen}\n"
        f"Pregunta: {pregunta}"
    )
    payload = {"model": "sonar-pro", "messages": [{"role": "system", "content": "Eres un asistente experto en análisis de rendimiento deportivo."}, {"role": "user", "content": prompt}], "max_tokens": 200}

    try:
        response = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload, timeout=30)
    except Exception as e:
        st.error(f"Error al conectar con Perplexity: {e}")
        return None

    if response.status_code != 200:
        st.error(f"Error al llamar Perplexity: {response.status_code} - {response.text}")
        return None

    try:
        data = response.json()
        contenido = data.get("choices", [{}])[0].get("message", {}).get("content", None)
        if not contenido:
            st.error("La respuesta de la IA no contiene texto válido.")
            return None
        return contenido
    except Exception as e:
        st.error(f"Error al procesar la respuesta de Perplexity: {e}")
        return None

def tab_analisis_ia(df_sesion):
    resumen = st.session_state.get("resumen_clusters")
    resumen_prediccion = st.session_state.get("resumen_prediccion")
    df_intervalos_prediccion = st.session_state.get("df_intervalos_prediccion")

    if resumen is None:
        st.warning("Primero ejecuta el análisis de clustering en la pestaña correspondiente.")
        return

    texto_resumen_completo = generar_contexto_completo(
        df_sesion,
        resumen_clusters=resumen,
        resumen_prediccion=resumen_prediccion,
        df_intervalos_prediccion=df_intervalos_prediccion
    )

    pregunta = st.text_area("Haz una pregunta sobre tus sesiones de entrenamiento, predicciones o análisis de rendimiento:", height=25)

    # ===========================================================================
    # Mostrar el contexto completo dentro de un expander, elimninar # para que se vea en la app.
    
    # with st.expander("Ver contexto completo (usado para la consulta IA)", expanded=False):
    #     st.code(texto_resumen_completo[:10000])
    # ===========================================================================

    if st.button("Consultar IA"):
        respuesta_ia = manejar_consulta_ia(texto_resumen_completo, pregunta)
        if respuesta_ia:
            st.markdown("### Respuesta IA")
            st.markdown(respuesta_ia)

# =========================================
# Gestión de contador de consultas IA con Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

secret = st.secrets["SERVICE_ACCOUNT_JSON"]
if isinstance(secret, str):
    SERVICE_ACCOUNT_INFO = json.loads(secret)
else:
    SERVICE_ACCOUNT_INFO = secret

SPREADSHEET_ID = st.secrets["SPREADSHEET_ID"]
RANGE_NAME = st.secrets["RANGE_NAME"]

try:
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
except Exception as e:
    st.error(f"Error inicializando conexión con Google Sheets: {e}")
    sheet = None


def leer_contador_gs():
    if sheet is None:
        st.warning("No se pudo conectar con Google Sheets (modo lectura).")
        return {"fecha": "", "contador": 0}
    try:
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])
        if not values or len(values[0]) < 2:
            return {"fecha": "", "contador": 0}
        return {"fecha": values[0][0], "contador": int(values[0][1])}
    except Exception as e:
        st.warning(f"Error leyendo contador de Google Sheets: {e}")
        return {"fecha": "", "contador": 0}

def guardar_contador_gs(fecha, contador):
    if sheet is None:
        st.warning("No se pudo conectar con Google Sheets (modo escritura).")
        return
    try:
        values = [[fecha, str(contador)]]
        body = {"values": values}
        sheet.values().update(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME, valueInputOption="USER_ENTERED", body=body).execute()
    except Exception as e:
        st.warning(f"Error guardando contador en Google Sheets: {e}")

def puede_consultar_ia():
    data = leer_contador_gs()
    hoy = datetime.now().strftime("%Y-%m-%d")
    if data["fecha"] != hoy:
        guardar_contador_gs(hoy, 0)
        return True
    return data["contador"] < 2 # Límite diario de 2 consultas

def incrementar_contador():
    data = leer_contador_gs()
    hoy = datetime.now().strftime("%Y-%m-%d")
    if data["fecha"] != hoy:
        guardar_contador_gs(hoy, 1)
    else:
        guardar_contador_gs(hoy, data["contador"] + 1)

def manejar_consulta_ia(contexto, pregunta):
    if not puede_consultar_ia():
        st.warning("Se alcanzó el límite de consultas diarias a la IA. Intenta mañana.")
        return None
    if pregunta.strip() == "":
        st.warning("Por favor escribe una pregunta antes de consultar la IA.")
        return None

    with st.spinner("Consultando IA..."):
        respuesta = analizar_con_perplexity(contexto, pregunta)
    if respuesta:
        respuesta = truncar_a_frase_completa(respuesta)
        incrementar_contador()
        return respuesta
    else:
        st.error("Error al consultar la IA.")
        return None


def truncar_a_frase_completa(texto):
    """
    Trunca el texto hasta la última oración completa.
    Considera '.', '!' o '?' como final de oración, 
    ignorando puntos que forman parte de números decimales.
    """
    # Buscar los signos de puntuación que terminan oraciones
    # Solo cuentan si van seguidos de un espacio + letra mayúscula o final de texto
    matches = list(re.finditer(r'([.!?])(?=\s+[A-Z]|$)', texto))
    if matches:
        pos_max = matches[-1].end()
        return texto[:pos_max]
    else:
        return texto

