# Archivo: app.py

import streamlit as st
import requests
import json
import os

# Configuración de la página
st.set_page_config(page_title="Asistente Legal y de Becas de Guatemala", page_icon="🇬🇹", layout="wide")

# Acceder a las claves de API de las variables de entorno
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
SERPER_API_KEY = os.environ.get("SERPER_API_KEY")

def buscar_informacion(query, solo_becas=False):
    url = "https://google.serper.dev/search"
    if solo_becas:
        query += " becas para guatemaltecos"
    else:
        query += " ley Guatemala"
    
    payload = json.dumps({
        "q": query
    })
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()

def generar_respuesta(prompt, contexto, solo_becas=False):
    url = "https://api.together.xyz/inference"
    if solo_becas:
        instruccion = "Responde la pregunta basándote en el contexto proporcionado y tu conocimiento general sobre becas disponibles para guatemaltecos. Si no hay información específica sobre becas para guatemaltecos, indícalo claramente."
    else:
        instruccion = "Responde la pregunta basándote en el contexto proporcionado y tu conocimiento general sobre las leyes de Guatemala. Si no tienes suficiente información, indica que no puedes responder con certeza."
    
    payload = json.dumps({
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "prompt": f"Contexto: {contexto}\n\nPregunta: {prompt}\n\n{instruccion}\n\nRespuesta:",
        "max_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.7,
        "top_k": 50,
        "repetition_penalty": 1,
        "stop": ["Pregunta:"]
    })
    headers = {
        'Authorization': f'Bearer {TOGETHER_API_KEY}',
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()['output']['choices'][0]['text'].strip()

def main():
    # Título de la aplicación
    st.title("Asistente Legal y de Becas de Guatemala 🇬🇹⚖️📚")

    # Checkbox para filtrar solo becas para guatemaltecos
    solo_becas = st.checkbox("Mostrar solo resultados de becas disponibles para guatemaltecos")

    # Interfaz de usuario
    if solo_becas:
        pregunta = st.text_input("Ingresa tu pregunta sobre becas para guatemaltecos:")
    else:
        pregunta = st.text_input("Ingresa tu pregunta sobre la ley de Guatemala o becas:")

    if st.button("Obtener respuesta"):
        if pregunta:
            with st.spinner("Buscando información y generando respuesta..."):
                # Buscar información relevante
                resultados_busqueda = buscar_informacion(pregunta, solo_becas)
                contexto = "\n".join([result.get('snippet', '') for result in resultados_busqueda.get('organic', [])])
                
                # Generar respuesta
                respuesta = generar_respuesta(pregunta, contexto, solo_becas)
                
                # Mostrar respuesta
                st.write("Respuesta:")
                st.write(respuesta)
                
                # Mostrar fuentes
                st.write("Fuentes:")
                for resultado in resultados_busqueda.get('organic', [])[:3]:
                    st.write(f"- [{resultado['title']}]({resultado['link']})")
        else:
            st.warning("Por favor, ingresa una pregunta.")

    # Agregar información en el pie de página
    st.markdown("---")
    st.markdown("**Nota:** Este asistente utiliza IA para generar respuestas basadas en información disponible en línea. "
                "Siempre verifica la información con fuentes oficiales para asuntos legales o de becas importantes.")

if __name__ == "__main__":
    main()
