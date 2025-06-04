# Instalar Unity editor version 6000.0.32f1 con Windows Build Support: unityhub://6000.0.32f1/b2e806cf271c

# DEV Windows:
- Ejecutar ./setup_env.bat para instalar todas las dependencias
- Luego activar entorno virtual venv/Scripts/activate 
- Build app:
    **Dentro de app/**
    - pyinstaller --onefile --windowed --name SimulationManager --icon="img/icon.ico" main.py
    - Luego mover '.env' 'img' 'Responses' 'Simulations' y 'Template' a la carpeta /dist que dentro tiene SimulationManager.exe
# DEV MacOS:
- chmod +x setup_env.sh
- Ejecutar ./setup_env.sh para instalar todas las dependencias
- Luego activar entorno virtual venv/Scripts/activate 
- Build app MacOS:
    **Dentro de app/** 
    - pip3 install pyinstaller
    - pyinstaller --onefile --windowed --name SimulationManager --icon="img/icon.icns" main.py