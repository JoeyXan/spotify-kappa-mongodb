#!/bin/bash

# Script de inicio para Sistema Kappa con MongoDB
# Para ejecutar en servidor Ubuntu

echo "=== Sistema de Recomendación - Arquitectura Kappa con MongoDB ==="
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 no está instalado"
    exit 1
fi

# Verificar MongoDB URI
if [ -z "$MONGODB_URI" ] && [ ! -f ".streamlit/secrets.toml" ]; then
    echo "ERROR: No se encontró la configuración de MongoDB"
    echo ""
    echo "Configura la variable de entorno MONGODB_URI:"
    echo '  export MONGODB_URI="mongodb+srv://usuario:password@cluster.mongodb.net/"'
    echo ""
    echo "O crea el archivo .streamlit/secrets.toml con:"
    echo '  [mongodb]'
    echo '  uri = "mongodb+srv://usuario:password@cluster.mongodb.net/"'
    echo ""
    echo "Ver MONGODB_SETUP.md para más información"
    exit 1
fi

# Instalar dependencias
echo "Instalando dependencias..."
pip3 install -r requirements.txt

echo ""
echo "=== Iniciando aplicación Streamlit ==="
echo ""
echo "La aplicación estará disponible en:"
echo "  - Local: http://localhost:8501"
echo "  - Red: http://$(hostname -I | awk '{print $1}'):8501"
echo ""
echo "Conectado a MongoDB Atlas"
echo ""
echo "Presiona Ctrl+C para detener"
echo ""

# Iniciar Streamlit
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
