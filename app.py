import streamlit as st
import requests
import json
from datetime import datetime

# Configuración de las APIs (las claves se obtienen de los secretos de Streamlit)
TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]
SERPER_API_KEY = st.secrets["SERPER_API_KEY"]

def get_scholarship_info(campo_estudio, pais, nivel_estudios, fecha_limite, solo_guatemaltecos):
    # Construir el prompt para la API de Together
    prompt = f"Proporciona información sobre becas para estudiar {campo_estudio} en {pais} para nivel {nivel_estudios} con fecha límite cercana a {fecha_limite}."
    if solo_guatemaltecos:
        prompt += " Incluye solo becas disponibles para guatemaltecos."
    prompt += " Incluye nombres de becas, requisitos básicos y enlaces si están disponibles."
    
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
            "max_tokens": 512,
            "temperature": 0.7
        }
    )
    
    ai_response = response.json()["output"]["choices"][0]["text"]
    
    # Llamada a la API de Serper para obtener resultados de búsqueda relacionados
    search_query = f"becas {campo_estudio} {pais} {nivel_estudios}"
    if solo_guatemaltecos:
        search_query += " para guatemaltecos"
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
    
    search_results = serper_response.json()["organic"][:3]  # Tomamos los primeros 3 resultados
    
    return ai_response, search_results

# Interfaz de Streamlit
st.title("Buscador de Becas")

campo_estudio = st.text_input("Campo de estudio")
pais = st.text_input("País")
nivel_estudios = st.selectbox("Nivel de estudios", ["Pregrado", "Maestría", "Doctorado", "Postdoctorado"])
fecha_limite = st.date_input("Fecha límite de aplicación")
solo_guatemaltecos = st.checkbox("Mostrar solo becas disponibles para guatemaltecos")

if st.button("Buscar becas"):
    if campo_estudio and pais and nivel_estudios and fecha_limite:
        fecha_limite_str = fecha_limite.strftime("%d/%m/%Y")
        ai_info, search_results = get_scholarship_info(campo_estudio, pais, nivel_estudios, fecha_limite_str, solo_guatemaltecos)
        
        st.subheader("Información de becas")
        st.write(ai_info)
        
        st.subheader("Resultados de búsqueda relacionados")
        for result in search_results:
            st.write(f"- [{result['title']}]({result['link']})")
            st.write(result['snippet'])
    else:
        st.warning("Por favor, completa todos los campos.")
