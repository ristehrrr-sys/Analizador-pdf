import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai
import pandas as pd
import io
import json

# ==========================================
# 1. CONFIGURACIÓN Y DISEÑO
# ==========================================
st.set_page_config(
    page_title="Asistente de Artículos Científicos", 
    page_icon="🔬",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. APLICACIÓN PRINCIPAL
# ==========================================
st.title("🔬 Asistente de Artículos Científicos")
st.subheader("📊 Extrae la Matriz de Consistencia en segundos")
st.write("Sube tu paper en PDF. La IA armará la matriz y podrás descargarla en Excel.")

archivo = st.file_uploader("📂 Sube tu archivo PDF aquí", type="pdf")

if st.button("🚀 Iniciar Análisis"):
    if archivo is None:
        st.warning("⚠️ Por favor, sube un archivo PDF antes de iniciar el análisis.")
    else:
        with st.spinner("La IA está leyendo el artículo y armando la matriz... ⏳"):
            try:
                lector = PdfReader(archivo)
                texto = ""
                for pagina in lector.pages:
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        texto += texto_pagina + " "
                
                if not texto.strip():
                    st.error("❌ No se pudo extraer texto. El PDF podría ser una imagen escaneada.")
                    st.stop()

                api_key = st.secrets["GEMINI_API_KEY"]
                genai.configure(api_key=api_key)
                modelo = genai.GenerativeModel('gemini-3.8-flash')
                
                # PROMPT MODIFICADO: Pedimos JSON para que sea fácil pasarlo a Excel
                prompt = f"""
                Actúa como un metodólogo de investigación experto. 
                Lee el siguiente artículo científico y extrae la información para armar una Matriz de Consistencia.
                
                REGLAS:
                1. Extrae lo que está explícito en el texto.
                2. Si falta algo (ej. la hipótesis), redacta una propuesta lógica basada en el artículo y agrégale un asterisco (*) al final para indicar que es sugerencia de la IA.
                
                DEVUELVE ÚNICAMENTE UN OBJETO JSON VÁLIDO CON ESTA ESTRUCTURA EXACTA (sin texto adicional, solo el JSON):
                {{
                    "resumen": "Aquí va un breve párrafo con el análisis general del documento.",
                    "matriz": [
                        {{
                            "Problema": "Texto del problema o propuesta*",
                            "Objetivos": "Texto del objetivo o propuesta*",
                            "Hipótesis": "Texto de la hipótesis o propuesta*",
                            "Variables": "Variable Independiente: ... / Variable Dependiente: ...",
                            "Dimensiones": "Dimensiones e indicadores encontrados o propuestos*"
                        }}
                    ]
                }}
                
                Aquí está el texto del artículo:
                {texto[:15000]}
                """
                
                try:
                    respuesta = modelo.generate_content(prompt)
                    # Limpiamos la respuesta por si la IA pone formato de código (```json ... ```)
                    texto_limpio = respuesta.text.replace("```json", "").replace("```", "").strip()
                    datos_json = json.loads(texto_limpio)
                except Exception as e:
                    if "429" in str(e):
                        st.warning("⏳ El servidor de Google está recibiendo muchas solicitudes. Por favor, espera unos 40 segundos y vuelve a intentar.")
                        st.stop()
                    else:
                        st.error(f"❌ Error procesando la respuesta de la IA: {e}")
                        st.stop()
                
                st.success("✅ ¡Análisis completado con éxito!")
                
                # Mostrar el resumen
                st.write(datos_json["resumen"])
                
                # Mostrar la tabla en pantalla
                st.subheader("📊 Matriz de Consistencia")
                df = pd.DataFrame(datos_json["matriz"])
                st.dataframe(df, use_container_width=True)
                
                # --- BOTÓN DE DESCARGA EN EXCEL ---
                st.markdown("---")
                st.subheader("📥 Descargar Resultados")
                st.write("Descarga la matriz directamente en formato Excel para pegarla en tu tesis.")
                
                # Creamos el archivo de Excel en memoria
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Matriz de Consistencia')
                
                nombre_limpio = archivo.name.replace(".pdf", "")
                
                st.download_button(
                    label="📊 Descargar Matriz en Excel (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"Matriz_Consistencia_{nombre_limpio}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
                
            except Exception as e:
                st.error(f"❌ Ocurrió un error inesperado: {e}")
