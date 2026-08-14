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
            hora_match = re.search(r"aproximadamente las\s+(\d{1,2}:\d{2})\s+hs", texto_denuncia, re.IGNORECASE)
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

        def tiene_palabra(palabras, texto):
            for p in palabras:
                if re.search(r'\b' + p + r'\b', texto):
                    return True
            return False

        caratula_detectada = ""
        modalidad_detectada = ""
        texto_lower = texto_denuncia.lower()
        
        if tiene_palabra(["disparo", "disparos", "detonaciones", "detonación"], texto_lower) and tiene_palabra(["arma", "fuego"], texto_lower) and not tiene_palabra(["robo", "robó", "robaron", "sustrajeron", "asaltaron"], texto_lower):
            caratula_detectada = "Abuso de Arma"
            modalidad_detectada = "Abuso de Arma"
            
        elif tiene_palabra(["robo", "robaron", "sustrajeron", "sustraído", "llevó", "asaltaron"], texto_lower) and tiene_palabra(["vehículo", "vehiculo", "auto", "automóvil", "automovil", "moto", "motovehículo", "motocicleta", "camioneta"], texto_lower):
            if tiene_palabra(["moto", "motovehículo", "motocicleta"], texto_lower):
                caratula_detectada = "Sustraccion Motovehiculo"
            else:
                caratula_detectada = "Sustraccion Automotor"
                
            if tiene_palabra(["arma", "intimidaron", "amenazaron"], texto_lower):
                modalidad_detectada = "Asalto"
            else:
                modalidad_detectada = "Levantamiento"

        elif tiene_palabra(["robo", "asaltaron", "sustrajeron", "robaron", "arma", "intimidaron"], texto_lower) and not tiene_palabra(["disparo", "detonaciones"], texto_lower):
            caratula_detectada = "Robo"
            modalidad_detectada = "Asalto en Via Publica"

        elif tiene_palabra(["hurto", "hurtaron"], texto_lower):
            caratula_detectada = "Hurto"
            modalidad_detectada = "Hurto"

        elif tiene_palabra(["tarjeta", "home banking", "transferencia", "mercadopago", "estafa", "engaño", "cuento del tío", "cuento del tio", "whatsapp", "facebook", "marketplace"], texto_lower):
            caratula_detectada = "Estafa"
            if tiene_palabra(["cuento del tío", "cuento del tio"], texto_lower):
                modalidad_detectada = "Cuento del Tio"
            elif tiene_palabra(["marketplace", "facebook"], texto_lower):
                modalidad_detectada = "MarketPlace"
            elif tiene_palabra(["whatsapp", "chat"], texto_lower):
                modalidad_detectada = "WhatsApp"
            else:
                modalidad_detectada = "Informatica"

        else:
            caratula_detectada = "Averiguacion de Ilícito"
            modalidad_detectada = "Sin Modalidad"

        genero_victima = "Masculino"
        if tiene_palabra(["propietaria", "la denunciante", "una mujer", "sra"], texto_lower):
            genero_victima = "Femenino"
            
        genero_imputado = "Ninguno"
        tiene_masc = tiene_palabra(["masculino", "hombre", "sujeto", "hombres", "sujetos", "un vecino", "el mismo"], texto_lower)
        tiene_fem = tiene_palabra(["femenino", "mujer", "una mujer", "señora"], texto_lower)
        
        if tiene_masc and tiene_fem:
            genero_imputado = "Ambos"
        elif tiene_masc:
            genero_imputado = "Masculino"
        elif tiene_fem:
            genero_imputado = "Femenino"

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
