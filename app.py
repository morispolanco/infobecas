import streamlit as st
import requests
import json
from datetime import datetime, date
import re

# Configuración de las APIs (las claves se obtienen de los secretos de Streamlit)
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
SERPER_API_KEY = st.secrets["SERPER_API_KEY"]

def parse_date(date_string):
    # Intentar parsear fechas en varios formatos comunes
    formats = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d %B %Y', '%B %d, %Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()
        except ValueError:
            pass
    return None

def get_scholarship_info(campo_estudio, pais, nivel_estudios, pais_ciudadania):
    today = date.today()

    # Construir el prompt para la API de Together
    prompt = f"""Proporciona información sobre becas vigentes para estudiar {campo_estudio} en {pais} para nivel {nivel_estudios}.
    Es crucial que solo incluyas convocatorias cuya fecha límite de entrega de documentos sea posterior a {today.strftime('%d/%m/%Y')}.
    Si no hay información clara sobre la fecha límite de la convocatoria, no la incluyas.
    """
    if pais_ciudadania:
        prompt += f" Incluye solo becas disponibles para ciudadanos de {pais_ciudadania}."
    prompt += """ Para cada beca, proporciona la siguiente información en formato estructurado:
    1. Nombre de la beca
    2. Institución que la otorga
    3. Requisitos básicos
    4. Fecha límite de aplicación (en formato DD/MM/YYYY)
    5. Enlace oficial si está disponible
    Asegúrate de incluir la fecha límite para cada beca en el formato especificado."""

    # Llamada a la API de Together
    response = requests.post(
        "https://api.together.xyz/inference",
        headers={
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "togethercomputer/llama-2-70b-chat",
            "prompt": prompt,
            "max_tokens": 1024,
            "temperature": 0.7
        }
    )
    ai_response = response.json().get("choices", [{}])[0].get("text", "")

    # Procesar la respuesta de la IA para extraer y verificar las fechas
    scholarships = re.split(r'\n\d+\.', ai_response)
    valid_scholarships = []
    for scholarship in scholarships:
        if scholarship.strip():
            # Buscar la fecha límite en el texto de la beca
            date_match = re.search(r'Fecha límite de aplicación:?\s*(\d{2}/\d{2}/\d{4})', scholarship)
            if date_match:
                deadline = parse_date(date_match.group(1))
                if deadline and deadline > today:
                    valid_scholarships.append(scholarship.strip())

    # Llamada a la API de Serper para obtener resultados de búsqueda relacionados
    current_year = datetime.now().year
    search_query = f"becas vigentes {campo_estudio} {pais} {nivel_estudios} {current_year}"
    if pais_ciudadania:
        search_query += f" para ciudadanos de {pais_ciudadania}"
    serper_response = requests.post(
        "https://google.serper.dev/search",
        headers={
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "q": search_query
        }
    )
    search_results = serper_response.json().get("organic", [])[:5]  # Limitamos a los 5 primeros resultados

    return valid_scholarships, search_results

# Interfaz de Streamlit
st.title("Buscador de Becas Vigentes")

campo_estudio = st.text_input("Campo de estudio")
pais = st.text_input("País de estudio")
nivel_estudios = st.selectbox("Nivel de estudios", [
    "Pregrado", "Maestría", "Doctorado", "Postdoctorado", 
    "Especialidad", "Curso", "Seminario"
])
pais_ciudadania = st.text_input("Mostrar solo becas disponibles para ciudadanos de (dejar en blanco si no aplica)")

if st.button("Buscar becas vigentes"):
    if campo_estudio and pais and nivel_estudios:
        valid_scholarships, search_results = get_scholarship_info(campo_estudio, pais, nivel_estudios, pais_ciudadania)
        
        st.subheader("Becas vigentes encontradas")
        if valid_scholarships:
            for scholarship in valid_scholarships:
                st.markdown(scholarship)
                st.markdown("---")
        else:
            st.write("No se encontraron becas vigentes que cumplan con los criterios especificados.")
        
        st.subheader("Resultados de búsqueda relacionados")
        if search_results:
            for result in search_results:
                st.write(f"- [{result.get('title')}]({result.get('link')})")
                st.write(result.get('snippet', ''))
        else:
            st.write("No se encontraron resultados de búsqueda adicionales.")
    else:
        st.warning("Por favor, completa todos los campos obligatorios.")
