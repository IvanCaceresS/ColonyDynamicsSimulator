import sys
import os
import traceback
import shutil
import subprocess
import platform
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkinter import ttk
from dotenv import load_dotenv
from pathlib import Path
import psutil
import openai
import math
from PIL import Image, ImageTk
from openai import error as openai_error_v0
import tiktoken
import re
from typing import Union, Tuple, Dict
AuthenticationError_v0 = openai_error_v0.AuthenticationError
InvalidRequestError_v0 = openai_error_v0.InvalidRequestError
APIConnectionError_v0 = openai_error_v0.APIConnectionError
OPENAI_V0_ERROR_IMPORTED = True
OPENAI_V1_CLIENT_EXISTS = False


# ======================================================
# Global State & Config Variables
# ======================================================
unity_path_ok = False
unity_version_ok = False
unity_projects_path_ok = False
apis_key_ok = False
apis_models_ok = False
initial_verification_complete = False
is_build_running = False
UNITY_EXECUTABLE = None
UNITY_PROJECTS_PATH = None
OPENAI_API_KEY = None
FINE_TUNED_MODEL_NAME = None
SECONDARY_FINE_TUNED_MODEL_NAME = None
UNITY_REQUIRED_VERSION_STRING = "6000.0.32f1" # Versión requerida
SIMULATIONS_DIR = "./Simulations"
SIMULATION_PROJECT_NAME = "Simulation"
SIMULATION_PROJECT_PATH = None
ASSETS_FOLDER = None
STREAMING_ASSETS_FOLDER = None
SIMULATION_LOADED_FILE = None
last_simulation_loaded = None
all_simulations_data = []
play_icon_text = "▶"
delete_icon_text = "🗑️"
loaded_indicator_text = "✓"
tooltip_window = None
tooltip_delay = 700
tooltip_job_id = None
logo_photo_ref = None
ICON_PATH = "img/icono.ico"
LOGO_PATHS = ["img/logo_light.png", "img/logo_dark.png"]
LOGO_WIDTH = 200
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
APP_FONT = ("Segoe UI", 11)
APP_FONT_BOLD = ("Segoe UI", 11, "bold")
TITLE_FONT = ("Times New Roman", 22, "bold")
STATUS_FONT = ("Segoe UI", 10)
TREEVIEW_FONT = ("Segoe UI", 10)
TREEVIEW_HEADER_FONT = ("Segoe UI", 10, "bold")
# --- Colores para Botones (Light, Dark) ---
COLOR_SUCCESS_GENERAL = ("#28a745", "#4CAF50")
COLOR_DANGER_GENERAL = ("#C62828", "#EF5350")
COLOR_INFO_GENERAL = ("#218838", "#66BB6A")
COLOR_WARNING_GENERAL = ("#E53935", "#E53935")
COLOR_DISABLED_GENERAL = ("#BDBDBD", "#757575")
COLOR_SIDEBAR_BG = None

def get_color_mode_index():
    return 1 if ctk.get_appearance_mode() == "Dark" else 0

# ======================================================
# INDIVIDUAL BUTTON COLOR DEFINITIONS (FG, HOVER, TEXT)
# ======================================================
_NEUTRAL_FG_COLOR = ("#A0A0A0", "#616161")
_NEUTRAL_HOVER_COLOR = ("#888888", "#757575")
_NEUTRAL_TEXT_COLOR = ("#000000", "#FFFFFF")
BTN_SETTINGS_FG_COLOR = _NEUTRAL_FG_COLOR
BTN_SETTINGS_HOVER_COLOR = _NEUTRAL_HOVER_COLOR
BTN_SETTINGS_TEXT_COLOR = _NEUTRAL_TEXT_COLOR
BTN_VERIFY_FG_COLOR = _NEUTRAL_FG_COLOR
BTN_VERIFY_HOVER_COLOR = _NEUTRAL_HOVER_COLOR
BTN_VERIFY_TEXT_COLOR = _NEUTRAL_TEXT_COLOR
BTN_ABOUT_FG_COLOR = _NEUTRAL_FG_COLOR
BTN_ABOUT_HOVER_COLOR = _NEUTRAL_HOVER_COLOR
BTN_ABOUT_TEXT_COLOR = _NEUTRAL_TEXT_COLOR
BTN_UNITY_DOWN_FG_COLOR = ("#4CAF50", "#4CAF50")
BTN_UNITY_DOWN_HOVER_COLOR = ("#388E3C", "#66BB6A")
BTN_UNITY_DOWN_TEXT_COLOR = ("#FFFFFF", "#FFFFFF")
BTN_EXIT_FG_COLOR = ("#E53935", "#E53935")
BTN_EXIT_HOVER_COLOR = ("#C62828", "#EF5350")
BTN_EXIT_TEXT_COLOR = ("#FFFFFF", "#FFFFFF")
BTN_RELOAD_FG_COLOR = ("#1E88E5", "#1E88E5")
BTN_RELOAD_HOVER_COLOR = ("#1565C0", "#42A5F5")
BTN_RELOAD_TEXT_COLOR = ("#FFFFFF", "#FFFFFF")
BTN_GRAPH_FG_COLOR = ("#673AB7", "#673AB7")
BTN_GRAPH_HOVER_COLOR = ("#512DA8", "#7E57C2")
BTN_GRAPH_TEXT_COLOR = ("#FFFFFF", "#FFFFFF")
BTN_CREATE_FG_COLOR = ("#28a745", "#4CAF50")
BTN_CREATE_HOVER_COLOR = ("#218838", "#66BB6A")
BTN_CREATE_TEXT_COLOR = ("#FFFFFF", "#FFFFFF")
BTN_CLEARSEARCH_FG_COLOR = ("#E53935", "#E53935")
BTN_CLEARSEARCH_HOVER_COLOR = ("#C62828", "#EF5350")
BTN_CLEARSEARCH_TEXT_COLOR = ("#FFFFFF", "#FFFFFF")
# ======================================================
# Start SimulationGraphics
# ======================================================
def SimulationGraphics(simulation_name):
    if not simulation_name:
        print("Error: Se debe proporcionar un nombre de simulación a la función SimulationGraphics.")
        return

    documents_path = Path.home() / "Documents"
    simulation_folder = documents_path / "SimulationLoggerData" / simulation_name

    csv_path = simulation_folder / "SimulationStats.csv"
    output_folder = simulation_folder / "Graficos"
    output_folder.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        print(f"El archivo CSV no existe en: {csv_path}")
        return

    try:
        df = pd.read_csv(csv_path, sep=";", engine="python")
    except Exception as e:
        print(f"Error al leer el archivo CSV ({csv_path}): {e}")
        return

    df.columns = df.columns.str.strip()

    if "Timestamp" not in df.columns:
        print("[Error] La columna 'Timestamp' no se encontró en el CSV.")
        return

    df = df[df["Timestamp"].astype(str).str.strip() != "0"]

    df["Timestamp"] = df["Timestamp"].astype(str).str.replace(r'\s+', ' ', regex=True)

    try:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%d-%m-%Y %H:%M:%S", errors="coerce")
    except Exception as e:
        print(f"Error al convertir la columna Timestamp: {e}")

    initial_rows = len(df)
    df = df.dropna(subset=["Timestamp"])
    if len(df) < initial_rows:
         print(f"Advertencia: Se eliminaron {initial_rows - len(df)} filas debido a formato inválido de Timestamp.")

    if df.empty:
        print("No quedan datos válidos después de procesar el Timestamp.")
        return

    known_columns = { # Usar un set para búsquedas más rápidas
        "Timestamp", "FPS", "RealTime", "SimulatedTime",
        "DeltaTime", "FrameCount", "Pausado", "Organism count"
    }
    organism_columns = [col for col in df.columns if col not in known_columns]

    # --- Gráfico 1: FPS over Time ---
    if "FPS" in df.columns:
        plt.figure(figsize=(12, 6))
        plt.plot(df["Timestamp"], df["FPS"], marker=".", linestyle="-", color="blue") # Cambiado a '.' para menos clutter si hay muchos puntos
        plt.title(f"FPS over Time ({simulation_name})")
        plt.xlabel("Timestamp")
        plt.ylabel("FPS")
        plt.xticks(rotation=45, ha='right') # Mejorar alineación de etiquetas rotadas
        plt.grid(True, linestyle='--', alpha=0.6) # Estilo de grid más sutil
        plt.tight_layout()
        try:
            plt.savefig(str(output_folder / "fps_over_time.png"))
        except Exception as e:
            print(f"Error al guardar fps_over_time.png: {e}")
        plt.close()
    else:
        print("Columna 'FPS' no encontrada, omitiendo gráfico FPS over Time.")


    # --- Gráfico 2: RealTime vs SimulatedTime ---
    if "RealTime" in df.columns and "SimulatedTime" in df.columns:
        plt.figure(figsize=(12, 6))
        plt.plot(df["Timestamp"], df["RealTime"], label="RealTime", marker=".", linestyle="-")
        plt.plot(df["Timestamp"], df["SimulatedTime"], label="SimulatedTime", marker=".", linestyle="-", color="orange")
        plt.title(f"RealTime vs SimulatedTime ({simulation_name})")
        plt.xlabel("Timestamp")
        plt.ylabel("Time (s)")
        plt.xticks(rotation=45, ha='right')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        try:
            plt.savefig(str(output_folder / "time_comparison.png"))
        except Exception as e:
            print(f"Error al guardar time_comparison.png: {e}")
        plt.close()
    else:
         print("Columnas 'RealTime' o 'SimulatedTime' no encontradas, omitiendo gráfico Time Comparison.")

    # --- Gráfico 3: Organism Counts over Time ---
    if organism_columns:
        plt.figure(figsize=(12, 6))
        for col in organism_columns:
            # Verificar que la columna exista y sea numérica antes de graficar
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                plt.plot(df["Timestamp"], df[col], label=col, marker=".", linestyle="-")
            else:
                print(f"Advertencia: Omitiendo columna de organismo no numérica o faltante: '{col}'")
        # Solo añadir elementos de gráfico si se graficó algo
        if plt.gca().has_data():
            plt.title(f"Organism Counts over Time ({simulation_name})")
            plt.xlabel("Timestamp")
            plt.ylabel("Count")
            plt.xticks(rotation=45, ha='right')
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.tight_layout()
            try:
                plt.savefig(str(output_folder / "organism_counts.png"))
            except Exception as e:
                print(f"Error al guardar organism_counts.png: {e}")
        plt.close() # Cerrar siempre la figura
    else:
        print("No se encontraron columnas de organismos específicas, omitiendo gráfico Organism Counts.")

    # --- Gráfico 4: Total Organisms over Time ---
    if "Organism count" in df.columns:
        plt.figure(figsize=(12, 6))
        plt.plot(df["Timestamp"], df["Organism count"], marker=".", linestyle="-", color="purple")
        plt.title(f"Total Organisms over Time ({simulation_name})")
        plt.xlabel("Timestamp")
        plt.ylabel("Total Count")
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        try:
            plt.savefig(str(output_folder / "total_organisms.png"))
        except Exception as e:
            print(f"Error al guardar total_organisms.png: {e}")
        plt.close()
    else:
        print("Columna 'Organism count' no encontrada, omitiendo gráfico Total Organisms.")

    # --- Gráfico 5: Frame Count over Time ---
    if "FrameCount" in df.columns:
        plt.figure(figsize=(12, 6))
        plt.plot(df["Timestamp"], df["FrameCount"], marker=".", linestyle="-", color="darkcyan") # Cambiado color y marcador
        plt.title(f"Frame Count over Time ({simulation_name})")
        plt.xlabel("Timestamp")
        plt.ylabel("Frame Count")
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        try:
            plt.savefig(str(output_folder / "frame_count.png"))
        except Exception as e:
            print(f"Error al guardar frame_count.png: {e}")
        plt.close()
    else:
        print("Columna 'FrameCount' no encontrada, omitiendo gráfico Frame Count.")


    # --- Gráfico 6: FPS Distribution ---
    if "FPS" in df.columns and not df["FPS"].isnull().all(): # Verificar que haya datos de FPS
        plt.figure(figsize=(12, 6))
        plt.hist(df["FPS"].dropna(), bins=20, color="green", edgecolor="black") # dropna por si acaso
        plt.title(f"FPS Distribution ({simulation_name})")
        plt.xlabel("FPS")
        plt.ylabel("Frequency")
        plt.grid(True, axis='y', linestyle='--', alpha=0.6) # Grid solo en eje y para histograma
        plt.tight_layout()
        try:
            plt.savefig(str(output_folder / "fps_histogram.png"))
        except Exception as e:
             print(f"Error al guardar fps_histogram.png: {e}")
        plt.close()
    elif "FPS" in df.columns:
         print("Columna 'FPS' encontrada pero sin datos válidos, omitiendo histograma FPS.")

    # --- Gráfico 7: Average FPS per Total Organisms ---
    if "Organism count" in df.columns and "FPS" in df.columns and not df["Organism count"].isnull().all() and not df["FPS"].isnull().all():
        # Asegurarse de que 'Organism count' sea numérico para agrupar correctamente
        if pd.api.types.is_numeric_dtype(df["Organism count"]):
             # Convertir a int si es posible para tener categorías más limpias
            df_agrupable = df.dropna(subset=["Organism count", "FPS"])
            try:
                 df_agrupable["Organism count"] = df_agrupable["Organism count"].astype(int)
            except ValueError:
                 print("Advertencia: 'Organism count' contiene valores no enteros, agrupando por valores flotantes.")

            # Agrupar y calcular media
            df_grouped = df_agrupable.groupby("Organism count")["FPS"].mean().reset_index()

            if not df_grouped.empty:
                plt.figure(figsize=(12, 6))
                plt.plot(df_grouped["Organism count"], df_grouped["FPS"], marker="o", linestyle="-", color="red")
                plt.title(f"Average FPS per Total Organisms ({simulation_name})")
                plt.xlabel("Total Organisms")
                plt.ylabel("Average FPS")
                plt.grid(True, linestyle='--', alpha=0.6)
                plt.tight_layout()
                try:
                    plt.savefig(str(output_folder / "total_organisms_vs_fps.png"))
                except Exception as e:
                    print(f"Error al guardar total_organisms_vs_fps.png: {e}")
                plt.close()
            else:
                print("No se pudieron agrupar datos para el gráfico Average FPS per Total Organisms.")
        else:
            print("Columna 'Organism count' no es numérica, omitiendo gráfico Average FPS per Total Organisms.")

    # --- Gráfico 8: Organisms per Simulated Time ---
    if "SimulatedTime" in df.columns and organism_columns:
         # Verificar que SimulatedTime sea numérico
         if pd.api.types.is_numeric_dtype(df["SimulatedTime"]):
            plt.figure(figsize=(12, 6))
            plotted_something = False
            for col in organism_columns:
                # Verificar de nuevo cada columna de organismo
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    plt.plot(df["SimulatedTime"], df[col], label=col, marker=".", linestyle="-")
                    plotted_something = True
                # No imprimir advertencia aquí de nuevo, ya se hizo en gráfico 3

            if plotted_something:
                plt.title(f"Organism Count over Simulated Time ({simulation_name})")
                plt.xlabel("Simulated Time (s)")
                plt.ylabel("Organism Count")
                plt.legend()
                plt.grid(True, linestyle='--', alpha=0.6)
                plt.tight_layout()
                try:
                    plt.savefig(str(output_folder / "organisms_vs_simulated_time.png"))
                except Exception as e:
                    print(f"Error al guardar organisms_vs_simulated_time.png: {e}")
            plt.close()
         else:
             print("Columna 'SimulatedTime' no es numérica, omitiendo gráfico Organisms vs Simulated Time.")

    print(f"SimulationGraphics: Los gráficos para '{simulation_name}' se han generado (o intentado generar) y guardado en: {output_folder}")
# ======================================================
# End SimulationGraphics
# ======================================================

# ======================================================
# Start api_manager
# ======================================================
load_dotenv(dotenv_path="./.env")
openai.api_key = os.getenv("OPENAI_API_KEY")
FINE_TUNED_MODEL_NAME = os.getenv("FINE_TUNED_MODEL_NAME")
SECOND_FINE_TUNED_MODEL_NAME = os.getenv("2ND_FINE_TUNED_MODEL_NAME")
print(f"OPENAI_API_KEY: {openai.api_key}")
print(f"FINE_TUNED_MODEL_NAME: {FINE_TUNED_MODEL_NAME}")
print(f"SECOND_FINE_TUNED_MODEL_NAME: {SECOND_FINE_TUNED_MODEL_NAME}")

SYSTEM_MESSAGE_PRIMARY = (
    "Eres un modelo especializado en generar código C# para simulaciones de Unity. Considera que los tiempos son en segundos; además, los colores en Unity se expresan en valores RGB divididos en 255. Debes contestar tal cual como se te fue entrenado, sin agregar nada más de lo que se espera en C#. No puedes responder en ningún otro lenguaje de programación ni añadir comentarios o palabras innecesarias. Solo puedes responder a consultas relacionadas con simulaciones en Unity sobre EColi, SCerevisiae o ambas, donde se indiquen: - El color de la(s) célula(s). - El tiempo de duplicación en minutos. - El porcentaje de crecimiento para separarse del padre. Tu respuesta debe incluir estrictamente estos scripts en el orden especificado: - Si se piden ambas (EColi y SCerevisiae): 1.PrefabMaterialCreator.cs, 2.CreatePrefabsOnClick.cs, 3.EColiComponent.cs, 4.SCerevisiaeComponent.cs, 5.EColiSystem.cs, 6.SCerevisiaeSystem.cs. - Si se pide solo EColi: 1.PrefabMaterialCreator.cs, 2.CreatePrefabsOnClick.cs, 3.EColiComponent.cs, 4.EColiSystem.cs. - Si se pide solo SCerevisiae: 1.PrefabMaterialCreator.cs, 2.CreatePrefabsOnClick.cs, 3.SCerevisiaeComponent.cs, 4.SCerevisiaeSystem.cs - Si se pide 2 EColi: 1.PrefabMaterialCreator.cs, 2.CreatePrefabsOnClick.cs, 3.EColi_1Component.cs, 4.EColi_2Component.cs, 5.EColi_1System.cs, 6.EColi_2System.cs. - Si se pide 2 SCerevisiae: 1.PrefabMaterialCreator.cs, 2.CreatePrefabsOnClick.cs, 3.SCerevisiae_1Component.cs, 4.SCerevisiae_2Component.cs, 5.SCerevisiae_1System.cs, 6.SCerevisiae_2System.cs. El formato de cada script debe ser \"1.PrefabMaterialCreator.cs{...}2.CreatePrefabsOnClick.cs{...}\" etc. Cualquier pregunta que no cumpla con las características anteriores será respondida con: \"ERROR FORMATO DE PREGUNTA.\"."
)
SYSTEM_MESSAGE_SECONDARY = (
    "Eres un traductor especializado en simulaciones biológicas para Unity. Tu función exclusiva es convertir descripciones en lenguaje natural en especificaciones técnicas estructuradas para EColi y SCerevisiae. Requisitos obligatorios: 1. Solo procesarás 1 o 2 organismos por solicitud 2. Organismos permitidos: exclusivamente EColi (bacteria) y SCerevisiae (levadura) 3. Parámetros requeridos para cada organismo: - Color (en formato nombre o adjetivo+color) - Tiempo de duplicación (en minutos) - Porcentaje de separación padre-hijo (50-95%) Instrucciones estrictas: • Si la solicitud menciona otros organismos, fenómenos no biológicos, o está fuera del contexto de simulaciones celulares: responde exactamente 'ERROR DE CONTENIDO' • Usa el formato: '[Cantidad] [Organismo]. El [Organismo] debe ser de color [color], duplicarse cada [X] minutos y el hijo se separa del padre cuando alcanza el [Y]% del crecimiento.' • Para múltiples organismos del mismo tipo usa sufijos numéricos (Ej: EColi_1, SCerevisiae_2) • Asigna valores por defecto coherentes cuando el usuario no especifique parámetros"
)

def count_tokens(text: str) -> int:
    try:
        encoding = tiktoken.encoding_for_model(FINE_TUNED_MODEL_NAME)
    except Exception:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def check_api_connection() -> bool:
    try:
        openai.Model.list()
        return True
    except Exception as e:
        print("Error al conectar con la API:", e)
        return False

def call_api_generic(pregunta: str, model_name: str, system_message: str) -> tuple:
    if not check_api_connection():
        return "", 0, 0

    try:
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": pregunta}
        ]
        
        input_tokens = count_tokens(system_message) + count_tokens(pregunta)
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=messages,
            temperature=0,
            timeout=30
        )
        
        reply = response.choices[0].message["content"].strip()
        output_tokens = count_tokens(reply)
        return reply, input_tokens, output_tokens
    except Exception as e:
        print(f"Error al llamar al modelo {model_name}: {e}")
        return "", 0, 0

def call_primary_model(pregunta: str) -> tuple:
    return call_api_generic(pregunta, FINE_TUNED_MODEL_NAME, SYSTEM_MESSAGE_PRIMARY)

def call_secondary_model(pregunta: str) -> tuple:
    return call_api_generic(pregunta, SECOND_FINE_TUNED_MODEL_NAME, SYSTEM_MESSAGE_SECONDARY)

def split_braces_outside_strings(code: str) -> str:
    result_lines = []
    in_string = False
    for line in code.splitlines(keepends=True):
        new_line_chars = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == '"':
                in_string = not in_string
                new_line_chars.append(ch)
            elif ch == '{' and not in_string:
                new_line_chars.append('\n{\n')
            elif ch == '}' and not in_string:
                new_line_chars.append('\n}\n')
            else:
                new_line_chars.append(ch)
            i += 1
        result_lines.append(''.join(new_line_chars))
    return ''.join(result_lines)

def separar_codigos_por_archivo(respuesta: str) -> dict:
    patrones = re.findall(r'(\d+)\.(\w+\.cs)\{(.*?)}(?=\d+\.|$)', respuesta, re.DOTALL)
    if not patrones:
        print("No se encontraron bloques de código en la respuesta.")
        return {}

    codigos = {}
    for _, archivo, contenido in patrones:
        codigos[archivo] = format_csharp(contenido.strip())
    return codigos

def format_csharp(contenido: str) -> str:
    preprocesado = split_braces_outside_strings(contenido)
    preprocesado = re.sub(r';', r';\n', preprocesado)
    preprocesado = re.sub(r'\n\s*\n', '\n', preprocesado)
    lineas = [l.strip() for l in preprocesado.split('\n') if l.strip()]
    nivel_indentacion = 0
    contenido_formateado = []
    indent_char = "    "
    for linea in lineas:
        if linea.startswith("}"):
            nivel_indentacion = max(nivel_indentacion - 1, 0)
        contenido_formateado.append(indent_char * nivel_indentacion + linea)
        if linea.endswith("{"):
            nivel_indentacion += 1
    return "\n".join(contenido_formateado)

def import_codes(codes: dict, simulation_name: str) -> bool:
    base_dir = os.getcwd()
    simulation_folder = os.path.join(base_dir, "Simulations", simulation_name)

    if os.path.exists(simulation_folder):
        if os.path.isdir(simulation_folder):
             print(f"Advertencia: La carpeta de simulación '{simulation_name}' ya existe en {simulation_folder}.")
        else:
             print(f"Error: Ya existe un archivo llamado '{simulation_name}' en la ubicación de Simulaciones. Elija otro nombre.")
             return False

    template_folder = os.path.join(base_dir, "Template")
    if not os.path.exists(template_folder) or not os.path.isdir(template_folder):
         print(f"Error: No se encontró la carpeta 'Template' en {base_dir}. No se puede crear la simulación.")
         return False

    try:
        if not os.path.exists(simulation_folder):
            shutil.copytree(template_folder, simulation_folder)
            print(f"Estructura de Template copiada a: {simulation_folder}")
        else:
            print(f"Usando carpeta de simulación existente: {simulation_folder}")
    except Exception as e:
        print(f"Error al copiar la estructura del Template: {e}")
        return False

    assets_editor_folder = os.path.join(simulation_folder, "Assets", "Editor")
    assets_scripts_folder = os.path.join(simulation_folder, "Assets", "Scripts")
    assets_scripts_components = os.path.join(assets_scripts_folder, "Components")
    assets_scripts_systems = os.path.join(assets_scripts_folder, "Systems")
    assets_scripts_general = os.path.join(assets_scripts_folder, "General")

    os.makedirs(assets_editor_folder, exist_ok=True)
    os.makedirs(assets_scripts_components, exist_ok=True)
    os.makedirs(assets_scripts_systems, exist_ok=True)
    os.makedirs(assets_scripts_general, exist_ok=True)

    template_system_path = os.path.join(template_folder, "Assets", "Scripts", "Systems", "GeneralSystem.cs")
    if not os.path.exists(template_system_path):
        print(f"Advertencia: No se encontró el archivo template 'GeneralSystem.cs' en {template_system_path}. Los scripts de sistema se escribirán directamente.")
        template_system_path = None

    template_create_path = os.path.join(template_folder, "Assets", "Scripts", "General", "CreatePrefabsOnClick.cs")
    if not os.path.exists(template_create_path):
        print(f"Advertencia: No se encontró el archivo template 'CreatePrefabsOnClick.cs' en {template_create_path}. Este script se escribirá directamente.")
        template_create_path = None

    files_processed = []
    for file_name, content in codes.items():
        dest_path = ""
        new_content = content

        try:
            if file_name == "PrefabMaterialCreator.cs":
                dest_path = os.path.join(assets_editor_folder, file_name)
                new_content = (
                    "#if UNITY_EDITOR\n"
                    "using UnityEngine;\n"
                    "using UnityEditor;\n"
                    "using System.IO;\n\n"
                    f"{content}\n"
                    "#endif\n"
                )
            elif "Component.cs" in file_name:
                dest_path = os.path.join(assets_scripts_components, file_name)
            elif "System.cs" in file_name:
                dest_path = os.path.join(assets_scripts_systems, file_name)
                if template_system_path:
                    try:
                        with open(template_system_path, "r", encoding="utf-8") as f:
                            template_lines = f.readlines()
                        organism_name = file_name.replace("System.cs", "")
                        new_class_declaration = f"public partial class {organism_name}System : SystemBase"
                        new_component_declaration = f"{organism_name}Component"
                        temp_content = "".join(template_lines)
                        temp_content = temp_content.replace("public partial class GeneralSystem : SystemBase", new_class_declaration)
                        temp_content = temp_content.replace("GeneralComponent", new_component_declaration)
                        template_lines = temp_content.splitlines(keepends=True)
                        insertion_index = -1
                        target_line_content = "transform.Scale=math.lerp(initialScale,maxScale,t);}"
                        for i, line in enumerate(template_lines):
                             if target_line_content in line.replace(" ", "").replace("\t", ""):
                                 insertion_index = i
                                 break
                        if insertion_index != -1:
                            template_lines.insert(insertion_index + 1, "\n" + content + "\n")
                            new_content = "".join(template_lines)
                        else:
                            print(f"Advertencia: No se encontró la línea de inserción ('{target_line_content}') en {template_system_path} para {file_name}. Se usará el contenido recibido directamente.")
                            new_content = content
                    except Exception as e:
                        print(f"Error procesando template de sistema para {file_name}: {e}. Se usará el contenido recibido directamente.")
                        new_content = content
            elif file_name == "CreatePrefabsOnClick.cs":
                 dest_path = os.path.join(assets_scripts_general, file_name)
                 if template_create_path:
                      try:
                           with open(template_create_path, "r", encoding="utf-8") as f:
                                template_lines = f.readlines()
                           insertion_index = -1
                           target_signature = "private void CargarPrefabs()"
                           target_content_part = "Resources.LoadAll<GameObject>"
                           for i, line in enumerate(template_lines):
                                if target_signature in line and target_content_part in line:
                                     insertion_index = i
                                     break
                           if insertion_index != -1:
                                template_lines.insert(insertion_index + 1, "\n" + content + "\n")
                                new_content = "".join(template_lines)
                           else:
                                print(f"Advertencia: No se encontró la línea de inserción ('{target_signature}' y '{target_content_part}') en {template_create_path}. Se usará el contenido recibido directamente.")
                                new_content = content 
                      except Exception as e:
                           print(f"Error procesando template CreatePrefabsOnClick para {file_name}: {e}. Se usará el contenido recibido directamente.")
                           new_content = content
            else:
                print(f"Advertencia: Archivo no reconocido '{file_name}'. Se colocará en Assets/Scripts/General.")
                dest_path = os.path.join(assets_scripts_general, file_name)

            if dest_path:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Archivo '{os.path.basename(dest_path)}' guardado en {os.path.dirname(dest_path)}")
                files_processed.append(dest_path)
            else:
                 print(f"Error: No se pudo determinar la ruta de destino para '{file_name}'. Archivo omitido.")
        except Exception as e:
            print(f"Error procesando el archivo '{file_name}': {e}")

    template_system_dest = os.path.join(assets_scripts_systems, "GeneralSystem.cs")
    if os.path.exists(template_system_dest):
        try:
            os.remove(template_system_dest)
            print(f"Archivo template '{os.path.basename(template_system_dest)}' eliminado de la simulación.")
        except Exception as e:
            print(f"Error al eliminar '{os.path.basename(template_system_dest)}': {e}")

    if files_processed:
        return True
    else:
        print("No se procesaron archivos.")
        return False

DELIMITER = "%|%"

try:
    # Crear una carpeta específica para tu aplicación dentro de Documentos
    APP_DATA_DIR = Path.home() / "Documents" / "UnitySimulationManagerData"
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True) # Crea la carpeta si no existe
    RESPONSES_DIR = APP_DATA_DIR / "Responses"
    RESPONSES_CSV = RESPONSES_DIR / "Responses.csv"
    print(f"INFO: Usando ruta de datos: {RESPONSES_CSV}") # Bueno para depurar
except Exception as e:
    print(f"ERROR CRÍTICO: No se pudo determinar o crear la ruta de datos del usuario: {e}")
    # Aquí podrías mostrar un error al usuario y salir, o intentar un fallback
    # Fallback (menos ideal): Intentar escribir junto al script/exe
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    RESPONSES_DIR = os.path.join(script_dir, "Responses")
    RESPONSES_CSV = os.path.join(RESPONSES_DIR, "Responses.csv")
    print(f"WARNING: Fallback a ruta junto al script/exe: {RESPONSES_CSV}")

def check_last_char_is_newline(filepath: Union[str, Path]) -> bool: # Acepta Path
    filepath = Path(filepath) # Asegurar que sea Path
    if not filepath.exists() or filepath.stat().st_size == 0:
        return True
    try:
        with open(filepath, 'rb') as f:
            f.seek(-1, os.SEEK_END)
            last_byte = f.read(1)
            return last_byte == b'\n'
    except Exception as e:
        print(f"Advertencia al verificar último carácter de {filepath}: {e}")
        return False

def get_next_id(csv_path: Union[str, Path]) -> int: # Acepta Path
    csv_path = Path(csv_path) # Asegurar que sea Path
    try:
        # Asegurar que el directorio exista ANTES de intentar leer/escribir
        csv_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error creando directorio para {csv_path}: {e}")
        raise

    if not csv_path.exists():
        return 1

    last_id = 0
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) <= 1:
            return 1
        for line in reversed(lines):
            line = line.strip()
            if line:
                try:
                    parts = line.split(DELIMITER)
                    if parts and parts[0].strip().isdigit():
                        last_id = int(parts[0].strip())
                        return last_id + 1
                except (IndexError, ValueError):
                    continue
        return 1
    except FileNotFoundError:
         return 1
    except Exception as e:
         print(f"Error leyendo CSV {csv_path} para obtener ID: {e}. Iniciando desde ID 1.")
         return 1

def write_response_to_csv(pregunta: str, respuesta: str, input_tokens: int, output_tokens: int) -> None:
    try:
        # Asegurar que el directorio exista (definido globalmente ahora)
        RESPONSES_DIR.mkdir(parents=True, exist_ok=True) # Usa la variable Path global

        # Determinar estado del archivo
        file_exists = RESPONSES_CSV.exists() # Usa la variable Path global
        is_empty = file_exists and RESPONSES_CSV.stat().st_size == 0
        write_header = not file_exists or is_empty

        # Obtener ID (también crea directorio si es necesario)
        next_id = get_next_id(RESPONSES_CSV)

        # Verificar newline
        needs_leading_newline = file_exists and not is_empty and not check_last_char_is_newline(RESPONSES_CSV)

        # Abrir y escribir
        with open(RESPONSES_CSV, "a", encoding="utf-8", newline='') as f:
            if needs_leading_newline:
                f.write('\n')
            if write_header:
                header = f"id{DELIMITER}pregunta{DELIMITER}respuesta{DELIMITER}input_tokens{DELIMITER}output_tokens\n"
                f.write(header)

            clean_pregunta = str(pregunta).replace(DELIMITER, "<DELIM>").replace('\n', '\\n').replace('\r', '')
            clean_respuesta = str(respuesta).replace(DELIMITER, "<DELIM>").replace('\n', '\\n').replace('\r', '')
            line = f"{next_id}{DELIMITER}{clean_pregunta}{DELIMITER}{clean_respuesta}{DELIMITER}{input_tokens}{DELIMITER}{output_tokens}\n"
            f.write(line)

        print(f"Respuesta guardada en: {RESPONSES_CSV} (id: {next_id})") # Muestra la ruta completa

    except IOError as e:
        print(f"Error Crítico de E/S al escribir en {RESPONSES_CSV}: {e}")
        print("Verifique permisos en la carpeta de Documentos o si el archivo está bloqueado.")
        # Considera mostrar un messagebox aquí si estás en la GUI
    except Exception as e:
        print(f"Error inesperado al escribir en CSV: {e}")
        traceback.print_exc()

def get_cached_response(pregunta: str) -> Union[str, None]:
    if not RESPONSES_CSV.exists(): # Usa la variable Path global
        return None
    try:
        with open(RESPONSES_CSV, "r", encoding="utf-8") as f:
             lines = f.readlines()
        clean_pregunta_search = str(pregunta).replace(DELIMITER, "<DELIM>").replace('\n', '\\n').replace('\r', '')
        for line in lines[1:]:
            line = line.strip()
            if not line: continue
            parts = line.split(DELIMITER)
            if len(parts) == 5:
                cached_pregunta = parts[1]
                cached_respuesta_raw = parts[2]
                if cached_pregunta == clean_pregunta_search:
                    original_respuesta = cached_respuesta_raw.replace('\\n', '\n').replace("<DELIM>", DELIMITER)
                    return original_respuesta
            else:
                print(f"Advertencia: Ignorando línea CSV con formato incorrecto (partes={len(parts)}): {line[:100]}...")
    except FileNotFoundError:
         return None
    except Exception as e:
         print(f"Error leyendo el caché desde {RESPONSES_CSV}: {e}")
         return None
    return None

def api_manager(simulation_name: str, simulation_description: str, use_cache: bool = True) -> bool:
    print(f"\n--- Iniciando Proceso para Simulación: '{simulation_name}' ---")
    print(f"Descripción recibida: \"{simulation_description}\"")

    # 1. Validar y Formatear la Pregunta con el Modelo Secundario
    print("\n1. Validando y formateando descripción con modelo secundario...")
    formatted_pregunta, second_input_tk, second_output_tk = call_secondary_model(simulation_description)

    # Manejo de errores específicos del modelo secundario o de conexión
    if formatted_pregunta.startswith("Error:") or (not formatted_pregunta and second_input_tk == 0 and second_output_tk == 0):
         error_msg = f"Error from validation model: {formatted_pregunta}. Possible causes: Invalid API Key, connection issue, model unavailable/misconfigured."
         print(f"Error crítico del modelo secundario: {error_msg}") # Keep logging
         return False, error_msg

    # Manejo de errores de contenido/formato detectados por el modelo secundario
    formatted_pregunta_strip = formatted_pregunta.strip()
    if formatted_pregunta_strip == "ERROR DE CONTENIDO":
        error_msg = "Invalid Content: The description must exclusively refer to E.Coli and/or S.Cerevisiae and their parameters."
        print("Error: " + error_msg)
        return False, error_msg
    elif formatted_pregunta_strip == "ERROR CANTIDAD EXCEDIDA":
        error_msg = "Exceeded Organism Limit: The maximum number of organisms (2) was exceeded."
        print("Error: " + error_msg)
        return False, error_msg
    elif "ERROR" in formatted_pregunta_strip.upper(): # Captura otros posibles errores
        error_msg = f"Validation Model Error: {formatted_pregunta_strip}"
        print("Error: " + error_msg)
        return False, error_msg

    print(f"Descripción validada y formateada:\n{formatted_pregunta}")

    # 2. Buscar en Caché o Generar con Modelo Primario
    final_response = None
    cache_hit = False
    total_input_tokens = second_input_tk
    total_output_tokens = second_output_tk

    if use_cache:
        print("\n2. Buscando respuesta en caché...")
        cached_response = get_cached_response(formatted_pregunta)
        if cached_response:
            print("   Respuesta encontrada en caché.")
            final_response = cached_response
            cache_hit = True
    else:
        print("\n2. Caché deshabilitado. Procediendo a generar código.")


    if not final_response:
        if not cache_hit and use_cache:
             print("   Respuesta no encontrada en caché.")
        print("   Generando código con modelo primario...")

        primary_response, primary_input_tk, primary_output_tk = call_primary_model(formatted_pregunta)
        total_input_tokens += primary_input_tk
        total_output_tokens += primary_output_tk

        # Manejo de errores del modelo primario
        if primary_response.startswith("Error:") or (not primary_response and primary_input_tk == 0 and primary_output_tk == 0):
            error_msg = f"Critical error from primary model: {primary_response}. Check API Key/connection/model ID."
            print("Error: " + error_msg)
            return False, error_msg

        if "ERROR FORMATO DE PREGUNTA" in primary_response.upper():
             error_msg = f"Format Error: The primary model rejected the formatted prompt:\n'{formatted_pregunta}'"
             print("Error: " + error_msg)
             return False, error_msg

        final_response = primary_response
        print("   Código generado.")

        # Guardar en caché si no hubo hit y el caché está habilitado
        if use_cache:
            write_response_to_csv(formatted_pregunta, final_response, total_input_tokens, total_output_tokens)

    # Verificar que tengamos una respuesta final
    if not final_response:
         error_msg = "Critical Error: No final response obtained (neither from cache nor API)."
         print(error_msg)
         return False, error_msg

    # 3. Separar y Formatear Códigos
    print("\n3. Extrayendo y formateando códigos C#...")
    codes = separar_codigos_por_archivo(final_response)

    if not codes:
        error_msg = f"Code Extraction Error: Could not extract valid C# code blocks from the response.\nResponse start:\n{final_response[:200]}..."
        print("Error: " + error_msg)
        return False, error_msg

    print(f"   Se extrajeron y formatearon {len(codes)} scripts:")
    for filename in codes.keys():
        print(f"   - {filename}")

    # 4. Importar Códigos al Proyecto
    print(f"\n4. Importando códigos a la simulación '{simulation_name}'...")
    success = import_codes(codes, simulation_name)

    if success:
        final_sim_path = os.path.join(SIMULATIONS_DIR, simulation_name)
        print(f"\n--- Proceso Completado Exitosamente ---")
        print(f"Simulación '{simulation_name}' creada/actualizada en: {final_sim_path}")
        return True, None
    else:
        error_msg = f"File Import Error: Failed to save generated scripts for '{simulation_name}'. Check console logs for details on specific file issues."
        print("\n--- Process Failed (Import Stage) ---")
        print(error_msg)
        return False, error_msg 


# ======================================================
# End api_manager
# ======================================================

# ======================================================
# GUI Utilities & Interaction Control
# ======================================================
def center_window(window, width, height):
    window.update_idletasks()
    sw, sh = window.winfo_screenwidth(), window.winfo_screenheight()
    x, y = (sw - width) // 2, (sh - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def apply_icon(window):
    """Aplica el icono global (ICON_PATH) a la ventana dada."""
    try:
        if ICON_PATH and os.path.exists(ICON_PATH) and platform.system() == "Windows":
            window.iconbitmap(ICON_PATH)
    except tk.TclError as e:
        print(f"Advertencia: Icono '{ICON_PATH}' no aplicable a una ventana. Error: {e}")
    except Exception as e:
        print(f"Error inesperado al aplicar icono: {e}")

class CustomInputDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, prompt, width=400, height=170):
        super().__init__(parent)
        self.title(title)
        apply_icon(self)
        center_window(self, width, height)
        self.resizable(False, False); self.transient(parent); self.grab_set()
        self.result = None
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure((0, 1), weight=1); self.grid_rowconfigure(2, weight=0)
        ctk.CTkLabel(self, text=prompt, font=APP_FONT).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        self.entry = ctk.CTkEntry(self, font=APP_FONT, width=width-40); self.entry.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        button_frame = ctk.CTkFrame(self, fg_color="transparent"); button_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="e")
        mode_idx = get_color_mode_index()
        ok_button = ctk.CTkButton(button_frame, text="OK", command=self.ok, width=80, font=APP_FONT, fg_color=COLOR_SUCCESS_GENERAL[mode_idx]); ok_button.pack(side="left", padx=(0, 10))
        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self.cancel, width=80, font=APP_FONT, fg_color=COLOR_WARNING_GENERAL[mode_idx], hover_color=COLOR_DANGER_GENERAL[mode_idx]); cancel_button.pack(side="left")
        self.bind("<Return>", lambda e: self.ok()); self.bind("<Escape>", lambda e: self.cancel())
        self.entry.focus(); self.wait_window()
    def ok(self): self.result = self.entry.get(); self.destroy()
    def cancel(self): self.destroy()

def custom_askstring(title, prompt):
    if 'main_window' in globals() and main_window.winfo_exists(): return CustomInputDialog(main_window, title, prompt).result
    print(f"Warn: Main window N/A for dialog '{title}'."); return None

def show_tooltip(widget, text):
    global tooltip_window; hide_tooltip()
    try: x, y = widget.winfo_pointerxy(); x += 20; y += 10
    except: return
    if isinstance(widget, ttk.Treeview): pass
    else:
        try: x, y, h = widget.winfo_rootx(), widget.winfo_rooty(), widget.winfo_height(); y += h + 5
        except: pass
    tooltip_window = tk.Toplevel(widget); tooltip_window.wm_overrideredirect(True); tooltip_window.wm_geometry(f"+{x}+{y}")
    label = tk.Label(tooltip_window, text=text, justify='left', background="#ffffe0", relief='solid', borderwidth=1, font=("Segoe UI", 9)); label.pack(ipadx=1)

def hide_tooltip():
    global tooltip_window
    if tooltip_window:
        try: tooltip_window.destroy()
        except tk.TclError: pass
        tooltip_window = None

def schedule_tooltip(widget, text):
    global tooltip_job_id; cancel_tooltip(widget)
    tooltip_job_id = widget.after(tooltip_delay, lambda: show_tooltip(widget, text))

def cancel_tooltip(widget):
    global tooltip_job_id
    if tooltip_job_id: widget.after_cancel(tooltip_job_id); tooltip_job_id = None
    hide_tooltip()

def on_closing():
    global is_build_running
    if is_build_running:
        messagebox.showwarning("Operation in Progress", "Please wait for the current build/load operation to finish before closing.")
        return

    if messagebox.askokcancel(
        title="Exit",
        message="Are you sure you want to exit Unity Simulation Manager?",
        icon='question'
        ):
        update_status("Cerrando aplicación...")
        print("Attempting to close associated Unity instances (if any)...")
        close_unity_thread = threading.Thread(target=ensure_unity_closed, daemon=True)
        close_unity_thread.start()
        print("Closing GUI...")
        main_window.after(200, main_window.destroy)

def disable_all_interactions():
    global is_build_running; is_build_running = True
    try:
        for btn in [reload_btn, graph_btn, create_btn]: btn.configure(state="disabled")
        if 'sidebar_frame' in globals():
            for w in sidebar_frame.winfo_children():
                if isinstance(w, (ctk.CTkButton, ctk.CTkSwitch)): w.configure(state="disabled")
        if 'search_entry' in globals(): search_entry.configure(state="disabled")
        if 'clear_search_btn' in globals(): clear_search_btn.configure(state="disabled")
        sim_tree.unbind("<Button-1>"); sim_tree.unbind("<Motion>"); sim_tree.configure(cursor="watch")
        update_status("Build in progress... Please wait.")
    except (NameError, tk.TclError) as e: print(f"Warning: Could not disable interactions: {e}")

def enable_all_interactions():
    global is_build_running; is_build_running = False
    try:
        if 'sidebar_frame' in globals():
            for w in sidebar_frame.winfo_children():
                if isinstance(w, (ctk.CTkButton, ctk.CTkSwitch)): w.configure(state="normal")
        if 'search_entry' in globals(): search_entry.configure(state="normal")
        if 'clear_search_btn' in globals(): clear_search_btn.configure(state="normal")
        sim_tree.bind("<Button-1>", handle_tree_click); sim_tree.bind("<Motion>", handle_tree_motion)
        sim_tree.configure(cursor="")
        update_button_states()
    except (NameError, tk.TclError) as e: print(f"Warning: Could not re-enable interactions: {e}")


# ======================================================
# Core Utilities & Error Handling
# ======================================================
def update_status(message):
    if 'main_window' in globals() and main_window.winfo_exists(): main_window.after(0, lambda: status_label.configure(text=str(message)))
    else: print(f"Status (GUI !ready): {message}")

def handle_unity_execution_error(e, operation_name="operation"):
    err_msg = (f"Error during Unity {operation_name}.\n\nDetails: {type(e).__name__}: {str(e)}\n\n"
               f"Check Unity installation/version ({UNITY_REQUIRED_VERSION_STRING}) and path.\n"
               "Consider reinstalling Unity Editor.")
    print(f"Unity Error ({operation_name}): {e}")
    if 'main_window' in globals() and main_window.winfo_exists(): main_window.after(0, lambda: messagebox.showerror("Unity Execution Error", err_msg))
    else: print("Critical error: " + err_msg)

def ensure_unity_closed():
    if not unity_path_ok or not UNITY_EXECUTABLE: return
    procs = []
    try:
        norm_exe = os.path.normcase(UNITY_EXECUTABLE)
        for p in psutil.process_iter(['exe', 'pid']):
            try:
                if p.info['exe'] and os.path.normcase(p.info['exe']) == norm_exe: procs.append(p)
            except (psutil.Error, TypeError, AttributeError): continue
    except Exception as ex: print(f"Error listing procs: {ex}"); return
    if procs:
        t_start = time.time(); print(f"Attempting to close {len(procs)} Unity instances...")
        for p in procs:
            try: p.terminate()
            except psutil.Error: pass
        _, alive = psutil.wait_procs(procs, timeout=5)
        if alive:
            print(f"{len(alive)} instances did not terminate gracefully, killing...")
            for p in alive:
                try: p.kill()
                except psutil.Error: pass
            _, alive_after_kill = psutil.wait_procs(alive, timeout=3)
            if alive_after_kill: print(f"Warning: {len(alive_after_kill)} Unity instances could not be closed.")
        print(f"Unity close check took {time.time()-t_start:.2f}s")

def open_graphs_folder(simulation_name):
    try:
        fldr = Path.home()/"Documents"/"SimulationLoggerData"/simulation_name/"Graficos"
        fldr.mkdir(parents=True, exist_ok=True)
        if platform.system() == "Windows": os.startfile(str(fldr))
        elif platform.system() == "Darwin": subprocess.Popen(["open", str(fldr)])
        else: subprocess.Popen(["xdg-open", str(fldr)])
    except Exception as e: messagebox.showerror("Error", f"Could not open graphs folder '{fldr}':\n{e}")

def get_folder_size(path):
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False): total += entry.stat(follow_symlinks=False).st_size
            elif entry.is_dir(follow_symlinks=False): total += get_folder_size(entry.path)
    except Exception: pass
    return total

def copy_directory(src, dst):
    try:
        if os.path.exists(dst): shutil.rmtree(dst, ignore_errors=True); time.sleep(0.1)
        shutil.copytree(src, dst, symlinks=False, ignore_dangling_symlinks=True); return True
    except Exception as e:
        msg = f"Error copying {src} to {dst}:\n{e}"; print(msg)
        if 'main_window' in globals() and main_window.winfo_exists(): main_window.after(0, lambda: messagebox.showerror("Copy Error", msg))
        return False

def get_build_target_and_executable(project_path):
    if not project_path: return "Unknown", None
    sistema = platform.system(); exe_name = SIMULATION_PROJECT_NAME
    if sistema == "Windows": target, pfolder, suff = "Win64", "Windows", ".exe"
    elif sistema == "Linux": target, pfolder, suff = "Linux64", "Linux", ""
    elif sistema == "Darwin": target, pfolder, suff = "OSXUniversal", "Mac", ".app"
    else: target, pfolder, suff = "Win64", "Windows", ".exe" # Default a Windows
    build_base = os.path.join(project_path, "Build", pfolder)
    ejecutable = os.path.join(build_base, exe_name + suff)
    return target, ejecutable

# ======================================================
# Simulation Logic
# ======================================================
def get_simulations():
    sims = []
    if not os.path.isdir(SIMULATIONS_DIR): return sims
    try:
        for item in os.listdir(SIMULATIONS_DIR):
            p = os.path.join(SIMULATIONS_DIR, item)
            if os.path.isdir(p) and all(os.path.exists(os.path.join(p, r)) for r in ["Assets", "ProjectSettings"]):
                c_str, l_str = "???", "Never"; c_ts, l_ts = 0, 0
                try: c_ts = os.path.getctime(p); c_str = time.strftime("%y-%m-%d %H:%M", time.localtime(c_ts))
                except: pass
                l_file = os.path.join(p, "last_opened.txt")
                if os.path.exists(l_file):
                    try:
                        with open(l_file, "r") as f: l_ts = float(f.read().strip())
                        l_str = time.strftime("%y-%m-%d %H:%M", time.localtime(l_ts))
                    except: pass
                sims.append({"name": item, "creation": c_str, "last_opened": l_str, "creation_ts": c_ts})
    except Exception as e: print(f"Err reading sims: {e}"); return []
    return sims

def update_last_opened(sim_name):
    folder = os.path.join(SIMULATIONS_DIR, sim_name)
    try: os.makedirs(folder, exist_ok=True)
    except: pass
    try:
        with open(os.path.join(folder, "last_opened.txt"), "w") as f: f.write(str(time.time()))
    except Exception as e: print(f"[Err] update_last_opened({sim_name}): {e}")

def read_last_loaded_simulation_name():
    if SIMULATION_LOADED_FILE and os.path.exists(SIMULATION_LOADED_FILE):
        try:
            with open(SIMULATION_LOADED_FILE, "r") as f: return f.read().strip()
        except Exception as e: print(f"Error reading {SIMULATION_LOADED_FILE}: {e}")
    return None

def load_simulation(sim_name):
    global last_simulation_loaded, SIMULATION_PROJECT_PATH, ASSETS_FOLDER, STREAMING_ASSETS_FOLDER, SIMULATION_LOADED_FILE
    if not unity_projects_path_ok or not UNITY_PROJECTS_PATH: messagebox.showerror("Config Error", "Invalid Unity projects path."); return False
    SIMULATION_PROJECT_PATH = os.path.join(UNITY_PROJECTS_PATH, SIMULATION_PROJECT_NAME)
    ASSETS_FOLDER = os.path.join(SIMULATION_PROJECT_PATH, "Assets")
    STREAMING_ASSETS_FOLDER = os.path.join(ASSETS_FOLDER, "StreamingAssets")
    SIMULATION_LOADED_FILE = os.path.join(STREAMING_ASSETS_FOLDER, "simulation_loaded.txt")
    src_path = os.path.join(SIMULATIONS_DIR, sim_name)
    if not os.path.isdir(src_path): messagebox.showerror("Error", f"Simulation '{sim_name}' not found."); return False
    try: os.makedirs(SIMULATION_PROJECT_PATH, exist_ok=True)
    except Exception as e: messagebox.showerror("Error", f"Could not create Unity project dir: {e}"); return False

    current_persistent_loaded = read_last_loaded_simulation_name()
    needs_full_copy = (not current_persistent_loaded or current_persistent_loaded != sim_name or not os.path.exists(ASSETS_FOLDER))

    copy_ok = True
    if needs_full_copy:
        update_status("Full copy (Assets, Packages, Settings)...")
        folders = ["Assets", "Packages", "ProjectSettings"]
        for fldr in folders:
            src = os.path.join(src_path, fldr); dst = os.path.join(SIMULATION_PROJECT_PATH, fldr)
            if os.path.exists(src):
                if not copy_directory(src, dst): copy_ok = False; break
            elif fldr in ["Assets", "ProjectSettings"]: messagebox.showwarning("Warning", f"Missing '{fldr}' in sim '{sim_name}'.")
    else:
        update_status("Updating Assets...")
        src_assets = os.path.join(src_path, "Assets"); dst_assets = ASSETS_FOLDER
        if os.path.exists(src_assets): copy_ok = copy_directory(src_assets, dst_assets)
        else: messagebox.showerror("Error", f"Missing 'Assets' in sim '{sim_name}'."); copy_ok = False

    if not copy_ok: update_status("Copy error. Load cancelled."); return False
    try:
        os.makedirs(STREAMING_ASSETS_FOLDER, exist_ok=True)
        with open(SIMULATION_LOADED_FILE, "w") as f: f.write(sim_name)
        print(f"State file updated with: {sim_name}")
    except Exception as e: messagebox.showwarning("Error", f"Could not create StreamingAssets or state file:\n{e}")

    update_last_opened(sim_name); last_simulation_loaded = sim_name
    if 'main_window' in globals() and main_window.winfo_exists(): main_window.after(50, populate_simulations)
    return True

def delete_simulation(sim_name):
    confirm = messagebox.askyesno(
        "Confirm Deletion",
        f"Permanently delete '{sim_name}' and all associated data (logs, graphs)?\n\nThis action cannot be undone.",
        icon='warning'
    )
    if not confirm:
        update_status("Deletion cancelled.")
        return

    update_status(f"Deleting '{sim_name}'...")
    errs = False
    global last_simulation_loaded, all_simulations_data

    # --- Manejo del archivo de estado ---
    loaded_sim_path = SIMULATION_LOADED_FILE
    if loaded_sim_path and os.path.exists(loaded_sim_path):
        try:
            loaded = read_last_loaded_simulation_name()
            if loaded == sim_name:
                os.remove(loaded_sim_path)
                print(f"State file '{loaded_sim_path}' removed.")
                if last_simulation_loaded == sim_name:
                    last_simulation_loaded = None
            elif last_simulation_loaded == sim_name:
                 last_simulation_loaded = None
        except Exception as e:
            print(f"Warn: Could not read or remove state file '{loaded_sim_path}': {e}")
    elif last_simulation_loaded == sim_name:
         last_simulation_loaded = None

    # --- Eliminación del directorio de simulación ---
    sim_p = os.path.join(SIMULATIONS_DIR, sim_name)
    if os.path.exists(sim_p):
        try:
            shutil.rmtree(sim_p)
            print(f"Simulation directory '{sim_p}' removed.")
        except PermissionError as e:
             messagebox.showerror("Error", f"Permission denied deleting simulation folder:\n{sim_p}\n{e}")
             errs = True
        except OSError as e:
             messagebox.showerror("Error", f"Could not delete simulation folder:\n{sim_p}\n{e}")
             errs = True
        except Exception as e:
             messagebox.showerror("Error", f"An unexpected error occurred deleting simulation folder:\n{sim_p}\n{e}")
             errs = True

    # --- Eliminación del directorio de datos ---
    try:
        data_p = Path.home() / "Documents" / "SimulationLoggerData" / sim_name
        if data_p.is_dir():
            try:
                shutil.rmtree(data_p)
                print(f"Data directory '{data_p}' removed.")
            except PermissionError as e:
                messagebox.showerror("Error", f"Permission denied deleting data folder:\n{data_p}\n{e}")
                errs = True
            except OSError as e:
                 messagebox.showerror("Error", f"Could not delete data folder:\n{data_p}\n{e}")
                 errs = True
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred deleting data folder:\n{data_p}\n{e}")
                errs = True
    except Exception as e:
         print(f"Warn: Could not determine or access data directory path: {e}")

    # --- Actualizar estructura de datos interna ---
    all_simulations_data = [s for s in all_simulations_data if s.get('name') != sim_name]

    # --- Actualización final de estado y UI ---
    if errs:
        update_status(f"Deletion of '{sim_name}' completed with errors.")
    else:
        update_status(f"Deletion of '{sim_name}' successful.")

    populate_simulations()


# ======================================================
# Unity Batch Execution & Progress Monitoring
# ======================================================
def format_time(seconds):
    if seconds is None or seconds < 0 or math.isinf(seconds) or math.isnan(seconds): return "--:--:--"
    if seconds == 0: return "0s"
    seconds = int(seconds); h, rem = divmod(seconds, 3600); m, s = divmod(rem, 60)
    if h > 0: return f"{h:02d}:{m:02d}:{s:02d}"
    elif m > 0: return f"{m:02d}:{s:02d}"
    else: return f"{s}s"

def monitor_unity_progress(stop_event, operation_tag):
    if not SIMULATION_PROJECT_PATH or not os.path.exists(SIMULATION_PROJECT_PATH): print(f"\nWarn: '{SIMULATION_PROJECT_PATH}' missing on monitor start."); return
    TARGET_MB = 3000.0; MB = 1024*1024; TARGET_BYTES = TARGET_MB * MB
    last_update = 0; start_time = time.time(); initial_bytes = 0; eta_str = "Calculating..."
    try: initial_bytes = get_folder_size(SIMULATION_PROJECT_PATH)
    except Exception as e: print(f"\nError get initial size: {e}"); initial_bytes = 0
    initial_mb = initial_bytes / MB
    print(f"[{operation_tag}] Monitor... Initial: {initial_mb:.1f}MB. Target: {TARGET_MB:.0f}MB")
    while not stop_event.is_set():
        now = time.time()
        if now - last_update > 1.5:
            current_bytes = 0
            try:
                current_bytes = get_folder_size(SIMULATION_PROJECT_PATH); current_mb = current_bytes / MB
                elapsed = now - start_time; increase = current_bytes - initial_bytes
                if elapsed > 5 and increase > 1024:
                    rate = increase / elapsed; remaining = TARGET_BYTES - current_bytes
                    if rate > 0 and remaining > 0: eta_sec = remaining / rate; eta_str = f"ETA: {format_time(eta_sec)}"
                    elif remaining <= 0: eta_str = "ETA: Completed"
                    else: eta_str = "ETA: --"
                elif elapsed <= 5: eta_str = "ETA: Calculating..."
                else: eta_str = "ETA: --"
                progress = (current_mb / TARGET_MB) * 100 if TARGET_MB > 0 else 0; display_p = min(progress, 100.0)
                msg = (f"[{operation_tag}] {current_mb:.1f}/{TARGET_MB:.0f}MB ({display_p:.1f}%) - {eta_str}      ")
                update_status(msg)
            except Exception as e: err_msg = f"Err read size: {e}"[:30]; update_status(f"[{operation_tag}] {err_msg}... - {eta_str}      ")
            last_update = now
        time.sleep(0.5)
    final_mb = get_folder_size(SIMULATION_PROJECT_PATH) / MB
    print(f"\n[{operation_tag}] Monitor end. Final size: {final_mb:.1f}MB")

def run_unity_batchmode(exec_method, op_name, log_file, timeout=600, extra_args=None):
    if not all([unity_path_ok, unity_version_ok, unity_projects_path_ok, SIMULATION_PROJECT_PATH]): update_status(f"Error: Cannot {op_name}. Check Unity config."); return False, None
    log_path = os.path.join(SIMULATION_PROJECT_PATH, log_file)
    cmd = [UNITY_EXECUTABLE, "-batchmode", "-quit", "-projectPath", os.path.normpath(SIMULATION_PROJECT_PATH), "-executeMethod", exec_method, "-logFile", log_path]
    if extra_args: cmd.extend(extra_args)
    success = False; stop = threading.Event(); exe_path = None
    monitor = threading.Thread(target=monitor_unity_progress, args=(stop, op_name.capitalize()), daemon=True)
    try:
        update_status(f"[{op_name.capitalize()}] Starting Unity..."); monitor.start()
        flags = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        proc = subprocess.run(cmd, check=True, timeout=timeout, creationflags=flags, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        print(f"--- Unity Stdout ({op_name}) ---\n{proc.stdout[-1000:]}\n---");
        if proc.stderr: print(f"--- Unity Stderr ({op_name}) ---\n{proc.stderr[-1000:]}\n---")
        update_status(f"[{op_name.capitalize()}] Unity process finished."); success = True
        if "BuildScript.PerformBuild" in exec_method:
            update_status(f"[{op_name.capitalize()}] Verifying build output..."); _, exe_path = get_build_target_and_executable(SIMULATION_PROJECT_PATH); found = False
            for attempt in range(6): # Check multiple times for filesystem delay
                if exe_path and os.path.exists(exe_path): found = True; print(f"Build check OK (attempt {attempt+1}): {exe_path}"); break
                print(f"Build check attempt {attempt+1} failed for {exe_path}"); time.sleep(0.5)
            if found: update_status(f"[{op_name.capitalize()}] Executable verified.")
            else: print(f"WARN: Build Executable NOT FOUND: {exe_path}"); success = False; handle_unity_execution_error(FileNotFoundError(f"Build output not found: {exe_path}"), op_name); update_status(f"[Error] {op_name.capitalize()} failed: Output missing.")
    except subprocess.CalledProcessError as e: handle_unity_execution_error(e, op_name); update_status(f"[Error] {op_name.capitalize()} fail (code {e.returncode}). Log: {log_path}"); print(f"--- Unity Output on Error ({op_name}) ---\n{e.stdout}\n{e.stderr}")
    except subprocess.TimeoutExpired as e: handle_unity_execution_error(e, op_name); update_status(f"[Error] {op_name.capitalize()} timed out. Log: {log_path}")
    except (FileNotFoundError, PermissionError) as e: handle_unity_execution_error(e, op_name); update_status(f"[Error] {op_name.capitalize()} fail (File/Perm).")
    except Exception as e: handle_unity_execution_error(e, f"{op_name} (unexpected)"); update_status(f"[Error] Unexpected error during {op_name}.")
    finally: stop.set(); monitor.join(timeout=1.0)
    return success, exe_path

def run_prefab_material_tool():
    success, _ = run_unity_batchmode("PrefabMaterialCreator.CreatePrefabsAndMaterials", "prefabs tool", "prefab_tool_log.txt", timeout=600)
    return success

def build_simulation_task(extra_args, callback):
    disable_all_interactions()
    success, final_exe = run_unity_batchmode("BuildScript.PerformBuild", "build", "build_log.txt", timeout=1800, extra_args=extra_args)
    if callback: main_window.after(0, lambda s=success, p=final_exe: callback(s, p))
    main_window.after(10, enable_all_interactions)

def build_simulation_threaded(callback=None):
    target, _ = get_build_target_and_executable(SIMULATION_PROJECT_PATH)
    if not target: print("Error: Could not determine build target"); update_status("Error: Build target unknown."); return
    threading.Thread(target=lambda: build_simulation_task(["-buildTarget", target], callback), daemon=True).start()

def open_simulation_executable():
    if not SIMULATION_PROJECT_PATH: update_status("Error: Project path not set."); return
    _, exe_path = get_build_target_and_executable(SIMULATION_PROJECT_PATH)
    if not exe_path: messagebox.showerror("Error", "Could not determine executable path."); return
    if os.path.exists(exe_path):
        try:
            update_status(f"Launching: {os.path.basename(exe_path)}...")
            if platform.system() == "Darwin": subprocess.Popen(["open", exe_path])
            elif platform.system() == "Windows": os.startfile(exe_path)
            else:
                if not os.access(exe_path, os.X_OK): os.chmod(exe_path, 0o755)
                subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path))
        except Exception as e: handle_unity_execution_error(e, f"run built sim ({os.path.basename(exe_path)})"); update_status(f"Error launching: {e}")
    else: messagebox.showerror("Error", f"Executable not found:\n{exe_path}\nPlease build the simulation first."); update_status("Error: Executable not found.")

def open_in_unity():
    if not all([unity_path_ok, unity_projects_path_ok, UNITY_EXECUTABLE, SIMULATION_PROJECT_PATH]): messagebox.showerror("Error", "Cannot open in Unity. Check config."); return
    if not os.path.isdir(SIMULATION_PROJECT_PATH): messagebox.showerror("Error", f"Project path does not exist:\n{SIMULATION_PROJECT_PATH}"); return
    try:
        update_status(f"Opening project in Unity Editor..."); cmd = [UNITY_EXECUTABLE, "-projectPath", os.path.normpath(SIMULATION_PROJECT_PATH)]
        subprocess.Popen(cmd); update_status("Launching Unity Editor...")
    except Exception as e: handle_unity_execution_error(e, "open in Unity")

# ======================================================
# API Simulation Creation
# ======================================================
def create_simulation_thread(sim_name, sim_desc, original_states):
    update_status(f"Creating '{sim_name}' via local API function...")
    success = False
    error_message_detail = f"Unknown error during creation of '{sim_name}'." 

    try:
        try:
            os.makedirs(SIMULATIONS_DIR, exist_ok=True)
        except Exception as e:
            error_message_detail = f"Could not create simulations directory: {SIMULATIONS_DIR}\n{type(e).__name__}: {e}"
            success = False
            main_window.after(0, lambda msg=error_message_detail: messagebox.showerror("Critical Setup Error", msg))
            update_status("Critical directory creation error.")
            return

        success, error_message = api_manager(sim_name, sim_desc, use_cache=True)

        if success:
            update_status(f"'{sim_name}' creation process completed successfully.")
            main_window.after(0, lambda: messagebox.showinfo("Success", f"Simulation '{sim_name}' created successfully."))
            global all_simulations_data
            all_simulations_data = get_simulations()
            main_window.after(50, populate_simulations)

        else:
            error_message_detail = error_message if error_message else f"Failed to create simulation '{sim_name}'. Reason unknown (check logs)."
            update_status(f"Error creating '{sim_name}'. Check logs.")
            main_window.after(0, lambda msg=error_message_detail: messagebox.showerror("Simulation Creation Failed", msg))

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        detailed_error = traceback.format_exc()

        error_message_detail = f"A critical unexpected error occurred during simulation creation:\n{error_type}: {error_msg}\n\nCheck logs for trace."
        main_window.after(0, lambda msg=error_message_detail: messagebox.showerror("Unexpected Creation Error", msg))
        update_status(f"Critical error during creation: {error_type}")
        print(f"--- CRITICAL ERROR in create_simulation_thread ---")
        print(detailed_error)
        print(f"--- End Critical Error ---")
        success = False

    finally:
        main_window.after(100, enable_all_interactions)
        print(f"Simulation creation thread for '{sim_name}' finished. Success: {success}")
        if not success:
            print(f"Failure reason: {error_message_detail}")

# ======================================================
# Verification Logic
# ======================================================
def perform_verification(show_results_box=False, on_startup=False):
    global unity_path_ok, unity_version_ok, unity_projects_path_ok, apis_key_ok, apis_models_ok, initial_verification_complete
    global UNITY_EXECUTABLE, UNITY_PROJECTS_PATH, OPENAI_API_KEY, FINE_TUNED_MODEL_NAME, SECONDARY_FINE_TUNED_MODEL_NAME
    global SIMULATION_PROJECT_PATH, ASSETS_FOLDER, STREAMING_ASSETS_FOLDER, SIMULATION_LOADED_FILE, last_simulation_loaded, all_simulations_data

    if not on_startup: update_status("Verifying configuration...")
    load_dotenv('.env', override=True)
    UNITY_EXECUTABLE = os.environ.get("UNITY_EXECUTABLE"); UNITY_PROJECTS_PATH = os.environ.get("UNITY_PROJECTS_PATH")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY"); FINE_TUNED_MODEL_NAME = os.getenv("FINE_TUNED_MODEL_NAME")
    SECONDARY_FINE_TUNED_MODEL_NAME = os.getenv("2ND_FINE_TUNED_MODEL_NAME")
    results = []; unity_path_ok=unity_version_ok=unity_projects_path_ok=apis_key_ok=apis_models_ok=False
    req_ver = UNITY_REQUIRED_VERSION_STRING

    # Verify Unity Executable and Version
    if not UNITY_EXECUTABLE: results.append("❌ Unity Exe: Path missing in .env file.")
    elif not os.path.isfile(UNITY_EXECUTABLE): results.append(f"❌ Unity Exe: Path invalid or not found:\n   '{UNITY_EXECUTABLE}'")
    else:
        unity_path_ok = True; results.append(f"✅ Unity Exe: Path OK.")
        try:
            editor_folder = "Editor"; exe_name = "Unity.exe" if platform.system() == "Windows" else "Unity"
            expected_suffix = os.path.join(req_ver, editor_folder, exe_name)
            normalized_exe_path = os.path.normcase(os.path.abspath(UNITY_EXECUTABLE))
            normalized_suffix = os.path.normcase(expected_suffix)
            if normalized_exe_path.endswith(normalized_suffix):
                unity_version_ok = True; results.append(f"✅ Unity Ver: Path ends correctly with '{expected_suffix}'.")
            else:
                parent_dir = os.path.dirname(normalized_exe_path)
                results.append(f"❌ Unity Ver: Path NOT end with '{expected_suffix}'.\n   Found: '...{os.path.sep}{os.path.basename(parent_dir)}{os.path.sep}{os.path.basename(normalized_exe_path)}'")
        except Exception as path_err: results.append(f"⚠️ Unity Ver: Path check error: {path_err}")

    # Verify Unity Projects Path
    if not UNITY_PROJECTS_PATH: results.append("❌ Projects Path: Missing in .env file.")
    elif not os.path.isdir(UNITY_PROJECTS_PATH): results.append(f"❌ Projects Path: Invalid or not a directory:\n   '{UNITY_PROJECTS_PATH}'")
    else:
        unity_projects_path_ok = True; results.append(f"✅ Projects Path: Directory OK.")
        SIMULATION_PROJECT_PATH = os.path.join(UNITY_PROJECTS_PATH, SIMULATION_PROJECT_NAME)
        ASSETS_FOLDER = os.path.join(SIMULATION_PROJECT_PATH, "Assets")
        STREAMING_ASSETS_FOLDER = os.path.join(ASSETS_FOLDER, "StreamingAssets")
        SIMULATION_LOADED_FILE = os.path.join(STREAMING_ASSETS_FOLDER, "simulation_loaded.txt")
        last_simulation_loaded = read_last_loaded_simulation_name()

    # Verify OpenAI API Key and Models
    apis_key_ok = False; apis_models_ok = False
    if not OPENAI_API_KEY: results.append("❌ API Key: Missing in .env file.")
    else:
        try:
            openai.api_key = OPENAI_API_KEY
            openai.Model.list(limit=1)
            apis_key_ok = True
            results.append("✅ API Key: Connection successful (v0.x).")
            list_models_func = lambda: openai.Model.list()
            retrieve_model_func = lambda model_id: openai.Model.retrieve(model_id)
            AuthErrType = AuthenticationError_v0
            InvalidReqErrType = InvalidRequestError_v0
            ConnErrType = APIConnectionError_v0

            # Common Model Verification Logic
            if apis_key_ok:
                models_ok_list = []
                primary_model_checked = False
                for model_name_label, model_id in [("Primary Model", FINE_TUNED_MODEL_NAME), ("Secondary Model", SECONDARY_FINE_TUNED_MODEL_NAME)]:
                    is_primary = (model_name_label == "Primary Model")
                    if is_primary: primary_model_checked = True

                    if not model_id:
                        msg = f"⚠️ {model_name_label}: Not set in .env file."
                        if is_primary: msg += " (Required for API creation)"
                        results.append(msg)
                        if is_primary: models_ok_list.append(False)
                        continue

                    try:
                        retrieve_model_func(model_id)
                        results.append(f"✅ {model_name_label}: ID '{model_id}' verified.")
                        if is_primary: models_ok_list.append(True)
                    except InvalidReqErrType as e:
                        results.append(f"❌ {model_name_label}: ID '{model_id}' NOT FOUND or invalid. Error: {e}")
                        if is_primary: models_ok_list.append(False)
                    except Exception as model_error:
                        results.append(f"❌ {model_name_label}: Error verifying ID '{model_id}'. Error: {type(model_error).__name__}: {model_error}")
                        if is_primary: models_ok_list.append(False)

                apis_models_ok = primary_model_checked and models_ok_list and models_ok_list[0]
                if not apis_models_ok and FINE_TUNED_MODEL_NAME: results.append("❌ Primary Model: Verification failed (Invalid/Not Found ID or API error).")
                elif not FINE_TUNED_MODEL_NAME: results.append("❌ Primary Model: ID not specified in .env (Required for API creation).")

        except AuthErrType as auth_err:
             results.append(f"❌ API Key: Invalid or expired. Error: {auth_err}")
             apis_key_ok = False; apis_models_ok = False
        except ConnErrType as conn_err:
             results.append(f"❌ API Connection: Failed to connect. Error: {conn_err}")
             apis_key_ok = False; apis_models_ok = False
        except Exception as api_err:
             results.append(f"❌ API Error: Unexpected error during verification. Error: {type(api_err).__name__}: {api_err}")
             apis_key_ok = False; apis_models_ok = False
             print(f"Unexpected API verification error: {api_err}"); import traceback; traceback.print_exc()

    if not initial_verification_complete: initial_verification_complete = True
    unity_status = "Unity OK" if unity_path_ok and unity_version_ok and unity_projects_path_ok else "Unity ERR"
    api_status = "API OK" if apis_key_ok and apis_models_ok else "API ERR"
    final_status = f"{unity_status} | {api_status}"

    # Update GUI
    if 'main_window' in globals() and main_window.winfo_exists():
        main_window.after(0, lambda: update_status(final_status))
        main_window.after(50, update_button_states)
        all_simulations_data = get_simulations()
        main_window.after(100, filter_simulations)

        if on_startup:
            errors = []
            if not unity_path_ok or not unity_projects_path_ok: errors.append("- Invalid Unity Executable or Projects path.")
            elif not unity_version_ok: errors.append(f"- Unity version/path mismatch (Requires ending '...{os.path.join(req_ver, 'Editor', 'Unity.exe')}').")
            if not unity_path_ok or not unity_version_ok or not unity_projects_path_ok: errors.append("  (Unity features might fail)")
            api_errors = False
            if not os.getenv("OPENAI_API_KEY"): errors.append("- OpenAI API Key missing in .env."); api_errors=True
            elif not apis_key_ok: errors.append("- OpenAI API Key invalid or connection failed."); api_errors=True
            else:
                if not FINE_TUNED_MODEL_NAME: errors.append("- Primary fine-tuned model ID missing in .env."); api_errors=True
                elif not apis_models_ok: errors.append("- Primary fine-tuned model ID invalid/not found."); api_errors=True
            if api_errors: errors.append("  (API creation disabled)")
            if errors:
                msg = "Config Issues:\n\n" + "\n".join(errors) + "\n\nUse 'Settings' to fix .env file."
                main_window.after(300, lambda m=msg: messagebox.showwarning("Initial Configuration Issues", m))
    else: print(f"Verification Status (No GUI): {final_status}")

    if show_results_box:
        text = "Verification Results:\n\n" + "\n".join(results)
        all_ok = unity_path_ok and unity_version_ok and unity_projects_path_ok and apis_key_ok and apis_models_ok
        if 'main_window' in globals() and main_window.winfo_exists():
             mtype = messagebox.showinfo if all_ok else messagebox.showwarning
             title = "Verification Complete" if all_ok else "Verification Issues Found"
             main_window.after(0, lambda t=title, msg=text: mtype(t, msg))


# ======================================================
# Configuration Window
# ======================================================
def open_config_window():
    cfg_win = ctk.CTkToplevel(main_window)
    cfg_win.title("Settings (.env Configuration)")
    apply_icon(cfg_win)
    center_window(cfg_win, 700, 200); cfg_win.resizable(False, False); cfg_win.transient(main_window); cfg_win.grab_set()
    frame = ctk.CTkFrame(cfg_win); frame.pack(fill="both", expand=True, padx=20, pady=20); frame.grid_columnconfigure(1, weight=1)
    entries = {}
    def create_row(parent, r_idx, lbl_txt, env_var, key, is_file=True):
        ctk.CTkLabel(parent, text=lbl_txt, anchor="w", font=APP_FONT).grid(row=r_idx, column=0, padx=(0, 10), pady=5, sticky="w")
        val = os.environ.get(env_var, ""); entry_var = ctk.StringVar(value=val); entries[key] = entry_var
        ctk.CTkEntry(parent, textvariable=entry_var, font=APP_FONT).grid(row=r_idx, column=1, padx=5, pady=5, sticky="ew")
        def browse():
            init_dir="/"; cur = entry_var.get()
            if cur: pdir = os.path.dirname(cur);
            if os.path.isdir(pdir): init_dir=pdir
            elif os.path.isdir(cur): init_dir=cur
            path = filedialog.askopenfilename(title=f"Select {lbl_txt}", initialdir=init_dir) if is_file else filedialog.askdirectory(title=f"Select {lbl_txt}", initialdir=init_dir)
            if path: entry_var.set(path)
        ctk.CTkButton(parent, text="...", width=30, command=browse, font=APP_FONT).grid(row=r_idx, column=2, padx=(5, 0), pady=5)
    create_row(frame, 0, "Unity Executable:", "UNITY_EXECUTABLE", "unity_exe", is_file=True)
    create_row(frame, 1, "Unity Projects Folder:", "UNITY_PROJECTS_PATH", "projects_path", is_file=False)
    btn_frame = ctk.CTkFrame(cfg_win, fg_color="transparent"); btn_frame.pack(fill="x", padx=20, pady=(0, 20)); btn_frame.columnconfigure((0, 3), weight=1); btn_frame.columnconfigure((1, 2), weight=0)
    def save_config():
        key=os.getenv("OPENAI_API_KEY",""); m1=os.getenv("FINE_TUNED_MODEL_NAME",""); m2=os.getenv("2ND_FINE_TUNED_MODEL_NAME","")
        exe=entries['unity_exe'].get().strip(); proj=entries['projects_path'].get().strip()
        if not exe or not proj: messagebox.showerror("Input Error", "Both Unity paths required.", parent=cfg_win); return
        try:
            with open(".env", "w", encoding='utf-8') as f:
                f.write(f"UNITY_EXECUTABLE={exe}\n"); f.write(f"UNITY_PROJECTS_PATH={proj}\n")
                f.write(f"OPENAI_API_KEY={key}\n"); f.write(f"FINE_TUNED_MODEL_NAME={m1}\n"); f.write(f"2ND_FINE_TUNED_MODEL_NAME={m2}\n")
            messagebox.showinfo("Success", "Settings saved. Re-verifying...", parent=cfg_win); cfg_win.destroy()
            main_window.after(100, lambda: perform_verification(show_results_box=True))
        except Exception as e: messagebox.showerror("Save Error", f"Could not write .env file:\n{e}", parent=cfg_win)

    mode_idx = get_color_mode_index()
    save_btn = ctk.CTkButton(btn_frame, text="Save and Verify", command=save_config, font=APP_FONT, fg_color=COLOR_SUCCESS_GENERAL[mode_idx], hover_color=COLOR_INFO_GENERAL[mode_idx]); save_btn.grid(row=0, column=1, padx=10, pady=10)
    cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=cfg_win.destroy, font=APP_FONT, fg_color=COLOR_WARNING_GENERAL[mode_idx], hover_color=COLOR_DANGER_GENERAL[mode_idx]); cancel_btn.grid(row=0, column=2, padx=10, pady=10)

# ======================================================
# GUI Definitions & Callbacks
# ======================================================
def populate_simulations():
    if not initial_verification_complete: return
    update_status("Reloading simulation list...")
    global all_simulations_data, last_simulation_loaded
    all_simulations_data = get_simulations()
    last_simulation_loaded = read_last_loaded_simulation_name()
    all_simulations_data.sort(key=lambda x: x['name'].lower())
    filter_simulations()
    update_status(f"List refreshed ({len(all_simulations_data)} total simulations found).")
    update_button_states()

def filter_simulations(event=None):
    if 'sim_tree' not in globals() or 'search_entry' not in globals(): return
    search_term = search_entry.get().lower().strip()
    for item in sim_tree.get_children():
        try: sim_tree.delete(item)
        except tk.TclError: pass

    displayed_count = 0
    for i, sim_data in enumerate(all_simulations_data):
        if search_term and search_term not in sim_data['name'].lower(): continue
        is_loaded = (sim_data["name"] == last_simulation_loaded)
        row_tag = "evenrow" if displayed_count % 2 == 0 else "oddrow"
        item_tags = [row_tag]
        if is_loaded: item_tags.append("loaded")
        loaded_sym = loaded_indicator_text if is_loaded else ""
        play_sym = play_icon_text; delete_sym = delete_icon_text
        try:
            sim_tree.insert("", "end", iid=sim_data["name"],
                            values=(sim_data["name"], sim_data["creation"], sim_data["last_opened"], loaded_sym, play_sym, delete_sym),
                            tags=tuple(item_tags))
            displayed_count += 1
        except tk.TclError as e: print(f"Error inserting '{sim_data['name']}': {e}") # Should be rare now

    status_msg = status_label.cget("text")
    if initial_verification_complete:
        if search_term: status_msg = f"Displaying {displayed_count} of {len(all_simulations_data)} matching '{search_term}'."
        else: status_msg = f"Displaying {len(all_simulations_data)} simulations."
    update_status(status_msg)
    if 'last_sort_column' in globals() and last_sort_column: sort_column(sim_tree, last_sort_column, sort_order[last_sort_column])
    update_button_states()

def clear_search():
    if 'search_entry' in globals(): search_entry.delete(0, 'end'); filter_simulations()

def update_button_states():
    if 'main_window' not in globals() or not main_window.winfo_exists() or is_build_running : return
    has_selection = bool(sim_tree.selection())
    can_create = apis_key_ok and apis_models_ok
    def get_state(enabled): return "normal" if enabled else "disabled"
    states = {
        'reload': get_state(not is_build_running),
        'graph': get_state(has_selection and not is_build_running),
        'create': get_state(can_create and not is_build_running),
        'verify': get_state(not is_build_running),
        'settings': get_state(not is_build_running),
        'about': get_state(not is_build_running),
        'unity_down': get_state(not is_build_running),
        'theme_switch': get_state(not is_build_running),
        'exit': get_state(not is_build_running),
        'search': get_state(not is_build_running)
    }
    try:
        reload_btn.configure(state=states['reload']); graph_btn.configure(state=states['graph']); create_btn.configure(state=states['create'])
        if 'settings_btn' in globals(): settings_btn.configure(state=states['settings'])
        if 'verify_btn' in globals(): verify_btn.configure(state=states['verify'])
        if 'unity_down_btn' in globals(): unity_down_btn.configure(state=states['unity_down'])
        if 'about_btn' in globals(): about_btn.configure(state=states['about'])
        if 'theme_switch' in globals(): theme_switch.configure(state=states['theme_switch'])
        if 'exit_btn' in globals(): exit_btn.configure(state=states['exit'])
        if 'search_entry' in globals(): search_entry.configure(state=states['search'])
        if 'clear_search_btn' in globals(): clear_search_btn.configure(state=states['search'])
    except (NameError, tk.TclError) as e: print(f"Warning: Could not update button states: {e}")

def on_load_simulation_request(simulation_name):
    global is_build_running
    if is_build_running: return
    print(f"Load request: {simulation_name}")
    if not all([unity_path_ok, unity_version_ok, unity_projects_path_ok]): messagebox.showerror("Unity Config Error", "Cannot load: Invalid Unity config."); return
    if simulation_name == last_simulation_loaded:
        update_status(f"'{simulation_name}' already loaded. Showing options..."); update_last_opened(simulation_name)
        _, cur_exe = get_build_target_and_executable(SIMULATION_PROJECT_PATH)
        main_window.after(0, lambda s=simulation_name, p=cur_exe: show_options_window(s, p)); return
    disable_all_interactions(); update_status(f"Starting load for '{simulation_name}'...")
    threading.Thread(target=load_simulation_logic, args=(simulation_name,), daemon=True).start()

def load_simulation_logic(simulation_name):
    load_ok = False
    try:
        update_status(f"Load '{simulation_name}': Closing Unity..."); ensure_unity_closed()
        update_status(f"Load '{simulation_name}': Copying files..."); load_ok = load_simulation(simulation_name)
        if load_ok:
            update_status(f"Load '{simulation_name}': Running prefab tool..."); prefab_ok = run_prefab_material_tool()
            if prefab_ok:
                update_status(f"Load '{simulation_name}': Starting build..."); build_simulation_threaded(callback=lambda ok, p: build_callback(ok, simulation_name, p))
            else:
                update_status(f"Error in post-load (prefabs) for '{simulation_name}'. Build cancelled.")
                messagebox.showerror("Post-Load Error", f"Prefab tool failed for '{simulation_name}'. Build cancelled.")
                main_window.after(10, enable_all_interactions)
        else:
            update_status(f"Error loading files for '{simulation_name}'. Stopped."); main_window.after(10, enable_all_interactions)
    except Exception as e:
        print(f"CRITICAL ERROR load_simulation_logic: {e}"); import traceback; traceback.print_exc()
        update_status(f"Critical error during load for '{simulation_name}'."); main_window.after(10, enable_all_interactions)

def build_callback(success, simulation_name, executable_path):
    if success and executable_path and os.path.exists(executable_path):
        update_status(f"Build for '{simulation_name}' successful.")
        show_options_window(simulation_name, executable_path)
    elif success and not executable_path:
         update_status(f"Build '{simulation_name}' finished, but exe path unknown.")
         messagebox.showerror("Build Error", f"Build for '{simulation_name}' completed, but exe path missing.")
    elif success and not os.path.exists(executable_path):
        update_status(f"Build '{simulation_name}' finished, but exe not found: {executable_path}")
        messagebox.showerror("Build Error", f"Build for '{simulation_name}' completed, but exe not found:\n{executable_path}\nCheck logs.")
    else: update_status(f"Build process for '{simulation_name}' failed.")

def on_delete_simulation_request(simulation_name):
    global is_build_running
    if is_build_running: return
    print(f"Delete request: {simulation_name}")
    delete_simulation(simulation_name)

def on_show_graphs_thread():
    global is_build_running
    if is_build_running: return
    sel = sim_tree.selection()
    if not sel: messagebox.showwarning("No Selection", "Select simulation to view graphs."); return
    sim_name = sim_tree.item(sel[0], "values")[0]
    disable_all_interactions(); update_status(f"Generating graphs for '{sim_name}'...")
    threading.Thread(target=show_graphs_logic, args=(sim_name,), daemon=True).start()

def show_graphs_logic(sim_name):
    """
    Genera y muestra los gráficos para la simulación dada llamando
    directamente a la función SimulationGraphics definida localmente.
    """
    try:
        data_dir = Path.home() / "Documents" / "SimulationLoggerData" / sim_name
        csv_path = data_dir / "SimulationStats.csv"
        graphs_dir = data_dir / "Graficos" 

        if not csv_path.exists():
            messagebox.showerror("Data Not Found",
                                 f"CSV 'SimulationStats.csv' for simulation '{sim_name}' not found in:\n{data_dir}")
            update_status(f"Error: CSV data missing for '{sim_name}'.")
            return

        graphs_dir.mkdir(parents=True, exist_ok=True)

        update_status(f"Generating graphs for '{sim_name}'...")
        SimulationGraphics(sim_name)

        update_status(f"Graph generation for '{sim_name}' completed.")
        print(f"Opening graphs folder: {graphs_dir}")
        open_graphs_folder(sim_name)

    except FileNotFoundError as e:
        messagebox.showerror("File Not Found Error", f"File not found during graph generation:\n{e}")
        update_status(f"Error: File not found while generating graphs for '{sim_name}'.")
        print(f"Graph generation FileNotFoundError: {e}")
        traceback.print_exc()
    except Exception as e:
        messagebox.showerror("Graph Error", f"An error occurred while generating graphs for '{sim_name}':\n{type(e).__name__}: {e}")
        update_status(f"Error generating graphs for '{sim_name}'.")
        print(f"Graph generation exception: {e}")
        traceback.print_exc()
    finally:
        if 'main_window' in globals() and hasattr(main_window, 'after'):
             main_window.after(0, enable_all_interactions)
        else:
             try:
                 enable_all_interactions()
             except NameError:
                 print("Advertencia: 'main_window' o 'enable_all_interactions' no definidas correctamente.")

def on_create_simulation():
    global is_build_running
    if is_build_running: return
    if not apis_key_ok or not apis_models_ok: messagebox.showerror("API Config Error", "Cannot create: Invalid API Key or primary model."); return
    sim_name = custom_askstring("Create New Simulation", "Enter simulation name:");
    if not sim_name: update_status("Creation cancelled."); return
    sim_name = sim_name.strip(); invalid = r'<>:"/\|?*' + "".join(map(chr, range(32)))
    if not sim_name or any(c in sim_name for c in invalid): messagebox.showerror("Invalid Name", f"Name '{sim_name}' has invalid chars."); update_status("Invalid sim name."); return
    if os.path.exists(os.path.join(SIMULATIONS_DIR, sim_name)): messagebox.showerror("Exists", f"Sim '{sim_name}' already exists."); update_status(f"Sim '{sim_name}' exists."); return
    sim_desc = custom_askstring("Simulation Description", "Briefly describe:");
    if sim_desc is None: update_status("Creation cancelled."); return
    else: sim_desc = sim_desc.strip()
    disable_all_interactions(); update_status(f"Initiating creation of '{sim_name}'...")
    threading.Thread(target=create_simulation_thread, args=(sim_name, sim_desc, {}), daemon=True).start()

def show_options_window(simulation_name, executable_path):
    opt_win = ctk.CTkToplevel(main_window)
    opt_win.title(f"Options for '{simulation_name}'")
    apply_icon(opt_win)
    center_window(opt_win, 380, 200); opt_win.resizable(False, False); opt_win.transient(main_window); opt_win.grab_set()
    frame = ctk.CTkFrame(opt_win); frame.pack(expand=True, fill="both", padx=20, pady=20)
    ctk.CTkLabel(frame, text=f"Simulation '{simulation_name}' is loaded.", font=APP_FONT_BOLD).pack(pady=(0, 15))
    exec_ok = executable_path and os.path.exists(executable_path); run_state = "normal" if exec_ok else "disabled"
    def run_close(): open_simulation_executable(); opt_win.destroy()
    def open_unity_close(): open_in_unity(); opt_win.destroy()

    mode_idx = get_color_mode_index()
    run_btn = ctk.CTkButton(frame, text="Run Simulation", command=run_close, state=run_state, font=APP_FONT, height=40, fg_color=COLOR_SUCCESS_GENERAL[mode_idx], hover_color=COLOR_INFO_GENERAL[mode_idx]); run_btn.pack(pady=8, fill="x", padx=10)
    if not exec_ok: ctk.CTkLabel(frame, text="Executable not found.", text_color="gray", font=("Segoe UI", 9)).pack(pady=(0, 5))
    open_btn = ctk.CTkButton(frame, text="Open Project in Unity Editor", command=open_unity_close, font=APP_FONT, height=40, fg_color="#1E88E5", hover_color="#42A5F5"); open_btn.pack(pady=8, fill="x", padx=10)
    update_status(f"Options available for loaded sim '{simulation_name}'."); opt_win.wait_window()

def handle_tree_click(event):
    global is_build_running
    if is_build_running: return
    region = sim_tree.identify_region(event.x, event.y)
    if region == "cell":
        item_id = sim_tree.identify_row(event.y); col_id = sim_tree.identify_column(event.x)
        if not item_id or not col_id: cancel_tooltip(sim_tree); return
        try:
            col_idx = int(col_id.replace('#','')) - 1; col_ids = sim_tree['columns']
            if 0 <= col_idx < len(col_ids):
                col_name_id = col_ids[col_idx]; sim_name = sim_tree.item(item_id, "values")[0]
                sim_tree.selection_set(item_id); sim_tree.focus(item_id); update_button_states()
                hide_tooltip()
                if col_name_id == "col_load": print(f"Action click: Load/Run '{sim_name}'"); on_load_simulation_request(sim_name)
                elif col_name_id == "col_delete": print(f"Action click: Delete '{sim_name}'"); on_delete_simulation_request(sim_name)
            else: cancel_tooltip(sim_tree)
        except Exception as e: print(f"Error Treeview click: {e}"); cancel_tooltip(sim_tree)
    elif region == "heading": pass 
    else: cancel_tooltip(sim_tree)

def handle_tree_motion(event):
    global is_build_running
    if is_build_running: return
    region = sim_tree.identify_region(event.x, event.y)
    if region != "cell": cancel_tooltip(sim_tree); return
    col_id = sim_tree.identify_column(event.x); item_id = sim_tree.identify_row(event.y)
    if not col_id or not item_id: cancel_tooltip(sim_tree); return
    try:
        col_idx = int(col_id.replace('#','')) - 1; col_ids = sim_tree['columns']
        if 0 <= col_idx < len(col_ids):
            col_name_id = col_ids[col_idx]; tooltip = None; sim_name = sim_tree.item(item_id, 'values')[0]
            if col_name_id == "col_load": tooltip = f"Load / Run Sim '{sim_name}'"
            elif col_name_id == "col_delete": tooltip = f"Delete Sim '{sim_name}'"
            elif col_name_id == "col_loaded":
                 cell_val = sim_tree.set(item_id, column=col_name_id)
                 if cell_val == loaded_indicator_text: tooltip = f"'{sim_name}' is currently loaded."
            if tooltip: schedule_tooltip(sim_tree, tooltip)
            else: cancel_tooltip(sim_tree)
        else: cancel_tooltip(sim_tree)
    except Exception as e: print(f"Error handle_tree_motion: {e}"); cancel_tooltip(sim_tree)

def handle_tree_leave(event): cancel_tooltip(sim_tree)

def load_logo(path, target_width):
    global logo_photo_ref
    try:
        img = Image.open(path); w_p = (target_width / float(img.size[0])); h = int((float(img.size[1]) * float(w_p))); img = img.resize((target_width, h), Image.Resampling.LANCZOS); logo_photo_ref = ImageTk.PhotoImage(img); return logo_photo_ref
    except FileNotFoundError: print(f"Warn: Logo not found '{path}'"); return None
    except Exception as e: print(f"Error loading logo: {e}"); return None

def update_treeview_style():
    if 'sim_tree' not in globals() or 'main_window' not in globals() or not main_window.winfo_exists(): return
    mode_idx = get_color_mode_index(); mode_str = "Dark" if mode_idx == 1 else "Light"
    print(f"Updating Treeview style for {mode_str} mode...")
    try:
        # Get colors from the CustomTkinter theme manager
        bg = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        fg = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        sel_bg = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        head_bg = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        head_fg = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["text_color"])
        odd = "#FDFDFD" if mode_str == "Light" else "#3A3A3A"
        even = "#F7F7F7" if mode_str == "Light" else "#343434"
        loaded_bg = "#D5F5D5" if mode_str == "Light" else "#284B28" # Light green / Dark green
        loaded_fg = fg
    except Exception as e:
        print(f"Error getting theme colors: {e}. Using fallback."); bg="#2B2B2B" if mode_str=="Dark" else "#DBDBDB"; fg="white" if mode_str=="Dark" else "black"; sel_bg="#565B5E" if mode_str=="Dark" else "#3470E7"; head_bg="#4A4D50" if mode_str=="Dark" else "#A5A9AC"; head_fg="white" if mode_str=="Dark" else "black"; odd="#3A3A3A" if mode_str=="Dark" else "#EFEFEF"; even="#343434" if mode_str=="Dark" else "#F7F7F7"; loaded_bg="#284B28" if mode_str=="Dark" else "#D5F5D5"; loaded_fg=fg

    style = ttk.Style()
    try: style.theme_use("clam")
    except tk.TclError: print("Warn: 'clam' theme not available.")
    style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg, rowheight=28, font=TREEVIEW_FONT)
    style.configure("Treeview.Heading", font=TREEVIEW_HEADER_FONT, background=head_bg, foreground=head_fg, relief="flat", padding=(10, 5))
    style.map("Treeview.Heading", relief=[('active','groove'), ('!active', 'flat')])
    style.map('Treeview', background=[('selected', sel_bg)], foreground=[('selected', head_fg)])
    sim_tree.tag_configure('oddrow', background=odd, foreground=fg)
    sim_tree.tag_configure('evenrow', background=even, foreground=fg)
    sim_tree.tag_configure('loaded', background=loaded_bg, foreground=loaded_fg, font=TREEVIEW_FONT)
    print("Treeview style updated.")

def toggle_appearance_mode():
    current_mode = ctk.get_appearance_mode(); new_mode = "Dark" if current_mode == "Light" else "Light"
    print(f"Switching appearance mode to: {new_mode}")
    ctk.set_appearance_mode(new_mode)
    if 'theme_switch' in globals(): theme_switch.configure(text=f"{new_mode} Mode")

    main_window.after(50, update_treeview_style)

    # Update Custom Button Colors
    mode_idx = get_color_mode_index()
    try:
        # Update Logo
        logo_photo = load_logo(LOGO_PATHS[mode_idx], LOGO_WIDTH)
        if logo_photo and 'sidebar_frame' in globals() and sidebar_frame.winfo_exists():
             logo_label = sidebar_frame.winfo_children()[0]
             if isinstance(logo_label, ctk.CTkLabel):
                 logo_label.configure(image=logo_photo)
                 logo_label.image = logo_photo

        # Update Sidebar Buttons
        settings_btn.configure(fg_color=BTN_SETTINGS_FG_COLOR[mode_idx], hover_color=BTN_SETTINGS_HOVER_COLOR[mode_idx], text_color=BTN_SETTINGS_TEXT_COLOR[mode_idx])
        verify_btn.configure(fg_color=BTN_VERIFY_FG_COLOR[mode_idx], hover_color=BTN_VERIFY_HOVER_COLOR[mode_idx], text_color=BTN_VERIFY_TEXT_COLOR[mode_idx])
        unity_down_btn.configure(fg_color=BTN_UNITY_DOWN_FG_COLOR[mode_idx], hover_color=BTN_UNITY_DOWN_HOVER_COLOR[mode_idx], text_color=BTN_UNITY_DOWN_TEXT_COLOR[mode_idx])
        about_btn.configure(fg_color=BTN_ABOUT_FG_COLOR[mode_idx], hover_color=BTN_ABOUT_HOVER_COLOR[mode_idx], text_color=BTN_ABOUT_TEXT_COLOR[mode_idx])
        exit_btn.configure(fg_color=BTN_EXIT_FG_COLOR[mode_idx], hover_color=BTN_EXIT_HOVER_COLOR[mode_idx], text_color=BTN_EXIT_TEXT_COLOR[mode_idx])

        # Update Bottom Buttons
        reload_btn.configure(fg_color=BTN_RELOAD_FG_COLOR[mode_idx], hover_color=BTN_RELOAD_HOVER_COLOR[mode_idx], text_color=BTN_RELOAD_TEXT_COLOR[mode_idx])
        graph_btn.configure(fg_color=BTN_GRAPH_FG_COLOR[mode_idx], hover_color=BTN_GRAPH_HOVER_COLOR[mode_idx], text_color=BTN_GRAPH_TEXT_COLOR[mode_idx])
        create_btn.configure(fg_color=BTN_CREATE_FG_COLOR[mode_idx], hover_color=BTN_CREATE_HOVER_COLOR[mode_idx], text_color=BTN_CREATE_TEXT_COLOR[mode_idx])

        # Update Search Button
        clear_search_btn.configure(fg_color=BTN_CLEARSEARCH_FG_COLOR[mode_idx], hover_color=BTN_CLEARSEARCH_HOVER_COLOR[mode_idx], text_color=BTN_CLEARSEARCH_TEXT_COLOR[mode_idx])

        print("Button colors updated for theme.")
    except NameError as e: print(f"Warn: Button color update failed (widget N/A?): {e}")
    except Exception as e: print(f"Error updating button colors: {e}")


# ======================================================
# GUI Setup
# ======================================================
main_window = ctk.CTk()
apply_icon(main_window)
main_window.title("Unity Simulation Manager v1.0")
initial_width=1050; initial_height=700; center_window(main_window, initial_width, initial_height)
main_window.resizable(True, True); main_window.minsize(850, 550)

# Layout
main_window.columnconfigure(0, weight=0); main_window.columnconfigure(1, weight=1)
main_window.rowconfigure(0, weight=1); main_window.rowconfigure(1, weight=0)

# Sidebar
sidebar_width=200; sidebar_frame = ctk.CTkFrame(main_window, width=sidebar_width, corner_radius=5, fg_color=COLOR_SIDEBAR_BG)
sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10); sidebar_frame.grid_propagate(False); sidebar_frame.columnconfigure(0, weight=1)

# Initial mode for logo and colors
mode_idx = get_color_mode_index()
initial_mode = ctk.get_appearance_mode()

logo_photo = load_logo(LOGO_PATHS[mode_idx], LOGO_WIDTH)
if logo_photo: ctk.CTkLabel(sidebar_frame, image=logo_photo, text="").pack(pady=(20, 10), padx=10)
else: ctk.CTkLabel(sidebar_frame, text="[Logo]", font=(APP_FONT[0], 14, "italic")).pack(pady=(20, 10), padx=10)
ctk.CTkLabel(sidebar_frame, text="Menu", font=(APP_FONT[0], 16, "bold")).pack(pady=(5, 15), padx=10)

# Sidebar Buttons
settings_btn = ctk.CTkButton(sidebar_frame, text="Settings (.env)", command=open_config_window, font=APP_FONT,
                             fg_color=BTN_SETTINGS_FG_COLOR[mode_idx],
                             hover_color=BTN_SETTINGS_HOVER_COLOR[mode_idx],
                             text_color=BTN_SETTINGS_TEXT_COLOR[mode_idx])
settings_btn.pack(fill="x", padx=15, pady=5)

verify_btn = ctk.CTkButton(sidebar_frame, text="Verify Config", command=lambda: perform_verification(show_results_box=True), font=APP_FONT,
                           fg_color=BTN_VERIFY_FG_COLOR[mode_idx],
                           hover_color=BTN_VERIFY_HOVER_COLOR[mode_idx],
                           text_color=BTN_VERIFY_TEXT_COLOR[mode_idx])
verify_btn.pack(fill="x", padx=15, pady=5)

separator = ctk.CTkFrame(sidebar_frame, height=2, fg_color="gray"); separator.pack(fill="x", padx=15, pady=15)

class UnityHubInfoDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, message_text, download_url):
        super().__init__(parent)
        self.title(title)
        apply_icon(self)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._message = message_text
        self._download_url = download_url

        # --- Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)

        # Message Label
        self.message_label = ctk.CTkLabel(self, text=self._message, font=APP_FONT, justify="left", wraplength=400)
        self.message_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 15), sticky="w")

        # Link Section Frame
        link_frame = ctk.CTkFrame(self, fg_color="transparent")
        link_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
        link_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(link_frame, text="Download Link:", font=APP_FONT_BOLD).grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.link_entry = ctk.CTkEntry(link_frame, font=APP_FONT)
        self.link_entry.insert(0, self._download_url)
        self.link_entry.configure(state="readonly")
        self.link_entry.grid(row=0, column=1, sticky="ew")

        # Button Frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="e")

        mode_idx = get_color_mode_index()

        # Copy Button
        self.copy_button = ctk.CTkButton(button_frame, text="Copy Link", command=self.copy_link, width=100, font=APP_FONT,
                                         fg_color=BTN_RELOAD_FG_COLOR[mode_idx], hover_color=BTN_RELOAD_HOVER_COLOR[mode_idx]) # Example colors
        self.copy_button.pack(side="left", padx=(0, 10))

        # Open Button
        open_button = ctk.CTkButton(button_frame, text="Open Page", command=self.open_download_page, width=100, font=APP_FONT,
                                       fg_color=BTN_GRAPH_FG_COLOR[mode_idx], hover_color=BTN_GRAPH_HOVER_COLOR[mode_idx]) # Example colors
        open_button.pack(side="left", padx=(0, 10))

        # Close Button
        close_button = ctk.CTkButton(button_frame, text="Close", command=self.destroy, width=80, font=APP_FONT,
                                      fg_color=COLOR_WARNING_GENERAL[mode_idx], hover_color=COLOR_DANGER_GENERAL[mode_idx]) # Example colors
        close_button.pack(side="left")

        self.update_idletasks()
        width = max(450, self.winfo_reqwidth())
        height = self.winfo_reqheight()
        center_window(self, width, height) 

        self.bind("<Escape>", lambda e: self.destroy())
        self.after(100, self.link_entry.focus) 
        self.wait_window()

    def copy_link(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self._download_url)
            print(f"Copied to clipboard: {self._download_url}")
            original_text = self.copy_button.cget("text")
            self.copy_button.configure(text="Copied!", state="disabled")
            self.after(1500, lambda: self.copy_button.configure(text=original_text, state="normal"))
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            messagebox.showerror("Clipboard Error", f"Could not copy link to clipboard:\n{e}", parent=self)

    def open_download_page(self):
        try:
            webbrowser.open(self._download_url)
            self.destroy()
        except Exception as e:
            print(f"Error opening URL in browser: {e}")
            messagebox.showerror("Browser Error", f"Could not open the download page in your browser:\n{e}", parent=self)

def handle_unity_download_click():
    if not 'UNITY_REQUIRED_VERSION_STRING' in globals() or not UNITY_REQUIRED_VERSION_STRING:
        print("Error: UNITY_REQUIRED_VERSION_STRING not defined.")
        if 'main_window' in globals() and main_window.winfo_exists():
             messagebox.showerror("Internal Error", "Required Unity version is not configured.", parent=main_window)
        return

    unity_uri = f"unityhub://{UNITY_REQUIRED_VERSION_STRING}/b2e806cf271c"

    # Determine OS, download link, and specific build module
    system_os = platform.system()
    build_support_module = "" # Initialize
    if system_os == "Windows":
        hub_download_link = "https://public-cdn.cloud.unity3d.com/hub/prod/UnityHubSetup.exe"
        os_name = "Windows"
        build_support_module = "- Windows Build Support (IL2CPP)"
    elif system_os == "Darwin":
        hub_download_link = "https://public-cdn.cloud.unity3d.com/hub/prod/UnityHubSetup.dmg"
        os_name = "macOS"
        build_support_module = "- Mac Build Support (Mono)"
    else:
        hub_download_link = "https://unity.com/download"
        os_name = system_os
        build_support_module = "- Platform Build Support (check options)"

    detailed_instructions = (
        "To install the correct Unity Editor using this tool:\n\n"
        "1. Install Unity Hub using the link below (if you haven't already), but don't run it after installation.\n\n"
        "2. Close this message and click the 'Download Unity Editor' button in this app again.\n"
        f"   This should open Unity Hub and automatically start the install process for the required editor version ({UNITY_REQUIRED_VERSION_STRING}).\n\n"
        "3. During the editor installation setup within Unity Hub, carefully review the modules to install. Ensure these are selected:\n"
        "   - Microsoft Visual Studio Community 2022\n"
        f"   {build_support_module}\n\n"
        "4. Continue the installation in Unity Editor until it is fully complete."
    )

    what_if_failed = (
        "\n" + ("-" * 45) + "\n\n"
        "If Unity Hub did NOT open when you clicked the button this time:\n"
        "- This usually means Unity Hub is not installed or not correctly registered to handle `unityhub://` links.\n"
        f"- Please ensure Unity Hub is installed (use the download link for {os_name} below).\n"
        "- Once Unity Editor is installed, try clicking the 'Download Unity Editor' button again (Step 2 above)."
    )

    message_text = detailed_instructions + what_if_failed

    try:
        print(f"Attempting to open: {unity_uri}")
        webbrowser.open(unity_uri)
    except Exception as e:
        print(f"Error attempting to open unityhub:// link: {e}")
        if 'main_window' in globals() and main_window.winfo_exists():
            messagebox.showwarning("Link Error",
                                   f"Could not directly ask Unity Hub to open the link:\n{e}\n\n"
                                   "Please follow the manual installation steps shown.", parent=main_window)

    if 'main_window' in globals() and main_window.winfo_exists():
        dialog = UnityHubInfoDialog(
            parent=main_window,
            title="Download Unity Editor / Hub Instructions",
            message_text=message_text,
            download_url=hub_download_link
        )
    else:
        print("INFO (Fallback - Custom Dialog): " + message_text.replace('\n\n', ' | ').replace('\n', ' ') + f" | Link: {hub_download_link}")

unity_down_btn = ctk.CTkButton(sidebar_frame, text="Download Unity Editor",
                              command=handle_unity_download_click,
                              font=APP_FONT,
                              fg_color=BTN_UNITY_DOWN_FG_COLOR[mode_idx],
                              hover_color=BTN_UNITY_DOWN_HOVER_COLOR[mode_idx],
                              text_color=BTN_UNITY_DOWN_TEXT_COLOR[mode_idx])
unity_down_btn.pack(fill="x", padx=15, pady=5)

about_btn = ctk.CTkButton(sidebar_frame, text="About", command=lambda: messagebox.showinfo("About", "Unity Simulation Manager v1.0.\nBy:\nIván Cáceres S. \nTobías Guerrero Ch."), font=APP_FONT,
                          fg_color=BTN_ABOUT_FG_COLOR[mode_idx],
                          hover_color=BTN_ABOUT_HOVER_COLOR[mode_idx],
                          text_color=BTN_ABOUT_TEXT_COLOR[mode_idx])
about_btn.pack(fill="x", padx=15, pady=5)

theme_switch = ctk.CTkSwitch(sidebar_frame, text=f"{initial_mode} Mode", command=toggle_appearance_mode, font=APP_FONT); theme_switch.pack(fill="x", side='bottom', padx=15, pady=(10, 5))
if initial_mode == "Dark": theme_switch.select()
else: theme_switch.deselect()

exit_btn = ctk.CTkButton(sidebar_frame, text="Exit Application", command=on_closing, font=APP_FONT,
                         fg_color=BTN_EXIT_FG_COLOR[mode_idx],
                         hover_color=BTN_EXIT_HOVER_COLOR[mode_idx],
                         text_color=BTN_EXIT_TEXT_COLOR[mode_idx])
exit_btn.pack(fill="x", side='bottom', padx=15, pady=(5, 20))

# Main Content
main_content_frame = ctk.CTkFrame(main_window, corner_radius=5); main_content_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
main_content_frame.columnconfigure(0, weight=1); main_content_frame.rowconfigure((0, 1, 3), weight=0); main_content_frame.rowconfigure(2, weight=1) # Treeview expands
header_frame = ctk.CTkFrame(main_content_frame, fg_color="transparent"); header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5)); header_frame.columnconfigure(0, weight=1)
ctk.CTkLabel(header_frame, text="Unity Simulation Manager", font=TITLE_FONT, anchor="center").grid(row=0, column=0, pady=(0, 10))
search_frame = ctk.CTkFrame(main_content_frame, fg_color="transparent"); search_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 5)); search_frame.columnconfigure(1, weight=1)
ctk.CTkLabel(search_frame, text="Search:", font=APP_FONT).grid(row=0, column=0, padx=(5, 5), pady=5)
search_entry = ctk.CTkEntry(search_frame, placeholder_text="Type simulation name to filter...", font=APP_FONT); search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew"); search_entry.bind("<KeyRelease>", filter_simulations)
clear_search_btn = ctk.CTkButton(search_frame, text="Clear", width=60, font=APP_FONT, command=clear_search,
                                fg_color=BTN_CLEARSEARCH_FG_COLOR[mode_idx],
                                hover_color=BTN_CLEARSEARCH_HOVER_COLOR[mode_idx],
                                text_color=BTN_CLEARSEARCH_TEXT_COLOR[mode_idx])
clear_search_btn.grid(row=0, column=2, padx=(5, 5), pady=5)

# Treeview
tree_frame = ctk.CTkFrame(main_content_frame, corner_radius=5); tree_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5); tree_frame.columnconfigure(0, weight=1); tree_frame.rowconfigure(0, weight=1)
columns = ("nombre", "creacion", "ultima", "col_loaded", "col_load", "col_delete")
sim_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
sim_tree.heading("nombre", text="Simulation Name", anchor='w'); sim_tree.column("nombre", width=200, anchor="w", stretch=tk.YES)
sim_tree.heading("creacion", text="Created", anchor='center'); sim_tree.column("creacion", width=120, anchor="center", stretch=tk.NO)
sim_tree.heading("ultima", text="Last Used", anchor='center'); sim_tree.column("ultima", width=120, anchor="center", stretch=tk.NO)
sim_tree.heading("col_loaded", text="Loaded", anchor='center'); sim_tree.column("col_loaded", width=90, stretch=tk.NO, anchor="center")
sim_tree.heading("col_load", text="Load/Run", anchor='center'); sim_tree.column("col_load", width=90, stretch=tk.NO, anchor="center")
sim_tree.heading("col_delete", text="Delete", anchor='center'); sim_tree.column("col_delete", width=90, stretch=tk.NO, anchor="center")

last_sort_column = None; sort_order = {c: False for c in columns if c not in ["col_load", "col_delete", "col_loaded"]}
def sort_column(tree, col, reverse):
    if col in ["col_load", "col_delete", "col_loaded"]: return
    global last_sort_column, sort_order
    try:
        data = [(tree.set(item, col), item) for item in tree.get_children('')]
        def conv_key(val):
            if col in ("creacion", "ultima"):
                if val in ("???", "Never") or not val: return 0
                try: return time.mktime(time.strptime(val, "%y-%m-%d %H:%M"))
                except ValueError: return 0
            else: return str(val).lower()
        data.sort(key=lambda t: conv_key(t[0]), reverse=reverse)
        for i, (_, item) in enumerate(data): tree.move(item, '', i)
        sort_order[col] = reverse; last_sort_column = col
        for c in sort_order:
             txt = tree.heading(c)['text'].replace(' ▲', '').replace(' ▼', '')
             if c == col: txt += (' ▼' if reverse else ' ▲')
             tree.heading(c, text=txt, command=lambda c_=c: sort_column(tree, c_, not sort_order.get(c_, False)))
    except Exception as e: print(f"Error sorting '{col}': {e}")

for col in columns:
    if col not in ["col_load", "col_delete", "col_loaded"]:
        txt = sim_tree.heading(col)['text'].replace(' ▲','').replace(' ▼','') # Clean text first
        anchor = 'w' if col=='nombre' else 'center'
        sim_tree.heading(col, text=txt, command=lambda c=col: sort_column(sim_tree, c, False), anchor=anchor)

sim_tree.grid(row=0, column=0, sticky="nsew"); scrollbar = ctk.CTkScrollbar(tree_frame, command=sim_tree.yview); scrollbar.grid(row=0, column=1, sticky="ns"); sim_tree.configure(yscrollcommand=scrollbar.set)
sim_tree.bind('<<TreeviewSelect>>', lambda e: update_button_states()); sim_tree.bind("<Button-1>", handle_tree_click); sim_tree.bind("<Motion>", handle_tree_motion); sim_tree.bind("<Leave>", handle_tree_leave)

# Bottom Buttons
button_frame_bottom = ctk.CTkFrame(main_content_frame, fg_color="transparent"); button_frame_bottom.grid(row=3, column=0, pady=(10, 10), padx=10, sticky="ew")
button_frame_bottom.columnconfigure((0, 4), weight=1); button_frame_bottom.columnconfigure((1, 2, 3), weight=0) # Center buttons
button_height=35

reload_btn = ctk.CTkButton(button_frame_bottom, text="Reload List", command=populate_simulations, font=APP_FONT, height=button_height,
                           fg_color=BTN_RELOAD_FG_COLOR[mode_idx],
                           hover_color=BTN_RELOAD_HOVER_COLOR[mode_idx],
                           text_color=BTN_RELOAD_TEXT_COLOR[mode_idx])
reload_btn.grid(row=0, column=1, padx=10, pady=5)

graph_btn = ctk.CTkButton(button_frame_bottom, text="Simulation Statistics", command=on_show_graphs_thread, font=APP_FONT, height=button_height,
                          fg_color=BTN_GRAPH_FG_COLOR[mode_idx],
                          hover_color=BTN_GRAPH_HOVER_COLOR[mode_idx],
                          text_color=BTN_GRAPH_TEXT_COLOR[mode_idx])
graph_btn.grid(row=0, column=2, padx=10, pady=5)

create_btn = ctk.CTkButton(button_frame_bottom, text="Create Sim (API)", command=on_create_simulation, font=APP_FONT, height=button_height,
                           fg_color=BTN_CREATE_FG_COLOR[mode_idx],
                           hover_color=BTN_CREATE_HOVER_COLOR[mode_idx],
                           text_color=BTN_CREATE_TEXT_COLOR[mode_idx])
create_btn.grid(row=0, column=3, padx=10, pady=5)

# Status Bar
status_frame = ctk.CTkFrame(main_window, height=25, corner_radius=0); status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
status_label = ctk.CTkLabel(status_frame, text="Initializing...", anchor="w", font=STATUS_FONT); status_label.pack(side="left", fill="x", expand=True, padx=10, pady=3)

# ======================================================
# App Initialization
# ======================================================
if __name__ == "__main__":
    main_window.after(10, update_treeview_style)
    update_button_states()
    update_status("Performing initial configuration verification...")
    threading.Thread(target=perform_verification, args=(False, True), daemon=True).start()

    main_window.protocol("WM_DELETE_WINDOW", on_closing)
    main_window.mainloop()