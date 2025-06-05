import os
import traceback
import openai
import tiktoken
import functools
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pathlib import Path
from typing import Union, Tuple, Dict, List, Any, Optional

try:
    from openai import error as openai_error_v0
    AuthenticationError_v0 = openai_error_v0.AuthenticationError
    InvalidRequestError_v0 = openai_error_v0.InvalidRequestError
    APIConnectionError_v0 = openai_error_v0.APIConnectionError
    RateLimitError_v0 = openai_error_v0.RateLimitError
    APIError_v0 = openai_error_v0.APIError
    ServiceUnavailableError_v0 = openai_error_v0.ServiceUnavailableError
    print("[api.py] OpenAI v0.x errors imported.")
    OPENAI_V0_ERROR_IMPORTED = True
except (ImportError, AttributeError):
    class AuthenticationError_v0(Exception): pass
    class InvalidRequestError_v0(Exception): pass
    class APIConnectionError_v0(Exception): pass
    class RateLimitError_v0(Exception): pass
    class APIError_v0(Exception): pass
    class ServiceUnavailableError_v0(Exception): pass
    print("[api.py] Warn: Failed to import OpenAI v0.x specific errors. Using generic classes.")
    OPENAI_V0_ERROR_IMPORTED = False

load_dotenv(dotenv_path="./api.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FINE_TUNED_MODEL_NAME = os.getenv("FINE_TUNED_MODEL_NAME")
SECONDARY_FINE_TUNED_MODEL_NAME = os.getenv("2ND_FINE_TUNED_MODEL_NAME")
API_SERVER_KEY = os.getenv("API_SERVER_KEY")
if not API_SERVER_KEY:
    print("CRITICAL ERROR [api.py]: API_SERVER_KEY not found in api.env. Protected endpoints will not work.")
else:
    print(f"[api.py] API_SERVER_KEY loaded ('{API_SERVER_KEY[:2]}...').")

if not OPENAI_API_KEY:
    print("CRITICAL ERROR [api.py]: OPENAI_API_KEY not found in api.env")
else:
    try:
        openai.api_key = OPENAI_API_KEY
        print(f"[api.py] OpenAI API Key: '{OPENAI_API_KEY[:2]}...'")
    except Exception as e:
        print(f"CRITICAL ERROR [api.py]: Error setting global OpenAI API key: {e}")

# SYSTEM_MESSAGE_PRIMARY = (
#     "Eres un modelo especializado en generar código C# para simulaciones de Unity. Considera que los tiempos son en segundos; además, los colores en Unity se expresan en valores RGB divididos en 255. Debes contestar tal cual como se te fue entrenado, sin agregar nada más de lo que se espera en C#. No puedes responder en ningún otro lenguaje de programación ni añadir comentarios o palabras innecesarias. Solo puedes responder a consultas relacionadas con simulaciones en Unity sobre Bacilos, Cocos o Helicoides, o cualquier combinación de hasta 4 organismos que pertenezcan a estas morfologías. Para cada organismo, se deben indicar: - El color de la(s) célula(s). - El tiempo de duplicación. - El porcentaje de crecimiento para separarse del padre (solo para Bacilos y Cocos). Tu respuesta debe incluir estrictamente estos scripts en el orden especificado: 1.PrefabMaterialCreator.cs, 2.CreatePrefabsOnClick.cs. Luego, para cada organismo solicitado (hasta 4), se listará su [NombreOrganismo]Component.cs en el orden en que fue mencionado en la solicitud original. Finalmente, para cada organismo solicitado (hasta 4), se listará su [NombreOrganismo]System.cs en el mismo orden que sus componentes. Cualquier pregunta que no cumpla con las características anteriores (ej. no especifica morfología, supera el límite de 4 organismos, incluye fenómenos no biológicos) será respondida con: \"ERROR FORMATO DE PREGUNTA.\". Siempre asegurate que en tu respuesta esten el siguiente formato los primeros dos scripts seguidos de los scripts component y system de los organismos \"1.PrefabMaterialCreator.cs{...}2.CreatePrefabsOnClick.cs{...}3.[NombreOrganismo]Component.cs{...}4.[NombreOrganismo]System.cs{...}5.[NombreOrganismo2]Component.cs{...}6.[NombreOrganismo2]System.cs{...}\" etc. Donde [NombreOrganismo] será reemplazado por el nombre específico del organismo indicado en la solicitud (ej. BaciloRojoComponent.cs. Considera que dentro de CreatePrefabsOnClick.cs siempre debes entregar 2 funciones completas (private void CreateSingleEntity y private void AddPhysicsComponents) sin importar el tipo, cantidad y comportamiento de los organismos. Considera también que para todos los organismos que pertenezcan a la misma morfología (es decir, todos los Bacilos entre sí, todos los Cocos entre sí, y todos los Helicoides entre sí):-Sus scripts [NombreOrganismo]Component.cs deben compartir exactamente la misma estructura de clase y los mismos campos (variables) públicos. Solo los valores asignados a estos campos, derivados de la solicitud del usuario (como color o tiempo de duplicación específico), podrán variar entre instancias de la misma morfología.-Sus scripts [NombreOrganismo]System.cs deben implementar la misma lógica de comportamiento fundamental y la misma estructura de métodos principales. Las diferencias en el comportamiento específico deben surgir del uso de los datos del Component correspondiente y no de una lógica de sistema radicalmente diferente para organismos de la misma morfología."
# )
SYSTEM_MESSAGE_PRIMARY = (
    "Eres un modelo especializado en generar código C# para simulaciones de Unity. "
    "Tu propósito es facilitar la creación de simulaciones biológicas de microorganismos utilizando el framework DOTS (Data-Oriented Technology Stack) de Unity, "
    "específicamente Unity.Entities, Unity.Mathematics y Unity.Physics.\n\n"
    "**Principios Generales de Generación de Código:**\n\n"
    "1.  **Lenguaje y Plataforma:** Generarás exclusivamente código C# compatible con Unity DOTS.\n"
    "2.  **Unidades y Formato:**\n"
    "    * Todos los valores de **tiempo** proporcionados en minutos en la consulta del usuario deben ser convertidos a **segundos** en el código C# (multiplicar por 60.0f).\n"
    "    * Los **colores** se definen en Unity mediante `new Color(R/255.0f, G/255.0f, B/255.0f, 1.0f)`. El canal Alfa (A) será siempre 1.0f (opaco).\n"
    "3.  **Respuesta Estricta:**\n"
    "    * Debes responder **exactamente** como se te ha entrenado, sin añadir ninguna funcionalidad, comentario C# (`//` o `/* */`), explicación o palabra innecesaria que no sea parte del código C# solicitado. Los mensajes de `Debug.LogWarning` o `Debug.LogError` sí son permitidos si son parte de la lógica estándar de las plantillas base.\n"
    "    * No puedes responder en ningún otro lenguaje de programación.\n\n"
    "**Alcance de las Consultas:**\n\n"
    "1.  Solo puedes responder a consultas relacionadas con la simulación de hasta un máximo de **4 organismos** en total.\n"
    "2.  Cada organismo debe pertenecer a una de las siguientes morfologías: **Bacilos** (forma de bastón), **Cocos** (forma esférica) o **Helicoides** (forma espiral).\n"
    "    * Si un organismo es un Coco que forma cadenas (ej. Streptococcus), se considera dentro de la categoría **Coco** para la estructura de su Componente y Sistema. Su comportamiento de encadenamiento se reflejará en la lógica del sistema.\n"
    "3.  Para cada organismo, la consulta del usuario debe indicar:\n"
    "    * El **nombre del organismo** (puede incluir guiones bajos o números, ej. `E.Coli_1`, `S_Cerevisiae2`). Este nombre se usará para `prefabName`.\n"
    "    * La **morfología explícita** (ej. \"forma de bacilo\", \"forma de coco\", \"forma de helicoide\").\n"
    "    * El **color** de la(s) célula(s).\n"
    "    * El **tiempo de duplicación** en minutos.\n"
    "    * **Solo para Bacilos y Cocos:** El **porcentaje de crecimiento** (0-100%) que el hijo debe alcanzar para separarse del padre (se traduce a un flotante 0.0-1.0 en el código). Los organismos Helicoidales no usan este parámetro para la separación, ya que tienen un mecanismo diferente.\n\n"
    "**Estructura y Orden de Scripts en la Respuesta:**\n"
    "Tu respuesta debe incluir estrictamente los siguientes scripts, concatenados sin texto intermedio, en el orden especificado. El formato es `[Número].[NombreScript].cs{[código C# para este script]}`.\n\n"
    "1.  `PrefabMaterialCreator.cs`\n"
    "2.  `CreatePrefabsOnClick.cs`\n"
    "A continuación, para cada **tipo morfológico único** (Bacilo, Coco, Helicoide) identificado en la solicitud del usuario, se listarán su par de scripts Componente y Sistema. Estos pares se ordenarán según el orden en que el *primer organismo de cada tipo morfológico único* fue mencionado en la solicitud original:\n"
    "3.  `[NombreDelPrimerOrganismoDeTipo1]Component.cs`\n"
    "4.  `[NombreDelPrimerOrganismoDeTipo1]System.cs`\n"
    "5.  `[NombreDelPrimerOrganismoDeTipo2]Component.cs` (si existe un segundo tipo morfológico único)\n"
    "6.  `[NombreDelPrimerOrganismoDeTipo2]System.cs` (si existe un segundo tipo morfológico único)\n"
    "   ... y así sucesivamente hasta cubrir todos los tipos morfológicos únicos presentes en la solicitud (máximo 3 tipos: Bacilo, Coco, Helicoide).\n\n"
    "   **Importante sobre Nombres de Componentes y Sistemas:**\n"
    "   * El nombre de la struct dentro del `Component.cs` (ej. `public struct NombreDelPrimerBaciloComponent`) y el tipo de componente referenciado en el `System.cs` correspondiente (ej. `ref NombreDelPrimerBaciloComponent organism`) y en `CreatePrefabsOnClick.cs` (ej. `new NombreDelPrimerBaciloComponent()`) DEBEN usar el nombre del *primer organismo de esa morfología específica* encontrado en la solicitud. \n"
    "   * Todos los organismos subsiguientes *de la misma morfología* en la misma solicitud usarán este mismo tipo de Componente y serán procesados por este mismo Sistema. No se deben generar scripts de Componente o Sistema con definiciones duplicadas para la misma morfología dentro de una misma respuesta.\n\n"
    "**Detalles del Contenido de los Scripts:**\n\n"
    "**A. `PrefabMaterialCreator.cs`:**\n"
    "   * Contendrá una llamada de función para cada organismo solicitado:\n"
    "       * **Bacilo:** `CPAM_Primitive(\"[NombreOrganismo]\", PrimitiveType.Capsule, new Vector3(0.5f, 1f, 0.5f), new Vector3(90, 0, 0), [IndexOrganismoEnConsulta], new Color(R/255.0f, G/255.0f, B/255.0f, 1f));`\n"
    "       * **Cocco:** `CPAM_Primitive(\"[NombreOrganismo]\", PrimitiveType.Sphere, new Vector3(5f, 5f, 5f), new Vector3(90, 0, 0), [IndexOrganismoEnConsulta], new Color(R/255.0f, G/255.0f, B/255.0f, 1f));` ([IndexOrganismoEnConsulta] es el índice basado en 0 del organismo en la lista original de la consulta).\n"
    "       * **Helicoide:** `float length=10f, helixR=0.5f, tubeR=0.1f, turns=3f; int helixSegments=30, tubeSegments=8; CPAM_Helical(\"[NombreOrganismo]\", length, helixR, tubeR, helixSegments, tubeSegments, turns, new Vector3(90,0,0), new Color(R/255.0f, G/255.0f, B/255.0f, 1f));` (Estos parámetros helicoidales son fijos).\n\n"
    "**B. `CreatePrefabsOnClick.cs`:**\n"
    "   * Debe incluir dos funciones principales: `private void CreateSingleEntity(...)` y `private void AddPhysicsComponents(...)`.\n"
    "   * **`CreateSingleEntity` function:**\n"
    "       * Implementar una cadena `if-else if` para cada `prefabName` (que corresponde a `[NombreOrganismo]` de la consulta).\n"
    "       * Dentro de cada bloque `if (prefabName == \"[NombreOrganismoActual]\")`, añadir el componente de datos específico: `entityManager.AddComponentData(newEntity, new [NombreDelPrimerOrganismoDeEstaMorfologia]Component { ... });`.\n"
    "       * Los campos del componente se inicializarán según la morfología y los datos de la consulta:\n"
    "           * `TimeReference`: Tiempo de duplicación en segundos (ej. `valorEnMinutos * 60.0f`).\n"
    "           * `SeparationThreshold` (Bacilos/Cocos): Porcentaje de separación (ej. `porcentaje / 100.0f`).\n"
    "           * `MaxScale`: `1f` para Bacilos, `5f` para Cocos.\n"
    "           * `GrowthTime`: Inicializado a `0f`.\n"
    "           * `GrowthDuration`: Para Bacilos y Cocos, es `TimeReference * SeparationThreshold`. Para Helicoides, es `TimeReference * 0.8f`.\n"
    "           * `TimeSinceLastDivision`: Inicializado a `0f`.\n"
    "           * `DivisionInterval`: Igual a `GrowthDuration`.\n"
    "           * `Parent`: Inicializado a `Entity.Null`.\n"
    "           * `IsInitialCell`: Inicializado a `true`.\n"
    "           * `TimeReferenceInitialized`: Inicializado a `false`.\n"
    "           * `SeparationSign` (Bacilos, Helicoides): Inicializado a `0`.\n"
    "           * `GrowthDirection` (Cocos): Inicializado a `float3.zero`.\n"
    "           * `CurrentAxialLength` (Helicoides): Inicializado a `MaxAxialLength / 2f` (donde `MaxAxialLength` es `10f`).\n"
    "           * `MaxAxialLength` (Helicoides): Fijo a `10f`.\n"
    "           * `ForwardSpeed` (Helicoides): Inicializado a `0f` para células iniciales, `0.3f` para hijas al momento de la división.\n"
    "           * `RandomState` (Helicoides): Inicializado con estado 0, por ejemplo, `default` o `new Unity.Mathematics.Random()` y luego inicializado en el sistema.\n"
    "       * Para **Bacilos**, añadir/actualizar `NonUniformScale`: `if (entityManager.HasComponent<NonUniformScale>(bakedPrefabEntityToInstantiate)) entityManager.SetComponentData(newEntity, new NonUniformScale { Value = new float3(0.5f, 1f, 0.5f) }); else entityManager.AddComponentData(newEntity, new NonUniformScale { Value = new float3(0.5f, 1f, 0.5f) });`\n"
    "       * Al final, llamar a `AddPhysicsComponents(newEntity, prefabName, originalPrefabScale);`.\n"
    "   * **`AddPhysicsComponents` function:**\n"
    "       * Un `switch (prefabName)` para cada `[NombreOrganismo]`.\n"
    "       * **Bacilo:** `colliderAsset = Unity.Physics.CapsuleCollider.Create(new CapsuleGeometry { Vertex0 = new float3(0, -originalPrefabScale * 0.5f, 0), Vertex1 = new float3(0, originalPrefabScale * 0.5f, 0), Radius = originalPrefabScale * 0.25f }, CollisionFilter.Default, physicsMat);` (Nota: `originalPrefabScale` aquí se refiere a la dimensión Y del `LocalTransform` si es relevante, o a un factor de escala global. Usar `scale` como en el .jsonl original para consistencia: `Vertex0 = new float3(0, -scale * 0.5f, 0), Vertex1 = new float3(0, scale * 0.5f, 0), Radius = scale * 0.25f`).\n"
    "       * **Cocco:** `colliderAsset = Unity.Physics.SphereCollider.Create(new SphereGeometry { Center = float3.zero, Radius = scale * 0.1f }, CollisionFilter.Default, physicsMat);` (Usar `scale` como en el .jsonl).\n"
    "       * **Helicoide:** Creación de `Unity.Physics.CompoundCollider` con `const float axialLength = 10f; const float helixRadius = 0.5f; const float tubeRadius = 0.1f; const float turns = 3f; const int colliderSegments = 14;`. Si falla, fallback a `CapsuleCollider` con dimensiones protectoras. Asegurar `if(heliColliders.IsCreated) heliColliders.Dispose();`.\n"
    "       * Añadir componentes físicos estándar (`PhysicsCollider`, `PhysicsMass`, `PhysicsVelocity`, `PhysicsGravityFactor`, `PhysicsDamping`) si `colliderAsset.IsCreated`.\n\n"
    "**C. `[NombreDelPrimerOrganismoDeEsteTipo]Component.cs`:**\n"
    "   * El nombre de la struct es `public struct [NombreDelPrimerOrganismoDeEsteTipo]Component : IComponentData`.\n"
    "   * **Campos para BaciloComponent:**\n"
    "       `public float TimeReference, MaxScale, GrowthTime, GrowthDuration, TimeSinceLastDivision, DivisionInterval, SeparationThreshold;`\n"
    "       `public bool HasGeneratedChild, IsInitialCell, TimeReferenceInitialized;`\n"
    "       `public Entity Parent; public int SeparationSign;`\n"
    "   * **Campos para CoccoComponent:**\n"
    "       `public float TimeReference, MaxScale, GrowthTime, GrowthDuration, TimeSinceLastDivision, DivisionInterval, SeparationThreshold;`\n"
    "       `public bool IsInitialCell, TimeReferenceInitialized;`\n"
    "       `public Entity Parent; public float3 GrowthDirection;`\n"
    "   * **Campos para HelicoideComponent:**\n"
    "       `public float CurrentAxialLength, MaxAxialLength, GrowthTime, GrowthDuration, TimeSinceLastDivision, DivisionInterval, TimeReference, ForwardSpeed;`\n"
    "       `public bool IsInitialCell, TimeReferenceInitialized;`\n"
    "       `public Entity Parent; public int SeparationSign; public Unity.Mathematics.Random RandomState;`\n\n"
    "**D. `[NombreDelPrimerOrganismoDeEsteTipo]System.cs`:**\n"
    "   * La clase hereda de `SystemBase`.\n"
    "   * El núcleo es `Entities.WithReadOnly(parentMap).ForEach((Entity entity, int entityInQueryIndex, ref LocalTransform transform, ref [NombreDelPrimerOrganismoDeEsteTipo]Component organism) => { ... }).ScheduleParallel(Dependency);`.\n"
    "   * La lógica interna es fija para cada morfología (Bacilo, Coco, Helicoide), incluyendo inicialización de `TimeReference` con variabilidad (multiplicador 0.9-1.1), crecimiento, división, interacción padre-hijo, y separación. Los Helicoides tienen lógica de movimiento y división más compleja, usando `organism.RandomState` para decisiones y variaciones.\n"
    "   * Para la inicialización del tiempo (`TimeReferenceInitialized`) en Bacilos/Cocos, usar `Unity.Mathematics.Random rng = new Unity.Mathematics.Random((uint)(entityInQueryIndex + 1) * 99999);`.\n"
    "   * Para la división en Bacilos, usar `Unity.Mathematics.Random rng_div=new Unity.Mathematics.Random((uint)(entityInQueryIndex+1)*12345); int s = rng_div.NextFloat() < 0.5f ? 1 : -1;` (asegurarse que `rng_div` se use, o un nombre único para la variable random dentro de la lógica de división).\n"
    "   * Para Helicoides, la semilla de `RandomState` se inicializa si `organism.RandomState.state == 0`: `uint seed = (uint)(entity.Index ^ (entity.Version << 16) ^ entityInQueryIndex) + (uint)(elapsedTimeForSeed * 1000.0f) + 1; organism.RandomState = new Unity.Mathematics.Random(seed == 0 ? 1u : seed);`. Similarmente para las hijas: `uint childSeed = (uint)(entity.Index ^ entity.Version ^ entityInQueryIndex ^ organism.RandomState.NextUInt()) + (uint)(elapsedTimeForSeed * 1000.0f) + 2; cd.RandomState = new Unity.Mathematics.Random(childSeed == 0 ? 1u : childSeed);`.\n\n"
    "**Manejo de Errores:**\n"
    "Cualquier pregunta que no cumpla con las características anteriores (ej. no especifica morfología para cada organismo, supera el límite de 4 organismos en total, incluye fenómenos no biológicos, o solicita parámetros no contemplados como diferentes mecanismos de separación para Bacilos/Cocos que no sea por porcentaje de crecimiento) será respondida estrictamente con: `\"ERROR FORMATO DE PREGUNTA.\"`.\n"
)

SYSTEM_MESSAGE_SECONDARY = (
    "Eres un traductor especializado en simulaciones biológicas para Unity. Tu función exclusiva es convertir descripciones en lenguaje natural en especificaciones técnicas estructuradas para organismos basados en su morfología. Requisitos obligatorios: 1. Procesarás de 1 a 4 organismos por solicitud 2. Morfologías permitidas: exclusivamente Bacilo (ej: E. coli, Pseudomonas), Cocco (ej: Estreptococos, S.Cerevisiae) y Helicoide (ej: Spirochaeta) 3. Parámetros requeridos para cada organismo: - Color (en formato nombre o adjetivo+color) - Tiempo de duplicación (en minutos) - Porcentaje de separación padre-hijo (50-95%) Solo para Bacilos y Cocos. Instrucciones estrictas: • Si la solicitud menciona fenómenos no biológicos, o está fuera del contexto de simulaciones celulares: responde exactamente 'ERROR DE CONTENIDO' • Si la solicitud menciona más de 4 organismos distintos: responde exactamente 'ERROR CANTIDAD EXCEDIDA' • Si el organismo solicitado NO especifica una de las tres morfologías aceptadas (Bacilo, Cocco, Helicoide): responde exactamente 'ERROR MORFOLOGIA NO ACEPTADA' • Usa el formato: 'Una [Nombre del Organismo] con forma de [Morfología] de color [color], se duplica cada [X] minutos y el hijo se separa del padre cuando alcanza el [Y]% del crecimiento.' (Para Bacilos y Cocos) o 'Una [Nombre del Organismo] con forma de [Morfología] de color [color] y se duplica cada [X] minutos.' (Para Helicoides) • Para múltiples organismos del mismo tipo o que compartan nombre usa sufijos numéricos (Ej: EColi_1, Spirochaeta_2) • Asigna valores por defecto coherentes cuando el usuario no especifique parámetros. Asegurate que el nombre del organismo sea sin espacios."
)

def count_tokens(text: str, model_name: str = "gpt-4o-mini") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        print(f"Warn: Model '{model_name}' not found in tiktoken. Using 'cl100k_base'.")
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception as e:
        print(f"Err getting encoding for {model_name}: {e}. Using 'cl100k_base'.")
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

CACHE_DIR_NAME = "Responses"
CACHE_FILE_NAME = "Responses.csv"
CACHE_DIR = Path.cwd() / CACHE_DIR_NAME
CACHE_CSV_PATH = CACHE_DIR / CACHE_FILE_NAME
DELIMITER = "%|%"

print(f"[api.py] Server cache path: {CACHE_CSV_PATH}")

def check_last_char_is_newline(filepath: Path) -> bool:
    """Checks if the last character of a file is a newline byte."""
    if not filepath.exists() or filepath.stat().st_size == 0: return True
    try:
        with open(filepath, 'rb') as f:
            f.seek(-1, os.SEEK_END)
            return f.read(1) == b'\n'
    except Exception as e:
        print(f"[Cache] Warn checking last char in {filepath}: {e}")
        return False

def get_next_id(csv_path: Path) -> int:
    """Determines the next available ID for a new record in the CSV file."""
    try: csv_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e: print(f"[Cache] Error creating directory for CSV: {e}"); raise
    if not csv_path.exists() or csv_path.stat().st_size == 0: return 1
    last_id = 0
    try:
        with open(csv_path, "r", encoding="utf-8") as f: lines = f.readlines()
        if len(lines) <= 1: return 1
        for line in reversed(lines[1:]):
            line = line.strip();
            if not line: continue
            try:
                parts = line.split(DELIMITER)
                if parts:
                    id_str = parts[0].strip()
                    if id_str and id_str.isdigit():
                        last_id = int(id_str); return last_id + 1
            except (IndexError, ValueError): continue
        print(f"[Cache] Warn: No valid ID found in {csv_path}. Starting from 1.")
        return 1
    except FileNotFoundError: return 1
    except Exception as e: print(f"[Cache] Error reading ID from {csv_path}: {e}. Using ID=1."); return 1

def write_response_to_csv(pregunta: str, respuesta: str, input_tokens: int, output_tokens: int) -> None:
    """Writes a question, its response, and token count to the cache CSV file."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        file_exists = CACHE_CSV_PATH.exists()
        is_empty = file_exists and CACHE_CSV_PATH.stat().st_size == 0
        write_header = not file_exists or is_empty
        next_id = get_next_id(CACHE_CSV_PATH)
        needs_leading_newline = file_exists and not is_empty and not check_last_char_is_newline(CACHE_CSV_PATH)

        with open(CACHE_CSV_PATH, "a", encoding="utf-8", newline='') as f:
            if needs_leading_newline: f.write('\n')
            if write_header:
                header = f"id{DELIMITER}question{DELIMITER}response{DELIMITER}input_tokens{DELIMITER}output_tokens\n"
                f.write(header)
            clean_q = str(pregunta).replace(DELIMITER, "<DELIM>").replace('\n', '\\n').replace('\r', '')
            clean_r = str(respuesta).replace(DELIMITER, "<DELIM>").replace('\n', '\\n').replace('\r', '')
            line = f"{next_id}{DELIMITER}{clean_q}{DELIMITER}{clean_r}{DELIMITER}{input_tokens}{DELIMITER}{output_tokens}\n"
            f.write(line)
        print(f"[Cache] Response saved: {CACHE_CSV_PATH.name} (id: {next_id})")
    except IOError as e: print(f"[Cache] I/O error writing to CSV: {e}")
    except Exception as e: print(f"[Cache] Unexpected error writing CSV: {e}\n{traceback.format_exc()}")

def get_cached_response(pregunta: str) -> Union[str, None]:
    """Searches for a cached response for a given question in the CSV file."""
    if not CACHE_CSV_PATH.is_file(): return None
    try:
        with open(CACHE_CSV_PATH, "r", encoding="utf-8") as f: lines = f.readlines()
        clean_q_search = str(pregunta).replace(DELIMITER, "<DELIM>").replace('\n', '\\n').replace('\r', '')
        for line in reversed(lines[1:]):
            line = line.strip()
            if not line: continue
            parts = line.split(DELIMITER)
            if len(parts) >= 3:
                cached_q = parts[1]; cached_r_raw = parts[2]
                if cached_q == clean_q_search:
                    original_r = cached_r_raw.replace('\\n', '\n').replace("<DELIM>", DELIMITER)
                    print(f"    [Cache HIT Server] '{pregunta[:50]}...'")
                    return original_r
        print(f"    [Cache MISS Server] '{pregunta[:50]}...'")
        return None
    except FileNotFoundError: print(f"[Cache] Warn: Cache file not found: {CACHE_CSV_PATH}"); return None
    except Exception as e: print(f"[Cache] Unexpected error reading cache {CACHE_CSV_PATH}: {e}"); return None

# --- End Cache Logic ---

def _call_openai_api(pregunta: str, model_name: str, system_message: str) -> dict:
    """Directly calls the OpenAI API and handles errors."""
    if not openai.api_key:
        return {"error": "OpenAI API Key not configured on the server.", "status_code": 500}
    if not model_name:
        return {"error": "Model name not configured on the server.", "status_code": 500}

    try:
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": pregunta}
        ]
        input_tokens = count_tokens(system_message, model_name) + count_tokens(pregunta, model_name)
        print(f"[API Call] Model: {model_name}, Input Tokens (calc): {input_tokens}")

        response = openai.ChatCompletion.create(
            model=model_name,
            messages=messages,
            temperature=0,
            timeout=45
        )
        reply = response.choices[0].message["content"].strip()
        output_tokens = count_tokens(reply, model_name)
        total_tokens_api = response.usage['total_tokens']
        print(f"[API Resp] Output Tokens (calc): {output_tokens}, Total Tokens (API): {total_tokens_api}")

        return {
            "reply": reply,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens_api": total_tokens_api,
            "status_code": 200
        }
    except AuthenticationError_v0 as e: print(f"Auth Err: {e}"); return {"error": f"OpenAI Auth Error: {e}", "status_code": 401}
    except InvalidRequestError_v0 as e:
        print(f"Invalid Req Err: {e}")
        error_msg = f"Invalid Request: {e}"
        if "does not exist" in str(e).lower(): error_msg = f"Invalid Request: Model '{model_name}' does not exist or you don't have access."
        return {"error": error_msg, "status_code": 400}
    except APIConnectionError_v0 as e: print(f"API Conn Err: {e}"); return {"error": f"API Conn Error: {e}", "status_code": 503}
    except RateLimitError_v0 as e: print(f"Rate Limit Err: {e}"); return {"error": f"Rate Limit Error: {e}", "status_code": 429}
    except ServiceUnavailableError_v0 as e: print(f"Service Unavail Err: {e}"); return {"error": f"Service Unavail Error: {e}", "status_code": 503}
    except APIError_v0 as e: print(f"API Err (OpenAI): {e}"); return {"error": f"API Error (OpenAI): {e}", "status_code": 500}
    except Exception as e:
        print(f"Unexpected Error in _call_openai_api: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        return {"error": f"Unexpected Server Error: {type(e).__name__}", "status_code": 500}

def _call_openai_api_with_cache(pregunta: str, model_name: str, system_message: str, use_cache: bool) -> dict:
    """Calls the OpenAI API, using cache logic if enabled."""
    if use_cache:
        cached_reply = get_cached_response(pregunta)
        if cached_reply is not None:
            print(f"[Cache] Using cached response for '{pregunta[:50]}...'")
            return {
                "reply": cached_reply, "input_tokens": 0, "output_tokens": 0,
                "total_tokens_api": 0, "status_code": 200, "cached": True
            }

    print(f"[API] No cache or miss. Calling OpenAI for '{pregunta[:50]}...'")
    api_result = _call_openai_api(pregunta, model_name, system_message)

    if use_cache and api_result.get("status_code") == 200 and "reply" in api_result:
        print(f"[Cache] Saving response to cache for '{pregunta[:50]}...'")
        write_response_to_csv(
            pregunta, api_result["reply"],
            api_result.get("input_tokens", 0), api_result.get("output_tokens", 0)
        )

    if api_result.get("status_code") == 200:
        api_result["cached"] = False

    return api_result

app = Flask(__name__)

def require_api_key(f):
    """Decorator to require an API key in the request headers."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        provided_key = request.headers.get('X-API-Key')

        if not API_SERVER_KEY:
            print("WARN: Attempted access without API_SERVER_KEY configured.")
            return jsonify({"error": "Authentication not configured on the server."}), 500

        if provided_key and provided_key == API_SERVER_KEY:
            return f(*args, **kwargs)
        else:
            print(f"WARN: Access denied. Provided key: '{provided_key[:5] if provided_key else 'None'}...'")
            return jsonify({"error": "Access denied. Invalid or missing API Key."}), 403
    return decorated_function

@app.route('/')
def index():
    """Basic endpoint to check if the API server is running."""
    return jsonify({"message": "Unity Sim API Server OK (with cache and auth)."})


@app.route('/verify_config', methods=['GET'])
@require_api_key
def verify_config():
    """Verifies the OpenAI API Key and model configuration."""
    results = {}
    key_ok = False; prim_ok = False; sec_ok = False
    results['api_server_key_status'] = "✅ API Server Key: Configured." if API_SERVER_KEY else "❌ API Server Key: NOT CONFIGURED in api.env!"

    if not OPENAI_API_KEY:
        results['openai_api_key_status'] = "❌ OpenAI API Key: Not configured in api.env."
    else:
        try:
            openai.Model.list(limit=1)
            results['openai_api_key_status'] = "✅ OpenAI API Key: Connection successful (v0.x)."
            key_ok = True
        except AuthenticationError_v0: results['openai_api_key_status'] = "❌ OpenAI API Key: Invalid or expired."
        except APIConnectionError_v0: results['openai_api_key_status'] = "❌ OpenAI API Key: OpenAI connection failed."
        except Exception as e: results['openai_api_key_status'] = f"❌ OpenAI API Key: Unexpected error ({type(e).__name__})."

    if key_ok:
        # Primary Model
        if not FINE_TUNED_MODEL_NAME:
            results['primary_model_status'] = "⚠️ Primary Model: Not configured in api.env."; prim_ok = False
        else:
            try:
                openai.Model.retrieve(FINE_TUNED_MODEL_NAME)
                results['primary_model_status'] = f"✅ Primary Model: '{FINE_TUNED_MODEL_NAME}' verified."; prim_ok = True
            except InvalidRequestError_v0: results['primary_model_status'] = f"❌ Primary Model: '{FINE_TUNED_MODEL_NAME}' NOT FOUND."; prim_ok = False
            except Exception as e: results['primary_model_status'] = f"❌ Primary Model: Error verifying '{FINE_TUNED_MODEL_NAME}' ({type(e).__name__})."; prim_ok = False
        # Secondary Model
        if not SECONDARY_FINE_TUNED_MODEL_NAME:
            results['secondary_model_status'] = "⚠️ Secondary Model: Not configured in api.env."; sec_ok = False
        else:
            try:
                openai.Model.retrieve(SECONDARY_FINE_TUNED_MODEL_NAME)
                results['secondary_model_status'] = f"✅ Secondary Model: '{SECONDARY_FINE_TUNED_MODEL_NAME}' verified."; sec_ok = True
            except InvalidRequestError_v0: results['secondary_model_status'] = f"❌ Secondary Model: '{SECONDARY_FINE_TUNED_MODEL_NAME}' NOT FOUND."; sec_ok = False
            except Exception as e: results['secondary_model_status'] = f"❌ Secondary Model: Error verifying '{SECONDARY_FINE_TUNED_MODEL_NAME}' ({type(e).__name__})."; sec_ok = False
    else:
        results['primary_model_status'] = " N/A (Requires valid OpenAI Key)"; prim_ok = False
        results['secondary_model_status'] = " N/A (Requires valid OpenAI Key)"; sec_ok = False

    all_config_ok = key_ok and prim_ok and sec_ok

    return jsonify({
        "verification_details": results,
        "openai_api_key_ok": key_ok,
        "primary_model_ok": prim_ok,
        "secondary_model_ok": sec_ok,
        "all_config_ok": all_config_ok
        }), 200

@app.route('/call_primary', methods=['POST'])
@require_api_key
def handle_call_primary():
    """Protected endpoint to call the primary model."""
    data = request.get_json()
    if not data or 'pregunta' not in data:
        return jsonify({"error": "Missing 'pregunta' in JSON."}), 400

    pregunta = data['pregunta']
    use_cache = data.get('use_cache', True)

    print(f"[API REQ] /call_primary: '{pregunta[:500]}...' (cache={use_cache})")

    if not FINE_TUNED_MODEL_NAME:
        return jsonify({"error": "Primary model not configured in api.env"}), 500

    result = _call_openai_api_with_cache(
        pregunta, FINE_TUNED_MODEL_NAME, SYSTEM_MESSAGE_PRIMARY, use_cache
    )
    return jsonify(result), result.get("status_code", 500)


@app.route('/call_secondary', methods=['POST'])
@require_api_key
def handle_call_secondary():
    """Protected endpoint to call the secondary model."""
    data = request.get_json()
    if not data or 'pregunta' not in data:
        return jsonify({"error": "Missing 'pregunta' in JSON."}), 400

    pregunta = data['pregunta']
    use_cache = data.get('use_cache', True)

    print(f"[API REQ] /call_secondary: '{pregunta[:100]}...' (cache={use_cache})")

    if not SECONDARY_FINE_TUNED_MODEL_NAME:
        return jsonify({"error": "Secondary model not configured in api.env"}), 500

    result = _call_openai_api_with_cache(
        pregunta, SECONDARY_FINE_TUNED_MODEL_NAME, SYSTEM_MESSAGE_SECONDARY, use_cache
    )
    print(f"[API RESP] /call_secondary: '{result.get('reply', '')[:100]}...' (status: {result.get('status_code', 500)})")
    return jsonify(result), result.get("status_code", 500)


if __name__ == '__main__':
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[api.py] Cache directory OK: {CACHE_DIR}")
    except Exception as e:
        print(f"[api.py] CRITICAL ERR: Failed to create cache directory {CACHE_DIR}: {e}")

    print(f"--- Starting API Server (with Auth and Cache) at port: {port} ---")
    print(f"    API Server Key: {'Configured' if API_SERVER_KEY else 'NOT CONFIGURED!! (Protected endpoints will fail)'}")
    print(f"    OpenAI API Key: {'Configured' if OPENAI_API_KEY else 'NOT CONFIGURED!!'}")
    print(f"    Primary Model: {FINE_TUNED_MODEL_NAME or 'Not configured'}")
    print(f"    Secondary Model: {SECONDARY_FINE_TUNED_MODEL_NAME or 'Not configured'}")
    print(f"    Cache file path: {CACHE_CSV_PATH}")
    print("----------------------------------------------------------")

    app.run(host='0.0.0.0', port=port, debug=True)