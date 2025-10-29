import streamlit as st
import pandas as pd
import io
from bokeh.embed import file_html
from bokeh.resources import CDN

from visualization import (
    tab_clustering,
    tab_kilometros_por_mes,
    tab_prediccion,
    mostrar_tabla_resumen_con_expansion,
)

from file_io import (
    leer_datos_zip_filtrado_pausas_unificado,
    obtener_sesiones
)

from analisis_ia import tab_analisis_ia

# ========================
# Íconos SVG para el reporte
ICONO_REPORTE = (
    '<svg xmlns="http://www.w3.org/2000/svg" height="44px" '
    'viewBox="0 -960 960 960" width="44px" fill="#222222" '
    'style="vertical-align:middle;margin-right:10px;">'
    '<path d="M680-330q-50 0-85-35t-35-85q0-50 35-85t85-35q50 0 85 35t35 85q0 50-35 85t-85 35Zm0-60q25.5 0 42.75-17.25T740-450q0-25.5-17.25-42.75T680-510q-25.5 0-42.75 17.25T620-450q0 25.5 17.25 42.75T680-390ZM440-50v-116q0-21 10-39.5t28-29.5q28-17 58-29.5t62-20.5l82 106 82-106q32 8 61.5 20.5T881-235q18 11 28.5 29.5T920-166v116H440Zm60-60h157l-82-106q-20 8-39 17.5T500-178v68Zm203 0h157v-68q-17-11-35.5-20.5T786-216l-83 106Zm-46 0Zm46 0Zm-523-10q-24.75 0-42.37-17.63Q120-155.25 120-180v-600q0-24.75 17.63-42.38Q155.25-840 180-840h600q24.75 0 42.38 17.62Q840-804.75 840-780v247q-11-20-26-37t-34-30v-180H180v600h200v60H180Zm100-500h341q14-5 28.84-7.5T680-630v-50H280v60Zm0 170h220q0-15 2.5-30.5T510-510H280v60Zm0 170h158q17-13 36-21.5t39-16.5v-22H280v60ZM180-180v-600 180-30 450Zm500-270Z"/>'
    '</svg>'
)

ICONO_SESION = (
    '<svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" '
    'width="40px" fill="#264653">'
    '<path d="M320-360h66.67v-126.67H556v90L680-520 556-644v90.67H353.33q-14.16 0-23.75 9.58Q320-534.17 320-520v160ZM479.97-78Q467-78 454.5-82.67q-12.5-4.66-21.83-14l-336-336q-9.34-9.33-14-21.86Q78-467.07 78-480.03q0-12.97 4.67-25.47 4.66-12.5 14-21.83l336-336q9.33-9.34 21.86-14 12.54-4.67 25.5-4.67 12.97 0 25.47 4.67 12.5 4.66 21.83 14l336 336q9.34 9.33 14 21.86 4.67 12.54 4.67 25.5 0 12.97-4.67 25.47-4.66 12.5-14 21.83l-336 336q-9.33 9.34-21.86 14Q492.93-78 479.97-78ZM312-312l168 168 336-336-336-336-336 336 168 168Zm168-168Z"/>'
    '</svg>'
)

ICONO_DISTANCIA = (
    '<svg xmlns="http://www.w3.org/2000/svg" height="40px" '
    'viewBox="0 -960 960 960" width="40px" fill="#264653" '
    'style="vertical-align:middle;margin-right:8px;">'
    '<path d="M653.33-160v-280H800v280H653.33Zm-246.66 0v-640h146.66v640H406.67ZM160-160v-440h146.67v440H160Z"/>'
    '</svg>'
)

ICONO_CLUSTER = (
    '<svg xmlns="http://www.w3.org/2000/svg" height="40px" '
    'viewBox="0 -960 960 960" width="40px" fill="#264653" '
    'style="vertical-align:middle;margin-right:8px;">'
    '<path d="m260.67-524 220-356 220 356h-440Z'
    'M704-80q-74.33 0-125.17-50.83Q528-181.67 528-256t50.83-125.17Q629.67-432 704-432t125.17 50.83Q880-330.33 880-256t-50.83 125.17Q778.33-80 704-80Z'
    'm-584-23.33v-309.34h309.33v309.34H120Z'
    'm584.06-43.34q45.94 0 77.61-31.72 31.66-31.72 31.66-77.67 0-45.94-31.72-77.61-31.72-31.66-77.67-31.66-45.94 0-77.61 31.72-31.66 31.72-31.66 77.67 0 45.94 31.72 77.61 31.72 31.66 77.67 31.66Z'
    'M186.67-170h176v-176h-176v176Z'
    'M380-590.67h201.33L480.67-753.33 380-590.67Z"/>'
    '</svg>'
)

ICONO_PREDICCION = (
    '<svg xmlns="http://www.w3.org/2000/svg" height="40px" '
    'viewBox="0 -960 960 960" width="40px" fill="#264653" '
    'style="vertical-align:middle;margin-right:8px;">'
    '<path d="M360-853.33V-920h240v66.67H360ZM480-80.67q-74 0-139.5-28.5T226-186.67q-49-49-77.5-114.5T120-440.67q0-74 28.5-139.5t77.5-114.5q49-49 114.5-77.5t139.5-28.5q65.33 0 123.67 21.67 58.33 21.67 105.66 61L762-770.67 808.67-724 756-671.33Q792.67-628 816.33-571 840-514 840-440.67q0 74-28.5 139.5T734-186.67q-49 49-114.5 77.5T480-80.67Zm0-66.66q122 0 207.67-85.67 85.66-85.67 85.66-207.67 0-122-85.66-207.66Q602-734 480-734q-122 0-207.67 85.67-85.66 85.66-85.66 207.66T272.33-233Q358-147.33 480-147.33ZM480-440Zm-75.33 151.33L632-441.33l-227.33-152v304.66Z"/>'
    '</svg>'
)

# ==== ICONOS GLOBALES ====
ICONO_CALENDARIO = (
    '<svg xmlns="http://www.w3.org/2000/svg" height="40px" '
    'viewBox="0 -960 960 960" width="40px" fill="#264653" '
    'style="vertical-align:middle;margin-right:8px;">'
    '<path d="M240-280h240v-80H240v80Zm120-160h240v-80H360v80Zm120-160h240v-80H480v80ZM200-120q-33 '
    '0-56.5-23.5T120-200v-560q0-33 23.5-56.5T200-840h560q33 0 '
    '56.5 23.5T840-760v560q0 33-23.5 56.5T760-120H200Zm0-80h560v-560H200v560Zm0-560v560-560Z"/>'
    '</svg>'
)

ICONO_IA = (
    '<svg xmlns="http://www.w3.org/2000/svg" height="40px" viewBox="0 -960 960 960" width="40px" fill="#264653" '
    'style="vertical-align:middle;margin-right:8px;">'
    '<path d="M319-160q-9 0-16.83-4.5Q294.33-169 290-177l-82-146.33h66.67l41.33 80h90.67v-33.34H336l-41.33-80H190l-61-106.66q-2-4.34-3.17-8.34-1.16-4-1.16-8.33 0-2.67 4.33-16.67l61-106.66h104.67l41.33-80h70.67v-33.34H316l-41.33 80H208L290-783q4.33-8 12.17-12.5Q310-800 319-800h111q14.33 0 23.83 9.5 9.5 9.5 9.5 23.83v170h-76.66l-33.34 33.34h110v126.66h-94.66l-39.34-80h-96L200-483.33h108l40 80h115.33v210q0 14.33-9.5 23.83-9.5 9.5-23.83 9.5H319Zm211 0q-14.33 0-23.83-9.5-9.5-9.5-9.5-23.83v-210H612l40-80h108l-33.33-33.34h-96l-39.34 80h-94.66v-126.66h110l-33.34-33.34h-76.66v-170q0-14.33 9.5-23.83 9.5-9.5 23.83-9.5h111q9 0 16.83 4.5Q665.67-791 670-783l82 146.33h-66.67l-41.33-80h-90.67v33.34H624l41.33 80H770l61 106.66q2 4.34 3.17 8.34 1.16 4 1.16 8.33 0 2.67-4.33 16.67l-61 106.66H665.33l-41.33 80h-70.67v33.34H644l41.33-80H752L670-177q-4.33 8-12.17 12.5Q650-160 641-160H530Z"/>'
    '</svg>'
)

# ===========================

# Configuración de página para pantalla completa
st.set_page_config(
    page_title="Reporte de Sesiones",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Ocultar menú, footer y encabezado para más espacio
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Título principal con ícono
st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    </style>
    <div style="
        display: flex;
        align-items: center;
        gap: 12px;
        font-family: 'Inter', sans-serif;
    ">
        {ICONO_REPORTE}
        <h1 style="
            font-size: 1.9rem;
            font-weight: 600;
            color: #264653;
            margin: 0;
        ">
            Reporte Running
        </h1>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Inicialización de variables de sesión ---
for var in ['datos_cargados', 'resumen_visible', 'mostrar_inputs']:
    if var not in st.session_state:
        st.session_state[var] = True if var != 'datos_cargados' else False

# --- Carga de datos ---
if st.session_state['mostrar_inputs']:
    opcion = st.radio(
        "¿Cómo quieres cargar tus datos?",
        ("Pegar enlace de Google Drive", "Subir archivo ZIP desde tu dispositivo")
    )

    if opcion == "Pegar enlace de Google Drive":
        urlzip = st.text_input("Pega la URL de tu archivo ZIP en Google Drive")
        if urlzip and not st.session_state['datos_cargados']:
            try:
                (df, df_granular, archivo_zip,
                 procesados, eliminados_fecha, eliminados_constancia, eliminados_distancia) = \
                    leer_datos_zip_filtrado_pausas_unificado(urlzip)

                st.session_state.update({
                    'df': df,
                    'df_granular': df_granular,
                    'procesados': procesados,
                    'eliminados_fecha': eliminados_fecha,
                    'eliminados_constancia': eliminados_constancia,
                    'eliminados_distancia': eliminados_distancia,
                    'datos_cargados': True,
                    'resumen_visible': True
                })
            except Exception as e:
                st.error(f"❌ Error al procesar los datos desde Google Drive: {e}")
                st.session_state['datos_cargados'] = False

    elif opcion == "Subir archivo ZIP desde tu dispositivo":
        archivo_subido = st.file_uploader("📂 Sube tu archivo ZIP", type="zip")
        if archivo_subido and not st.session_state['datos_cargados']:
            try:
                zip_bytes = io.BytesIO(archivo_subido.read())
                (df, df_granular, archivo_zip,
                 procesados, eliminados_fecha, eliminados_constancia, eliminados_distancia) = \
                    leer_datos_zip_filtrado_pausas_unificado(zip_bytes)

                st.session_state.update({
                    'df': df,
                    'df_granular': df_granular,
                    'procesados': procesados,
                    'eliminados_fecha': eliminados_fecha,
                    'eliminados_constancia': eliminados_constancia,
                    'eliminados_distancia': eliminados_distancia,
                    'datos_cargados': True,
                    'resumen_visible': True
                })
            except Exception as e:
                st.error(f"❌ Error al procesar los datos desde archivo local: {e}")
                st.session_state['datos_cargados'] = False


    elif opcion == "Subir archivo ZIP desde tu dispositivo":
        archivo_subido = st.file_uploader("📂 Sube tu archivo ZIP", type="zip")
        if archivo_subido and not st.session_state['datos_cargados']:
            try:
                zip_bytes = io.BytesIO(archivo_subido.read())
                (df, df_granular, archivo_zip, pais_uso_horario,
                 procesados, eliminados_fecha, eliminados_constancia, eliminados_distancia) = \
                    leer_datos_zip_filtrado_pausas_unificado(zip_bytes)
                st.session_state.update({
                    'df': df,
                    'df_granular': df_granular,
                    'pais_uso_horario': pais_uso_horario,
                    'procesados': procesados,
                    'eliminados_fecha': eliminados_fecha,
                    'eliminados_constancia': eliminados_constancia,
                    'eliminados_distancia': eliminados_distancia,
                    'datos_cargados': True,
                    'resumen_visible': True
                })
            except Exception as e:
                st.error(f"❌ Error al procesar los datos desde archivo local: {e}")
                st.session_state['datos_cargados'] = False

# --- Mostrar resultados si los datos fueron cargados ---
if st.session_state['datos_cargados']:
    if st.session_state['resumen_visible']:
        st.info(f"🗑️ Sesiones descartadas por antigüedad (>12 meses): {st.session_state['eliminados_fecha']}")
        st.info(f"🗑️ Sesiones descartadas por poca distancia (<200 metros): {st.session_state['eliminados_distancia']}")
        st.info(f"🗑️ Sesiones descartadas por pausas significativas entre puntos (>16 segundos): {st.session_state['eliminados_constancia']}")
        st.success(f"✅ Sesiones procesadas: {st.session_state['procesados']}")

        if st.button("Mostrar análisis de las sesiones"):
            st.session_state['resumen_visible'] = False
            st.session_state['mostrar_inputs'] = False
            st.rerun()

    else:
        df_sesion, df_5k, df_10k, df_21k, df_42k = obtener_sesiones(st.session_state['df_granular'])
        st.session_state.update({
            'df_sesion': df_sesion,
            'df_5k': df_5k,
            'df_10k': df_10k,
            'df_21k': df_21k,
            'df_42k': df_42k
        })

        # --- Configurar pestañas ---
        pred_tabs, pred_dfs, pred_distancias = [], [], []
        if not df_5k.empty: pred_tabs.append("Predicción 5K"); pred_dfs.append(df_5k); pred_distancias.append(5.0)
        if not df_10k.empty: pred_tabs.append("Predicción 10K"); pred_dfs.append(df_10k); pred_distancias.append(10.0)
        if not df_21k.empty: pred_tabs.append("Media Maratón (21K)"); pred_dfs.append(df_21k); pred_distancias.append(21.0)
        if not df_42k.empty: pred_tabs.append("Maratón (42K)"); pred_dfs.append(df_42k); pred_distancias.append(42.195)

        # ======== DEFINICIÓN DE TABS ========
        # Orden: Tipos de sesión, Distancia recorrida, Predicción(s), Resumen
        tab_names = [" Tipos de sesión", " Distancia recorrida"] + pred_tabs + [" Resumen", "Análisis IA"]
        tabs = st.tabs(tab_names)

        # ============================================================
        # PESTAÑA 1: TIPOS DE SESIÓN (CLUSTERING)
        # ============================================================
        with tabs[0]:
            st.markdown(
                f"""
                <div style='display: flex; align-items: center; gap: 8px;'>
                    {ICONO_CLUSTER}
                    <h3 style='margin: 0; font-weight: 600; color: #264653;'>Tipos de sesión</h3>
                </div>
                """,
                unsafe_allow_html=True
            )
            tab_clustering(df_sesion)

        # ============================================================
        # PESTAÑA 2: DISTANCIA RECORRIDA
        # ============================================================
        with tabs[1]:
            st.markdown(
                f"""
                <div style='display: flex; align-items: center; gap: 8px;'>
                    {ICONO_DISTANCIA}
                    <h3 style='margin: 0; font-weight: 600;'>Distancia recorrida</h3>
                </div>
                """,
                unsafe_allow_html=True
            )

            grafico_km = tab_kilometros_por_mes(df_sesion)
            if grafico_km is not None:
                st.bokeh_chart(grafico_km, use_container_width=True)

        # ============================================================
        # PESTAÑAS DE PREDICCIÓN
        # ============================================================
        graficos_prediccion = []
        resumenes_prediccion = []

        # Definir colores diferentes para cada predicción
        colores_prediccion = ['#6A994E', '#E76F51', '#2A9D8F', '#F4A261']

        for idx, (tab_name, df_pred, dist) in enumerate(zip(pred_tabs, pred_dfs, pred_distancias)):
            with tabs[2 + idx]:  # <-- ajustado: índice 2 para la primera predicción
                st.markdown(
                    f"""
                    <div style='display: flex; align-items: center; gap: 8px;'>
                        {ICONO_PREDICCION}
                        <h3 style='margin: 0; font-weight: 600; color: #264653;'>{tab_name}</h3>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Pasar el color correspondiente según el índice
                color = colores_prediccion[idx % len(colores_prediccion)]
                grafico1, grafico2, resumen = tab_prediccion(df_pred, dist, st.session_state['df_granular'], color_principal=color)

                if resumen:
                    st.markdown(
                        f"<div style='white-space: nowrap; font-weight: bold;'>{resumen}</div>",
                        unsafe_allow_html=True
                    )
                    resumenes_prediccion.append(resumen)
                else:
                    resumenes_prediccion.append("")

                if grafico1 is not None:
                    st.bokeh_chart(grafico1, use_container_width=True)
                if grafico2 is not None:
                    st.bokeh_chart(grafico2, use_container_width=True)

                graficos_prediccion.append((grafico1, grafico2))

        # ============================================================
        # PESTAÑA: TABLA RESUMEN SESIONES
        # ============================================================
        with tabs[-2]:
            st.markdown(f"""
                <div style='display: flex; align-items: center; gap: 8px;'>
                    {ICONO_CALENDARIO}
                    <h3 style='margin: 0; font-weight: 600; color: #264653;'>Resumen de sesiones</h3>
                </div>
            """, unsafe_allow_html=True)

            mostrar_tabla_resumen_con_expansion(st.session_state["df_sesion"])

        # ============================================================
        # PESTAÑA: ANÁLISIS IA
        # ============================================================
        with tabs[-1]:
            st.markdown(
                f"""
                <div style='display: flex; align-items: center; gap: 8px;'>
                    {ICONO_IA}
                    <h3 style='margin: 0; font-weight: 600; color: #264653;'>Análisis IA</h3>
                </div>
                """,
                unsafe_allow_html=True
            )

            tab_analisis_ia(df_sesion)  # Función del análisis IA que te mostré antes


        st.markdown("---")
        # ============================================================
        # BOTÓN: Generar reporte HTML
        # ============================================================
        if st.button("Generar reporte en HTML"):

            # Copia de datos base
            df = df_sesion.copy()
            df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
            df['distancia'] = pd.to_numeric(df.get('distancia', 0), errors='coerce').round(2)
            df['archivo'] = df.index.astype(str)
            df['mes_num'] = df['fecha'].dt.month.fillna(0).astype(int)
            df['anio'] = df['fecha'].dt.year.fillna(0).astype(int)

            MES_NOMBRES = [
                "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
            ]

            resumen = (
                df.groupby(['anio', 'mes_num'], dropna=False)
                .agg(sesiones=('archivo', 'count'), distancia_total=('distancia', 'sum'))
                .reset_index()
                .sort_values(['anio', 'mes_num'], ascending=[False, False])
            )

            # ============================================================
            # ESTRUCTURA DEL HTML
            # ============================================================
            html_reporte = """
            <html>
            <head>
                <meta charset='utf-8'>
                <title>Reporte de Running</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .section { background-color: #f7f9fc; border: 1px solid #ddd; border-radius: 8px;
                                padding: 15px 25px; margin-bottom: 20px; }
                    h1, h2, h3, h4 { color: #2a3f66; }
                </style>
            </head>
            <body>
            """

            # Título principal
            html_reporte += f"""
            <div style='display: flex; align-items: center; gap: 10px;'>
                {ICONO_REPORTE}
                <h1 style='margin: 0; font-size: 1.8rem; font-weight: 600; color: #000000;'>
                    Reporte Running
                </h1>
            </div>
            """

            # ============================================================
            # 1️⃣ Tipos de sesión
            # ============================================================
            html_reporte += '<div class="section">'
            html_reporte += f"""
            <div style='display: flex; align-items: center; gap: 8px; margin-top: 1.5em;'>
                {ICONO_CLUSTER}
                <h3 style='margin: 0; color: #264653; font-weight: 600;'>Tipos de sesión</h3>
            </div>
            """

            try:
                # Obtenemos gráfico Bokeh y datos de tarjetas para HTML
                grafico_cluster_obj, tarjetas_cluster, colores_cluster = tab_clustering(df_sesion, solo_objeto=True)

                # Agregar gráfico al HTML
                if grafico_cluster_obj is not None:
                    html_reporte += file_html(grafico_cluster_obj, CDN, "")

                # Agregar tarjetas de resumen al HTML
                if tarjetas_cluster is not None:
                    # Ordenar las tarjetas por distancia_media ascendente
                    tarjetas_cluster = tarjetas_cluster.sort_values("distancia_media")
                    # Estilo CSS inline para las tarjetas
                    html_reporte += """
                    <style>
                    .sesion-card {
                        display:flex; align-items:center; justify-content:space-between;
                        padding:10px 14px; border-radius:12px; margin-bottom:8px;
                        box-shadow:0 1px 3px rgba(0,0,0,0.06); /* sombra más suave */
                    }
                    .sesion-left { display:flex; align-items:center; gap:12px; min-width:60px; }
                    .sesion-tipo { flex:1; font-weight:600; font-size:15px; }
                    .sesion-info { flex:1; line-height:1.2; }
                    .sesion-count { font-weight: normal; color:#264653; text-align:right; min-width:70px; }
                    </style>
                    """

                    for _, fila in tarjetas_cluster.iterrows():
                        tipo = fila["tipo_sesion"]
                        dist = fila["distancia_media"]
                        ritmo = fila["ritmo_medio"]
                        count = fila["cantidad_sesiones"]
                        # Usa el color pastel HEX por tipo
                        color_hex = colores_cluster.get(tipo, "#E6F0FA")
                        # Conversión HEX → RGB
                        r, g, b = int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16)
                        # Opacidad baja para efecto suave pastel
                        bg_color = f"rgba({r},{g},{b},0.13)"

                        sesion_label = "sesión" if count == 1 else "sesiones"
                        html_reporte += f"""
                        <div class="sesion-card" style="background-color:{bg_color}; color:#264653;">
                            <div class="sesion-left">{ICONO_SESION}</div>
                            <div class="sesion-tipo">{tipo}</div>
                            <div class="sesion-info">
                                {dist:.1f} km (distancia media)<br>
                                {ritmo} min/km (ritmo medio)
                            </div>
                            <div class="sesion-count">{count} {sesion_label}</div>
                        </div>
                        """

            except Exception as e:
                html_reporte += f"<p>(Error al exportar gráfico y tarjetas de tipos de sesión: {e})</p>"

            html_reporte += "</div>"

            # ============================================================
            # 2️⃣ Distancia recorrida
            # ============================================================
            html_reporte += '<div class="section">'
            html_reporte += f"""
            <div style='display: flex; align-items: center; gap: 8px; margin-top: 1.5em;'>
                {ICONO_DISTANCIA}
                <h3 style='margin: 0; color: #264653; font-weight: 600;'>Distancia recorrida</h3>
            </div>
            """
            try:
                if grafico_km is not None:
                    html_reporte += file_html(grafico_km, CDN, "")
            except Exception as e:
                html_reporte += f"<p>(Error al exportar gráfico de kilómetros: {e})</p>"
            html_reporte += "</div>"

            # ============================================================
            # 3️⃣ Predicciones
            # ============================================================
            html_reporte += '<div class="section">'

            # Definir colores diferentes para cada predicción
            colores_prediccion = ['#6A994E', '#E76F51', '#2A9D8F', '#F4A261']

            n_tabs = min(len(pred_tabs), len(graficos_prediccion), len(resumenes_prediccion))

            for i in range(n_tabs):
                tab_name = pred_tabs[i]
                g1, g2 = graficos_prediccion[i]  # g1 y g2 están disponibles
                resumen_pred = resumenes_prediccion[i]

                html_reporte += f"""
                <div style='display: flex; align-items: center; gap: 8px; margin-top: 1.5em;'>
                    {ICONO_PREDICCION}
                    <h3 style='margin: 0; color: #264653; font-weight: 600;'>{tab_name}</h4>
                </div>
                """

                if resumen_pred:
                    html_reporte += f"<p><b>{resumen_pred}</b></p>"

                # Solo exportar el gráfico de predicción (g1), NO el histograma (g2)
                if g1 is not None:
                    try:
                        html_reporte += file_html(g1, CDN, "")
                    except Exception as e:
                        html_reporte += f"<p>(Error al exportar gráfico de predicción: {e})</p>"
                
                # g2 (histograma) se ignora completamente en el HTML

            html_reporte += "</div>"

            # ============================================================
            # 4️⃣ Resumen mensual
            # ============================================================
            html_reporte += '<div class="section">'
            html_reporte += f"""
            <div style='display: flex; align-items: center; gap: 8px; margin-top: 1.5em;'>
                {ICONO_CALENDARIO}
                <h3 style='margin: 0; color: #264653; font-weight: 600;'>Resumen</h3>
            </div>
            """

            # Estilo para las tarjetas de resumen (alineación tipo “Tipos de sesión”)
            html_reporte += """
            <style>
            .resumen-card {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 10px 14px;
                border-radius: 12px;
                margin-bottom: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                background-color: #2A9D8F; /* Color de fondo unificado para todas las tarjetas */
                color: white; /* Ajustar el color del texto para mejor contraste */
            }
            .resumen-left {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 25px;
                font-weight: bold;
            }
            .resumen-mes {
                flex: 2;
                font-weight: 600;
                font-size: 15px;
            }
            .resumen-dist {
                flex: 1;
                text-align: left;
            }
            .resumen-sesiones {
                flex: 1;
                text-align: right;
                font-weight: normal;
            }
            </style>

            """

            for _, fila in resumen.iterrows():
                mes_num = int(fila['mes_num'])
                anio = int(fila['anio'])
                sesiones = int(fila['sesiones'])
                distancia_total = float(fila['distancia_total']) if not pd.isna(fila['distancia_total']) else 0.0
                mes_nombre_upper = MES_NOMBRES[mes_num].upper() if 1 <= mes_num <= 12 else "SIN FECHA"

                html_reporte += f"""
                <div class="resumen-card">
                    <div class="resumen-left">┃</div>
                    <div class="resumen-mes">{mes_nombre_upper} {anio}</div>
                    <div class="resumen-dist">{distancia_total:.2f} km</div>
                    <div class="resumen-sesiones">{sesiones} sesiones</div>
                </div>
                """

            html_reporte += "</div>"

            # ============================================================
            # FINAL DEL HTML
            # ============================================================
            html_reporte += "</body></html>"

            # ============================================================
            # BOTÓN DESCARGA
            # ============================================================
            st.download_button(
                "⬇️ Descargar reporte",
                data=html_reporte.encode("utf-8"),
                file_name="reporte_sesiones.html",
                mime="text/html"
            )
