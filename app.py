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
                
                modelo = genai.GenerativeModel('gemini-3.5-flash-lite')
                
                resultado_texto = ""
                peticion_lower = peticion_usuario.lower()

                # --- LÓGICA 1: BUSCAR AUTOR Y SU IDEA EN 15 PALABRAS ---
                if any(palabra in peticion_lower for palabra in ["busca a", "autor", "quien es", "idea de", "piensa"]):
                    prompt = f"""
                    Act as an expert researcher. 
                    Search the following text for information regarding the user's request: "{peticion_usuario}".
                    
                    Your response MUST strictly follow this format (translate the output to Spanish):
                    **Autor encontrado:** [Author's name]
                    **Idea Central:** [Summarize their main idea in 15 words or less]
                    **Cita del texto:** [A short quote from the text supporting this idea]
                    
                    If the author is not found, respond exactly: "El autor no se menciona en el documento proporcionado".
                    
                    Text:
                    {texto_completo[:25000]}
                    """
                    respuesta = modelo.generate_content(prompt)
                    resultado_texto = respuesta.text

                # --- LÓGICA 2: REDACTAR ANTECEDENTES ESTRUCTURADOS ---
                elif "antecedente" in peticion_lower:
                    prompt = f"""
                    Act as an expert methodologist specialized in APA 7th edition. 
                    Read the following scientific article and extract the research background (previous studies mentioned in the text).
                    
                    FOR EACH BACKGROUND STUDY FOUND, you must use STRICTLY the following structure (translate the output to Spanish):
                    
                    ---
                    **[Number]. [Author's Last Name], [Year]**
                    *   **Muestra:** [Indicate the sample size or type. If not mentioned, write "No especificada".]
                    *   **Objetivo:** [State the main objective in one sentence.]
                    *   **Metodología:** [Briefly describe the methodology.]
                    *   **Resultados:** [State the main finding in one sentence.]
                    *   **Aporte:** [Explain why it is relevant to the current research.]
                    ---
                    
                    If the document does not mention clear backgrounds, write: "El documento no presenta una sección explícita de antecedentes".
                    
                    Text:
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
                        Extract the 3 most important central ideas from this text fragment and EXPLICITLY LOOK for the sample size (number of participants). Be very concise. Output in Spanish.
                        Text: {bloque}
                        """
                        res = modelo.generate_content(prompt_bloque)
                        ideas_parciales.append(res.text)
                    texto_unificado = "\n".join(ideas_parciales)
                    prompt_final = f"""
                    Combine these ideas into a single structured summary in Spanish. 
                    MANDATORY: You must include a "Muestra" section with the number of participants if found. If not mentioned, write "La muestra no está explícita".
                    
                    Extracted ideas: 
                    {texto_unificado}
                    """
                    respuesta_final = modelo.generate_content(prompt_final)
                    resultado_texto = respuesta_final.text

                # --- LÓGICA 4: MATRIZ DE CONSISTENCIA ---
                elif "matriz" in peticion_lower or "consistencia" in peticion_lower:
                    prompt = f"""
                    Act as an expert research methodologist. 
                    Read the following scientific article and extract the information to build a Consistency Matrix (Matriz de Consistencia). Output in Spanish.
                    
                    STRICT EXTRACTION RULES:
                    1. If the information is in the text, extract it clearly and concisely.
                    2. If the information is NOT explicit, you MUST write exactly: "⚠️ No se encuentra explícito en el documento".
                    3. For each missing piece of information, you MUST add a paragraph below called "💡 Alternativa de solución:".
                    
                    OUTPUT STRUCTURE:
                    **1. Problema Central:** [Extracted text or missing + Alternative]
                    **2. Objetivos:** [Extracted text or missing + Alternative]
                    **3. Hipótesis:** [Extracted text or missing + Alternative]
                    **4. Variables:** [Extracted text or missing + Alternative]
                    **5. Dimensiones:** [Extracted text or missing + Alternative]
                    **6. Matriz de Consistencia (Markdown Table):**
                    Create a table with columns: Problema | Objetivos | Hipótesis | Variables | Dimensiones.
                    
                    Text:
                    {texto_completo[:15000]}
                    """
                    respuesta = modelo.generate_content(prompt)
                    resultado_texto = respuesta.text

                # --- LÓGICA 5: OTRAS PREGUNTAS ---
                else:
                    prompt = f"""
                    Act as a research expert. Answer the following request clearly and concisely based on the text. Output in Spanish.
                    REQUEST: "{peticion_usuario}"
                    
                    Text:
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
