import sys
import os
import textwrap
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
import numpy as np
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score

if getattr(sys, 'frozen', False):
    APP_BASE_DIR = Path(sys.executable).resolve().parent.parent.parent.parent
else:
    APP_BASE_DIR = Path(__file__).resolve().parent

unity_path_ok = False
unity_version_ok = False
unity_projects_path_ok = False
apis_key_ok = False
apis_models_ok = False
initial_verification_complete = False
is_build_running = False
UNITY_EXECUTABLE = None
UNITY_PROJECTS_PATH = None
API_BASE_URL = None
API_KEY = None
UNITY_REQUIRED_VERSION_STRING = "6000.0.32f1"
SIMULATIONS_DIR = APP_BASE_DIR / "Simulations"
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
ICON_PATH_MAC = APP_BASE_DIR / "img" / "icon.icns"
LOGO_PATHS = [APP_BASE_DIR / "img" / "logo_light.png", APP_BASE_DIR / "img" / "logo_dark.png"]
LOGO_WIDTH = 200
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
APP_FONT = ("Segoe UI", 11)
APP_FONT_BOLD = ("Segoe UI", 11, "bold")
TITLE_FONT = ("Times New Roman", 22, "bold")
STATUS_FONT = ("Segoe UI", 10)
TREEVIEW_FONT = ("Segoe UI", 10)
TREEVIEW_HEADER_FONT = ("Segoe UI", 10, "bold")
COLOR_SUCCESS_GENERAL = ("#28a745", "#4CAF50")
COLOR_DANGER_GENERAL = ("#C62828", "#EF5350")
COLOR_INFO_GENERAL = ("#218838", "#66BB6A")
COLOR_WARNING_GENERAL = ("#E53935", "#E53935")
COLOR_DISABLED_GENERAL = ("#BDBDBD", "#757575")
COLOR_SIDEBAR_BG = None
settings_button_blink_job = None

def get_color_mode_index():
    return 1 if ctk.get_appearance_mode() == "Dark" else 0

_NEUTRAL_FG_COLOR = ("#A0A0A0", "#616161")
_NEUTRAL_HOVER_COLOR = ("#888888", "#757575")
_NEUTRAL_TEXT_COLOR = ("#000000", "#FFFFFF")
_BLINK_COLOR = ("#FFD900", "#FF9800")
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

UNITY_PRODUCT_NAME = "InitialSetup"
LOG_SUBFOLDER = "SimulationLoggerData"
CSV_FILENAME = "SimulationStats.csv"
GRAPHICS_SUBFOLDER = "Graphics"
DOTENV_PATH = APP_BASE_DIR / ".env"

def find_unity_persistent_path(product_name: str) -> Union[Path, None]:
    system = platform.system()
    home = Path.home()
    search_base: Union[Path, None] = None
    potential_paths: list[Path] = []
    try:
        if system == "Darwin":
            search_base = home / 'Library' / 'Application Support'
        else:
            return None
        if not search_base or not search_base.is_dir():
            return None
        for company_dir in search_base.iterdir():
            if company_dir.is_dir():
                _potential_product_path = company_dir / product_name
                if _potential_product_path.is_dir():
                    potential_paths.append(_potential_product_path)
        if len(potential_paths) == 1:
            found_path = potential_paths[0]
            return found_path
        elif len(potential_paths) == 0:
            return None
        else:
            return None
    except PermissionError:
        return None
    except Exception:
        return None

def find_simulation_data_path(simulation_name: str) -> Union[Path, None]:
    if not simulation_name:
        return None
    product_base_path = find_unity_persistent_path(UNITY_PRODUCT_NAME)
    if not product_base_path:
        return None
    simulation_path = product_base_path / LOG_SUBFOLDER / simulation_name
    return simulation_path

def exponential_func(x, a, b):
    return a * np.exp(b * x)

def SimulationGraphics(simulation_name):
    if not simulation_name:
        return
    simulation_folder = find_simulation_data_path(simulation_name)
    if not simulation_folder:
        return
    csv_path = simulation_folder / CSV_FILENAME
    output_folder = simulation_folder / GRAPHICS_SUBFOLDER
    try:
        output_folder.mkdir(parents=True, exist_ok=True)
    except OSError:
         return
    if not csv_path.is_file():
        return
    try:
        df = pd.read_csv(csv_path, sep=";", engine="python")
        if df.empty:
             return
    except pd.errors.EmptyDataError:
         return
    except Exception:
        return
    try:
        df.columns = df.columns.str.strip()
        if "Timestamp" not in df.columns:
            return
        df["Timestamp_str"] = df["Timestamp"].astype(str).str.strip()
        df = df[df["Timestamp_str"].str.lower().isin(['0', '']) == False].copy()
        df["Timestamp"] = pd.to_datetime(df["Timestamp_str"], format="%d-%m-%Y %H:%M:%S", errors='coerce')
        df.dropna(subset=["Timestamp"], inplace=True)
        if df.empty:
            return
        df.sort_values(by="Timestamp", inplace=True)
    except Exception:
        return
    known_columns = {"Timestamp", "Timestamp_str", "FPS", "RealTime", "SimulatedTime", "DeltaTime", "FrameCount", "Pausado"}
    organism_columns = sorted([col for col in df.columns if col not in known_columns])
    plot_generated_count = 0
    if "FPS" in df.columns:
        plt.figure(figsize=(12, 6))
        plt.plot(df["Timestamp"], df["FPS"], marker=".", linestyle="-", color="blue")
        plt.title(f"FPS over Time ({simulation_name})")
        plt.xlabel("Timestamp")
        plt.ylabel("FPS")
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        try:
            plt.savefig(str(output_folder / "fps_over_time.png"))
            plot_generated_count += 1
        except Exception:
            pass
        plt.close()
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
            plot_generated_count += 1
        except Exception:
            pass
        plt.close()
    if organism_columns:
        plt.figure(figsize=(12, 6))
        plotted_any_organism = False
        for col in organism_columns:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                plt.plot(df["Timestamp"], df[col], label=col, marker=".", linestyle="-")
                plotted_any_organism = True
        if plotted_any_organism:
            plt.title(f"Organism Counts over Time ({simulation_name})")
            plt.xlabel("Timestamp")
            plt.ylabel("Count")
            plt.xticks(rotation=45, ha='right')
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.tight_layout()
            try:
                plt.savefig(str(output_folder / "organism_counts.png"))
                plot_generated_count += 1
            except Exception:
                pass
        plt.close()
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
            plot_generated_count += 1
        except Exception:
            pass
        plt.close()
    if "FrameCount" in df.columns:
        plt.figure(figsize=(12, 6))
        plt.plot(df["Timestamp"], df["FrameCount"], marker=".", linestyle="-", color="darkcyan")
        plt.title(f"Frame Count over Time ({simulation_name})")
        plt.xlabel("Timestamp")
        plt.ylabel("Frame Count")
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        try:
            plt.savefig(str(output_folder / "frame_count.png"))
            plot_generated_count += 1
        except Exception:
            pass
        plt.close()
    if "FPS" in df.columns and not df["FPS"].isnull().all():
        plt.figure(figsize=(12, 6))
        plt.hist(df["FPS"].dropna(), bins=20, color="green", edgecolor="black")
        plt.title(f"FPS Distribution ({simulation_name})")
        plt.xlabel("FPS")
        plt.ylabel("Frequency")
        plt.grid(True, axis='y', linestyle='--', alpha=0.6)
        plt.tight_layout()
        try:
            plt.savefig(str(output_folder / "fps_histogram.png"))
            plot_generated_count += 1
        except Exception:
             pass
        plt.close()
    if "Organism count" in df.columns and "FPS" in df.columns and not df["Organism count"].isnull().all() and not df["FPS"].isnull().all():
        if pd.api.types.is_numeric_dtype(df["Organism count"]):
            df_groupable = df.dropna(subset=["Organism count", "FPS"])
            try:
                 df_groupable["Organism count"] = df_groupable["Organism count"].astype(int)
            except ValueError:
                 pass
            df_grouped = df_groupable.groupby("Organism count")["FPS"].mean().reset_index()
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
                    plot_generated_count += 1
                except Exception:
                    pass
                plt.close()
    if "SimulatedTime" in df.columns and organism_columns:
        if pd.api.types.is_numeric_dtype(df["SimulatedTime"]) and not df["SimulatedTime"].isnull().all():
            plt.figure(figsize=(14, 7))
            plotted_something = False
            actual_organisms_plotted = []
            time_data_full = df["SimulatedTime"]
            for col in organism_columns:
                if col == "Organism count":
                    continue
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]) and not df[col].isnull().all():
                    valid_indices = df[col].notna() & time_data_full.notna()
                    time_data_clean = time_data_full[valid_indices].values
                    organism_data_clean = df.loc[valid_indices, col].values
                    if len(time_data_clean) > 0:
                        plt.plot(time_data_clean, organism_data_clean, label=f"{col}", marker=".", linestyle="-", alpha=0.7)
                        plotted_something = True
                        if col not in actual_organisms_plotted:
                            actual_organisms_plotted.append(col)
                    else:
                        continue
                    if len(time_data_clean) >= 2:
                        try:
                            initial_a = organism_data_clean[0] if organism_data_clean[0] > 0 else 1.0
                            if np.all(organism_data_clean == organism_data_clean[0]):
                                initial_b = 0.0
                            elif len(time_data_clean) > 1 and organism_data_clean[-1] > initial_a and time_data_clean[-1] > time_data_clean[0]:
                                time_diff = time_data_clean[-1] - time_data_clean[0]
                                if time_diff > 1e-9:
                                    initial_b = np.log(organism_data_clean[-1] / initial_a) / time_diff
                                else:
                                    initial_b = 0.0
                            else:
                                initial_b = 0.01
                            if not np.isfinite(initial_b):
                                initial_b = 0.01
                            p0 = [initial_a, initial_b]
                            bounds = ([0, -np.inf], [np.inf, np.inf])
                            params, covariance = curve_fit(
                                exponential_func,
                                time_data_clean,
                                organism_data_clean,
                                p0=p0,
                                bounds=bounds,
                                maxfev=10000
                            )
                            a_fit, b_fit = params
                            organism_predicted = exponential_func(time_data_clean, a_fit, b_fit)
                            r_squared = r2_score(organism_data_clean, organism_predicted)
                            time_fit = np.linspace(time_data_clean.min(), time_data_clean.max(), 100)
                            organism_fit = exponential_func(time_fit, a_fit, b_fit)
                            label_fit = f"{col} (Exp: a={a_fit:.2f}, b={b_fit:.3f}, R²={r_squared:.2f})"
                            plt.plot(time_fit, organism_fit, label=label_fit, linestyle="--")
                        except RuntimeError:
                            pass
                        except ValueError:
                            pass
                        except Exception:
                            pass
            if plotted_something:
                plt.title(f"Specific Organism Count & Exponential Fit over Simulated Time ({simulation_name})")
                plt.xlabel("Simulated Time (s)")
                plt.ylabel("Organism Count")
                if len(actual_organisms_plotted) > 2:
                    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
                    plt.tight_layout(rect=[0, 0, 0.85, 1])
                else:
                    plt.legend()
                    plt.tight_layout()
                plt.grid(True, linestyle='--', alpha=0.6)
                try:
                    save_path = output_folder / "organisms_vs_simulated_time_fit.png"
                    plt.savefig(str(save_path))
                    plot_generated_count += 1
                except Exception:
                    pass
            plt.close()

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

def _insert_code_between_markers(template_content: str, code_to_insert: str, start_marker: str, end_marker: str) -> Union[str, None]:
    pattern = re.compile(re.escape(start_marker) + r'.*?' + re.escape(end_marker), re.DOTALL)
    match = pattern.search(template_content)
    if not match:
        return None
    start_index = match.start()
    end_index = match.end()
    new_block = f"{start_marker}\n{code_to_insert}\n{end_marker}"
    return template_content[:start_index] + new_block + template_content[end_index:]

def separar_codigos_por_archivo(respuesta: str) -> Dict[str, str]:
    actual_content = respuesta.strip().strip('"')
    regex_especifico = r"1\.PrefabMaterialCreator\.cs\{(.*?)\}2\.OrganismTypes\{(.*?)\}"
    match = re.search(regex_especifico, actual_content, re.DOTALL)
    codigos = {}
    if match:
        codigos["PrefabMaterialCreator.cs"] = match.group(1).strip()
        codigos["OrganismTypes"] = match.group(2).strip()
    else:
        print("Warning: Response string does not match expected format.")
    return codigos

def get_collider_templates() -> dict:
    return {
        "Bacilo": textwrap.dedent("""
            colliderAsset = Unity.Physics.CapsuleCollider.Create(new CapsuleGeometry
            {
                Vertex0 = new float3(0, -__LENGTH__ * 0.5f, 0), Vertex1 = new float3(0, __LENGTH__ * 0.5f, 0), Radius = __RADIUS__
            }, CollisionFilter.Default, physicsMat);
        """).strip(),
        "Cocco": textwrap.dedent("""
            colliderAsset = Unity.Physics.SphereCollider.Create(new SphereGeometry
            {
                Center = float3.zero, Radius = 0.5f
            }, CollisionFilter.Default, physicsMat);
        """).strip(),
        "Helicoide": textwrap.dedent("""
            colliderAsset = CreateHelicalCollider(__MAX_AXIAL_LENGTH__, physicsMat);
        """).strip()
    }

def parse_organism_data(input_str: str) -> list:
    if not input_str.startswith('[') or not input_str.endswith(']'):
        raise ValueError("Organism data must be enclosed in '[]'")
    content = input_str.strip('[]')
    organism_entries = re.split(r';\s*(?=[^)]*(?:\(|$))', content)
    parsed_data = []
    for entry in filter(None, (e.strip() for e in organism_entries)):
        match = re.match(r'([^->]+)\s*->\s*([^()]+)\s*\((.*)\)', entry)
        if not match:
            print(f"Warning: Organism entry '{entry}' has incorrect format and will be ignored.")
            continue
        name, morphology, params_str = (m.strip() for m in match.groups())
        params = {
            key.strip(): value.strip()
            for pair in re.split(r',\s*(?=[a-zA-Z0-9_]+\s*=)', params_str)
            if '=' in pair
            for key, value in [pair.split('=', 1)]
        }
        parsed_data.append({'name': name, 'morphology': morphology, 'params': params})
    return parsed_data

def generate_csharp_switch_cases(organism_data: list, templates: dict) -> str:
    final_case_blocks = []
    for organism in organism_data:
        name, morphology, params = organism['name'], organism['morphology'], organism['params']
        code_template = templates.get(morphology)
        if not code_template:
            body = f"// Morfología '{morphology}' no implementada."
            full_block = f'            case "{name}":\n                {body}\n                break;'
            final_case_blocks.append(full_block)
            continue
        body = ""
        try:
            if morphology == "Bacilo":
                body = code_template.replace('__LENGTH__', params['Length']).replace('__RADIUS__', params['Radius'])
            elif morphology == "Helicoide":
                body = code_template.replace('__MAX_AXIAL_LENGTH__', params['MaxAxialLength'])
            else:
                body = code_template
        except KeyError as e:
            body = f"// Error: Parámetro {e} faltante para {name}."
        indented_body = textwrap.indent(body, ' ' * 16)
        full_block = f'            case "{name}":\n{indented_body}\n                break;'
        final_case_blocks.append(full_block)
    return "\n\n".join(final_case_blocks)

def generate_csharp_if_else_block(organism_data: list) -> str:
    EXCLUDED_PARAMS_BY_MORPHOLOGY = {
        "Bacilo": {"Radius", "Length"}, "Cocco": {"Diameter"}, "Helicoide": set()
    }
    blocks = []
    param_indent = ' ' * 16
    for i, organism in enumerate(organism_data):
        name, morphology = organism['name'], organism['morphology']
        params_to_exclude = EXCLUDED_PARAMS_BY_MORPHOLOGY.get(morphology, set())
        param_lines = [f"{param_indent}{key} = {value}," for key, value in organism['params'].items() if key not in params_to_exclude]
        if param_lines: param_lines[-1] = param_lines[-1].rstrip(',')
        params_code = "\n".join(param_lines)
        keyword = "if" if i == 0 else "else if"
        block = textwrap.dedent(f"""\
            {keyword} (prefabName == "{name}")
            {{
                entityManager.AddComponentData(newEntity, new {name}Component
                {{
{params_code}
                }});
            }}""")
        blocks.append(block.strip())
    return "\n        ".join(blocks)

def import_codes(codes: Dict[str, str], simulation_name: str) -> bool:
    simulation_folder = SIMULATIONS_DIR / simulation_name
    template_folder = APP_BASE_DIR / "Template"
    if not template_folder.is_dir():
        print(f"Error: Template folder not found at '{template_folder}'")
        return False
    if not simulation_folder.exists():
        try:
            shutil.copytree(template_folder, simulation_folder)
        except Exception as e:
            print(f"Error creating simulation folder from template: {e}")
            return False
    assets_editor_folder = simulation_folder / "Assets" / "Editor"
    assets_scripts_folder = simulation_folder / "Assets" / "Scripts"
    assets_scripts_components = assets_scripts_folder / "Components"
    assets_scripts_systems = assets_scripts_folder / "Systems"
    assets_scripts_general = assets_scripts_folder / "General"
    for d in [assets_editor_folder, assets_scripts_components, assets_scripts_systems, assets_scripts_general]:
        d.mkdir(parents=True, exist_ok=True)
    files_processed = []
    pmc_content = codes.get("PrefabMaterialCreator.cs")
    if pmc_content:
        dest_path = assets_editor_folder / "PrefabMaterialCreator.cs"
        try:
            with open(dest_path, "r+", encoding="utf-8") as f:
                template_text = f.read()
                new_content = _insert_code_between_markers(template_text, pmc_content, "//CODE START", "//CODE END")
                if new_content:
                    f.seek(0); f.write(new_content); f.truncate()
                    files_processed.append(dest_path)
        except Exception as e:
            print(f"Error processing PrefabMaterialCreator.cs: {e}")
    organism_types_content = codes.get("OrganismTypes")
    if organism_types_content:
        try:
            organisms = parse_organism_data(organism_types_content)
            cpoc_path = assets_scripts_general / "CreatePrefabsOnClick.cs"
            if cpoc_path.exists() and organisms:
                switch_code = generate_csharp_switch_cases(organisms, get_collider_templates())
                if_else_code = generate_csharp_if_else_block(organisms)
                with open(cpoc_path, "r+", encoding="utf-8") as f:
                    content = f.read()
                    new_content = _insert_code_between_markers(content, if_else_code, "//if_else_block START", "//if_else_block END")
                    if new_content:
                        new_content = _insert_code_between_markers(new_content, switch_code, "//case statements START", "//case statements END")
                    if new_content:
                        f.seek(0); f.write(new_content); f.truncate()
                        files_processed.append(cpoc_path)
            for org in organisms:
                name, morph, params = org['name'], org['morphology'], org['params']
                for file_type in ["Component", "System"]:
                    template_file = f"{morph}{file_type}.cs"
                    source_path = template_folder / "Assets" / "Scripts" / f"{file_type}s" / template_file
                    if source_path.exists():
                        dest_file = f"{name}{file_type}.cs"
                        dest_path = assets_scripts_folder / f"{file_type}s" / dest_file
                        tpl_text = source_path.read_text(encoding='utf-8').replace(morph, name)
                        if morph == "Bacilo" and file_type == "System":
                            try:
                                tpl_text = tpl_text.replace('__LENGTH__', params['Length'])
                            except KeyError:
                                print(f"Warning: 'Length' param not found for Bacilo '{name}'.")
                        dest_path.write_text(tpl_text, encoding='utf-8')
                        files_processed.append(dest_path)
        except Exception as e:
            print(f"Error processing OrganismTypes: {e}")
    processed_basenames = {fp.name for fp in files_processed}
    for template_base_name in ["Bacilo", "Cocco", "Helicoide"]:
        for file_type in ["Component", "System"]:
            filename_to_check = f"{template_base_name}{file_type}.cs"
            if filename_to_check not in processed_basenames:
                path_to_remove = simulation_folder / "Assets" / "Scripts" / f"{file_type}s" / filename_to_check
                if path_to_remove.exists():
                    try:
                        path_to_remove.unlink()
                    except OSError as e:
                        print(f"Error cleaning template '{filename_to_check}': {e}")
    return bool(files_processed)

DELIMITER = "%|%"
RESPONSES_CSV = None
try:
    APP_DATA_DIR_DOCS = Path.home() / "Documents" / "ColonyDynamicsSimulatorData"
    APP_DATA_DIR_DOCS.mkdir(parents=True, exist_ok=True)
    RESPONSES_DIR_DOCS = APP_DATA_DIR_DOCS / "Responses"
    RESPONSES_DIR_DOCS.mkdir(parents=True, exist_ok=True)
    RESPONSES_CSV = RESPONSES_DIR_DOCS / "Responses.csv"
except Exception:
    try:
        RESPONSES_DIR = APP_BASE_DIR / "UserData" / "Responses"
        RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
        RESPONSES_CSV = RESPONSES_DIR / "Responses.csv"
    except Exception:
        RESPONSES_CSV = None

def check_last_char_is_newline(filepath: Union[str, Path]) -> bool:
    if not RESPONSES_CSV: return True
    filepath = Path(filepath)
    if not filepath.exists() or filepath.stat().st_size == 0:
        return True
    try:
        with open(filepath, 'rb') as f:
            f.seek(-1, os.SEEK_END)
            last_byte = f.read(1)
            return last_byte == b'\n'
    except Exception:
        return False

def get_next_id(csv_path: Union[str, Path]) -> int:
    if not RESPONSES_CSV: return 1
    csv_path = Path(csv_path)
    try:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
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
    except Exception:
         return 1

def write_response_to_csv(prompt: str, response: str, input_tokens: int, output_tokens: int) -> None:
    if not RESPONSES_CSV:
         return
    try:
        file_exists = RESPONSES_CSV.exists()
        is_empty = file_exists and RESPONSES_CSV.stat().st_size == 0
        write_header = not file_exists or is_empty
        next_id = get_next_id(RESPONSES_CSV)
        needs_leading_newline = file_exists and not is_empty and not check_last_char_is_newline(RESPONSES_CSV)
        with open(RESPONSES_CSV, "a", encoding="utf-8", newline='') as f:
            if needs_leading_newline:
                f.write('\n')
            if write_header:
                header = f"id{DELIMITER}prompt{DELIMITER}response{DELIMITER}input_tokens{DELIMITER}output_tokens\n"
                f.write(header)
            clean_prompt = str(prompt).replace(DELIMITER, "<DELIM>").replace('\n', '\\n').replace('\r', '')
            clean_response = str(response).replace(DELIMITER, "<DELIM>").replace('\n', '\\n').replace('\r', '')
            line = f"{next_id}{DELIMITER}{clean_prompt}{DELIMITER}{clean_response}{DELIMITER}{input_tokens}{DELIMITER}{output_tokens}\n"
            f.write(line)
    except IOError:
        pass
    except Exception:
        pass

def get_cached_response(prompt: str) -> Union[str, None]:
    if not RESPONSES_CSV or not RESPONSES_CSV.exists():
        return None
    try:
        with open(RESPONSES_CSV, "r", encoding="utf-8") as f:
             lines = f.readlines()
        clean_prompt_search = str(prompt).replace(DELIMITER, "<DELIM>").replace('\n', '\\n').replace('\r', '')
        for line in lines[1:]:
            line = line.strip()
            if not line: continue
            parts = line.split(DELIMITER)
            if len(parts) == 5:
                cached_prompt = parts[1]
                cached_response_raw = parts[2]
                if cached_prompt == clean_prompt_search:
                    original_response = cached_response_raw.replace('\\n', '\n').replace("<DELIM>", DELIMITER)
                    return original_response
            else:
                pass
    except FileNotFoundError:
         return None
    except Exception:
         return None
    return None

def clear_api_cache():
    if 'RESPONSES_CSV' not in globals() or RESPONSES_CSV is None:
        messagebox.showerror("Configuration Error", "Cache file path is not defined. Cannot clear.")
        return
    confirm = messagebox.askyesno(
        "Confirm Cache Deletion",
        f"Are you sure you want to permanently delete the API response cache file?\n\n({RESPONSES_CSV})\n",
        icon='warning'
    )
    if not confirm:
        update_status("Cache deletion cancelled by user.")
        return
    try:
        if RESPONSES_CSV.is_file():
            RESPONSES_CSV.unlink()
            messagebox.showinfo("Success", "The cache file (Responses.csv) has been successfully deleted.")
            update_status("API response cache cleared.")
        else:
            messagebox.showinfo("Information", "The cache file did not exist. Nothing was deleted.")
            update_status("Cache clear attempted, but the file did not exist.")
    except PermissionError:
        messagebox.showerror("Permission Error", f"Could not delete the file. Please ensure it is not open in another program and that you have write permissions.\n\nPath: {RESPONSES_CSV}")
        update_status("Permission error while clearing cache.")
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred while trying to delete the cache file:\n\n{e}")
        update_status(f"Unexpected error while clearing cache: {e}")

def api_manager(sim_name: str, sim_desc: str, use_cache: bool = True) -> Tuple[bool, Union[str, None]]:
    if not API_BASE_URL:
        return False, "Config Error: API_BASE_URL missing."
    if not apis_key_ok or not apis_models_ok:
        return False, "API/Model Configuration Error: API key or required models failed verification. Please check Settings and Verify Config."
    fmt_q, tk_is, tk_os, err_s = call_secondary_model_via_api(sim_desc)
    if err_s:
        return False, f"Error in API call (Secondary Model): {err_s}"
    if not fmt_q:
         return False, "Error from Secondary Model: API returned an empty response."
    fmt_q_s = fmt_q.strip()
    if fmt_q_s == "ERROR DE CONTENIDO":
        return False, "Validation Failed: The description contains content that is not suitable for a simulation of organisms with morphology (Bacilo, Cocco, Helicoide)."
    if fmt_q_s == "ERROR CANTIDAD EXCEDIDA":
        return False, "Validation Failed: More than 5 organisms were requested. Maximum limit: 5."
    if fmt_q_s == "ERROR MORFOLOGIA NO ACEPTADA":
        return False, "Validation Failed: The organism's morphology is not accepted or is not one of the allowed types (Bacilo, Cocco, Helicoide)."
    if fmt_q_s.upper().startswith("ERROR"):
        return False, f"Error from Secondary Model: {fmt_q_s}"
    final_response: Optional[str] = None
    cache_hit = False
    total_tk_in = tk_is
    total_tk_out = tk_os
    if use_cache:
        cached_response = get_cached_response(fmt_q)
        if cached_response:
            final_response = cached_response
            cache_hit = True
    if not final_response:
        prim_r, tk_ip, tk_op, err_p = call_primary_model_via_api(fmt_q)
        if err_p:
            return False, f"Error in API call (Primary Model): {err_p}"
        if not prim_r:
            return False, "Error from Primary Model: API returned an empty response."
        if "ERROR FORMATO" in prim_r.upper():
            return False, f"Prompt Format Error: Primary model rejected the formatted prompt:\n'{fmt_q}'"
        final_response = prim_r
        total_tk_in += tk_ip
        total_tk_out += tk_op
        if use_cache and not cache_hit:
            write_response_to_csv(fmt_q, final_response, total_tk_in, total_tk_out)
    if not final_response:
        return False, "Critical Error: No valid final response obtained (neither from cache nor generated)."
    codes = separar_codigos_por_archivo(final_response)
    if not codes:
        return False, f"Extraction Error: No valid C# code blocks found in the response.\nStart of received response:\n{final_response[:800]}..."
    ok_import = import_codes(codes, sim_name)
    if ok_import:
        return True, None
    else:
        return False, f"Import Error: Failed to save scripts for simulation '{sim_name}'. Please check logs for details."

def center_window(window, width, height):
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def apply_icon(window):
    try:
        if ICON_PATH_MAC and ICON_PATH_MAC.exists():
            img = tk.PhotoImage(file=str(ICON_PATH_MAC))
            window.tk.call('wm', 'iconphoto', window._w, img)
        elif ICON_PATH_MAC:
            pass
    except tk.TclError:
        pass
    except Exception:
        pass

class CustomInputDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, prompt, width=400, height=170):
        super().__init__(parent)
        self.title(title)
        apply_icon(self)
        center_window(self, width, height)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        ctk.CTkLabel(self, text=prompt, font=APP_FONT, wraplength=width-40).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        self.entry = ctk.CTkEntry(self, font=APP_FONT, width=width-40)
        self.entry.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="e")
        mode_idx = get_color_mode_index()
        ok_button = ctk.CTkButton(button_frame, text="OK", command=self.ok_action, width=80, font=APP_FONT,
                                  fg_color=COLOR_SUCCESS_GENERAL[mode_idx], hover_color=COLOR_INFO_GENERAL[mode_idx])
        ok_button.pack(side="left", padx=(0, 10))
        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self.cancel_action, width=80, font=APP_FONT,
                                      fg_color=COLOR_WARNING_GENERAL[mode_idx], hover_color=COLOR_DANGER_GENERAL[mode_idx])
        cancel_button.pack(side="left")
        self.bind("<Return>", lambda event: self.ok_action())
        self.bind("<Escape>", lambda event: self.cancel_action())
        self.entry.focus()
        self.wait_window()

    def ok_action(self):
        self.result = self.entry.get()
        self.destroy()

    def cancel_action(self):
        self.result = None
        self.destroy()

def custom_askstring(title, prompt):
    if 'main_window' in globals() and main_window and main_window.winfo_exists():
        dialog = CustomInputDialog(main_window, title, prompt)
        return dialog.result
    else:
        return None

def show_tooltip(widget, text):
    global tooltip_window
    hide_tooltip()
    try:
        x, y = widget.winfo_pointerxy()
        x += 20
        y += 10
    except tk.TclError:
        return
    tooltip_window = tk.Toplevel(widget)
    tooltip_window.wm_overrideredirect(True)
    tooltip_window.wm_geometry(f"+{x}+{y}")
    label = tk.Label(tooltip_window, text=text, justify='left',
                     background="#ffffe0",
                     relief='solid', borderwidth=1,
                     font=("Segoe UI", 9))
    label.pack(ipadx=1)

def hide_tooltip():
    global tooltip_window
    if tooltip_window:
        try:
            tooltip_window.destroy()
        except tk.TclError:
            pass
        tooltip_window = None

def schedule_tooltip(widget, text):
    global tooltip_job_id
    cancel_tooltip(widget)
    tooltip_job_id = widget.after(tooltip_delay, lambda: show_tooltip(widget, text))

def cancel_tooltip(widget):
    global tooltip_job_id
    if tooltip_job_id:
        widget.after_cancel(tooltip_job_id)
        tooltip_job_id = None
    hide_tooltip()

def on_closing():
    global is_build_running
    if is_build_running:
        messagebox.showwarning("Operation in Progress", "A build or load operation is currently running. Please wait for it to finish before closing.")
        return
    if messagebox.askokcancel(
        title="Exit Confirmation",
        message="Are you sure you want to exit the Colony Dynamics Simulator?",
        icon='question'
        ):
        if callable(globals().get('update_status')): update_status("Closing application...")
        close_unity_thread = threading.Thread(target=ensure_unity_closed, daemon=True)
        close_unity_thread.start()
        close_unity_thread.join(timeout=2.0)
        if 'main_window' in globals() and main_window:
            try:
                main_window.destroy()
            except tk.TclError:
                pass
            except Exception:
                pass
        sys.exit(0)

def disable_all_interactions():
    global is_build_running
    is_build_running = True
    mode_idx = get_color_mode_index()
    disabled_color = COLOR_DISABLED_GENERAL[mode_idx]
    try:
        if 'reload_btn' in globals(): reload_btn.configure(state="disabled", fg_color=disabled_color)
        if 'graph_btn' in globals(): graph_btn.configure(state="disabled", fg_color=disabled_color)
        if 'create_btn' in globals(): create_btn.configure(state="disabled", fg_color=disabled_color)
        if 'sidebar_frame' in globals() and sidebar_frame.winfo_exists():
            for widget in sidebar_frame.winfo_children():
                if isinstance(widget, (ctk.CTkButton, ctk.CTkSwitch)):
                    widget.configure(state="disabled")
                    if isinstance(widget, ctk.CTkButton): widget.configure(fg_color=disabled_color)
        if 'search_entry' in globals(): search_entry.configure(state="disabled")
        if 'clear_search_btn' in globals(): clear_search_btn.configure(state="disabled", fg_color=disabled_color)
        if 'sim_tree' in globals():
            sim_tree.unbind("<Button-1>")
            sim_tree.unbind("<Motion>")
            sim_tree.unbind("<Leave>")
            sim_tree.configure(cursor="watch")
        if callable(globals().get('update_status')): update_status("Operation in progress... Please wait.")
    except (NameError, tk.TclError):
        pass

def enable_all_interactions():
    global is_build_running
    is_build_running = False
    try:
        if 'sidebar_frame' in globals() and sidebar_frame.winfo_exists():
            for widget in sidebar_frame.winfo_children():
                if isinstance(widget, (ctk.CTkButton, ctk.CTkSwitch)):
                    widget.configure(state="normal")
        if 'search_entry' in globals(): search_entry.configure(state="normal")
        if 'clear_search_btn' in globals(): clear_search_btn.configure(state="normal")
        if 'sim_tree' in globals():
            sim_tree.bind("<Button-1>", handle_tree_click)
            sim_tree.bind("<Motion>", handle_tree_motion)
            sim_tree.bind("<Leave>", handle_tree_leave)
            sim_tree.configure(cursor="")
        if callable(globals().get('update_button_states')):
             if 'main_window' in globals() and main_window:
                  main_window.after(10, update_button_states)
             else:
                  update_button_states()
    except (NameError, tk.TclError):
        pass

def update_status(message):
    try:
        if 'main_window' in globals() and main_window and main_window.winfo_exists() and 'status_label' in globals():
            main_window.after(0, lambda msg=str(message): status_label.configure(text=msg))
    except Exception:
         pass

def handle_unity_execution_error(error, operation_name="operation"):
    error_type = type(error).__name__
    error_details = str(error)
    if isinstance(error, subprocess.CalledProcessError):
        details = f"Process exited with code {error.returncode}."
        if error.stdout: details += f"\nLast stdout: ...{error.stdout[-200:]}"
        if error.stderr: details += f"\nStderr: {error.stderr[-200:]}"
        error_details = details
    elif isinstance(error, subprocess.TimeoutExpired):
        error_details = f"Process timed out after {error.timeout} seconds."
    elif isinstance(error, FileNotFoundError):
        error_details = f"Command or project path not found: {error.filename}"
    elif isinstance(error, PermissionError):
         error_details = "Permission denied. Check file/folder permissions."
    error_message = (
        f"An error occurred during the Unity {operation_name}.\n\n"
        f"Error Type: {error_type}\n"
        f"Details: {error_details}\n\n"
        f"Possible Causes:\n"
        f"- Incorrect Unity executable path in .env.\n"
        f"- Incorrect Unity version (Required: {UNITY_REQUIRED_VERSION_STRING}).\n"
        f"- Invalid Unity project path.\n"
        f"- Insufficient permissions.\n"
        f"- Unity Editor crashed or is unresponsive.\n\n"
        f"Check the console output and Unity log files (if generated) for more information."
    )
    try:
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
            main_window.after(0, lambda title=f"Unity {operation_name.capitalize()} Error", msg=error_message: messagebox.showerror(title, msg))
        else:
            pass
    except Exception:
        pass

def ensure_unity_closed():
    if not unity_path_ok or not UNITY_EXECUTABLE:
        return
    unity_processes = []
    try:
        normalized_unity_exe = Path(UNITY_EXECUTABLE).resolve()
        for proc in psutil.process_iter(['exe', 'pid', 'name']):
            try:
                proc_info = proc.info
                if proc_info['exe']:
                    proc_exe_path = Path(proc_info['exe']).resolve()
                    if proc_exe_path == normalized_unity_exe:
                        unity_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, FileNotFoundError):
                continue
            except Exception:
                 continue
    except Exception:
        return
    if unity_processes:
        time_start = time.time()
        for proc in unity_processes:
            try:
                proc.terminate()
            except psutil.NoSuchProcess:
                 pass
            except psutil.Error:
                pass
        gone, alive = psutil.wait_procs(unity_processes, timeout=5)
        if alive:
            for proc in alive:
                try:
                    proc.kill()
                except psutil.NoSuchProcess:
                    pass
                except psutil.Error:
                    pass
            psutil.wait_procs(alive, timeout=3)

def open_graphs_folder(simulation_name):
    if not simulation_name:
        messagebox.showerror("Error", "No simulation name provided to open the graphics folder.")
        return
    simulation_data_dir = find_simulation_data_path(simulation_name)
    if not simulation_data_dir:
        messagebox.showerror("Error", f"Could not find the data directory for simulation '{simulation_name}'.\nCannot open the graphics folder.")
        return
    folder_to_open = simulation_data_dir
    try:
        (folder_to_open / GRAPHICS_SUBFOLDER).mkdir(parents=True, exist_ok=True)
        subprocess.Popen(["open", str(folder_to_open)])
    except FileNotFoundError:
         cmd = 'open'
         messagebox.showerror("System Error", f"Could not find the system command ('{cmd}') to open the folder on this OS (Darwin).")
    except Exception as e:
         messagebox.showerror("Error", f"Could not open the graphics folder:\n{folder_to_open}\n\nError: {e}")
         traceback.print_exc()

def get_folder_size(path: Union[str, Path]) -> int:
    total = 0
    try:
        p = Path(path)
        if not p.is_dir(): return 0
        for entry in p.iterdir():
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += get_folder_size(entry)
            except (FileNotFoundError, PermissionError):
                continue
            except Exception:
                 continue
    except (FileNotFoundError, PermissionError):
        pass
    except Exception:
        pass
    return total

def copy_directory(src: Union[str, Path], dst: Union[str, Path]) -> bool:
    src_path = Path(src)
    dst_path = Path(dst)
    if not src_path.is_dir():
        msg = f"Source for copy is not a valid directory: {src_path}"
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
            main_window.after(0, lambda: messagebox.showerror("Copy Error", msg))
        return False
    try:
        if dst_path.exists():
            try:
                if dst_path.is_dir(): shutil.rmtree(dst_path, ignore_errors=False)
                else: dst_path.unlink()
            except Exception:
                 if dst_path.is_dir(): shutil.rmtree(dst_path, ignore_errors=True)
                 elif dst_path.is_file(): dst_path.unlink(missing_ok=True)
            time.sleep(0.1)
        shutil.copytree(src_path, dst_path, symlinks=False, ignore_dangling_symlinks=True)
        return True
    except Exception as e:
        msg = f"Error copying directory:\nFrom: {src_path}\nTo:   {dst_path}\n\nError: {e}"
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
            main_window.after(0, lambda: messagebox.showerror("Copy Error", msg))
        if dst_path.exists() and dst_path.is_dir():
             try: shutil.rmtree(dst_path, ignore_errors=True)
             except: pass
        return False

def get_build_target_and_executable(project_path: Union[str, Path, None]) -> Tuple[Union[str, None], Union[str, None]]:
    if not project_path:
        return None, None
    project_path = Path(project_path)
    executable_name = SIMULATION_PROJECT_NAME
    build_target = "OSXUniversal"
    platform_folder = "Mac"
    executable_suffix = ".app"
    build_base_dir = project_path / "Build" / platform_folder
    executable_path = build_base_dir / (executable_name + executable_suffix)
    return build_target, str(executable_path)

def get_simulations() -> list[Dict]:
    simulations = []
    if not SIMULATIONS_DIR.is_dir():
        return simulations
    try:
        for item in SIMULATIONS_DIR.iterdir():
            if item.is_dir():
                assets_path = item / "Assets"
                settings_path = item / "ProjectSettings"
                if assets_path.is_dir() and settings_path.is_dir():
                    created_str, last_opened_str = "???", "Never"
                    created_timestamp, last_opened_timestamp = 0, 0
                    try:
                        created_timestamp = item.stat().st_ctime
                        created_str = time.strftime("%y-%m-%d %H:%M", time.localtime(created_timestamp))
                    except Exception: pass
                    last_opened_file = item / "last_opened.txt"
                    if last_opened_file.is_file():
                        try:
                            with open(last_opened_file, "r", encoding="utf-8") as f:
                                last_opened_timestamp = float(f.read().strip())
                            last_opened_str = time.strftime("%y-%m-%d %H:%M", time.localtime(last_opened_timestamp))
                        except (ValueError, OSError): pass
                    simulations.append({
                        "name": item.name,
                        "creation": created_str,
                        "last_opened": last_opened_str,
                        "creation_ts": created_timestamp,
                    })
    except Exception:
        return []
    return simulations

def update_last_opened(sim_name: str):
    simulation_folder = SIMULATIONS_DIR / sim_name
    try:
        simulation_folder.mkdir(parents=True, exist_ok=True)
        last_opened_file = simulation_folder / "last_opened.txt"
        with open(last_opened_file, "w") as f:
            f.write(str(time.time()))
    except Exception:
        pass

def read_last_loaded_simulation_name() -> Union[str, None]:
    global SIMULATION_LOADED_FILE
    file_path_obj = None
    current_value = SIMULATION_LOADED_FILE
    if isinstance(current_value, Path):
        file_path_obj = current_value
    elif isinstance(current_value, str) and current_value:
        try:
            file_path_obj = Path(current_value)
        except Exception:
            return None
    elif current_value is None:
        pass
    else:
        return None
    if file_path_obj and file_path_obj.exists() and file_path_obj.is_file():
        try:
            with open(file_path_obj, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return content if content else None
        except Exception:
            return None
    else:
        return None

def load_simulation(sim_name: str) -> bool:
    global last_simulation_loaded, SIMULATION_PROJECT_PATH, ASSETS_FOLDER, STREAMING_ASSETS_FOLDER, SIMULATION_LOADED_FILE
    if not unity_projects_path_ok or not UNITY_PROJECTS_PATH:
        messagebox.showerror("Configuration Error", "Cannot load simulation: The Unity Projects Path is not configured or invalid in the .env file.")
        return False
    try:
        base_project_path = Path(UNITY_PROJECTS_PATH)
        SIMULATION_PROJECT_PATH = base_project_path / SIMULATION_PROJECT_NAME
        ASSETS_FOLDER = SIMULATION_PROJECT_PATH / "Assets"
        STREAMING_ASSETS_FOLDER = ASSETS_FOLDER / "StreamingAssets"
        SIMULATION_LOADED_FILE = STREAMING_ASSETS_FOLDER / "simulation_loaded.txt"
    except Exception as path_e:
         messagebox.showerror("Path Error", f"Could not construct required project paths from UNITY_PROJECTS_PATH ('{UNITY_PROJECTS_PATH}').\nError: {path_e}")
         return False
    source_path = SIMULATIONS_DIR / sim_name
    if not source_path.is_dir():
        messagebox.showerror("Load Error", f"Simulation source folder not found:\n{source_path}")
        return False
    try:
        SIMULATION_PROJECT_PATH.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        messagebox.showerror("Directory Error", f"Could not create or access the target Unity project directory:\n{SIMULATION_PROJECT_PATH}\n\nError: {e}")
        return False
    current_persistent_loaded = read_last_loaded_simulation_name()
    needs_full_copy = (
        not current_persistent_loaded or
        current_persistent_loaded != sim_name or
        not ASSETS_FOLDER.is_dir()
    )
    copy_ok = True
    folders_to_copy = ["Assets", "Packages", "ProjectSettings"]
    if needs_full_copy:
        update_status(f"Loading '{sim_name}': Full copy (Assets, Packages, Settings)...")
        for folder_name in folders_to_copy:
            target_folder = SIMULATION_PROJECT_PATH / folder_name
            if target_folder.exists():
                 try:
                      if target_folder.is_dir(): shutil.rmtree(target_folder, ignore_errors=True)
                      else: target_folder.unlink(missing_ok=True)
                      time.sleep(0.1)
                 except Exception: pass
        for folder_name in folders_to_copy:
            src_folder = source_path / folder_name
            dst_folder = SIMULATION_PROJECT_PATH / folder_name
            if src_folder.is_dir():
                if not copy_directory(src_folder, dst_folder):
                    copy_ok = False
                    break
            elif folder_name in ["Assets", "ProjectSettings"]:
                messagebox.showwarning("Missing Folder", f"Required folder '{folder_name}' is missing in the source simulation '{sim_name}'. The loaded project might be incomplete.")
                if folder_name == "Assets": copy_ok = False; break
    else:
        update_status(f"Loading '{sim_name}': Updating Assets folder...")
        src_assets = source_path / "Assets"
        dst_assets = ASSETS_FOLDER
        if src_assets.is_dir():
            if not copy_directory(src_assets, dst_assets):
                copy_ok = False
        else:
            messagebox.showerror("Load Error", f"Cannot update: 'Assets' folder is missing in the source simulation '{sim_name}'.")
            copy_ok = False
    if not copy_ok:
        update_status(f"Error during file copy for '{sim_name}'. Load cancelled.")
        return False
    try:
        STREAMING_ASSETS_FOLDER.mkdir(parents=True, exist_ok=True)
        with open(SIMULATION_LOADED_FILE, "w") as f:
            f.write(sim_name)
    except Exception as e:
        messagebox.showwarning("State File Error", f"Could not create StreamingAssets folder or update the simulation state file:\n{SIMULATION_LOADED_FILE}\n\nError: {e}")
    update_last_opened(sim_name)
    last_simulation_loaded = sim_name
    if 'main_window' in globals() and main_window and main_window.winfo_exists():
        main_window.after(50, populate_simulations)
    elif callable(globals().get('populate_simulations')):
         populate_simulations()
    update_status(f"Simulation '{sim_name}' loaded successfully.")
    return True

def delete_simulation(sim_name: str):
    global last_simulation_loaded, all_simulations_data, SIMULATION_LOADED_FILE, SIMULATIONS_DIR
    if not sim_name:
        messagebox.showerror("Error", "No simulation name provided for deletion.")
        return
    confirm = messagebox.askyesno(
        "Confirm Deletion",
        f"Permanently delete the simulation '{sim_name}' and ALL associated data (logs, graphs, configuration)?\n\nThis action cannot be undone!",
        icon='warning'
    )
    if not confirm:
        if callable(globals().get('update_status')): update_status("Deletion cancelled.")
        return
    if callable(globals().get('update_status')): update_status(f"Deleting '{sim_name}'...")
    errors_occurred = False
    state_file_path_obj = None
    current_state_file_value = SIMULATION_LOADED_FILE
    if isinstance(current_state_file_value, Path):
        state_file_path_obj = current_state_file_value
    elif isinstance(current_state_file_value, str) and current_state_file_value:
        try: state_file_path_obj = Path(current_state_file_value)
        except Exception: errors_occurred = True
    elif current_state_file_value is None: pass
    else:
        errors_occurred = True
    if state_file_path_obj:
        if state_file_path_obj.is_file():
            try:
                loaded_name_from_file = read_last_loaded_simulation_name()
                if loaded_name_from_file == sim_name:
                    state_file_path_obj.unlink()
                    if last_simulation_loaded == sim_name:
                        last_simulation_loaded = None
            except Exception:
                errors_occurred = True
        else:
            if last_simulation_loaded == sim_name:
                 last_simulation_loaded = None
    else:
        if last_simulation_loaded == sim_name:
             last_simulation_loaded = None
    if isinstance(SIMULATIONS_DIR, Path):
        local_sim_path = SIMULATIONS_DIR / sim_name
        if local_sim_path.exists():
            if local_sim_path.is_dir():
                try:
                    shutil.rmtree(local_sim_path)
                except PermissionError as e:
                    messagebox.showerror("Permission Error", f"Permission denied while deleting the local configuration folder:\n{local_sim_path}\n\n{e}")
                    errors_occurred = True
                except OSError as e:
                    messagebox.showerror("System Error", f"Could not delete the local configuration folder (in use?):\n{local_sim_path}\n\n{e}")
                    errors_occurred = True
                except Exception as e:
                    messagebox.showerror("Unexpected Error", f"An unexpected error occurred deleting the local configuration folder:\n{local_sim_path}\n\n{e}")
                    errors_occurred = True
            else:
                try:
                    local_sim_path.unlink()
                except Exception:
                     errors_occurred = True
    else:
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
            messagebox.showerror("Internal Error", f"Configuration Error: SIMULATIONS_DIR type is {type(SIMULATIONS_DIR)}, expected Path. Cannot delete local data.")
        errors_occurred = True
    unity_data_path = find_simulation_data_path(sim_name)
    if unity_data_path is None:
        pass
    elif unity_data_path.exists():
        if unity_data_path.is_dir():
            try:
                shutil.rmtree(unity_data_path)
            except PermissionError as e:
                messagebox.showerror("Permission Error", f"Permission denied while deleting the Unity data folder:\n{unity_data_path}\n\n{e}")
                errors_occurred = True
            except OSError as e:
                messagebox.showerror("System Error", f"Could not delete the Unity data folder (in use?):\n{unity_data_path}\n\n{e}")
                errors_occurred = True
            except Exception as e:
                messagebox.showerror("Unexpected Error", f"An unexpected error occurred deleting the Unity data folder:\n{unity_data_path}\n\n{e}")
                errors_occurred = True
            pass
        else:
            errors_occurred = True
    if 'all_simulations_data' in globals():
        all_simulations_data[:] = [s for s in all_simulations_data if isinstance(s, dict) and s.get('name') != sim_name]
    final_message = f"Deletion of '{sim_name}' completed"
    if errors_occurred:
        final_message += " with errors."
    else:
        final_message += " successfully."
    if callable(globals().get('update_status')):
        update_status(final_message)
    if callable(globals().get('populate_simulations')):
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
             main_window.after(0, populate_simulations)
        else:
             populate_simulations()
    else:
        pass

def format_time(seconds: Union[float, int, None]) -> str:
    if seconds is None or seconds < 0 or math.isinf(seconds) or math.isnan(seconds):
        return "--:--:--"
    if seconds == 0:
        return "0s"
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    elif minutes > 0:
        return f"{minutes:02d}:{seconds:02d}"
    else:
        return f"{seconds}s"

def monitor_unity_progress(stop_event: threading.Event, operation_tag: str):
    global SIMULATION_PROJECT_PATH
    project_path = None
    if SIMULATION_PROJECT_PATH:
        try:
            project_path = Path(SIMULATION_PROJECT_PATH)
            if not project_path.is_dir():
                pass
        except Exception:
            update_status(f"[{operation_tag}] Error: Invalid project path. Cannot monitor.")
            return
    else:
        update_status(f"[{operation_tag}] Error: Project path not set. Cannot monitor.")
        return
    UPDATE_INTERVAL = 1.0
    SIZE_CHECK_INTERVAL = 5.0
    last_time_update = 0
    last_size_check_time = 0
    last_logged_mb = -1.0
    start_time = time.time()
    update_status(f"[{operation_tag}] Starting...")
    while not stop_event.is_set():
        current_time = time.time()
        if current_time - last_time_update >= UPDATE_INTERVAL:
            elapsed_time = current_time - start_time
            formatted_elapsed_time = format_time(elapsed_time)
            status_message = f"[{operation_tag}] Running... Elapsed: {formatted_elapsed_time}"
            update_status(status_message.ljust(60))
            last_time_update = current_time
        if project_path and (current_time - last_size_check_time >= SIZE_CHECK_INTERVAL):
            try:
                if project_path.is_dir():
                    current_bytes = get_folder_size(project_path)
                    current_mb = current_bytes / (1024*1024)
                    if abs(current_mb - last_logged_mb) > 1.0:
                         last_logged_mb = current_mb
                else:
                    if last_logged_mb != -999:
                         last_logged_mb = -999
            except Exception:
                 pass
            last_size_check_time = current_time
        time.sleep(0.3)

def run_unity_batchmode(exec_method: str, op_name: str, log_file_name: str, timeout: int = 600, extra_args: list = None) -> tuple[bool, Union[str, None]]:
    if not all([unity_path_ok, unity_version_ok, unity_projects_path_ok, SIMULATION_PROJECT_PATH, UNITY_EXECUTABLE]):
        update_status(f"Error: Cannot run Unity '{op_name}'. Check Unity configuration.")
        messagebox.showerror("Configuration Error", f"Cannot run the Unity {op_name} operation.\nPlease verify the Unity executable path, version, and projects path in Settings.")
        return False, None
    project_path_obj = Path(SIMULATION_PROJECT_PATH)
    if not project_path_obj.is_dir():
         update_status(f"Error: Project path does not exist: {project_path_obj}")
         messagebox.showerror("Project Not Found", f"The Unity project path does not exist or is not a directory:\n{project_path_obj}")
         return False, None
    log_path = project_path_obj / log_file_name
    command = [
        UNITY_EXECUTABLE,
        "-batchmode",
        "-quit",
        "-projectPath", str(project_path_obj.resolve()),
        "-executeMethod", exec_method,
        "-logFile", str(log_path.resolve())
    ]
    if extra_args:
        command.extend(extra_args)
    success = False
    stop_monitor_event = threading.Event()
    executable_path = None
    monitor_thread = threading.Thread(target=monitor_unity_progress, args=(stop_monitor_event, op_name.capitalize()), daemon=True)
    try:
        update_status(f"[{op_name.capitalize()}] Starting Unity process...")
        monitor_thread.start()
        creation_flags = 0
        process = subprocess.run(
            command,
            check=True,
            timeout=timeout,
            creationflags=creation_flags,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        update_status(f"[{op_name.capitalize()}] Unity process finished successfully.")
        success = True
        if "BuildScript.PerformBuild" in exec_method:
            update_status(f"[{op_name.capitalize()}] Verifying build output...")
            _, build_exe_path_str = get_build_target_and_executable(SIMULATION_PROJECT_PATH)
            if build_exe_path_str:
                build_exe_path = Path(build_exe_path_str)
                found = False
                for attempt in range(6):
                    time.sleep(0.5 * attempt)
                    if build_exe_path.exists() and (build_exe_path.is_file() or build_exe_path.is_dir()):
                        found = True
                        executable_path = str(build_exe_path)
                        break
                if found:
                    update_status(f"[{op_name.capitalize()}] Build executable verified.")
                else:
                    success = False
                    handle_unity_execution_error(FileNotFoundError(f"Build output '{build_exe_path.name}' not found in '{build_exe_path.parent}' after process completion."), op_name)
                    update_status(f"[Error] {op_name.capitalize()} failed: Build output missing.")
            else:
                 success = False
                 update_status(f"[Error] {op_name.capitalize()} failed: Could not determine output path.")
    except subprocess.CalledProcessError as e:
        handle_unity_execution_error(e, op_name)
        update_status(f"[Error] {op_name.capitalize()} failed (Exit Code {e.returncode}). See console/log: {log_path.name}")
    except subprocess.TimeoutExpired as e:
        handle_unity_execution_error(e, op_name)
        update_status(f"[Error] {op_name.capitalize()} timed out after {timeout}s. See log: {log_path.name}")
    except (FileNotFoundError, PermissionError) as e:
        handle_unity_execution_error(e, op_name)
        update_status(f"[Error] {op_name.capitalize()} failed (File Not Found or Permission). Check Unity path.")
    except Exception as e:
        handle_unity_execution_error(e, f"{op_name} (unexpected)")
        update_status(f"[Error] Unexpected error during {op_name}. Check console.")
    finally:
        stop_monitor_event.set()
        if monitor_thread.is_alive():
             monitor_thread.join(timeout=1.0)
    return success, executable_path

def run_prefab_material_tool() -> bool:
    update_status("Running prefab/material creation tool...")
    success, _ = run_unity_batchmode(
        exec_method="PrefabMaterialCreator.CreatePrefabsAndMaterials",
        op_name="Prefab Tool",
        log_file_name="prefab_tool_log.txt",
        timeout=600
    )
    if success:
         update_status("Prefab/material tool completed successfully.")
    else:
         update_status("Error during prefab/material creation. Check logs.")
    return success

def build_simulation_task(extra_args: list, callback):
    disable_all_interactions()
    success, final_exe_path = run_unity_batchmode(
        exec_method="BuildScript.PerformBuild",
        op_name="Build",
        log_file_name="build_log.txt",
        timeout=1800,
        extra_args=extra_args
    )
    if callback:
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
            main_window.after(0, lambda s=success, p=final_exe_path: callback(s, p))
        else:
             pass
    if 'main_window' in globals() and main_window and main_window.winfo_exists():
        main_window.after(10, enable_all_interactions)
    else:
         enable_all_interactions()

def build_simulation_threaded(callback=None):
    build_target, _ = get_build_target_and_executable(SIMULATION_PROJECT_PATH)
    if not build_target:
        update_status("Error: Build target unknown. Cannot start build.")
        messagebox.showerror("Build Error", "Could not determine the build target for your operating system.")
        return
    build_thread = threading.Thread(
        target=build_simulation_task,
        args=(["-buildTarget", build_target], callback),
        daemon=True
    )
    build_thread.start()

def open_simulation_executable():
    if not SIMULATION_PROJECT_PATH:
        update_status("Error: Project path not set. Cannot find executable.")
        messagebox.showerror("Error", "Project path is not set. Load a simulation first.")
        return
    _, exe_path_str = get_build_target_and_executable(SIMULATION_PROJECT_PATH)
    if not exe_path_str:
        messagebox.showerror("Error", "Could not determine the expected executable path for this OS.")
        return
    exe_path = Path(exe_path_str)
    if exe_path.exists():
        try:
            base_name = exe_path.name
            update_status(f"Launching: {base_name}...")
            if exe_path.is_dir():
                 subprocess.Popen(["open", str(exe_path)])
            else:
                 raise FileNotFoundError(f".app bundle not found or is not a directory: {exe_path}")
            update_status(f"Launched {base_name}.")
        except Exception as e:
            handle_unity_execution_error(e, f"launch simulation ({exe_path.name})")
            update_status(f"Error launching simulation: {e}")
    else:
        messagebox.showerror("Executable Not Found", f"The simulation executable was not found at:\n{exe_path}\n\nPlease build the simulation first.")
        update_status("Error: Simulation executable not found.")

def open_in_unity():
    if not all([unity_path_ok, unity_projects_path_ok, UNITY_EXECUTABLE, SIMULATION_PROJECT_PATH]):
        messagebox.showerror("Configuration Error", "Cannot open in Unity. Please check Unity executable and project paths in Settings.")
        return
    project_path_obj = Path(SIMULATION_PROJECT_PATH)
    if not project_path_obj.is_dir():
        messagebox.showerror("Project Not Found", f"The project path does not exist or is not a directory:\n{project_path_obj}")
        return
    try:
        app_bundle_to_open_path_str = None
        if UNITY_EXECUTABLE and "/Contents/MacOS/Unity" in str(UNITY_EXECUTABLE):
            potential_app_bundle = Path(UNITY_EXECUTABLE).parent.parent.parent
            if potential_app_bundle.name.endswith(".app"):
                app_bundle_to_open_path_str = str(potential_app_bundle)
        if app_bundle_to_open_path_str:
            command = ["open", "-a", app_bundle_to_open_path_str, "--args", "-projectPath", str(project_path_obj.resolve())]
        else:
            command = [UNITY_EXECUTABLE, "-projectPath", str(project_path_obj.resolve())]
        subprocess.Popen(command)
        update_status("Unity Editor is launching...")
    except Exception as e:
        handle_unity_execution_error(e, "open project in Unity")
        update_status("Error launching Unity Editor.")

def create_simulation_thread(sim_name: str, sim_desc: str):
    update_status(f"Creating '{sim_name}' using API...")
    success = False
    error_message_detail = f"An unknown error occurred during the creation of '{sim_name}'."
    try:
        try:
            SIMULATIONS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            error_message_detail = f"Could not create the base simulations directory:\n{SIMULATIONS_DIR}\n\n{type(e).__name__}: {e}"
            success = False
            if 'main_window' in globals() and main_window:
                 main_window.after(0, lambda msg=error_message_detail: messagebox.showerror("Critical Setup Error", msg))
            update_status("Critical directory creation error. Cannot continue.")
            return
        success, error_message = api_manager(sim_name, sim_desc, use_cache=True)
        if success:
            final_message = f"Simulation '{sim_name}' created successfully via API."
            update_status(final_message)
            if 'main_window' in globals() and main_window:
                 main_window.after(0, lambda name=sim_name: messagebox.showinfo("Success", f"Simulation '{name}' created successfully."))
            global all_simulations_data
            all_simulations_data = get_simulations()
            if 'main_window' in globals() and main_window:
                 main_window.after(50, populate_simulations)
        else:
            error_message_detail = error_message if error_message else f"Failed to create simulation '{sim_name}'. Reason unknown (check console logs)."
            update_status(f"Error creating '{sim_name}'. Check logs.")
            if 'main_window' in globals() and main_window:
                 main_window.after(0, lambda msg=error_message_detail: messagebox.showerror("Simulation Creation Failed", msg))
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        detailed_error = traceback.format_exc()
        error_message_detail = f"A critical unexpected error occurred during the simulation creation process:\n{error_type}: {error_msg}\n\nPlease check the console logs for a detailed traceback."
        if 'main_window' in globals() and main_window:
             main_window.after(0, lambda msg=error_message_detail: messagebox.showerror("Unexpected Creation Error", msg))
        update_status(f"Critical error during creation: {error_type}")
        success = False
    finally:
        if 'main_window' in globals() and main_window:
            main_window.after(100, enable_all_interactions)
        else:
             enable_all_interactions()

def _perform_blink_animation():
    global settings_button_blink_job
    if 'settings_btn' in globals() and settings_btn.winfo_exists() and 'main_window' in globals() and main_window.winfo_exists():
        mode_idx = get_color_mode_index()
        current_fg_color_tuple = settings_btn.cget("fg_color")
        normal_color_tuple = BTN_SETTINGS_FG_COLOR
        hover_color_tuple = _BLINK_COLOR
        actual_current_fg = settings_btn._apply_appearance_mode(current_fg_color_tuple)
        actual_normal_color = settings_btn._apply_appearance_mode(normal_color_tuple[mode_idx])
        if actual_current_fg == actual_normal_color:
            settings_btn.configure(fg_color=hover_color_tuple[mode_idx])
        else:
            settings_btn.configure(fg_color=normal_color_tuple[mode_idx])
        settings_button_blink_job = main_window.after(500, _perform_blink_animation)
    else:
        if settings_button_blink_job:
            if 'main_window' in globals() and main_window.winfo_exists():
                 main_window.after_cancel(settings_button_blink_job)
            settings_button_blink_job = None

def start_settings_button_blink():
    global settings_button_blink_job
    if settings_button_blink_job: return
    if 'settings_btn' in globals() and settings_btn.winfo_exists() and 'main_window' in globals() and main_window.winfo_exists():
        _perform_blink_animation()

def stop_settings_button_blink():
    global settings_button_blink_job
    if settings_button_blink_job:
        if 'main_window' in globals() and main_window.winfo_exists():
             main_window.after_cancel(settings_button_blink_job)
        settings_button_blink_job = None
    if 'settings_btn' in globals() and settings_btn.winfo_exists():
        mode_idx = get_color_mode_index()
        settings_btn.configure(fg_color=BTN_SETTINGS_FG_COLOR[mode_idx])

def perform_verification(show_results_box=False, on_startup=False):
    global unity_path_ok, unity_version_ok, unity_projects_path_ok, apis_key_ok, apis_models_ok, initial_verification_complete
    global UNITY_EXECUTABLE, UNITY_PROJECTS_PATH, API_BASE_URL, API_KEY
    global SIMULATION_PROJECT_PATH, ASSETS_FOLDER, STREAMING_ASSETS_FOLDER, SIMULATION_LOADED_FILE, last_simulation_loaded, all_simulations_data
    if not on_startup:
        update_status("Verifying configuration...")
    load_dotenv(DOTENV_PATH, override=True)
    unity_executable_from_env = os.environ.get("UNITY_EXECUTABLE")
    UNITY_PROJECTS_PATH = os.environ.get("UNITY_PROJECTS_PATH")
    API_BASE_URL = os.getenv("API_BASE_URL")
    API_KEY = os.getenv("API_KEY")
    unity_path_ok = unity_version_ok = unity_projects_path_ok = apis_key_ok = apis_models_ok = False
    results = []
    req_ver = UNITY_REQUIRED_VERSION_STRING
    resolved_unity_executable_str = None
    unity_exe_env_path = Path(unity_executable_from_env) if unity_executable_from_env else None
    is_macos_app_bundle_env = unity_exe_env_path and unity_exe_env_path.name.endswith(".app") and unity_exe_env_path.is_dir()
    if is_macos_app_bundle_env:
        resolved_unity_executable_str = str(unity_exe_env_path / "Contents" / "MacOS" / "Unity")
    UNITY_EXECUTABLE = resolved_unity_executable_str
    if not unity_executable_from_env:
        results.append("❌ Unity Executable: Path missing in .env file.")
    elif not unity_exe_env_path or not unity_exe_env_path.exists():
         results.append(f"❌ Unity Executable: Path does not exist:\n   '{unity_executable_from_env}'")
    elif not is_macos_app_bundle_env:
         results.append(f"❌ Unity Executable: Path is not a valid '.app' bundle directory:\n   '{unity_executable_from_env}'")
    elif not Path(UNITY_EXECUTABLE).is_file():
         results.append(f"❌ Unity Executable: Internal binary not found:\n   '{UNITY_EXECUTABLE}'")
    else:
        unity_path_ok = True
        results.append(f"✅ Unity Executable: Path OK ('{unity_executable_from_env}').")
        try:
            version_folder_name = unity_exe_env_path.parent.name
            if version_folder_name == req_ver:
                unity_version_ok = True
                results.append(f"✅ Unity Version: Parent directory of '.app' ('{version_folder_name}') matches required version '{req_ver}'.")
            else:
                results.append(f"❌ Unity Version: Parent directory of '.app' ('{version_folder_name}') does not match required version '{req_ver}'.")
        except Exception as path_err:
            results.append(f"⚠️ Unity Version: Error during path check: {path_err}")
    if not UNITY_PROJECTS_PATH:
        results.append("❌ Projects Path: Missing in .env file.")
    elif not Path(UNITY_PROJECTS_PATH).is_dir():
        results.append(f"❌ Projects Path: Path invalid or not a directory:\n   '{UNITY_PROJECTS_PATH}'")
    else:
        unity_projects_path_ok = True
        results.append(f"✅ Projects Path: Directory OK.")
        try:
            base_proj_path = Path(UNITY_PROJECTS_PATH)
            SIMULATION_PROJECT_PATH = base_proj_path / SIMULATION_PROJECT_NAME
            ASSETS_FOLDER = SIMULATION_PROJECT_PATH / "Assets"
            STREAMING_ASSETS_FOLDER = ASSETS_FOLDER / "StreamingAssets"
            SIMULATION_LOADED_FILE = STREAMING_ASSETS_FOLDER / "simulation_loaded.txt"
            last_simulation_loaded = read_last_loaded_simulation_name()
        except Exception as path_e:
             results.append(f"⚠️ Project Paths: Error constructing paths: {path_e}")
             unity_projects_path_ok = False

    should_blink_settings = not unity_path_ok or not unity_projects_path_ok or not API_BASE_URL or not API_KEY

    if not API_BASE_URL: results.append("❌ API Server URL: Missing in .env file."); results.append("   ↳ Cannot verify server/OpenAI config.")
    elif not API_KEY: results.append("❌ Client API Key: Missing in .env file."); results.append("   ↳ Cannot authenticate with API server.")
    else:
        results.append(f"ℹ️ API Server URL: {API_BASE_URL}")
        verify_url = f"{API_BASE_URL.rstrip('/')}/verify_config"
        headers = {'X-API-Key': API_KEY}
        try:
            if 'requests' not in sys.modules:
                 raise ImportError("The 'requests' library is required for API server communication.")
            response = requests.get(verify_url, headers=headers, timeout=15)
            response.raise_for_status()
            server_data = response.json()
            details = server_data.get('verification_details', {})
            client_auth_status = details.get('api_server_key_status', "ERROR")
            client_auth_ok = "ok" in client_auth_status.lower() or "verified" in client_auth_status.lower() or "✅" in client_auth_status
            server_openai_key_ok = server_data.get('openai_api_key_ok', False)
            server_primary_model_ok = server_data.get('primary_model_ok', False)
            apis_key_ok = client_auth_ok and server_openai_key_ok
            apis_models_ok = apis_key_ok and server_primary_model_ok
            results.append(details.get('api_server_key_status', '❔ Client API Key Status (Server): Unknown'))
            results.append(details.get('openai_api_key_status', '❔ OpenAI Key Status (Server): Unknown'))
            results.append(details.get('primary_model_status', '❔ Primary Model Status (Server): Unknown'))
            results.append(details.get('secondary_model_status', '❔ Secondary Model Status (Server): Unknown'))
            should_blink_settings = should_blink_settings or not (apis_key_ok and apis_models_ok)
        except ImportError as imp_err:
             results.append(f"❌ API Server Check: {imp_err}"); apis_key_ok = apis_models_ok = False; should_blink_settings = True
        except requests.exceptions.ConnectionError: results.append(f"❌ API Server Check: CONNECTION FAILED! ({API_BASE_URL})"); apis_key_ok = apis_models_ok = False; should_blink_settings = True
        except requests.exceptions.Timeout: results.append(f"❌ API Server Check: TIMEOUT! ({API_BASE_URL})"); apis_key_ok = apis_models_ok = False; should_blink_settings = True
        except requests.exceptions.RequestException as e:
            status = e.response.status_code if e.response is not None else '??'; err_txt = f"Request failed ({status})."; detail="N/A"
            if e.response is not None:
                try: detail = e.response.json().get('error', e.response.text[:100]+'...')
                except: detail = e.response.text[:100]+'...'; err_txt += f" Detail: {detail}"
                if status == 403: err_txt += "\n   ↳ Access DENIED. Is Client API_KEY correct?"
            results.append(f"❌ API Server Check: {err_txt}"); apis_key_ok = apis_models_ok = False; should_blink_settings = True
        except Exception as e: results.append(f"❌ API Server Check: Unexpected error: {type(e).__name__}"); apis_key_ok = apis_models_ok = False; should_blink_settings = True
    
    initial_verification_complete = True
    unity_status = "Unity OK" if unity_path_ok and unity_version_ok and unity_projects_path_ok else "Unity ERR"
    api_status = "API OK" if apis_key_ok and apis_models_ok else "API ERR"
    final_status_string = f"Status: {unity_status} | {api_status}"

    def update_blink_state_on_main_thread():
        if 'settings_btn' in globals() and settings_btn.winfo_exists():
            if should_blink_settings: start_settings_button_blink()
            else: stop_settings_button_blink()
    
    if 'main_window' in globals() and main_window.winfo_exists():
        if threading.current_thread() is not threading.main_thread():
            main_window.after(0, update_blink_state_on_main_thread)
        else:
            update_blink_state_on_main_thread()

    try:
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
            main_window.after(0, lambda: update_status(final_status_string))
            main_window.after(50, update_button_states)
            all_simulations_data = get_simulations()
            main_window.after(100, filter_simulations)
            if on_startup:
                error_messages = []
                if not unity_path_ok: error_messages.append("- Invalid Unity Executable path in .env (Must be the .app bundle).")
                elif not unity_version_ok: error_messages.append(f"- Unity path does not seem to match required version ({req_ver}).")
                if not unity_projects_path_ok: error_messages.append("- Invalid Unity Projects path in .env.")
                if not (unity_path_ok and unity_version_ok and unity_projects_path_ok):
                     error_messages.append("  (Core Unity features like Build/Load may fail)")
                api_errors_found = False
                if not API_BASE_URL: error_messages.append("- API Server URL missing in .env."); api_errors_found=True
                elif not API_KEY: error_messages.append("- Client API Key missing in .env."); api_errors_found=True
                elif not apis_key_ok: error_messages.append("- API Server: Auth Error or Server-side OpenAI Key Error."); api_errors_found=True
                elif not apis_models_ok: error_messages.append("- API Server: Primary Model Error (Server-side)."); api_errors_found=True
                if api_errors_found:
                     error_messages.append("  (API-based simulation creation will be disabled)")
                if error_messages:
                    startup_message = "Initial Configuration Issues Found:\n\n" + "\n".join(error_messages) + "\n\nPlease use 'Settings' to correct the .env file and then click 'Verify Config'."
                    main_window.after(300, lambda m=startup_message: messagebox.showwarning("Initial Configuration Issues", m))
    except Exception:
         pass
    if show_results_box:
        results_text = "Configuration Verification Results:\n\n" + "\n".join(results)
        all_checks_ok = unity_path_ok and unity_version_ok and unity_projects_path_ok and apis_key_ok and apis_models_ok
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
             message_type = messagebox.showinfo if all_checks_ok else messagebox.showwarning
             popup_title = "Verification Complete" if all_checks_ok else "Verification Issues Found"
             main_window.after(0, lambda title=popup_title, msg=results_text: message_type(title, msg))

def open_config_window():
    stop_settings_button_blink()
    if 'main_window' not in globals() or not main_window: return
    config_win = ctk.CTkToplevel(main_window)
    config_win.title("Settings (.env Configuration)")
    apply_icon(config_win)
    center_window(config_win, 700, 300)
    config_win.resizable(False, False)
    config_win.transient(main_window)
    config_win.grab_set()
    frame = ctk.CTkFrame(config_win)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    frame.grid_columnconfigure(1, weight=1)
    entries = {}
    def create_row(parent_frame, row_index, label_text, env_variable_name, dict_key, browse_for_file=True, add_browse_button=True):
        ctk.CTkLabel(parent_frame, text=label_text, anchor="w", font=APP_FONT).grid(row=row_index, column=0, padx=(0, 10), pady=5, sticky="w")
        current_value = os.environ.get(env_variable_name, "")
        entry_var = ctk.StringVar(value=current_value)
        entries[dict_key] = entry_var
        entry_widget = ctk.CTkEntry(parent_frame, textvariable=entry_var, font=APP_FONT)
        entry_widget.grid(row=row_index, column=1, padx=5, pady=5, sticky="ew")
        if add_browse_button:
            def browse_action():
                initial_dir = "/"
                current_path = entry_var.get()
                if current_path:
                    potential_dir = Path(current_path)
                    if potential_dir.is_file(): initial_dir = str(potential_dir.parent)
                    elif potential_dir.is_dir(): initial_dir = str(potential_dir)
                    elif potential_dir.name.endswith(".app") and potential_dir.parent.is_dir(): initial_dir = str(potential_dir.parent)

                elif dict_key == "projects_path" and Path.home().is_dir():
                    initial_dir = str(Path.home())
                selected_path = None
                if browse_for_file: # For Unity Executable, allow selecting .app bundle
                    selected_path = filedialog.askopenfilename(
                        title=f"Select {label_text}",
                        initialdir=initial_dir,
                        parent=config_win,
                        filetypes=[("Application", "*.app")] if platform.system() == "Darwin" else None
                    )
                else: # Browse for directory
                    selected_path = filedialog.askdirectory(
                        title=f"Select {label_text}",
                        initialdir=initial_dir,
                        parent=config_win
                    )
                if selected_path:
                    entry_var.set(selected_path)
            browse_button = ctk.CTkButton(parent_frame, text="...", width=30, command=browse_action, font=APP_FONT)
            browse_button.grid(row=row_index, column=2, padx=(5, 0), pady=5)
        else:
            frame.grid_columnconfigure(2, weight=0, minsize=35)
    create_row(frame, 0, "Unity Executable (.app):", "UNITY_EXECUTABLE", "unity_exe", browse_for_file=True, add_browse_button=True)
    create_row(frame, 1, "Unity Projects Folder:", "UNITY_PROJECTS_PATH", "projects_path", browse_for_file=False, add_browse_button=True)
    create_row(frame, 2, "API Server URL:", "API_BASE_URL", "api_url", browse_for_file=False, add_browse_button=False)
    create_row(frame, 3, "API Key (Client):", "API_KEY", "api_key", browse_for_file=False, add_browse_button=False)
    button_frame_bottom = ctk.CTkFrame(config_win, fg_color="transparent")
    button_frame_bottom.pack(fill="x", padx=20, pady=(0, 20))
    button_frame_bottom.columnconfigure(0, weight=1)
    button_frame_bottom.columnconfigure(1, weight=0)
    button_frame_bottom.columnconfigure(2, weight=0)
    button_frame_bottom.columnconfigure(3, weight=1)
    def save_config_action():
        unity_exe_path = entries['unity_exe'].get().strip()
        projects_folder_path = entries['projects_path'].get().strip()
        api_url = entries['api_url'].get().strip()
        api_key = entries['api_key'].get().strip()
        if not unity_exe_path or not projects_folder_path:
            messagebox.showerror("Input Error", "Unity Executable and Projects Folder paths are required.", parent=config_win)
            return
        if not api_url:
             messagebox.showwarning("Warning", "API Server URL is empty.\nAPI features will be disabled.", parent=config_win)
        elif not (api_url.startswith("http://") or api_url.startswith("https://")):
             messagebox.showerror("Input Error", "API URL format is invalid (must start with http:// or https://).", parent=config_win)
             return
        if not api_key:
            messagebox.showwarning("Warning", "The API Key (Client) field is empty.\nAuthentication with the API server will fail, disabling API features.", parent=config_win)
        try:
            with open(DOTENV_PATH, "w", encoding='utf-8') as f:
                f.write(f"UNITY_EXECUTABLE={unity_exe_path}\n")
                f.write(f"UNITY_PROJECTS_PATH={projects_folder_path}\n")
                f.write(f"API_BASE_URL={api_url}\n")
                f.write(f"API_KEY={api_key}\n")
            messagebox.showinfo("Success", "Settings saved to .env file.\nRe-running verification...", parent=config_win)
            config_win.destroy()
            if 'main_window' in globals() and main_window:
                 main_window.after(100, lambda: perform_verification(show_results_box=True))
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not write to the .env file:\n{e}", parent=config_win)
    mode_idx = get_color_mode_index()
    save_button = ctk.CTkButton(button_frame_bottom, text="Save and Verify", command=save_config_action, font=APP_FONT,
                                fg_color=COLOR_SUCCESS_GENERAL[mode_idx], hover_color=COLOR_INFO_GENERAL[mode_idx])
    save_button.grid(row=0, column=1, padx=10, pady=10)
    cancel_button = ctk.CTkButton(button_frame_bottom, text="Cancel", command=config_win.destroy, font=APP_FONT,
                                  fg_color=COLOR_WARNING_GENERAL[mode_idx], hover_color=COLOR_DANGER_GENERAL[mode_idx])
    cancel_button.grid(row=0, column=2, padx=10, pady=10)
    config_win.wait_window()

def cleanup_simulation_logger_data(actual_simulation_names: set):
    logger_data_path = None
    try:
        persistent_path = find_unity_persistent_path(UNITY_PRODUCT_NAME)
        if not persistent_path:
            return
        logger_data_path = persistent_path / LOG_SUBFOLDER
        if not logger_data_path.is_dir():
            return
        deleted_count = 0
        error_count = 0
        for item in logger_data_path.iterdir():
            if item.is_dir():
                folder_name = item.name
                if folder_name not in actual_simulation_names:
                    try:
                        shutil.rmtree(item)
                        deleted_count += 1
                    except PermissionError:
                        error_count += 1
                    except OSError:
                        error_count += 1
                    except Exception:
                        error_count += 1
    except Exception:
        pass

def populate_simulations():
    if not initial_verification_complete:
        return
    if callable(globals().get('update_status')): update_status("Reloading simulation list and performing cleanup...")
    global all_simulations_data, last_simulation_loaded, SIMULATION_LOADED_FILE
    all_simulations_data = get_simulations()
    actual_sim_names = {sim['name'] for sim in all_simulations_data if isinstance(sim, dict) and 'name' in sim}
    current_loaded_in_file = read_last_loaded_simulation_name()
    last_simulation_loaded = current_loaded_in_file
    if current_loaded_in_file and current_loaded_in_file not in actual_sim_names:
        state_file_path = None
        if isinstance(SIMULATION_LOADED_FILE, Path):
            state_file_path = SIMULATION_LOADED_FILE
        elif isinstance(SIMULATION_LOADED_FILE, str):
             try: state_file_path = Path(SIMULATION_LOADED_FILE)
             except Exception: pass
        if state_file_path and state_file_path.is_file():
            try:
                state_file_path.unlink()
                last_simulation_loaded = None
            except PermissionError:
                pass
            except Exception:
                pass
        else:
            last_simulation_loaded = None
    cleanup_simulation_logger_data(actual_sim_names)
    all_simulations_data.sort(key=lambda x: x.get('name', '').lower())
    filter_simulations()
    status_msg = f"List refreshed. Found {len(all_simulations_data)} total simulation(s)."
    if last_simulation_loaded:
         status_msg += f" ('{last_simulation_loaded}' is loaded)"
    if callable(globals().get('update_status')): update_status(status_msg)
    if callable(globals().get('update_button_states')): update_button_states()

def filter_simulations(event=None):
    if 'sim_tree' not in globals() or 'search_entry' not in globals():
        return
    search_term = search_entry.get().lower().strip()
    try:
        for item in sim_tree.get_children():
            sim_tree.delete(item)
    except tk.TclError:
        return
    displayed_count = 0
    for sim_data in all_simulations_data:
        if search_term and search_term not in sim_data['name'].lower():
            continue
        is_loaded = (sim_data["name"] == last_simulation_loaded)
        row_tag = "evenrow" if displayed_count % 2 == 0 else "oddrow"
        item_tags = [row_tag]
        if is_loaded:
            item_tags.append("loaded")
        loaded_symbol = loaded_indicator_text if is_loaded else ""
        play_symbol = play_icon_text
        delete_symbol = delete_icon_text
        try:
            sim_tree.insert("", "end", iid=sim_data["name"],
                            values=(
                                sim_data["name"],
                                sim_data["creation"],
                                sim_data["last_opened"],
                                loaded_symbol,
                                play_symbol,
                                delete_symbol
                            ),
                            tags=tuple(item_tags))
            displayed_count += 1
        except tk.TclError:
            pass
    status_msg = status_label.cget("text")
    if initial_verification_complete:
        if search_term:
            status_msg = f"Displaying {displayed_count} of {len(all_simulations_data)} simulation(s) matching '{search_term}'."
        else:
            status_msg = f"Displaying {len(all_simulations_data)} simulation(s)."
        if last_simulation_loaded:
             status_msg += f" ('{last_simulation_loaded}' is loaded)"
    update_status(status_msg)
    if 'last_sort_column' in globals() and last_sort_column:
        current_reverse = sort_order.get(last_sort_column, False)
        sort_column(sim_tree, last_sort_column, current_reverse)
    update_button_states()

def clear_search():
    if 'search_entry' in globals():
        search_entry.delete(0, 'end')
        filter_simulations()

def update_button_states():
    if 'main_window' not in globals() or not main_window or not main_window.winfo_exists() or is_build_running:
        return
    has_selection = bool(sim_tree.selection())
    can_create = apis_key_ok and apis_models_ok
    def get_state(enabled_condition):
        return "normal" if enabled_condition else "disabled"
    settings_enabled = not is_build_running
    verify_enabled = not is_build_running
    clear_cache_enabled = not is_build_running
    unity_down_enabled = not is_build_running
    about_enabled = not is_build_running
    theme_switch_enabled = not is_build_running
    exit_enabled = not is_build_running
    reload_enabled = not is_build_running
    graph_enabled = has_selection and not is_build_running
    create_enabled = can_create and not is_build_running
    search_enabled = not is_build_running
    mode_idx = get_color_mode_index()
    disabled_fg = COLOR_DISABLED_GENERAL[mode_idx]
    try:
        if 'reload_btn' in globals(): reload_btn.configure(state=get_state(reload_enabled), fg_color=BTN_RELOAD_FG_COLOR[mode_idx] if reload_enabled else disabled_fg)
        if 'graph_btn' in globals(): graph_btn.configure(state=get_state(graph_enabled), fg_color=BTN_GRAPH_FG_COLOR[mode_idx] if graph_enabled else disabled_fg)
        if 'create_btn' in globals(): create_btn.configure(state=get_state(create_enabled), fg_color=BTN_CREATE_FG_COLOR[mode_idx] if create_enabled else disabled_fg)
        if settings_button_blink_job is None:
            if 'settings_btn' in globals():
                settings_btn.configure(state=get_state(settings_enabled), fg_color=BTN_SETTINGS_FG_COLOR[mode_idx] if settings_enabled else disabled_fg)
        elif 'settings_btn' in globals():
            settings_btn.configure(state=get_state(settings_enabled))
        if 'verify_btn' in globals(): verify_btn.configure(state=get_state(verify_enabled), fg_color=BTN_VERIFY_FG_COLOR[mode_idx], hover_color=BTN_VERIFY_HOVER_COLOR[mode_idx], text_color=BTN_VERIFY_TEXT_COLOR[mode_idx])
        if 'clear_cache_btn' in globals(): clear_cache_btn.configure(state=get_state(clear_cache_enabled), fg_color=BTN_EXIT_FG_COLOR[mode_idx] if clear_cache_enabled else disabled_fg)
        if 'unity_down_btn' in globals(): unity_down_btn.configure(state=get_state(unity_down_enabled), fg_color=BTN_UNITY_DOWN_FG_COLOR[mode_idx], hover_color=BTN_UNITY_DOWN_HOVER_COLOR[mode_idx], text_color=BTN_UNITY_DOWN_TEXT_COLOR[mode_idx])
        if 'about_btn' in globals(): about_btn.configure(state=get_state(about_enabled), fg_color=BTN_ABOUT_FG_COLOR[mode_idx], hover_color=BTN_ABOUT_HOVER_COLOR[mode_idx], text_color=BTN_ABOUT_TEXT_COLOR[mode_idx])
        if 'exit_btn' in globals(): exit_btn.configure(state=get_state(exit_enabled), fg_color=BTN_EXIT_FG_COLOR[mode_idx], hover_color=BTN_EXIT_HOVER_COLOR[mode_idx], text_color=BTN_EXIT_TEXT_COLOR[mode_idx])
        if 'theme_switch' in globals(): theme_switch.configure(state=get_state(theme_switch_enabled))
        if 'search_entry' in globals(): search_entry.configure(state=get_state(search_enabled))
        if 'clear_search_btn' in globals(): clear_search_btn.configure(state=get_state(search_enabled), fg_color=BTN_CLEARSEARCH_FG_COLOR[mode_idx], hover_color=BTN_CLEARSEARCH_HOVER_COLOR[mode_idx], text_color=BTN_CLEARSEARCH_TEXT_COLOR[mode_idx])
    except (NameError, tk.TclError):
        pass

def on_load_simulation_request(simulation_name: str):
    global is_build_running
    if is_build_running:
        return
    if not all([unity_path_ok, unity_version_ok, unity_projects_path_ok]):
        messagebox.showerror("Unity Configuration Error", "Cannot load simulation: Unity path, version, or projects path is invalid. Please check Settings.")
        return
    if simulation_name == last_simulation_loaded:
        update_status(f"'{simulation_name}' is already loaded. Showing options...")
        update_last_opened(simulation_name)
        _, current_executable = get_build_target_and_executable(SIMULATION_PROJECT_PATH)
        if 'main_window' in globals() and main_window:
            main_window.after(0, lambda s=simulation_name, p=current_executable: show_options_window(s, p))
        return
    disable_all_interactions()
    update_status(f"Starting load process for '{simulation_name}'...")
    load_thread = threading.Thread(target=load_simulation_logic, args=(simulation_name,), daemon=True)
    load_thread.start()

def load_simulation_logic(simulation_name: str):
    try:
        update_status(f"Load '{simulation_name}': Ensuring Unity is closed...");
        ensure_unity_closed()
        update_status(f"Load '{simulation_name}': Copying simulation files...");
        copy_ok = load_simulation(simulation_name)
        if copy_ok:
            update_status(f"Load '{simulation_name}': Running prefab/material tool...");
            prefab_ok = run_prefab_material_tool()
            if prefab_ok:
                update_status(f"Load '{simulation_name}': Starting simulation build...");
                build_simulation_threaded(callback=lambda ok, path: build_callback(ok, simulation_name, path))
            else:
                update_status(f"Error in post-load (prefab tool) for '{simulation_name}'. Build cancelled.")
                messagebox.showerror("Post-Load Error", f"The prefab/material creation tool failed for '{simulation_name}'.\nThe simulation build has been cancelled. Check console/logs.")
                if 'main_window' in globals() and main_window: main_window.after(10, enable_all_interactions)
        else:
            update_status(f"Error loading files for '{simulation_name}'. Load process stopped.");
            if 'main_window' in globals() and main_window: main_window.after(10, enable_all_interactions)
    except Exception:
        update_status(f"Critical error during load sequence for '{simulation_name}'. Check console.")
        if 'main_window' in globals() and main_window: main_window.after(10, enable_all_interactions)

def build_callback(success: bool, simulation_name: str, executable_path: Union[str, None]):
    if success:
        if executable_path and Path(executable_path).exists():
            update_status(f"Build for '{simulation_name}' completed successfully.")
            show_options_window(simulation_name, executable_path)
        elif executable_path:
             update_status(f"Build '{simulation_name}' finished, but executable not found: {executable_path}")
             messagebox.showerror("Build Error", f"Build for '{simulation_name}' completed, but the executable was not found at the expected location:\n{executable_path}\n\nPlease build the simulation first.")
        else:
            update_status(f"Build '{simulation_name}' finished, but executable path unknown.")
            messagebox.showerror("Build Error", f"Build for '{simulation_name}' completed, but the executable path could not be determined.")
    else:
        update_status(f"Build process for '{simulation_name}' failed. Check logs/console.")

def on_delete_simulation_request(simulation_name: str):
    global is_build_running
    if is_build_running:
        return
    delete_simulation(simulation_name)

def on_show_graphs_thread():
    global is_build_running
    if is_build_running:
        return
    selected_items = sim_tree.selection()
    if not selected_items:
        messagebox.showwarning("No Selection", "Please select a simulation from the list to view its statistics.")
        return
    sim_name = sim_tree.item(selected_items[0], "values")[0]
    disable_all_interactions()
    update_status(f"Generating statistics graphs for '{sim_name}'...")
    graph_thread = threading.Thread(target=show_graphs_logic, args=(sim_name,), daemon=True)
    graph_thread.start()

def show_graphs_logic(sim_name: str):
    if not callable(globals().get('find_simulation_data_path')) or \
       not callable(globals().get('SimulationGraphics')) or \
       not callable(globals().get('open_graphs_folder')):
        messagebox.showerror("Internal Error", "Required graph generation functions are not defined.")
        if 'main_window' in globals() and main_window: main_window.after(0, enable_all_interactions)
        return
    try:
        if callable(globals().get('update_status')): update_status(f"Locating data for '{sim_name}'...")
        simulation_data_dir = find_simulation_data_path(sim_name)
        if not simulation_data_dir:
            if callable(globals().get('update_status')): update_status(f"Error: Data directory not found for '{sim_name}'.")
            return
        csv_path = simulation_data_dir / CSV_FILENAME
        graphs_dir = simulation_data_dir / GRAPHICS_SUBFOLDER
        if not csv_path.is_file():
            messagebox.showerror("Missing Data",
                                 f"The required statistics file ('{CSV_FILENAME}') for simulation '{sim_name}' was not found in:\n{simulation_data_dir}\n\nCannot generate graphs.")
            if callable(globals().get('update_status')): update_status(f"Error: Statistics CSV file missing for '{sim_name}'.")
            return
        if callable(globals().get('update_status')): update_status(f"Generating graphs for '{sim_name}'...")
        SimulationGraphics(sim_name)
        if callable(globals().get('update_status')): update_status(f"Graph generation attempted. Opening graphs folder for '{sim_name}'...")
        open_graphs_folder(sim_name)
        if callable(globals().get('update_status')): update_status(f"Graph process completed for '{sim_name}'.")
    except FileNotFoundError as e:
        messagebox.showerror("File Error", f"A required file was not found during the graph process:\n{e}")
        if callable(globals().get('update_status')): update_status(f"Error: File not found while processing '{sim_name}'.")
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred while processing graphs for '{sim_name}':\n{type(e).__name__}: {e}")
        if callable(globals().get('update_status')): update_status(f"Error processing graphs for '{sim_name}'. Check console.")
    finally:
        try:
            if 'main_window' in globals() and main_window is not None and main_window.winfo_exists():
                 main_window.after(0, enable_all_interactions)
            elif callable(globals().get('enable_all_interactions')):
                 enable_all_interactions()()
        except NameError:
            pass
        except Exception:
            pass

def on_create_simulation():
    global is_build_running
    if is_build_running:
        return
    if not apis_key_ok or not apis_models_ok:
        messagebox.showerror("API Configuration Error", "Cannot create simulation: Invalid or unverified API Key or API Server configuration.\nPlease check Settings and Verify Config.")
        return
    sim_name = custom_askstring("Create New Simulation", "Enter a unique name for the new simulation:")
    if sim_name is None:
        update_status("Simulation creation cancelled.")
        return
    sim_name = sim_name.strip()
    invalid_chars = r'<>:"/\|?*' + "".join(map(chr, range(32)))
    if not sim_name:
         messagebox.showerror("Invalid Name", "Simulation name cannot be empty.")
         update_status("Invalid simulation name (empty).")
         return
    if any(c in invalid_chars for c in sim_name):
        messagebox.showerror("Invalid Name", f"Simulation name '{sim_name}' contains invalid characters ({invalid_chars}).")
        update_status("Invalid simulation name (characters).")
        return
    if (SIMULATIONS_DIR / sim_name).exists():
        messagebox.showerror("Name Exists", f"A simulation named '{sim_name}' already exists. Please choose a different name.")
        update_status(f"Simulation '{sim_name}' already exists.")
        return
    sim_desc = custom_askstring("Simulation Description", "Provide a brief description for the simulation (e.g., 'EColi red fast, SCerevisiae blue slow'):")
    if sim_desc is None:
        update_status("Simulation creation cancelled.")
        return
    sim_desc = sim_desc.strip()
    if not sim_desc:
         if not messagebox.askyesno("Empty Description", "The description is empty. Continue anyway?", icon='question'):
              update_status("Simulation creation cancelled.")
              return
    disable_all_interactions()
    update_status(f"Initiating creation of '{sim_name}' via API...")
    creation_thread = threading.Thread(target=create_simulation_thread, args=(sim_name, sim_desc), daemon=True)
    creation_thread.start()

def show_options_window(simulation_name: str, executable_path: Union[str, None]):
    if 'main_window' not in globals() or not main_window: return
    options_win = ctk.CTkToplevel(main_window)
    options_win.title(f"Options for '{simulation_name}'")
    apply_icon(options_win)
    center_window(options_win, 380, 200)
    options_win.resizable(False, False)
    options_win.transient(main_window)
    options_win.grab_set()
    frame = ctk.CTkFrame(options_win)
    frame.pack(expand=True, fill="both", padx=20, pady=20)
    ctk.CTkLabel(frame, text=f"Simulation '{simulation_name}' is loaded and built.", font=APP_FONT_BOLD).pack(pady=(0, 15))
    executable_exists = executable_path and Path(executable_path).exists()
    run_button_state = "normal" if executable_exists else "disabled"
    def run_and_close():
        open_simulation_executable()
        options_win.destroy()
    def open_unity_and_close():
        open_in_unity()
        options_win.destroy()
    mode_idx = get_color_mode_index()
    run_button = ctk.CTkButton(frame, text="Run Simulation", command=run_and_close, state=run_button_state, font=APP_FONT, height=40,
                               fg_color=COLOR_SUCCESS_GENERAL[mode_idx] if executable_exists else COLOR_DISABLED_GENERAL[mode_idx],
                               hover_color=COLOR_INFO_GENERAL[mode_idx] if executable_exists else COLOR_DISABLED_GENERAL[mode_idx])
    run_button.pack(pady=8, fill="x", padx=10)
    if not executable_exists:
        reason = f"Executable not found at:\n{executable_path}" if executable_path else "Executable path is unknown."
        ctk.CTkLabel(frame, text=reason, text_color="gray", font=("Segoe UI", 9)).pack(pady=(0, 5))
    open_editor_button = ctk.CTkButton(frame, text="Open Project in Unity Editor", command=open_unity_and_close, font=APP_FONT, height=40,
                                     fg_color="#1E88E5", hover_color="#42A5F5")
    open_editor_button.pack(pady=8, fill="x", padx=10)
    update_status(f"Options available for loaded simulation '{simulation_name}'.")
    options_win.wait_window()

def handle_tree_click(event):
    global is_build_running
    if is_build_running: return
    region = sim_tree.identify_region(event.x, event.y)
    item_id = sim_tree.identify_row(event.y)
    if region == "cell" and item_id:
        column_id_str = sim_tree.identify_column(event.x)
        if not column_id_str:
            cancel_tooltip(sim_tree)
            return
        try:
            column_index = int(column_id_str.replace('#','')) - 1
            column_ids_tuple = sim_tree['columns']
            if 0 <= column_index < len(column_ids_tuple):
                column_name = column_ids_tuple[column_index]
                simulation_name = sim_tree.item(item_id, "values")[0]
                sim_tree.selection_set(item_id)
                sim_tree.focus(item_id)
                update_button_states()
                hide_tooltip()
                if column_name == "col_load":
                    on_load_simulation_request(simulation_name)
                elif column_name == "col_delete":
                    on_delete_simulation_request(simulation_name)
            else: cancel_tooltip(sim_tree)
        except (ValueError, IndexError, tk.TclError):
            cancel_tooltip(sim_tree)
    elif region == "heading":
        pass
    else:
        cancel_tooltip(sim_tree)

def handle_tree_motion(event):
    global is_build_running
    if is_build_running: return
    region = sim_tree.identify_region(event.x, event.y)
    item_id = sim_tree.identify_row(event.y)
    if region == "cell" and item_id:
        column_id_str = sim_tree.identify_column(event.x)
        if not column_id_str: cancel_tooltip(sim_tree); return
        try:
            column_index = int(column_id_str.replace('#','')) - 1
            column_ids_tuple = sim_tree['columns']
            if 0 <= column_index < len(column_ids_tuple):
                column_name = column_ids_tuple[column_index]
                tooltip_text = None
                simulation_name = sim_tree.item(item_id, 'values')[0]
                if column_name == "col_load":
                    tooltip_text = f"Load / Run Simulation '{simulation_name}'"
                elif column_name == "col_delete":
                    tooltip_text = f"Delete Simulation '{simulation_name}'"
                elif column_name == "col_loaded":
                    cell_value = sim_tree.set(item_id, column=column_name)
                    if cell_value == loaded_indicator_text:
                        tooltip_text = f"Simulation '{simulation_name}' is currently loaded in the Unity project."
                if tooltip_text:
                    schedule_tooltip(sim_tree, tooltip_text)
                else:
                    cancel_tooltip(sim_tree)
            else: cancel_tooltip(sim_tree)
        except (ValueError, IndexError, tk.TclError):
            cancel_tooltip(sim_tree)
    else:
        cancel_tooltip(sim_tree)

def handle_tree_leave(event):
    cancel_tooltip(sim_tree)

def load_logo(image_path: Union[str, Path], target_width: int) -> Union[ImageTk.PhotoImage, None]:
    global logo_photo_ref
    try:
        image_path_obj = Path(image_path)
        if not image_path_obj.is_file():
            return None
        img = Image.open(image_path_obj)
        width_percent = (target_width / float(img.size[0]))
        new_height = int((float(img.size[1]) * float(width_percent)))
        img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
        logo_photo_ref = ImageTk.PhotoImage(img)
        return logo_photo_ref
    except FileNotFoundError:
        return None
    except Exception:
        return None

def update_treeview_style():
    if 'sim_tree' not in globals() or 'main_window' not in globals() or not main_window.winfo_exists():
        return
    mode_idx = get_color_mode_index()
    mode_str = "Dark" if mode_idx == 1 else "Light"
    try:
        bg_color = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        fg_color = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        select_bg_color = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        select_fg_color = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["text_color"])
        header_bg_color = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["border_color"])
        header_fg_color = fg_color
        odd_row_bg = main_window._apply_appearance_mode(("#FFFFFF", "#3A3A3A"))
        even_row_bg = main_window._apply_appearance_mode(("#F5F5F5", "#343434"))
        loaded_row_bg = main_window._apply_appearance_mode(("#E8F5E9", "#2E7D32"))
        loaded_row_fg = fg_color
    except Exception:
        if mode_str == "Dark":
            bg_color, fg_color = "#2B2B2B", "white"
            select_bg_color, select_fg_color = "#565B5E", "white"
            header_bg_color, header_fg_color = "#4A4D50", "white"
            odd_row_bg, even_row_bg = "#3A3A3A", "#343434"
            loaded_row_bg, loaded_row_fg = "#2E7D32", "white"
        else:
            bg_color, fg_color = "#FFFFFF", "black"
            select_bg_color, select_fg_color = "#DDF0FF", "black"
            header_bg_color, header_fg_color = "#EAEAEA", "black"
            odd_row_bg, even_row_bg = "#FFFFFF", "#F5F5F5"
            loaded_row_bg, loaded_row_fg = "#E8F5E9", "black"
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Treeview",
                    background=bg_color,
                    foreground=fg_color,
                    fieldbackground=bg_color,
                    rowheight=28,
                    font=TREEVIEW_FONT)
    style.configure("Treeview.Heading",
                    font=TREEVIEW_HEADER_FONT,
                    background=header_bg_color,
                    foreground=header_fg_color,
                    relief="flat",
                    padding=(10, 5))
    style.map("Treeview.Heading",
              relief=[('active', 'groove'), ('!active', 'flat')])
    style.map('Treeview',
              background=[('selected', select_bg_color)],
              foreground=[('selected', select_fg_color)])
    sim_tree.tag_configure('oddrow', background=odd_row_bg, foreground=fg_color)
    sim_tree.tag_configure('evenrow', background=even_row_bg, foreground=fg_color)
    sim_tree.tag_configure('loaded', background=loaded_row_bg, foreground=loaded_row_fg)

def toggle_appearance_mode():
    current_mode = ctk.get_appearance_mode()
    new_mode = "Dark" if current_mode == "Light" else "Light"
    ctk.set_appearance_mode(new_mode)
    if 'theme_switch' in globals() and theme_switch:
        theme_switch.configure(text=f"{new_mode} Mode")
    if 'main_window' in globals() and main_window:
         main_window.after(50, update_treeview_style)
    mode_idx = get_color_mode_index()
    try:
        logo_path = LOGO_PATHS[mode_idx]
        new_logo_photo = load_logo(logo_path, LOGO_WIDTH - 20)
        if new_logo_photo and 'sidebar_frame' in globals() and sidebar_frame.winfo_exists():
             logo_widget = None
             for w in sidebar_frame.winfo_children():
                  if isinstance(w, ctk.CTkLabel) and hasattr(w, 'image'):
                       logo_widget = w
                       break
             if logo_widget:
                 logo_widget.configure(image=new_logo_photo)
                 logo_widget.image = new_logo_photo
        if 'settings_btn' in globals(): settings_btn.configure(fg_color=BTN_SETTINGS_FG_COLOR[mode_idx], hover_color=BTN_SETTINGS_HOVER_COLOR[mode_idx], text_color=BTN_SETTINGS_TEXT_COLOR[mode_idx])
        if 'verify_btn' in globals(): verify_btn.configure(fg_color=BTN_VERIFY_FG_COLOR[mode_idx], hover_color=BTN_VERIFY_HOVER_COLOR[mode_idx], text_color=BTN_VERIFY_TEXT_COLOR[mode_idx])
        if 'unity_down_btn' in globals(): unity_down_btn.configure(fg_color=BTN_UNITY_DOWN_FG_COLOR[mode_idx], hover_color=BTN_UNITY_DOWN_HOVER_COLOR[mode_idx], text_color=BTN_UNITY_DOWN_TEXT_COLOR[mode_idx])
        if 'about_btn' in globals(): about_btn.configure(fg_color=BTN_ABOUT_FG_COLOR[mode_idx], hover_color=BTN_ABOUT_HOVER_COLOR[mode_idx], text_color=BTN_ABOUT_TEXT_COLOR[mode_idx])
        if 'exit_btn' in globals(): exit_btn.configure(fg_color=BTN_EXIT_FG_COLOR[mode_idx], hover_color=BTN_EXIT_HOVER_COLOR[mode_idx], text_color=BTN_EXIT_TEXT_COLOR[mode_idx])
        if 'reload_btn' in globals(): reload_btn.configure(fg_color=BTN_RELOAD_FG_COLOR[mode_idx], hover_color=BTN_RELOAD_HOVER_COLOR[mode_idx], text_color=BTN_RELOAD_TEXT_COLOR[mode_idx])
        if 'graph_btn' in globals(): graph_btn.configure(fg_color=BTN_GRAPH_FG_COLOR[mode_idx], hover_color=BTN_GRAPH_HOVER_COLOR[mode_idx], text_color=BTN_GRAPH_TEXT_COLOR[mode_idx])
        if 'create_btn' in globals(): create_btn.configure(fg_color=BTN_CREATE_FG_COLOR[mode_idx], hover_color=BTN_CREATE_HOVER_COLOR[mode_idx], text_color=BTN_CREATE_TEXT_COLOR[mode_idx])
        if 'clear_search_btn' in globals(): clear_search_btn.configure(fg_color=BTN_CLEARSEARCH_FG_COLOR[mode_idx], hover_color=BTN_CLEARSEARCH_HOVER_COLOR[mode_idx], text_color=BTN_CLEARSEARCH_TEXT_COLOR[mode_idx])
        if 'clear_cache_btn' in globals(): clear_cache_btn.configure(fg_color=BTN_EXIT_FG_COLOR[mode_idx], hover_color=BTN_EXIT_HOVER_COLOR[mode_idx], text_color=BTN_EXIT_TEXT_COLOR[mode_idx])
        update_button_states()
    except NameError:
        pass
    except Exception:
        pass

main_window = ctk.CTk()
apply_icon(main_window)
main_window.title("Colony Dynamics Simulator v1.0")
initial_width=1050
initial_height=700
center_window(main_window, initial_width, initial_height)
main_window.resizable(True, True)
main_window.minsize(850, 550)
main_window.columnconfigure(0, weight=0)
main_window.columnconfigure(1, weight=1)
main_window.rowconfigure(0, weight=1)
main_window.rowconfigure(1, weight=0)
sidebar_width=200
sidebar_frame = ctk.CTkFrame(main_window, width=sidebar_width, corner_radius=5, fg_color=COLOR_SIDEBAR_BG)
sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
sidebar_frame.grid_propagate(False)
sidebar_frame.columnconfigure(0, weight=1)
initial_mode = ctk.get_appearance_mode()
mode_idx = get_color_mode_index()
logo_path = LOGO_PATHS[mode_idx]
logo_photo = load_logo(logo_path, LOGO_WIDTH - 20)
if logo_photo:
    logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="")
    logo_label.pack(pady=(20, 10), padx=10)
    logo_label.image = logo_photo
else:
    ctk.CTkLabel(sidebar_frame, text="[Logo]", font=(APP_FONT[0], 14, "italic")).pack(pady=(20, 10), padx=10)
ctk.CTkLabel(sidebar_frame, text="Menu", font=(APP_FONT[0], 16, "bold")).pack(pady=(5, 15), padx=10)
settings_btn = ctk.CTkButton(sidebar_frame, text="Settings (.env)", command=open_config_window, font=APP_FONT,
                             fg_color=BTN_SETTINGS_FG_COLOR[mode_idx], hover_color=BTN_SETTINGS_HOVER_COLOR[mode_idx], text_color=BTN_SETTINGS_TEXT_COLOR[mode_idx])
settings_btn.pack(fill="x", padx=15, pady=5)
verify_btn = ctk.CTkButton(sidebar_frame, text="Verify Config", command=lambda: perform_verification(show_results_box=True), font=APP_FONT,
                           fg_color=BTN_VERIFY_FG_COLOR[mode_idx], hover_color=BTN_VERIFY_HOVER_COLOR[mode_idx], text_color=BTN_VERIFY_TEXT_COLOR[mode_idx])
verify_btn.pack(fill="x", padx=15, pady=5)
clear_cache_btn = ctk.CTkButton(sidebar_frame, text="Clear API Cache", command=clear_api_cache, font=APP_FONT,
                                fg_color=BTN_EXIT_FG_COLOR[mode_idx], hover_color=BTN_EXIT_HOVER_COLOR[mode_idx], text_color=BTN_EXIT_TEXT_COLOR[mode_idx])
clear_cache_btn.pack(fill="x", padx=15, pady=5)
separator = ctk.CTkFrame(sidebar_frame, height=2, fg_color="gray")
separator.pack(fill="x", padx=15, pady=15)

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
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.message_label = ctk.CTkLabel(self, text=self._message, font=APP_FONT, justify="left", wraplength=400)
        self.message_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 15), sticky="w")
        link_frame = ctk.CTkFrame(self, fg_color="transparent")
        link_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
        link_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(link_frame, text="Download Link:", font=APP_FONT_BOLD).grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.link_entry = ctk.CTkEntry(link_frame, font=APP_FONT)
        self.link_entry.insert(0, self._download_url)
        self.link_entry.configure(state="readonly")
        self.link_entry.grid(row=0, column=1, sticky="ew")
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="e")
        mode_idx = get_color_mode_index()
        self.copy_button = ctk.CTkButton(button_frame, text="Copy Link", command=self.copy_link, width=100, font=APP_FONT,
                                         fg_color=BTN_RELOAD_FG_COLOR[mode_idx], hover_color=BTN_RELOAD_HOVER_COLOR[mode_idx])
        self.copy_button.pack(side="left", padx=(0, 10))
        open_button = ctk.CTkButton(button_frame, text="Open Page", command=self.open_download_page, width=100, font=APP_FONT,
                                       fg_color=BTN_GRAPH_FG_COLOR[mode_idx], hover_color=BTN_GRAPH_HOVER_COLOR[mode_idx])
        open_button.pack(side="left", padx=(0, 10))
        close_button = ctk.CTkButton(button_frame, text="Close", command=self.destroy, width=80, font=APP_FONT,
                                      fg_color=COLOR_WARNING_GENERAL[mode_idx], hover_color=COLOR_DANGER_GENERAL[mode_idx])
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
            original_text = self.copy_button.cget("text")
            self.copy_button.configure(text="Copied!", state="disabled")
            self.after(1500, lambda: self.copy_button.configure(text=original_text, state="normal"))
        except Exception as e:
            messagebox.showerror("Clipboard Error", f"Could not copy link to clipboard:\n{e}", parent=self)

    def open_download_page(self):
        try:
            webbrowser.open(self._download_url)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Browser Error", f"Could not open the download page in your browser:\n{e}", parent=self)

def handle_unity_download_click():
    if not 'UNITY_REQUIRED_VERSION_STRING' in globals() or not UNITY_REQUIRED_VERSION_STRING:
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
             messagebox.showerror("Internal Error", "The required Unity version is not configured internally.", parent=main_window)
        return
    unity_version_hash = "b2e806cf271c"
    unity_hub_uri = f"unityhub://{UNITY_REQUIRED_VERSION_STRING}/{unity_version_hash}"
    build_support_module_text = "- Mac Build Support (Mono or IL2CPP - check project needs)"
    hub_download_link = "https://public-cdn.cloud.unity3d.com/hub/prod/UnityHubSetup.dmg"
    os_name = "macOS"
    instructions = (
        "To install the correct Unity Editor version using this tool:\n\n"
        "1. Install Unity Hub using the link below if you haven't already.\n"
        "   (Close the Hub after installation if it opens automatically).\n\n"
        "2. Close this message, then click the 'Download Unity Editor' button in this application again.\n"
        f"   This should prompt Unity Hub to open and start installing the required Editor version ({UNITY_REQUIRED_VERSION_STRING}).\n\n"
        "3. In the Unity Hub installation options, carefully review the modules to add. Ensure the following are selected:\n"
        "   - Microsoft Visual Studio Community (or your preferred IDE)\n"
        f"   {build_support_module_text}\n\n"
        "4. Complete the installation process within Unity Hub."
    )
    troubleshooting = (
        "\n" + ("-" * 45) + "\n\n"
        "If Unity Hub did NOT open or prompt for installation:\n"
        "- Ensure Unity Hub is installed and running.\n"
        f"- Try opening the link manually in your browser (might trigger Hub): {unity_hub_uri}\n"
        "- If issues persist, you may need to manually find and install the specific Editor version ({UNITY_REQUIRED_VERSION_STRING}) via the Unity Hub 'Installs' section and 'Add' button, then select 'Install from archive'."
    )
    full_message_text = instructions + troubleshooting
    try:
        webbrowser.open(unity_hub_uri)
    except Exception:
        pass
    if 'main_window' in globals() and main_window and main_window.winfo_exists():
        UnityHubInfoDialog(
            parent=main_window,
            title="Download Unity Editor / Hub Instructions",
            message_text=full_message_text,
            download_url=hub_download_link
        )

unity_down_btn = ctk.CTkButton(sidebar_frame, text="Download Unity Editor",
                              command=handle_unity_download_click,
                              font=APP_FONT,
                              fg_color=BTN_UNITY_DOWN_FG_COLOR[mode_idx], hover_color=BTN_UNITY_DOWN_HOVER_COLOR[mode_idx], text_color=BTN_UNITY_DOWN_TEXT_COLOR[mode_idx])
unity_down_btn.pack(fill="x", padx=15, pady=5)
about_btn = ctk.CTkButton(sidebar_frame, text="About",
                          command=lambda: messagebox.showinfo("About", "Colony Dynamics Simulator v1.0.\n\nAuthors:\nIván Cáceres S.\nTobías Guerrero Ch."),
                          font=APP_FONT,
                          fg_color=BTN_ABOUT_FG_COLOR[mode_idx], hover_color=BTN_ABOUT_HOVER_COLOR[mode_idx], text_color=BTN_ABOUT_TEXT_COLOR[mode_idx])
about_btn.pack(fill="x", padx=15, pady=5)
theme_switch = ctk.CTkSwitch(sidebar_frame, text=f"{initial_mode} Mode", command=toggle_appearance_mode, font=APP_FONT)
theme_switch.pack(fill="x", side='bottom', padx=15, pady=(10, 5))
if initial_mode == "Dark": theme_switch.select()
else: theme_switch.deselect()
exit_btn = ctk.CTkButton(sidebar_frame, text="Exit Application", command=on_closing, font=APP_FONT,
                         fg_color=BTN_EXIT_FG_COLOR[mode_idx], hover_color=BTN_EXIT_HOVER_COLOR[mode_idx], text_color=BTN_EXIT_TEXT_COLOR[mode_idx])
exit_btn.pack(fill="x", side='bottom', padx=15, pady=(5, 20))
main_content_frame = ctk.CTkFrame(main_window, corner_radius=5)
main_content_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
main_content_frame.columnconfigure(0, weight=1)
main_content_frame.rowconfigure(0, weight=0)
main_content_frame.rowconfigure(1, weight=0)
main_content_frame.rowconfigure(2, weight=1)
main_content_frame.rowconfigure(3, weight=0)
header_frame = ctk.CTkFrame(main_content_frame, fg_color="transparent")
header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
header_frame.columnconfigure(0, weight=1)
ctk.CTkLabel(header_frame, text="Colony Dynamics Simulator", font=TITLE_FONT, anchor="center").grid(row=0, column=0, pady=(0, 10))
search_frame = ctk.CTkFrame(main_content_frame, fg_color="transparent")
search_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 5))
search_frame.columnconfigure(1, weight=1)
ctk.CTkLabel(search_frame, text="Search:", font=APP_FONT).grid(row=0, column=0, padx=(5, 5), pady=5)
search_entry = ctk.CTkEntry(search_frame, placeholder_text="Type simulation name to filter...", font=APP_FONT)
search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
search_entry.bind("<KeyRelease>", filter_simulations)
clear_search_btn = ctk.CTkButton(search_frame, text="Clear", width=60, font=APP_FONT, command=clear_search,
                                fg_color=BTN_CLEARSEARCH_FG_COLOR[mode_idx], hover_color=BTN_CLEARSEARCH_HOVER_COLOR[mode_idx], text_color=BTN_CLEARSEARCH_TEXT_COLOR[mode_idx])
clear_search_btn.grid(row=0, column=2, padx=(5, 5), pady=5)
tree_frame = ctk.CTkFrame(main_content_frame, corner_radius=5)
tree_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
tree_frame.columnconfigure(0, weight=1)
tree_frame.rowconfigure(0, weight=1)
columns = ("col_name", "col_created", "col_last_used", "col_loaded", "col_load", "col_delete")
sim_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
sim_tree.heading("col_name", text="Simulation Name", anchor='w')
sim_tree.column("col_name", width=250, minwidth=150, anchor="w", stretch=tk.YES)
sim_tree.heading("col_created", text="Created", anchor='center')
sim_tree.column("col_created", width=120, minwidth=100, anchor="center", stretch=tk.NO)
sim_tree.heading("col_last_used", text="Last Used", anchor='center')
sim_tree.column("col_last_used", width=120, minwidth=100, anchor="center", stretch=tk.NO)
sim_tree.heading("col_loaded", text="Loaded", anchor='center')
sim_tree.column("col_loaded", width=70, minwidth=60, stretch=tk.NO, anchor="center")
sim_tree.heading("col_load", text="Load/Run", anchor='center')
sim_tree.column("col_load", width=90, minwidth=80, stretch=tk.NO, anchor="center")
sim_tree.heading("col_delete", text="Delete", anchor='center')
sim_tree.column("col_delete", width=80, minwidth=70, stretch=tk.NO, anchor="center")
last_sort_column = None
sort_order = {col: False for col in columns if col not in ["col_load", "col_delete", "col_loaded"]}

def sort_column(tree, col, reverse):
    if col in ["col_load", "col_delete", "col_loaded"]:
        return
    global last_sort_column, sort_order
    try:
        data = [(tree.set(item, col), item) for item in tree.get_children('')]
        def get_sort_key(value_str):
            if col in ("col_created", "col_last_used"):
                if value_str in ("???", "Never") or not value_str: return 0
                try:
                    return time.mktime(time.strptime(value_str, "%y-%m-%d %H:%M"))
                except ValueError: return 0
            else: return str(value_str).lower()
        data.sort(key=lambda t: get_sort_key(t[0]), reverse=reverse)
        for i, (_, item) in enumerate(data):
            tree.move(item, '', i)
        sort_order[col] = reverse
        last_sort_column = col
        for c in sort_order:
             current_heading = tree.heading(c)
             heading_text = current_heading['text'].replace(' ▲', '').replace(' ▼', '')
             if c == col:
                 heading_text += (' ▼' if reverse else ' ▲')
             tree.heading(c, text=heading_text, command=lambda c_ref=c: sort_column(tree, c_ref, not sort_order.get(c_ref, False)))
    except Exception:
        pass

for col_name in columns:
    if col_name not in ["col_load", "col_delete", "col_loaded"]:
        current_text = sim_tree.heading(col_name)['text']
        anchor_dir = 'w' if col_name=='col_name' else 'center'
        sim_tree.heading(col_name, text=current_text, command=lambda c=col_name: sort_column(sim_tree, c, False), anchor=anchor_dir)

sim_tree.grid(row=0, column=0, sticky="nsew")
scrollbar = ctk.CTkScrollbar(tree_frame, command=sim_tree.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
sim_tree.configure(yscrollcommand=scrollbar.set)
sim_tree.bind('<<TreeviewSelect>>', lambda e: update_button_states())
sim_tree.bind("<Button-1>", handle_tree_click)
sim_tree.bind("<Motion>", handle_tree_motion)
sim_tree.bind("<Leave>", handle_tree_leave)
button_frame_bottom = ctk.CTkFrame(main_content_frame, fg_color="transparent")
button_frame_bottom.grid(row=3, column=0, pady=(10, 10), padx=10, sticky="ew")
button_frame_bottom.columnconfigure(0, weight=1)
button_frame_bottom.columnconfigure(1, weight=0)
button_frame_bottom.columnconfigure(2, weight=0)
button_frame_bottom.columnconfigure(3, weight=0)
button_frame_bottom.columnconfigure(4, weight=1)
button_height=35
reload_btn = ctk.CTkButton(button_frame_bottom, text="Reload List", command=populate_simulations, font=APP_FONT, height=button_height,
                           fg_color=BTN_RELOAD_FG_COLOR[mode_idx], hover_color=BTN_RELOAD_HOVER_COLOR[mode_idx], text_color=BTN_RELOAD_TEXT_COLOR[mode_idx])
reload_btn.grid(row=0, column=1, padx=10, pady=5)
graph_btn = ctk.CTkButton(button_frame_bottom, text="Simulation Statistics", command=on_show_graphs_thread, font=APP_FONT, height=button_height,
                          fg_color=BTN_GRAPH_FG_COLOR[mode_idx], hover_color=BTN_GRAPH_HOVER_COLOR[mode_idx], text_color=BTN_GRAPH_TEXT_COLOR[mode_idx])
graph_btn.grid(row=0, column=2, padx=10, pady=5)
create_btn = ctk.CTkButton(button_frame_bottom, text="Create Sim (API)", command=on_create_simulation, font=APP_FONT, height=button_height,
                           fg_color=BTN_CREATE_FG_COLOR[mode_idx], hover_color=BTN_CREATE_HOVER_COLOR[mode_idx], text_color=BTN_CREATE_TEXT_COLOR[mode_idx])
create_btn.grid(row=0, column=3, padx=10, pady=5)
status_frame = ctk.CTkFrame(main_window, height=25, corner_radius=0)
status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
status_label = ctk.CTkLabel(status_frame, text="Initializing...", anchor="w", font=STATUS_FONT)
status_label.pack(side="left", fill="x", expand=True, padx=10, pady=3)

if __name__ == "__main__":
    main_window.after(10, update_treeview_style)
    update_button_states()
    update_status("Performing initial configuration verification...")
    initial_verify_thread = threading.Thread(target=perform_verification, args=(False, True), daemon=True)
    initial_verify_thread.start()
    main_window.protocol("WM_DELETE_WINDOW", on_closing)
    main_window.mainloop()
