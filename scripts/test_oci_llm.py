#!/usr/bin/env python3.12
"""Test OCI GenAI con clases correctas del SDK."""
import os
import sys
import oci
from oci.generative_ai_inference import models as m

# Cargar config
CONFIG_FILE = os.path.expanduser("~/.oci/config")
config = oci.config.from_file(CONFIG_FILE, "DEFAULT")
TENANCY_OCID = config["tenancy"]
REGION = "us-chicago-1"

# Crear cliente
client = oci.generative_ai_inference.GenerativeAiInferenceClient(
    config=config,
    region=REGION,
)

print(f"Compartment: {TENANCY_OCID[:30]}...")
print("-" * 60)


def test_cohere_v2():
    """Prueba con CohereChatRequestV2 (formato Cohere v2)."""
    print("\n[1] Testing Cohere v2 (CohereChatRequestV2)...")
    try:
        serving_mode = m.OnDemandServingMode(model_id="cohere.command-latest")

        # Cohere v2 espera contenido como string directo, no como dict
        chat_request = m.CohereChatRequestV2(
            messages=[
                m.CohereUserMessageV2(
                    content="Di hola en una palabra",
                )
            ],
            max_tokens=20,
            temperature=0.0,
        )

        chat_details = m.ChatDetails(
            compartment_id=TENANCY_OCID,
            serving_mode=serving_mode,
            chat_request=chat_request,
        )

        response = client.chat(chat_details=chat_details)
        content = response.data.chat_response.choices[0].message.content
        print(f"  OK!")
        print(f"  Response: {content}")
        return True
    except Exception as e:
        print(f"  Failed: {str(e)[:200]}")
        return False


def test_cohere_v1():
    """Prueba con CohereChatRequest (formato Cohere v1)."""
    print("\n[2] Testing Cohere v1 (CohereChatRequest)...")
    try:
        serving_mode = m.OnDemandServingMode(model_id="cohere.command-latest")

        chat_request = m.CohereChatRequest(
            message="Di hola en una palabra",  # v1 usa 'message' singular
            max_tokens=20,
            temperature=0.0,
            is_stream=False,
        )

        chat_details = m.ChatDetails(
            compartment_id=TENANCY_OCID,
            serving_mode=serving_mode,
            chat_request=chat_request,
        )

        response = client.chat(chat_details=chat_details)
        content = response.data.chat_response.text  # v1 usa .text
        print(f"  OK!")
        print(f"  Response: {content}")
        return True
    except Exception as e:
        print(f"  Failed: {str(e)[:200]}")
        return False


def test_generic():
    """Prueba con GenericChatRequest (formato generico)."""
    print("\n[3] Testing generic (GenericChatRequest)...")
    try:
        serving_mode = m.OnDemandServingMode(model_id="cohere.command-latest")

        # GenericChatRequest con ChatContent
        chat_request = m.GenericChatRequest(
            messages=[
                m.Message(
                    role="USER",
                    content=[
                        m.ChatContent(type="TEXT", text="Di hola")
                    ]
                )
            ],
            max_tokens=20,
            temperature=0.0,
        )

        chat_details = m.ChatDetails(
            compartment_id=TENANCY_OCID,
            serving_mode=serving_mode,
            chat_request=chat_request,
        )

        response = client.chat(chat_details=chat_details)
        content = response.data.chat_response.choices[0].message.content
        print(f"  OK!")
        print(f"  Response: {content}")
        return True
    except Exception as e:
        print(f"  Failed: {str(e)[:200]}")
        return False


def test_gemini():
    """Prueba con Gemini como fallback."""
    print("\n[4] Testing Gemini (google.gemini-2.5-flash)...")
    try:
        serving_mode = m.OnDemandServingMode(model_id="google.gemini-2.5-flash")

        # Gemini tambien usa chat API
        chat_request = m.GenericChatRequest(
            messages=[
                m.Message(
                    role="USER",
                    content=[
                        m.ChatContent(type="TEXT", text="Di hola")
                    ]
                )
            ],
            max_tokens=20,
            temperature=0.0,
        )

        chat_details = m.ChatDetails(
            compartment_id=TENANCY_OCID,
            serving_mode=serving_mode,
            chat_request=chat_request,
        )

        response = client.chat(chat_details=chat_details)
        content = response.data.chat_response.choices[0].message.content
        print(f"  OK!")
        print(f"  Response: {content}")
        return True
    except Exception as e:
        print(f"  Failed: {str(e)[:200]}")
        return False


# Probar en orden
if test_cohere_v2():
    print("\n  >> Cohere v2 funciona como PRIMARY")
elif test_cohere_v1():
    print("\n  >> Cohere v1 funciona como PRIMARY")
elif test_generic():
    print("\n  >> Chat generico funciona como PRIMARY")
elif test_gemini():
    print("\n  >> Gemini funciona como FALLBACK")
else:
    print("\n  >> Ningun modelo funciono. Revisar permisos/IAM.")
    sys.exit(1)
