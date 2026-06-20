#!/usr/bin/env bash
# AWS Academy setup - Version mejorada
# Credenciales SOLO en memoria (no se guardan en archivos)

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  AWS Academy - Setup Seguro v2${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo "Vamos a configurar las credenciales."
echo "Las 2 sensibles (secret y token) NO se veran en pantalla."
echo ""

# Funcion helper (sin eval que rompe con caracteres especiales)
ask_input() {
  local prompt="$1"
  local is_secret="$2"
  local var_name="$3"
  local value=""

  if [ "$is_secret" = "secret" ]; then
    read -s -r -p "$prompt" value
    echo ""
  else
    read -r -p "$prompt" value
  fi

  if [ -z "$value" ]; then
    echo -e "${RED}ERROR: '$prompt' no puede estar vacio${NC}" >&2
    return 1
  fi

  # printf -v asigna de forma segura (no usa eval, no rompe con caracteres especiales)
  printf -v "$var_name" '%s' "$value"
  unset value
}

# Verificar AWS CLI
if ! command -v aws &> /dev/null; then
  echo -e "${RED}ERROR: AWS CLI no instalado. Ejecuta: sudo dnf install -y awscli${NC}"
  exit 1
fi

# Verificar si ya hay credenciales
if [ -n "$AWS_ACCESS_KEY_ID" ] && aws sts get-caller-identity &>/dev/null; then
  echo -e "${GREEN}Ya tienes credenciales validas:${NC}"
  echo "  Account: $(aws sts get-caller-identity --query Account --output text 2>/dev/null)"
  echo ""
  read -p "Reconfigurar de todas formas? (s/n): " RECONFIG
  if [ "$RECONFIG" != "s" ] && [ "$RECONFIG" != "S" ]; then
    echo "OK, saliendo"
    exit 0
  fi
fi

# Pedir las 3 credenciales (paso a paso)
echo -e "${CYAN}Paso 1/3: Access Key ID${NC}"
echo "  (empieza con ASIAT o AKIA, ~20 caracteres)"
ask_input "  Pegar aqui: " "normal" "AWS_ACCESS_KEY_ID" || exit 1
echo ""

echo -e "${CYAN}Paso 2/3: Secret Access Key${NC}"
echo "  (cadena larga de ~40 caracteres, NO se vera al escribir)"
ask_input "  Pegar aqui (no se ve): " "secret" "AWS_SECRET_ACCESS_KEY" || exit 1
echo ""

echo -e "${CYAN}Paso 3/3: Session Token${NC}"
echo "  (cadena MUY larga, ~500 caracteres, NO se vera al escribir)"
ask_input "  Pegar aqui (no se ve): " "secret" "AWS_SESSION_TOKEN" || exit 1
echo ""

# Region
read -p "Region [us-east-1]: " REGION_INPUT
REGION=${REGION_INPUT:-us-east-1}

# Exportar
export AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY
export AWS_SESSION_TOKEN
export AWS_DEFAULT_REGION=$REGION
export AWS_REGION=$REGION

# Verificar
echo ""
echo -e "${CYAN}Verificando credenciales...${NC}"
RESULT=$(aws sts get-caller-identity 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  # Parsear respuesta JSON
  ACCOUNT=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['Account'])" 2>/dev/null || echo "$RESULT" | grep -oP '"Account":\s*"\K[^"]+')
  USER_ARN=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['Arn'])" 2>/dev/null || echo "$RESULT" | grep -oP '"Arn":\s*"\K[^"]+')

  echo -e "${GREEN}OK Credenciales validas${NC}"
  echo ""
  echo "  Account: $ACCOUNT"
  echo "  Region: $REGION"
  echo "  ARN: $USER_ARN"
  echo ""

  # Crear bucket SAM
  echo -e "${CYAN}Creando bucket S3 para SAM artifacts...${NC}"
  BUCKET_NAME="sentinel-sam-artifacts-$(date +%s)"
  if aws s3 mb "s3://${BUCKET_NAME}" --region "$REGION" 2>&1 | grep -q "make_bucket"; then
    echo -e "${GREEN}Bucket creado: $BUCKET_NAME${NC}"
    echo "$BUCKET_NAME" > ~/.sentinel-sam-bucket
    echo "SAM_BUCKET_NAME=$BUCKET_NAME" > /home/lFunknown/sentinel-academia/.env.deploy
  else
    echo -e "${YELLOW}No se pudo crear (puede que ya exista)${NC}"
    if [ -f ~/.sentinel-sam-bucket ]; then
      BUCKET_NAME=$(cat ~/.sentinel-sam-bucket)
      echo "Usando bucket existente: $BUCKET_NAME"
    fi
  fi

  # Alias
  echo ""
  read -p "Agregar alias 'aws-setup' a tu ~/.bashrc? (s/n): " ADD_ALIAS
  if [ "$ADD_ALIAS" = "s" ] || [ "$ADD_ALIAS" = "S" ]; then
    LINE='alias aws-setup="bash /home/lFunknown/sentinel-academia/scripts/aws-academy-setup.sh"'
    if ! grep -q "aws-setup" ~/.bashrc; then
      echo "" >> ~/.bashrc
      echo "# AWS Academy setup alias" >> ~/.bashrc
      echo "$LINE" >> ~/.bashrc
      echo -e "${GREEN}Alias agregado${NC}"
      echo "  En nuevas terminales: ejecuta 'aws-setup'"
    else
      echo "Alias ya existe en ~/.bashrc"
    fi
  fi

  echo ""
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}  LISTO! Credenciales activas${NC}"
  echo -e "${GREEN}========================================${NC}"
  echo ""
  echo "Estas credenciales expiran en 3-4 horas."
  echo "Cuando caduquen:"
  echo "  1. AWS Academy → End Lab → Start Lab"
  echo "  2. Copia las 3 nuevas credenciales"
  echo "  3. Ejecuta: aws-setup"
else
  echo -e "${RED}ERROR: Credenciales invalidas${NC}"
  echo "$RESULT"
  echo ""
  echo "Posibles causas:"
  echo "  1. Copiaste mal alguna credencial (verifica espacios al inicio/final)"
  echo "  2. Tu lab de AWS Academy expiro (Empezaste uno nuevo?)"
  echo "  3. Las credenciales son de otro entorno"
  echo ""
  echo -e "${YELLOW}Tip: En AWS Academy, click 'Start Lab' y espera 1-2 min${NC}"
  echo -e "${YELLOW}antes de copiar las credenciales.${NC}"
  exit 1
fi
