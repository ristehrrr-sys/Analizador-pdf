import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai

# ==========================================
# 1. CONFIGURACIÓN Y DISEÑO DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Asistente de Artículos Científicos", 
    page_icon="🔬",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

# CSS para ocultar el menú superior de Streamlit, el logo de GitHub y el pie de página
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. APLICACIÓN PRINCIPAL (PÚBLICA)
# ==========================================
st.title("🔬 Asistente de Artículos Científicos")
st.subheader("📊 Extrae la Matriz de Consistencia en segundos")
st.write("Sube tu paper en PDF y la IA identificará automáticamente el problema central, la hipótesis, las variables y armará tu matriz.")

# Subir el archivo
archivo = st.file_uploader("📂 Sube tu archivo PDF aquí", type="pdf")

# Botón de análisis
if st.button("🚀 Iniciar Análisis"):
    if archivo is None:
        st.warning("⚠️ Por favor, sube un archivo PDF antes de iniciar el análisis.")
    else:
        with st.spinner("La IA está leyendo el artículo y armando la matriz... ⏳"):
            try:
                # Extraer el texto del PDF
                lector = PdfReader(archivo)
                texto = ""
                for pagina in lector.pages:
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        texto += texto_pagina + " "
                
                if not texto.strip():
                    st.error("❌ No se pudo extraer texto. El PDF podría ser una imagen escaneada.")
                    st.stop()

                # Configurar la IA usando la clave segura de los Secrets
                api_key = st.secrets["GEMINI_API_KEY"]
                genai.configure(api_key=api_key)
                
                modelo = genai.GenerativeModel('gemini-3.8-flash')
                
                # Prompt riguroso con validación y alternativas
                prompt = f"""
                Actúa como un metodólogo de investigación experto. 
                Lee el siguiente artículo científico y extrae la información para armar una Matriz de Consistencia.
                
                REGLAS ESTRICTAS DE EXTRACCIÓN:
                1. Si la información solicitada está en el texto, extráela de forma resumida y clara.
                2. Si la información NO está explícita o el artículo carece de ella, DEBES escribir exactamente la frase: "⚠️ No se encuentra explícito en el documento".
                3. Para cada dato faltante, DEBES agregar un párrafo debajo llamado "💡 Alternativa de solución:" donde sugieras cómo el investigador podría formularlo o qué debería buscar.
                
                ESTRUCTURA DE SALIDA:
                
                **1. Problema Central:**
                [Texto extraído o mensaje de faltante + Alternativa de solución]
                
                **2. Objetivos (General y Específicos):**
                [Texto extraído o mensaje de faltante + Alternativa de solución]
                
                **3. Hipótesis:**
                [Texto extraído o mensaje de faltante + Alternativa de solución]
                
                **4. Variables:**
                - Variable Independiente (Causa): [Texto o mensaje]
                - Variable Dependiente (Efecto): [Texto o mensaje]
                
                **5. Dimensiones e Indicadores:**
                [Texto extraído o mensaje de faltante + Alternativa de solución]
                
                **6. Matriz de Consistencia (Resumen final en tabla):**
                Crea una tabla en formato Markdown con las columnas: Problema | Objetivos | Hipótesis | Variables | Dimensiones. Si alguna celda falta, pon "No hallado en el texto".
                
                Aquí está el texto del artículo:
                {texto[:15000]}
                """
                
                respuesta = modelo.generate_content(prompt)
                resultado_texto = respuesta.text
                
                st.success("✅ ¡Análisis completado con éxito!")
                st.markdown(resultado_texto)
                
                # --- BOTÓN DE DESCARGA ---
                st.markdown("---")
                st.subheader("📥 Descargar Resultados")
                st.write("Descarga el análisis para revisar las alternativas de solución y la matriz.")
                
                nombre_limpio = archivo.name.replace(".pdf", "")
                
                st.download_button(
                    label="Descargar Matriz en formato de texto (.txt)",
                    data=resultado_texto,
                    file_name=f"Matriz_Consistencia_{nombre_limpio}.txt",
                    mime="text/plain",
                    type="primary"
                )
                
            except Exception as e:
                st.error(f"❌ Ocurrió un error al analizar: {e}")
