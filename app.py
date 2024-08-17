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
                if deadline and deadline >= date.today():  # Verificar que la fecha límite sea posterior a la fecha actual
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
