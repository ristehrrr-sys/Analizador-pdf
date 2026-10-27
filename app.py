import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai

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
st.subheader("💬 Pregúntale lo que quieras al paper")
st.write("Sube tu PDF y pídele a la IA un resumen, antecedentes en APA, buscar a un autor, o extraer la matriz.")

archivo = st.file_uploader("📂 Sube tu archivo PDF aquí", type="pdf")

peticion_usuario = st.text_input("📝 ¿Qué necesitas del documento?", 
                                placeholder="Ej: 'Dame los antecedentes en APA 7', 'Busca a Bourdieu', 'Haz la matriz'...")

if st.button("🚀 Iniciar Análisis"):
    if archivo is None:
        st.warning("⚠️ Por favor, sube un archivo PDF antes de iniciar el análisis.")
    elif not peticion_usuario.strip():
        st.info("💡 Por favor, escribe qué quieres que la IA haga con el documento.")
    else:
        with st.spinner("La IA está procesando tu petición... ⏳"):
            try:
                lector = PdfReader(archivo)
                texto_completo = ""
                for pagina in lector.pages:
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        texto_completo += texto_pagina + " "
                
                if not texto_completo.strip():
                    st.error("❌ No se pudo extraer texto. El PDF podría ser una imagen escaneada.")
                    st.stop()

                api_key = st.secrets["GEMINI_API_KEY"]
                genai.configure(api_key=api_key)
                
                # --- EL CAMBIO ESTÁ AQUÍ (Modelo Lite) ---
                modelo = genai.GenerativeModel('gemini-3.5-flash-lite')
                
                resultado_texto = ""
                peticion_lower = peticion_usuario.lower()

                # --- LÓGICA 1: BUSCAR AUTOR Y SU IDEA EN 15 PALABRAS ---
                if any(palabra in peticion_lower for palabra in ["busca a", "autor", "quien es", "idea de", "piensa"]):
                    prompt = f"""
                    Actúa como un investigador experto. 
                    En el siguiente texto, busca información sobre la petición del usuario: "{peticion_usuario}".
                    
                    Tu respuesta debe tener ESTRICTAMENTE este formato:
                    **Autor encontrado:** [Nombre del autor]
                    **Idea Central:** [Resumen de su idea principal en 15 palabras o menos]
                    **Cita del texto:** [Un fragmento corto del texto que respalde esa idea]
                    
                    Si no encuentras al autor, responde exactamente: "El autor no se menciona en el documento proporcionado".
                    
                    Aquí está el texto:
                    {texto_completo[:25000]}
                    """
                    respuesta = modelo.generate_content(prompt)
                    resultado_texto = respuesta.text

                # --- LÓGICA 2: REDACTAR ANTECEDENTES EN APA 7 (CON MUESTRA) ---
                elif "antecedente" in peticion_lower:
                    prompt = f"""
                    Actúa como un metodólogo experto en normas APA 7ma edición. 
                    Lee el siguiente artículo científico y extrae los antecedentes de investigación.
                    
                    Tu tarea es redactar cada antecedente como un párrafo académico de 150 a 200 palabras. 
                    REGLA CRÍTICA: Si el estudio menciona la muestra (número de participantes, tipo de muestreo), DEBES incluirla obligatoriamente en la redacción.
                    
                    Para cada autor o estudio, sigue esta estructura:
                    1. Cita en formato APA 7 (ej. Apellido, Año).
                    2. Objetivo del estudio.
                    3. Breve metodología (incluyendo la muestra si está disponible).
                    4. Resultados principales.
                    5. Aporte a la investigación actual.
                    
                    Si el documento no menciona antecedentes claros, redacta: "El documento no presenta una sección explícita de antecedentes".
                    
                    Aquí está el texto del artículo:
                    {texto_completo[:20000]}
                    """
                    respuesta = modelo.generate_content(prompt)
                    resultado_texto = respuesta.text

                # --- LÓGICA 3: RESUMEN DE IDEAS CENTRALES (CON MUESTRA) ---
                elif "resumen" in peticion_lower or "idea" in peticion_lower:
                    st.info("📚 La IA está dividiendo el texto para extraer las ideas centrales...")
                    tamano_bloque = 15000
                    bloques = [texto_completo[i:i+tamano_bloque] for i in range(0, len(texto_completo), tamano_bloque)]
                    ideas_parciales = []
                    for i, bloque in enumerate(bloques[:3]): 
                        prompt_bloque = f"""
                        Extrae las 3 ideas centrales más importantes de este fragmento y BUSCA EXPLÍCITAMENTE si se menciona la muestra (número de participantes). Sé muy conciso.
                        Texto: {bloque}
                        """
                        res = modelo.generate_content(prompt_bloque)
                        ideas_parciales.append(res.text)
                    texto_unificado = "\n".join(ideas_parciales)
                    prompt_final = f"""
                    Une estas ideas en un solo resumen estructurado. 
                    OBLIGATORIO: Debes incluir una sección de "Muestra" con el número de participantes si fue encontrado. Si no se menciona, escribe "La muestra no está explícita".
                    
                    Ideas extraídas: 
                    {texto_unificado}
                    """
                    respuesta_final = modelo.generate_content(prompt_final)
                    resultado_texto = respuesta_final.text

                # --- LÓGICA 4: MATRIZ DE CONSISTENCIA ---
                elif "matriz" in peticion_lower or "consistencia" in peticion_lower:
                    prompt = f"""
                    Actúa como un metodólogo de investigación experto. 
                    Lee el siguiente artículo científico y extrae la información para armar una Matriz de Consistencia.
                    
                    REGLAS ESTRICTAS DE EXTRACCIÓN:
                    1. Si la información está en el texto, extráela de forma resumida y clara.
                    2. Si la información NO está explícita, DEBES escribir exactamente: "⚠️ No se encuentra explícito en el documento".
                    3. Para cada dato faltante, DEBES agregar un párrafo debajo llamado "💡 Alternativa de solución:".
                    
                    ESTRUCTURA DE SALIDA:
                    **1. Problema Central:** [Texto o faltante + Alternativa]
                    **2. Objetivos:** [Texto o faltante + Alternativa]
                    **3. Hipótesis:** [Texto o faltante + Alternativa]
                    **4. Variables:** [Texto o faltante + Alternativa]
                    **5. Dimensiones:** [Texto o faltante + Alternativa]
                    **6. Matriz de Consistencia (Tabla Markdown):**
                    Crea una tabla con las columnas: Problema | Objetivos | Hipótesis | Variables | Dimensiones.
                    
                    Aquí está el texto:
                    {texto_completo[:15000]}
                    """
                    respuesta = modelo.generate_content(prompt)
                    resultado_texto = respuesta.text

                # --- LÓGICA 5: OTRAS PREGUNTAS ---
                else:
                    prompt = f"""
                    Actúa como un experto en investigación. Responde de manera clara y concisa a la siguiente petición basándote en el texto:
                    PETICIÓN: "{peticion_usuario}"
                    
                    Aquí está el texto:
                    {texto_completo[:15000]}
                    """
                    respuesta = modelo.generate_content(prompt)
                    resultado_texto = respuesta.text
                
                # Mostrar resultado
                st.success("✅ ¡Análisis completado!")
                st.markdown(resultado_texto)
                
                # Botón de descarga
                st.markdown("---")
                st.subheader("📥 Descargar Resultados")
                nombre_limpio = archivo.name.replace(".pdf", "")
                st.download_button(
                    label="Descargar Resultado en formato de texto (.txt)",
                    data=resultado_texto,
                    file_name=f"Analisis_{nombre_limpio}.txt",
                    mime="text/plain",
                    type="primary"
                )
                
            except Exception as e:
                if "429" in str(e):
                    st.warning("⏳ El servidor de Google está recibiendo muchas solicitudes. Por favor, espera unos 40 segundos y vuelve a intentar.")
                else:
                    st.error(f"❌ Ocurrió un error al analizar: {e}")
