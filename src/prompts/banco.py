BANCO_DE_PROMPT = [
    {
        "nombre": "seo_youtube",
        "system_instruction": "Actúa como un experto en SEO y crecimiento en YouTube. "
        "Dado un tema de video, genera títulos atractivos optimizados para maximizar el CTR, "
        "una descripción corta persuasiva y etiquetas clave.",
        "ejemplo_usuario": "Quiero hacer un video sobre cómo aprender Python desde cero.",
        "claves_esperadas": {"titulos_sugeridos", "descripcion_seo", "tags_recomendados"},
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "titulos_sugeridos": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "descripcion_seo": {"type": "STRING"},
                "tags_recomendados": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                }
            },
            "required": ["titulos_sugeridos", "descripcion_seo", "tags_recomendados"]
        }
    },
    {
        "nombre": "estructura_guion",
        "system_instruction": "Eres un director de contenidos y guionista experto en retención de audiencia en YouTube. "
        "Diseña un gancho potente para los primeros segundos del video "
        "y una estructura modular por bloques para el contenido principal.",
        "ejemplo_usuario": "Necesito estructurar un video sobre los errores comunes al programar con asistentes de IA.",
        "claves_esperadas": {"gancho_5_segundos", "estructura_bloques", "cta_final"},
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "gancho_5_segundos": {"type": "STRING"},
                "estructura_bloques": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                },
                "cta_final": {"type": "STRING"}
            },
            "required": ["gancho_5_segundos", "estructura_bloques", "cta_final"]
        }
    },
    {
        "nombre": "analisis_competencia",
        "system_instruction": "Analiza la propuesta de valor para un video de YouTube, "
        "identificando el punto de dolor principal de la audiencia "
        "y un ángulo diferenciador único para destacar frente a otros creadores del mismo nicho.",
        "ejemplo_usuario": "Voy a subir un tutorial sobre cómo desplegar una aplicación web en Render.",
        "claves_esperadas": {"punto_dolor", "angulo_diferenciador", "publico_ideal"},
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "punto_dolor": {"type": "STRING"},
                "angulo_diferenciador": {"type": "STRING"},
                "publico_ideal": {"type": "STRING"}
            },
            "required": ["punto_dolor", "angulo_diferenciador", "publico_ideal"]
        }
    }
]