
import subprocess
import json
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPORT_DIR = os.path.join(BASE_DIR, 'data', 'tests')
JSON_REPORT_PATH = os.path.join(REPORT_DIR, 'report.json')
HTML_REPORT_PATH = os.path.join(REPORT_DIR, 'report.html')
PYTEST_EXECUTABLE = os.path.join(os.path.dirname(sys.executable), 'pytest')

def run_tests_and_generate_reports():
    """
    Lance les tests et génère un rapport JSON (pour l'UI) et un rapport HTML (pour les détails).
    """
    os.makedirs(REPORT_DIR, exist_ok=True)
    
    command = [
        PYTEST_EXECUTABLE,
        "--json-report", f"--json-report-file={JSON_REPORT_PATH}",
        f"--html={HTML_REPORT_PATH}", "--self-contained-html" # <-- NOUVELLES OPTIONS
    ]
    
    print("Lancement des tests unitaires et génération des rapports...")
    try:
        subprocess.run(command, check=True, cwd=BASE_DIR, capture_output=True, text=True, timeout=120)
        print("Tests terminés avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"Les tests se sont terminés avec des échecs.")
        # C'est un comportement normal si un test échoue, on continue.
    
    return get_latest_json_report()

def get_latest_json_report():
    """Lit le dernier rapport JSON s'il existe."""
    if os.path.exists(JSON_REPORT_PATH):
        with open(JSON_REPORT_PATH, 'r') as f:
            return json.load(f)
    return None