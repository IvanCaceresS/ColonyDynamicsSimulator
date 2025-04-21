# Instalar Unity editor version 6000.0.32f1 con Windows Build Support: unityhub://6000.0.32f1/b2e806cf271c

# DEV:
- Ejecutar ./setup_env.bat para instalar todas las dependencias
- Luego activar entorno virtual venv/Scripts/activateEjecutar main.py
- Build app:
    - pyinstaller --onefile --windowed --name SimulationManager --icon="img/icono.ico" --add-data "C:\Codes\UnityProjects\SimulationManager\venv\lib\site-packages\tiktoken_ext;tiktoken_ext" --hidden-import "tiktoken.load" main.py
    - Luego mover '.env' 'img' 'Responses' 'Simulations' y 'Template' a la carpeta /dist que dentro tiene SimulationManager.exe