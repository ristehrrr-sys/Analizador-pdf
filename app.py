import streamlit as st
import re
from collections import Counter
from pypdf import PdfReader

# Configuración de la página
st.set_page_config(page_title="Analizador de PDF", page_icon="📄")
st.title("📄 Analizador de PDFs")
st.write("Sube tu documento y descubre cuáles son las palabras que más se repiten.")

# Barra lateral
with st.sidebar:
    st.header("⚙️ Opciones")
    num_palabras = st.slider("¿Cuántas palabras quieres ver?", 5, 50, 10)
    quitar_stopwords = st.checkbox("Ignorar palabras comunes (el, la, de...)", value=True)

# Lista de palabras comunes en español
STOPWORDS = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "a", "en", "y", "o", "que", "es", "por", "para", "con", "se", "su", "sus", "lo", "como", "más", "pero", "le", "ya", "este", "sí", "porque", "esta", "entre", "cuando", "muy", "sin", "sobre", "también", "me", "hasta", "hay", "donde", "quien", "desde", "todo", "nos", "durante", "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos", "e", "esto", "mí", "antes", "algunos", "qué", "yo", "otro", "otras", "otra", "él", "tanto", "esa", "estos", "mucho", "quienes", "nada", "muchos", "cual", "poco", "ella", "estar", "estas", "algunas", "algo", "nosotros"}

# Subir archivo
archivo = st.file_uploader("Elige un archivo PDF", type="pdf")

if archivo is not None:
    with st.spinner("Analizando el documento... ⏳"):
        try:
            lector = PdfReader(archivo)
            texto_completo = ""
            
            for pagina in lector.pages:
                texto = pagina.extract_text()
                if texto:
                    texto_completo += texto + " "
            
            if not texto_completo.strip():
                st.warning("⚠️ El PDF no tiene texto extraíble. (¿Es una imagen escaneada?)")
            else:
                # Limpiar texto
                palabras = re.findall(r'\b\w+\b', texto_completo.lower())
                
                if quitar_stopwords:
                    palabras = [p for p in palabras if p not in STOPWORDS and len(p) > 2]
                
                contador = Counter(palabras)
                
                st.success(f"✅ ¡Análisis completado! Se encontraron {len(palabras)} palabras.")
                
                # Mostrar tabla
                st.subheader(f"Top {num_palabras} palabras:")
                datos = [{"Palabra": p, "Apariciones": c} for p, c in contador.most_common(num_palabras)]
                st.table(datos)
                
                # Mostrar gráfico
                st.subheader("Gráfico de frecuencia:")
                st.bar_chart({d["Palabra"]: d["Apariciones"] for d in datos})
                
        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {e}")
else:
    st.info("👆 Por favor, sube un archivo PDF para comenzar.")
