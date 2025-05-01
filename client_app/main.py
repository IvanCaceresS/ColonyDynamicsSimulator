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
import psutil
import math
from PIL import Image, ImageTk
import re
import requests
from typing import Union, Tuple, Dict, List, Any, Optional, Callable
import plistlib

unity_path_ok: bool = False
unity_version_ok: bool = False
unity_projects_path_ok: bool = False
apis_key_ok: bool = False        
apis_models_ok: bool = False
initial_verification_complete: bool = False
is_build_running: bool = False
UNITY_EXECUTABLE: Optional[str] = None
UNITY_PROJECTS_PATH: Optional[str] = None
API_BASE_URL: Optional[str] = None
UNITY_REQUIRED_VERSION_STRING: str = "6000.0.32f1"
SIMULATIONS_DIR_NAME: str = "Simulations"
SIMULATIONS_DIR: Path = Path.cwd() / SIMULATIONS_DIR_NAME
SIMULATION_PROJECT_NAME: str = "Simulation"
SIMULATION_PROJECT_PATH: Optional[Path] = None
ASSETS_FOLDER: Optional[Path] = None
STREAMING_ASSETS_FOLDER: Optional[Path] = None
SIMULATION_LOADED_FILE: Optional[Path] = None
last_simulation_loaded: Optional[str] = None
all_simulations_data: List[Dict[str, Any]] = []
play_icon_text: str = "▶"
delete_icon_text: str = "🗑️"
loaded_indicator_text: str = "✓"
tooltip_window: Optional[tk.Toplevel] = None
tooltip_delay: int = 700
tooltip_job_id: Optional[str] = None
logo_photo_ref: Any = None
ICON_PATH_WIN = "img/icono.ico"
ICON_PATH_MAC = "img/icono.icns"
LOGO_PATHS: List[str] = ["img/logo_light.png", "img/logo_dark.png"]
LOGO_WIDTH: int = 200
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
APP_FONT: Tuple[str, int] = ("Segoe UI", 11)
APP_FONT_BOLD: Tuple[str, int, str] = ("Segoe UI", 11, "bold")
TITLE_FONT: Tuple[str, int, str] = ("Times New Roman", 22, "bold")
STATUS_FONT: Tuple[str, int] = ("Segoe UI", 10)
TREEVIEW_FONT: Tuple[str, int] = ("Segoe UI", 10)
TREEVIEW_HEADER_FONT: Tuple[str, int, str] = ("Segoe UI", 10, "bold")
# --- Colors Buttons (Light, Dark) ---
COLOR_SUCCESS_GENERAL: Tuple[str, str] = ("#28a745", "#4CAF50")
COLOR_DANGER_GENERAL: Tuple[str, str] = ("#C62828", "#EF5350")
COLOR_INFO_GENERAL: Tuple[str, str] = ("#218838", "#66BB6A")
COLOR_WARNING_GENERAL: Tuple[str, str] = ("#E53935", "#E53935")
COLOR_DISABLED_GENERAL: Tuple[str, str] = ("#BDBDBD", "#757575")
COLOR_SIDEBAR_BG: Optional[Tuple[str, str]] = None

def get_color_mode_index() -> int:
    return 1 if ctk.get_appearance_mode() == "Dark" else 0

# ======================================================
# INDIVIDUAL BUTTON COLOR DEFINITIONS
# ======================================================
_NEUTRAL_FG_COLOR: Tuple[str, str] = ("#A0A0A0", "#616161")
_NEUTRAL_HOVER_COLOR: Tuple[str, str] = ("#888888", "#757575")
_NEUTRAL_TEXT_COLOR: Tuple[str, str] = ("#000000", "#FFFFFF")
BTN_SETTINGS_FG_COLOR = _NEUTRAL_FG_COLOR; BTN_SETTINGS_HOVER_COLOR = _NEUTRAL_HOVER_COLOR; BTN_SETTINGS_TEXT_COLOR = _NEUTRAL_TEXT_COLOR
BTN_VERIFY_FG_COLOR = _NEUTRAL_FG_COLOR; BTN_VERIFY_HOVER_COLOR = _NEUTRAL_HOVER_COLOR; BTN_VERIFY_TEXT_COLOR = _NEUTRAL_TEXT_COLOR
BTN_ABOUT_FG_COLOR = _NEUTRAL_FG_COLOR; BTN_ABOUT_HOVER_COLOR = _NEUTRAL_HOVER_COLOR; BTN_ABOUT_TEXT_COLOR = _NEUTRAL_TEXT_COLOR
BTN_UNITY_DOWN_FG_COLOR = ("#4CAF50", "#4CAF50"); BTN_UNITY_DOWN_HOVER_COLOR = ("#388E3C", "#66BB6A"); BTN_UNITY_DOWN_TEXT_COLOR = ("#FFFFFF", "#FFFFFF")
BTN_EXIT_FG_COLOR = ("#E53935", "#E53935"); BTN_EXIT_HOVER_COLOR = ("#C62828", "#EF5350"); BTN_EXIT_TEXT_COLOR = ("#FFFFFF", "#FFFFFF")
BTN_RELOAD_FG_COLOR = ("#1E88E5", "#1E88E5"); BTN_RELOAD_HOVER_COLOR = ("#1565C0", "#42A5F5"); BTN_RELOAD_TEXT_COLOR = ("#FFFFFF", "#FFFFFF")
BTN_GRAPH_FG_COLOR = ("#673AB7", "#673AB7"); BTN_GRAPH_HOVER_COLOR = ("#512DA8", "#7E57C2"); BTN_GRAPH_TEXT_COLOR = ("#FFFFFF", "#FFFFFF")
BTN_CREATE_FG_COLOR = ("#28a745", "#4CAF50"); BTN_CREATE_HOVER_COLOR = ("#218838", "#66BB6A"); BTN_CREATE_TEXT_COLOR = ("#FFFFFF", "#FFFFFF")
BTN_CLEARSEARCH_FG_COLOR = ("#E53935", "#E53935"); BTN_CLEARSEARCH_HOVER_COLOR = ("#C62828", "#EF5350"); BTN_CLEARSEARCH_TEXT_COLOR = ("#FFFFFF", "#FFFFFF")

def SimulationGraphics(simulation_name: str) -> Optional[Path]:
    if not simulation_name:
        print("Error: Simulation name required.")
        return None
    sim_folder = Path.home() / "Documents" / "SimulationLoggerData" / simulation_name
    csv_path = sim_folder / "SimulationStats.csv"
    output_folder = sim_folder / "Graphics"
    try:
        output_folder.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error creating graphics folder {output_folder}: {e}")
        if 'main_window' in globals() and main_window.winfo_exists():
            messagebox.showerror("Graphics Error", f"Could not create:\n{output_folder}\n{e}", parent=main_window)
        return None
    if not csv_path.is_file():
        print(f"CSV file does not exist: {csv_path}")
        if 'main_window' in globals() and main_window.winfo_exists():
            messagebox.showerror("Graphics Error", f"Data not found:\n{csv_path}", parent=main_window)
        return None
    try:
        df = pd.read_csv(csv_path, sep=";", engine="python", on_bad_lines='warn')
    except Exception as e:
        print(f"Error reading CSV ({csv_path}): {e}")
        if 'main_window' in globals() and main_window.winfo_exists():
            messagebox.showerror("Graphics Error", f"Error reading CSV:\n{csv_path}\n{e}", parent=main_window)
        return None
    if df.empty:
        print("CSV is empty.")
        if 'main_window' in globals() and main_window.winfo_exists():
            messagebox.showinfo("No Data", "Stats.csv is empty.", parent=main_window)
        return None
    df.columns = df.columns.str.strip()
    if "Timestamp" not in df.columns:
        print("Error: 'Timestamp' column not found.") 
        if 'main_window' in globals() and main_window.winfo_exists():
            messagebox.showerror("Graphics Error", "'Timestamp' column not found.", parent=main_window)
        return None
    df = df[df["Timestamp"].astype(str).str.strip() != "0"]
    df["Timestamp"] = df["Timestamp"].astype(str).str.replace(r'\s+', ' ', regex=True)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format="%d-%m-%Y %H:%M:%S", errors="coerce")
    initial_rows = len(df)
    df = df.dropna(subset=["Timestamp"])
    rows_dropped = initial_rows - len(df)
    if rows_dropped > 0:
        print(f"Warning: {rows_dropped} rows dropped (invalid Timestamp).") 
    if df.empty:
        print("No valid data after Timestamp processing.") 
        if 'main_window' in globals() and main_window.winfo_exists():
            messagebox.showwarning("No Data", "No valid data to plot.", parent=main_window) 
        return None
    known_cols = {"Timestamp", "FPS", "RealTime", "SimulatedTime", "DeltaTime", "FrameCount", "Pausado", "Organism count"}
    org_cols = [c for c in df.columns if c not in known_cols]
    plots = []
    plt.style.use('seaborn-v0_8-darkgrid')
    def save_plot(filename: str):
        try:
            fp = output_folder / filename
            plt.savefig(str(fp), dpi=100)
            plots.append(fp.name)
        except Exception as e:
            print(f"Error saving {filename}: {e}") 
        plt.close()
    # --- Plot 1: FPS over Time --- 
    if "FPS" in df.columns and pd.api.types.is_numeric_dtype(df["FPS"]) and not df["FPS"].isnull().all():
        plt.figure(figsize=(12, 6))
        plt.plot(df["Timestamp"], df["FPS"], marker=".", linestyle="-", color="blue", markersize=4)
        plt.title(f"FPS over Time ({simulation_name})", fontsize=14)
        plt.xlabel("Time", fontsize=10) 
        plt.ylabel("FPS", fontsize=10) 
        plt.xticks(rotation=45, ha='right', fontsize=9)
        plt.yticks(fontsize=9)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        save_plot("fps_over_time.png")
    else:
        print("Invalid/missing 'FPS' data, skipping FPS plot.") 
    # --- Plot 2: RealTime vs SimulatedTime ---
    if ("RealTime" in df.columns and pd.api.types.is_numeric_dtype(df["RealTime"]) and not df["RealTime"].isnull().all() and
        "SimulatedTime" in df.columns and pd.api.types.is_numeric_dtype(df["SimulatedTime"]) and not df["SimulatedTime"].isnull().all()):
        plt.figure(figsize=(12, 6))
        plt.plot(df["Timestamp"], df["RealTime"], label="Real Time", marker=".", linestyle="-", markersize=4) 
        plt.plot(df["Timestamp"], df["SimulatedTime"], label="Simulated Time", marker=".", linestyle="-", color="orange", markersize=4) 
        plt.title(f"Real Time vs. Simulated Time ({simulation_name})", fontsize=14) 
        plt.xlabel("Real Time (Timestamp)", fontsize=10) 
        plt.ylabel("Time (s)", fontsize=10) 
        plt.xticks(rotation=45, ha='right', fontsize=9)
        plt.yticks(fontsize=9)
        plt.legend(fontsize=10)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        save_plot("time_comparison.png")
    else:
        print("Invalid/missing 'RealTime' or 'SimulatedTime' data, skipping Time comparison plot.")
    # --- Plot 3: Organism Counts over Time ---
    if org_cols:
        plt.figure(figsize=(12, 6))
        plotted = False
        for col in org_cols:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]) and not df[col].isnull().all():
                plt.plot(df["Timestamp"], df[col], label=col, marker=".", linestyle="-", markersize=4)
                plotted = True
            else:
                print(f"Warning: Skipping non-numeric/empty organism column: '{col}'") 
        if plotted:
            plt.title(f"Specific Organism Counts ({simulation_name})", fontsize=14) 
            plt.xlabel("Time", fontsize=10) 
            plt.ylabel("Count", fontsize=10) 
            plt.xticks(rotation=45, ha='right', fontsize=9)
            plt.yticks(fontsize=9)
            plt.legend(fontsize=10)
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.tight_layout()
            save_plot("organism_counts.png")
        else:
            print("No specific organism columns were plotted.") 
            plt.close()
    else:
        print("No specific organism columns found, skipping plot.") 
    # --- Plot 4: Total Organisms over Time ---
    if "Organism count" in df.columns and pd.api.types.is_numeric_dtype(df["Organism count"]) and not df["Organism count"].isnull().all():
        plt.figure(figsize=(12, 6))
        plt.plot(df["Timestamp"], df["Organism count"], marker=".", linestyle="-", color="purple", markersize=4)
        plt.title(f"Total Organism Count ({simulation_name})", fontsize=14) 
        plt.xlabel("Time", fontsize=10) 
        plt.ylabel("Total Count", fontsize=10) 
        plt.xticks(rotation=45, ha='right', fontsize=9)
        plt.yticks(fontsize=9)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        save_plot("total_organisms.png")
    else:
        print("Invalid/missing 'Organism count' data, skipping Total Organisms plot.") 
    # --- Plot 5: Frame Count over Time --- 
    if "FrameCount" in df.columns and pd.api.types.is_numeric_dtype(df["FrameCount"]) and not df["FrameCount"].isnull().all():
        plt.figure(figsize=(12, 6))
        plt.plot(df["Timestamp"], df["FrameCount"], marker=".", linestyle="-", color="darkcyan", markersize=4)
        plt.title(f"Frame Count ({simulation_name})", fontsize=14)
        plt.xlabel("Time", fontsize=10) 
        plt.ylabel("Frame Count", fontsize=10) 
        plt.xticks(rotation=45, ha='right', fontsize=9)
        plt.yticks(fontsize=9)
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        save_plot("frame_count.png")
    else:
        print("Invalid/missing 'FrameCount' data, skipping Frame Count plot.") 
    # --- Plot 6: FPS Distribution --- 
    if "FPS" in df.columns and pd.api.types.is_numeric_dtype(df["FPS"]) and not df["FPS"].isnull().all():
        plt.figure(figsize=(10, 6))
        plt.hist(df["FPS"].dropna(), bins=20, color="green", edgecolor="black", alpha=0.7)
        plt.title(f"FPS Distribution ({simulation_name})", fontsize=14) 
        plt.xlabel("FPS", fontsize=10) 
        plt.ylabel("Frequency", fontsize=10) 
        plt.xticks(fontsize=9)
        plt.yticks(fontsize=9)
        plt.grid(True, axis='y', linestyle='--', alpha=0.6)
        plt.tight_layout()
        save_plot("fps_histogram.png")
    else:
        print("Invalid/missing 'FPS' data, skipping FPS histogram.") 
    # --- Plot 7: Average FPS per Total Organisms --- 
    if ("Organism count" in df.columns and pd.api.types.is_numeric_dtype(df["Organism count"]) and not df["Organism count"].isnull().all() and
        "FPS" in df.columns and pd.api.types.is_numeric_dtype(df["FPS"]) and not df["FPS"].isnull().all()):
        df_grp = df.dropna(subset=["Organism count", "FPS"])
        try:
            df_grp["Organism count"] = df_grp["Organism count"].astype(int)
        except ValueError:
            print("Warning: 'Organism count' not integer, grouping by float.")
        grouped = df_grp.groupby("Organism count")["FPS"].mean().reset_index()
        if not grouped.empty and len(grouped) > 1:
            plt.figure(figsize=(12, 6))
            plt.plot(grouped["Organism count"], grouped["FPS"], marker="o", linestyle="-", color="red")
            plt.title(f"Average FPS by Total Organism Count ({simulation_name})", fontsize=14) 
            plt.xlabel("Total Organism Count", fontsize=10)
            plt.ylabel("Average FPS", fontsize=10)
            plt.xticks(fontsize=9)
            plt.yticks(fontsize=9)
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.tight_layout()
            save_plot("total_organisms_vs_fps.png")
        else:
            print("Could not group enough data for Organisms vs FPS plot.")
    else:
        print("Invalid/missing 'Organism count' or 'FPS' data, skipping Org vs FPS plot.") 
    # --- Plot 8: Organisms per Simulated Time --- 
    if ("SimulatedTime" in df.columns and pd.api.types.is_numeric_dtype(df["SimulatedTime"]) and not df["SimulatedTime"].isnull().all() and org_cols):
        plt.figure(figsize=(12, 6))
        plotted = False
        for col in org_cols:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]) and not df[col].isnull().all():
                plt.plot(df["SimulatedTime"], df[col], label=col, marker=".", linestyle="-", markersize=4)
                plotted = True
        if plotted:
            plt.title(f"Organism Count by Simulated Time ({simulation_name})", fontsize=14) 
            plt.xlabel("Simulated Time (s)", fontsize=10) 
            plt.ylabel("Organism Count", fontsize=10) 
            plt.xticks(fontsize=9)
            plt.yticks(fontsize=9)
            plt.legend(fontsize=10)
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.tight_layout()
            save_plot("organisms_vs_simulated_time.png")
        else:
            print("No organism column plotted against Simulated Time.")
            plt.close()
    else:
        print("Invalid/missing 'SimulatedTime' data or no org columns, skipping Org vs SimTime plot.")
    if plots:
        print(f"Graphics OK: {len(plots)} in {output_folder}")
        return output_folder
    else:
        print(f"Graphics: None generated for '{simulation_name}'.")
        if 'main_window' in globals() and main_window.winfo_exists():
            messagebox.showinfo("No Graphics", f"No graphics were generated for '{simulation_name}'.\nCheck data.", parent=main_window)
        return None
load_dotenv(dotenv_path=".env")
UNITY_EXECUTABLE = os.getenv("UNITY_EXECUTABLE")
UNITY_PROJECTS_PATH = os.getenv("UNITY_PROJECTS_PATH")
API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")
print(f"UNITY_EXE: {UNITY_EXECUTABLE}")
print(f"UNITY_PROJ: {UNITY_PROJECTS_PATH}")
print(f"API_URL: {API_BASE_URL}")
print(f"API_KEY (Client): {'Configurada' if API_KEY else 'NO CONFIGURADA!! (Las llamadas a API fallarán)'}")

def _make_api_request(endpoint: str, data: Dict) -> Tuple[Dict, Optional[str]]:
    if not API_BASE_URL:
        return {}, "Config Error: API_BASE_URL missing."
    if not API_KEY:
        return {}, "Config Error: API_KEY missing."

    url = f"{API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {'Content-Type': 'application/json', 'X-API-Key': API_KEY}

    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        response.raise_for_status()
        try:
            return response.json(), None
        except requests.exceptions.JSONDecodeError:
            return {}, f"API Error: Invalid JSON from {url}. Status: {response.status_code}."
    except requests.exceptions.ConnectionError:
        return {}, f"API Error: Connection failed to {url}."
    except requests.exceptions.Timeout:
        return {}, f"API Error: Timeout requesting {url}."
    except requests.exceptions.RequestException as e:
        status = e.response.status_code if e.response is not None else '???'
        body_preview = e.response.text[:50] + '...' if (e.response and e.response.text) else 'N/A'
        return {}, f"API Error: Request failed to {url}. Status: {status}. Detail: {body_preview}"
    except Exception as e:
        return {}, f"API Error: Unexpected error on {url}: {type(e).__name__}."

def call_secondary_model_via_api(question: str) -> Tuple[str, int, int, Optional[str]]:
    resp: Dict
    err: Optional[str]
    resp, err = _make_api_request('call_secondary', {'pregunta': question})
    if err:
        return "", 0, 0, err
    if 'error' in resp:
        return "", 0, 0, f"API Error (secondary): {resp['error']}"
    return resp.get('reply', ''), resp.get('input_tokens', 0), resp.get('output_tokens', 0), None

def call_primary_model_via_api(question: str) -> Tuple[str, int, int, Optional[str]]:
    resp: Dict
    err: Optional[str]
    resp, err = _make_api_request('call_primary', {'pregunta': question})
    if err:
        return "", 0, 0, err
    if 'error' in resp:
        return "", 0, 0, f"API Error (primary): {resp['error']}"
    return resp.get('reply', ''), resp.get('input_tokens', 0), resp.get('output_tokens', 0), None


def split_braces_outside_strings(code: str) -> str:
    result_lines = []
    in_string = False
    escape_next = False
    for line in code.splitlines(keepends=True):
        new_line_chars = []
        i = 0
        while i < len(line):
            ch = line[i]
            if escape_next:
                new_line_chars.append(ch)
                escape_next = False
            elif ch == '\\':
                new_line_chars.append(ch)
                escape_next = True
            elif ch == '"':
                in_string = not in_string
                new_line_chars.append(ch)
            elif ch == '{' and not in_string:
                prefix = '\n' if not ''.join(new_line_chars).endswith(('\n', ' ', '\t', '{')) else ''
                suffix = '\n' if i + 1 < len(line) and line[i+1] != '\n' else ''
                new_line_chars.append(f"{prefix}{{{suffix}")
            elif ch == '}' and not in_string:
                prefix = '\n' if not ''.join(new_line_chars).endswith(('\n', ' ', '\t', '{')) else ''
                suffix = '\n' if i + 1 < len(line) and line[i+1] != '\n' else ''
                new_line_chars.append(f"{prefix}}}{suffix}")
            else:
                new_line_chars.append(ch)
            i += 1
        result_lines.append(''.join(new_line_chars))
    return ''.join(result_lines)

def separar_codigos_por_archivo(respuesta: str) -> Dict[str, str]:
    codigos = {}
    pattern = re.compile(r"(\d+)\s*\.\s*([\w_]+\.cs)\s*\{(.*?)\}\s*(?=\d+\s*\.\s*[\w_]+\.cs|\Z)", re.DOTALL)
    matches = pattern.findall(respuesta)
    if not matches:
        print("Warn: No bloques N.Archivo.cs{...} hallados.")
        return {}
    print(f"Separador: {len(matches)} bloques hallados.")
    i = 0
    for num, archivo, contenido in matches:
        i += 1
        archivo = archivo.strip()
        contenido_limpio = contenido.strip()
        print(f"  [{i}/{len(matches)}] Proc Bloque: {num}.{archivo}")
        if not re.match(r"^[\w_\d]+\.cs$", archivo):
            print(f"    Warn: Nombre archivo inválido '{archivo}', skip.")
            continue
        codigos[archivo] = format_csharp(contenido_limpio)
    if not codigos:
        print("Err: No se extrajo ningún bloque válido.")
    return codigos

def format_csharp(contenido: str) -> str:
    try:
        contenido = re.sub(r';', ';\n', contenido)
        contenido = split_braces_outside_strings(contenido)
        contenido = re.sub(r'\n\s*\n', '\n', contenido)
        lineas = [line.strip() for line in contenido.splitlines() if line.strip()]
        if not lineas:
            return ""
        nivel = 0
        formatted_lines: List[str] = []
        indent_str = "    "
        for linea in lineas:
            if linea.startswith("}") or linea.startswith("]") or linea.startswith(");"):
                nivel = max(0, nivel - 1)
            formatted_lines.append(indent_str * nivel + linea)
            if linea.endswith("{") or linea.endswith("["):
                nivel += 1
        return "\n".join(formatted_lines)
    except Exception as e:
        print(f"Err format C#: {e}. Retornando original.")
        return contenido

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

# --- Cache Logic ---
DELIMITER = "%|%"

try:
    APP_DATA_DIR = Path.home() / "Documents" / "UnitySimulationManagerData"
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"INFO: Usando carpeta de datos: {APP_DATA_DIR}")
except Exception as e:
    print(f"Warn: Falló crear/acceder a carpeta de datos en Documentos ({e}). Usando carpeta local de caché.")
    APP_DATA_DIR = Path.cwd() / "UnitySimulationManagerData"
    try:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        print(f"INFO: Usando carpeta local: {APP_DATA_DIR}")
    except Exception as e:
        print(f"ERR CRÍTICO: !crear datos en carpeta local: {e}")

RESPONSES_DIR = APP_DATA_DIR / "Responses" # 
RESPONSES_CSV = RESPONSES_DIR / "Responses.csv"
print(f"INFO: Archivo de caché de respuestas: {RESPONSES_CSV}")

def check_last_char_nl(fp: Path) -> bool:
    if not fp.exists() or fp.stat().st_size == 0:
        return True

    try:
        with open(fp, 'rb') as f:
            f.seek(-1, os.SEEK_END)
            return f.read(1) == b'\n'
    except OSError as e:
        print(f"Warn check_last_char_nl ({fp}): Error al leer el archivo: {e}")
        return False
    except Exception as e:
        print(f"Warn check_last_char_nl ({fp}): Error inesperado: {e}")
        return False 
    
def get_next_id(csv_p: Path) -> int:
    try:
        csv_p.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Err creando dir para CSV {csv_p}: {e}")
        raise
    if not csv_p.exists() or csv_p.stat().st_size == 0:
        return 1
    last_id = 0
    try:
        lines = csv_p.read_text("utf-8").splitlines()
        if len(lines) <= 1:
            return 1
        for ln in reversed(lines[1:]):
            ln = ln.strip()
            if not ln:
                continue
            try:
                parts = ln.split(DELIMITER)
                if len(parts) > 0:
                    id_str = parts[0].strip()
                    if id_str:
                        last_id = int(id_str)
                        return last_id + 1
            except (ValueError, IndexError) as e:
                continue
        print(f"Warn: No se encontró ID válido en {csv_p} después del encabezado. Comenzando desde 1.")
        return 1
    except Exception as e:
        print(f"Err leyendo ID de {csv_p}: {e}. Usando ID=1.")
        return 1 

def write_response_to_csv(q: str, r: str, tk_in: int, tk_out: int) -> None:
    try:
        RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
        file_exists = RESPONSES_CSV.exists()
        is_empty = file_exists and RESPONSES_CSV.stat().st_size == 0
        needs_header = not file_exists or is_empty
        next_id = get_next_id(RESPONSES_CSV)
        needs_leading_newline = file_exists and not is_empty and not check_last_char_nl(RESPONSES_CSV)
        with open(RESPONSES_CSV, "a", encoding="utf-8", newline='') as f:
            if needs_leading_newline:
                f.write('\n')
            if needs_header:
                f.write(f"id{DELIMITER}question{DELIMITER}response{DELIMITER}input_tokens{DELIMITER}output_tokens\n")
            cleaned_q = str(q).replace(DELIMITER, "<D>").replace('\n', '\\n').replace('\r', '')
            cleaned_r = str(r).replace(DELIMITER, "<D>").replace('\n', '\\n').replace('\r', '')
            f.write(f"{next_id}{DELIMITER}{cleaned_q}{DELIMITER}{cleaned_r}{DELIMITER}{tk_in}{DELIMITER}{tk_out}\n")
        print(f"Resp guardada caché: {RESPONSES_CSV.name} (id:{next_id})")

    except Exception as e:
        print(f"Err escribiendo caché: {e}\n{traceback.format_exc()}")

def get_cached_response(q: str) -> Union[str, None]:
    if not RESPONSES_CSV.is_file():
        return None
    try:
        lines = RESPONSES_CSV.read_text("utf-8").splitlines()
        cleaned_q_search = str(q).replace(DELIMITER, "<D>").replace('\n', '\\n').replace('\r', '')
        for ln in reversed(lines[1:]):
            ln = ln.strip()
            if not ln:
                continue
            parts = ln.split(DELIMITER)
            if len(parts) >= 3:
                cached_q = parts[1]
                if cached_q == cleaned_q_search:
                    cr_raw = parts[2]
                    original_r = cr_raw.replace('\\n', '\n').replace("<D>", DELIMITER)
                    print(f" [Cache HIT] '{q[:50]}...'")
                    return original_r
        print(f" [Cache MISS] '{q[:50]}...'")
        return None
    except Exception as e:
        print(f"Err leyendo caché {RESPONSES_CSV}: {e}")
        return None

def api_manager(sim_name: str, sim_desc: str, use_cache: bool = True) -> Tuple[bool, Union[str, None]]:
    print(f"\n--- Inicio Proceso API para '{sim_name}' ---")
    print(f"Descripción de entrada: \"{sim_desc}\"")
    if not API_BASE_URL:
        return False, "Error de Configuración: La URL base de la API (API_BASE_URL) no está definida."
    print("\n1. Validando descripción con API (Modelo Secundario)...")
    fmt_q, tk_is, tk_os, err_s = call_secondary_model_via_api(sim_desc)
    if err_s:
        return False, f"Error en la llamada API (Modelo Validación): {err_s}"
    if not fmt_q:
         return False, "Error del Modelo Validación: La API devolvió una respuesta vacía."
    fmt_q_s = fmt_q.strip()
    if fmt_q_s == "ERROR DE CONTENIDO":
        return False, "Validación Fallida: La descripción contiene organismos o temas no permitidos. Solo EColi, SCerevisiae o ambos."
    if fmt_q_s == "ERROR CANTIDAD EXCEDIDA":
         return False, "Validación Fallida: Se solicitó más de 2 organismos. Límite máximo: 2."
    if fmt_q_s.upper().startswith("ERROR"):
         return False, f"Error del Modelo Validación: {fmt_q_s}"
    print(f"Descripción validada y formateada correctamente:\n{fmt_q}")
    final_response: Optional[str] = None 
    cache_hit = False 
    total_tk_in = tk_is 
    total_tk_out = tk_os 
    if use_cache:
        print("\n2. Buscando respuesta en la caché local...")
        cached_response = get_cached_response(fmt_q)
        if cached_response:
            final_response = cached_response
            cache_hit = True
    if not final_response:
        if use_cache:
            print("   !No se encontró en caché.")
        print("   Generando código con API (Modelo Primario)...")
        prim_r, tk_ip, tk_op, err_p = call_primary_model_via_api(fmt_q)
        if err_p:
            return False, f"Error en la llamada API (Modelo Generación): {err_p}"
        if not prim_r:
            return False, "Error del Modelo Generación: La API devolvió una respuesta vacía."
        if "ERROR FORMATO" in prim_r.upper():
            return False, f"Error de Formato de Pregunta: El modelo de generación rechazó la pregunta formateada:\n'{fmt_q}'"
        final_response = prim_r
        total_tk_in += tk_ip
        total_tk_out += tk_op
        print("   Código Generado OK.")
        if use_cache and not cache_hit:
            write_response_to_csv(fmt_q, final_response, total_tk_in, total_tk_out)
    if not final_response:
        return False, "Error Crítico: No se obtuvo una respuesta final válida (ni de caché ni generada)."
    print("\n3. Extrayendo bloques de código C#...")
    codes = separar_codigos_por_archivo(final_response)
    if not codes:
        return False, f"Error de Extracción: No se encontraron bloques de código C# válidos en la respuesta.\nInicio de respuesta recibida:\n{final_response[:800]}..."
    print(f"   {len(codes)} scripts C# extraídos:")
    for file_name in codes.keys():
         print(f"   - {file_name}")
    print(f"\n4. Importando scripts a la carpeta de la simulación '{sim_name}'...")
    ok_import = import_codes(codes, sim_name)
    if ok_import:
        print(f"\n--- Proceso API Finalizado con Éxito ---")
        print(f"Simulación '{sim_name}' creada en: {SIMULATIONS_DIR/sim_name}")
        return True, None 
    else:
        return False, f"Error de Importación: Falló al guardar los scripts para la simulación '{sim_name}'. Por favor, revisa los logs para más detalles."

# ======================================================
# GUI Utilities & Interaction Control
# ======================================================
def center_window(win: Union[tk.Tk, tk.Toplevel], w: int, h: int): win.update_idletasks(); sw=win.winfo_screenwidth(); sh=win.winfo_screenheight(); x=(sw-w)//2; y=(sh-h)//2; win.geometry(f"{w}x{h}+{x}+{y}")
def apply_icon(window):
    """Aplica el icono .ico de Windows a la ventana dada, si corresponde."""
    try:
        # Usar la variable específica de Windows y la comprobación de plataforma
        if ICON_PATH_WIN and os.path.exists(ICON_PATH_WIN) and platform.system() == "Windows":
            window.iconbitmap(ICON_PATH_WIN)
    except tk.TclError as e:
        # Actualizar mensaje de error para reflejar la variable usada
        print(f"Advertencia: Icono '{ICON_PATH_WIN}' no aplicable a una ventana. Error: {e}")
    except Exception as e:
        print(f"Error inesperado al aplicar icono: {e}")

class CustomInputDialog(ctk.CTkToplevel):
    def __init__(self, parent: Union[tk.Tk, tk.Toplevel], title: str, prompt: str, w: int = 400, h: int = 170):
        super().__init__(parent)
        self.title(title)
        apply_icon(self)
        center_window(self, w, h)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result: Optional[str] = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        prompt_label = ctk.CTkLabel(
            self,
            text=prompt,
            font=APP_FONT,
            anchor="w" 
        )
        prompt_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        self.entry = ctk.CTkEntry(
            self,
            font=APP_FONT,
            width=w - 40 
        )
        self.entry.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="e")
        idx = get_color_mode_index()

        ok_button = ctk.CTkButton(
            button_frame,
            text="OK",
            command=self._ok,
            width=80,
            font=APP_FONT,
            fg_color=COLOR_SUCCESS_GENERAL[idx]
        )
        ok_button.pack(side="left", padx=(0, 10))

        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._cancel,
            width=80,
            font=APP_FONT,
            fg_color=COLOR_WARNING_GENERAL[idx],
            hover_color=COLOR_DANGER_GENERAL[idx]
        )
        cancel_button.pack(side="left")
        self.bind("<Return>", self._ok)
        self.bind("<Escape>", self._cancel)
        self.entry.focus()
        self.wait_window()

    def _ok(self, e=None):
        self.result = self.entry.get()
        self.destroy()

    def _cancel(self, e=None):
        self.result = None
        self.destroy()

def custom_askstring(title: str, prompt: str) -> Union[str, None]:
    if 'main_window' in globals() and main_window.winfo_exists():
        dialog = CustomInputDialog(main_window, title, prompt)
        return dialog.result
    else:
        print(f"Warn: No se encontró o no es válida la ventana principal para el diálogo '{title}'.")
        return None

def show_tooltip(widget: tk.Widget, text: str):
    global tooltip_window
    hide_tooltip()

    try:
        x = widget.winfo_rootx() + 10
        y = widget.winfo_rooty() + widget.winfo_height() + 5
        sw = widget.winfo_screenwidth()
        sh = widget.winfo_screenheight()
        tooltip_window = tk.Toplevel(widget)
        tooltip_window.wm_overrideredirect(True)
        tooltip_window.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(
            tooltip_window,
            text=text,
            justify='left',
            bg="#ffffe0",  
            relief='solid', 
            bd=1,
            font=("Segoe UI", 9)
        )
        lbl.pack(ipadx=2, ipady=1)
        tooltip_window.update_idletasks()
        tip_w = tooltip_window.winfo_width()
        tip_h = tooltip_window.winfo_height()
        if x + tip_w > sw:
            x = sw - tip_w - 5
        if y + tip_h > sh:
            y = widget.winfo_rooty() - tip_h - 5
        tooltip_window.wm_geometry(f"+{max(0, x)}+{max(0, y)}")

    except Exception as e:
        print(f"Warn show_tooltip: {e}")
        tooltip_window = None

def hide_tooltip():
    global tooltip_window
    if tooltip_window:
        try:
            tooltip_window.destroy()
        except Exception:
            pass
        finally:
            tooltip_window = None

def schedule_tooltip(widget: tk.Widget, text: str):
    global tooltip_job_id
    cancel_tooltip(widget)
    tooltip_job_id = widget.after(
        tooltip_delay,
        lambda w=widget, t=text: show_tooltip(w, t)
    )

def cancel_tooltip(widget: tk.Widget):
    global tooltip_job_id
    hide_tooltip()

    if tooltip_job_id:
        try:
            widget.after_cancel(tooltip_job_id)
        except Exception:
            pass
        finally:
            tooltip_job_id = None
def on_closing():
    global is_build_running
    if is_build_running:
        messagebox.showwarning("In Progress", "Please wait.", parent=main_window)
        return
    if messagebox.askokcancel("Exit", "Are you sure?", icon='question', parent=main_window):
        update_status("Closing...")
        print("Closing Unity...")
        threading.Thread(target=ensure_unity_closed, daemon=True).start()
        print("Closing GUI...")
        main_window.after(200, main_window.destroy)
def disable_all_interactions():
    global is_build_running
    is_build_running = True
    widgets: List[Optional[tk.Widget]] = []
    for name in ['reload_btn', 'graph_btn', 'create_btn', 'search_entry', 'clear_search_btn', 'settings_btn', 'verify_btn', 'unity_down_btn', 'about_btn', 'exit_btn', 'theme_switch']:
        widget = globals().get(name)
        if widget:
            widgets.append(widget)

    for w in widgets:
        if w and hasattr(w, 'configure'):
            try:
                w.configure(state="disabled")
            except Exception as e:
                print(f"Warn: Deshabilitando {w}: {e}")

    if 'sim_tree' in globals():
        try:
            sim_tree.unbind("<Button-1>")
            sim_tree.unbind("<Motion>")
            sim_tree.configure(cursor="watch")
        except Exception as e:
            print(f"Warn: Deshabilitando Treeview: {e}")

    update_status("Operation in progress...")

def enable_all_interactions():
    global is_build_running
    is_build_running = False
    widgets: List[Optional[tk.Widget]] = []
    for name in ['reload_btn', 'graph_btn', 'create_btn', 'search_entry', 'clear_search_btn', 'settings_btn', 'verify_btn', 'unity_down_btn', 'about_btn', 'exit_btn', 'theme_switch']:
         widget = globals().get(name)
         if widget:
             widgets.append(widget)

    for w in widgets:
        if w and hasattr(w, 'configure'):
            try:
                w.configure(state="normal")
            except Exception as e:
                 print(f"Warn: Habilitando {w}: {e}")

    if 'sim_tree' in globals():
        try:
            sim_tree.bind("<Button-1>", handle_tree_click)
            sim_tree.bind("<Motion>", handle_tree_motion)
            sim_tree.configure(cursor="")
        except Exception as e:
             print(f"Warn: Habilitando Treeview: {e}")

    update_button_states()
    if 'status_label' in globals():
        cur_status = status_label.cget("text")
        if "progress" in cur_status.lower() or "..." in cur_status:
            threading.Thread(target=perform_verification, args=(False, False), daemon=True).start()

def update_status(msg: str):
    if 'main_window' in globals() and main_window.winfo_exists() and 'status_label' in globals():
        main_window.after(0, lambda m=msg: status_label.configure(text=str(m)))
    else:
        print(f"Status(noGUI): {msg}")
def handle_unity_execution_error(e: Exception, op: str = "operation"):
    err_msg = (
        f"Unity Error during '{op}'.\n\n"
        f"Details: {type(e).__name__}: {e}\n\n"
        f"Verify Unity path/version ({UNITY_REQUIRED_VERSION_STRING})."
    )
    print(f"Unity Error ({op}): {e}")
    if 'main_window' in globals() and isinstance(main_window, tk.Tk) and main_window.winfo_exists():
        main_window.after(0, lambda: messagebox.showerror("Unity Execution Error", err_msg, parent=main_window))
    else:
        print("Critical Error (no GUI): " + err_msg)

def ensure_unity_closed():
    if not unity_path_ok or not UNITY_EXECUTABLE:
        print("[UC] Skip check: Unity path not configured.")
        return

    procs: List[psutil.Process] = []
    try:
        unity_exe_path = Path(UNITY_EXECUTABLE).resolve()
        print(f"[UC] Searching for process: {unity_exe_path}")
        for p in psutil.process_iter(['exe', 'pid']):
            try:
                p_exe_str = p.info.get('exe')
                if p_exe_str:
                    p_exe_path = Path(p_exe_str).resolve()
                    if p_exe_path == unity_exe_path:
                        procs.append(p)
                        print(f"  Found PID {p.pid}")
            except (psutil.Error, OSError, ValueError):
                continue
    except Exception as ex:
        print(f"[UC] Error iterating processes: {ex}")
        return
    if not procs:
        print("[UC] No running instances found.")
        return
    t0 = time.time()
    print(f"[UC] Terminating {len(procs)} instances...")
    for p in procs:
        try:
            p.terminate()
        except psutil.Error as e:
            print(f"Warning: Failed to terminate PID {p.pid}: {e}")
    gone, alive = psutil.wait_procs(procs, timeout=5)
    print(f"[UC] {len(gone)} instances terminated successfully.")
    if alive:
        print(f"[UC] {len(alive)} instances did not respond, killing...")
        for p in alive:
            try:
                p.kill()
            except psutil.Error as e:
                print(f"Warning: Failed to kill PID {p.pid}: {e}")
        gone2, alive2 = psutil.wait_procs(alive, timeout=3)
        print(f"[UC] {len(gone2)} instances killed successfully.")
        if alive2:
            print(f"WARN: {len(alive2)} instances could not be closed: {[p.pid for p in alive2]}")
    print(f"[UC] Check finished in {time.time()-t0:.2f}s")

def open_graphs_folder(sim: str):
    try:
        graphs_folder = Path.home() / "Documents" / "SimulationLoggerData" / sim / "Graphics"
        if not graphs_folder.is_dir():
            messagebox.showinfo(
                "Folder Not Found",
                f"Graphs folder for '{sim}' does not exist.\n({graphs_folder})",
                parent=main_window
            )
            return
        print(f"Opening folder: {graphs_folder}")
        sys = platform.system()
        if sys == "Windows":
            os.startfile(str(graphs_folder))
        elif sys == "Darwin":
            subprocess.Popen(["open", str(graphs_folder)])
        else:
            subprocess.Popen(["xdg-open", str(graphs_folder)])
    except Exception as e:
         messagebox.showerror(
             "Error Opening Folder",
             f"Failed to open graphs folder:\n{graphs_folder}\nError: {e}",
             parent=main_window
         )
def get_folder_size(path):
    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False): total += entry.stat(follow_symlinks=False).st_size
            elif entry.is_dir(follow_symlinks=False): total += get_folder_size(entry.path)
    except Exception: pass
    return total
def copy_directory(src_s: str, dst_s: str) -> bool:
    src = Path(src_s)
    dst = Path(dst_s)
    print(f"Copying: {src} -> {dst}")
    try:
        if dst.exists():
            print(f" Elim {dst}")
            retries = 3
            for i in range(retries):
                 try:
                     if dst.is_dir(): shutil.rmtree(dst, ignore_errors=False)
                     else: dst.unlink()
                     break
                 except Exception as e_rm:
                     print(f" Warn elim {dst} (intento {i+1}/{retries}): {e_rm}")
                     if i == retries - 1: raise
                     time.sleep(0.3)
        print(f" shutil.copytree...")
        shutil.copytree(src, dst, symlinks=False, ignore_dangling_symlinks=True, dirs_exist_ok=False)
        print(" Copia OK.")
        return True
    except Exception as e:
        msg = f"Error copying {src} to {dst}:\n{type(e).__name__}: {e}"
        print(f" {msg}\n{traceback.format_exc()}")
        if 'main_window' in globals() and hasattr(globals().get('main_window'), 'winfo_exists') and globals()['main_window'].winfo_exists():
             messagebox.showerror("Copy Error", msg, parent=globals()['main_window'])
        return False
def get_build_target_and_executable(proj_p_s: str) -> Tuple[Union[str, None], Union[Path, None]]:
    if not proj_p_s: return None, None
    proj_p = Path(proj_p_s); sys = platform.system(); exe_n = SIMULATION_PROJECT_NAME
    if sys == "Windows": t, pf, s = "Win64", "Windows", ".exe"
    elif sys == "Linux": t, pf, s = "Linux64", "Linux", ""
    elif sys == "Darwin": t, pf, s = "OSXUniversal", "Mac", ".app"
    else: print(f"SO desc:{sys}. Default Win."); t, pf, s = "Win64", "Windows", ".exe"
    build_b = proj_p / "Build" / pf; exe_p = build_b / (exe_n + s)
    return t, exe_p

# ======================================================
# Simulation Logic
# ======================================================
def get_simulations() -> List[Dict[str, Any]]:
    sims: List[Dict[str, Any]] = []
    if not SIMULATIONS_DIR.is_dir():
        try: SIMULATIONS_DIR.mkdir(parents=True, exist_ok=True); print(f"Created:{SIMULATIONS_DIR}")
        except Exception as e: print(f"Err creating {SIMULATIONS_DIR}:{e}"); return sims
        return sims
    try:
        for item in SIMULATIONS_DIR.iterdir():
            if item.is_dir() and (item / "Assets").is_dir() and (item / "ProjectSettings").is_dir():
                name = item.name
                c_ts, l_ts = 0.0, 0.0
                c_s, l_s = "???", "Never"
                try:
                    c_ts = item.stat().st_ctime
                    c_s = time.strftime("%y-%m-%d %H:%M", time.localtime(c_ts))
                except Exception:
                    pass
                l_file = item / "last_opened.txt"
                if l_file.is_file():
                    try:
                        l_ts = float(l_file.read_text().strip())
                        l_s = time.strftime("%y-%m-%d %H:%M", time.localtime(l_ts))
                    except (ValueError, IOError):
                        pass
                sims.append({
                    "name": name,
                    "creation": c_s,
                    "last_opened": l_s,
                    "creation_ts": c_ts,
                    "last_opened_ts": l_ts
                })
    except Exception as e:
        print(f"Err leyendo sims {SIMULATIONS_DIR}:{e}")
        return []
    return sims
def update_last_opened(sim: str):
    sim_folder = SIMULATIONS_DIR / sim
    if not sim_folder.is_dir():
        print(f"Warn: Folder '{sim}' does not exist (upd last_opened).")
        return
    try:
        (sim_folder / "last_opened.txt").write_text(str(time.time()))
    except Exception as e:
        print(f"Err updating last_opened for '{sim}': {e}")
def read_last_loaded_simulation_name() -> Union[str, None]:
    if STREAMING_ASSETS_FOLDER and SIMULATION_LOADED_FILE and SIMULATION_LOADED_FILE.is_file():
        try:
            return SIMULATION_LOADED_FILE.read_text('utf-8').strip()
        except Exception as e:
            print(f"Err reading state file {SIMULATION_LOADED_FILE}: {e}")
    return None
def load_simulation(sim: str) -> bool:
    global last_simulation_loaded, SIMULATION_PROJECT_PATH, ASSETS_FOLDER, STREAMING_ASSETS_FOLDER, SIMULATION_LOADED_FILE

    if not unity_projects_path_ok or not UNITY_PROJECTS_PATH:
        if 'messagebox' in globals() and messagebox:
            messagebox.showerror("Config Error", "Invalid Unity projects path.")
        else:
            print("Config Error: Invalid Unity projects path.")
        return False

    base = Path(UNITY_PROJECTS_PATH)
    SIM_PROJ = base / SIMULATION_PROJECT_NAME
    ASSETS = SIM_PROJ / "Assets"
    STREAM = ASSETS / "StreamingAssets"
    STATE_F = STREAM / "simulation_loaded.txt"
    src = SIMULATIONS_DIR / sim

    SIMULATION_PROJECT_PATH = SIM_PROJ
    ASSETS_FOLDER = ASSETS
    STREAMING_ASSETS_FOLDER = STREAM
    SIMULATION_LOADED_FILE = STATE_F

    if not src.is_dir():
        if 'messagebox' in globals() and messagebox:
            messagebox.showerror("Error", f"Simulation folder '{sim}' not found.")
        else:
             print(f"Error: Simulation folder '{sim}' not found.")
        return False

    try:
        SIM_PROJ.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        if 'messagebox' in globals() and messagebox:
            messagebox.showerror("Error", f"Failed to create project directory:\n{SIM_PROJ}\n{e}")
        else:
            print(f"Error: Failed to create project directory {SIM_PROJ}: {e}")
        return False

    current_loaded_sim = read_last_loaded_simulation_name()
    full_copy_needed = (
        not current_loaded_sim or
        current_loaded_sim != sim or
        not ASSETS.is_dir()
    )
    reason = (
        "!state" if not current_loaded_sim else
        (f"'{current_loaded_sim}'!='{sim}'" if current_loaded_sim != sim else
         ("!Assets" if not ASSETS.is_dir() else "update Assets"))
    )
    print(f"Full copy needed: {full_copy_needed}. Reason: {reason}")

    ok = True
    folders_to_copy = ["Assets", "Packages", "ProjectSettings"]

    if full_copy_needed:
        if 'update_status' in globals() and update_status:
             update_status(f"Loading '{sim}': Full Copy...")
        print("Performing full copy...")
        for folder_name in folders_to_copy:
            dest_folder = SIM_PROJ / folder_name
            if dest_folder.exists():
                print(f" Deleting existing: {dest_folder}")
                try:
                    if dest_folder.is_dir():
                        shutil.rmtree(dest_folder)
                    else:
                        dest_folder.unlink()
                except Exception as e:
                    print(f" Error deleting {dest_folder}: {e}")
                    ok = False
                    break
        if ok:
            for folder_name in folders_to_copy:
                src_folder = src / folder_name
                dest_folder = SIM_PROJ / folder_name
                if src_folder.exists():
                    if 'copy_directory' in globals() and copy_directory:
                        if not copy_directory(str(src_folder), str(dest_folder)):
                            ok = False
                            break
                    else:
                         print(f"Warning: copy_directory function not available. Cannot copy {src_folder}.")
                         ok = False
                         break
                elif folder_name in ["Assets", "ProjectSettings"]:
                     if 'messagebox' in globals() and messagebox:
                        messagebox.showwarning("Warning", f"Source '{folder_name}' folder is missing in '{sim}'.")
                     else:
                        print(f"Warning: Source '{folder_name}' folder is missing in '{sim}'.")

    else:
        if 'update_status' in globals() and update_status:
             update_status(f"Loading '{sim}': Updating Assets...")
        print("Updating Assets folder...")
        src_assets = src / "Assets"
        dest_assets = ASSETS
        if src_assets.is_dir():
            if 'copy_directory' in globals() and copy_directory:
                ok = copy_directory(str(src_assets), str(dest_assets))
            else:
                 print(f"Warning: copy_directory function not available. Cannot copy {src_assets}.")
                 ok = False
        else:
            if 'messagebox' in globals() and messagebox:
                messagebox.showerror("Error", f"Source 'Assets' folder is missing in '{sim}'.")
            else:
                 print(f"Error: Source 'Assets' folder is missing in '{sim}'.")
            ok = False
    if not ok:
        if 'update_status' in globals() and update_status:
            update_status(f"Error copying '{sim}'. Operation cancelled.")
        else:
            print(f"Error copying '{sim}'. Operation cancelled.")
        return False
    try:
        STREAM.mkdir(parents=True, exist_ok=True)
        STATE_F.write_text(sim, 'utf-8')
        print(f"State file '{STATE_F.name}' updated with -> '{sim}'")
    except Exception as e:
        if 'messagebox' in globals() and messagebox:
            messagebox.showwarning("Warning", f"Failed to write state file:\n{STATE_F}\n{e}")
        else:
             print(f"Warning: Failed to write state file {STATE_F}: {e}")

    update_last_opened(sim)
    last_simulation_loaded = sim
    if 'main_window' in globals() and hasattr(globals().get('main_window'), 'winfo_exists') and globals()['main_window'].winfo_exists():
         if 'populate_simulations' in globals() and populate_simulations:
            globals()['main_window'].after(50, populate_simulations)
         else:
             print("Warning: populate_simulations function not available for GUI update.")
    print(f"Simulation '{sim}' loaded successfully into project {SIM_PROJ}")
    return True

def delete_simulation(sim: str):
    if 'messagebox' in globals() and messagebox:
        if not messagebox.askyesno(
            "Confirm Deletion",
            f"PERMANENTLY DELETE '{sim}'?\n(Folder, logs, graphics)\nTHIS IS NOT REVERSIBLE!",
            icon='warning',
            parent=globals().get('main_window')
        ):
            if 'update_status' in globals() and update_status:
                 update_status("Deletion cancelled.")
            print("Deletion cancelled by user.")
            return
    else:
        confirm = input(f"PERMANENTLY DELETE '{sim}'? (y/n): ")
        if confirm.lower() != 'y':
            if 'update_status' in globals() and update_status:
                 update_status("Deletion cancelled.")
            print("Deletion cancelled by user.")
            return
    if 'update_status' in globals() and update_status:
         update_status(f"Deleting '{sim}'...")
    print(f"--- Deleting '{sim}' ---")
    errors_occurred = False
    global last_simulation_loaded, all_simulations_data
    if SIMULATION_LOADED_FILE and SIMULATION_LOADED_FILE.is_file():
        try:
            if SIMULATION_LOADED_FILE.read_text('utf-8').strip() == sim:
                print(f" Deleting global state file: {SIMULATION_LOADED_FILE}")
                SIMULATION_LOADED_FILE.unlink()
                if last_simulation_loaded == sim:
                    last_simulation_loaded = None
        except Exception as e:
            print(f" Warning deleting state file: {e}")
            errors_occurred = True
    elif last_simulation_loaded == sim:
        last_simulation_loaded = None
    sim_folder = SIMULATIONS_DIR / sim
    if sim_folder.exists():
        print(f" Deleting simulation directory: {sim_folder}")
        try:
            if sim_folder.is_dir():
                shutil.rmtree(sim_folder)
            else:
                sim_folder.unlink()
        except Exception as e:
            msg = f"Error deleting simulation folder:\n{e}"
            if 'messagebox' in globals() and messagebox:
                messagebox.showerror("Error", msg, parent=globals().get('main_window'))
            print(f" ERROR: {msg}")
            errors_occurred = True
    else:
        print(f" Simulation directory '{sim_folder.name}' not found.")
    try:
        data_folder = Path.home() / "Documents" / "SimulationLoggerData" / sim
        if data_folder.is_dir():
            print(f" Deleting data directory: {data_folder}")
            try:
                shutil.rmtree(data_folder)
            except Exception as e:
                msg = f"Error deleting data folder:\n{e}"
                if 'messagebox' in globals() and messagebox:
                     messagebox.showerror("Error", msg, parent=globals().get('main_window'))
                print(f" ERROR: {msg}")
                errors_occurred = True
        else:
            print(f" Data directory '{data_folder.name}' not found.")
    except Exception as e:
         print(f" Warning accessing data path: {e}")
    all_simulations_data = [s for s in all_simulations_data if s.get('name') != sim]
    if 'update_status' in globals() and update_status:
         update_status(f"Deletion of '{sim}' {'completed with errors.' if errors_occurred else 'successful.'}")
    else:
         print(f"Deletion of '{sim}' {'completed with errors.' if errors_occurred else 'successful.'}")
    print(f"--- Finished deleting '{sim}' ---")
    if 'populate_simulations' in globals() and populate_simulations:
        populate_simulations()
    else:
        print("Warning: populate_simulations function not available for GUI update.")

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
            for attempt in range(6):
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
def create_simulation_thread(sim_name: str, sim_desc: str):
    update_status(f"Creating '{sim_name}'(API)...")
    ok = False
    err_d = f"Error description '{sim_name}'."
    try:
        SIMULATIONS_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        err_d = f"Failed to create base directory:\n{SIMULATIONS_DIR}\n{e}"
        ok = False
        if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'messagebox' in globals() and messagebox:
            main_window.after(0, lambda m=err_d: messagebox.showerror("Critical Error", m, parent=main_window))
        update_status("Critical directory error.")
    else:
        try:
            ok, err_api = api_manager(sim_name, sim_desc, use_cache=True)
            if ok:
                update_status(f"Creation of '{sim_name}' OK.")
                if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'messagebox' in globals() and messagebox:
                    main_window.after(0, lambda: messagebox.showinfo("Success", f"Sim '{sim_name}' created.", parent=main_window))
                global all_simulations_data
                all_simulations_data = get_simulations()
                if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'populate_simulations' in globals() and populate_simulations:
                    main_window.after(50, populate_simulations)
            else:
                err_d = err_api if err_api else f"Failed '{sim_name}'. Description reason."
                update_status(f"Error creating '{sim_name}'. Check logs.")
                print(f"API creation error:{err_d}")
                if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'messagebox' in globals() and messagebox:
                     main_window.after(0, lambda m=err_d: messagebox.showerror("Creation Failed", m, parent=main_window))
        except Exception as e:
            err_d = f"Unexpected critical error:\n{type(e).__name__}:{e}"
            print(f"--- CRITICAL ERROR create_sim ---\n{traceback.format_exc()}\n--- End Error ---")
            if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'messagebox' in globals() and messagebox:
                 main_window.after(0, lambda m=err_d: messagebox.showerror("Unexpected Creation Error", m, parent=main_window))
            update_status(f"Critical error:{type(e).__name__}")
            ok = False
    finally:
        if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'enable_all_interactions' in globals() and enable_all_interactions:
             main_window.after(100, enable_all_interactions)
        print(f"Creation thread for '{sim_name}' finished. OK:{ok}")
        if not ok:
            print(f"Failed:{err_d}")

# ======================================================
# Verification Logic
# ======================================================
def perform_verification(show_results=False, on_startup=False):
    # Declarar uso de globales (buena práctica) y añadir las de API
    global unity_path_ok, unity_version_ok, unity_projects_path_ok, apis_key_ok, apis_models_ok
    global initial_verification_complete, UNITY_EXECUTABLE, UNITY_PROJECTS_PATH, API_BASE_URL, API_KEY # Añadir API_KEY
    global SIMULATION_PROJECT_PATH, ASSETS_FOLDER, STREAMING_ASSETS_FOLDER, SIMULATION_LOADED_FILE, last_simulation_loaded, all_simulations_data

    if not on_startup:
        # Usar verificación de existencia y llamada segura
        status_func = globals().get('update_status')
        if status_func and callable(status_func):
             status_func("Verifying configuration...")
        else:
             print("Verifying configuration...")

    # Initialize global status flags at the start of verification
    unity_path_ok, unity_version_ok, unity_projects_path_ok = False, False, False
    apis_key_ok, apis_models_ok = False, False # Initialize API flags too

    # Load environment variables
    dotenv_func = globals().get('load_dotenv')
    if dotenv_func and callable(dotenv_func):
        dotenv_func('.env', override=True)
    UNITY_EXECUTABLE = os.getenv("UNITY_EXECUTABLE")
    UNITY_PROJECTS_PATH = os.getenv("UNITY_PROJECTS_PATH")
    API_BASE_URL = os.getenv("API_BASE_URL")
    API_KEY = os.getenv("API_KEY") # Cargar la clave API del cliente

    results = [] # Para el popup de detalles
    req_ver = UNITY_REQUIRED_VERSION_STRING

    # --- Verify Unity Executable and Version ---
    if not UNITY_EXECUTABLE:
        results.append("❌ Unity Exe: Path missing in .env file.")
    elif not os.path.exists(UNITY_EXECUTABLE):
        results.append(f"❌ Unity Exe: Path does not exist:\n    '{UNITY_EXECUTABLE}'")
    else:
        # Path exists, mark this part OK for now, might be invalidated by OS check
        unity_path_ok = True # <<< ACTUALIZA GLOBAL
        results.append(f"✅ Unity Exe: Path exists.")
        try:
            current_os = platform.system()
            if current_os == "Windows":
                if not os.path.isfile(UNITY_EXECUTABLE):
                    results.append(f"❌ Unity Exe: Path is not a file on Windows:\n    '{UNITY_EXECUTABLE}'")
                    unity_path_ok = False # <<< CORRIGE GLOBAL
                else:
                    editor_folder = "Editor"; exe_name = "Unity.exe"
                    expected_suffix = os.path.join(req_ver, editor_folder, exe_name)
                    normalized_exe_path = os.path.normcase(os.path.abspath(UNITY_EXECUTABLE))
                    normalized_suffix = os.path.normcase(expected_suffix)
                    if normalized_exe_path.endswith(normalized_suffix):
                        unity_version_ok = True # <<< ACTUALIZA GLOBAL
                        results.append(f"✅ Unity Ver: Path indicates version {req_ver}.")
                    else:
                        parent_dir = os.path.dirname(normalized_exe_path); grandparent_dir = os.path.dirname(parent_dir)
                        if grandparent_dir and grandparent_dir != parent_dir: found_structure = f"...{os.sep}{os.path.basename(grandparent_dir)}{os.sep}{os.path.basename(parent_dir)}{os.sep}{os.path.basename(normalized_exe_path)}"
                        elif parent_dir and parent_dir != normalized_exe_path: found_structure = f"...{os.sep}{os.path.basename(parent_dir)}{os.sep}{os.path.basename(normalized_exe_path)}"
                        else: found_structure = f"...{os.sep}{os.path.basename(normalized_exe_path)}"
                        results.append(f"❌ Unity Ver: Path structure mismatch.\n    Expected end: '...{os.sep}{expected_suffix}'\n    Found: '{found_structure}'")
                        # unity_version_ok remains False
            elif current_os == "Darwin":
                plist_path = None; is_app_bundle = UNITY_EXECUTABLE.endswith(".app") and os.path.isdir(UNITY_EXECUTABLE); is_likely_binary = os.path.isfile(UNITY_EXECUTABLE) and "Contents/MacOS/Unity" in UNITY_EXECUTABLE.replace("\\", "/")
                if is_app_bundle:
                    plist_path = os.path.join(UNITY_EXECUTABLE, "Contents", "Info.plist")
                    # unity_path_ok remains True
                elif is_likely_binary:
                    app_bundle_path_parts = UNITY_EXECUTABLE.replace("\\", "/").split(".app/")
                    if len(app_bundle_path_parts) > 0:
                        app_bundle_path = app_bundle_path_parts[0] + ".app"
                        if os.path.isdir(app_bundle_path): plist_path = os.path.join(app_bundle_path, "Contents", "Info.plist"); # unity_path_ok remains True
                        else: unity_path_ok = False; results.append(f"❌ Unity Exe: Path seems like internal binary, but couldn't find '.app' bundle.") # <<< CORRIGE GLOBAL
                    else: unity_path_ok = False; results.append(f"❌ Unity Exe: Path is a file but not recognized as Unity binary within a .app bundle.") # <<< CORRIGE GLOBAL
                else: unity_path_ok = False; results.append(f"❌ Unity Exe: Path is not a valid '.app' bundle or recognized executable on macOS:\n    '{UNITY_EXECUTABLE}'") # <<< CORRIGE GLOBAL
                if unity_path_ok and plist_path and os.path.exists(plist_path):
                    try:
                        with open(plist_path, 'rb') as fp: plist_data = plistlib.load(fp)
                        detected_version = plist_data.get('CFBundleShortVersionString', plist_data.get('CFBundleVersion'))
                        if detected_version:
                             results.append(f"ℹ️ Unity Ver: Found version '{detected_version}' in Info.plist.")
                             if detected_version == req_ver: unity_version_ok = True; results.append(f"✅ Unity Ver: Info.plist version matches required '{req_ver}'.") # <<< ACTUALIZA GLOBAL
                             else: results.append(f"❌ Unity Ver: Info.plist version '{detected_version}' does NOT match required '{req_ver}'.") # unity_version_ok remains False
                        else: results.append(f"⚠️ Unity Ver: Could not find version string in Info.plist at '{plist_path}'.")
                    except Exception as plist_err: results.append(f"⚠️ Unity Ver: Error reading Info.plist '{plist_path}'. Error: {plist_err}")
                elif unity_path_ok: results.append(f"⚠️ Unity Ver: Could not verify version via Info.plist for path '{UNITY_EXECUTABLE}'. Version check skipped.")
            else: # Linux u otro OS
                 results.append(f"⚠️ Unity Ver: Verification for {current_os} not fully implemented (only checks if path exists).")
                 if os.path.isfile(UNITY_EXECUTABLE):
                     # unity_path_ok remains True if it's a file
                     if req_ver in UNITY_EXECUTABLE: unity_version_ok = True; results.append(f"✅ Unity Ver: Path contains required version string '{req_ver}'.") # <<< ACTUALIZA GLOBAL
                     else: results.append(f"❌ Unity Ver: Path does not contain required version string '{req_ver}'.") # unity_version_ok remains False
                 else: unity_path_ok = False; results.append(f"❌ Unity Exe: Path is not a valid file on {current_os}.") # <<< CORRIGE GLOBAL
        except Exception as ver_err:
            results.append(f"⚠️ Unity Ver: Unexpected error during version check: {ver_err}")
            print(f"Version check error: {ver_err}"); traceback.print_exc()

    # --- Verify Unity Projects Path ---
    if not UNITY_PROJECTS_PATH:
        results.append("❌ Proj Path: Not defined.")
    elif not Path(UNITY_PROJECTS_PATH).is_dir():
        results.append(f"❌ Proj Path: Invalid:\n '{UNITY_PROJECTS_PATH}'")
    else:
        unity_projects_path_ok = True # <<< ACTUALIZA GLOBAL
        results.append("✅ Proj Path: OK.")
        # Establecer rutas derivadas como objetos Path
        base = Path(UNITY_PROJECTS_PATH)
        SIM_PROJ = base / SIMULATION_PROJECT_NAME
        ASSETS = SIM_PROJ / "Assets"
        STREAM = ASSETS / "StreamingAssets"
        STATE_F = STREAM / "simulation_loaded.txt"
        # Asignar objetos Path directamente a globales
        SIMULATION_PROJECT_PATH = SIM_PROJ
        ASSETS_FOLDER = ASSETS
        STREAMING_ASSETS_FOLDER = STREAM
        SIMULATION_LOADED_FILE = STATE_F
        # Leer último cargado (verificar si la función existe)
        read_func = globals().get('read_last_loaded_simulation_name')
        if read_func and callable(read_func):
            last_simulation_loaded = read_func()
        else:
            last_simulation_loaded = None

    # --- Verify API (using external API server) ---
    if not API_BASE_URL:
        results.append("❌ API URL: Not defined.")
        results.append("   ↳ Cannot check OpenAI / Server.")
        # apis_key_ok and apis_models_ok permanecen False
    else:
        results.append(f"ℹ️ API URL: {API_BASE_URL}")
        url = f"{API_BASE_URL.rstrip('/')}/verify_config"
        try:
            if not API_KEY: # Clave API del cliente
                 results.append("❌ Client API Key: Not defined in .env.")
                 results.append("   ↳ Cannot check OpenAI / Server Auth.")
                 raise ValueError("Local API_KEY not configured for /verify_config call")

            headers = {'X-API-Key': API_KEY}
            print(f" Verifying->{url} (with Client API Key)...")

            # Verificar si la librería 'requests' está disponible
            if 'requests' in sys.modules:
                resp = requests.get(url, headers=headers, timeout=15)
                resp.raise_for_status()
                data = resp.json()
                print(f" Verifying<-{data}")

                # Actualizar flags GLOBALES basados en la respuesta del servidor
                apis_key_ok = data.get('openai_api_key_ok', False) # Clave OpenAI (en servidor)
                primary_model_ok = data.get('primary_model_ok', False)
                # secondary_model_ok = data.get('secondary_model_ok', False) # No crucial para estado OK?
                apis_models_ok = apis_key_ok and primary_model_ok # API OK si clave OpenAI y modelo primario OK

                # Añadir detalles de la respuesta del servidor
                dets = data.get('verification_details', {})
                results.append(dets.get('openai_api_key_status', '❌ OpenAI Key Status (Server): ?'))
                results.append(dets.get('api_server_key_status', '❌ Server Auth Key Status: ?')) # Estado de la clave Cliente
                results.append(dets.get('primary_model_status', '❌ Primary Model (Server): ?'))
                results.append(dets.get('secondary_model_status', '❌ Secondary Model (Server): ?'))

                # Corregir estado si la clave del cliente falló la autenticación en el servidor
                server_auth_status = dets.get('api_server_key_status', '')
                if "OK" not in server_auth_status and "Configured" not in server_auth_status and "✅" not in server_auth_status:
                     apis_key_ok = False # Si la clave del cliente es mala, la API no está OK
                     apis_models_ok = False

            else:
                results.append("❌ API Serv Check: 'requests' library not imported/available.")
                # apis_key_ok, apis_models_ok permanecen False

        except ValueError as ve:
            print(f" Local error before calling API: {ve}")
            # apis_key_ok, apis_models_ok permanecen False
        except requests.exceptions.ConnectionError:
            results.append(f"❌ API Serv Check: CONNECTION FAILED! ({API_BASE_URL}). Is api.py running?")
            apis_key_ok = apis_models_ok = False
        except requests.exceptions.Timeout:
            results.append(f"❌ API Serv Check: TIMEOUT! ({API_BASE_URL}).")
            apis_key_ok = apis_models_ok = False
        except requests.exceptions.RequestException as e:
            results.append(f"❌ API Serv Check: Request error to {url}.")
            err_b = f"{type(e).__name__}:{e}"; sc = "???"
            if e.response is not None:
                sc = str(e.response.status_code)
                try: err_b = e.response.json().get('error', e.response.text)
                except: err_b = e.response.text[:200] + "..."
                if sc == '403': results.append(f"   ↳ Server Error(403): Access DENIED to /verify_config. Is client API_KEY correct?")
                else: results.append(f"   ↳ Server Error({sc}): {err_b}")
            else: results.append(f"   ↳ {err_b}")
            apis_key_ok = apis_models_ok = False
        except Exception as e:
             results.append(f"❌ API Serv Check: Unexpected error: {type(e).__name__}")
             print(f"--- CRITICAL ERROR verify_config call ---\n{traceback.format_exc()}\n--- End Error ---")
             apis_key_ok = apis_models_ok = False

    # --- Final Status Update ---
    # !!! ELIMINADA la línea que sobrescribía globales con locales !!!

    initial_verification_complete = True # Marcar verificación como completada

    # Calcular string de estado usando las variables GLOBALES actualizadas
    # <<< CORREGIDO: Usa globales >>>
    u_stat = "Unity OK" if unity_path_ok and unity_version_ok and unity_projects_path_ok else "Unity ERR"
    a_stat = "API OK" if apis_key_ok and apis_models_ok else "API ERR"
    status = f"Status:{u_stat} | {a_stat}"

    # --- Actualizar GUI y mostrar resultados ---
    main_window_obj = globals().get('main_window')
    if main_window_obj and isinstance(main_window_obj, tk.Tk) and hasattr(main_window_obj, 'winfo_exists') and main_window_obj.winfo_exists():
        update_status_func = globals().get('update_status')
        if update_status_func and callable(update_status_func):
             main_window_obj.after(0, lambda s=status: update_status_func(s))

        update_buttons_func = globals().get('update_button_states')
        if update_buttons_func and callable(update_buttons_func):
             main_window_obj.after(50, update_buttons_func)

        # Recargar lista de simulaciones si la ruta de proyectos es válida
        if unity_projects_path_ok: # Usar global
             get_sims_func = globals().get('get_simulations')
             if get_sims_func and callable(get_sims_func):
                  all_simulations_data = get_sims_func()
             else: print("Warning: get_simulations function not available.")

             filter_sims_func = globals().get('filter_simulations')
             if filter_sims_func and callable(filter_sims_func):
                  main_window_obj.after(100, filter_sims_func)
             else: print("Warning: filter_simulations function not available for GUI update.")

        # Mostrar errores de inicio si aplica
        if on_startup:
            errs = []
            api_err_flag = False
            # Comprobar estado de Unity con globales
            if not unity_path_ok or not unity_projects_path_ok: errs.append("- Unity paths not OK.")
            elif not unity_version_ok: errs.append(f"- Unity Version/Path not OK (req:'{req_ver}').")
            if not unity_path_ok or not unity_version_ok or not unity_projects_path_ok: errs.append("  (Unity features might fail)")
            # Comprobar estado de API con globales
            if not API_BASE_URL: errs.append("- API URL not configured."); api_err_flag=True
            elif not apis_key_ok: errs.append("- API Server: API Key/Auth Error."); api_err_flag=True
            elif not apis_models_ok: errs.append("- API Server: Primary Model Error."); api_err_flag=True
            if api_err_flag: errs.append("  (API Creation/Verification OFF)")
            # Mostrar mensaje si hay errores
            if errs:
                msg = "Initial Config Problems:\n\n" + "\n".join(errs) + "\n\nUse 'Settings'(local) and verify 'api.py'/'api.env'."
                msgbox_func = globals().get('messagebox')
                if msgbox_func and callable(msgbox_func.showwarning):
                     main_window_obj.after(300, lambda m=msg: msgbox_func.showwarning("Config Problems", m, parent=main_window_obj))
                else:
                     print(f"Config Problems (no GUI): {msg}")
    else: # No GUI
         print(f"Verification Status (no GUI): {status}")

    # Mostrar resultados detallados si se pidió
    if show_results:
         txt = "Verification Results:\n\n---Local---\n" + "\n".join([r for r in results if "Unity" in r or "Proj" in r or "URL" in r]) + \
               "\n\n---OpenAI & Server Auth (via API)---\n" + "\n".join([r for r in results if "API" in r or "Model" in r or "?" in r or "Server" in r or "OpenAI" in r]) # Filtro mejorado
         # Usar variables GLOBALES para el estado general final
         # <<< CORREGIDO: Usa globales >>>
         all_ok = unity_path_ok and unity_version_ok and unity_projects_path_ok and apis_key_ok and apis_models_ok
         main_window_obj_results = globals().get('main_window')
         msgbox_func_results = globals().get('messagebox')
         if main_window_obj_results and isinstance(main_window_obj_results, tk.Tk) and hasattr(main_window_obj_results, 'winfo_exists') and main_window_obj_results.winfo_exists() and msgbox_func_results and callable(msgbox_func_results.showinfo):
             mt = msgbox_func_results.showinfo if all_ok else msgbox_func_results.showwarning
             tl = "Verification OK" if all_ok else "Verification Problems"
             main_window_obj_results.after(0, lambda t=tl, m=txt: mt(t, m, parent=main_window_obj_results))
         else: # No GUI
             print("\nVerification Results (no GUI):")
             print(txt)
             print(f"\nOverall Status: {'OK' if all_ok else 'PROBLEMS'}")

# ======================================================
# Configuration Window
# ======================================================
def open_config_window():
    cfg=ctk.CTkToplevel(main_window); cfg.title("Settings (Local)"); apply_icon(cfg); center_window(cfg,700,250); cfg.resizable(False,False); cfg.transient(main_window); cfg.grab_set(); frame=ctk.CTkFrame(cfg); frame.pack(fill="both",expand=True,padx=20,pady=20); frame.grid_columnconfigure(1,weight=1); entries:Dict[str,ctk.StringVar]={}
    def create_row(r,lbl,var,key,isf=True,isp=True):
        ctk.CTkLabel(frame,text=lbl,anchor="w",font=APP_FONT).grid(row=r,column=0,padx=(0,10),pady=5,sticky="w")
        val=os.getenv(var,""); ev=ctk.StringVar(value=val); entries[key]=ev; ew=ctk.CTkEntry(frame,textvariable=ev,font=APP_FONT); ew.grid(row=r,column=1,padx=5,pady=5,sticky="ew")
        if isp:
            def browse():
                init="/"; cur=ev.get();
                if cur: p=Path(cur); init=str(p.parent) if p.is_file() else (str(p) if p.is_dir() else (str(p.parent) if p.parent.is_dir() else "/"))
                path=filedialog.askopenfilename(title=f"Select {lbl}",initialdir=init,parent=cfg) if isf else filedialog.askdirectory(title=f"Select {lbl}",initialdir=init,parent=cfg);
                if path: ev.set(str(Path(path).resolve()))
            bb=ctk.CTkButton(frame,text="...",width=30,command=browse,font=APP_FONT); bb.grid(row=r,column=2,padx=(5,0),pady=5)
        else: frame.grid_columnconfigure(2,weight=0,minsize=35)
    create_row(0,"Unity Exe:","UNITY_EXECUTABLE","unity_exe",True,True)
    create_row(1,"Unity Proj Fldr:","UNITY_PROJECTS_PATH","projects_path",False,True)
    create_row(2,"API Server URL:","API_BASE_URL","api_url",False,False)
    create_row(3,"API Key (Client):", "API_KEY", "api_key", False, False)
    bf=ctk.CTkFrame(cfg,fg_color="transparent"); bf.pack(fill="x",padx=20,pady=(0,20)); bf.columnconfigure((0,3),weight=1); bf.columnconfigure((1,2),weight=0)
    def save():
        global API_KEY
        ue=entries['unity_exe'].get().strip()
        pp=entries['projects_path'].get().strip()
        au=entries['api_url'].get().strip()
        ak=entries['api_key'].get().strip()

        if not ue or not Path(ue).is_file(): messagebox.showerror("Error","Unity Exe path not OK.", parent=cfg); return
        if not pp or not Path(pp).is_dir(): messagebox.showerror("Error","Proj path not OK.", parent=cfg); return
        if not au or not (au.startswith("http://") or au.startswith("https://")): messagebox.showerror("Error","API URL not OK (http(s)://...).", parent=cfg); return
        if not ak:
            messagebox.showwarning("Warning", "The API Key (Client) field is empty.\nAuthentication with the API server will fail.", parent=cfg)

        try:
            content = f"UNITY_EXECUTABLE={ue}\nUNITY_PROJECTS_PATH={pp}\nAPI_BASE_URL={au}\nAPI_KEY={ak}\n"
            Path(".env").write_text(content,"utf-8")
            API_KEY = ak
            print(f"API_KEY (Client) in-memory updated: {'Configured' if API_KEY else 'EMPTY!!'}")
            messagebox.showinfo("OK","Local config OK.\nRe-verifying...", parent=cfg)
            cfg.destroy()
            main_window.after(100,lambda: threading.Thread(target=perform_verification, args=(True, False), daemon=True).start())

        except Exception as e:
             messagebox.showerror("Save Error",f"Failed to write .env:\n{e}", parent=cfg)

    idx=get_color_mode_index(); saveb=ctk.CTkButton(bf,text="Save & Verify",command=save,font=APP_FONT,fg_color=COLOR_SUCCESS_GENERAL[idx],hover_color=COLOR_INFO_GENERAL[idx]); saveb.grid(row=0,column=1,padx=10,pady=10); cancelb=ctk.CTkButton(bf,text="Cancel",command=cfg.destroy,font=APP_FONT,fg_color=COLOR_WARNING_GENERAL[idx],hover_color=COLOR_DANGER_GENERAL[idx]); cancelb.grid(row=0,column=2,padx=10,pady=10)

# ======================================================
# GUI Definitions & Callbacks
# ======================================================
def populate_simulations():
    if not initial_verification_complete: print("[Pop] Skip: !Verif."); return
    if 'sim_tree' not in globals() or not sim_tree.winfo_exists(): print("[Pop] Err: !Treeview."); return
    update_status("Reloading sims...")
    global all_simulations_data, last_simulation_loaded
    all_simulations_data = get_simulations()
    last_simulation_loaded = read_last_loaded_simulation_name()
    all_simulations_data.sort(key=lambda x: x.get('name', '').lower())
    filter_simulations()
def filter_simulations(e=None):
    if 'sim_tree' not in globals() or 'search_entry' not in globals():
        print("[Filter] Err: !Widgets sim_tree or search_entry not found.")
        return
    term = search_entry.get().lower().strip()
    count = 0
    try:
        items = sim_tree.get_children()
        if items:
            sim_tree.delete(*items)
    except tk.TclError:
        print("[Filter] Warn: Tcl error clearing treeview, window likely closing.")
        return
    for i, sim in enumerate(all_simulations_data):
        name = sim.get('name', f'sim_{i}')
        if not name:
            print(f"[Filter] Warn: Nameless simulation found at index {i}. Skipping.")
            continue

        if term and term not in name.lower():
            continue

        loaded = (name == last_simulation_loaded)
        tag = "even" if count % 2 == 0 else "odd"
        tags = [tag]
        if loaded:
            tags.append("loaded")

        ls = loaded_indicator_text if loaded else ""
        ps = play_icon_text
        ds = delete_icon_text

        try:
            sim_tree.insert(
                "",
                "end",
                iid=name,
                values=(
                    name,
                    sim.get("creation","?"),
                    sim.get("last_opened","Never"),
                    ls,
                    ps,
                    ds
                ),
                tags=tuple(tags)
            )
        except tk.TclError as te:
            print(f"Err inserting simulation '{name}' into treeview: {te}")
            continue
        count += 1

    total = len(all_simulations_data)
    filter_part = ''
    if term:
        filter_part = ' (filter: "{}")'.format(term)

    msg = ""
    if initial_verification_complete:
        msg = f"Showing {count}/{total}{filter_part}."
    else:
        msg = "Waiting for initial verification..."

    prefix = ""
    if 'status_label' in globals() and status_label:
        try:
            cur_stat = status_label.cget("text")
            if "Status:" in cur_stat:
                parts = cur_stat.split("|")
                prefix = f"{parts[0].strip()} | {parts[1].strip()} | " if len(parts) > 1 else f"{parts[0].strip()} | "
        except tk.TclError:
             print("[Filter] Warn: Tcl error getting status_label text.")
             prefix = ""
        except Exception as e:
             print(f"[Filter] Warn: Unexpected error getting status_label text: {e}")
             prefix = ""

    update_status(f"{prefix}{msg}")

    if 'last_sort_column' in globals() and last_sort_column:
         if last_sort_column in sort_order:
             reverse = sort_order.get(last_sort_column, False)
             sort_column(sim_tree, last_sort_column, reverse)
         else:
              print(f"[Filter] Warn: last_sort_column '{last_sort_column}' is not a sortable column.")
    else:
        pass

    update_button_states()
def clear_search():
    if 'search_entry' in globals() and search_entry:
        search_entry.delete(0, 'end')
        filter_simulations()
def update_button_states():
    if 'main_window' not in globals() or not main_window or not hasattr(main_window, 'winfo_exists') or not main_window.winfo_exists() or is_build_running:
        return
    sel = bool(sim_tree.selection()) if 'sim_tree' in globals() and sim_tree else False
    api_ok = apis_key_ok and apis_models_ok
    unity_ok = unity_path_ok and unity_version_ok and unity_projects_path_ok
    def get_s(en: bool) -> str:
        return "normal" if en and not is_build_running else "disabled"

    widget_conditions = {
        'reload_btn': True, 'graph_btn': sel, 'create_btn': api_ok,
        'verify_btn': True, 'settings_btn': True, 'about_btn': True,
        'unity_down_btn': True, 'theme_switch': True, 'exit_btn': True,
        'search_entry': True, 'clear_search_btn': True
    }

    try:
        for name, condition in widget_conditions.items():
            widget = globals().get(name)
            if widget and hasattr(widget, 'configure'):
                widget.configure(state=get_s(condition))
    except Exception as e:
        print(f"Warn: Upd button states: {e}")

def on_load_simulation_request(sim: str):
    global is_build_running
    if is_build_running:
        print("[LoadReq] Skip: Build ON.")
        return
    print(f"Req Load/Run:{sim}")
    if not all([unity_path_ok, unity_version_ok, unity_projects_path_ok]):
        if 'messagebox' in globals() and messagebox: messagebox.showerror("Unity Config Error", "Cannot Load: Unity config not OK.")
        else: print("Unity Config Error: Cannot Load: Unity config not OK.")
        return
    if sim == last_simulation_loaded:
        update_status(f"'{sim}' already loaded. Options...")
        print(f"'{sim}' already OK. Options...")
        update_last_opened(sim)
        _, exe = get_build_target_and_executable(str(SIMULATION_PROJECT_PATH))
        if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'show_options_window' in globals() and show_options_window:
             main_window.after(0, lambda s=sim, p=exe: show_options_window(s, p))
        return
    disable_all_interactions()
    update_status(f"Initiating load+build '{sim}'...")
    threading.Thread(target=load_simulation_logic, args=(sim,), daemon=True).start()
def load_simulation_logic(sim: str):
    load_ok = False
    build_init = False
    try:
        update_status(f"Load'{sim}':Closing Unity...")
        ensure_unity_closed()
        update_status(f"Load'{sim}':Copying...")
        load_ok = load_simulation(sim)
        if load_ok:
            update_status(f"Load'{sim}':Prefabs...")
            prefab_ok = run_prefab_material_tool()
            if prefab_ok:
                update_status(f"Load'{sim}':Build...")
                build_init = True
                build_simulation_threaded(callback=lambda ok, p: build_callback(ok, sim, p))
            else:
                update_status(f"Err prefabs'{sim}'.Build OFF.")
                if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'messagebox' in globals() and messagebox: main_window.after(0, lambda: messagebox.showerror("Post-Load Error", f"Prefabs failed for'{sim}'.\nBuild OFF."))
        else:
            update_status(f"Err loading files'{sim}'.Stopping.")
    except Exception as e:
        print(f"CRIT ERROR load_sim_logic'{sim}':{e}\n{traceback.format_exc()}")
        update_status(f"Critical load error'{sim}'.")
        if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'messagebox' in globals() and messagebox: main_window.after(0, lambda: messagebox.showerror("Critical Load Error", f"Unexpected error loading'{sim}'.\n\n{type(e).__name__}"))
    finally:
        if not build_init:
            if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'enable_all_interactions' in globals() and enable_all_interactions: main_window.after(10, enable_all_interactions)
            print("[Load Logic] Finish (no build). Interact ON.")
def build_callback(ok: bool, sim: str, exe: Optional[Path]):
    print(f"Callback Build'{sim}'.OK:{ok},Exe:{exe}")
    if ok and exe and exe.exists():
        update_status(f"Build'{sim}'OK.")
        show_options_window(sim, exe)
    elif ok:
        msg = f"Build'{sim}'OK, but exe not found:\n{exe or 'Path unknown'}\n\nCheck logs."
        update_status(f"Build Error:!Output'{sim}'.")
        if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'messagebox' in globals() and messagebox: messagebox.showerror("Build Error", msg, parent=main_window)
    else:
        update_status(f"Build'{sim}'failed. Check logs.")
def on_delete_simulation_request(sim: str):
    global is_build_running
    if is_build_running:
        print("[Delete Req] Skip: Build ON.")
        return
    print(f"Req Delete:{sim}")
    delete_simulation(sim) 
def on_show_graphs_thread():
    global is_build_running
    if is_build_running: return
    if 'sim_tree' not in globals() or not sim_tree or not sim_tree.winfo_exists(): return
    sel = sim_tree.selection()
    if not sel:
        if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'messagebox' in globals() and messagebox: messagebox.showwarning("!Selected", "Select sim for stats.", parent=main_window)
        return
    sim = sim_tree.item(sel[0], "values")[0]
    disable_all_interactions()
    update_status(f"Graphs'{sim}'...")
    threading.Thread(target=show_graphs_logic, args=(sim,), daemon=True).start()
def show_graphs_logic(sim: str):
    out: Optional[Path] = None
    try:
        print(f"Graphs'{sim}'...")
        if 'SimulationGraphics' in globals() and SimulationGraphics:
             out = SimulationGraphics(sim)
        else:
             print("Warning: SimulationGraphics class not available.")

        if out:
            update_status(f"Graphs'{sim}'OK.")
            print(f"Opening:{out}")
            if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'open_graphs_folder' in globals() and open_graphs_folder: main_window.after(0, lambda n=sim: open_graphs_folder(n))
            else: print("Warning: open_graphs_folder function not available for GUI.")
        else:
            update_status(f"!Graphs'{sim}'.")
    except Exception as e:
        msg = f"Unexpected graphs error'{sim}':\n{e}"
        print(f"Err show_graphs:{msg}\n{traceback.format_exc()}")
        if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'messagebox' in globals() and messagebox: main_window.after(0, lambda: messagebox.showerror("Graphs Error", msg, parent=main_window))
        update_status(f"Graphs error'{sim}'.")
    finally:
        if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'enable_all_interactions' in globals() and enable_all_interactions: main_window.after(50, enable_all_interactions)
        print(f"Graphs thread'{sim}'finished.")
def on_create_simulation():
    global is_build_running
    if is_build_running: return
    if not apis_key_ok or not apis_models_ok:
        if 'messagebox' in globals() and messagebox:
            messagebox.showerror("API Config Error", "Cannot Create:\nAPI Server reports problems (key/model) or no response.\n\nVerify 'api.py'/'api.env'.", parent=main_window)
        else:
            print("API Config Error: Cannot Create:\nAPI Server reports problems (key/model) or no response.\n\nVerify 'api.py'/'api.env'.")
        return
    name = custom_askstring("Create Sim", "Unique Name:")
    if not name: update_status("Creation OFF."); return
    name = name.strip()
    inv = r'<>:"/\|?*' + ("".join(map(chr, range(32))))
    if not name or any(c in inv for c in name):
        if 'messagebox' in globals() and messagebox: messagebox.showerror("!Name", f"Name'{name}'invalid.", parent=main_window)
        else: print(f"Error: Name'{name}'invalid.")
        update_status("Err:Sim name not OK."); return
    if (SIMULATIONS_DIR / name).exists():
        if 'messagebox' in globals() and messagebox: messagebox.showerror("Sim Exists", f"Sim'{name}' already exists.", parent=main_window)
        else: print(f"Error: Sim'{name}' already exists.")
        update_status(f"Err:Sim'{name}'exists."); return
    desc = custom_askstring("Sim Description", "Describe (e.g.,'red EColi dup 20m sep 60%'):")
    if desc is None: update_status("Creation OFF."); return
    desc = desc.strip()
    if not desc: update_status("Creation OFF(!desc)."); return
    disable_all_interactions()
    update_status(f"Creating'{name}' via API...")
    threading.Thread(target=create_simulation_thread, args=(name, desc), daemon=True).start()
def show_options_window(sim: str, exe: Optional[Path]):
    if 'main_window' not in globals() or not main_window or not hasattr(main_window, 'winfo_exists') or not main_window.winfo_exists(): return
    win = ctk.CTkToplevel(main_window); win.title(f"Opts'{sim}'"); apply_icon(win); center_window(win, 380, 200); win.resizable(False, False); win.transient(main_window); win.grab_set(); frame = ctk.CTkFrame(win); frame.pack(expand=True, fill="both", padx=20, pady=20); frame.columnconfigure(0, weight=1); ctk.CTkLabel(frame, text=f"Sim'{sim}'loaded.", font=APP_FONT_BOLD).pack(pady=(0, 15)); ok = exe and exe.exists(); state = "normal" if ok else "disabled"; tip = f"Execute\n{exe}" if ok else "Exe not found."
    def run_c():
        if ok: open_simulation_executable() 
        win.destroy()
    def open_u_c():
        open_in_unity() 
        win.destroy()
    idx = get_color_mode_index()
    run = ctk.CTkButton(frame, text="Execute Sim", command=run_c, state=state, font=APP_FONT, height=40, fg_color=COLOR_SUCCESS_GENERAL[idx], hover_color=COLOR_INFO_GENERAL[idx]); run.pack(pady=8, fill="x", padx=10); run.bind("<Enter>", lambda e, t=tip: schedule_tooltip(run, t)); run.bind("<Leave>", lambda e: cancel_tooltip(run))
    open_u = ctk.CTkButton(frame, text="Open in Unity Editor", command=open_u_c, font=APP_FONT, height=40, fg_color="#1E88E5", hover_color="#42A5F5"); open_u.pack(pady=8, fill="x", padx=10); open_u.bind("<Enter>", lambda e: schedule_tooltip(open_u, "Opens Unity base project")); open_u.bind("<Leave>", lambda e: cancel_tooltip(open_u))
    update_status(f"Opts for'{sim}'."); win.protocol("WM_DELETE_WINDOW", win.destroy); win.wait_window()
def handle_tree_click(event):
    global is_build_running
    if is_build_running or 'sim_tree' not in globals() or not sim_tree: return
    region = sim_tree.identify_region(event.x, event.y)
    if region == "cell":
        item = sim_tree.identify_row(event.y)
        col = sim_tree.identify_column(event.x)
        if not item or not col:
            cancel_tooltip(sim_tree)
            return
        try:
            idx = int(col.replace('#', '')) - 1
            name_id = sim_tree['columns'][idx]
            sim_tree.selection_set(item)
            sim_tree.focus(item)
            update_button_states()
            hide_tooltip()
            if name_id == "col_load":
                can = unity_path_ok and unity_version_ok and unity_projects_path_ok
                if can:
                    print(f"Click Load/Run'{item}'")
                    on_load_simulation_request(item)
                else:
                    print(f"Click Ign Load/Run'{item}'(Unity!OK)")
                    if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists() and 'messagebox' in globals() and messagebox: messagebox.showwarning("Disabled", "Cannot load/run.\nVerify Unity config.", parent=main_window)
            elif name_id == "col_delete":
                print(f"Click Delete'{item}'")
                on_delete_simulation_request(item)
        except (IndexError, ValueError, tk.TclError) as e:
            print(f"Err Tree click:{e}")
            cancel_tooltip(sim_tree)
        except Exception as e:
            print(f"Unexpected Tree click error:{e}\n{traceback.format_exc()}")
            cancel_tooltip(sim_tree)
    elif region == "heading":
        pass 
    else:
        cancel_tooltip(sim_tree)
def handle_tree_motion(event):
    global is_build_running
    if is_build_running or 'sim_tree' not in globals() or not sim_tree: return
    region = sim_tree.identify_region(event.x, event.y)
    if region != "cell":
        cancel_tooltip(sim_tree)
        return
    col = sim_tree.identify_column(event.x)
    item = sim_tree.identify_row(event.y)
    if not col or not item:
        cancel_tooltip(sim_tree)
        return
    try:
        idx = int(col.replace('#', '')) - 1
        if 0 <= idx < len(sim_tree['columns']):
            name_id = sim_tree['columns'][idx]
            tip = None
            sim = sim_tree.item(item, 'values')[0]
            if name_id == "col_load":
                tip = f"Load/Run'{sim}'" if unity_path_ok and unity_version_ok and unity_projects_path_ok else "Load/Run (Unity not OK)"
            elif name_id == "col_delete":
                tip = f"Delete'{sim}'"
            elif name_id == "col_loaded" and sim_tree.set(item, name_id) == loaded_indicator_text:
                tip = f"'{sim}' loaded."

            if tip:
                schedule_tooltip(sim_tree, tip) 
            else:
                cancel_tooltip(sim_tree) 
        else:
            cancel_tooltip(sim_tree)
    except Exception:
        cancel_tooltip(sim_tree)
def handle_tree_leave(event):
    cancel_tooltip(sim_tree)
def load_logo(path_s: str, width: int) -> Union[ImageTk.PhotoImage, None]:
    global logo_photo_ref
    try:
        p = Path(path_s)
        if not p.is_file():
            print(f"WARN:Logo not found'{p}'")
            return None
        img = Image.open(p)
        wp = width / float(img.size[0])
        h = int(img.size[1] * wp)
        res = img.resize((width, h), Image.Resampling.LANCZOS)
        logo_photo_ref = ImageTk.PhotoImage(res)
        return logo_photo_ref
    except Exception as e:
        print(f"Err load logo'{path_s}':{e}")
        return None
def update_treeview_style():
    if 'sim_tree' not in globals() or 'main_window' not in globals() or not main_window or not hasattr(main_window, 'winfo_exists') or not main_window.winfo_exists(): return
    idx = get_color_mode_index(); mode = "Dark" if idx == 1 else "Light"; print(f"Update Tree style {mode}...")
    try:
        bg = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        fg = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        sel_bg = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        sel_fg = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["text_color"])
        head_bg = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["border_color"])
        head_fg = fg
        odd = "#F0F0F0" if mode == "Light" else "#3A3A3A"
        even = bg
        loaded_bg = "#D5F5D5" if mode == "Light" else "#284B28"
        style = ttk.Style()
        try:
            if 'clam' in style.theme_names(): style.theme_use("clam")
        except tk.TclError: print("WARN: Tema 'clam' not available.")
        style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg, rowheight=28, font=TREEVIEW_FONT)
        style.configure("Treeview.Heading", font=TREEVIEW_HEADER_FONT, background=head_bg, foreground=head_fg, relief="flat", padding=(10, 5))
        style.map("Treeview.Heading", relief=[('active', 'flat'), ('!active', 'flat')])
        style.map('Treeview', background=[('selected', sel_bg)], foreground=[('selected', sel_fg)])
        sim_tree.tag_configure('oddrow', background=odd, foreground=fg)
        sim_tree.tag_configure('evenrow', background=even, foreground=fg)
        sim_tree.tag_configure('loaded', background=loaded_bg, foreground=fg, font=TREEVIEW_FONT)
        print("Tree style OK.")
        sim_tree.update_idletasks()
    except Exception as e: print(f"Err update tree style:{e}\n{traceback.format_exc()}")
def toggle_appearance_mode():
    new = "Dark" if ctk.get_appearance_mode() == "Light" else "Light"; print(f"Mode->{new}"); ctk.set_appearance_mode(new);
    if 'theme_switch' in globals() and theme_switch: theme_switch.configure(text=f"{new} Mode"); main_window.after(50, update_dynamic_styles) 
def update_dynamic_styles():
    idx = get_color_mode_index()
    try:
        logo = load_logo(LOGO_PATHS[idx], LOGO_WIDTH - 20)
        if logo and 'logo_label' in globals() and logo_label and hasattr(logo_label, 'winfo_exists') and logo_label.winfo_exists():
            logo_label.configure(image=logo)
            logo_label.image = logo

    except Exception as e:
        print(f"Err upd logo: {e}")

    update_treeview_style()

    try:
        colors = {
            "settings": (BTN_SETTINGS_FG_COLOR, BTN_SETTINGS_HOVER_COLOR, BTN_SETTINGS_TEXT_COLOR),
            "verify": (BTN_VERIFY_FG_COLOR, BTN_VERIFY_HOVER_COLOR, BTN_VERIFY_TEXT_COLOR),
            "unity_down": (BTN_UNITY_DOWN_FG_COLOR, BTN_UNITY_DOWN_HOVER_COLOR, BTN_UNITY_DOWN_TEXT_COLOR),
            "about": (BTN_ABOUT_FG_COLOR, BTN_ABOUT_HOVER_COLOR, BTN_ABOUT_TEXT_COLOR),
            "exit": (BTN_EXIT_FG_COLOR, BTN_EXIT_HOVER_COLOR, BTN_EXIT_TEXT_COLOR),
            "reload": (BTN_RELOAD_FG_COLOR, BTN_RELOAD_HOVER_COLOR, BTN_RELOAD_TEXT_COLOR),
            "graph": (BTN_GRAPH_FG_COLOR, BTN_GRAPH_HOVER_COLOR, BTN_GRAPH_TEXT_COLOR),
            "create": (BTN_CREATE_FG_COLOR, BTN_CREATE_HOVER_COLOR, BTN_CREATE_TEXT_COLOR),
            "clear_search": (BTN_CLEARSEARCH_FG_COLOR, BTN_CLEARSEARCH_HOVER_COLOR, BTN_CLEARSEARCH_TEXT_COLOR),
        }

        for name, (fg_colors, hover_colors, text_colors) in colors.items():
            button_widget = globals().get(f"{name}_btn")
            if button_widget and hasattr(button_widget, 'configure'):
                button_widget.configure(
                    fg_color=fg_colors[idx],
                    hover_color=hover_colors[idx],
                    text_color=text_colors[idx]
                )

        print("Btn colors OK.")

    except Exception as e:
        print(f"Err upd btn colors: {e}")

# ======================================================
# GUI Setup
# ======================================================
main_window = ctk.CTk()
apply_icon(main_window) 
main_window.title("Unity Simulation Manager v1.1.3 (API Client)") 
initial_width = 1050
initial_height = 700
center_window(main_window, initial_width, initial_height) 
main_window.resizable(True, True)
main_window.minsize(850, 550)
main_window.columnconfigure(1, weight=1)
main_window.rowconfigure(0, weight=1)

sidebar_w = 200
sidebar_fg = COLOR_SIDEBAR_BG if COLOR_SIDEBAR_BG else ctk.ThemeManager.theme["CTkFrame"]["fg_color"]
sidebar_frame = ctk.CTkFrame(main_window, width=sidebar_w, corner_radius=5, fg_color=sidebar_fg)
sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
sidebar_frame.grid_propagate(False)
sidebar_frame.columnconfigure(0, weight=1)
mode_idx = get_color_mode_index() 
initial_mode = ctk.get_appearance_mode()
logo_photo = load_logo(LOGO_PATHS[mode_idx], LOGO_WIDTH - 20)
logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="")
logo_label.pack(pady=(20, 10), padx=10)
if not logo_photo: logo_label.configure(text="[Logo]", font=(APP_FONT[0], 14, "italic")) 
ctk.CTkLabel(sidebar_frame, text="Menu", font=(APP_FONT[0], 16, "bold")).pack(pady=(5, 15), padx=10) 
settings_btn = ctk.CTkButton(sidebar_frame, text="Settings (.env)", command=open_config_window, font=APP_FONT, fg_color=BTN_SETTINGS_FG_COLOR[mode_idx], hover_color=BTN_SETTINGS_HOVER_COLOR[mode_idx], text_color=BTN_SETTINGS_TEXT_COLOR[mode_idx])
settings_btn.pack(fill="x", padx=15, pady=5)
verify_btn = ctk.CTkButton(sidebar_frame, text="Verify Config", command=lambda: perform_verification(show_results=True), font=APP_FONT, fg_color=BTN_VERIFY_FG_COLOR[mode_idx], hover_color=BTN_VERIFY_HOVER_COLOR[mode_idx], text_color=BTN_VERIFY_TEXT_COLOR[mode_idx])
verify_btn.pack(fill="x", padx=15, pady=5)
separator = ctk.CTkFrame(sidebar_frame, height=2, fg_color="gray")
separator.pack(fill="x", padx=15, pady=15)

class UnityHubInfoDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, msg, url):
        super().__init__(parent); self.title(title); apply_icon(self); self.resizable(False,False); self.transient(parent); self.grab_set(); self._msg=msg; self._url=url; self.grid_columnconfigure(0,weight=1); self.grid_rowconfigure(0,weight=1); ctk.CTkLabel(self,text=self._msg,font=APP_FONT,justify="left",wraplength=400).grid(row=0,column=0,columnspan=2,padx=20,pady=(20,15),sticky="w"); lf=ctk.CTkFrame(self,fg_color="transparent"); lf.grid(row=1,column=0,columnspan=2,padx=20,pady=(0,10),sticky="ew"); lf.grid_columnconfigure(1,weight=1); ctk.CTkLabel(lf,text="Hub Link:",font=APP_FONT_BOLD).grid(row=0,column=0,padx=(0,5),sticky="w"); self.le=ctk.CTkEntry(lf,font=APP_FONT); self.le.insert(0,self._url); self.le.configure(state="readonly"); self.le.grid(row=0,column=1,sticky="ew"); bf=ctk.CTkFrame(self,fg_color="transparent"); bf.grid(row=2,column=0,columnspan=2,padx=20,pady=(10,20),sticky="e"); idx=get_color_mode_index(); self.cb=ctk.CTkButton(bf,text="Copy",command=self.copy,width=100,font=APP_FONT,fg_color=BTN_RELOAD_FG_COLOR[idx],hover_color=BTN_RELOAD_HOVER_COLOR[idx]); self.cb.pack(side="left",padx=(0,10)); ob=ctk.CTkButton(bf,text="Open",command=self.open,width=100,font=APP_FONT,fg_color=BTN_GRAPH_FG_COLOR[idx],hover_color=BTN_GRAPH_HOVER_COLOR[idx]); ob.pack(side="left",padx=(0,10)); clb=ctk.CTkButton(bf,text="Close",command=self.destroy,width=80,font=APP_FONT,fg_color=COLOR_WARNING_GENERAL[idx],hover_color=COLOR_DANGER_GENERAL[idx]); clb.pack(side="left"); self.update_idletasks(); w=max(450,self.winfo_reqwidth()); h=self.winfo_reqheight(); center_window(self,w,h); self.bind("<Escape>",lambda e:self.destroy()); self.after(100,self.le.focus); self.wait_window() 
    def copy(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self._url)
            print(f"Copied: {self._url}")
            copy_button = self.cb
            original_button_text = copy_button.cget("text")
            copy_button.configure(text="Copied!", state="disabled")
            self.after(1500, lambda: copy_button.configure(text=original_button_text, state="normal"))

        except Exception as e:
            messagebox.showerror(
                "Clipboard Error",
                f"Error copying link:\n{e}", 
                parent=self
            )

    def open(self):
        try:
            webbrowser.open(self._url)
            self.destroy()

        except Exception as e:
            messagebox.showerror(
                "Browser Error", 
                f"Error opening page:\n{e}",
                parent=self
            )
def handle_unity_download_click():
    if 'UNITY_REQUIRED_VERSION_STRING' not in globals() or not UNITY_REQUIRED_VERSION_STRING: print("Err:!UNITY_REQ_VER."); messagebox.showerror("Internal Error","Unity version not configured.", parent=main_window); return
    uri=f"unityhub://{UNITY_REQUIRED_VERSION_STRING}/b2e806cf271c"; sys=platform.system(); mod=""; link=""; osn=""
    if sys=="Windows": link="https://public-cdn.cloud.unity3d.com/hub/prod/UnityHubSetup.exe"; osn="Win"; mod="- Win Build Supp (IL2CPP)"
    elif sys=="Darwin": link="https://public-cdn.cloud.unity3d.com/hub/prod/UnityHubSetup.dmg"; osn="macOS"; mod="- Mac Build Supp (Mono)"
    else: link="https://unity.com/download"; osn=sys; mod="- Platform Build Supp (verify opts)"
    instr=f"Steps to Install Unity:\n\n1. Install Hub (link below), DO NOT run.\n\n2. Close and click 'Download Unity'.\n   It should open Hub and install ver {UNITY_REQUIRED_VERSION_STRING}.\n\n3. In Hub, select:\n   - VS Community 2022\n   {mod}\n\n4. Continue install in Hub."; fallb="\n"+("-"*45)+"\n\nIf Hub did NOT open:\n- Ensure Hub is installed (link).\n- After installing Hub, try step 2."; msg=instr+fallb 
    try: print(f"Try open:{uri}"); webbrowser.open(uri);
    except Exception as e: print(f"Err open unityhub://:{e}"); messagebox.showwarning("Link Error",f"Failed to open link:\n{e}\n\nFollow manual steps.", parent=main_window)
    if 'main_window' in globals() and main_window and hasattr(main_window, 'winfo_exists') and main_window.winfo_exists(): UnityHubInfoDialog(main_window,"Unity Download Instructions",msg,link) 
    else: print(f"INFO(Fallback Dlg):{msg.replace(chr(10)+chr(10),'|').replace(chr(10),' ')} | Link:{link}")

unity_down_btn = ctk.CTkButton(sidebar_frame, text="Download Unity", command=handle_unity_download_click, font=APP_FONT, fg_color=BTN_UNITY_DOWN_FG_COLOR[mode_idx], hover_color=BTN_UNITY_DOWN_HOVER_COLOR[mode_idx], text_color=BTN_UNITY_DOWN_TEXT_COLOR[mode_idx])
unity_down_btn.pack(fill="x", padx=15, pady=5)
about_btn = ctk.CTkButton(sidebar_frame, text="About", command=lambda: messagebox.showinfo("About", "Unity Sim Mgr v1.1.3\n(API Client)\n\nBy:\nIván Cáceres S.\nTobías Guerrero Ch.", parent=main_window), font=APP_FONT, fg_color=BTN_ABOUT_FG_COLOR[mode_idx], hover_color=BTN_ABOUT_HOVER_COLOR[mode_idx], text_color=BTN_ABOUT_TEXT_COLOR[mode_idx]) 
about_btn.pack(fill="x", padx=15, pady=5)
theme_switch = ctk.CTkSwitch(sidebar_frame, text=f"{initial_mode} Mode", command=toggle_appearance_mode, font=APP_FONT)
theme_switch.pack(fill="x", side='bottom', padx=15, pady=(10, 5))
if initial_mode == "Dark": theme_switch.select()
else: theme_switch.deselect()
exit_btn = ctk.CTkButton(sidebar_frame, text="Exit", command=on_closing, font=APP_FONT, fg_color=BTN_EXIT_FG_COLOR[mode_idx], hover_color=BTN_EXIT_HOVER_COLOR[mode_idx], text_color=BTN_EXIT_TEXT_COLOR[mode_idx]) 
exit_btn.pack(fill="x", side='bottom', padx=(15, 15), pady=(5, 20))

# --- Main Content ---
main_content = ctk.CTkFrame(main_window, corner_radius=5)
main_content.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
main_content.columnconfigure(0, weight=1)
main_content.rowconfigure(2, weight=1)
header = ctk.CTkFrame(main_content, fg_color="transparent")
header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
header.columnconfigure(0, weight=1)
ctk.CTkLabel(header, text="Unity Simulation Manager", font=TITLE_FONT, anchor="center").grid(row=0, column=0, pady=(0, 10))
search = ctk.CTkFrame(main_content, fg_color="transparent")
search.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 5))
search.columnconfigure(1, weight=1)
ctk.CTkLabel(search, text="Search:", font=APP_FONT).grid(row=0, column=0, padx=(5, 5), pady=5)
search_entry = ctk.CTkEntry(search, placeholder_text="Filter...", font=APP_FONT)
search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
search_entry.bind("<KeyRelease>", filter_simulations)
clear_search_btn = ctk.CTkButton(search, text="Clear", width=60, font=APP_FONT, command=clear_search, fg_color=BTN_CLEARSEARCH_FG_COLOR[mode_idx], hover_color=BTN_CLEARSEARCH_HOVER_COLOR[mode_idx], text_color=BTN_CLEARSEARCH_TEXT_COLOR[mode_idx])
clear_search_btn.grid(row=0, column=2, padx=(5, 5), pady=5)

# --- Treeview Setup ---
tree_frame = ctk.CTkFrame(main_content, corner_radius=5)
tree_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
tree_frame.columnconfigure(0, weight=1)
tree_frame.rowconfigure(0, weight=1)
columns = ("nombre", "creacion", "ultima", "col_loaded", "col_load", "col_delete")
sim_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
sim_tree.grid(row=0, column=0, sticky="nsew")

sim_tree.heading("nombre", text="Simulation", anchor='w')
sim_tree.column("nombre", width=200, minwidth=150, anchor="w", stretch=tk.YES)
sim_tree.heading("creacion", text="Created", anchor='center') 
sim_tree.column("creacion", width=120, minwidth=100, anchor="center", stretch=tk.NO)
sim_tree.heading("ultima", text="Last Used", anchor='center')
sim_tree.column("ultima", width=120, minwidth=100, anchor="center", stretch=tk.NO)
sim_tree.heading("col_loaded", text="Loaded", anchor='center')
sim_tree.column("col_loaded", width=70, minwidth=60, stretch=tk.NO, anchor="center")
sim_tree.heading("col_load", text="Load/Run", anchor='center')
sim_tree.column("col_load", width=90, minwidth=80, stretch=tk.NO, anchor="center")
sim_tree.heading("col_delete", text="Delete", anchor='center') 
sim_tree.column("col_delete", width=70, minwidth=60, stretch=tk.NO, anchor="center")
last_sort_column: Optional[str] = None
sort_order: Dict[str, bool] = {c: False for c in columns if c not in ["col_load", "col_delete", "col_loaded"]}
def sort_column(tree: ttk.Treeview, col: str, reverse: bool):
    if col in ["col_load", "col_delete", "col_loaded"]:
        return

    global last_sort_column, sort_order

    try:
        data = [(tree.set(item, col), item) for item in tree.get_children('')]

        def get_sort_key(value_str: str):
            if col in ("creacion", "ultima"):
                if value_str in ("???", "Never") or not value_str:
                    return float('inf') if not reverse else float('-inf')
                try:
                    return time.mktime(time.strptime(value_str, "%y-%m-%d %H:%M"))
                except ValueError:
                    return 0
            else:
                return str(value_str).lower()

        data.sort(key=lambda t: get_sort_key(t[0]), reverse=reverse)

        for i, (_, item_id) in enumerate(data):
            tree.move(item_id, '', i)

        sort_order[col] = reverse
        last_sort_column = col

        for c in sort_order:
             heading_info = tree.heading(c)
             if heading_info:
                 current_text = heading_info['text'].replace(' ▲', '').replace(' ▼', '')
                 if c == col:
                     current_text += (' ▼' if reverse else ' ▲')
                 tree.heading(c, text=current_text, command=lambda c_=c: sort_column(tree, c_, not sort_order.get(c_, False)))

    except Exception as e:
        print(f"Error sorting column '{col}': {e}")
        traceback.print_exc()

for col in sort_order.keys():
    anchor = 'w' if col == 'nombre' else 'center'
    current_heading_text = sim_tree.heading(col)['text']
    sim_tree.heading(col, text=current_heading_text, anchor=anchor, command=lambda c=col: sort_column(sim_tree, c, False))

scrollbar = ctk.CTkScrollbar(tree_frame, command=sim_tree.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
sim_tree.configure(yscrollcommand=scrollbar.set)
sim_tree.bind('<<TreeviewSelect>>', lambda e: update_button_states())
sim_tree.bind("<Button-1>", handle_tree_click)
sim_tree.bind("<Motion>", handle_tree_motion)
sim_tree.bind("<Leave>", handle_tree_leave)

bottom_btns = ctk.CTkFrame(main_content, fg_color="transparent")
bottom_btns.grid(row=3, column=0, pady=(10, 10), padx=10, sticky="ew")
bottom_btns.columnconfigure((0, 4), weight=1)
bottom_btns.columnconfigure((1, 2, 3), weight=0)
btn_h = 35
reload_btn = ctk.CTkButton(bottom_btns, text="Reload List", command=populate_simulations, font=APP_FONT, height=btn_h, fg_color=BTN_RELOAD_FG_COLOR[mode_idx], hover_color=BTN_RELOAD_HOVER_COLOR[mode_idx], text_color=BTN_RELOAD_TEXT_COLOR[mode_idx])
reload_btn.grid(row=0, column=1, padx=10, pady=5)
reload_btn.bind("<Enter>", lambda e: schedule_tooltip(reload_btn, "Reloads simulation list."))
reload_btn.bind("<Leave>", lambda e: cancel_tooltip(reload_btn))
graph_btn = ctk.CTkButton(bottom_btns, text="View Stats", command=on_show_graphs_thread, font=APP_FONT, height=btn_h, fg_color=BTN_GRAPH_FG_COLOR[mode_idx], hover_color=BTN_GRAPH_HOVER_COLOR[mode_idx], text_color=BTN_GRAPH_TEXT_COLOR[mode_idx])
graph_btn.grid(row=0, column=2, padx=10, pady=5)
graph_btn.bind("<Enter>", lambda e: schedule_tooltip(graph_btn, "Generates/shows graphs for selected sim."))
graph_btn.bind("<Leave>", lambda e: cancel_tooltip(graph_btn))
create_btn = ctk.CTkButton(bottom_btns, text="Create Sim (API)", command=on_create_simulation, font=APP_FONT, height=btn_h, fg_color=BTN_CREATE_FG_COLOR[mode_idx], hover_color=BTN_CREATE_HOVER_COLOR[mode_idx], text_color=BTN_CREATE_TEXT_COLOR[mode_idx])
create_btn.grid(row=0, column=3, padx=10, pady=5)
create_btn.bind("<Enter>", lambda e: schedule_tooltip(create_btn, "Creates sim via OpenAI API (server)."))
create_btn.bind("<Leave>", lambda e: cancel_tooltip(create_btn))

# --- Status Bar ---
status_frame = ctk.CTkFrame(main_window, height=25, corner_radius=0)
status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
status_label = ctk.CTkLabel(status_frame, text="Initializing...", anchor="w", font=STATUS_FONT)
status_label.pack(side="left", fill="x", expand=True, padx=10, pady=3)

# ======================================================
# App Initialization
# ======================================================
if __name__ == "__main__":
    print("Starting Unity Sim Mgr (API Client v1.1.3)...")
    try:
        SIMULATIONS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"ERROR: Failed to create {SIMULATIONS_DIR}:{e}")
        sys.exit(1)
    main_window.after(10, update_dynamic_styles)
    main_window.after(20, update_button_states)
    update_status("Verifying initial config...")
    threading.Thread(target=perform_verification, args=(False, True), daemon=True).start()
    main_window.protocol("WM_DELETE_WINDOW", on_closing)
    main_window.mainloop()
    print("App closed.")