#!/usr/bin/env bash
# Regenera todos los diagramas Mermaid usando mermaid.ink (sin dependencias)
# Uso: bash scripts/regenerate-diagrams.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
DIAGRAMS_DIR="$ROOT_DIR/docs/02-arquitectura"
FUENTES_DIR="$DIAGRAMS_DIR/fuentes"
OUTPUT_DIR="$DIAGRAMS_DIR/diagrams"

# Verificar que existen las carpetas
if [ ! -d "$FUENTES_DIR" ]; then
  echo "ERROR: No se encontro la carpeta $FUENTES_DIR"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

# Regenerar todos los .mmd
for mmd_file in "$FUENTES_DIR"/*.mmd; do
  if [ -f "$mmd_file" ]; then
    filename=$(basename "$mmd_file" .mmd)
    echo "Procesando $filename..."

    # Generar PNG
    encoded=$(base64 -w 0 < "$mmd_file" | tr '+/' '-_' | tr -d '=')
    curl -s -o "$OUTPUT_DIR/${filename}.png" \
      "https://mermaid.ink/img/${encoded}?type=png&bgColor=white" \
      -w "  PNG: %{http_code} (%{size_download} bytes)\n"

    # Generar SVG
    curl -s -o "$OUTPUT_DIR/${filename}.svg" \
      "https://mermaid.ink/svg/${encoded}" \
      -w "  SVG: %{http_code} (%{size_download} bytes)\n"
  fi
done

# Regenerar tambien el diagrama de resiliencia
RESILIENCIA_DIR="$ROOT_DIR/docs/03-resiliencia-llm/diagrams"
if [ -d "$RESILIENCIA_DIR" ]; then
  for mmd_file in "$RESILIENCIA_DIR"/*.mmd; do
    if [ -f "$mmd_file" ]; then
      filename=$(basename "$mmd_file" .mmd)
      echo "Procesando $filename (resiliencia)..."

      encoded=$(base64 -w 0 < "$mmd_file" | tr '+/' '-_' | tr -d '=')
      curl -s -o "$RESILIENCIA_DIR/${filename}.png" \
        "https://mermaid.ink/img/${encoded}?type=png&bgColor=white" \
        -w "  PNG: %{http_code} (%{size_download} bytes)\n"

      curl -s -o "$RESILIENCIA_DIR/${filename}.svg" \
        "https://mermaid.ink/svg/${encoded}" \
        -w "  SVG: %{http_code} (%{size_download} bytes)\n"
    fi
  done
fi

echo ""
echo "Listo. Diagramas regenerados en:"
echo "  $OUTPUT_DIR"
[ -d "$RESILIENCIA_DIR" ] && echo "  $RESILIENCIA_DIR"
