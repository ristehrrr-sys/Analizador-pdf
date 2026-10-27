import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai

# Configuración de la página
st.set_page_config(page_title="Analizador de Papers", page_icon="🔬")

# ==========================================
# SISTEMA DE INICIAR SESIÓN
# ==========================================
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔒 Acceso Restringido")
    st.write("Por favor, ingresa la contraseña para usar el Analizador de Artículos Científicos.")
    
    password = st.text_input("Contraseña:", type="password")
    
    if st.button("Iniciar Sesión"):
        if password == "tesis2024": 
            st.session_state.autenticado = True
            st.rerun() 
        else:
            st.error("❌ Contraseña incorrecta")
    
    st.stop() 

# ==========================================
# APLICACIÓN PRINCIPAL
# ==========================================
st.title("🔬 Asistente de Artículos Científicos")
st.write("Sube un paper en PDF y la IA extraerá el problema central, hipótesis y variables.")

with st.sidebar:
    st.header("🔑 Configuración")
    api_key = st.text_input("Pega tu API Key de Google Gemini:", type="password")
    st.markdown("[Obtén tu API Key gratis aquí](https://aistudio.google.com/app/apikey)")
    
    st.markdown("---")
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

archivo = st.file_uploader("📂 Sube tu archivo PDF aquí", type="pdf")

if st.button("🚀 Iniciar Análisis"):
    if not api_key:
        st.warning("⚠️ Primero debes ingresar tu API Key en la barra lateral izquierda.")
    elif archivo is None:
        st.warning("⚠️ Por favor, sube un archivo PDF antes de iniciar el análisis.")
    else:
        with st.spinner("La IA está leyendo el artículo y armando la matriz... ⏳"):
            try:
                # 1. Extraer el texto del PDF
                lector = PdfReader(archivo)
                texto = ""
                for pagina in lector.pages:
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        texto += texto_pagina + " "
                
                if not texto.strip():
                    st.error("❌ No se pudo extraer texto. El PDF podría ser una imagen escaneada.")
                    st.stop()

                # 2. Configurar la IA
                genai.configure(api_key=api_key)
                
                # Usamos el modelo más reciente y estable
                modelo = genai.GenerativeModel('gemini-2.0-flash')
                
                # 3. Crear la orden para la IA
                prompt = f"""
                Actúa como un metodólogo de investigación experto. 
                Lee el siguiente artículo científico y extrae la información para armar una Matriz de Consistencia.
                
                Tu respuesta debe tener este formato exacto:
                **1. Problema Central:** (Redáctalo en una sola oración clara)
                **2. Hipótesis:** (Si no está explícita, deduce una basada en el texto)
                **3. Variables:**
                - Variable Independiente (Causa):
                - Variable Dependiente (Efecto):
                
                **4. Matriz de Consistencia (en formato tabla):**
                Crea una tabla con las columnas: Problema | Objetivos | Hipótesis | Variables | Dimensiones.
                
                Aquí está el texto del artículo:
                {texto[:15000]}
                """
                
                # 4. Generar y mostrar el resultado
                respuesta = modelo.generate_content(prompt)
                
                st.success("✅ ¡Análisis completado con éxito!")
                st.markdown(respuesta.text)
                
            except Exception as e:
                st.error(f"❌ Ocurrió un error al analizar: {e}")
