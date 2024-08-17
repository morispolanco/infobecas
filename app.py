import streamlit as st
import requests
import json
from datetime import datetime, date

# Configuración de las APIs (las claves se obtienen de los secretos de Streamlit)
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
SERPER_API_KEY = st.secrets["SERPER_API_KEY"]

def get_scholarship_info(campo_estudio, pais, nivel_estudios, fecha_limite, pais_ciudadania):
    # Asegurarse de que la fecha límite sea futura
    if fecha_limite <= date.today():
        return "Por favor, ingrese una fecha límite futura.", []

    # Construir el prompt para la API de Together
    prompt = f"""Proporciona información sobre becas vigentes para estudiar {campo_estudio} en {pais} para nivel {nivel_estudios} con fecha límite posterior a {fecha_limite.strftime('%d/%m/%Y')}.
    Es crucial que solo incluyas convocatorias que estén actualmente abiertas y cuya fecha límite sea posterior a la fecha especificada.
    Si no hay información sobre la vigencia de la convocatoria, no la incluyas.
    """
    if pais_ciudadania:
        prompt += f" Incluye solo becas disponibles para ciudadanos de {pais_ciudadania}."
    prompt += " Para cada beca, proporciona: nombre de la beca, institución que la otorga, requisitos básicos, fecha límite de aplicación y enlace oficial si está disponible."

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

    return ai_response, search_results

# Interfaz de Streamlit
st.title("Buscador de Becas Vigentes")

campo_estudio = st.text_input("Campo de estudio")
pais = st.text_input("País de estudio")
nivel_estudios = st.selectbox("Nivel de estudios", ["Pregrado", "Maestría", "Doctorado", "Postdoctorado"])
fecha_limite = st.date_input("Fecha límite de aplicación", min_value=date.today())
pais_ciudadania = st.text_input("Mostrar solo becas disponibles para ciudadanos de (dejar en blanco si no aplica)")

if st.button("Buscar becas vigentes"):
    if campo_estudio and pais and nivel_estudios and fecha_limite:
        ai_info, search_results = get_scholarship_info(campo_estudio, pais, nivel_estudios, fecha_limite, pais_ciudadania)
        
        st.subheader("Información de becas vigentes")
        st.write(ai_info)
        
        st.subheader("Resultados de búsqueda relacionados")
        if search_results:
            for result in search_results:
                st.write(f"- [{result.get('title')}]({result.get('link')})")
                st.write(result.get('snippet', ''))
        else:
            st.write("No se encontraron resultados de búsqueda.")
    else:
        st.warning("Por favor, completa todos los campos obligatorios.")
