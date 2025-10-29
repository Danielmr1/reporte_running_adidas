import zipfile, io, json, pytz
import pandas as pd

from datetime import datetime, timedelta
from timezonefinder import TimezoneFinder

# ==========================
def es_sesion_constante(df_granular, umbral_segundos=16, tolerancia_pct=5):
    if df_granular.empty or "timestamp" not in df_granular.columns:
        return False
    intervalos = df_granular["timestamp"].diff().dt.total_seconds().dropna()
    if intervalos.empty:
        return False
    total = len(intervalos)
    largos = (intervalos > umbral_segundos).sum()
    pct_largos = (largos / total) * 100

    return pct_largos <= tolerancia_pct

# ==========================
def leer_json_granular(data_json, id_sesion=None):
    registros = []
    for rec in data_json:
        r = {
            "timestamp": rec.get("timestamp"),
            "altitude": rec.get("altitude"),
            "distance": rec.get("distance"),
            "speed": rec.get("speed"),
            "duration": rec.get("duration"),
            "id_sesion": rec.get("id_sesion", id_sesion),
            "archivo": rec.get("archivo"),
        }
        registros.append(r)

    df_granular = pd.DataFrame(registros)
    if df_granular.empty:

        return df_granular

    # Convertir de milisegundos a datetime UTC
    df_granular["timestamp"] = pd.to_datetime(df_granular["timestamp"], unit="ms", errors="coerce")

    # duration_s
    if "duration" in df_granular.columns and df_granular["duration"].notna().any():
        df_granular["duration_s"] = df_granular["duration"] / 1000
    else:
        t0 = df_granular["timestamp"].iloc[0]
        df_granular["duration_s"] = (df_granular["timestamp"] - t0).dt.total_seconds()

    # Limpiar nombre de archivo
    df_granular["archivo"] = df_granular["archivo"].astype(str).str.replace("Sport-sessions/GPS-data/", "", regex=False)

    return df_granular

# ==========================
def filtrar_archivos_json_ultimos_12_meses(nombres_archivos):
    hoy = datetime.now()
    limite = hoy - timedelta(days=365)
    archivos_filtrados = []
    eliminados = 0
    for nombre in nombres_archivos:
        if "/GPS-data/" in nombre and nombre.lower().endswith(".json"):
            try:
                fecha_str = nombre.split("/")[-1].split("_")[0]
                fecha_archivo = datetime.strptime(fecha_str, "%Y-%m-%d")
                if fecha_archivo >= limite:
                    archivos_filtrados.append(nombre)
                else:
                    eliminados += 1
            except Exception:
                eliminados += 1
    return archivos_filtrados, eliminados

# ==========================
def leer_datos_zip_filtrado_pausas_unificado(origen_zip):
    """
    Lee un ZIP con JSON de sesiones de running.
    Mantiene timestamps en UTC hasta después del filtro de constancia.
    """

    tf = TimezoneFinder()

    # Detectar si origen_zip es URL de Google Drive
    if isinstance(origen_zip, str) and origen_zip.startswith("http"):
        import re
        import requests
        patron_id = r"/d/([a-zA-Z0-9_-]+)"
        coincidencia = re.search(patron_id, origen_zip)
        if not coincidencia:
            raise ValueError("URL inválida de Google Drive")
        id_archivo = coincidencia.group(1)

        url_descarga = f"https://drive.google.com/uc?export=download&id={id_archivo}"
        res = requests.get(url_descarga)
        res.raise_for_status()
        archivo_zip = zipfile.ZipFile(io.BytesIO(res.content))
    elif isinstance(origen_zip, io.BytesIO):
        archivo_zip = zipfile.ZipFile(origen_zip)
    elif isinstance(origen_zip, str):
        # Ruta local
        with open(origen_zip, "rb") as f:
            archivo_zip = zipfile.ZipFile(io.BytesIO(f.read()))
    else:
        raise TypeError("El parámetro debe ser una URL de Google Drive, ruta local o BytesIO.")

    # Resto del código original sin cambios...
    archivos_json = [n for n in archivo_zip.namelist()
                     if "/GPS-data/" in n and n.lower().endswith(".json")]

    archivos_validos, eliminados_fecha = filtrar_archivos_json_ultimos_12_meses(archivos_json)

    dfs = []
    df_granular_sessions = []
    eliminados_constancia = 0
    eliminados_distancia = 0

    for nombre in archivos_validos:
        with archivo_zip.open(nombre) as f_json:
            data_json = json.load(f_json)

        if not data_json or "distance" not in data_json[-1]:
            eliminados_distancia += 1
            continue
        if data_json[-1]["distance"] < 200:
            eliminados_distancia += 1
            continue

        archivo_simple = nombre.split('/')[-1].replace('.json', '')

        for rec in data_json:
            rec["archivo"] = archivo_simple

        df_granular = leer_json_granular(data_json, id_sesion=archivo_simple)

        if not es_sesion_constante(df_granular, umbral_segundos=16, tolerancia_pct=5):
            eliminados_constancia += 1
            continue

        lat_first = next((p.get("latitude") for p in data_json if p.get("latitude") is not None), None)
        lon_first = next((p.get("longitude") for p in data_json if p.get("longitude") is not None), None)

        if lat_first is not None and lon_first is not None:
            tz_name = tf.timezone_at(lat=lat_first, lng=lon_first)
            tz_local = pytz.timezone(tz_name) if tz_name else pytz.UTC
        else:
            tz_local = pytz.UTC

        df_granular["timestamp"] = (
            df_granular["timestamp"]
            .dt.tz_localize("UTC")
            .dt.tz_convert(tz_local)
            .dt.tz_localize(None)
        )

        df_agg = df_granular.groupby("archivo", as_index=False).agg(
            distancia_total_km=("distance", lambda x: x.max() / 1000),
            tiempo_total_s=("duration_s", "max")
        )

        dfs.append(df_agg)
        df_granular_sessions.append(df_granular)

    if not dfs:
        raise FileNotFoundError("No se encontraron sesiones válidas")

    df_total = pd.concat(dfs, ignore_index=True)
    df_granular_total = pd.concat(df_granular_sessions, ignore_index=True)
    procesados = len(archivos_validos) - eliminados_constancia - eliminados_distancia

    return df_total, df_granular_total, archivo_zip, procesados, eliminados_fecha, eliminados_constancia, eliminados_distancia

# ==========================
def obtener_sesiones(df_granular):
    """
    Construye el DataFrame de sesiones resumidas a partir de df_granular.
    Ya se asume que 'timestamp' está en hora local correcta.
    Devuelve df_sesion y subsets por distancia objetivo.
    """
    sesiones_unicas = df_granular["archivo"].unique()
    df_sesion_list = []

    for sesion in sesiones_unicas:
        if not isinstance(sesion, str) or not sesion:
            continue

        df_gran = df_granular[df_granular["archivo"] == sesion].sort_values("timestamp").reset_index(drop=True)
        if df_gran.empty:
            continue

        archivo_limpio = sesion.replace("Sport-sessions/GPS-data/", "")

        # --- fecha de inicio de la sesión ---
        fecha = df_gran["timestamp"].iloc[0]

        # --- cálculos básicos ---
        distancia = df_gran["distance"].iloc[-1] / 1000  # km
        tiempo = df_gran["duration_s"].iloc[-1] / 60  # min
        ritmo = tiempo / distancia if distancia > 0 else None

        # --- armar registro de sesión ---
        df_sesion_list.append({
            "archivo": archivo_limpio,
            "fecha": fecha,
            "distancia": distancia,
            "tiempo": tiempo,
            "ritmo": ritmo,
        })

    df_sesion = pd.DataFrame(df_sesion_list)

    
    # ============================================================
    # Filtrar por distancias objetivo con tolerancia del 10%
    distancias_objetivo = {
        "5K": 5.0,
        "10K": 10.0,
        "21K": 21.0975,
        "42K": 42.195,
    }
    margen = 0.10  # 10% de tolerancia

    df_5k = df_sesion[(df_sesion["distancia"] >= distancias_objetivo["5K"] * (1 - margen)) &
                      (df_sesion["distancia"] <= distancias_objetivo["5K"] * (1 + margen))]

    df_10k = df_sesion[(df_sesion["distancia"] >= distancias_objetivo["10K"] * (1 - margen)) &
                       (df_sesion["distancia"] <= distancias_objetivo["10K"] * (1 + margen))]

    df_21k = df_sesion[(df_sesion["distancia"] >= distancias_objetivo["21K"] * (1 - margen)) &
                       (df_sesion["distancia"] <= distancias_objetivo["21K"] * (1 + margen))]

    df_42k = df_sesion[(df_sesion["distancia"] >= distancias_objetivo["42K"] * (1 - margen)) &
                       (df_sesion["distancia"] <= distancias_objetivo["42K"] * (1 + margen))]

    return df_sesion, df_5k, df_10k, df_21k, df_42k