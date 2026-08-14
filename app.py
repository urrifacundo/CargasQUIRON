import streamlit as st
import pandas as pd
import re

# --- SEGURIDAD ---
def check_password():
    def password_entered():import streamlit as st
import pandas as pd
import re
import os

# Configuración de la página
st.set_page_config(page_title="Gestor de Denuncias - Quirón", layout="wide")

# --- SEGURIDAD (CONTRASEÑA) ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "1234":  # Puedes cambiar "1234" por la contraseña que prefieras
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
    st.stop()

# --- CARGA DE BASES DE DATOS ---
@st.cache_data
def cargar_bases():
    df_comisarias = pd.DataFrame()
    df_caratulas = pd.DataFrame()
    
    if os.path.exists('Comisarias.xlsx'):
        df_comisarias = pd.read_excel('Comisarias.xlsx')
    
    if os.path.exists('Caratulas QUIRON.xls'):
        df_caratulas = pd.read_excel('Caratulas QUIRON.xls')
        
    return df_comisarias, df_caratulas

df_comisarias, df_caratulas = cargar_bases()

st.title("📋 Asistente de Carga de Denuncias")
st.write("Pega el texto completo de la denuncia para autocompletar todos los campos del sistema.")

# Área de texto para la denuncia
texto_denuncia = st.text_area("Pega aquí el texto de la denuncia:", height=220, placeholder="Ej: En la ciudad de Rafael Castillo, partido de La Matanza...")

if st.button("Procesar Denuncia", type="primary"):
    if texto_denuncia.strip() == "":
        st.warning("Por favor, ingresa un texto de denuncia.")
    else:
        # --- EXTRACCIÓN AUTOMÁTICA DE DATOS (NLP BÁSICO) ---
        
        # 1. Partido y Localidad
        partido_match = re.search(r"partido de\s+([\w\s]+),", texto_denuncia, re.IGNORECASE)
        localidad_match = re.search(r"ciudad de\s+([\w\s]+),", texto_denuncia, re.IGNORECASE)
        
        partido = partido_match.group(1).strip().upper() if partido_match else ""
        localidad = localidad_match.group(1).strip().upper() if localidad_match else ""
        
        # 2. Fecha y Hora del hecho
        fecha_match = re.search(r"fecha\s+(\d{1,2}\s+de\s+[\w\s]+?(?:del corriente año|\d{4}))", texto_denuncia, re.IGNORECASE)
        fecha_hecho = fecha_match.group(1) if fecha_match else ""

        hora_match = re.search(r"aproximadamente las\s+(\d{1,2}:\d{2})\s+horas", texto_denuncia, re.IGNORECASE)
        hora_hecho = hora_match.group(1) if hora_match else ""

        # 3. Víctima / Denunciante
        victima_match = re.search(r"manifestando ser\s+([A-ZÁÉÍÓÚ\s]+),", texto_denuncia)
        victima = victima_match.group(1).strip() if victima_match else ""

        # 4. Búsqueda de Comisaría (Jurisdicción)
        jurisdiccion = "No encontrada automáticamente"
        if not df_comisarias.empty and partido and localidad:
            match = df_comisarias[
                (df_comisarias['partido_hecho'].astype(str).str.strip().str.upper() == partido) & 
                (df_comisarias['localidad_hecho'].astype(str).str.strip().str.upper() == localidad)
            ]
            if not match.empty:
                jurisdiccion = str(match.iloc[0]['analisis_jurisdiccion'])

        # --- ORDEN EXACTO SEGÚN LA IMAGEN DEL SISTEMA ---
        st.success("¡Denuncia procesada con éxito! Copia los campos necesarios:")

        # Dividimos en dos columnas para una visualización cómoda y ordenada
        col1, col2 = st.columns(2)

        with col1:
            st.text_input("Partido", value=partido)
            st.text_input("Localidad", value=localidad)
            st.text_input("Jurisdiccion", value=jurisdiccion)
            st.text_input("Lugar del hecho", value="")
            st.text_input("Coordenadas", value="")
            st.text_input("Fecha del hecho", value=fecha_hecho)
            st.text_input("Hora del hecho", value=hora_hecho)
            st.text_input("Tipo de lugar", value="")

        with col2:
            # Selector inteligente de Carátulas basadas en tu Excel Quirón
            lista_caratulas = []
            if not df_caratulas.empty:
                lista_caratulas = df_caratulas['Caratula'].dropna().unique().tolist()
            
            caratula_seleccionada = st.selectbox("Caratula", options=["Seleccione una..."] + lista_caratulas)
            
            modalidad = ""
            if caratula_seleccionada != "Seleccione una..." and not df_caratulas.empty:
                mod_row = df_caratulas[df_caratulas['Caratula'] == caratula_seleccionada]
                if not mod_row.empty:
                    modalidad = str(mod_row.iloc[0]['Modalidad'])

            st.text_input("Modalidad", value=modalidad if modalidad != "nan" else "")
            st.text_input("Imputados", value="")
            st.text_input("Victimas", value=victima)
            st.text_input("Menores", value="")
            st.text_input("Lesionados", value="")
            st.text_input("Armas", value="")

        st.text_area("Observaciones", value="", height=80)
        
        st.info("💡 Haz clic dentro de cualquier caja de texto para copiar el contenido y pegarlo rápidamente en tu sistema.")
