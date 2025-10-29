import streamlit as st
import pandas as pd
import numpy as np
import re

from bokeh.models import (
    ColumnDataSource, 
    FuncTickFormatter, 
    LinearAxis, 
    Range1d, 
    WheelZoomTool, 
    Span, 
    Label,
    HoverTool
)

from bokeh.plotting import figure
from bokeh.palettes import Category10, Category20, Turbo256
from scipy.stats import norm
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Alto estándar para gráficos
PLOT_HEIGHT = 350

# ===========================

def minseg_formatter():
    """
    Devuelve un formatter para mostrar valores decimales de minutos
    en formato min:seg (ej. 5.25 -> '5:15').
    """
    return FuncTickFormatter(code="""
        var minutos = Math.floor(tick);
        var segundos = Math.round((tick - minutos) * 60);
        if (segundos < 10) {
            return minutos + ":0" + segundos;
        } else {
            return minutos + ":" + segundos;
        }
    """)

# ===========================

def ritmo_decimal_a_min_seg(decimal_ritmo):
    minutos = int(decimal_ritmo)
    segundos = int(round((decimal_ritmo - minutos) * 60))
    return f"{minutos}:{segundos:02d}"

# ========================
def ritmo_decimal_a_hora_min_seg(minutos_decimales):
    horas = int(minutos_decimales // 60)
    minutos = int(minutos_decimales % 60)
    segundos = int(round((minutos_decimales - int(minutos_decimales)) * 60))
    return f"{horas}:{minutos:02d}:{segundos:02d}"

# ===========================

def tab_kilometros_por_mes(df_sesion):
    """
    Genera un gráfico Bokeh con kilómetros mensuales y acumulados.
    Adaptable al ancho de pantalla.
    Además guarda el resumen en st.session_state["resumen_km"] para no recalcularlo.
    """
    # Validación de datos
    if (df_sesion is None or 
        df_sesion.empty or 
        'fecha' not in df_sesion.columns or 
        'distancia' not in df_sesion.columns):
        
        return figure(
            title="⚠️ No hay datos disponibles",
            height=PLOT_HEIGHT,
            toolbar_location=None,
            sizing_mode="stretch_width"
        )
    
    # Copia para evitar modificar el DataFrame original
    df = df_sesion.copy()
    
    # Conversión de fechas
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    df = df.dropna(subset=['fecha', 'distancia'])
    
    if df.empty:
        return figure(
            title="⚠️ No hay fechas válidas en los datos",
            height=PLOT_HEIGHT,
            toolbar_location=None,
            sizing_mode="stretch_width"
        )
    
    # Generación de rango de meses
    hoy = pd.Timestamp(datetime.now())
    meses = pd.date_range(end=hoy, periods=12, freq='MS').strftime('%Y-%m').tolist()
    
    # Agrupación y merge
    df['mes'] = df['fecha'].dt.to_period('M').astype(str)
    df['año'] = df['fecha'].dt.year
    km_por_mes = df.groupby('mes', as_index=False)['distancia'].sum()
    sesiones_por_mes = df.groupby('mes', as_index=False)['distancia'].count()
    
    df_completo = pd.DataFrame({'mes': meses})
    km_por_mes = df_completo.merge(km_por_mes, on='mes', how='left').fillna(0)
    sesiones_por_mes = df_completo.merge(sesiones_por_mes, on='mes', how='left').fillna(0)
    km_por_mes['distancia_acum'] = km_por_mes['distancia'].cumsum()
    km_por_mes['sesiones'] = sesiones_por_mes['distancia']
    
    # --- Resumen anual ---
    resumen_anual = df.groupby('año').agg(distancia=('distancia', 'sum'), sesiones=('distancia', 'count')).reset_index()
    resumen_anual['distancia'] = resumen_anual['distancia'].round(1)
    
    # --- Mes más y menos activo ---
    if (km_por_mes['distancia'] == 0).any():
        meses_minimos = km_por_mes.loc[km_por_mes['distancia'] == 0, 'mes'].tolist()
        mes_min_txt = ", ".join(meses_minimos)
        valor_min = 0.0
    else:
        mes_min = km_por_mes.loc[km_por_mes['distancia'].idxmin()]
        mes_min_txt = mes_min['mes']
        valor_min = mes_min['distancia']
    
    mes_max = km_por_mes.loc[km_por_mes['distancia'].idxmax()]
    
    # Construir resumen textual
    lineas = ["Resumen anual:"]
    for _, row in resumen_anual.iterrows():
        lineas.append(f"- {row['año']}: {row['distancia']} km ({row['sesiones']} sesiones)")
    
    lineas.append("\nKilómetros por mes:")
    for _, row in km_por_mes.iterrows():
        sesiones_txt = f"{int(row['sesiones'])} sesión" if row['sesiones'] == 1 else f"{int(row['sesiones'])} sesiones"
        lineas.append(f"- {row['mes']}: {row['distancia']} km ({sesiones_txt}, acumulado: {row['distancia_acum']} km)")
    
    lineas.append(f"\nMes más activo: {mes_max['mes']} ({mes_max['distancia']} km)")
    lineas.append(f"Mes menos activo: {mes_min_txt} ({valor_min} km)")
    
    # Guardar resumen en session_state
    st.session_state["resumen_km"] = "\n".join(lineas)
    
    # --- CREACIÓN DEL GRÁFICO --- (sin cambios)
    max_mensual = km_por_mes['distancia'].max()
    max_acumulado = km_por_mes['distancia_acum'].max()
    
    y_max_mensual = max_mensual * 1.2 if max_mensual > 0 else 10
    y_max_acumulado = max_acumulado * 1.2 if max_acumulado > 0 else 10
    
    source = ColumnDataSource(km_por_mes)
    
    p = figure(
        x_range=meses,
        height=PLOT_HEIGHT,
        toolbar_location=None,
        tools="",
        sizing_mode="stretch_width"
    )
    
    p.vbar(
        x='mes',
        top='distancia',
        width=0.8,
        color="#1976d2",
        source=source,
        legend_label="Kilómetros mensuales",
        alpha=0.8
    )
    
    p.y_range = Range1d(0, y_max_mensual)
    p.yaxis.axis_label = "Kilómetros mensuales"
    p.yaxis.major_label_text_color = "#1976d2"
    
    p.extra_y_ranges = {"acumulados": Range1d(start=0, end=y_max_acumulado)}
    p.line(
        x='mes',
        y='distancia_acum',
        color="#FF8C00",
        line_width=3,
        legend_label="Kilómetros acumulados",
        source=source,
        y_range_name="acumulados"
    )
    
    p.circle(
        x='mes',
        y='distancia_acum',
        size=6,
        color="#FF8C00",
        source=source,
        y_range_name="acumulados"
    )
    
    eje_derecho = LinearAxis(
        y_range_name="acumulados",
        axis_label="Kilómetros acumulados",
        major_label_text_color="#FF8C00"
    )
    p.add_layout(eje_derecho, 'right')
    
    p.xaxis.axis_label = "Año-Mes"
    p.xaxis.major_label_orientation = 0.8
    p.xgrid.grid_line_color = None
    
    p.legend.location = "top_left"
    p.legend.click_policy = "hide"
    p.legend.background_fill_alpha = 0.8
    
    hover = HoverTool(
        tooltips=[
            ("Año-Mes", "@mes"),
            ("Km mensuales", "@distancia{0,0.0} km"),
            ("Km acumulados", "@distancia_acum{0,0.0} km")
        ],
        mode='vline'
    )
    p.add_tools(hover)
    
    p.background_fill_color = "#f9f9f9"
    p.border_fill_color = "white"
    
    return p

# ============================  

def extraer_fecha_desde_archivo(nombre_archivo):
    """Extrae la fecha UTC desde nombres tipo 2024-12-25_22-08-05-UTC_xxxxxx.json"""
    match = re.search(r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})-UTC", nombre_archivo)
    if not match:
        return pd.NaT
    try:
        return pd.to_datetime(match.group(1), format="%Y-%m-%d_%H-%M-%S")
    except Exception:
        return pd.NaT

# ==============================

def calcular_desniveles(df_granular, id_sesion=None):
    """
    Calcula el desnivel positivo (elev_gain) y negativo (elev_loss)
    a partir de la columna 'altitude', aplicando suavizado y filtrado
    para eliminar ruido de GPS.
    """

    if "altitude" not in df_granular.columns or df_granular["altitude"].isna().all():
        return {"elev_gain": 0.0, "elev_loss": 0.0}

    try:
        # --- Suavizar señal de altitud ---
        alt = df_granular["altitude"].interpolate().to_numpy()

        # Eliminar saltos espurios mayores a 5 m por muestra consecutiva
        diffs = np.diff(alt)
        diffs = np.clip(diffs, -5, 5)  # Limita cambios por muestra a ±5 m

        # Filtrar pequeñas variaciones (<0.3 m) que son ruido típico de GPS
        diffs[np.abs(diffs) < 0.3] = 0

        elev_gain = np.sum(diffs[diffs > 0])
        elev_loss = -np.sum(diffs[diffs < 0])

        # --- Evitar valores absurdos ---
        # Si el desnivel supera 150 m por km → probablemente error
        distancia_total_km = df_granular["distance"].iloc[-1] / 1000 if "distance" in df_granular.columns else 1
        if distancia_total_km > 0 and elev_gain / distancia_total_km > 150:
            elev_gain = elev_loss = 0

        return {"elev_gain": float(elev_gain), "elev_loss": float(elev_loss)}

    except Exception as e:
        print(f"⚠️ Error calculando desniveles para sesión {id_sesion}: {e}")
        return {"elev_gain": 0.0, "elev_loss": 0.0}

# =====================================

def tab_prediccion(df_sesion, distancia_objetivo, df_granular, color_principal="#6A994E"):
    if df_sesion is None or df_sesion.empty:
        return None, None, "⚠️ No hay datos de sesiones para esta distancia."

    cercanos = df_sesion

    elevaciones = []
    for _, fila in cercanos.iterrows():
        archivo = fila["archivo"]
        df_gran_sesion = df_granular[df_granular["archivo"] == archivo]
        if df_gran_sesion.empty:
            elevaciones.append({"elev_gain": np.nan, "elev_loss": np.nan})
            continue
        try:
            desnivel = calcular_desniveles(df_gran_sesion, archivo)
        except Exception as e:
            print(f"⚠️ Error calculando desnivel para {archivo}: {e}")
            desnivel = {"elev_gain": np.nan, "elev_loss": np.nan}
        elevaciones.append(desnivel)

    cercanos = cercanos.copy()
    cercanos.loc[:, "elev_gain"] = [e["elev_gain"] for e in elevaciones]
    cercanos.loc[:, "elev_loss"] = [e["elev_loss"] for e in elevaciones]

    # --- Cálculo base de predicción ---
    ritmo_promedio = cercanos["ritmo"].mean()
    elev_prom = cercanos["elev_gain"].mean()
    ajuste_desnivel = 1 + (elev_prom / 1000 * 0.015)
    ritmo_ajustado = ritmo_promedio * ajuste_desnivel
    tiempo_estimado_min = distancia_objetivo * ritmo_ajustado

    # --- Preparación de gráficos ---
    archivos_usados = cercanos["archivo"].unique()
    N = len(archivos_usados)
    registros = []

    for archivo in archivos_usados:
        df_temp = df_granular[df_granular["archivo"] == archivo].copy()
        if df_temp.empty or "distance" not in df_temp.columns or "duration_s" not in df_temp.columns:
            continue

        df_temp = df_temp.sort_values("timestamp").reset_index(drop=True)
        dist = df_temp["distance"].to_numpy()
        dur = df_temp["duration_s"].to_numpy()
        if len(dist) < 2:
            continue

        distancia_total_km = dist[-1] / 1000.0
        tiempo_anterior = 0.0
        ultimo_idx = 0
        fecha = extraer_fecha_desde_archivo(archivo)

        # Intervalo inicial (0.1 km)
        idx_01 = np.argmax(dist >= 100)
        if dist[idx_01] >= 100:
            tiempo_actual = dur[idx_01]
            tiempo_segmento = tiempo_actual - tiempo_anterior
            ritmo = (tiempo_segmento / (dist[idx_01] - dist[0])) * 1000 / 60
            registros.append({"archivo": archivo, "fecha": fecha, "intervalo": 0.1, "ritmo_intervalo": ritmo})
            tiempo_anterior = tiempo_actual
            ultimo_idx = idx_01

        # Cada kilómetro
        for km in range(1, int(np.floor(distancia_total_km)) + 1):
            idxs = np.where(dist >= km * 1000)[0]
            if len(idxs) == 0:
                continue
            idx_fin = idxs[0]
            if idx_fin <= ultimo_idx:
                continue
            tiempo_actual = dur[idx_fin]
            distancia_segmento = dist[idx_fin] - dist[ultimo_idx]
            if distancia_segmento <= 0:
                continue
            tiempo_segmento = tiempo_actual - tiempo_anterior
            ritmo = (tiempo_segmento / distancia_segmento) * 1000 / 60
            registros.append({"archivo": archivo, "fecha": fecha, "intervalo": float(km), "ritmo_intervalo": ritmo})
            tiempo_anterior = tiempo_actual
            ultimo_idx = idx_fin

        # Segmento final
        distancia_restante = dist[-1] - dist[ultimo_idx]
        if distancia_restante >= 50:
            tiempo_final = dur[-1]
            tiempo_segmento = tiempo_final - tiempo_anterior
            ritmo = (tiempo_segmento / distancia_restante) * 1000 / 60
            registros.append(
                {"archivo": archivo, "fecha": fecha, "intervalo": distancia_total_km, "ritmo_intervalo": ritmo}
            )

    if not registros:
        return None, None, "⚠️ No se pudieron calcular los ritmos por kilómetro."

    df_intervalos = pd.DataFrame(registros)
    dist_max = df_intervalos["intervalo"].max()
    df_intervalos["intervalo_redondeado"] = df_intervalos["intervalo"].apply(
        lambda x: x if np.isclose(x, dist_max) or x <= 0.2 else round(x)
    )

    df_prom = (
        df_intervalos.groupby("intervalo_redondeado", as_index=False)
        .agg(ritmo_prom=("ritmo_intervalo", "mean"), ritmo_std=("ritmo_intervalo", "std"))
    )
    df_prom["ritmo_min"] = df_prom["ritmo_prom"] - df_prom["ritmo_std"]
    df_prom["ritmo_max"] = df_prom["ritmo_prom"] + df_prom["ritmo_std"]

    # --- Ajuste para línea y área hasta distancia objetivo o máxima ---
    max_dist_sesiones = df_intervalos["intervalo"].max()
    try:
        dist_obj_val = float(np.ravel(distancia_objetivo)[0])
    except Exception:
        dist_obj_val = float(distancia_objetivo) if np.isscalar(distancia_objetivo) else np.nan

    limite_linea = min(dist_obj_val, max_dist_sesiones)

    df_prom_filtrado = df_prom[df_prom["intervalo_redondeado"] <= limite_linea]

    ritmo_min_global = df_intervalos["ritmo_intervalo"].min()
    ritmo_max_global = df_intervalos["ritmo_intervalo"].max()
    y_min = ritmo_min_global - 1.0
    y_max = ritmo_max_global + 1.0

    # --- Gráfico principal ---
    import colorsys
    rgb = tuple(int(color_principal.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
    color_oscuro = '#%02x%02x%02x' % tuple(int(c*255) for c in colorsys.hls_to_rgb(h, max(0, l-0.2), s))

    p1 = figure(
        title=f"{N} sesiones utilizadas en la predicción",
        x_axis_label="Distancia (km)",
        y_axis_label="Ritmo (min/km)",
        height=PLOT_HEIGHT - 50,
        y_range=(y_min, y_max),
        x_range=(0, limite_linea + 0.2),
        toolbar_location=None,
        sizing_mode="stretch_width"
    )

    p1.varea(
        x=df_prom_filtrado["intervalo_redondeado"],
        y1=df_prom_filtrado["ritmo_min"],
        y2=df_prom_filtrado["ritmo_max"],
        fill_alpha=0.9,
        color=color_principal
    )
    p1.line(df_prom_filtrado["intervalo_redondeado"], df_prom_filtrado["ritmo_prom"], line_width=2, color=color_oscuro)

    p1.xaxis.ticker = list(np.arange(0, int(np.ceil(limite_linea)) + 1))
    p1.yaxis.formatter = minseg_formatter()

    # --- Segundo gráfico ---
    ritmos_min = df_intervalos["ritmo_intervalo"].dropna()
    hist, edges = np.histogram(ritmos_min, bins=20)
    ritmo_str = ritmo_decimal_a_min_seg(ritmo_ajustado)
    tiempo_str = ritmo_decimal_a_hora_min_seg(tiempo_estimado_min)

    p2 = figure(
        title="Histograma de ritmos por intervalo",
        x_axis_label="Ritmo (min/km)",
        y_axis_label="Frecuencia",
        height=PLOT_HEIGHT - 50,
        toolbar_location=None,
        sizing_mode="stretch_width"
    )

    p2.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
            fill_color="#F7C948", line_color="#5F4B8B", alpha=1)
    mu, std = norm.fit(ritmos_min)
    x = np.linspace(float(ritmos_min.min()), float(ritmos_min.max()), 100)
    y = norm.pdf(x, mu, std) * len(ritmos_min) * (edges[1] - edges[0])
    p2.line(x, y, line_color="red", line_width=2)

    p2.add_layout(Span(location=ritmo_ajustado, dimension='height', line_color="#B22222",
                       line_dash='dashed', line_width=3))
    p2.add_layout(Label(
        x=ritmo_ajustado + 0.01, y=max(hist) * 0.95,
        text=f"Ritmo estimado: {ritmo_str} min/km",
        text_color="#5F4B8B", angle=0, x_offset=10,
        background_fill_color="white", background_fill_alpha=0.7
    ))

    p2.xaxis.formatter = minseg_formatter()
    p2.add_tools(WheelZoomTool())

    # --- Resumen ---
    resumen = f"Tiempo estimado: {tiempo_str} (h:m:s)"

    # Guardar en session_state
    resumen_contexto = f"Tiempo estimado para {dist_obj_val:.1f} km: {tiempo_str} (h:m:s)"
    st.session_state["resumen_prediccion"] = resumen_contexto

    return p1, p2, resumen

# ==========================
def mostrar_tabla_resumen_con_expansion(df_sesion):
    
    MES_NOMBRES = [
        "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]

    ICONO_SVG = (
        '<svg xmlns="http://www.w3.org/2000/svg" height="22px" viewBox="0 -960 960 960" '
        'width="40px" fill="#434343">'
        '<path d="m216-160-56-56 384-384H440v80h-80v-160h233q16 0 31 6t26 17l120 '
        '119q27 27 66 42t84 16v80q-62 0-112.5-19T718-476l-40-42-88 88 90 90-262 '
        '151-40-69 172-99-68-68-266 265Zm-96-280v-80h200v80H120ZM40-560v-80h200v80H40Zm739-80q-33 '
        '0-57-23.5T698-720q0-33 24-56.5t57-23.5q33 0 57 23.5t24 56.5q0 33-24 56.5T779-640Zm-659-40v-80h200v80H120Z"/>'
        '</svg>'
    )

    if df_sesion is None or df_sesion.empty:
        st.info("No hay sesiones registradas.")
        return

    df = df_sesion.copy()

    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    else:
        df['fecha'] = pd.NaT

    if 'distancia' not in df.columns and 'distance' in df.columns:
        df['distancia'] = df['distance']
    df['distancia'] = pd.to_numeric(df.get('distancia', 0), errors='coerce').round(2)

    if 'tiempo' in df.columns:
        df['tiempo'] = pd.to_numeric(df['tiempo'], errors='coerce')
    elif 'time' in df.columns:
        df['tiempo'] = pd.to_numeric(df['time'], errors='coerce')
    elif 'duration' in df.columns:
        dur = pd.to_numeric(df['duration'], errors='coerce')
        df['tiempo'] = dur.apply(lambda x: (x / 1000 / 60)
                                 if pd.notna(x) and abs(x) > 1000
                                 else (x / 60 if pd.notna(x) and abs(x) > 100 else x))
    else:
        df['tiempo'] = pd.NA

    if 'archivo' not in df.columns and 'file' in df.columns:
        df['archivo'] = df['file']
    if 'archivo' not in df.columns:
        df['archivo'] = df.index.astype(str)

    def _mes_anio_from_row(row):
        try:
            mn = int(row['fecha'].month)
            y = int(row['fecha'].year)
            if 1 <= mn <= 12:
                return f"{MES_NOMBRES[mn].capitalize()} {y}"
            return "Sin fecha"
        except Exception:
            return "Sin fecha"

    df['mes_anio'] = df.apply(_mes_anio_from_row, axis=1)
    df['mes_num'] = df['fecha'].dt.month.fillna(0).astype(int)
    df['anio'] = df['fecha'].dt.year.fillna(0).astype(int)

    resumen = (
        df.groupby(['anio', 'mes_num', 'mes_anio'], dropna=False)
          .agg(sesiones=('archivo', 'count'), distancia_total=('distancia', 'sum'))
          .reset_index()
          .sort_values(['anio', 'mes_num'], ascending=[False, False])
    )

    st.markdown("""
    <style>
    .streamlit-expanderHeader {
        border-left: 4px solid #007BFF !important;
        padding-left: 10px !important;
        text-transform: uppercase !important;
        font-weight: 700 !important;
        letter-spacing: 0.3px !important;
    }
    .sesion-row { display:flex; justify-content:space-between; align-items:center;
                  padding:6px 0; border-bottom:1px solid #eee; }
    .sesion-left { display:flex; align-items:center; gap:10px; }
    .sesion-info { line-height:1.2; }
    .sesion-info strong { font-size:15px; }
    .sesion-date { text-align:right; color:#555; font-size:13px; min-width:70px; }
    </style>
    """, unsafe_allow_html=True)

    for _, fila in resumen.iterrows():
        mes_num = int(fila['mes_num'])
        anio = int(fila['anio'])
        sesiones = int(fila['sesiones'])
        distancia_total = float(fila['distancia_total']) if not pd.isna(fila['distancia_total']) else 0.0

        mes_nombre_upper = MES_NOMBRES[mes_num].upper() if 1 <= mes_num <= 12 else "SIN FECHA"
        # Orden correcto: barra + mes/año + distancia + sesiones
        titulo = f"┃ {mes_nombre_upper} {anio} • {distancia_total:.2f} km • {sesiones} sesiones"

        with st.expander(titulo):
            df_mes = df[(df['mes_num'] == mes_num) & (df['anio'] == anio)].sort_values('fecha', ascending=False)
            if df_mes.empty:
                st.info("No hay sesiones para este mes.")
                continue

            for _, s in df_mes.iterrows():
                try:
                    dist_text = f"{float(s['distancia']):.2f} km"
                except Exception:
                    dist_text = "-"

                tiempo_val = s.get('tiempo', None)
                tiempo_text = ritmo_decimal_a_hora_min_seg(tiempo_val)
                fecha_text = s['fecha'].strftime("%d/%m/%y") if pd.notna(s['fecha']) else "-"

                st.markdown(
                    f"""
                    <div class="sesion-row">
                        <div class="sesion-left">
                            <div class="sesion-icon">{ICONO_SVG}</div>
                            <div class="sesion-info">
                                <strong>{dist_text}</strong><br>
                                <span style="color:#444;">{tiempo_text}</span>
                            </div>
                        </div>
                        <div class="sesion-date">{fecha_text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

# =======================
def get_palette(n):
    if n in Category10:
        return Category10[n]
    elif n in Category20:
        return Category20[n]
    elif n < 3:
        return ["#1f77b4", "#ff7f0e"]
    else:
        step = len(Turbo256) // n
        return [Turbo256[i * step] for i in range(n)]

# ==========================
def tab_clustering(df_sesion, solo_objeto=False):
    ICONO_SESION = (
        '<svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" '
        'width="40px" fill="#264653">'
        '<path d="M320-360h66.67v-126.67H556v90L680-520 556-644v90.67H353.33q-14.16 0-23.75 9.58Q320-534.17 320-520v160Z"/>'
        '</svg>'
    )

    if not {"distancia", "ritmo"}.issubset(df_sesion.columns):
        st.warning("No se encontraron las columnas 'distancia' y 'ritmo'.")
        return None, None, None

    X = df_sesion[["distancia", "ritmo"]].copy().dropna()
    if len(X) < 3:
        st.info("Se necesitan al menos 3 sesiones para agrupar.")
        return None, None, None

    # Escalamiento y clustering
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    silhouette_scores = []
    possible_k = range(2, min(8, len(X_scaled)))
    for k in possible_k:
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        silhouette_scores.append((k, score))
    best_k = max(silhouette_scores, key=lambda x: x[1])[0]

    model_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    df_sesion["cluster"] = model_final.fit_predict(X_scaled)

    # Asignar nombres a clusters
    cluster_stats = df_sesion.groupby("cluster").agg({"distancia":"mean","ritmo":"mean"}).reset_index()
    def asignar_nombre_cluster(dist_media, ritmo_medio):
        if dist_media < 3:
            return "Sprint / Muy Corta"
        elif dist_media < 6:
            return "Corta / Rápida" if ritmo_medio < 5.0 else "Corta / Suave"
        elif dist_media < 10:
            return "Media / Rápida" if ritmo_medio < 5.5 else "Media / Moderada"
        elif dist_media < 15:
            return "10K / Tempo" if ritmo_medio < 5.5 else "10K / Base"
        elif dist_media < 25:
            return "Media Maratón / Tempo" if ritmo_medio < 6.0 else "Larga / Constante"
        else:
            return "Maratón / Competencia" if ritmo_medio < 6.0 else "Muy Larga / Recuperación"

    nombre_clusters = {row["cluster"]: asignar_nombre_cluster(row["distancia"], row["ritmo"]) 
                       for _, row in cluster_stats.iterrows()}
    df_sesion["tipo_sesion"] = df_sesion["cluster"].map(nombre_clusters)

    # Resumen y paleta
    resumen = df_sesion.groupby("tipo_sesion").agg(
        distancia_media=("distancia", "mean"),
        ritmo_medio=("ritmo", "mean"),
        cantidad_sesiones=("archivo", "count"),
        cluster_id=("cluster", "first")
    ).reset_index()
    resumen["distancia_media"] = resumen["distancia_media"].round(1)
    resumen["ritmo_medio"] = resumen["ritmo_medio"].apply(ritmo_decimal_a_min_seg)

    # Ordenar tipo_orden por distancia_media ascendente
    tipo_orden = resumen.sort_values("distancia_media")["tipo_sesion"].tolist()
    palette = get_palette(len(tipo_orden))
    color_map = {tipo: palette[i] for i, tipo in enumerate(tipo_orden)}

    # Límites del gráfico
    x_min, x_max = 0, df_sesion["distancia"].max() + 1
    ritmo_min = df_sesion["ritmo"].min()
    ritmo_max = df_sesion["ritmo"].max()
    y_min = max(0, ritmo_min - 0.5)
    y_max = ritmo_max + 0.5

    p = figure(
        height=PLOT_HEIGHT,
        x_axis_label="Distancia (km)", y_axis_label="Ritmo (min/km)",
        toolbar_location=None,
        x_range=(x_min, x_max), y_range=(y_min, y_max),
        sizing_mode="stretch_width"
    )
    p.yaxis.formatter = minseg_formatter()

    # Dibujar elipses/áreas primero
    max_width = (x_max - x_min) / 2
    max_height = (y_max - y_min) / 2
    for tipo, cluster_data in df_sesion.groupby("tipo_sesion"):
        color = color_map[tipo]
        x = cluster_data["distancia"].values
        y = cluster_data["ritmo"].values

        if len(x) >= 3:
            cov = np.cov(x, y)
            vals, vecs = np.linalg.eigh(cov)
            order = vals.argsort()[::-1]
            vals, vecs = vals[order], vecs[:, order]
            theta = np.degrees(np.arctan2(*vecs[:,0][::-1]))
            width, height = 2.0*np.sqrt(vals)
        elif len(x) == 2:
            width = min(abs(x[1]-x[0]) + 0.1, max_width)
            height = min(abs(y[1]-y[0]) + 0.1, max_height)
            theta = 0
        else:  # 1 punto
            width = height = 0.4
            theta = 0

        t = np.linspace(0, 2*np.pi, 100)
        ellipse_x = width*np.cos(t)
        ellipse_y = height*np.sin(t)
        rot = np.radians(theta)
        x_rot = ellipse_x*np.cos(rot) - ellipse_y*np.sin(rot) + np.mean(x)
        y_rot = ellipse_x*np.sin(rot) + ellipse_y*np.cos(rot) + np.mean(y)

        p.patch(
            x_rot, y_rot, fill_color=color, fill_alpha=0.15,
            line_color=color, line_alpha=0.3, line_width=1.2
        )

    # Dibujar puntos encima
    for tipo, cluster_data in df_sesion.groupby("tipo_sesion"):
        color = color_map[tipo]
        source = ColumnDataSource(cluster_data)
        p.circle(x="distancia", y="ritmo", size=9, color=color, alpha=0.8,
                 legend_label=tipo, source=source)

    p.legend.title = "Tipos de sesión"
    p.legend.location = "top_left"
    p.legend.click_policy = "hide"

    # Forzar orden en la leyenda según tipo_orden
    p.legend.items = [
        item for tipo in tipo_orden
        for item in p.legend.items if item.label['value'] == tipo
    ]

    # Tarjetas
    if not solo_objeto:
        st.bokeh_chart(p, use_container_width=True)
        st.markdown("""
        <style>
        .sesion-card {display:flex; align-items:center; justify-content:space-between;
        padding:10px 14px; border-radius:12px; margin-bottom:8px;
        box-shadow:0 1px 3px rgba(0,0,0,0.1);}
        .sesion-left { display:flex; align-items:center; gap:12px; min-width:60px; }
        .sesion-tipo { flex:1; font-weight:600; font-size:15px; }
        .sesion-info { flex:1; line-height:1.2; }
        .sesion-count { color:#333; text-align:right; min-width:70px; }
        </style>""", unsafe_allow_html=True)
        # Ordenar resumen según el orden de tipo_orden
        resumen_ordenado = pd.Categorical(resumen["tipo_sesion"], categories=tipo_orden, ordered=True)
        resumen = resumen.loc[resumen_ordenado.argsort()]

        for _, fila in resumen.iterrows():

            tipo=fila["tipo_sesion"]
            dist=fila["distancia_media"]
            ritmo=fila["ritmo_medio"]
            count=fila["cantidad_sesiones"]
            color_hex=color_map.get(tipo,"#888888")
            r,g,b=int(color_hex[1:3],16), int(color_hex[3:5],16), int(color_hex[5:7],16)
            bg_color=f"rgba({r},{g},{b},0.12)"
            sesion_label="sesión" if count==1 else "sesiones"
            st.markdown(
                f"""<div class="sesion-card" style="background-color:{bg_color};">
                <div class="sesion-left">{ICONO_SESION}</div>
                <div class="sesion-tipo">{tipo}</div>
                <div class="sesion-info">{dist:.1f} km (distancia media)<br>{ritmo} min/km (ritmo medio)</div>
                <div class="sesion-count">{count} {sesion_label}</div></div>""",
                unsafe_allow_html=True)
    
    # Guardar en session_state para no recalcular en otras pestañas
    st.session_state["resumen_clusters"] = resumen

    return p, resumen, color_map
