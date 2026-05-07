"""
Prueba rápida de la API de Gemini (Google Generative AI)
Ejecutar: python test_gemini.py
"""
import requests
import json

# ⚠️ Reemplaza con tu API Key real
API_KEY = "AIzaSyDvmj2IPyArfCiiFQYyeW2KLoi1zvAlJB0"

# Endpoint de Gemini
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={API_KEY}"

# Prompt de prueba
payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": "Hola como estas?"
                }
            ]
        }
    ],
    "generationConfig": {
        "temperature": 0.7,
        "maxOutputTokens": 1024
    }
}

def test_gemini():
    print("🚀 Enviando solicitud a Gemini API...")
    print("-" * 50)

    try:
        response = requests.post(
            URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )

        print(f"Status Code: {response.status_code}")
        print("-" * 50)

        if response.status_code == 200:
            data = response.json()
            # Extraer el texto de la respuesta
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            print("✅ Respuesta de Gemini:\n")
            print(text)
            print("-" * 50)

            # Intentar parsear el JSON de la respuesta
            try:
                # Gemini a veces envuelve el JSON en ```json ... ```
                clean = text.strip()
                if clean.startswith("```"):
                    clean = clean.split("\n", 1)[1]  # quitar primera línea ```json
                    clean = clean.rsplit("```", 1)[0]  # quitar último ```
                exercises = json.loads(clean)
                print("📋 Ejercicios parseados:")
                for i, ex in enumerate(exercises, 1):
                    print(f"   {i}. {ex['pregunta']} = {ex['respuesta']}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"⚠️ No se pudo parsear como JSON: {e}")
                print("   (La respuesta de texto sigue siendo válida arriba)")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.json())

    except requests.exceptions.Timeout:
        print("❌ Timeout: La API tardó demasiado en responder")
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión: Verifica tu internet")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    test_gemini()
