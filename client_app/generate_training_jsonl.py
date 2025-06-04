import os

def extraer_contenido_archivo1(ruta_archivo):
    """
    Extrae contenido del primer archivo:
    - Después de la línea 14.
    - Antes de la línea que contiene "AssetDatabase.SaveAssets();".
    """
    contenido_extraido_lineas = []
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        indice_inicio = 14
        marcador_fin = "AssetDatabase.SaveAssets();"
        
        if len(lineas) > indice_inicio:
            for i in range(indice_inicio, len(lineas)):
                linea_actual = lineas[i]
                if marcador_fin in linea_actual:
                    break
                contenido_extraido_lineas.append(linea_actual.strip())
        
        return " ".join(contenido_extraido_lineas).strip()

    except FileNotFoundError:
        print(f"Error: Archivo no encontrado - {ruta_archivo}")
        return ""
    except Exception as e:
        print(f"Error al procesar {ruta_archivo}: {e}")
        return ""

def extraer_contenido_archivo2(ruta_archivo):
    """
    Extrae contenido del segundo archivo:
    - Después de "CreateSingleEntity(sourcePrefabGO.name, bakedPrefabEntity, spawnPos, randomRotation, originalScale);}}".
    - Antes de "private void OnAllPrefabsPlaced()".
    """
    contenido_extraido_lineas = []
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        marcador_inicio = "CreateSingleEntity(sourcePrefabGO.name, bakedPrefabEntity, spawnPos, randomRotation, originalScale);}}"
        marcador_fin = "private void OnAllPrefabsPlaced()"
        capturando = False
        for linea_actual in lineas:
            if capturando:
                if marcador_fin in linea_actual:
                    break
                contenido_extraido_lineas.append(linea_actual.strip())
            
            if marcador_inicio in linea_actual:
                capturando = True
        
        return " ".join(contenido_extraido_lineas).strip()

    except FileNotFoundError:
        print(f"Error: Archivo no encontrado - {ruta_archivo}")
        return ""
    except Exception as e:
        print(f"Error al procesar {ruta_archivo}: {e}")
        return ""

def extraer_contenido_systems_especifico(ruta_archivo):
    """
    Extrae contenido específico para archivos del directorio Systems:
    - Después de la línea que contiene "var ecb = ecbSystem.CreateCommandBuffer().AsParallelWriter();".
    - Antes de la línea que contiene "ecbSystem.AddJobHandleForProducer(Dependency);".
    """
    contenido_extraido_lineas = []
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        marcador_inicio = "var ecb = ecbSystem.CreateCommandBuffer().AsParallelWriter();"
        marcador_fin = "ecbSystem.AddJobHandleForProducer(Dependency);"
        capturando = False

        for linea_actual in lineas:
            if capturando:
                if marcador_fin in linea_actual:
                    break # Detenerse ANTES de esta línea
                contenido_extraido_lineas.append(linea_actual.strip())
            
            # Si encontramos el marcador de inicio, empezamos a capturar la *siguiente* línea
            if marcador_inicio in linea_actual:
                capturando = True
        
        return " ".join(contenido_extraido_lineas).strip()

    except FileNotFoundError:
        print(f"Error: Archivo no encontrado - {ruta_archivo}")
        return ""
    except Exception as e:
        print(f"Error al procesar {ruta_archivo} para Systems: {e}")
        return ""

def procesar_directorio_generico(directorio_path, contador_inicial, funcion_extraccion_contenido, nombre_tipo_directorio=""):
    """
    Procesa todos los archivos .cs en el directorio_path dado usando una función de extracción específica.
    Devuelve una lista de strings formateados y el siguiente número de contador.
    """
    contenidos_formateados = []
    contador_actual = contador_inicial
    
    if not os.path.isdir(directorio_path):
        print(f"Error: Directorio no encontrado - {directorio_path}")
        return [], contador_actual

    try:
        archivos_cs = sorted([f for f in os.listdir(directorio_path) if f.endswith(".cs") and os.path.isfile(os.path.join(directorio_path, f))])
        for nombre_archivo in archivos_cs:
            ruta_completa_archivo = os.path.join(directorio_path, nombre_archivo)
            contenido_una_linea = funcion_extraccion_contenido(ruta_completa_archivo)
            
            if contenido_una_linea or contenido_una_linea == "": # Incluir aunque el contenido extraído sea vacío, como '{ }'
                formato_item = f"{contador_actual}.{nombre_archivo}{{{contenido_una_linea}}}"
                contenidos_formateados.append(formato_item)
                contador_actual += 1
            else:
                print(f"Advertencia: No se extrajo contenido de {ruta_completa_archivo} para {nombre_tipo_directorio} o hubo un error.")

        return contenidos_formateados, contador_actual
    except Exception as e:
        print(f"Error al listar o procesar archivos en {directorio_path}: {e}")
        return [], contador_actual

def extraer_todo_el_contenido(ruta_archivo):
    """
    Extrae todo el contenido de un archivo y lo devuelve en una sola línea.
    """
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            contenido_bruto = f.read()
        lineas_contenido = contenido_bruto.splitlines()
        contenido_una_linea = " ".join(linea.strip() for linea in lineas_contenido if linea.strip()).strip()
        return contenido_una_linea
    except FileNotFoundError:
        print(f"Error: Archivo no encontrado - {ruta_archivo}")
        return None # Devuelve None para indicar error o archivo no encontrado
    except Exception as e:
        print(f"Error al leer todo el contenido de {ruta_archivo}: {e}")
        return None


def main():
    # --- Configuración de Rutas ---
    # Asegúrate de que estas rutas sean correctas para tu sistema.
    # El r"" al principio (raw string) ayuda a manejar las barras invertidas en Windows.
    base_path = r"C:\Users\Ivaaan\Downloads\SimulationTest\Assets"
    
    ruta_archivo1 = os.path.join(base_path, r"Editor\PrefabMaterialCreator.cs")
    ruta_archivo2 = os.path.join(base_path, r"Scripts\General\CreatePrefabsOnClick.cs")
    ruta_directorio_componentes = os.path.join(base_path, r"Scripts\Components")
    ruta_directorio_systems = os.path.join(base_path, r"Scripts\Systems")
    
    ruta_salida_txt = "output.txt"

    todos_los_segmentos = []
    contador_actual = 1

    # 1. Procesar PrefabMaterialCreator.cs
    contenido1 = extraer_contenido_archivo1(ruta_archivo1)
    if contenido1 is not None: # Se procesó, incluso si el contenido es vacío.
        todos_los_segmentos.append(f"{contador_actual}.PrefabMaterialCreator.cs{{{contenido1}}}")
        contador_actual += 1

    # 2. Procesar CreatePrefabsOnClick.cs
    contenido2 = extraer_contenido_archivo2(ruta_archivo2)
    if contenido2 is not None: # Se procesó, incluso si el contenido es vacío.
        todos_los_segmentos.append(f"{contador_actual}.CreatePrefabsOnClick.cs{{{contenido2}}}")
        contador_actual += 1
    
    # 3. Procesar archivos en Components (todo el contenido)
    print(f"\nProcesando directorio Components: {ruta_directorio_componentes}")
    contenidos_componentes, contador_actual = procesar_directorio_generico(
        ruta_directorio_componentes, 
        contador_actual, 
        extraer_todo_el_contenido,
        nombre_tipo_directorio="Components"
    )
    todos_los_segmentos.extend(contenidos_componentes)

    # 4. Procesar archivos en Systems (contenido específico)
    print(f"\nProcesando directorio Systems: {ruta_directorio_systems}")
    contenidos_systems, contador_actual = procesar_directorio_generico(
        ruta_directorio_systems,
        contador_actual,
        extraer_contenido_systems_especifico,
        nombre_tipo_directorio="Systems"
    )
    todos_los_segmentos.extend(contenidos_systems)

    # Unir todos los segmentos.
    string_final = "".join(todos_los_segmentos)

    try:
        with open(ruta_salida_txt, 'w', encoding='utf-8') as f_out:
            f_out.write(string_final)
        print(f"\nProceso completado. Resultado guardado en: {os.path.abspath(ruta_salida_txt)}")
        if not string_final:
            print("Advertencia: El string final está vacío. Verifica las rutas y los contenidos de los archivos.")
    except Exception as e:
        print(f"Error al escribir el archivo de salida {ruta_salida_txt}: {e}")

if __name__ == "__main__":
    main()