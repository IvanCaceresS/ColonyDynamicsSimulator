#!/bin/bash

# Salir inmediatamente si un comando falla
set -e

# Nombre del entorno virtual
VENV_DIR="venv"

# --- Comprobación de Python 3 ---
# Intenta encontrar python3 o python, prefiere python3
PYTHON_CMD=python3
if ! command -v python3 &> /dev/null
then
    echo "Advertencia: Comando 'python3' no encontrado, intentando con 'python'."
    PYTHON_CMD=python
    if ! command -v python &> /dev/null
    then
        echo "Error: No se encontró 'python3' ni 'python'. Asegúrate de que Python 3 esté instalado y en el PATH."
        exit 1
    fi
fi
echo "Usando $($PYTHON_CMD --version) para crear el entorno."

# --- Eliminar Entorno Existente (Opcional) ---
if [ -d "$VENV_DIR" ]; then
    echo "Eliminando entorno virtual existente ($VENV_DIR)..."
    rm -rf "$VENV_DIR"
fi

# --- Crear Entorno Virtual ---
echo "Creando nuevo entorno virtual en '$VENV_DIR'..."
"$PYTHON_CMD" -m venv "$VENV_DIR"
if [ $? -ne 0 ]; then
    echo "Error: Falló la creación del entorno virtual."
    exit 1
fi

# --- Activar Entorno Virtual (para este script) ---
# Nota: Esto activa el entorno SOLO para los comandos DENTRO de este script.
# NO activa el entorno en tu terminal después de que el script termine.
echo "Activando entorno virtual para la instalación..."
source "$VENV_DIR/bin/activate"

# --- Verificar Activación (dentro del script) ---
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: No se pudo activar el entorno virtual internamente para instalar paquetes."
    exit 1
else
    echo "Entorno virtual activado temporalmente (Python: $(which python))."
fi


# --- Actualizar Herramientas Base ---
echo "Actualizando pip, setuptools y wheel..."
python -m pip install --upgrade pip setuptools wheel
if [ $? -ne 0 ]; then
    echo "Error: Falló la actualización de pip/setuptools/wheel."
    # Considera salir aquí si es crítico: exit 1
fi

# --- Instalar Dependencias ---
if [ -f "requirements.txt" ]; then
    echo "Instalando dependencias desde requirements.txt..."
    pip install --no-cache-dir -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Falló la instalación de dependencias desde requirements.txt."
        exit 1
    fi
else
    echo "No se encontró requirements.txt, omitiendo instalación de dependencias."
fi

# --- Desactivar (opcional, el script terminará de todos modos) ---
# echo "Desactivando entorno virtual temporal..."
# deactivate # Opcional, ya que el script está a punto de terminar

# --- Mensaje Final ---
echo "" # Línea en blanco
echo "--------------------------------------------------------------------"
echo "Entorno virtual '$VENV_DIR' configurado y actualizado exitosamente."
echo ""
echo "Para ACTIVARLO en tu terminal, ejecuta:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "Para DESACTIVARLO, simplemente ejecuta:"
echo "  deactivate"
echo "--------------------------------------------------------------------"

exit 0