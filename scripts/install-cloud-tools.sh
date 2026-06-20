#!/usr/bin/env bash
# Instala AWS CLI, SAM CLI y OCI CLI usando mise + pipx
# Ejecutar con sudo donde sea necesario

set -e

echo "=== 1. Verificar mise ==="
mise --version

echo ""
echo "=== 2. Instalar Python 3.14.3 via mise (si no esta) ==="
mise use --global python@3.14.3
eval "$(mise activate bash)"
mise install python@3.14.3
python3 --version

echo ""
echo "=== 3. Instalar AWS CLI via mise ==="
# AWS CLI disponible via el backend "aqua" en mise
mise use --global "ubi:aws/aws-cli@latest" 2>/dev/null || \
  mise use --global "aws-cli@latest" 2>/dev/null || \
  echo "  (usando instalacion alternativa con pip)"

# Verificar si mise lo instalo
if command -v aws &> /dev/null; then
  echo "  AWS CLI instalado via mise"
else
  echo "  Instalando AWS CLI via pip (alternativa)"
  pip install --user awscli
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  export PATH="$HOME/.local/bin:$PATH"
fi

echo ""
echo "=== 4. Instalar pipx (gestor de apps Python) ==="
# pipx necesita sudo si no esta
if ! command -v pipx &> /dev/null; then
  sudo dnf install -y pipx || pip install --user pipx
fi
pipx ensurepath
export PATH="$HOME/.local/bin:$PATH"

echo ""
echo "=== 5. Instalar SAM CLI via pipx ==="
pipx install aws-sam-cli
# Inyectar dependencias comunes
pipx inject aws-sam-cli boto3 pydantic 'aws-lambda-powertools[tracer,metrics]'

echo ""
echo "=== 6. Instalar OCI CLI via pipx ==="
pipx install oci-cli

echo ""
echo "=== 7. Recargar shell y verificar ==="
source ~/.bashrc
eval "$(mise activate bash)"

echo "Versiones instaladas:"
echo "  Python: $(python3 --version)"
echo "  AWS CLI: $(aws --version 2>&1)"
echo "  SAM CLI: $(sam --version 2>&1)"
echo "  OCI CLI: $(oci --version 2>&1)"

echo ""
echo "Si alguna version no aparece, reinicia la terminal:"
echo "  exec bash"
echo "  o cierra y abre una nueva terminal"
