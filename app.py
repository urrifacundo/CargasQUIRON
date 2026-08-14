import streamlit as st
import pandas as pd
import re

# --- SEGURIDAD ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "1234": # CAMBIA "1234" POR LA CONTRASEÑA QUE QUIERAS
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Ingresa la contraseña para acceder:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Ingresa la contraseña para acceder:", type="password", on_change=password_entered, key="password")
        st.error("Contraseña incorrecta")
        return False
    else:
        return True

if not check_password():
    st.stop() # Detiene la ejecución si no hay contraseña

# --- A PARTIR DE AQUÍ VA EL CÓDIGO QUE YA TENÍAS ---

# Configuración de la página
st.set_page_config(page_title="Gestor de Denuncias - Quiron", layout="wide")

st.title("📋 Asistente Automatizado de Denuncias")
st.write("Pega el texto de la denuncia abajo para extraer los datos y autocompletar los campos.")

# Cargar bases de datos de forma segura
@st.cache_data
def cargar_bases():
    try:
        df_comisarias = pd.read_excel('Comisarias.xlsx')
    except:
        df_comisarias = pd.DataFrame()
        
    try:
        df_caratulas = pd.read_excel('Caratulas QUIRON.xls')
    except:
        df_caratulas = pd.DataFrame()
        
    return df_comisarias, df_caratulas

df_comisarias, df_caratulas = cargar_bases()

# Área de texto para pegar la denuncia
texto_denuncia = st.text_area("Pega aquí el texto de la denuncia:", height=200, placeholder="Ej: En la ciudad de Rafael Castillo, partido de La Matanza...")

if st.button("Procesar Denuncia", type="primary"):
    if texto_denuncia.strip() == "":
        st.warning("Por favor, ingresa un texto de denuncia.")
    else:
        # --- EXTRACCIÓN DE DATOS ---
        # Partido y Localidad
        partido_match = re.search(r"partido de\s+([\w\s]+),", texto_denuncia, re.IGNORECASE)
        localidad_match = re.search(r"ciudad de\s+([\w\s]+),", texto_denuncia, re.IGNORECASE)
        
        partido = partido_match.group(1).strip().upper() if partido_match else ""
        localidad = localidad_match.group(1).strip().upper() if localidad_match else ""
        
        # Fecha del hecho (ej: fecha 05 de agosto del corriente año)
        fecha_match = re.search(r"fecha\s+(\d{1,2}\s+de\s+[\w\s]+?(?:del corriente año|\d{4}))", texto_denuncia, re.IGNORECASE)
        fecha_hecho = fecha_match.group(1) if fecha_match else ""

        # Hora del hecho (ej: siendo aproximadamente las 15:00 horas)
        hora_match = re.search(r"aproximadamente las\s+(\d{1,2}:\d{2})\s+horas", texto_denuncia, re.IGNORECASE)
        hora_hecho = hora_match.group(1) if hora_match else ""

        # Victimas / Denunciante (ej: manifestando ser EZEQUIEL ERNESTO DIAZ)
        victima_match = re.search(r"manifestando ser\s+([A-ZÁÉÍÓÚ\s]+),", texto_denuncia)
        victima = victima_match.group(1).strip() if victima_match else ""

        # --- BUSCAR COMISARIA EN EXCEL ---
        jurisdiccion = "No encontrada automáticamente"
        if not df_comisarias.empty and partido and localidad:
            resultado = df_comisarias[
                (df_comisarias['partido_hecho'].str.upper() == partido) & 
                (df_comisarias['localidad_hecho'].str.upper() == localidad)
            ]
            if not resultado.empty:
                jurisdiccion = resultado.iloc[0]['analisis_jurisdiccion']

        # --- MOSTRAR RESULTADOS TIPO FORMULARIO ---
        st.success("¡Datos extraídos con éxito!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Partido", value=partido)
            st.text_input("Localidad", value=localidad)
            st.text_input("Jurisdicción sugerida", value=jurisdiccion)
            st.text_input("Fecha del hecho", value=fecha_hecho)
            st.text_input("Hora del hecho", value=hora_hecho)
            
        with col2:
            st.text_input("Víctimas", value=victima)
            
            # Selector inteligente de carátulas basadas en tu archivo Quiron
            lista_caratulas = []
            if not df_caratulas.empty:
                # Limpiamos duplicados y valores nulos
                lista_caratulas = df_caratulas['Caratula'].dropna().unique().tolist()
            
            caratula_seleccionada = st.selectbox("Carátula (Guía Quirón)", options=["Seleccione una..."] + lista_caratulas)
            
            modalidad = ""
            if caratula_seleccionada != "Seleccione una..." and not df_caratulas.empty:
                mod_row = df_caratulas[df_caratulas['Caratula'] == caratula_seleccionada]
                if not mod_row.empty:
                    modalidad = str(mod_row.iloc[0]['Modalidad'])
            
            st.text_input("Modalidad sugerida", value=modalidad if modalidad != "nan" else "")

        st.info("💡 Consejo: Haz clic en los campos para copiar el texto y pegarlo directamente en tu sistema de carga habitual.")
