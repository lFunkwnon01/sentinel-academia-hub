#!/usr/bin/env python3.12
"""Test final con TextContent (la clase correcta)."""
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

print(f"Compartment: {TENANCY_OCID[:30]}...")
print("=" * 60)


def test_model(model_id, label):
    """Prueba un modelo con TextContent."""
    print(f"\n[{label}] {model_id}...")
    try:
        serving_mode = m.OnDemandServingMode(model_id=model_id)
        chat_request = m.GenericChatRequest(
            messages=[
                m.Message(
                    role="USER",
                    content=[
                        m.TextContent(text="Di hola en una palabra")
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
        print(f"  OK! Response: {content}")
        return True
    except Exception as e:
        error = str(e)
        if "400" in error:
            # Extract message
            import re
            match = re.search(r"'message': '([^']+)'", error)
            if match:
                print(f"  400: {match.group(1)}")
            else:
                print(f"  400: {error[:200]}")
        else:
            print(f"  Error: {error[:200]}")
        return False


# Probar varios modelos
results = {}

# Cohere v1 (ya sabemos que funciona pero con CohereChatRequest)
print("\n[1] Probando con GenericChatRequest + TextContent...")
print("-" * 60)

# Probar Gemini con TextContent
results["gemini"] = test_model("google.gemini-2.5-flash", "Gemini")
results["cohere-latest"] = test_model("cohere.command-latest", "Cohere latest")
results["cohere-r"] = test_model("cohere.command-r-08-2024", "Cohere r")

print("\n" + "=" * 60)
print("RESUMEN:")
for model, ok in results.items():
    status = "OK" if ok else "FAIL"
    print(f"  {model}: {status}")
print("=" * 60)
