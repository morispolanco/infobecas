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

def get_scholarship_info(campo_estudio, pais, nivel_estudios, pais_ciudadania, fecha_limite):
    prompt = "Proporciona información sobre becas vigentes para estudiar en cualquier país y nivel de estudios"

    if campo_estudio:
        prompt += f" en el campo de estudio de {campo_estudio}"
    if pais:
        prompt += f" en {pais}"
    if nivel_estudios:
        prompt += f" para nivel {nivel_estudios}"
    if pais_ciudadania:
        prompt += f" disponibles para ciudadanos de {pais_ciudadania}"
    if fecha_limite:
        prompt += f" con fecha límite de aplicación antes del {fecha_limite.strftime('%d/%m/%Y')}"

    response = requests.post(
        "https://api.together.xyz/inference",
        headers={
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "togethercomputer/llama-3.1-405b-chat",
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
    if campo_estudio or pais or nivel_estudios or pais_ciudadania or fecha_limite:
        current_year = datetime.now().year
        search_query = f"becas vigentes {current_year}"
        if campo_estudio:
            search_query += f" {campo_estudio}"
        if pais:
            search_query += f" {pais}"
        if nivel_estudios:
            search_query += f" {nivel_estudios}"
        if pais_ciudadania:
            search_query += f" para ciudadanos de {pais_ciudadania}"
        if fecha_limite:
            search_query += f" con fecha límite de aplicación antes del {fecha_limite.strftime('%d/%m/%Y')}"
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
fecha_limite = st.date_input("Fecha límite de aplicación (opcional)")

if st.button("Buscar becas"):
    valid_scholarships, search_results = get_scholarship_info(campo_estudio, pais, nivel_estudios, pais_ciudadania, fecha_limite)
    
    st.subheader("Resultados")
    if valid_scholarships:
        for scholarship in valid_scholarships:
            st.markdown(scholarship)
            st.markdown("---")
    if search_results:
        for result in search_results:
            st.write(f"- [{result.get('title')}]({result.get('link')})")
            st.write(result.get('snippet', ''))
    if not valid_scholarships and not search_results:
        st.write("")
