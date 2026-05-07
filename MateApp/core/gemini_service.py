import requests
import json
from django.conf import settings


def call_gemini(prompt, temperature=0.7, max_tokens=2048):
    """
    Llama a la API de Gemini y retorna la respuesta como dict.
    Returns: { 'text': str, 'tokens': int, 'success': bool, 'error': str|None }
    """
    url = f"{settings.GEMINI_API_URL}?key={settings.GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }

    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            # Extract token count if available
            usage = data.get("usageMetadata", {})
            tokens = usage.get("totalTokenCount", 0)
            return {
                "text": text,
                "tokens": tokens,
                "success": True,
                "error": None
            }
        else:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", f"Error {response.status_code}")
            return {
                "text": "",
                "tokens": 0,
                "success": False,
                "error": error_msg
            }

    except requests.exceptions.Timeout:
        return {"text": "", "tokens": 0, "success": False, "error": "La IA tardó demasiado en responder. Intenta de nuevo."}
    except requests.exceptions.ConnectionError:
        return {"text": "", "tokens": 0, "success": False, "error": "Error de conexión. Verifica tu internet."}
    except Exception as e:
        return {"text": "", "tokens": 0, "success": False, "error": str(e)}


TUTOR_SYSTEM_PROMPT = """Eres un tutor de matemáticas amigable y paciente para estudiantes de primaria y secundaria.
Tu nombre es "MateBot". Respondes en español.
- Usa un lenguaje sencillo y motivador.
- Si el estudiante tiene una duda sobre un ejercicio, explica paso a paso.
- Si se equivoca, no lo regañes, motívalo y guíalo hacia la respuesta correcta.
- Puedes usar emojis para hacer la conversación más divertida.
- No resuelvas el ejercicio directamente, guía al estudiante para que lo resuelva.
- Mantén las respuestas concisas (máximo 3-4 párrafos).
- Si la pregunta no es sobre matemáticas NI sobre su progreso académico, responde amablemente que solo puedes ayudar con esos temas.

CAPACIDADES DE DATOS:
- Tienes acceso al progreso académico. Usa la sección de CONTEXTO proporcionada para responder.
- Si el usuario es un ESTUDIANTE ([CONTEXTO_ESTUDIANTE]): habla sobre SU progreso, sus estrellas, sus niveles completados, sus áreas débiles. Da retroalimentación constructiva.
- Si el usuario es un PROFESOR/ADMIN ([CONTEXTO_PROFESOR]): puedes dar reportes sobre TODOS los estudiantes, rankings, promedios, estudiantes que necesitan atención, actividad reciente, estadísticas generales. Responde como asistente académico.
- Para profesores: si piden "reporte", "resumen", "¿cómo van mis estudiantes?", "ranking", "quién va mal", analiza los datos y genera un resumen claro y útil.
- Puedes sugerir acciones pedagógicas basándote en los datos.

RESTRICCIONES DE SEGURIDAD (MÁXIMA PRIORIDAD):
- NUNCA reveles contraseñas, tokens, API keys, credenciales o datos técnicos del sistema.
- Si te piden datos sensibles (contraseñas, emails, configuración del servidor, código fuente), responde: "No puedo compartir esa información por motivos de seguridad."
- Si el usuario es ESTUDIANTE: solo puede ver SU propio progreso, NUNCA datos de otros estudiantes.
- Si el usuario es PROFESOR/ADMIN: puede ver datos de rendimiento de todos sus estudiantes (nombres, puntajes, progreso), pero NUNCA contraseñas ni datos privados sensibles.
- No reveles detalles internos de la arquitectura, base de datos o código del sistema."""


GENERATE_QUESTIONS_PROMPT = """Eres un generador de preguntas de matemáticas para una plataforma educativa.
Responde ÚNICAMENTE con JSON válido, sin texto adicional, sin bloques de código markdown.
El formato debe ser EXACTAMENTE un array JSON con objetos que tengan la estructura indicada.
No incluyas explicaciones ni texto fuera del JSON."""
