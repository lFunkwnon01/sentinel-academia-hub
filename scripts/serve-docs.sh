#!/usr/bin/env bash
# Construye y sirve la documentacion del API con Redoc
# Uso: bash scripts/serve-docs.sh [puerto]

PORT="${1:-8080}"

echo "Construyendo documentacion con Redoc..."
npx @redocly/cli build-docs api-mock/openapi.yaml --output api-docs.html

if [ ! -f api-docs.html ]; then
  echo "ERROR: No se genero api-docs.html"
  exit 1
fi

echo ""
echo "Documentacion generada: api-docs.html"
echo ""
echo "Sirviendo en http://localhost:$PORT/api-docs.html"
echo "Para detener: Ctrl+C"
echo ""

# Servir el directorio actual en el puerto especificado
# Usar python3 si esta disponible, sino npx http-server
if command -v python3 &> /dev/null; then
  cd "$(dirname api-docs.html)"
  python3 -m http.server $PORT
elif command -v npx &> /dev/null; then
  npx http-server -p $PORT
else
  echo "ERROR: Necesitas Python 3 o Node.js instalado"
  exit 1
fi
