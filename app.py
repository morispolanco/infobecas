import streamlit as st
import requests
import json
from datetime import datetime, date
import re

# Configuración de las APIs (las claves se obtienen de los secretos de Streamlit)
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
SERPER_API_KEY = st.secrets["SERPER_API_KEY"]

def parse_date(date_string):
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
    prompt = "Proporciona información sobre becas vigentes para estudiar en cualquier país y nivel de estudios"

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
            date_match = re.search(r'Fecha límite de aplicación:?\s*(\d{2}/\d{2}/\d{4})', scholarship)
            if date_match:
                deadline = parse_date(date_match.group(1))
                if deadline and deadline >= date.today():  
                    valid_scholarships.append(scholarship.strip())

    # Llamada a la API de Serper para obtener resultados de búsqueda relacionados
    current_year = datetime.now().year
    search_query = f"becas vigentes {current_year}"
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

campo_estudio = st.text_input("Campo de estudio (opcional)")
pais = st.text_input("País de estudio (opcional)")
nivel_estudios = st.selectbox("Nivel de estudios (opcional)", [
    "", "Pregrado", "Maestría", "Doctorado", "Postdoctorado", 
    "Especialidad", "Curso", "Seminario"
])
pais_ciudadania = st.text_input("Mostrar solo becas disponibles para ciudadanos de (opcional)")

if st.button("Buscar becas vigentes"):
    if campo_estudio or pais or nivel_estudios or pais_ciudadania:
        valid_scholarships, search_results = get_scholarship_info(campo_estudio, pais, nivel_estudios, pais_ciudadania)
    else:
        prompt = "Proporciona información sobre becas vigentes para estudiar en cualquier país y nivel de estudios"
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
        scholarships = re.split(r'\n\d+\.', ai_response)
        valid_scholarships = []
        for scholarship in scholarships:
            if scholarship.strip():
                date_match = re.search(r'Fecha límite de aplicación:?\s*(\d{2}/\d{2}/\d{4})', scholarship)
                if date_match:
                    deadline = parse_date(date_match.group(1))
                    if deadline and deadline >= date.today():  
                        valid_scholarships.append(scholarship.strip())
        search_results = []
    
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
