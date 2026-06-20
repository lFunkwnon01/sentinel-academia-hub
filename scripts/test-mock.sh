#!/usr/bin/env bash
# Script para probar el mock del API
# Uso: bash scripts/test-mock.sh

set -e
BASE_URL="${BASE_URL:-http://127.0.0.1:4010}"

echo "Probando mock en $BASE_URL"
echo "=========================================="

# 1. GET /api/dashboard/metrics
echo ""
echo "1. GET /api/dashboard/metrics?rango=30"
echo "------------------------------------------"
curl -s "$BASE_URL/api/dashboard/metrics?rango=30" | head -c 500
echo ""

# 2. GET /api/quejas
echo ""
echo "2. GET /api/quejas"
echo "------------------------------------------"
curl -s "$BASE_URL/api/quejas" | head -c 500
echo ""

# 3. POST /api/quejas
echo ""
echo "3. POST /api/quejas"
echo "------------------------------------------"
curl -s -X POST "$BASE_URL/api/quejas" \
  -H "Content-Type: application/json" \
  -H "x-correlation-id: test-script-1" \
  -d '{
    "titulo": "Queja de prueba desde script",
    "descripcion": "Descripcion suficientemente larga para validar",
    "categoriaDeclarada": "ACADEMICA"
  }' | head -c 500
echo ""

# 4. GET /api/quejas/{id}/analysis
echo ""
echo "4. GET /api/quejas/q-test-123/analysis"
echo "------------------------------------------"
curl -s "$BASE_URL/api/quejas/q-test-123/analysis" | head -c 500
echo ""

# 5. POST /api/chat
echo ""
echo "5. POST /api/chat"
echo "------------------------------------------"
curl -s -X POST "$BASE_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Cual es el proceso para escalar una queja critica?"
  }' | head -c 500
echo ""

echo ""
echo "=========================================="
echo "Si ves respuestas JSON arriba, el mock funciona correctamente."
