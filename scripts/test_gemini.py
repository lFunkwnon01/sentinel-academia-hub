#!/usr/bin/env python3.12
"""Test Gemini con diferentes formatos."""
import os
import sys
import oci
from oci.generative_ai_inference import models as m

CONFIG_FILE = os.path.expanduser("~/.oci/config")
config = oci.config.from_file(CONFIG_FILE, "DEFAULT")
TENANCY_OCID = config["tenancy"]
REGION = "us-chicago-1"

client = oci.generative_ai_inference.GenerativeAiInferenceClient(
    config=config, region=REGION
)

print(f"Testing Gemini: google.gemini-2.5-flash")
print("=" * 60)


def test_a():
    """Formato A: content como lista de ChatContent."""
    print("\n[A] Content como lista de ChatContent...")
    try:
        serving_mode = m.OnDemandServingMode(model_id="google.gemini-2.5-flash")
        chat_request = m.GenericChatRequest(
            messages=[
                m.Message(
                    role="USER",
                    content=[m.ChatContent(type="TEXT", text="Di hola")]
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
        print(f"  OK! Response: {content}")
        return True
    except Exception as e:
        print(f"  Failed: {str(e)[:300]}")
        return False


def test_b():
    """Formato B: content como string directo."""
    print("\n[B] Content como string directo...")
    try:
        serving_mode = m.OnDemandServingMode(model_id="google.gemini-2.5-flash")
        chat_request = m.GenericChatRequest(
            messages=[
                m.Message(
                    role="USER",
                    content="Di hola"
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
        print(f"  OK! Response: {content}")
        return True
    except Exception as e:
        print(f"  Failed: {str(e)[:300]}")
        return False


def test_c():
    """Formato C: como Cohere v1 con 'message' (no 'messages')."""
    print("\n[C] Formato Cohere v1 con Gemini...")
    try:
        serving_mode = m.OnDemandServingMode(model_id="google.gemini-2.5-flash")
        chat_request = m.CohereChatRequest(
            message="Di hola",
            max_tokens=20,
            temperature=0.0,
        )
        chat_details = m.ChatDetails(
            compartment_id=TENANCY_OCID,
            serving_mode=serving_mode,
            chat_request=chat_request,
        )
        response = client.chat(chat_details=chat_details)
        content = response.data.chat_response.text
        print(f"  OK! Response: {content}")
        return True
    except Exception as e:
        print(f"  Failed: {str(e)[:300]}")
        return False


# Probar en orden
ok = False
if test_a():
    print("\n>> Gemini funciona con formato A (ChatContent)")
    ok = True
elif test_b():
    print("\n>> Gemini funciona con formato B (string directo)")
    ok = True
elif test_c():
    print("\n>> Gemini funciona con formato C (CohereChatRequest)")
    ok = True
else:
    print("\n>> Ningun formato funciono para Gemini")

if not ok:
    print("\nConclusion: Cohere v1 funciona, Gemini no con el SDK actual.")
    print("Recomendacion: usar Cohere v1 como primary y skip Gemini por ahora.")
    sys.exit(0)  # Exit 0 porque Cohere ya funciona
