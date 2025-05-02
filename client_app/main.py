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
import numpy as np
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score

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
UNITY_REQUIRED_VERSION_STRING = "6000.0.32f1"
SIMULATIONS_DIR = Path("./Simulations")
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
ICON_PATH_WIN = "img/icono.ico"
ICON_PATH_MAC = "img/icono.icns"
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
# --- Button Colors (Light, Dark) ---
COLOR_SUCCESS_GENERAL = ("#28a745", "#4CAF50")
COLOR_DANGER_GENERAL = ("#C62828", "#EF5350")
COLOR_INFO_GENERAL = ("#218838", "#66BB6A")
COLOR_WARNING_GENERAL = ("#E53935", "#E53935")
COLOR_DISABLED_GENERAL = ("#BDBDBD", "#757575")
COLOR_SIDEBAR_BG = None

def get_color_mode_index():
    """Returns 0 for Light mode, 1 for Dark mode."""
    return 1 if ctk.get_appearance_mode() == "Dark" else 0

# --- Individual Button Color Definitions (FG, HOVER, TEXT) ---
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


# --- Constants ---
UNITY_PRODUCT_NAME = "InitialSetup" # Name used by Unity for its persistent data folder
LOG_SUBFOLDER = "SimulationLoggerData" # Subfolder within persistent data for logs
CSV_FILENAME = "SimulationStats.csv" # Name of the log file
GRAPHICS_SUBFOLDER = "Graphics" # Subfolder for generated graphs

# --- Simulation Graphics Generation ---

def find_unity_persistent_path(product_name: str) -> Union[Path, None]:
    """
    Searches for the path to the product folder ('product_name')
    within standard Unity persistent data locations (Application.persistentDataPath).
    Returns the full path (.../CompanyName/ProductName) or None if not found or ambiguous.
    """
    system = platform.system()
    home = Path.home()
    search_base: Union[Path, None] = None
    potential_paths: list[Path] = []

    try:
        # 1. Determine the base directory to search (root of persistentDataPath)
        if system == "Windows":
            local_app_data_str = os.getenv('LOCALAPPDATA', '')
            if local_app_data_str:
                app_data_parent = Path(local_app_data_str).parent
                search_base = app_data_parent / 'LocalLow'
            else:
                search_base = home / 'AppData' / 'LocalLow' # Fallback
            # print(f"  [PathFinder] Search base (Win): {search_base}")
        elif system == "Darwin":  # macOS
            search_base = home / 'Library' / 'Application Support'
            # print(f"  [PathFinder] Search base (Mac): {search_base}")
        elif system == "Linux":
            search_base_unity = home / '.config' / 'unity3d'
            if search_base_unity.is_dir():
                 search_base = search_base_unity
            else:
                 # Alternative (less common for pure Unity): XDG_CONFIG_HOME
                 # config_home = Path(os.getenv('XDG_CONFIG_HOME', home / '.config'))
                 # search_base = config_home / product_name # Or /Company/Product...
                 print(f"  [PathFinder] Warning: Standard Unity base directory ('{search_base_unity}') not found.")
                 return None # Cannot search without a known base
            # print(f"  [PathFinder] Search base (Linux): {search_base}")
        else:
            print(f"  [PathFinder] Error: OS '{system}' not supported for automatic search.")
            return None

        if not search_base or not search_base.is_dir():
            print(f"  [PathFinder] Error: Base directory '{search_base}' does not exist or is not accessible.")
            return None

        # 2. Iterate over 'company' folders (name unknown)
        # print(f"  [PathFinder] Searching for '{product_name}' in subfolders of '{search_base}'...")
        for company_dir in search_base.iterdir():
            if company_dir.is_dir():
                _potential_product_path = company_dir / product_name
                if _potential_product_path.is_dir():
                    # print(f"    -> Match found: {_potential_product_path}")
                    potential_paths.append(_potential_product_path)

        # 3. Evaluate results
        if len(potential_paths) == 1:
            found_path = potential_paths[0]
            # print(f"  [PathFinder] Success: Unique path found: {found_path}")
            return found_path
        elif len(potential_paths) == 0:
            print(f"  [PathFinder] Error: Product folder '{product_name}' not found under '{search_base}'.")
            print(f"  Ensure the Unity application ('{product_name}') has run at least once and created its data folder.")
            return None
        else: # Ambiguity
            print(f"  [PathFinder] Error: Ambiguity! Multiple paths found for '{product_name}':")
            for p in potential_paths: print(f"    - {p}")
            print(f"  Clean up old or duplicate installations.")
            return None

    except PermissionError:
        print(f"  [PathFinder] Permission error attempting to search in '{search_base}'.")
        return None
    except Exception as e:
        print(f"  [PathFinder] Unexpected error during product path search: {e}")
        traceback.print_exc()
        return None

def find_simulation_data_path(simulation_name: str) -> Union[Path, None]:
    """
    Finds the full path to the data folder for a specific simulation,
    first locating the Unity product base folder.
    Returns Path(.../SimulationLoggerData/simulation_name) or None if not found.
    """
    if not simulation_name:
        print("[find_simulation_data_path] Error: Empty simulation name provided.")
        return None

    product_base_path = find_unity_persistent_path(UNITY_PRODUCT_NAME)

    if not product_base_path:
        print(f"[find_simulation_data_path] Could not find the base product folder '{UNITY_PRODUCT_NAME}' to locate data for '{simulation_name}'.")
        return None

    simulation_path = product_base_path / LOG_SUBFOLDER / simulation_name
    return simulation_path

def exponential_func(x, a, b):
    """Base exponential function: y = a * exp(b * x)"""
    # Use np.exp to handle numpy arrays correctly
    return a * np.exp(b * x)

def SimulationGraphics(simulation_name):
    """
    Generates graphs for a simulation, locating the CSV data dynamically
    by calling find_simulation_data_path.
    """
    if not simulation_name:
        print("Error: A simulation name must be provided to the SimulationGraphics function.")
        # Consider using messagebox if this is a GUI application
        # messagebox.showerror("Error", "No simulation name provided to SimulationGraphics.")
        return

    print(f"\n--- Starting Graph Generation for Simulation: '{simulation_name}' ---")

    # --- STEP 1: Locate the data folder using the helper function ---
    print("Step 1: Locating data folder...")
    simulation_folder = find_simulation_data_path(simulation_name)

    if not simulation_folder:
        print(f"Critical Error: Could not locate data folder for '{simulation_name}'. Aborting graph generation.")
        # Specific error was already printed by helper functions.
        # Consider messagebox for GUI
        # messagebox.showerror("Error", f"Could not locate data folder for simulation '{simulation_name}'.")
        return # Exit if folder not found

    print(f"  Data folder located: {simulation_folder}")

    # --- STEP 2: Construct full paths for CSV and Graphics ---
    csv_path = simulation_folder / CSV_FILENAME
    output_folder = simulation_folder / GRAPHICS_SUBFOLDER
    print(f"  Expected CSV path: {csv_path}")
    print(f"  Output folder for graphs: {output_folder}")

    # --- STEP 3: Create output folder for graphs ---
    try:
        print(f"Step 3: Ensuring graphics folder exists...")
        output_folder.mkdir(parents=True, exist_ok=True) # Creates if it doesn't exist
        print(f"  Folder '{output_folder}' ensured.")
    except OSError as e:
         print(f"  Critical Error creating/ensuring output folder '{output_folder}': {e}. Aborting.")
         # Consider messagebox
         # messagebox.showerror("Error", f"Could not create output folder:\n{output_folder}\nError: {e}")
         return

    # --- STEP 4: Verify and read the CSV file ---
    print(f"Step 4: Verifying and reading CSV file...")
    if not csv_path.is_file():
        print(f"  Error: CSV file not found at the expected path: {csv_path}")
        # Consider messagebox
        # messagebox.showerror("Error", f"CSV file not found:\n{csv_path}")
        return

    try:
        df = pd.read_csv(csv_path, sep=";", engine="python") # Assuming ';' separator from C# logger
        if df.empty:
             print(f"  Error: The CSV file '{csv_path}' is empty.")
             # Consider messagebox
             # messagebox.showerror("Error", f"The CSV file is empty:\n{csv_path}")
             return
        print(f"  CSV read successful ({len(df)} rows).")
    except pd.errors.EmptyDataError:
         print(f"  Error: The CSV file '{csv_path}' is empty or contains no data.")
         return
    except Exception as e:
        print(f"  Critical Error reading or parsing CSV file '{csv_path}': {e}")
        traceback.print_exc() # Print full error details for debugging
        # Consider messagebox
        # messagebox.showerror("CSV Read Error", f"Failed to read CSV file:\n{csv_path}\nError: {e}")
        return

    # --- STEP 5: Data Processing ---
    print(f"Step 5: Processing data...")
    try:
        df.columns = df.columns.str.strip() # Clean column names

        if "Timestamp" not in df.columns: # Check crucial Timestamp column
            print("  Error: Required column 'Timestamp' not found in the CSV.")
            return

        # Convert Timestamp to string, clean spaces, then to datetime
        df["Timestamp_str"] = df["Timestamp"].astype(str).str.strip()
        # Remove rows where the original timestamp was '0' or empty
        df = df[df["Timestamp_str"].str.lower().isin(['0', '']) == False].copy()

        # Attempt conversion to the expected format
        df["Timestamp"] = pd.to_datetime(df["Timestamp_str"], format="%d-%m-%Y %H:%M:%S", errors='coerce')

        # Remove rows where conversion failed (resulted in NaT)
        initial_rows = len(df)
        df.dropna(subset=["Timestamp"], inplace=True)
        rows_dropped = initial_rows - len(df)
        if rows_dropped > 0:
            print(f"  Warning: Removed {rows_dropped} rows with invalid Timestamp format.")

        if df.empty:
            print("  Error: No valid data remaining after processing Timestamps.")
            return

        # Sort by Timestamp (important for time-series graphs)
        df.sort_values(by="Timestamp", inplace=True)

        print("  Data processing completed.")

    except Exception as e:
        print(f"  Error during data processing: {e}")
        traceback.print_exc()
        return

    # --- STEP 6: Identify Organism Columns ---
    # Known columns that are NOT organisms
    known_columns = {"Timestamp", "Timestamp_str", "FPS", "RealTime", "SimulatedTime", "DeltaTime", "FrameCount", "Pausado"} # "Pausado" -> "Paused"? Check C# logger
    organism_columns = sorted([col for col in df.columns if col not in known_columns]) # Sort alphabetically
    print(f"  Identified organism columns: {organism_columns}")

    # --- STEP 7: Generate Graphs ---
    print(f"Step 7: Generating graphs...")
    plot_generated_count = 0 # Counter for successfully generated graphs

    # --- Graph 1: FPS over Time ---
    if "FPS" in df.columns:
        plt.figure(figsize=(12, 6))
        plt.plot(df["Timestamp"], df["FPS"], marker=".", linestyle="-", color="blue")
        plt.title(f"FPS over Time ({simulation_name})")
        plt.xlabel("Timestamp")
        plt.ylabel("FPS")
        plt.xticks(rotation=45, ha='right') # Better alignment for rotated labels
        plt.grid(True, linestyle='--', alpha=0.6) # Subtle grid style
        plt.tight_layout()
        try:
            plt.savefig(str(output_folder / "fps_over_time.png"))
            plot_generated_count += 1
        except Exception as e:
            print(f"Error saving fps_over_time.png: {e}")
        plt.close()
    else:
        print("Column 'FPS' not found, skipping FPS over Time graph.")


    # --- Graph 2: RealTime vs SimulatedTime ---
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
        except Exception as e:
            print(f"Error saving time_comparison.png: {e}")
        plt.close()
    else:
         print("Columns 'RealTime' or 'SimulatedTime' not found, skipping Time Comparison graph.")

    # --- Graph 3: Organism Counts over Time ---
    if organism_columns:
        plt.figure(figsize=(12, 6))
        plotted_any_organism = False
        for col in organism_columns:
            # Verify column exists and is numeric before plotting
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                plt.plot(df["Timestamp"], df[col], label=col, marker=".", linestyle="-")
                plotted_any_organism = True
            else:
                print(f"Warning: Skipping non-numeric or missing organism column: '{col}'")

        if plotted_any_organism: # Only add graph elements if something was plotted
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
            except Exception as e:
                print(f"Error saving organism_counts.png: {e}")
        plt.close() # Always close the figure
    else:
        print("No specific organism columns found, skipping Organism Counts graph.")

    # --- Graph 4: Total Organisms over Time ---
    if "Organism count" in df.columns: # Check for the specific "total" column name
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
        except Exception as e:
            print(f"Error saving total_organisms.png: {e}")
        plt.close()
    else:
        print("Column 'Organism count' not found, skipping Total Organisms graph.")

    # --- Graph 5: Frame Count over Time ---
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
        except Exception as e:
            print(f"Error saving frame_count.png: {e}")
        plt.close()
    else:
        print("Column 'FrameCount' not found, skipping Frame Count graph.")


    # --- Graph 6: FPS Distribution ---
    if "FPS" in df.columns and not df["FPS"].isnull().all(): # Check if FPS data exists
        plt.figure(figsize=(12, 6))
        plt.hist(df["FPS"].dropna(), bins=20, color="green", edgecolor="black") # dropna just in case
        plt.title(f"FPS Distribution ({simulation_name})")
        plt.xlabel("FPS")
        plt.ylabel("Frequency")
        plt.grid(True, axis='y', linestyle='--', alpha=0.6) # Grid only on y-axis for histograms
        plt.tight_layout()
        try:
            plt.savefig(str(output_folder / "fps_histogram.png"))
            plot_generated_count += 1
        except Exception as e:
             print(f"Error saving fps_histogram.png: {e}")
        plt.close()
    elif "FPS" in df.columns:
         print("Column 'FPS' found but contains no valid data, skipping FPS histogram.")

    # --- Graph 7: Average FPS per Total Organisms ---
    if "Organism count" in df.columns and "FPS" in df.columns and not df["Organism count"].isnull().all() and not df["FPS"].isnull().all():
        # Ensure 'Organism count' is numeric for correct grouping
        if pd.api.types.is_numeric_dtype(df["Organism count"]):
            # Convert to int if possible for cleaner categories
            df_groupable = df.dropna(subset=["Organism count", "FPS"])
            try:
                 df_groupable["Organism count"] = df_groupable["Organism count"].astype(int)
            except ValueError:
                 print("Warning: 'Organism count' contains non-integer values, grouping by float values.")

            # Group and calculate mean
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
                except Exception as e:
                    print(f"Error saving total_organisms_vs_fps.png: {e}")
                plt.close()
            else:
                print("Could not group data for Average FPS per Total Organisms graph.")
        else:
            print("Column 'Organism count' is not numeric, skipping Average FPS per Total Organisms graph.")

    # --- Graph 8: Organisms per Simulated Time with Exponential Fit ---
    if "SimulatedTime" in df.columns and organism_columns:
        # Verify SimulatedTime is numeric and not empty
        if pd.api.types.is_numeric_dtype(df["SimulatedTime"]) and not df["SimulatedTime"].isnull().all():
            plt.figure(figsize=(14, 7)) # Slightly wider for potentially long legend
            plotted_something = False
            actual_organisms_plotted = [] # To control legend and title

            # Prepare time data once if valid
            time_data_full = df["SimulatedTime"]

            for col in organism_columns:
                # Skip the 'Organism count' column specifically for this graph
                if col == "Organism count":
                    print(f"  Skipping column '{col}' from Graph 8 as requested.")
                    continue

                # Verify each organism column again and that it's not empty
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]) and not df[col].isnull().all():

                    # 1. Plot original data
                    # Filter NaNs for initial plot too, ensuring consistency
                    valid_indices = df[col].notna() & time_data_full.notna()
                    time_data_clean = time_data_full[valid_indices].values
                    organism_data_clean = df.loc[valid_indices, col].values

                    # Only plot if valid data exists after cleaning NaNs
                    if len(time_data_clean) > 0:
                        plt.plot(time_data_clean, organism_data_clean, label=f"{col}", marker=".", linestyle="-", alpha=0.7)
                        plotted_something = True
                        if col not in actual_organisms_plotted:
                            actual_organisms_plotted.append(col) # Add to list of plotted organisms
                    else:
                        print(f"  Warning: No valid numeric data for '{col}' on Y-axis or corresponding 'SimulatedTime'.")
                        continue # Skip to next organism if no valid data

                    # 2. Attempt exponential fit
                    # Need at least 2 points to attempt a fit
                    if len(time_data_clean) >= 2:
                        try:
                            # Initial guess: a = first value > 0, b = small positive value
                            initial_a = organism_data_clean[0] if organism_data_clean[0] > 0 else 1.0
                            if np.all(organism_data_clean == organism_data_clean[0]):
                                initial_b = 0.0 # If constant, b is 0
                            elif len(time_data_clean) > 1 and organism_data_clean[-1] > initial_a and time_data_clean[-1] > time_data_clean[0]:
                                # Avoid division by zero if times are identical
                                time_diff = time_data_clean[-1] - time_data_clean[0]
                                if time_diff > 1e-9: # Small threshold to avoid division by zero
                                    initial_b = np.log(organism_data_clean[-1] / initial_a) / time_diff
                                else:
                                    initial_b = 0.0 # If times are nearly identical, b is 0
                            else:
                                initial_b = 0.01 # Default guess

                            # Ensure b is not NaN or Inf
                            if not np.isfinite(initial_b):
                                initial_b = 0.01

                            p0 = [initial_a, initial_b]
                            bounds = ([0, -np.inf], [np.inf, np.inf]) # a >= 0

                            # Perform curve fitting
                            params, covariance = curve_fit(
                                exponential_func,
                                time_data_clean,
                                organism_data_clean,
                                p0=p0,
                                bounds=bounds,
                                maxfev=10000 # Increase iterations if needed
                            )
                            a_fit, b_fit = params

                            # Calculate R-squared for the fit
                            organism_predicted = exponential_func(time_data_clean, a_fit, b_fit)
                            r_squared = r2_score(organism_data_clean, organism_predicted)

                            # Generate points for the fitted curve over the clean time range
                            time_fit = np.linspace(time_data_clean.min(), time_data_clean.max(), 100)
                            organism_fit = exponential_func(time_fit, a_fit, b_fit)

                            # 3. Plot the fitted curve
                            label_fit = f"{col} (Exp: a={a_fit:.2f}, b={b_fit:.3f}, R²={r_squared:.2f})" # Added R²
                            plt.plot(time_fit, organism_fit, label=label_fit, linestyle="--")

                        except RuntimeError:
                            print(f"  Warning: Could not fit exponential curve for '{col}'. Optimization did not converge.")
                        except ValueError as ve:
                            print(f"  Warning: Value error during fitting for '{col}'. Incompatible data? {ve}")
                        except Exception as e:
                            print(f"  Warning: Unexpected error during curve fitting for '{col}': {e}")
                    else:
                        print(f"  Warning: Not enough data points ({len(time_data_clean)}) to fit curve for '{col}'.")


            if plotted_something:
                plt.title(f"Specific Organism Count & Exponential Fit over Simulated Time ({simulation_name})") # Adjusted title
                plt.xlabel("Simulated Time (s)")
                plt.ylabel("Organism Count")
                # Place legend outside if many lines
                if len(actual_organisms_plotted) > 2: # If > 2 organisms (4 lines total with fits)
                    plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")
                    plt.tight_layout(rect=[0, 0, 0.85, 1]) # Adjust layout for external legend
                else:
                    plt.legend()
                    plt.tight_layout() # Normal adjustment if legend fits inside

                plt.grid(True, linestyle='--', alpha=0.6)

                try:
                    # Keep the filename, but it now only contains specific organisms
                    save_path = output_folder / "organisms_vs_simulated_time_fit.png"
                    plt.savefig(str(save_path))
                    plot_generated_count += 1
                    print(f"  Graph 'organisms_vs_simulated_time_fit.png' saved (excluding 'Organism count').")
                except Exception as e:
                    print(f"  Error saving organisms_vs_simulated_time_fit.png: {e}")
            else:
                print("  Nothing plotted for Organisms vs Simulated Time (no valid data or only 'Organism count' found).")

            plt.close() # Close figure to free memory
        elif "SimulatedTime" in df.columns and df["SimulatedTime"].isnull().all():
            print("Column 'SimulatedTime' exists but all values are null, skipping Organisms vs Simulated Time graph.")
        else: # If the column is NOT numeric
            print("Column 'SimulatedTime' is not numeric, skipping Organisms vs Simulated Time graph.")
    elif not organism_columns:
        print("No specific organism columns found, skipping Organisms vs Simulated Time graph.")
    else: # If 'SimulatedTime' is not in the columns
        print("Column 'SimulatedTime' not found, skipping Organisms vs Simulated Time graph.")

    # --- Final Message ---
    print(f"\n--- Graph generation process completed for '{simulation_name}' ---")
    if plot_generated_count > 0:
        print(f"{plot_generated_count} graphs were generated in: {output_folder}")
    else:
        print("No useful graphs were generated due to missing data or issues.")
    # Optional: Automatically open the folder after generation
    # open_graphs_folder(simulation_name)


# --- API Manager & Code Generation ---

# Load environment variables from .env file
load_dotenv(dotenv_path="./.env")
API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")
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


# --- API Response Caching ---
DELIMITER = "%|%" # Delimiter for the simple CSV cache

try:
    # Create an application-specific folder within Documents
    # Use Pathlib for robust path handling
    APP_DATA_DIR = Path.home() / "Documents" / "UnitySimulationManagerData"
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True) # Ensure it exists
    RESPONSES_DIR = APP_DATA_DIR / "Responses"
    RESPONSES_CSV = RESPONSES_DIR / "Responses.csv" # Full Path object
    print(f"INFO: Using data path: {RESPONSES_CSV}") # Good for debugging
except Exception as e:
    print(f"CRITICAL ERROR: Could not determine or create user data path in Documents: {e}")
    # Fallback: Try to write alongside the script/executable (less ideal)
    try:
        # Get script directory safely
        if getattr(sys, 'frozen', False): # Check if running as compiled executable
            script_dir = Path(sys.executable).parent
        else: # Running as script
            script_dir = Path(__file__).parent
        RESPONSES_DIR = script_dir / "Responses"
        RESPONSES_CSV = RESPONSES_DIR / "Responses.csv"
        RESPONSES_DIR.mkdir(parents=True, exist_ok=True) # Try creating here too
        print(f"WARNING: Falling back to script/exe directory path: {RESPONSES_CSV}")
    except Exception as fallback_e:
        print(f"CRITICAL ERROR: Fallback path also failed: {fallback_e}")
        # In a GUI app, show a critical error message and potentially exit
        messagebox.showerror("Fatal Error", "Cannot establish a data storage location (Documents or executable path). Caching and history will be disabled.")
        RESPONSES_CSV = None # Indicate failure

def check_last_char_is_newline(filepath: Union[str, Path]) -> bool:
    """Checks if the last character of a file is a newline."""
    if not RESPONSES_CSV: return True # If path couldn't be set, assume ok

    filepath = Path(filepath) # Ensure it's a Path object
    if not filepath.exists() or filepath.stat().st_size == 0:
        return True # Empty or non-existent file is fine
    try:
        with open(filepath, 'rb') as f: # Read in binary mode
            f.seek(-1, os.SEEK_END) # Go to the last byte
            last_byte = f.read(1)
            return last_byte == b'\n'
    except Exception as e:
        print(f"Warning checking last character of {filepath}: {e}")
        return False # Assume not newline on error

def get_next_id(csv_path: Union[str, Path]) -> int:
    """Gets the next sequential ID for the cache CSV."""
    if not RESPONSES_CSV: return 1 # If path couldn't be set, start at 1

    csv_path = Path(csv_path) # Ensure Path object
    try:
        # Ensure the parent directory exists BEFORE trying to read/write
        csv_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory for {csv_path}: {e}")
        raise # Re-raise if directory creation fails

    if not csv_path.exists():
        return 1 # Start from 1 if file doesn't exist

    last_id = 0
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) <= 1: # Only header or empty
            return 1
        # Read from the end to find the last valid ID quickly
        for line in reversed(lines):
            line = line.strip()
            if line: # Skip empty lines
                try:
                    parts = line.split(DELIMITER)
                    if parts and parts[0].strip().isdigit():
                        last_id = int(parts[0].strip())
                        return last_id + 1 # Next ID
                except (IndexError, ValueError):
                    # Ignore lines that don't have a valid numeric ID at the start
                    print(f"Warning: Skipping malformed line in CSV cache: {line[:50]}...")
                    continue
        # If no valid ID found in any line (e.g., only header exists)
        return 1
    except FileNotFoundError:
         return 1 # Should be handled by the initial check, but safe fallback
    except Exception as e:
         print(f"Error reading CSV {csv_path} to get ID: {e}. Starting from ID 1.")
         return 1

def write_response_to_csv(prompt: str, response: str, input_tokens: int, output_tokens: int) -> None:
    """Writes the API prompt and response to the cache CSV."""
    if not RESPONSES_CSV:
         print("Error: Cannot write response to CSV, data path not configured.")
         return

    try:
        # Directory existence is ensured by get_next_id or initial setup

        # Determine file state
        file_exists = RESPONSES_CSV.exists()
        is_empty = file_exists and RESPONSES_CSV.stat().st_size == 0
        write_header = not file_exists or is_empty

        # Get next ID (also creates directory if needed)
        next_id = get_next_id(RESPONSES_CSV)

        # Check if the last line needs a preceding newline
        needs_leading_newline = file_exists and not is_empty and not check_last_char_is_newline(RESPONSES_CSV)

        # Open and write
        with open(RESPONSES_CSV, "a", encoding="utf-8", newline='') as f: # Use newline='' for csv module compatibility (though not used here)
            if needs_leading_newline:
                f.write('\n') # Add newline if missing from previous write
            if write_header:
                header = f"id{DELIMITER}prompt{DELIMITER}response{DELIMITER}input_tokens{DELIMITER}output_tokens\n"
                f.write(header)

            # Clean prompt and response for CSV storage (replace delimiter and newlines)
            clean_prompt = str(prompt).replace(DELIMITER, "<DELIM>").replace('\n', '\\n').replace('\r', '')
            clean_response = str(response).replace(DELIMITER, "<DELIM>").replace('\n', '\\n').replace('\r', '')
            line = f"{next_id}{DELIMITER}{clean_prompt}{DELIMITER}{clean_response}{DELIMITER}{input_tokens}{DELIMITER}{output_tokens}\n"
            f.write(line)

        print(f"Response saved to: {RESPONSES_CSV} (id: {next_id})")

    except IOError as e:
        print(f"Critical I/O Error writing to {RESPONSES_CSV}: {e}")
        print("Check permissions in the target folder or if the file is locked.")
        # Consider showing a messagebox in the GUI
        messagebox.showerror("Cache Write Error", f"Could not write to the response cache file:\n{RESPONSES_CSV}\n\nError: {e}\n\nCaching may be disabled.")
    except Exception as e:
        print(f"Unexpected error writing to CSV cache: {e}")
        traceback.print_exc()

def get_cached_response(prompt: str) -> Union[str, None]:
    """Retrieves a cached response for a given prompt from the CSV."""
    if not RESPONSES_CSV or not RESPONSES_CSV.exists():
        return None # No cache file to read

    try:
        with open(RESPONSES_CSV, "r", encoding="utf-8") as f:
             lines = f.readlines()

        # Prepare the search prompt (cleaned same way as when writing)
        clean_prompt_search = str(prompt).replace(DELIMITER, "<DELIM>").replace('\n', '\\n').replace('\r', '')

        # Iterate through lines (skip header)
        for line in lines[1:]:
            line = line.strip()
            if not line: continue # Skip empty lines

            parts = line.split(DELIMITER)
            if len(parts) == 5: # Expecting id, prompt, response, in_tokens, out_tokens
                cached_prompt = parts[1]
                cached_response_raw = parts[2]
                # Compare cleaned prompts
                if cached_prompt == clean_prompt_search:
                    # Restore original response format (newlines, delimiter)
                    original_response = cached_response_raw.replace('\\n', '\n').replace("<DELIM>", DELIMITER)
                    print(f"Cache hit found for prompt (ID: {parts[0]})")
                    return original_response
            else:
                # Log incorrectly formatted lines
                print(f"Warning: Ignoring CSV cache line with incorrect format (parts={len(parts)}): {line[:100]}...")

    except FileNotFoundError:
         return None # File might have been deleted between check and open
    except Exception as e:
         print(f"Error reading cache from {RESPONSES_CSV}: {e}")
         return None # Return None on any read error

    return None # Return None if no match found

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

# --- GUI Utilities & Interaction Control ---

def center_window(window, width, height):
    """Centers a Tkinter window on the screen."""
    window.update_idletasks() # Ensure dimensions are calculated
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def apply_icon(window):
    """Applies the appropriate icon (.ico for Win, .icns for Mac) to the window."""
    try:
        icon_path = None
        if platform.system() == "Windows" and ICON_PATH_WIN and os.path.exists(ICON_PATH_WIN):
            icon_path = ICON_PATH_WIN
            window.iconbitmap(icon_path)
        elif platform.system() == "Darwin" and ICON_PATH_MAC and os.path.exists(ICON_PATH_MAC):
            # Setting icon on macOS requires different handling, often via app bundle or specific libraries.
            # Tkinter's iconbitmap doesn't directly support .icns.
            # For simplicity, we'll skip the macOS icon setting here via basic Tkinter.
            # A library like `pystray` or packaging tools (py2app) handle this better.
            print(f"Info: macOS icon setting skipped for {ICON_PATH_MAC} (requires app bundling).")
            pass # Placeholder for potential future macOS icon implementation
        # else: No specific icon handling for other OS like Linux via basic Tkinter

    except tk.TclError as e:
        if icon_path: # Only show error if we tried to apply one
            print(f"Warning: Icon '{icon_path}' could not be applied. Error: {e}")
    except Exception as e:
        print(f"Unexpected error applying icon: {e}")

class CustomInputDialog(ctk.CTkToplevel):
    """A custom modal dialog for text input using CustomTkinter."""
    def __init__(self, parent, title, prompt, width=400, height=170):
        super().__init__(parent)
        self.title(title)
        apply_icon(self) # Apply icon to the dialog
        center_window(self, width, height)
        self.resizable(False, False)
        self.transient(parent) # Stay on top of parent
        self.grab_set() # Make modal

        self.result = None # To store the user input

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) # Prompt label
        self.grid_rowconfigure(1, weight=1) # Entry expands slightly if needed
        self.grid_rowconfigure(2, weight=0) # Button frame

        # Prompt Label
        ctk.CTkLabel(self, text=prompt, font=APP_FONT, wraplength=width-40).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Entry Widget
        self.entry = ctk.CTkEntry(self, font=APP_FONT, width=width-40)
        self.entry.grid(row=1, column=0, padx=20, pady=5, sticky="ew")

        # Button Frame
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="e")

        mode_idx = get_color_mode_index()

        # OK Button
        ok_button = ctk.CTkButton(button_frame, text="OK", command=self.ok_action, width=80, font=APP_FONT,
                                  fg_color=COLOR_SUCCESS_GENERAL[mode_idx], hover_color=COLOR_INFO_GENERAL[mode_idx])
        ok_button.pack(side="left", padx=(0, 10))

        # Cancel Button
        cancel_button = ctk.CTkButton(button_frame, text="Cancel", command=self.cancel_action, width=80, font=APP_FONT,
                                      fg_color=COLOR_WARNING_GENERAL[mode_idx], hover_color=COLOR_DANGER_GENERAL[mode_idx])
        cancel_button.pack(side="left")

        # Bindings
        self.bind("<Return>", lambda event: self.ok_action())
        self.bind("<Escape>", lambda event: self.cancel_action())

        self.entry.focus() # Set focus to the entry field
        self.wait_window() # Wait until the window is destroyed

    def ok_action(self):
        self.result = self.entry.get()
        self.destroy()

    def cancel_action(self):
        self.result = None # Explicitly set to None on cancel
        self.destroy()

def custom_askstring(title, prompt):
    """Displays the custom input dialog and returns the result."""
    if 'main_window' in globals() and main_window and main_window.winfo_exists():
        dialog = CustomInputDialog(main_window, title, prompt)
        return dialog.result
    else:
        # Fallback if the main window isn't available (e.g., during early init or error)
        print(f"Warning: Main window not available for dialog '{title}'. Cannot show dialog.")
        # Optionally, use standard input as a command-line fallback:
        # return input(f"{prompt} ")
        return None


def show_tooltip(widget, text):
    """Displays a tooltip window near the widget."""
    global tooltip_window
    hide_tooltip() # Hide any existing tooltip first

    try:
        # Get mouse pointer coordinates (relative to screen)
        x, y = widget.winfo_pointerxy()
        x += 20 # Offset slightly from cursor
        y += 10
    except tk.TclError:
        # Error getting pointer coords (e.g., window closed)
        return

    # Alternative positioning relative to widget (less reliable with complex layouts)
    # try:
    #     x, y, h = widget.winfo_rootx(), widget.winfo_rooty(), widget.winfo_height()
    #     y += h + 5 # Position below the widget
    # except tk.TclError:
    #     pass # Use pointer coords if widget coords fail

    tooltip_window = tk.Toplevel(widget)
    tooltip_window.wm_overrideredirect(True) # No window decorations (border, title bar)
    tooltip_window.wm_geometry(f"+{x}+{y}") # Position the window

    label = tk.Label(tooltip_window, text=text, justify='left',
                     background="#ffffe0", # Pale yellow background
                     relief='solid', borderwidth=1,
                     font=("Segoe UI", 9)) # Tooltip font
    label.pack(ipadx=1)

def hide_tooltip():
    """Destroys the currently displayed tooltip window."""
    global tooltip_window
    if tooltip_window:
        try:
            tooltip_window.destroy()
        except tk.TclError:
            pass # Window might already be destroyed
        tooltip_window = None

def schedule_tooltip(widget, text):
    """Schedules a tooltip to appear after a delay."""
    global tooltip_job_id
    cancel_tooltip(widget) # Cancel any pending tooltip for this widget
    tooltip_job_id = widget.after(tooltip_delay, lambda: show_tooltip(widget, text))

def cancel_tooltip(widget):
    """Cancels any scheduled tooltip and hides the current one."""
    global tooltip_job_id
    if tooltip_job_id:
        widget.after_cancel(tooltip_job_id)
        tooltip_job_id = None
    hide_tooltip()

def on_closing():
    """Handles the application close request."""
    global is_build_running
    if is_build_running:
        messagebox.showwarning("Operation in Progress", "A build or load operation is currently running. Please wait for it to finish before closing.")
        return

    if messagebox.askokcancel(
        title="Exit Confirmation",
        message="Are you sure you want to exit the Unity Simulation Manager?",
        icon='question' # Standard question icon
        ):
        if callable(globals().get('update_status')): update_status("Closing application...")
        print("Attempting to close associated Unity instances (if any)...")
        # Run Unity closing in a separate thread to avoid blocking the GUI shutdown
        close_unity_thread = threading.Thread(target=ensure_unity_closed, daemon=True)
        close_unity_thread.start()

        print("Closing GUI...")
        # Give a moment for the status update and thread to start, then destroy
        if 'main_window' in globals() and main_window:
            main_window.after(200, main_window.destroy)
        else:
            sys.exit() # Force exit if main_window is gone

def disable_all_interactions():
    """Disables buttons and treeview interactions during long operations."""
    global is_build_running
    is_build_running = True
    mode_idx = get_color_mode_index()
    disabled_color = COLOR_DISABLED_GENERAL[mode_idx]

    try:
        # Disable main action buttons
        if 'reload_btn' in globals(): reload_btn.configure(state="disabled", fg_color=disabled_color)
        if 'graph_btn' in globals(): graph_btn.configure(state="disabled", fg_color=disabled_color)
        if 'create_btn' in globals(): create_btn.configure(state="disabled", fg_color=disabled_color)

        # Disable sidebar controls
        if 'sidebar_frame' in globals() and sidebar_frame.winfo_exists():
            for widget in sidebar_frame.winfo_children():
                if isinstance(widget, (ctk.CTkButton, ctk.CTkSwitch)):
                    # Store original color? Maybe not needed if we re-apply theme colors on enable.
                    widget.configure(state="disabled")
                    if isinstance(widget, ctk.CTkButton): widget.configure(fg_color=disabled_color)


        # Disable search controls
        if 'search_entry' in globals(): search_entry.configure(state="disabled")
        if 'clear_search_btn' in globals(): clear_search_btn.configure(state="disabled", fg_color=disabled_color)

        # Disable treeview interactions
        if 'sim_tree' in globals():
            sim_tree.unbind("<Button-1>")
            sim_tree.unbind("<Motion>")
            sim_tree.unbind("<Leave>") # Also unbind leave to prevent tooltip issues
            sim_tree.configure(cursor="watch") # Show busy cursor

        if callable(globals().get('update_status')): update_status("Operation in progress... Please wait.")
    except (NameError, tk.TclError) as e:
        print(f"Warning: Could not disable all interactions: {e}")

def enable_all_interactions():
    """Re-enables buttons and treeview interactions."""
    global is_build_running
    is_build_running = False

    try:
        # Re-enable sidebar controls (color updated by update_button_states)
        if 'sidebar_frame' in globals() and sidebar_frame.winfo_exists():
            for widget in sidebar_frame.winfo_children():
                if isinstance(widget, (ctk.CTkButton, ctk.CTkSwitch)):
                    widget.configure(state="normal")

        # Re-enable search controls (color updated by update_button_states)
        if 'search_entry' in globals(): search_entry.configure(state="normal")
        if 'clear_search_btn' in globals(): clear_search_btn.configure(state="normal")

        # Re-bind treeview events
        if 'sim_tree' in globals():
            sim_tree.bind("<Button-1>", handle_tree_click)
            sim_tree.bind("<Motion>", handle_tree_motion)
            sim_tree.bind("<Leave>", handle_tree_leave)
            sim_tree.configure(cursor="") # Restore default cursor

        # Update button states and colors based on current conditions
        if callable(globals().get('update_button_states')):
             # Schedule update slightly later to ensure UI has settled
             if 'main_window' in globals() and main_window:
                  main_window.after(10, update_button_states)
             else:
                  update_button_states() # Call directly if no window

        # Optionally clear the status bar or set a default message
        # if callable(globals().get('update_status')): update_status("Ready.")

    except (NameError, tk.TclError) as e:
        print(f"Warning: Could not re-enable all interactions: {e}")


# --- Core Utilities & Error Handling ---

def update_status(message):
    """Updates the status bar label safely."""
    try:
        if 'main_window' in globals() and main_window and main_window.winfo_exists() and 'status_label' in globals():
            # Use after(0, ...) to ensure update happens in the main GUI thread
            main_window.after(0, lambda msg=str(message): status_label.configure(text=msg))
        else:
            # Fallback if GUI is not ready or elements are missing
            print(f"Status Update (GUI not ready): {message}")
    except Exception as e:
         print(f"Error updating status bar: {e}")

def handle_unity_execution_error(error, operation_name="operation"):
    """Displays a formatted error message for Unity process failures."""
    error_type = type(error).__name__
    error_details = str(error)

    # Customize message based on error type
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
    print(f"--- Unity Execution Error ({operation_name}) ---")
    print(f"Error: {error}")
    print(traceback.format_exc()) # Print traceback to console for debugging
    print("--- End Unity Execution Error ---")

    # Show message box in the main thread
    try:
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
            main_window.after(0, lambda title=f"Unity {operation_name.capitalize()} Error", msg=error_message: messagebox.showerror(title, msg))
        else:
            print("Critical Error (No GUI): " + error_message)
    except Exception as mb_error:
        print(f"Error showing messagebox for Unity error: {mb_error}")

def ensure_unity_closed():
    """Attempts to find and terminate running Unity Editor processes matching the configured path."""
    if not unity_path_ok or not UNITY_EXECUTABLE:
        # print("Skipping Unity close check: Path not configured or invalid.")
        return

    unity_processes = []
    try:
        # Normalize the executable path for reliable comparison
        normalized_unity_exe = Path(UNITY_EXECUTABLE).resolve()
        # print(f"Looking for Unity processes matching: {normalized_unity_exe}")

        for proc in psutil.process_iter(['exe', 'pid', 'name']):
            try:
                proc_info = proc.info
                if proc_info['exe']:
                    proc_exe_path = Path(proc_info['exe']).resolve()
                    # Compare resolved paths
                    if proc_exe_path == normalized_unity_exe:
                        unity_processes.append(proc)
                        # print(f"  Found matching process: PID {proc_info['pid']}, Name {proc_info['name']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, FileNotFoundError):
                continue # Process ended, permission issue, or path invalid - skip
            except Exception as inner_ex:
                 print(f"  Error inspecting process PID {proc.pid}: {inner_ex}")
                 continue

    except Exception as ex:
        print(f"Error listing processes: {ex}")
        return

    if unity_processes:
        time_start = time.time()
        print(f"Attempting to terminate {len(unity_processes)} Unity instance(s)...")
        for proc in unity_processes:
            try:
                print(f"  Terminating PID {proc.pid}...")
                proc.terminate()
            except psutil.NoSuchProcess:
                 print(f"    PID {proc.pid} already terminated.")
            except psutil.Error as term_err:
                print(f"    Error terminating PID {proc.pid}: {term_err}")

        # Wait briefly and check which processes are still alive
        gone, alive = psutil.wait_procs(unity_processes, timeout=5) # Wait up to 5 seconds

        if alive:
            print(f"  {len(alive)} instance(s) did not terminate gracefully. Attempting to kill...")
            for proc in alive:
                try:
                    print(f"    Killing PID {proc.pid}...")
                    proc.kill()
                except psutil.NoSuchProcess:
                    print(f"      PID {proc.pid} already gone.")
                except psutil.Error as kill_err:
                    print(f"      Error killing PID {proc.pid}: {kill_err}")

            # Final check after kill attempt
            _, alive_after_kill = psutil.wait_procs(alive, timeout=3)
            if alive_after_kill:
                print(f"Warning: {len(alive_after_kill)} Unity instance(s) could not be closed forcefully.")
            else:
                 print("  All targeted instances terminated.")
        else:
             print("  All targeted instances terminated gracefully.")

        print(f"Unity closing attempt took {time.time() - time_start:.2f}s")
    # else:
        # print("No running Unity instances found matching the configured path.")


def open_graphs_folder(simulation_name):
    """
    Opens the 'Graphics' folder within the simulation's data directory,
    locating it dynamically using find_simulation_data_path.
    Shows errors via messagebox.
    """
    if not simulation_name:
        messagebox.showerror("Error", "No simulation name provided to open the graphics folder.")
        return

    print(f"Attempting to open graphics folder for: '{simulation_name}'")
    # Call the helper function to find the base data path
    simulation_data_dir = find_simulation_data_path(simulation_name)

    if not simulation_data_dir:
        # find_simulation_data_path should have already printed a more detailed error
        messagebox.showerror("Error", f"Could not find the data directory for simulation '{simulation_name}'.\nCannot open the graphics folder.")
        return

    # Construct the path to the specific graphics folder
    graphs_folder_path = simulation_data_dir / GRAPHICS_SUBFOLDER

    try:
        # Ensure the folder exists before trying to open it
        print(f"  Ensuring existence of: {graphs_folder_path}")
        graphs_folder_path.mkdir(parents=True, exist_ok=True) # Create if not exists

        print(f"  Opening folder: {graphs_folder_path}")
        # Open the folder using the appropriate method for the OS
        if platform.system() == "Windows":
            os.startfile(str(graphs_folder_path)) # Use str() for compatibility
        elif platform.system() == "Darwin": # macOS
            subprocess.Popen(["open", str(graphs_folder_path)])
        else: # Linux and others (assume xdg-open)
            subprocess.Popen(["xdg-open", str(graphs_folder_path)])

    except FileNotFoundError:
         # Error if the command 'open' or 'xdg-open' is not found
         cmd = 'open' if platform.system() == 'Darwin' else 'xdg-open'
         messagebox.showerror("System Error", f"Could not find the system command ('{cmd}') to open the folder on this OS ({platform.system()}).")
    except Exception as e:
         # Other errors (permissions, etc.)
         messagebox.showerror("Error", f"Could not open the graphics folder:\n{graphs_folder_path}\n\nError: {e}")
         print(f"Error opening graphics folder: {e}")
         traceback.print_exc() # Log detailed error


def get_folder_size(path: Union[str, Path]) -> int:
    """Recursively calculates the total size of files within a folder."""
    total = 0
    try:
        # Use Path object for consistency
        p = Path(path)
        if not p.is_dir(): return 0 # Return 0 if path isn't a directory

        for entry in p.iterdir(): # Use iterdir for potentially better performance
            try:
                if entry.is_file(follow_symlinks=False):
                    total += entry.stat(follow_symlinks=False).st_size
                elif entry.is_dir(follow_symlinks=False):
                    total += get_folder_size(entry) # Recursive call
            except (FileNotFoundError, PermissionError):
                # Skip files/dirs that vanish or we can't access
                continue
            except Exception as scan_err:
                 print(f"Warning: Error processing entry {entry}: {scan_err}")
                 continue # Skip problematic entry
    except (FileNotFoundError, PermissionError):
        # Error accessing the root path itself
        pass
    except Exception as e:
        print(f"Warning: Error getting folder size for {path}: {e}")
        pass # Return 0 or current total on other errors
    return total

def copy_directory(src: Union[str, Path], dst: Union[str, Path]) -> bool:
    """Copies a directory, removing the destination first if it exists."""
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.is_dir():
        msg = f"Source for copy is not a valid directory: {src_path}"
        print(f"Error: {msg}")
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
            main_window.after(0, lambda: messagebox.showerror("Copy Error", msg))
        return False

    try:
        if dst_path.exists():
            print(f"  Destination '{dst_path}' exists, removing first...")
            # Robust removal
            try:
                if dst_path.is_dir():
                    shutil.rmtree(dst_path, ignore_errors=False) # Try without ignore_errors first
                else:
                    dst_path.unlink() # Remove if it's a file
            except Exception as rm_e:
                 print(f"  Force removal required for '{dst_path}': {rm_e}")
                 # Try again ignoring errors (might be needed for locked files etc.)
                 if dst_path.is_dir(): shutil.rmtree(dst_path, ignore_errors=True)
                 elif dst_path.is_file(): dst_path.unlink(missing_ok=True)

            time.sleep(0.1) # Brief pause for filesystem

        # Perform the copy
        shutil.copytree(src_path, dst_path, symlinks=False, ignore_dangling_symlinks=True)
        print(f"  Successfully copied '{src_path}' to '{dst_path}'")
        return True
    except Exception as e:
        msg = f"Error copying directory:\nFrom: {src_path}\nTo:   {dst_path}\n\nError: {e}"
        print(f"Error: {msg}")
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
            main_window.after(0, lambda: messagebox.showerror("Copy Error", msg))
        # Attempt cleanup of partially copied destination
        if dst_path.exists() and dst_path.is_dir():
             try: shutil.rmtree(dst_path, ignore_errors=True)
             except: pass
        return False

def get_build_target_and_executable(project_path: Union[str, Path, None]) -> Tuple[Union[str, None], Union[str, None]]:
    """Determines the Unity build target string and expected executable path based on the OS."""
    if not project_path:
        print("Warning: Cannot determine build target, project path is None.")
        return None, None

    project_path = Path(project_path) # Ensure Path object
    system = platform.system()
    executable_name = SIMULATION_PROJECT_NAME # Base name from global constant

    build_target = None
    platform_folder = None
    executable_suffix = ""

    if system == "Windows":
        build_target, platform_folder, executable_suffix = "Win64", "Windows", ".exe"
    elif system == "Linux":
        build_target, platform_folder, executable_suffix = "Linux64", "Linux", ""
    elif system == "Darwin": # macOS
        build_target, platform_folder, executable_suffix = "OSXUniversal", "Mac", ".app"
    else:
        print(f"Warning: Unsupported OS '{system}'. Defaulting build target to Windows.")
        build_target, platform_folder, executable_suffix = "Win64", "Windows", ".exe"

    if build_target and platform_folder:
        build_base_dir = project_path / "Build" / platform_folder
        executable_path = build_base_dir / (executable_name + executable_suffix)
        return build_target, str(executable_path) # Return strings for compatibility
    else:
         return None, None # Should not happen with the default case


# --- Simulation Management Logic ---

def get_simulations() -> list[Dict]:
    """Scans the SIMULATIONS_DIR for valid simulation projects and returns their details."""
    simulations = []
    if not SIMULATIONS_DIR.is_dir():
        # print(f"Simulations directory not found: {SIMULATIONS_DIR}")
        return simulations # Return empty list if base dir doesn't exist

    try:
        for item in SIMULATIONS_DIR.iterdir():
            if item.is_dir():
                # Basic check: Does it contain essential Unity project folders?
                assets_path = item / "Assets"
                settings_path = item / "ProjectSettings"
                if assets_path.is_dir() and settings_path.is_dir():
                    # Get metadata
                    created_str, last_opened_str = "???", "Never"
                    created_timestamp, last_opened_timestamp = 0, 0
                    try:
                        created_timestamp = item.stat().st_ctime
                        created_str = time.strftime("%y-%m-%d %H:%M", time.localtime(created_timestamp))
                    except Exception: pass # Ignore errors getting creation time

                    # Check for our custom last opened file
                    last_opened_file = item / "last_opened.txt"
                    if last_opened_file.is_file():
                        try:
                            with open(last_opened_file, "r") as f:
                                last_opened_timestamp = float(f.read().strip())
                            last_opened_str = time.strftime("%y-%m-%d %H:%M", time.localtime(last_opened_timestamp))
                        except (ValueError, OSError): pass # Ignore errors reading/parsing last opened time

                    simulations.append({
                        "name": item.name,
                        "creation": created_str,
                        "last_opened": last_opened_str,
                        "creation_ts": created_timestamp, # Keep timestamp for sorting
                        # Add last_opened_timestamp if needed for sorting:
                        # "last_opened_ts": last_opened_timestamp
                    })
    except Exception as e:
        print(f"Error reading simulations from {SIMULATIONS_DIR}: {e}")
        return [] # Return empty list on error

    # print(f"Found {len(simulations)} simulations.")
    return simulations

def update_last_opened(sim_name: str):
    """Updates the 'last_opened.txt' timestamp file for a given simulation."""
    simulation_folder = SIMULATIONS_DIR / sim_name
    try:
        simulation_folder.mkdir(parents=True, exist_ok=True) # Ensure folder exists
        last_opened_file = simulation_folder / "last_opened.txt"
        with open(last_opened_file, "w") as f:
            f.write(str(time.time())) # Write current timestamp
    except Exception as e:
        print(f"[Error] Failed to update last opened timestamp for '{sim_name}': {e}")

def read_last_loaded_simulation_name() -> Union[str, None]:
    """
    Reads the name of the last loaded simulation from the state file
    (expected at SIMULATION_LOADED_FILE).
    Handles None, Path, or string input for SIMULATION_LOADED_FILE defensively.
    Returns the simulation name (str) or None if not found/error.
    """
    global SIMULATION_LOADED_FILE # Access the global variable

    file_path_obj = None

    # --- Defensive Check and Conversion ---
    current_value = SIMULATION_LOADED_FILE # Capture the value for checking
    if isinstance(current_value, Path):
        file_path_obj = current_value
    elif isinstance(current_value, str) and current_value:
        # Log a warning if it's unexpectedly a string, then try to convert
        print(f"Warning: read_last_loaded_simulation_name received SIMULATION_LOADED_FILE as a string ('{current_value}'). Converting to Path.")
        try:
            file_path_obj = Path(current_value)
        except Exception as e:
            # Log error if conversion fails, cannot proceed
            print(f"Error converting string '{current_value}' to Path in read_last_loaded_simulation_name: {e}")
            return None
    elif current_value is None:
        # It's expected that it might be None initially or after deletion
        pass # file_path_obj remains None
    else:
        # Log if it's some other unexpected type
        print(f"Warning: read_last_loaded_simulation_name received SIMULATION_LOADED_FILE with unexpected type: {type(current_value)}")
        return None
    # --- End Defensive Check ---

    # Proceed only if we have a valid Path object AND the file exists
    if file_path_obj and file_path_obj.exists() and file_path_obj.is_file():
        try:
            # Use the confirmed Path object to open the file
            with open(file_path_obj, "r", encoding="utf-8") as f:
                content = f.read().strip()
                # Return content only if it's not empty
                return content if content else None
        except Exception as e:
            print(f"Error reading simulation name from {file_path_obj}: {e}")
            return None # Return None on read error
    else:
        # Return None if path is None or file doesn't exist/is not a file
        # print(f"Debug: State file path is None or does not exist/is not a file: {file_path_obj}") # Optional debug
        return None

def load_simulation(sim_name: str) -> bool:
    """
    Loads a simulation by copying its files ('Assets', 'Packages', 'ProjectSettings')
    from the SIMULATIONS_DIR to the active UNITY_PROJECTS_PATH/SIMULATION_PROJECT_NAME.
    Updates the state file in StreamingAssets.
    Returns True on success, False on failure.
    """
    global last_simulation_loaded, SIMULATION_PROJECT_PATH, ASSETS_FOLDER, STREAMING_ASSETS_FOLDER, SIMULATION_LOADED_FILE

    # --- Pre-checks ---
    if not unity_projects_path_ok or not UNITY_PROJECTS_PATH:
        messagebox.showerror("Configuration Error", "Cannot load simulation: The Unity Projects Path is not configured or invalid in the .env file.")
        return False

    # Define target paths using Pathlib
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

    # Ensure the main Unity project directory exists
    try:
        SIMULATION_PROJECT_PATH.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        messagebox.showerror("Directory Error", f"Could not create or access the target Unity project directory:\n{SIMULATION_PROJECT_PATH}\n\nError: {e}")
        return False

    # --- Determine if a full copy is needed ---
    # A full copy is needed if:
    # - The state file doesn't exist or is empty.
    # - The state file contains a different simulation name.
    # - The target Assets folder doesn't exist (implies a fresh or corrupted target).
    current_persistent_loaded = read_last_loaded_simulation_name()
    needs_full_copy = (
        not current_persistent_loaded or
        current_persistent_loaded != sim_name or
        not ASSETS_FOLDER.is_dir() # Check if Assets exists
    )
    copy_operation = "Full Copy" if needs_full_copy else "Update"

    print(f"Load '{sim_name}': Performing '{copy_operation}'.")

    # --- Perform Copy ---
    copy_ok = True
    folders_to_copy = ["Assets", "Packages", "ProjectSettings"]

    if needs_full_copy:
        update_status(f"Loading '{sim_name}': Full copy (Assets, Packages, Settings)...")
        # Remove existing folders first to ensure clean state
        for folder_name in folders_to_copy:
            target_folder = SIMULATION_PROJECT_PATH / folder_name
            if target_folder.exists():
                 try:
                      if target_folder.is_dir(): shutil.rmtree(target_folder, ignore_errors=True)
                      else: target_folder.unlink(missing_ok=True)
                      time.sleep(0.1) # Filesystem delay buffer
                 except Exception as rm_e: print(f"Warning: Could not remove existing '{target_folder}' before copy: {rm_e}")

        # Copy required folders
        for folder_name in folders_to_copy:
            src_folder = source_path / folder_name
            dst_folder = SIMULATION_PROJECT_PATH / folder_name
            if src_folder.is_dir():
                print(f"  Copying {folder_name}...")
                if not copy_directory(src_folder, dst_folder):
                    copy_ok = False
                    break # Stop if any copy fails
            elif folder_name in ["Assets", "ProjectSettings"]: # Packages is optional sometimes
                messagebox.showwarning("Missing Folder", f"Required folder '{folder_name}' is missing in the source simulation '{sim_name}'. The loaded project might be incomplete.")
                # Decide if this is critical - Assets probably is.
                if folder_name == "Assets": copy_ok = False; break
    else:
        # Only update Assets if not doing a full copy
        update_status(f"Loading '{sim_name}': Updating Assets folder...")
        src_assets = source_path / "Assets"
        dst_assets = ASSETS_FOLDER # Already defined Path object
        if src_assets.is_dir():
            if not copy_directory(src_assets, dst_assets): # copy_directory handles removal of dst
                copy_ok = False
        else:
            messagebox.showerror("Load Error", f"Cannot update: 'Assets' folder is missing in the source simulation '{sim_name}'.")
            copy_ok = False

    # --- Finalize and Update State ---
    if not copy_ok:
        update_status(f"Error during file copy for '{sim_name}'. Load cancelled.")
        return False

    try:
        # Ensure StreamingAssets exists and write the state file
        STREAMING_ASSETS_FOLDER.mkdir(parents=True, exist_ok=True)
        with open(SIMULATION_LOADED_FILE, "w") as f:
            f.write(sim_name)
        print(f"State file '{SIMULATION_LOADED_FILE.name}' updated with: {sim_name}")
    except Exception as e:
        # This is usually less critical, but warn the user
        messagebox.showwarning("State File Error", f"Could not create StreamingAssets folder or update the simulation state file:\n{SIMULATION_LOADED_FILE}\n\nError: {e}")
        # Proceed, but the state might be inconsistent

    # Update internal state and UI
    update_last_opened(sim_name) # Update timestamp in source sim dir
    last_simulation_loaded = sim_name # Update global variable

    # Refresh the simulation list in the GUI (schedule in main thread)
    if 'main_window' in globals() and main_window and main_window.winfo_exists():
        main_window.after(50, populate_simulations)
    elif callable(globals().get('populate_simulations')):
         populate_simulations() # Call directly if no GUI

    update_status(f"Simulation '{sim_name}' loaded successfully.")
    return True

def delete_simulation(sim_name: str):
    """
    Deletes a simulation:
    1. Asks for confirmation.
    2. Removes the state file if it corresponds to this simulation.
    3. Deletes the local configuration/metadata directory (SIMULATIONS_DIR/sim_name).
    4. Deletes the Unity-generated data directory (using find_simulation_data_path).
    5. Updates internal data structures and the UI.
    """
    global last_simulation_loaded, all_simulations_data, SIMULATION_LOADED_FILE, SIMULATIONS_DIR

    if not sim_name:
        messagebox.showerror("Error", "No simulation name provided for deletion.")
        return

    # --- 1. Confirmation ---
    confirm = messagebox.askyesno(
        "Confirm Deletion",
        f"Permanently delete the simulation '{sim_name}' and ALL associated data (logs, graphs, configuration)?\n\nThis action cannot be undone!",
        icon='warning' # Use warning icon
    )
    if not confirm:
        if callable(globals().get('update_status')): update_status("Deletion cancelled.")
        print(f"Deletion of '{sim_name}' cancelled by user.")
        return

    if callable(globals().get('update_status')): update_status(f"Deleting '{sim_name}'...")
    print(f"--- Starting deletion of '{sim_name}' ---")
    errors_occurred = False # Flag to track if any step fails

    # --- 2. Handle State File (Last Loaded) ---
    # print(f"  Checking state file status. Current global value: {SIMULATION_LOADED_FILE}")

    state_file_path_obj = None # Variable to hold the confirmed Path object

    # --- Defensive Check and Conversion for SIMULATION_LOADED_FILE ---
    current_state_file_value = SIMULATION_LOADED_FILE # Get current global value
    if isinstance(current_state_file_value, Path):
        state_file_path_obj = current_state_file_value
    elif isinstance(current_state_file_value, str) and current_state_file_value:
        # print(f"  Warning: SIMULATION_LOADED_FILE is a string ('{current_state_file_value}') in delete_simulation. Converting to Path.")
        try: state_file_path_obj = Path(current_state_file_value)
        except Exception as e:
            print(f"  Error converting state file string '{current_state_file_value}' to Path: {e}"); errors_occurred = True
    elif current_state_file_value is None: pass # Okay if None
    else:
        print(f"  Warning: Global SIMULATION_LOADED_FILE has unexpected type: {type(current_state_file_value)}"); errors_occurred = True
    # --- End Defensive Check ---

    # Proceed only if we have a valid Path object
    if state_file_path_obj:
        # print(f"  Attempting operations on verified state file path: {state_file_path_obj}")
        if state_file_path_obj.is_file(): # Check if it exists and is a file
            # print(f"  State file exists on disk.")
            try:
                loaded_name_from_file = read_last_loaded_simulation_name() # Use reliable read function
                # print(f"  Simulation name read from state file: '{loaded_name_from_file}'")
                # If it matches the simulation being deleted, remove the file
                if loaded_name_from_file == sim_name:
                    state_file_path_obj.unlink() # Use Path method unlink()
                    print(f"  State file '{state_file_path_obj}' deleted because it contained '{sim_name}'.")
                    # Clear the global 'last_simulation_loaded' variable as well
                    if last_simulation_loaded == sim_name:
                        last_simulation_loaded = None
                        print("  Global 'last_simulation_loaded' variable cleared.")
            except Exception as e:
                # Catch errors during read/unlink
                print(f"  Warning: Could not read or delete state file '{state_file_path_obj}': {e}")
                errors_occurred = True
        else:
            # print(f"  State file path defined but file not found or not a file at: {state_file_path_obj}")
            # Still clear the global variable if it matches the one being deleted
            if last_simulation_loaded == sim_name:
                 last_simulation_loaded = None
                 print("  Global 'last_simulation_loaded' cleared (state file didn't exist or wasn't a file).")
    else:
        # state_file_path_obj is None (either initially or due to conversion error)
        # print("  Skipping state file operations (Path object is None or invalid).")
        # Still clear the global 'last_simulation_loaded' if it matches the sim being deleted
        if last_simulation_loaded == sim_name:
             last_simulation_loaded = None
             print("  Global 'last_simulation_loaded' cleared (state file path was None/invalid).")


    # --- 3. Delete LOCAL Simulation Directory (Configuration/Metadata) ---
    # This is the directory managed by this application, inside SIMULATIONS_DIR.
    if isinstance(SIMULATIONS_DIR, Path):
        local_sim_path = SIMULATIONS_DIR / sim_name # Build Path using Pathlib operator
        print(f"  Attempting to delete local config directory: {local_sim_path}")
        if local_sim_path.exists():
            if local_sim_path.is_dir():
                try:
                    shutil.rmtree(local_sim_path)
                    print(f"    Local config directory '{local_sim_path}' deleted.")
                except PermissionError as e:
                    messagebox.showerror("Permission Error", f"Permission denied while deleting the local configuration folder:\n{local_sim_path}\n\n{e}")
                    errors_occurred = True
                except OSError as e:
                    messagebox.showerror("System Error", f"Could not delete the local configuration folder (in use?):\n{local_sim_path}\n\n{e}")
                    errors_occurred = True
                except Exception as e:
                    messagebox.showerror("Unexpected Error", f"An unexpected error occurred deleting the local configuration folder:\n{local_sim_path}\n\n{e}")
                    traceback.print_exc()
                    errors_occurred = True
            else:
                # Handle case where local_sim_path is unexpectedly a file
                print(f"  Warning: Expected a directory at '{local_sim_path}', but found a file. Attempting to delete file...")
                try:
                    local_sim_path.unlink() # Attempt to delete as file
                except Exception as e:
                     print(f"  Error deleting unexpected file at '{local_sim_path}': {e}")
                     errors_occurred = True
        else:
             print(f"  Local config directory '{local_sim_path}' not found (nothing to delete).")
    else:
        # This is a critical internal configuration error
        print(f"  CRITICAL ERROR: SIMULATIONS_DIR is not a Path object ({type(SIMULATIONS_DIR)}). Cannot delete local sim folder.")
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
            messagebox.showerror("Internal Error", f"Configuration Error: SIMULATIONS_DIR type is {type(SIMULATIONS_DIR)}, expected Path. Cannot delete local data.")
        errors_occurred = True # Mark as error


    # --- 4. Delete Unity-Generated DATA Directory (persistentDataPath) ---
    print(f"  Attempting to delete Unity data directory for '{sim_name}'...")
    # Use the helper function to find the correct path
    unity_data_path = find_simulation_data_path(sim_name) # Returns Path or None

    if unity_data_path is None:
        # find_simulation_data_path should have already printed a detailed error
        print(f"  Info: Could not determine the Unity data directory path for '{sim_name}'. Skipping deletion (may not exist).")
        # Optionally show a non-blocking warning if this is unexpected
        # messagebox.showwarning("Data Not Found", f"Could not find the data folder generated by Unity for '{sim_name}'. It might have already been deleted or couldn't be located.")
        # Don't mark as error unless deletion is strictly required
    elif unity_data_path.exists():
        if unity_data_path.is_dir():
            try:
                shutil.rmtree(unity_data_path)
                print(f"    Unity data directory '{unity_data_path}' deleted.")
            except PermissionError as e:
                messagebox.showerror("Permission Error", f"Permission denied while deleting the Unity data folder:\n{unity_data_path}\n\n{e}")
                errors_occurred = True
            except OSError as e:
                messagebox.showerror("System Error", f"Could not delete the Unity data folder (in use?):\n{unity_data_path}\n\n{e}")
                errors_occurred = True
            except Exception as e:
                messagebox.showerror("Unexpected Error", f"An unexpected error occurred deleting the Unity data folder:\n{unity_data_path}\n\n{e}")
                traceback.print_exc()
                errors_occurred = True
        else:
            # Unusual if find_simulation_data_path worked, but handle for safety
            print(f"  Warning: Expected a directory at '{unity_data_path}', but found a file. File not deleted.")
            errors_occurred = True # Consider this an error state
    else:
        print(f"  Unity data directory '{unity_data_path}' not found (nothing to delete).")

    # --- 5. Update Internal Data Structure ---
    if 'all_simulations_data' in globals():
        initial_count = len(all_simulations_data)
        # Filter out the simulation being deleted (handle potential non-dict items)
        all_simulations_data[:] = [s for s in all_simulations_data if isinstance(s, dict) and s.get('name') != sim_name]
        if len(all_simulations_data) < initial_count:
             print(f"  Entry for '{sim_name}' removed from internal 'all_simulations_data' list.")
        else:
             print(f"  Warning: '{sim_name}' not found in internal 'all_simulations_data' list to remove.")

    # --- 6. Final Status Update and UI Refresh ---
    print(f"--- Finished deletion process for '{sim_name}' ---")
    final_message = f"Deletion of '{sim_name}' completed"
    if errors_occurred:
        final_message += " with errors."
        print("  Errors occurred during the deletion process. Please review previous messages.")
    else:
        final_message += " successfully."
        print("  Deletion completed without reported errors.")

    # Update status bar
    if callable(globals().get('update_status')):
        update_status(final_message)

    # Refresh the simulation list in the UI
    if callable(globals().get('populate_simulations')):
        print("  Refreshing simulation list in UI...")
        # Run populate_simulations in the main thread if necessary
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
             main_window.after(0, populate_simulations)
        else:
             populate_simulations() # Call directly if no GUI context or already in main thread
    else:
        print("  Warning: Function 'populate_simulations' not found to refresh UI.")


# --- Unity Batch Execution & Progress Monitoring ---

def format_time(seconds: Union[float, int, None]) -> str:
    """Formats seconds into HH:MM:SS, MM:SS, or Xs format."""
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
                print(f"[{operation_tag}] Monitor: Project path '{project_path}' not found initially. Will check again.")
        except Exception as path_e:
            print(f"[{operation_tag}] Monitor Error: Invalid project path '{SIMULATION_PROJECT_PATH}': {path_e}")
            update_status(f"[{operation_tag}] Error: Invalid project path. Cannot monitor.")
            return
    else:
        print(f"[{operation_tag}] Monitor Error: SIMULATION_PROJECT_PATH is None. Cannot monitor.")
        update_status(f"[{operation_tag}] Error: Project path not set. Cannot monitor.")
        return

    UPDATE_INTERVAL = 1.0
    SIZE_CHECK_INTERVAL = 5.0

    last_time_update = 0
    last_size_check_time = 0
    last_logged_mb = -1.0
    start_time = time.time()

    print(f"[{operation_tag}] Monitor Thread Started. Tracking elapsed time.")
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
                         print(f"  MONITOR [{operation_tag}]: Current size ~{current_mb:.1f} MB (at {format_time(current_time - start_time)})")
                         last_logged_mb = current_mb
                else:
                    if last_logged_mb != -999:
                         print(f"  MONITOR [{operation_tag}]: Project directory '{project_path.name}' not found during size check.")
                         last_logged_mb = -999
            except Exception as e:
                 print(f"  MONITOR [{operation_tag}]: Warning - Error checking size: {e}")
            last_size_check_time = current_time
        time.sleep(0.3)

    final_elapsed_time = time.time() - start_time
    print(f"\n[{operation_tag}] Monitor Stopped. Total Duration: {format_time(final_elapsed_time)}")
    if project_path:
        try:
            if project_path.is_dir():
                 final_bytes = get_folder_size(project_path)
                 final_mb = final_bytes / (1024*1024)
                 print(f"[{operation_tag}] Final project size: ~{final_mb:.1f} MB")
            else:
                 print(f"[{operation_tag}] Final project directory not found.")
        except Exception as e:
            print(f"[{operation_tag}] Warning - Error getting final size: {e}")

def run_unity_batchmode(exec_method: str, op_name: str, log_file_name: str, timeout: int = 600, extra_args: list = None) -> tuple[bool, Union[str, None]]:
    """
    Runs Unity in batch mode to execute a specific editor script method.
    Monitors progress using folder size.
    Returns (success_bool, executable_path_if_build_or_None).
    """
    # --- Pre-checks ---
    if not all([unity_path_ok, unity_version_ok, unity_projects_path_ok, SIMULATION_PROJECT_PATH]):
        update_status(f"Error: Cannot run Unity '{op_name}'. Check Unity configuration.")
        messagebox.showerror("Configuration Error", f"Cannot run the Unity {op_name} operation.\nPlease verify the Unity executable path, version, and projects path in Settings.")
        return False, None

    project_path_obj = Path(SIMULATION_PROJECT_PATH)
    if not project_path_obj.is_dir():
         update_status(f"Error: Project path does not exist: {project_path_obj}")
         messagebox.showerror("Project Not Found", f"The Unity project path does not exist or is not a directory:\n{project_path_obj}")
         return False, None

    log_path = project_path_obj / log_file_name

    # --- Construct Command ---
    command = [
        UNITY_EXECUTABLE,
        "-batchmode",
        "-quit", # Quit after execution
        "-projectPath", str(project_path_obj.resolve()), # Use resolved absolute path
        "-executeMethod", exec_method,
        "-logFile", str(log_path.resolve()) # Use absolute path for log
    ]
    if extra_args:
        command.extend(extra_args)

    print(f"\n--- Running Unity ({op_name}) ---")
    print(f"Command: {' '.join(command)}") # Log the command for debugging

    success = False
    stop_monitor_event = threading.Event()
    executable_path = None # Store path if it's a build operation

    # Start progress monitor in a separate thread
    monitor_thread = threading.Thread(target=monitor_unity_progress, args=(stop_monitor_event, op_name.capitalize()), daemon=True)

    try:
        update_status(f"[{op_name.capitalize()}] Starting Unity process...")
        monitor_thread.start()

        # Platform-specific flags for subprocess
        creation_flags = 0
        if platform.system() == "Windows":
            creation_flags = subprocess.CREATE_NO_WINDOW # Hide console window on Windows

        # Run the Unity process
        process = subprocess.run(
            command,
            check=True, # Raises CalledProcessError on non-zero exit code
            timeout=timeout, # Timeout in seconds
            creationflags=creation_flags,
            capture_output=True, # Capture stdout/stderr
            text=True, # Decode output as text
            encoding='utf-8', # Specify encoding
            errors='ignore' # Ignore decoding errors
        )

        # Log output if successful (last 1000 chars)
        print(f"--- Unity Stdout ({op_name}) ---")
        print(process.stdout[-1000:])
        print("--- End Unity Stdout ---")
        if process.stderr:
            print(f"--- Unity Stderr ({op_name}) ---")
            print(process.stderr[-1000:])
            print("--- End Unity Stderr ---")

        update_status(f"[{op_name.capitalize()}] Unity process finished successfully.")
        success = True

        # --- Post-Build Check (if applicable) ---
        if "BuildScript.PerformBuild" in exec_method:
            update_status(f"[{op_name.capitalize()}] Verifying build output...")
            _, build_exe_path_str = get_build_target_and_executable(SIMULATION_PROJECT_PATH)

            if build_exe_path_str:
                build_exe_path = Path(build_exe_path_str)
                found = False
                # Check multiple times for filesystem delays, especially on network drives/VMs
                for attempt in range(6):
                    time.sleep(0.5 * attempt) # Increasing delay
                    if build_exe_path.exists() and (build_exe_path.is_file() or build_exe_path.is_dir()): # Check exists and type (.app is dir)
                        found = True
                        executable_path = str(build_exe_path) # Store the verified path
                        print(f"Build output verified successfully (Attempt {attempt+1}): {executable_path}")
                        break
                    else:
                        print(f"Build output check attempt {attempt+1} failed for: {build_exe_path}")

                if found:
                    update_status(f"[{op_name.capitalize()}] Build executable verified.")
                else:
                    print(f"ERROR: Build output NOT FOUND after checks: {build_exe_path}")
                    success = False # Mark as failure if output is missing
                    handle_unity_execution_error(FileNotFoundError(f"Build output '{build_exe_path.name}' not found in '{build_exe_path.parent}' after process completion."), op_name)
                    update_status(f"[Error] {op_name.capitalize()} failed: Build output missing.")
            else:
                 print("ERROR: Could not determine expected build executable path.")
                 success = False
                 update_status(f"[Error] {op_name.capitalize()} failed: Could not determine output path.")


    # --- Error Handling ---
    except subprocess.CalledProcessError as e:
        handle_unity_execution_error(e, op_name)
        update_status(f"[Error] {op_name.capitalize()} failed (Exit Code {e.returncode}). See console/log: {log_path.name}")
        # Optionally log the full output on error
        # print(f"--- Unity Output on Error ({op_name}) ---")
        # print("Stdout:\n", e.stdout)
        # print("Stderr:\n", e.stderr)
        # print("--- End Unity Output on Error ---")
    except subprocess.TimeoutExpired as e:
        handle_unity_execution_error(e, op_name)
        update_status(f"[Error] {op_name.capitalize()} timed out after {timeout}s. See log: {log_path.name}")
    except (FileNotFoundError, PermissionError) as e: # Errors starting the process
        handle_unity_execution_error(e, op_name)
        update_status(f"[Error] {op_name.capitalize()} failed (File Not Found or Permission). Check Unity path.")
    except Exception as e: # Catch-all for unexpected errors
        handle_unity_execution_error(e, f"{op_name} (unexpected)")
        update_status(f"[Error] Unexpected error during {op_name}. Check console.")
    finally:
        # Ensure the monitor thread is stopped
        stop_monitor_event.set()
        if monitor_thread.is_alive():
             monitor_thread.join(timeout=1.0) # Wait briefly for monitor to finish

    print(f"--- Unity ({op_name}) Finished. Success: {success} ---")
    return success, executable_path # Return success status and path (if applicable)


def run_prefab_material_tool() -> bool:
    """Runs the Unity batch process specifically for creating prefabs and materials."""
    update_status("Running prefab/material creation tool...")
    success, _ = run_unity_batchmode(
        exec_method="PrefabMaterialCreator.CreatePrefabsAndMaterials",
        op_name="Prefab Tool",
        log_file_name="prefab_tool_log.txt",
        timeout=600 # 10 minutes timeout
    )
    if success:
         update_status("Prefab/material tool completed successfully.")
    else:
         update_status("Error during prefab/material creation. Check logs.")
    return success

def build_simulation_task(extra_args: list, callback):
    """Task run in a thread to build the simulation and call the callback."""
    disable_all_interactions() # Disable UI during build
    success, final_exe_path = run_unity_batchmode(
        exec_method="BuildScript.PerformBuild",
        op_name="Build",
        log_file_name="build_log.txt",
        timeout=1800, # 30 minutes timeout for build
        extra_args=extra_args
    )

    # Schedule callback execution in the main GUI thread
    if callback:
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
            main_window.after(0, lambda s=success, p=final_exe_path: callback(s, p))
        else:
             print("Warning: Main window not available for build callback.")
             # Optionally call directly, but beware of thread safety issues if callback interacts with GUI
             # callback(success, final_exe_path)

    # Re-enable interactions after the build attempt (also in main thread)
    if 'main_window' in globals() and main_window and main_window.winfo_exists():
        main_window.after(10, enable_all_interactions)
    else:
         enable_all_interactions() # Call directly if no GUI


def build_simulation_threaded(callback=None):
    """Starts the simulation build process in a separate thread."""
    # Determine build target based on current OS
    build_target, _ = get_build_target_and_executable(SIMULATION_PROJECT_PATH)
    if not build_target:
        print("Error: Could not determine build target for the current OS.")
        update_status("Error: Build target unknown. Cannot start build.")
        messagebox.showerror("Build Error", "Could not determine the build target for your operating system.")
        return

    # Start the build task in a new daemon thread
    build_thread = threading.Thread(
        target=build_simulation_task,
        args=(["-buildTarget", build_target], callback), # Pass build target as extra arg
        daemon=True
    )
    build_thread.start()


def open_simulation_executable():
    """Launches the built simulation executable for the current OS."""
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
            print(f"Attempting to launch: {exe_path}")

            if platform.system() == "Darwin": # macOS (.app is a directory)
                 if exe_path.is_dir():
                      subprocess.Popen(["open", str(exe_path)])
                 else:
                      raise FileNotFoundError(f".app bundle not found or is not a directory: {exe_path}")
            elif platform.system() == "Windows": # Windows (.exe is a file)
                 if exe_path.is_file():
                      os.startfile(str(exe_path)) # Recommended way to open files on Windows
                 else:
                      raise FileNotFoundError(f"Executable file not found or is not a file: {exe_path}")
            else: # Linux (executable file, might need permissions)
                 if exe_path.is_file():
                     # Ensure execute permission
                     if not os.access(str(exe_path), os.X_OK):
                          print(f"  Adding execute permission to: {exe_path}")
                          try:
                              os.chmod(str(exe_path), os.stat(str(exe_path)).st_mode | 0o111) # Add execute for user/group/other
                          except Exception as chmod_e:
                              print(f"  Warning: Failed to set execute permission: {chmod_e}")
                     # Launch from its directory
                     subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent))
                 else:
                      raise FileNotFoundError(f"Executable file not found or is not a file: {exe_path}")

            update_status(f"Launched {base_name}.")
        except Exception as e:
            handle_unity_execution_error(e, f"launch simulation ({exe_path.name})")
            update_status(f"Error launching simulation: {e}")
    else:
        messagebox.showerror("Executable Not Found", f"The simulation executable was not found at:\n{exe_path}\n\nPlease build the simulation first.")
        update_status("Error: Simulation executable not found.")


def open_in_unity():
    """Opens the current simulation project in the Unity Editor."""
    # --- Pre-checks ---
    if not all([unity_path_ok, unity_projects_path_ok, UNITY_EXECUTABLE, SIMULATION_PROJECT_PATH]):
        messagebox.showerror("Configuration Error", "Cannot open in Unity. Please check Unity executable and project paths in Settings.")
        return

    project_path_obj = Path(SIMULATION_PROJECT_PATH)
    if not project_path_obj.is_dir():
        messagebox.showerror("Project Not Found", f"The project path does not exist or is not a directory:\n{project_path_obj}")
        return

    # --- Launch Unity ---
    try:
        update_status(f"Opening project '{project_path_obj.name}' in Unity Editor...")
        command = [UNITY_EXECUTABLE, "-projectPath", str(project_path_obj.resolve())]
        print(f"Launching Unity Editor with command: {' '.join(command)}")

        # Use Popen for non-blocking launch
        subprocess.Popen(command)

        update_status("Unity Editor is launching...")
    except Exception as e:
        handle_unity_execution_error(e, "open project in Unity")
        update_status("Error launching Unity Editor.")


# --- API Simulation Creation ---

def create_simulation_thread(sim_name: str, sim_desc: str):
    """
    Handles the simulation creation process via API in a separate thread.
    Updates status and shows messages upon completion or error.
    """
    update_status(f"Creating '{sim_name}' using API...")
    success = False
    error_message_detail = f"An unknown error occurred during the creation of '{sim_name}'."

    try:
        # Ensure base simulations directory exists
        try:
            SIMULATIONS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            error_message_detail = f"Could not create the base simulations directory:\n{SIMULATIONS_DIR}\n\n{type(e).__name__}: {e}"
            success = False
            # Show error immediately in main thread
            if 'main_window' in globals() and main_window:
                 main_window.after(0, lambda msg=error_message_detail: messagebox.showerror("Critical Setup Error", msg))
            update_status("Critical directory creation error. Cannot continue.")
            # No finally block needed here as interactions weren't disabled yet typically
            return # Stop the thread

        # Call the API manager function (handles API calls, caching, file import)
        success, error_message = api_manager(sim_name, sim_desc, use_cache=True) # Use cache by default

        # --- Process Result ---
        if success:
            final_message = f"Simulation '{sim_name}' created successfully via API."
            update_status(final_message)
            print(final_message)
            # Show success message in main thread
            if 'main_window' in globals() and main_window:
                 main_window.after(0, lambda name=sim_name: messagebox.showinfo("Success", f"Simulation '{name}' created successfully."))

            # Refresh simulation list data and UI (in main thread)
            global all_simulations_data
            all_simulations_data = get_simulations() # Update internal list
            if 'main_window' in globals() and main_window:
                 main_window.after(50, populate_simulations) # Refresh GUI list

        else:
            # api_manager returns a specific error message on failure
            error_message_detail = error_message if error_message else f"Failed to create simulation '{sim_name}'. Reason unknown (check console logs)."
            update_status(f"Error creating '{sim_name}'. Check logs.")
            print(f"Error creating '{sim_name}': {error_message_detail}")
            # Show error message in main thread
            if 'main_window' in globals() and main_window:
                 main_window.after(0, lambda msg=error_message_detail: messagebox.showerror("Simulation Creation Failed", msg))

    except Exception as e:
        # Catch unexpected errors within this thread's logic
        error_type = type(e).__name__
        error_msg = str(e)
        detailed_error = traceback.format_exc()

        error_message_detail = f"A critical unexpected error occurred during the simulation creation process:\n{error_type}: {error_msg}\n\nPlease check the console logs for a detailed traceback."
        if 'main_window' in globals() and main_window:
             main_window.after(0, lambda msg=error_message_detail: messagebox.showerror("Unexpected Creation Error", msg))
        update_status(f"Critical error during creation: {error_type}")
        print(f"--- CRITICAL ERROR in create_simulation_thread ---")
        print(detailed_error)
        print(f"--- End Critical Error ---")
        success = False # Ensure success is False

    finally:
        # --- Re-enable UI Interactions ---
        # Always re-enable interactions, regardless of success/failure
        if 'main_window' in globals() and main_window:
            main_window.after(100, enable_all_interactions) # Schedule in main thread
        else:
             enable_all_interactions() # Call directly if no GUI context

        print(f"Simulation creation thread for '{sim_name}' finished. Success: {success}")
        if not success:
            print(f"Failure reason logged above or: {error_message_detail}")


# --- Verification Logic ---

def perform_verification(show_results_box=False, on_startup=False):
    """
    Verifies Unity setup locally and API config via the server.
    Updates global status variables and the UI status bar.
    Optionally shows a detailed results message box.
    """
    global unity_path_ok, unity_version_ok, unity_projects_path_ok, apis_key_ok, apis_models_ok, initial_verification_complete
    global UNITY_EXECUTABLE, UNITY_PROJECTS_PATH, API_BASE_URL, API_KEY # Use API_KEY for client auth
    global SIMULATION_PROJECT_PATH, ASSETS_FOLDER, STREAMING_ASSETS_FOLDER, SIMULATION_LOADED_FILE, last_simulation_loaded, all_simulations_data

    if not on_startup: update_status("Verifying configuration...")
    load_dotenv('.env', override=True)
    UNITY_EXECUTABLE = os.getenv("UNITY_EXECUTABLE"); UNITY_PROJECTS_PATH = os.getenv("UNITY_PROJECTS_PATH")
    API_BASE_URL = os.getenv("API_BASE_URL"); API_KEY = os.getenv("API_KEY") # Load client API key

    # Reset status flags
    unity_path_ok=unity_version_ok=unity_projects_path_ok=apis_key_ok=apis_models_ok=False
    results = []; req_ver = UNITY_REQUIRED_VERSION_STRING

    # --- 1. Verify Unity Executable and Version (Local Check) ---
    if not UNITY_EXECUTABLE: results.append("❌ Unity Executable: Path missing in .env file.")
    # Use Path for existence check
    elif not Path(UNITY_EXECUTABLE).exists(): results.append(f"❌ Unity Executable: Path does not exist:\n   '{UNITY_EXECUTABLE}'")
    else:
        unity_path_ok = True; results.append(f"✅ Unity Executable: Path exists.")
        # OS-specific file/directory and version check
        try:
            current_os = platform.system()
            unity_exe_path = Path(UNITY_EXECUTABLE).resolve()

            if current_os == "Windows":
                if not unity_exe_path.is_file():
                    results.append(f"❌ Unity Exe: Path is not a file on Windows:\n    '{UNITY_EXECUTABLE}'")
                    unity_path_ok = False
                else: # Check version based on path structure
                    expected_suffix = Path(req_ver) / "Editor" / "Unity.exe"
                    # Check if the resolved path ends with the expected structure (case-insensitive on Windows)
                    if str(unity_exe_path).lower().endswith(str(expected_suffix).lower()):
                        unity_version_ok = True; results.append(f"✅ Unity Version: Path indicates version {req_ver}.")
                    else: # Fallback check on parent folder name
                        if unity_exe_path.parent.parent.name == req_ver:
                            unity_version_ok = True; results.append(f"✅ Unity Version: Parent folder matches version {req_ver}.")
                        else:
                            results.append(f"❌ Unity Version: Path structure/parent folder mismatch (Req: '{req_ver}').")
            elif current_os == "Darwin": # macOS Check
                 is_app_bundle = unity_exe_path.is_dir() and unity_exe_path.suffix == ".app"
                 is_binary_inside = unity_exe_path.is_file() and "Contents/MacOS/Unity" in str(unity_exe_path)
                 plist_path = None
                 if is_app_bundle: plist_path = unity_exe_path / "Contents" / "Info.plist"
                 elif is_binary_inside:
                      bundle_candidate = unity_exe_path
                      for _ in range(3): # Look up max 3 levels for .app folder
                           if bundle_candidate.suffix == ".app": break
                           bundle_candidate = bundle_candidate.parent
                      if bundle_candidate.suffix == ".app" and bundle_candidate.is_dir(): plist_path = bundle_candidate / "Contents" / "Info.plist"
                      else: unity_path_ok = False; results.append(f"❌ Unity Exe: Binary path found, but containing '.app' bundle not located.")
                 else: unity_path_ok = False; results.append(f"❌ Unity Exe: Path is not a valid '.app' or recognized executable on macOS.")

                 if unity_path_ok and plist_path and plist_path.exists():
                      try:
                          with open(plist_path, 'rb') as fp: plist_data = plistlib.load(fp)
                          detected_version = plist_data.get('CFBundleShortVersionString', plist_data.get('CFBundleVersion'))
                          if detected_version:
                               results.append(f"ℹ️ Unity Ver: Found '{detected_version}' in Info.plist.")
                               if detected_version == req_ver: unity_version_ok = True; results.append(f"✅ Unity Ver: Info.plist version matches required '{req_ver}'.")
                               else: results.append(f"❌ Unity Ver: Info.plist version '{detected_version}' != required '{req_ver}'.")
                          else: results.append(f"⚠️ Unity Ver: Version not found in Info.plist.")
                      except Exception as plist_err: results.append(f"⚠️ Unity Ver: Error reading Info.plist: {plist_err}")
                 elif unity_path_ok: results.append(f"⚠️ Unity Ver: Could not find/read Info.plist to verify version.")
            else: # Linux / Other OS
                if not unity_exe_path.is_file(): unity_path_ok = False; results.append(f"❌ Unity Exe: Path is not a file on {current_os}.")
                else: # Basic check if version string is in the path for Linux/Other
                    if req_ver in str(unity_exe_path): unity_version_ok = True; results.append(f"✅ Unity Ver: Path contains required version string '{req_ver}'.")
                    else: results.append(f"❌ Unity Ver: Path does not contain required version string '{req_ver}'.")

        except Exception as ver_err: results.append(f"⚠️ Unity Version: Unexpected error during check: {ver_err}")

    # --- 2. Verify Unity Projects Path (Local Check) ---
    if not UNITY_PROJECTS_PATH: results.append("❌ Projects Path: Missing in .env file.")
    elif not Path(UNITY_PROJECTS_PATH).is_dir(): results.append(f"❌ Projects Path: Invalid or not directory:\n   '{UNITY_PROJECTS_PATH}'")
    else:
        unity_projects_path_ok = True; results.append(f"✅ Projects Path: Directory OK.")
        try: # Define project paths only if base path is OK
            base_proj = Path(UNITY_PROJECTS_PATH); SIMULATION_PROJECT_PATH = base_proj / SIMULATION_PROJECT_NAME
            ASSETS_FOLDER = SIMULATION_PROJECT_PATH / "Assets"; STREAMING_ASSETS_FOLDER = ASSETS_FOLDER / "StreamingAssets"
            SIMULATION_LOADED_FILE = STREAMING_ASSETS_FOLDER / "simulation_loaded.txt"; last_simulation_loaded = read_last_loaded_simulation_name()
        except Exception as path_e: results.append(f"⚠️ Project Paths: Error constructing paths: {path_e}"); unity_projects_path_ok = False

    # --- 3. Verify API Server Configuration ---
    if not API_BASE_URL: results.append("❌ API Server URL: Missing in .env file."); results.append("   ↳ Cannot verify server/OpenAI config.")
    elif not API_KEY: results.append("❌ Client API Key: Missing in .env file."); results.append("   ↳ Cannot authenticate with API server.")
    else:
        results.append(f"ℹ️ API Server URL: {API_BASE_URL}")
        verify_url = f"{API_BASE_URL.rstrip('/')}/verify_config"
        headers = {'X-API-Key': API_KEY} # Send client key for server auth
        try:
            print(f"  Verifying API config via server: {verify_url}")
            # Ensure requests library is available
            if 'requests' not in sys.modules:
                 raise ImportError("The 'requests' library is required for API server communication.")

            response = requests.get(verify_url, headers=headers, timeout=15) # 15s timeout
            response.raise_for_status() # Check for HTTP errors (4xx/5xx)
            server_data = response.json()
            print(f"  <- Server Verification Response: {server_data}")

            details = server_data.get('verification_details', {})
            client_auth_status = details.get('api_server_key_status', "ERROR")
            # Consider authentication OK if the status contains OK, verified, or the checkmark emoji
            client_auth_ok = "ok" in client_auth_status.lower() or "verified" in client_auth_status.lower() or "✅" in client_auth_status
            # Check server's OpenAI key status
            server_openai_key_ok = server_data.get('openai_api_key_ok', False)
            # Check server's primary model status
            server_primary_model_ok = server_data.get('primary_model_ok', False)
            
            # API is considered "OK" if client auth passes AND server reports OpenAI key is OK
            apis_key_ok = client_auth_ok and server_openai_key_ok
            apis_models_ok = apis_key_ok and server_primary_model_ok

            # Add detailed results from server response
            results.append(details.get('api_server_key_status', '❔ Client API Key Status (Server): Unknown'))
            results.append(details.get('openai_api_key_status', '❔ OpenAI Key Status (Server): Unknown'))
            results.append(details.get('primary_model_status', '❔ Primary Model Status (Server): Unknown'))
            results.append(details.get('secondary_model_status', '❔ Secondary Model Status (Server): Unknown'))

        except ImportError as imp_err:
             results.append(f"❌ API Server Check: {imp_err}"); apis_key_ok = apis_models_ok = False
        except requests.exceptions.ConnectionError: results.append(f"❌ API Server Check: CONNECTION FAILED! ({API_BASE_URL})"); apis_key_ok = apis_models_ok = False
        except requests.exceptions.Timeout: results.append(f"❌ API Server Check: TIMEOUT! ({API_BASE_URL})"); apis_key_ok = apis_models_ok = False
        except requests.exceptions.RequestException as e:
            status = e.response.status_code if e.response is not None else '??'; err_txt = f"Request failed ({status})."; detail="N/A"
            if e.response is not None:
                try: detail = e.response.json().get('error', e.response.text[:100]+'...')
                except: detail = e.response.text[:100]+'...'; err_txt += f" Detail: {detail}"
                if status == 403: err_txt += "\n   ↳ Access DENIED. Is Client API_KEY correct?"
            results.append(f"❌ API Server Check: {err_txt}"); apis_key_ok = apis_models_ok = False
        except Exception as e: results.append(f"❌ API Server Check: Unexpected error: {type(e).__name__}"); print(f"Verify API Error: {e}"); traceback.print_exc(); apis_key_ok = apis_models_ok = False

    # --- Final Status and UI Update ---
    initial_verification_complete = True
    unity_status = "Unity OK" if unity_path_ok and unity_version_ok and unity_projects_path_ok else "Unity ERR"
    api_status = "API OK" if apis_key_ok and apis_models_ok else "API ERR" # Status based on combined local + server checks
    final_status = f"Status: {unity_status} | {api_status}"

    try: # Safely update GUI
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
            main_window.after(0, lambda: update_status(final_status))
            main_window.after(50, update_button_states)
            if unity_projects_path_ok: all_simulations_data = get_simulations(); main_window.after(100, filter_simulations)
            if on_startup:
                errors = []; api_err = False
                if not unity_path_ok or not unity_projects_path_ok: errors.append("- Invalid Unity Executable or Projects path.")
                elif not unity_version_ok: errors.append(f"- Unity version/path mismatch (Requires '{req_ver}').")
                if not (unity_path_ok and unity_version_ok and unity_projects_path_ok): errors.append("  (Core Unity features might fail)")
                if not API_BASE_URL: errors.append("- API Server URL missing in .env."); api_err=True
                elif not API_KEY: errors.append("- Client API Key missing in .env."); api_err=True
                elif not apis_key_ok: errors.append("- API Server: Auth Error or Server-side OpenAI Key Error."); api_err=True # Combined reason
                elif not apis_models_ok: errors.append("- API Server: Primary Model Error (Server-side)."); api_err=True
                if api_err: errors.append("  (API creation/verification disabled)")
                if errors: msg = "Initial Configuration Issues:\n\n" + "\n".join(errors) + "\n\nPlease use 'Settings' to fix local .env\nand ensure API server is running correctly."; main_window.after(300, lambda m=msg: messagebox.showwarning("Initial Configuration Issues", m))
        else: print(f"Verification Status (No GUI): {final_status}")
    except Exception as ui_err: print(f"Error updating GUI after verification: {ui_err}")

    if show_results_box:
        results_text = "--- Local Verification ---\n" + "\n".join([r for r in results if "Unity" in r or "Proj" in r]) + \
                       "\n\n--- API Server Verification ---\n" + "\n".join([r for r in results if "API" in r or "Model" in r or "?" in r or "Server" in r or "OpenAI" in r]) # Show all API related results
        all_ok = unity_path_ok and unity_version_ok and unity_projects_path_ok and apis_key_ok and apis_models_ok
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
             mtype = messagebox.showinfo if all_ok else messagebox.showwarning; title = "Verification Complete" if all_ok else "Verification Issues Found"
             main_window.after(0, lambda t=title, msg=results_text: mtype(t, msg))
        else: print("\n--- Verification Results ---\n" + results_text + "\n--- End ---")

# --- Configuration Window ---

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


# --- GUI Definitions & Callbacks ---

def cleanup_simulation_logger_data(actual_simulation_names: set):
    """
    Removes subdirectories within the SimulationLoggerData folder that do not
    correspond to existing simulations in the SIMULATIONS_DIR.
    """
    print("\n--- Starting Simulation Logger Data Cleanup ---")
    logger_data_path = None
    try:
        # 1. Find the base persistent data path for the Unity product
        persistent_path = find_unity_persistent_path(UNITY_PRODUCT_NAME)
        if not persistent_path:
            print("  Skipping cleanup: Could not find Unity persistent data path.")
            return

        # 2. Construct the path to the specific logger data folder
        logger_data_path = persistent_path / LOG_SUBFOLDER

        # 3. Check if the logger data folder exists
        if not logger_data_path.is_dir():
            print(f"  Skipping cleanup: Logger data directory not found at '{logger_data_path}'.")
            return

        print(f"  Checking logger data directory: {logger_data_path}")
        deleted_count = 0
        error_count = 0

        # 4. Iterate through items in the logger data folder
        for item in logger_data_path.iterdir():
            # Only consider directories (each representing a simulation's logs)
            if item.is_dir():
                folder_name = item.name
                # 5. Check if the folder name corresponds to an existing simulation
                if folder_name not in actual_simulation_names:
                    print(f"  Found orphaned logger data folder: '{folder_name}'. Deleting...")
                    try:
                        shutil.rmtree(item)
                        print(f"    Successfully deleted '{item}'.")
                        deleted_count += 1
                    except PermissionError:
                        print(f"    Error: Permission denied deleting '{item}'. Skipping.")
                        error_count += 1
                    except OSError as e:
                        print(f"    Error deleting '{item}' (possibly in use?): {e}. Skipping.")
                        error_count += 1
                    except Exception as e:
                        print(f"    Unexpected error deleting '{item}': {e}. Skipping.")
                        traceback.print_exc()
                        error_count += 1
                # else:
                    # print(f"  Keeping valid logger data folder: '{folder_name}'") # Optional: Log kept folders

        print(f"--- Logger Data Cleanup Finished ---")
        if deleted_count > 0:
            print(f"  Deleted {deleted_count} orphaned logger data folder(s).")
        else:
            print(f"  No orphaned logger data folders found to delete.")
        if error_count > 0:
            print(f"  Encountered {error_count} error(s) during deletion.")

    except Exception as e:
        print(f"  Error during logger data cleanup process (Path: {logger_data_path}): {e}")
        traceback.print_exc()

def populate_simulations():
    """Fetches simulation data, performs cleanup, updates list, and refreshes the treeview."""
    if not initial_verification_complete:
        return

    if callable(globals().get('update_status')): update_status("Reloading simulation list and performing cleanup...")

    global all_simulations_data, last_simulation_loaded, SIMULATION_LOADED_FILE

    # 1. Get fresh list of simulations from SIMULATIONS_DIR
    all_simulations_data = get_simulations()
    actual_sim_names = {sim['name'] for sim in all_simulations_data if isinstance(sim, dict) and 'name' in sim}
    print(f"Found {len(actual_sim_names)} simulations in {SIMULATIONS_DIR}.")

    # 2. Read the currently loaded simulation state
    current_loaded_in_file = read_last_loaded_simulation_name()
    # Update the global variable *before* validation, filter_simulations needs it
    last_simulation_loaded = current_loaded_in_file

    # 3. Validate the loaded simulation state file (simulation_loaded.txt)
    if current_loaded_in_file and current_loaded_in_file not in actual_sim_names:
        print(f"Warning: Loaded simulation '{current_loaded_in_file}' in state file does not exist in {SIMULATIONS_DIR}.")
        state_file_path = None
        if isinstance(SIMULATION_LOADED_FILE, Path):
            state_file_path = SIMULATION_LOADED_FILE
        elif isinstance(SIMULATION_LOADED_FILE, str):
             try: state_file_path = Path(SIMULATION_LOADED_FILE)
             except Exception: pass

        if state_file_path and state_file_path.is_file():
            print(f"  Attempting to delete invalid state file: {state_file_path}")
            try:
                state_file_path.unlink()
                print("    Successfully deleted invalid state file.")
                last_simulation_loaded = None # Reset global variable as state is invalid
            except PermissionError:
                print("    Error: Permission denied deleting state file.")
            except Exception as e:
                print(f"    Error deleting state file: {e}")
        else:
            print(f"  State file not found or path invalid ({SIMULATION_LOADED_FILE}), cannot delete.")
            last_simulation_loaded = None # Reset global variable anyway if state is invalid

    # 4. Cleanup orphaned logger data folders
    # Run this *after* determining the valid simulation names
    cleanup_simulation_logger_data(actual_sim_names)

    # 5. Sort simulation data (optional, e.g., by name)
    all_simulations_data.sort(key=lambda x: x.get('name', '').lower())

    # 6. Refresh the Treeview using the filtered data
    filter_simulations() # This function populates the treeview

    # 7. Update Status Bar
    status_msg = f"List refreshed. Found {len(all_simulations_data)} total simulation(s)."
    # Use the potentially updated 'last_simulation_loaded' global var here
    if last_simulation_loaded:
         status_msg += f" ('{last_simulation_loaded}' is loaded)"
    if callable(globals().get('update_status')): update_status(status_msg)

    # 8. Update Button States
    if callable(globals().get('update_button_states')): update_button_states()

def filter_simulations(event=None):
    """Filters the simulations displayed in the treeview based on the search entry."""
    if 'sim_tree' not in globals() or 'search_entry' not in globals():
        # print("Warning: Treeview or search entry not ready for filtering.")
        return

    search_term = search_entry.get().lower().strip()

    # --- Clear existing items ---
    try:
        for item in sim_tree.get_children():
            sim_tree.delete(item)
    except tk.TclError as e:
        print(f"Warning: Error clearing treeview items: {e}")
        return # Avoid proceeding if clearing failed

    # --- Populate with filtered data ---
    displayed_count = 0
    for sim_data in all_simulations_data: # Iterate through the global list
        # Apply filter
        if search_term and search_term not in sim_data['name'].lower():
            continue # Skip if name doesn't match search term

        # Determine if this simulation is the currently loaded one
        is_loaded = (sim_data["name"] == last_simulation_loaded)

        # Assign alternating row tags for styling
        row_tag = "evenrow" if displayed_count % 2 == 0 else "oddrow"
        item_tags = [row_tag]
        if is_loaded:
            item_tags.append("loaded") # Add specific tag for loaded row styling

        # Prepare values for the row
        loaded_symbol = loaded_indicator_text if is_loaded else ""
        play_symbol = play_icon_text # Text for the play button column
        delete_symbol = delete_icon_text # Text for the delete button column

        try:
            sim_tree.insert("", "end", iid=sim_data["name"], # Use unique name as item ID
                            values=(
                                sim_data["name"],
                                sim_data["creation"],
                                sim_data["last_opened"],
                                loaded_symbol,
                                play_symbol,
                                delete_symbol
                            ),
                            tags=tuple(item_tags)) # Apply generated tags
            displayed_count += 1
        except tk.TclError as e:
            # This might happen if an invalid character is in the name and used as IID
            print(f"Error inserting simulation '{sim_data.get('name', 'N/A')}' into treeview: {e}")
            # Consider sanitizing sim_data["name"] if this becomes common

    # Update status bar based on filter results
    status_msg = status_label.cget("text") # Get current status to potentially append to
    if initial_verification_complete: # Only update count if verification is done
        if search_term:
            status_msg = f"Displaying {displayed_count} of {len(all_simulations_data)} simulation(s) matching '{search_term}'."
        else:
            status_msg = f"Displaying {len(all_simulations_data)} simulation(s)."
        if last_simulation_loaded:
             status_msg += f" ('{last_simulation_loaded}' is loaded)"
    update_status(status_msg)

    # Re-apply sorting if a column was previously sorted
    if 'last_sort_column' in globals() and last_sort_column:
        # Need to get the current sort order for that column
        current_reverse = sort_order.get(last_sort_column, False)
        sort_column(sim_tree, last_sort_column, current_reverse)

    update_button_states() # Update buttons based on selection state


def clear_search():
    """Clears the search entry and refreshes the simulation list."""
    if 'search_entry' in globals():
        search_entry.delete(0, 'end')
        filter_simulations() # Re-run filter to show all items


def update_button_states():
    """Updates the enabled/disabled state and appearance of buttons based on current context."""
    if 'main_window' not in globals() or not main_window or not main_window.winfo_exists() or is_build_running:
        # Don't update if GUI not ready, window closed, or build running (handled by disable/enable)
        return

    # Determine conditions
    has_selection = bool(sim_tree.selection()) # Is an item selected in the treeview?
    # Can create simulation if API key and primary model are verified
    can_create = apis_key_ok and apis_models_ok

    # Helper to get state string
    def get_state(enabled_condition):
        return "normal" if enabled_condition else "disabled"

    # Define state for each button/control
    # Sidebar buttons rely mostly on config verification
    settings_enabled = not is_build_running
    verify_enabled = not is_build_running
    unity_down_enabled = not is_build_running
    about_enabled = not is_build_running
    theme_switch_enabled = not is_build_running
    exit_enabled = not is_build_running

    # Main action buttons depend on config and selection
    reload_enabled = not is_build_running
    graph_enabled = has_selection and not is_build_running # Needs selection
    create_enabled = can_create and not is_build_running # Needs valid API config

    # Search controls
    search_enabled = not is_build_running

    # Get current color mode index
    mode_idx = get_color_mode_index()
    disabled_fg = COLOR_DISABLED_GENERAL[mode_idx]

    # Apply states and potentially disabled colors
    try:
        # Main Action Buttons
        if 'reload_btn' in globals(): reload_btn.configure(state=get_state(reload_enabled), fg_color=BTN_RELOAD_FG_COLOR[mode_idx] if reload_enabled else disabled_fg)
        if 'graph_btn' in globals(): graph_btn.configure(state=get_state(graph_enabled), fg_color=BTN_GRAPH_FG_COLOR[mode_idx] if graph_enabled else disabled_fg)
        if 'create_btn' in globals(): create_btn.configure(state=get_state(create_enabled), fg_color=BTN_CREATE_FG_COLOR[mode_idx] if create_enabled else disabled_fg)

        # Sidebar Buttons
        if 'settings_btn' in globals(): settings_btn.configure(state=get_state(settings_enabled), fg_color=BTN_SETTINGS_FG_COLOR[mode_idx] if settings_enabled else disabled_fg)
        if 'verify_btn' in globals(): verify_btn.configure(state=get_state(verify_enabled), fg_color=BTN_VERIFY_FG_COLOR[mode_idx] if verify_enabled else disabled_fg)
        if 'unity_down_btn' in globals(): unity_down_btn.configure(state=get_state(unity_down_enabled), fg_color=BTN_UNITY_DOWN_FG_COLOR[mode_idx] if unity_down_enabled else disabled_fg)
        if 'about_btn' in globals(): about_btn.configure(state=get_state(about_enabled), fg_color=BTN_ABOUT_FG_COLOR[mode_idx] if about_enabled else disabled_fg)
        if 'exit_btn' in globals(): exit_btn.configure(state=get_state(exit_enabled), fg_color=BTN_EXIT_FG_COLOR[mode_idx] if exit_enabled else disabled_fg)

        # Sidebar Switch
        if 'theme_switch' in globals(): theme_switch.configure(state=get_state(theme_switch_enabled))

        # Search Controls
        if 'search_entry' in globals(): search_entry.configure(state=get_state(search_enabled))
        if 'clear_search_btn' in globals(): clear_search_btn.configure(state=get_state(search_enabled), fg_color=BTN_CLEARSEARCH_FG_COLOR[mode_idx] if search_enabled else disabled_fg)

    except (NameError, tk.TclError) as e:
        # Catch errors if widgets don't exist yet or window is closing
        print(f"Warning: Could not update button states: {e}")


def on_load_simulation_request(simulation_name: str):
    """Handles the request to load/run a simulation (from treeview click)."""
    global is_build_running
    if is_build_running:
        print("Load request ignored: Build/Load already in progress.")
        return

    print(f"Load/Run request received for: {simulation_name}")

    # --- Pre-checks ---
    if not all([unity_path_ok, unity_version_ok, unity_projects_path_ok]):
        messagebox.showerror("Unity Configuration Error", "Cannot load simulation: Unity path, version, or projects path is invalid. Please check Settings.")
        return

    # --- Check if already loaded ---
    if simulation_name == last_simulation_loaded:
        update_status(f"'{simulation_name}' is already loaded. Showing options...")
        update_last_opened(simulation_name) # Update timestamp even if already loaded
        _, current_executable = get_build_target_and_executable(SIMULATION_PROJECT_PATH)
        # Show options window (Run, Open in Editor) in main thread
        if 'main_window' in globals() and main_window:
            main_window.after(0, lambda s=simulation_name, p=current_executable: show_options_window(s, p))
        return

    # --- Start Load Process in Thread ---
    # Disable UI immediately
    disable_all_interactions()
    update_status(f"Starting load process for '{simulation_name}'...")
    # Run the potentially long-running logic in a separate thread
    load_thread = threading.Thread(target=load_simulation_logic, args=(simulation_name,), daemon=True)
    load_thread.start()

def load_simulation_logic(simulation_name: str):
    """
    The core logic for loading a simulation, run in a thread.
    Includes closing Unity, copying files, running prefab tool, and starting build.
    """
    load_successful = False # Track overall success
    try:
        # 1. Ensure any existing Unity instance for the project is closed
        update_status(f"Load '{simulation_name}': Ensuring Unity is closed...");
        ensure_unity_closed() # Terminates matching Unity processes

        # 2. Copy simulation files
        update_status(f"Load '{simulation_name}': Copying simulation files...");
        copy_ok = load_simulation(simulation_name) # This function handles UI updates/errors

        if copy_ok:
            # 3. Run prefab/material tool (after files are copied)
            update_status(f"Load '{simulation_name}': Running prefab/material tool...");
            prefab_ok = run_prefab_material_tool() # This handles its own status/errors

            if prefab_ok:
                # 4. Start the build process (threaded)
                update_status(f"Load '{simulation_name}': Starting simulation build...");
                # The build_simulation_threaded function starts another thread
                # We pass build_callback to handle the result of the build
                build_simulation_threaded(callback=lambda ok, path: build_callback(ok, simulation_name, path))
                # Note: Interactions remain disabled until the build finishes (handled by build_callback/build_simulation_task)
                load_successful = True # Loading part succeeded, build is running
            else:
                # Prefab tool failed
                update_status(f"Error in post-load (prefab tool) for '{simulation_name}'. Build cancelled.")
                messagebox.showerror("Post-Load Error", f"The prefab/material creation tool failed for '{simulation_name}'.\nThe simulation build has been cancelled. Check console/logs.")
                # Need to re-enable interactions here if prefab tool fails
                if 'main_window' in globals() and main_window: main_window.after(10, enable_all_interactions)
        else:
            # File copy failed
            update_status(f"Error loading files for '{simulation_name}'. Load process stopped.");
            # Re-enable interactions as load failed early
            if 'main_window' in globals() and main_window: main_window.after(10, enable_all_interactions)

    except Exception as e:
        # Catch unexpected errors in the loading sequence itself
        print(f"CRITICAL ERROR in load_simulation_logic for '{simulation_name}': {e}")
        import traceback
        traceback.print_exc()
        update_status(f"Critical error during load sequence for '{simulation_name}'. Check console.")
        # Ensure interactions are re-enabled on critical failure
        if 'main_window' in globals() and main_window: main_window.after(10, enable_all_interactions)

    # Note: enable_all_interactions is called by the build task upon completion/failure if it gets that far.

def build_callback(success: bool, simulation_name: str, executable_path: Union[str, None]):
    """Callback executed after the build attempt finishes."""
    if success:
        if executable_path and Path(executable_path).exists():
            update_status(f"Build for '{simulation_name}' completed successfully.")
            print(f"Build successful for '{simulation_name}'. Executable at: {executable_path}")
            # Show options window (Run, Open in Editor)
            show_options_window(simulation_name, executable_path)
        elif executable_path: # Build succeeded but file missing
             update_status(f"Build '{simulation_name}' finished, but executable not found: {executable_path}")
             print(f"Error: Build process reported success, but executable missing at: {executable_path}")
             messagebox.showerror("Build Error", f"Build for '{simulation_name}' completed, but the executable was not found at the expected location:\n{executable_path}\n\nPlease check the build log.")
        else: # Build succeeded but path couldn't be determined
            update_status(f"Build '{simulation_name}' finished, but executable path unknown.")
            print(f"Error: Build process reported success, but could not determine executable path.")
            messagebox.showerror("Build Error", f"Build for '{simulation_name}' completed, but the executable path could not be determined.")
    else:
        # Build process itself failed (error during Unity execution)
        # Specific error message should have been shown by run_unity_batchmode/handle_unity_execution_error
        update_status(f"Build process for '{simulation_name}' failed. Check logs/console.")
        print(f"Build failed for '{simulation_name}'.")
        # Optionally show a generic failure message here, but might be redundant
        # messagebox.showerror("Build Failed", f"The build process for '{simulation_name}' failed. Please check the console output and build log for details.")

    # Interactions are re-enabled by build_simulation_task's finally block

def on_delete_simulation_request(simulation_name: str):
    """Handles the request to delete a simulation (from treeview click)."""
    global is_build_running
    if is_build_running:
        print("Delete request ignored: Build/Load in progress.")
        return

    print(f"Delete request received for: {simulation_name}")
    # Call the main deletion logic (which includes confirmation)
    delete_simulation(simulation_name)
    # delete_simulation handles its own status updates and UI refresh


def on_show_graphs_thread():
    """Initiates graph generation in a separate thread."""
    global is_build_running
    if is_build_running:
        print("Show Graphs request ignored: Build/Load in progress.")
        return

    # Get selected simulation
    selected_items = sim_tree.selection()
    if not selected_items:
        messagebox.showwarning("No Selection", "Please select a simulation from the list to view its statistics.")
        return

    sim_name = sim_tree.item(selected_items[0], "values")[0] # Get name from first column

    # Disable UI and start thread
    disable_all_interactions()
    update_status(f"Generating statistics graphs for '{sim_name}'...")
    graph_thread = threading.Thread(target=show_graphs_logic, args=(sim_name,), daemon=True)
    graph_thread.start()

def show_graphs_logic(sim_name: str):
    """
    Generates and attempts to open the graphs folder for the given simulation.
    Handles locating data dynamically. Run in a thread.
    """
    # Ensure necessary functions are available
    if not callable(globals().get('find_simulation_data_path')) or \
       not callable(globals().get('SimulationGraphics')) or \
       not callable(globals().get('open_graphs_folder')):
        messagebox.showerror("Internal Error", "Required graph generation functions (find_simulation_data_path, SimulationGraphics, open_graphs_folder) are not defined.")
        # Re-enable UI before returning
        if 'main_window' in globals() and main_window: main_window.after(0, enable_all_interactions)
        return

    try:
        if callable(globals().get('update_status')): update_status(f"Locating data for '{sim_name}'...")
        print(f"--- Starting graph logic for: '{sim_name}' ---")

        # 1. Find the Unity data path using the helper function
        simulation_data_dir = find_simulation_data_path(sim_name)

        if not simulation_data_dir:
            # Error message already shown by find_simulation_data_path or messagebox in open_graphs_folder
            # Just update status here
            if callable(globals().get('update_status')): update_status(f"Error: Data directory not found for '{sim_name}'.")
            return # Exit thread

        print(f"  Data directory found: {simulation_data_dir}")
        # Construct expected paths within the data directory
        csv_path = simulation_data_dir / CSV_FILENAME
        graphs_dir = simulation_data_dir / GRAPHICS_SUBFOLDER # Needed for open_graphs_folder

        # 2. Check if the CSV file exists (necessary for graph generation)
        if not csv_path.is_file():
            messagebox.showerror("Missing Data",
                                 f"The required statistics file ('{CSV_FILENAME}') for simulation '{sim_name}' was not found in:\n{simulation_data_dir}\n\nCannot generate graphs.")
            if callable(globals().get('update_status')): update_status(f"Error: Statistics CSV file missing for '{sim_name}'.")
            return # Exit thread

        # 3. Call SimulationGraphics (which now also uses find_simulation_data_path)
        if callable(globals().get('update_status')): update_status(f"Generating graphs for '{sim_name}'...")
        print(f"  Calling SimulationGraphics for '{sim_name}'...")
        # --- Execute graph generation ---
        SimulationGraphics(sim_name)
        # -------------------------------
        # SimulationGraphics handles its own internal errors/messages/logging

        # 4. If SimulationGraphics didn't abort, try opening the folder
        if callable(globals().get('update_status')): update_status(f"Graph generation attempted. Opening graphs folder for '{sim_name}'...")
        print(f"  Calling open_graphs_folder for '{sim_name}'...")
        open_graphs_folder(sim_name) # This uses the same logic to find the folder

        if callable(globals().get('update_status')): update_status(f"Graph process completed for '{sim_name}'.")

    except FileNotFoundError as e:
        # Less likely now, but could occur for other reasons
        messagebox.showerror("File Error", f"A required file was not found during the graph process:\n{e}")
        if callable(globals().get('update_status')): update_status(f"Error: File not found while processing '{sim_name}'.")
        print(f"show_graphs_logic - FileNotFoundError: {e}")
        traceback.print_exc()
    except Exception as e:
        # Catch any other unexpected errors during the logic
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred while processing graphs for '{sim_name}':\n{type(e).__name__}: {e}")
        if callable(globals().get('update_status')): update_status(f"Error processing graphs for '{sim_name}'. Check console.")
        print(f"show_graphs_logic - Unexpected Exception: {e}")
        traceback.print_exc()
    finally:
        # --- Re-enable UI Interactions ---
        # Always run this, ensuring UI becomes responsive again
        try:
            if 'main_window' in globals() and main_window is not None and main_window.winfo_exists():
                 # Use after(0, ...) to ensure execution in the main Tkinter thread
                 main_window.after(0, enable_all_interactions)
            elif callable(globals().get('enable_all_interactions')):
                 enable_all_interactions()() # Call directly if no main_window.after context
        except NameError:
            print("Warning: 'main_window' or 'enable_all_interactions' not defined globally for UI re-enabling.")
        except Exception as e:
            print(f"Error in finally block attempting to re-enable UI: {e}")

def on_create_simulation():
    """Handles the 'Create Sim (API)' button click."""
    global is_build_running
    if is_build_running:
        print("Create request ignored: Build/Load in progress.")
        return

    # Check API configuration first
    if not apis_key_ok or not apis_models_ok:
        messagebox.showerror("API Configuration Error", "Cannot create simulation: Invalid or unverified OpenAI API Key or Primary Model ID.\nPlease check Settings and Verify Config.")
        return

    # 1. Get Simulation Name
    sim_name = custom_askstring("Create New Simulation", "Enter a unique name for the new simulation:")
    if sim_name is None: # User cancelled
        update_status("Simulation creation cancelled.")
        return
    sim_name = sim_name.strip()

    # Validate name (basic check for empty and invalid characters)
    invalid_chars = r'<>:"/\|?*' + "".join(map(chr, range(32))) # Control chars + Windows forbidden
    if not sim_name:
         messagebox.showerror("Invalid Name", "Simulation name cannot be empty.")
         update_status("Invalid simulation name (empty).")
         return
    if any(c in invalid_chars for c in sim_name):
        messagebox.showerror("Invalid Name", f"Simulation name '{sim_name}' contains invalid characters ({invalid_chars}).")
        update_status("Invalid simulation name (characters).")
        return
    # Check for existing simulation with the same name
    if (SIMULATIONS_DIR / sim_name).exists():
        messagebox.showerror("Name Exists", f"A simulation named '{sim_name}' already exists. Please choose a different name.")
        update_status(f"Simulation '{sim_name}' already exists.")
        return

    # 2. Get Simulation Description
    sim_desc = custom_askstring("Simulation Description", "Provide a brief description for the simulation (e.g., 'EColi red fast, SCerevisiae blue slow'):")
    if sim_desc is None: # User cancelled
        update_status("Simulation creation cancelled.")
        return
    sim_desc = sim_desc.strip()
    if not sim_desc:
         # Optional: Allow empty description or prompt again
         if not messagebox.askyesno("Empty Description", "The description is empty. Continue anyway?", icon='question'):
              update_status("Simulation creation cancelled.")
              return
         # Keep sim_desc as "" if user confirms

    # 3. Start Creation Thread
    disable_all_interactions()
    update_status(f"Initiating creation of '{sim_name}' via API...")
    # Run the creation logic (including API calls and file import) in a thread
    creation_thread = threading.Thread(target=create_simulation_thread, args=(sim_name, sim_desc), daemon=True)
    creation_thread.start()


def show_options_window(simulation_name: str, executable_path: Union[str, None]):
    """Displays a modal window with options for a loaded simulation (Run, Open in Editor)."""
    if 'main_window' not in globals() or not main_window: return

    options_win = ctk.CTkToplevel(main_window)
    options_win.title(f"Options for '{simulation_name}'")
    apply_icon(options_win)
    center_window(options_win, 380, 200) # Width, Height
    options_win.resizable(False, False)
    options_win.transient(main_window)
    options_win.grab_set() # Make modal

    frame = ctk.CTkFrame(options_win)
    frame.pack(expand=True, fill="both", padx=20, pady=20)

    ctk.CTkLabel(frame, text=f"Simulation '{simulation_name}' is loaded and built.", font=APP_FONT_BOLD).pack(pady=(0, 15))

    # Check if executable exists
    executable_exists = executable_path and Path(executable_path).exists()
    run_button_state = "normal" if executable_exists else "disabled"

    # Actions for buttons
    def run_and_close():
        open_simulation_executable() # Attempts to launch the built sim
        options_win.destroy()

    def open_unity_and_close():
        open_in_unity() # Opens the project in the editor
        options_win.destroy()

    mode_idx = get_color_mode_index()

    # Run Button
    run_button = ctk.CTkButton(frame, text="Run Simulation", command=run_and_close, state=run_button_state, font=APP_FONT, height=40,
                               fg_color=COLOR_SUCCESS_GENERAL[mode_idx] if executable_exists else COLOR_DISABLED_GENERAL[mode_idx],
                               hover_color=COLOR_INFO_GENERAL[mode_idx] if executable_exists else COLOR_DISABLED_GENERAL[mode_idx])
    run_button.pack(pady=8, fill="x", padx=10)

    # Show message if executable not found
    if not executable_exists:
        reason = f"Executable not found at:\n{executable_path}" if executable_path else "Executable path is unknown."
        ctk.CTkLabel(frame, text=reason, text_color="gray", font=("Segoe UI", 9)).pack(pady=(0, 5))

    # Open in Editor Button
    open_editor_button = ctk.CTkButton(frame, text="Open Project in Unity Editor", command=open_unity_and_close, font=APP_FONT, height=40,
                                     fg_color="#1E88E5", hover_color="#42A5F5") # Consistent blue color
    open_editor_button.pack(pady=8, fill="x", padx=10)

    update_status(f"Options available for loaded simulation '{simulation_name}'.")
    options_win.wait_window() # Wait for this window to close

def handle_tree_click(event):
    """Handles clicks within the Treeview, triggering actions like Load or Delete."""
    global is_build_running
    if is_build_running: return # Ignore clicks during operations

    region = sim_tree.identify_region(event.x, event.y)
    item_id = sim_tree.identify_row(event.y) # Get the item clicked on

    if region == "cell" and item_id: # Click was on a cell in a specific row
        column_id_str = sim_tree.identify_column(event.x) # e.g., "#5"

        if not column_id_str:
            cancel_tooltip(sim_tree)
            return

        try:
            # Convert column ID string to index and get column name
            column_index = int(column_id_str.replace('#','')) - 1 # "#1" -> 0, "#2" -> 1, etc.
            column_ids_tuple = sim_tree['columns'] # ('nombre', 'creacion', ...)

            if 0 <= column_index < len(column_ids_tuple):
                column_name = column_ids_tuple[column_index] # Get the internal column name
                simulation_name = sim_tree.item(item_id, "values")[0] # Get sim name from first column

                # Select the clicked row visually
                sim_tree.selection_set(item_id)
                sim_tree.focus(item_id)
                update_button_states() # Update main buttons based on selection
                hide_tooltip() # Hide tooltip immediately on click

                # Perform action based on the clicked column
                if column_name == "col_load": # Check against internal column names
                    print(f"Action Click: Load/Run '{simulation_name}'")
                    on_load_simulation_request(simulation_name)
                elif column_name == "col_delete":
                    print(f"Action Click: Delete '{simulation_name}'")
                    on_delete_simulation_request(simulation_name)
                # else: Click on other columns just selects the row (handled above)

            else: cancel_tooltip(sim_tree) # Clicked outside defined columns?
        except (ValueError, IndexError, tk.TclError) as e:
            print(f"Error processing Treeview click: {e}")
            cancel_tooltip(sim_tree)
    elif region == "heading":
        # Clicked on a header (handled by sort_column binding)
        pass
    else:
        # Clicked outside cells or headings (e.g., empty space)
        cancel_tooltip(sim_tree)

def handle_tree_motion(event):
    """Shows tooltips when hovering over specific 'button' columns in the Treeview."""
    global is_build_running
    if is_build_running: return # No tooltips during operations

    region = sim_tree.identify_region(event.x, event.y)
    item_id = sim_tree.identify_row(event.y)

    if region == "cell" and item_id: # Hovering over a cell
        column_id_str = sim_tree.identify_column(event.x)
        if not column_id_str: cancel_tooltip(sim_tree); return

        try:
            column_index = int(column_id_str.replace('#','')) - 1
            column_ids_tuple = sim_tree['columns']

            if 0 <= column_index < len(column_ids_tuple):
                column_name = column_ids_tuple[column_index]
                tooltip_text = None
                simulation_name = sim_tree.item(item_id, 'values')[0]

                # Define tooltips for specific columns
                if column_name == "col_load":
                    tooltip_text = f"Load / Run Simulation '{simulation_name}'"
                elif column_name == "col_delete":
                    tooltip_text = f"Delete Simulation '{simulation_name}'"
                elif column_name == "col_loaded":
                    # Show tooltip only if the loaded indicator is present
                    cell_value = sim_tree.set(item_id, column=column_name)
                    if cell_value == loaded_indicator_text:
                        tooltip_text = f"Simulation '{simulation_name}' is currently loaded in the Unity project."

                # Schedule or cancel tooltip
                if tooltip_text:
                    schedule_tooltip(sim_tree, tooltip_text)
                else:
                    cancel_tooltip(sim_tree) # Cancel if not over an actionable column
            else: cancel_tooltip(sim_tree) # Outside defined columns
        except (ValueError, IndexError, tk.TclError) as e:
            # print(f"Error during handle_tree_motion: {e}") # Can be noisy
            cancel_tooltip(sim_tree)
    else:
        # Mouse moved out of cells (e.g., to heading, empty space, or outside treeview)
        cancel_tooltip(sim_tree)


def handle_tree_leave(event):
    """Hides the tooltip when the mouse leaves the Treeview widget."""
    cancel_tooltip(sim_tree)

def load_logo(image_path: str, target_width: int) -> Union[ImageTk.PhotoImage, None]:
    """Loads and resizes a logo image, returning a PhotoImage object."""
    global logo_photo_ref # Keep a reference to prevent garbage collection
    try:
        img = Image.open(image_path)
        # Calculate new height maintaining aspect ratio
        width_percent = (target_width / float(img.size[0]))
        new_height = int((float(img.size[1]) * float(width_percent)))
        # Resize using high-quality downsampling filter
        img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
        logo_photo_ref = ImageTk.PhotoImage(img)
        return logo_photo_ref
    except FileNotFoundError:
        print(f"Warning: Logo image not found at '{image_path}'")
        return None
    except Exception as e:
        print(f"Error loading or processing logo image '{image_path}': {e}")
        return None

def update_treeview_style():
    """Applies appropriate styling to the ttk.Treeview based on the current CTk theme."""
    if 'sim_tree' not in globals() or 'main_window' not in globals() or not main_window.winfo_exists():
        # print("Cannot update Treeview style: widgets not ready.")
        return

    mode_idx = get_color_mode_index()
    mode_str = "Dark" if mode_idx == 1 else "Light"
    # print(f"Updating Treeview style for {mode_str} mode...")

    try:
        # Get theme colors dynamically from CustomTkinter (more robust)
        bg_color = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        fg_color = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        select_bg_color = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        select_fg_color = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["text_color"]) # Use button text color for selected row text
        # Use slightly different bg for header for contrast
        header_bg_color = main_window._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["border_color"]) # Or another subtle color
        header_fg_color = fg_color # Use standard text color for header

        # Define row colors (adjust as needed)
        odd_row_bg = main_window._apply_appearance_mode(("#FFFFFF", "#3A3A3A")) # White / Dark Gray
        even_row_bg = main_window._apply_appearance_mode(("#F5F5F5", "#343434")) # Off-white / Slightly lighter Dark Gray
        # Loaded row colors (e.g., subtle green tint)
        loaded_row_bg = main_window._apply_appearance_mode(("#E8F5E9", "#2E7D32")) # Light Green / Dark Green (adjust!)
        loaded_row_fg = fg_color # Use default text color for loaded row

    except Exception as e:
        print(f"Error getting theme colors for Treeview: {e}. Using fallback colors.")
        # Fallback colors (hardcoded)
        if mode_str == "Dark":
            bg_color, fg_color = "#2B2B2B", "white"
            select_bg_color, select_fg_color = "#565B5E", "white"
            header_bg_color, header_fg_color = "#4A4D50", "white"
            odd_row_bg, even_row_bg = "#3A3A3A", "#343434"
            loaded_row_bg, loaded_row_fg = "#2E7D32", "white"
        else: # Light Mode Fallback
            bg_color, fg_color = "#FFFFFF", "black"
            select_bg_color, select_fg_color = "#DDF0FF", "black" # Light blue selection
            header_bg_color, header_fg_color = "#EAEAEA", "black" # Light gray header
            odd_row_bg, even_row_bg = "#FFFFFF", "#F5F5F5"
            loaded_row_bg, loaded_row_fg = "#E8F5E9", "black" # Light green

    # --- Apply Styles ---
    style = ttk.Style()
    try:
        style.theme_use("clam") # 'clam' often looks better with custom colors
    except tk.TclError:
        print("Warning: ttk theme 'clam' not available. Using default theme.")
        # Styles might not apply as expected with the default theme

    # Configure base Treeview style
    style.configure("Treeview",
                    background=bg_color,
                    foreground=fg_color,
                    fieldbackground=bg_color, # Background of the area behind cells
                    rowheight=28, # Adjust row height if needed
                    font=TREEVIEW_FONT)

    # Configure Heading style
    style.configure("Treeview.Heading",
                    font=TREEVIEW_HEADER_FONT,
                    background=header_bg_color,
                    foreground=header_fg_color,
                    relief="flat", # Flat look
                    padding=(10, 5)) # Padding (horizontal, vertical)
    # Change relief on hover/click
    style.map("Treeview.Heading",
              relief=[('active', 'groove'), ('!active', 'flat')])

    # Configure selected row appearance
    style.map('Treeview',
              background=[('selected', select_bg_color)],
              foreground=[('selected', select_fg_color)])

    # Configure tags for row styling (use the colors defined above)
    # Need to re-apply tag configure every time style changes
    sim_tree.tag_configure('oddrow', background=odd_row_bg, foreground=fg_color)
    sim_tree.tag_configure('evenrow', background=even_row_bg, foreground=fg_color)
    sim_tree.tag_configure('loaded', background=loaded_row_bg, foreground=loaded_row_fg) # Apply loaded style

    # Force redraw (might be needed sometimes, but often handled by Tkinter)
    # sim_tree.update_idletasks()
    # print("Treeview style updated.")

def toggle_appearance_mode():
    """Switches the CustomTkinter appearance mode and updates relevant styles."""
    current_mode = ctk.get_appearance_mode()
    new_mode = "Dark" if current_mode == "Light" else "Light"
    print(f"Switching appearance mode to: {new_mode}")
    ctk.set_appearance_mode(new_mode)

    # Update the switch text
    if 'theme_switch' in globals() and theme_switch:
        theme_switch.configure(text=f"{new_mode} Mode")

    # Schedule Treeview style update (needs to happen after theme change)
    if 'main_window' in globals() and main_window:
         main_window.after(50, update_treeview_style) # Small delay

    # Update CustomTkinter Button Colors based on the new mode
    mode_idx = get_color_mode_index()
    try:
        # Update Logo
        logo_path = LOGO_PATHS[mode_idx]
        new_logo_photo = load_logo(logo_path, LOGO_WIDTH)
        if new_logo_photo and 'sidebar_frame' in globals() and sidebar_frame.winfo_exists():
             # Find the logo label widget (assuming it's the first label)
             logo_widget = None
             for w in sidebar_frame.winfo_children():
                  if isinstance(w, ctk.CTkLabel) and hasattr(w, 'image'): # Find the label with an image
                       logo_widget = w
                       break
             if logo_widget:
                 logo_widget.configure(image=new_logo_photo)
                 logo_widget.image = new_logo_photo # Keep reference

        # Update Sidebar Buttons
        if 'settings_btn' in globals(): settings_btn.configure(fg_color=BTN_SETTINGS_FG_COLOR[mode_idx], hover_color=BTN_SETTINGS_HOVER_COLOR[mode_idx], text_color=BTN_SETTINGS_TEXT_COLOR[mode_idx])
        if 'verify_btn' in globals(): verify_btn.configure(fg_color=BTN_VERIFY_FG_COLOR[mode_idx], hover_color=BTN_VERIFY_HOVER_COLOR[mode_idx], text_color=BTN_VERIFY_TEXT_COLOR[mode_idx])
        if 'unity_down_btn' in globals(): unity_down_btn.configure(fg_color=BTN_UNITY_DOWN_FG_COLOR[mode_idx], hover_color=BTN_UNITY_DOWN_HOVER_COLOR[mode_idx], text_color=BTN_UNITY_DOWN_TEXT_COLOR[mode_idx])
        if 'about_btn' in globals(): about_btn.configure(fg_color=BTN_ABOUT_FG_COLOR[mode_idx], hover_color=BTN_ABOUT_HOVER_COLOR[mode_idx], text_color=BTN_ABOUT_TEXT_COLOR[mode_idx])
        if 'exit_btn' in globals(): exit_btn.configure(fg_color=BTN_EXIT_FG_COLOR[mode_idx], hover_color=BTN_EXIT_HOVER_COLOR[mode_idx], text_color=BTN_EXIT_TEXT_COLOR[mode_idx])

        # Update Bottom Buttons
        if 'reload_btn' in globals(): reload_btn.configure(fg_color=BTN_RELOAD_FG_COLOR[mode_idx], hover_color=BTN_RELOAD_HOVER_COLOR[mode_idx], text_color=BTN_RELOAD_TEXT_COLOR[mode_idx])
        if 'graph_btn' in globals(): graph_btn.configure(fg_color=BTN_GRAPH_FG_COLOR[mode_idx], hover_color=BTN_GRAPH_HOVER_COLOR[mode_idx], text_color=BTN_GRAPH_TEXT_COLOR[mode_idx])
        if 'create_btn' in globals(): create_btn.configure(fg_color=BTN_CREATE_FG_COLOR[mode_idx], hover_color=BTN_CREATE_HOVER_COLOR[mode_idx], text_color=BTN_CREATE_TEXT_COLOR[mode_idx])

        # Update Search Button
        if 'clear_search_btn' in globals(): clear_search_btn.configure(fg_color=BTN_CLEARSEARCH_FG_COLOR[mode_idx], hover_color=BTN_CLEARSEARCH_HOVER_COLOR[mode_idx], text_color=BTN_CLEARSEARCH_TEXT_COLOR[mode_idx])

        # Update disabled button colors (important after theme change)
        update_button_states() # This function now handles disabled colors too

        print("Widget colors updated for new theme.")
    except NameError as e:
        print(f"Warning: Button color update failed (widget might not exist yet): {e}")
    except Exception as e:
        print(f"Error updating widget colors for theme: {e}")


# ======================================================
# GUI Setup
# ======================================================
main_window = ctk.CTk()
apply_icon(main_window)
main_window.title("Unity Simulation Manager v1.0")
initial_width=1050
initial_height=700
center_window(main_window, initial_width, initial_height)
main_window.resizable(True, True)
main_window.minsize(850, 550) # Minimum size to keep layout reasonable

# --- Main Layout ---
# Sidebar (column 0, fixed width), Main Content (column 1, expands)
# Content Area (row 0, expands), Status Bar (row 1, fixed height)
main_window.columnconfigure(0, weight=0)
main_window.columnconfigure(1, weight=1)
main_window.rowconfigure(0, weight=1)
main_window.rowconfigure(1, weight=0)

# --- Sidebar ---
sidebar_width=200
sidebar_frame = ctk.CTkFrame(main_window, width=sidebar_width, corner_radius=5, fg_color=COLOR_SIDEBAR_BG)
sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
sidebar_frame.grid_propagate(False) # Prevent resizing based on content
sidebar_frame.columnconfigure(0, weight=1) # Allow buttons to fill horizontally

# Initial mode for logo and button colors
initial_mode = ctk.get_appearance_mode()
mode_idx = get_color_mode_index()

# Logo
logo_path = LOGO_PATHS[mode_idx]
logo_photo = load_logo(logo_path, LOGO_WIDTH - 20) # Leave some padding
if logo_photo:
    logo_label = ctk.CTkLabel(sidebar_frame, image=logo_photo, text="")
    logo_label.pack(pady=(20, 10), padx=10)
    logo_label.image = logo_photo # Keep reference
else:
    ctk.CTkLabel(sidebar_frame, text="[Logo]", font=(APP_FONT[0], 14, "italic")).pack(pady=(20, 10), padx=10)

# Menu Label
ctk.CTkLabel(sidebar_frame, text="Menu", font=(APP_FONT[0], 16, "bold")).pack(pady=(5, 15), padx=10)

# Sidebar Buttons
settings_btn = ctk.CTkButton(sidebar_frame, text="Settings (.env)", command=open_config_window, font=APP_FONT,
                             fg_color=BTN_SETTINGS_FG_COLOR[mode_idx], hover_color=BTN_SETTINGS_HOVER_COLOR[mode_idx], text_color=BTN_SETTINGS_TEXT_COLOR[mode_idx])
settings_btn.pack(fill="x", padx=15, pady=5)

verify_btn = ctk.CTkButton(sidebar_frame, text="Verify Config", command=lambda: perform_verification(show_results_box=True), font=APP_FONT,
                           fg_color=BTN_VERIFY_FG_COLOR[mode_idx], hover_color=BTN_VERIFY_HOVER_COLOR[mode_idx], text_color=BTN_VERIFY_TEXT_COLOR[mode_idx])
verify_btn.pack(fill="x", padx=15, pady=5)

# Separator
separator = ctk.CTkFrame(sidebar_frame, height=2, fg_color="gray")
separator.pack(fill="x", padx=15, pady=15)

# --- Unity Hub Info Dialog ---
class UnityHubInfoDialog(ctk.CTkToplevel):
    """Modal dialog to show Unity Hub installation instructions and links."""
    def __init__(self, parent, title, message_text, download_url):
        super().__init__(parent)
        self.title(title)
        apply_icon(self)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set() # Make modal

        self._message = message_text
        self._download_url = download_url

        # --- Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1) # Message label expands
        self.grid_rowconfigure(1, weight=0) # Link section
        self.grid_rowconfigure(2, weight=0) # Button frame

        # Message Label
        self.message_label = ctk.CTkLabel(self, text=self._message, font=APP_FONT, justify="left", wraplength=400)
        self.message_label.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 15), sticky="w")

        # Link Section Frame
        link_frame = ctk.CTkFrame(self, fg_color="transparent")
        link_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
        link_frame.grid_columnconfigure(1, weight=1) # Entry expands

        ctk.CTkLabel(link_frame, text="Download Link:", font=APP_FONT_BOLD).grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.link_entry = ctk.CTkEntry(link_frame, font=APP_FONT)
        self.link_entry.insert(0, self._download_url)
        self.link_entry.configure(state="readonly") # Make read-only
        self.link_entry.grid(row=0, column=1, sticky="ew")

        # Button Frame (Right-aligned)
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="e")

        mode_idx = get_color_mode_index()

        # Copy Button
        self.copy_button = ctk.CTkButton(button_frame, text="Copy Link", command=self.copy_link, width=100, font=APP_FONT,
                                         fg_color=BTN_RELOAD_FG_COLOR[mode_idx], hover_color=BTN_RELOAD_HOVER_COLOR[mode_idx]) # Blue
        self.copy_button.pack(side="left", padx=(0, 10))

        # Open Button
        open_button = ctk.CTkButton(button_frame, text="Open Page", command=self.open_download_page, width=100, font=APP_FONT,
                                       fg_color=BTN_GRAPH_FG_COLOR[mode_idx], hover_color=BTN_GRAPH_HOVER_COLOR[mode_idx]) # Purple
        open_button.pack(side="left", padx=(0, 10))

        # Close Button
        close_button = ctk.CTkButton(button_frame, text="Close", command=self.destroy, width=80, font=APP_FONT,
                                      fg_color=COLOR_WARNING_GENERAL[mode_idx], hover_color=COLOR_DANGER_GENERAL[mode_idx]) # Red/Orange
        close_button.pack(side="left")

        # Center window after content is packed
        self.update_idletasks()
        width = max(450, self.winfo_reqwidth()) # Ensure minimum width
        height = self.winfo_reqheight()
        center_window(self, width, height)

        # Bind Escape key to close
        self.bind("<Escape>", lambda e: self.destroy())
        # Set focus slightly after window appears
        self.after(100, self.link_entry.focus)
        self.wait_window() # Wait until destroyed

    def copy_link(self):
        """Copies the download URL to the clipboard."""
        try:
            self.clipboard_clear()
            self.clipboard_append(self._download_url)
            print(f"Copied to clipboard: {self._download_url}")
            # Provide feedback
            original_text = self.copy_button.cget("text")
            self.copy_button.configure(text="Copied!", state="disabled")
            # Reset button after a delay
            self.after(1500, lambda: self.copy_button.configure(text=original_text, state="normal"))
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            messagebox.showerror("Clipboard Error", f"Could not copy link to clipboard:\n{e}", parent=self)

    def open_download_page(self):
        """Opens the download URL in the default web browser."""
        try:
            webbrowser.open(self._download_url)
            self.destroy() # Close dialog after opening link
        except Exception as e:
            print(f"Error opening URL in browser: {e}")
            messagebox.showerror("Browser Error", f"Could not open the download page in your browser:\n{e}", parent=self)

# --- Unity Download Button Logic ---
def handle_unity_download_click():
    """Handles the click for the 'Download Unity Editor' button."""
    if not 'UNITY_REQUIRED_VERSION_STRING' in globals() or not UNITY_REQUIRED_VERSION_STRING:
        print("Error: UNITY_REQUIRED_VERSION_STRING constant is not defined.")
        if 'main_window' in globals() and main_window and main_window.winfo_exists():
             messagebox.showerror("Internal Error", "The required Unity version is not configured internally.", parent=main_window)
        return

    # Construct the Unity Hub deep link URI
    # The specific hash might be version-dependent, find from Unity download archive/Hub logs if needed
    unity_version_hash = "b2e806cf271c" # Example hash for 6000.0.3f1 - VERIFY THIS
    unity_hub_uri = f"unityhub://{UNITY_REQUIRED_VERSION_STRING}/{unity_version_hash}"

    # Determine OS, download link, and specific build module required
    system_os = platform.system()
    build_support_module_text = ""
    hub_download_link = ""
    os_name = system_os

    if system_os == "Windows":
        hub_download_link = "https://public-cdn.cloud.unity3d.com/hub/prod/UnityHubSetup.exe"
        os_name = "Windows"
        build_support_module_text = "- Windows Build Support (IL2CPP)" # Common requirement
    elif system_os == "Darwin": # macOS
        hub_download_link = "https://public-cdn.cloud.unity3d.com/hub/prod/UnityHubSetup.dmg"
        os_name = "macOS"
        build_support_module_text = "- Mac Build Support (Mono or IL2CPP - check project needs)" # Mono often default
    else: # Linux / Other
        hub_download_link = "https://unity.com/download" # General download page
        build_support_module_text = f"- {os_name} Build Support (check specific requirements)"

    # Detailed instructions for the dialog
    instructions = (
        "To install the correct Unity Editor version using this tool:\n\n"
        "1. Install Unity Hub using the link below if you haven't already.\n"
        "   (Close the Hub after installation if it opens automatically).\n\n"
        "2. Close this message, then click the 'Download Unity Editor' button in this application again.\n"
        f"   This should prompt Unity Hub to open and start installing the required Editor version ({UNITY_REQUIRED_VERSION_STRING}).\n\n"
        "3. In the Unity Hub installation options, carefully review the modules to add. Ensure the following are selected:\n"
        "   - Microsoft Visual Studio Community (or your preferred IDE)\n"
        f"   {build_support_module_text}\n\n" # Add platform-specific module
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

    # Try opening the Unity Hub link first
    try:
        print(f"Attempting to open Unity Hub link: {unity_hub_uri}")
        opened = webbrowser.open(unity_hub_uri)
        if not opened:
            print("Warning: webbrowser.open returned False. System might not have handler for unityhub://")
            # Consider showing a small note that it might not have worked immediately
    except Exception as e:
        print(f"Error attempting to open unityhub:// link: {e}")
        # Don't prevent the dialog from showing, but maybe add a note
        # full_message_text = f"(Note: Failed to automatically open Unity Hub link: {e})\n\n" + full_message_text

    # Show the instructional dialog regardless of link opening success
    if 'main_window' in globals() and main_window and main_window.winfo_exists():
        dialog = UnityHubInfoDialog(
            parent=main_window,
            title="Download Unity Editor / Hub Instructions",
            message_text=full_message_text,
            download_url=hub_download_link # Provide direct Hub download link
        )
    else:
        # Fallback if GUI not available
        print("INFO (Unity Download Instructions - No GUI):")
        print(full_message_text)
        print(f"Unity Hub Download Link ({os_name}): {hub_download_link}")


# Continue Sidebar Buttons
unity_down_btn = ctk.CTkButton(sidebar_frame, text="Download Unity Editor",
                              command=handle_unity_download_click, # Calls the logic above
                              font=APP_FONT,
                              fg_color=BTN_UNITY_DOWN_FG_COLOR[mode_idx], hover_color=BTN_UNITY_DOWN_HOVER_COLOR[mode_idx], text_color=BTN_UNITY_DOWN_TEXT_COLOR[mode_idx])
unity_down_btn.pack(fill="x", padx=15, pady=5)

about_btn = ctk.CTkButton(sidebar_frame, text="About",
                          command=lambda: messagebox.showinfo("About", "Unity Simulation Manager v1.0.\n\nAuthors:\nIván Cáceres S.\nTobías Guerrero Ch."),
                          font=APP_FONT,
                          fg_color=BTN_ABOUT_FG_COLOR[mode_idx], hover_color=BTN_ABOUT_HOVER_COLOR[mode_idx], text_color=BTN_ABOUT_TEXT_COLOR[mode_idx])
about_btn.pack(fill="x", padx=15, pady=5)

# Theme Switch (Bottom of Sidebar)
theme_switch = ctk.CTkSwitch(sidebar_frame, text=f"{initial_mode} Mode", command=toggle_appearance_mode, font=APP_FONT)
theme_switch.pack(fill="x", side='bottom', padx=15, pady=(10, 5))
# Set initial state of the switch
if initial_mode == "Dark": theme_switch.select()
else: theme_switch.deselect()

# Exit Button (Bottom of Sidebar)
exit_btn = ctk.CTkButton(sidebar_frame, text="Exit Application", command=on_closing, font=APP_FONT,
                         fg_color=BTN_EXIT_FG_COLOR[mode_idx], hover_color=BTN_EXIT_HOVER_COLOR[mode_idx], text_color=BTN_EXIT_TEXT_COLOR[mode_idx])
exit_btn.pack(fill="x", side='bottom', padx=15, pady=(5, 20))


# --- Main Content Area ---
main_content_frame = ctk.CTkFrame(main_window, corner_radius=5)
main_content_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
# Layout: Title, Search, Treeview (expands), Bottom Buttons
main_content_frame.columnconfigure(0, weight=1)
main_content_frame.rowconfigure(0, weight=0) # Title
main_content_frame.rowconfigure(1, weight=0) # Search
main_content_frame.rowconfigure(2, weight=1) # Treeview expands
main_content_frame.rowconfigure(3, weight=0) # Bottom buttons

# Title Label
header_frame = ctk.CTkFrame(main_content_frame, fg_color="transparent")
header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
header_frame.columnconfigure(0, weight=1)
ctk.CTkLabel(header_frame, text="Unity Simulation Manager", font=TITLE_FONT, anchor="center").grid(row=0, column=0, pady=(0, 10))

# Search Bar Area
search_frame = ctk.CTkFrame(main_content_frame, fg_color="transparent")
search_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(5, 5))
search_frame.columnconfigure(1, weight=1) # Search entry expands

ctk.CTkLabel(search_frame, text="Search:", font=APP_FONT).grid(row=0, column=0, padx=(5, 5), pady=5)
search_entry = ctk.CTkEntry(search_frame, placeholder_text="Type simulation name to filter...", font=APP_FONT)
search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
search_entry.bind("<KeyRelease>", filter_simulations) # Filter as user types

clear_search_btn = ctk.CTkButton(search_frame, text="Clear", width=60, font=APP_FONT, command=clear_search,
                                fg_color=BTN_CLEARSEARCH_FG_COLOR[mode_idx], hover_color=BTN_CLEARSEARCH_HOVER_COLOR[mode_idx], text_color=BTN_CLEARSEARCH_TEXT_COLOR[mode_idx])
clear_search_btn.grid(row=0, column=2, padx=(5, 5), pady=5)

# --- Treeview for Simulations ---
tree_frame = ctk.CTkFrame(main_content_frame, corner_radius=5)
tree_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
tree_frame.columnconfigure(0, weight=1) # Treeview expands horizontally
tree_frame.rowconfigure(0, weight=1) # Treeview expands vertically

# Define columns (use internal names)
columns = ("col_name", "col_created", "col_last_used", "col_loaded", "col_load", "col_delete")
sim_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

# Define Headings and Column Properties
sim_tree.heading("col_name", text="Simulation Name", anchor='w')
sim_tree.column("col_name", width=250, minwidth=150, anchor="w", stretch=tk.YES) # Allow stretch

sim_tree.heading("col_created", text="Created", anchor='center')
sim_tree.column("col_created", width=120, minwidth=100, anchor="center", stretch=tk.NO)

sim_tree.heading("col_last_used", text="Last Used", anchor='center')
sim_tree.column("col_last_used", width=120, minwidth=100, anchor="center", stretch=tk.NO)

sim_tree.heading("col_loaded", text="Loaded", anchor='center') # Status indicator
sim_tree.column("col_loaded", width=70, minwidth=60, stretch=tk.NO, anchor="center")

sim_tree.heading("col_load", text="Load/Run", anchor='center') # Action column
sim_tree.column("col_load", width=90, minwidth=80, stretch=tk.NO, anchor="center")

sim_tree.heading("col_delete", text="Delete", anchor='center') # Action column
sim_tree.column("col_delete", width=80, minwidth=70, stretch=tk.NO, anchor="center")

# Sorting Logic
last_sort_column = None # Track last sorted column
# Store sort order (False=Ascending, True=Descending)
sort_order = {col: False for col in columns if col not in ["col_load", "col_delete", "col_loaded"]}

def sort_column(tree, col, reverse):
    """Sorts the treeview column."""
    # Prevent sorting action columns
    if col in ["col_load", "col_delete", "col_loaded"]:
        return

    global last_sort_column, sort_order
    try:
        # Get data for sorting: list of tuples (value, item_id)
        data = [(tree.set(item, col), item) for item in tree.get_children('')]

        # Conversion key function based on column type
        def get_sort_key(value_str):
            if col in ("col_created", "col_last_used"):
                if value_str in ("???", "Never") or not value_str: return 0 # Treat unknowns/Never as earliest
                try: # Convert 'yy-mm-dd HH:MM' to timestamp
                    return time.mktime(time.strptime(value_str, "%y-%m-%d %H:%M"))
                except ValueError: return 0 # Fallback for parsing errors
            # Default: Case-insensitive string sort
            else: return str(value_str).lower()

        # Sort the data
        data.sort(key=lambda t: get_sort_key(t[0]), reverse=reverse)

        # Rearrange items in the treeview
        for i, (_, item) in enumerate(data):
            tree.move(item, '', i)

        # Update sort order state
        sort_order[col] = reverse
        last_sort_column = col

        # Update heading text with sort indicators (▲/▼) and rebind command
        for c in sort_order: # Iterate through sortable columns only
             current_heading = tree.heading(c)
             heading_text = current_heading['text'].replace(' ▲', '').replace(' ▼', '') # Remove old indicator
             if c == col: # Add indicator to the sorted column
                 heading_text += (' ▼' if reverse else ' ▲')
             # Re-assign heading text and command (lambda captures current state)
             tree.heading(c, text=heading_text, command=lambda c_ref=c: sort_column(tree, c_ref, not sort_order.get(c_ref, False)))

    except Exception as e:
        print(f"Error sorting column '{col}': {e}")


# Initial binding for sortable columns
for col_name in columns:
    if col_name not in ["col_load", "col_delete", "col_loaded"]:
        current_text = sim_tree.heading(col_name)['text'] # Get original text
        anchor_dir = 'w' if col_name=='col_name' else 'center'
        # Initial sort command: sort ascending (reverse=False)
        sim_tree.heading(col_name, text=current_text, command=lambda c=col_name: sort_column(sim_tree, c, False), anchor=anchor_dir)


# Place Treeview and Scrollbar
sim_tree.grid(row=0, column=0, sticky="nsew")
scrollbar = ctk.CTkScrollbar(tree_frame, command=sim_tree.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
sim_tree.configure(yscrollcommand=scrollbar.set)

# Bind Treeview Events
sim_tree.bind('<<TreeviewSelect>>', lambda e: update_button_states()) # Update buttons on selection change
sim_tree.bind("<Button-1>", handle_tree_click) # Handle clicks for actions
sim_tree.bind("<Motion>", handle_tree_motion) # Handle hover for tooltips
sim_tree.bind("<Leave>", handle_tree_leave) # Hide tooltip on mouse leave

# --- Bottom Action Buttons ---
button_frame_bottom = ctk.CTkFrame(main_content_frame, fg_color="transparent")
button_frame_bottom.grid(row=3, column=0, pady=(10, 10), padx=10, sticky="ew")
# Center buttons using spacer columns with weights
button_frame_bottom.columnconfigure(0, weight=1) # Left spacer
button_frame_bottom.columnconfigure(1, weight=0) # Reload
button_frame_bottom.columnconfigure(2, weight=0) # Graph
button_frame_bottom.columnconfigure(3, weight=0) # Create
button_frame_bottom.columnconfigure(4, weight=1) # Right spacer
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


# --- Status Bar ---
status_frame = ctk.CTkFrame(main_window, height=25, corner_radius=0)
status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=0)
status_label = ctk.CTkLabel(status_frame, text="Initializing...", anchor="w", font=STATUS_FONT)
status_label.pack(side="left", fill="x", expand=True, padx=10, pady=3)


# ======================================================
# Application Initialization
# ======================================================
if __name__ == "__main__":
    # Apply initial styles after window is created
    main_window.after(10, update_treeview_style)
    # Set initial button states (mostly disabled until verification)
    update_button_states()
    # Start initial configuration verification in a thread
    update_status("Performing initial configuration verification...")
    initial_verify_thread = threading.Thread(target=perform_verification, args=(False, True), daemon=True)
    initial_verify_thread.start()

    # Set closing protocol
    main_window.protocol("WM_DELETE_WINDOW", on_closing)
    # Start the GUI event loop
    main_window.mainloop()