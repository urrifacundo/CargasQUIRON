import streamlit as st
import pandas as pd
import re
import os

st.set_page_config(page_title="Gestor de Denuncias - Quirón", layout="wide")

def check_password():
    def password_entered():
        if st.session_state["password"] == "1234":
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

st.title("Asistente de Carga de Denuncias")
st.write("Pega el texto completo de la denuncia para autocompletar todos los campos del sistema.")

texto_denuncia = st.text_area("Pega aquí el texto de la denuncia:", height=220, placeholder="Ej: En la ciudad de Rafael Castillo...")

if st.button("Procesar Denuncia", type="primary"):
    if texto_denuncia.strip() == "":
        st.warning("Por favor, ingresa un texto de denuncia.")
    else:
        partido_match = re.search(r"partido de\s+([\w\s]+),", texto_denuncia, re.IGNORECASE)
        localidad_match = re.search(r"localidad de\s+([\w\s]+),", texto_denuncia, re.IGNORECASE)
        if not localidad_match:
            localidad_match = re.search(r"ciudad de\s+([\w\s]+),", texto_denuncia, re.IGNORECASE)
        
        partido = partido_match.group(1).strip().upper() if partido_match else ""
        localidad = localidad_match.group(1).strip().upper() if localidad_match else ""
        
        fecha_match = re.search(r"a los\s+(\d{1,2}\s+días\s+del\s+mes\s+de\s+[\w\s]+?(?:del año\s+\d{4}|\d{4}))", texto_denuncia, re.IGNORECASE)
        if not fecha_match:
            fecha_match = re.search(r"fecha\s+(\d{1,2}\s+de\s+[\w\s]+)", texto_denuncia, re.IGNORECASE)
        fecha_hecho = fecha_match.group(1) if fecha_match else ""

        hora_match = re.search(r"siendo las\s+(\d{1,2}\.\d{2}|\d{1,2}:\d{2})\s+horas", texto_denuncia, re.IGNORECASE)
        if not hora_match:
            hora_match = re.search(r"aproximadamente las\s+(\d{1,2}:\d{2})\s+horas", texto_denuncia, re.IGNORECASE)
        hora_hecho = hora_match.group(1).replace(".", ":") if hora_match else ""

        victima_match = re.search(r"manifestando ser y llamarse:\s+([A-ZÁÉÍÓÚ\s]+),", texto_denuncia)
        if not victima_match:
            victima_match = re.search(r"manifestando ser\s+([A-ZÁÉÍÓÚ\s]+),", texto_denuncia)
        victima = victima_match.group(1).strip() if victima_match else ""

        jurisdiccion = "No encontrada automáticamente"
        if not df_comisarias.empty and partido and localidad:
            match = df_comisarias[
                (df_comisarias['partido_hecho'].astype(str).str.strip().str.upper() == partido) & 
                (df_comisarias['localidad_hecho'].astype(str).str.strip().str.upper() == localidad)
            ]
            if not match.empty:
                jurisdiccion = str(match.iloc[0]['analisis_jurisdiccion'])

        caratula_detectada = ""
        modalidad_detectada = ""
        
        texto_lower = texto_denuncia.lower()
        
        if "arma de fuego" in texto_lower or "intimidaron" in texto_lower or "robo" in texto_lower or "asaltaron" in texto_lower or "sustrajeron" in texto_lower:
            if "vehiculo" in texto_lower or "auto" in texto_lower or "rodado" in texto_lower:
                caratula_detectada = "Sustraccion Automotor"
                modalidad_detectada = "Asalto"
            else:
                caratula_detectada = "Robo"
                modalidad_detectada = "Asalto en Via Publica"
        elif "hurto" in texto_lower:
            caratula_detectada = "Hurto"
            modalidad_detectada = "Hurto"
        elif "tarjeta" in texto_lower or "home banking" in texto_lower or "transferencia" in texto_lower or "mercadopago" in texto_lower:
            caratula_detectada = "Estafa"
            modalidad_detectada = "Informatica"
        elif "cuento del tío" in texto_lower or "cuento del tio" in texto_lower:
            caratula_detectada = "Estafa"
            modalidad_detectada = "Cuento del Tio"
        else:
            caratula_detectada = "Estafa"
            modalidad_detectada = "Otros"

        genero_victima = "Masculino"
        if "la denunciante" in texto_lower or "comparece... una mujer" in texto_lower or "sra." in texto_lower:
            genero_victima = "Femenino"
        
        genero_imputado = "Masculino" if "masculino" in texto_lower or "sujetos" in texto_lower or "personas" in texto_lower else "Ninguno"

        st.success("¡Denuncia procesada con éxito! Copia los campos necesarios:")

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
            st.text_input("Caratula", value=caratula_detectada)
            st.text_input("Modalidad", value=modalidad_detectada)
            st.text_input("Imputados", value=genero_imputado)
            st.text_input("Victimas", value=genero_victima)
            st.text_input("Menores", value="")
            st.text_input("Lesionados", value="")
            st.text_input("Armas", value="")

        st.text_area("Observaciones", value="", height=80)
        
        st.info("Haz clic dentro de cualquier caja de texto para copiar el contenido y pegarlo rápidamente en tu sistema.")
