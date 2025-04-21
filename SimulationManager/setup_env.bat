@echo off
setlocal enabledelayedexpansion

:: Nombre del entorno virtual
set VENV_DIR=venv

:: Si el entorno ya existe, eliminarlo
if exist %VENV_DIR% (
    echo Eliminando entorno virtual existente...
    rmdir /s /q %VENV_DIR%
)

:: Crear el entorno virtual
echo Creando nuevo entorno virtual...
python -m venv %VENV_DIR%

:: Activar el entorno virtual
call %VENV_DIR%\Scripts\activate

:: Verificar si la activación fue exitosa
if "%VIRTUAL_ENV%"=="" (
    echo Error: No se pudo activar el entorno virtual.
    pause
    exit /b 1
)

:: Actualizar pip, setuptools y wheel
echo Actualizando pip, setuptools y wheel...
python -m pip install --upgrade pip setuptools wheel

:: Instalar dependencias desde requirements.txt si existe
if exist requirements.txt (
    echo Instalando dependencias desde requirements.txt...
    pip install --no-cache-dir -r requirements.txt
) else (
    echo No se encontró requirements.txt, omitiendo instalación de dependencias.
)

echo.
echo Entorno virtual configurado y actualizado exitosamente.
echo Para activarlo en el futuro, usa: call %VENV_DIR%\Scripts\activate
pause
