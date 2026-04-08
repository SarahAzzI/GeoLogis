import os
import sys

# Ajoute le répertoire 'pipeline' au PYTHONPATH pendant l'exécution des tests
PACKAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PACKAGE_DIR not in sys.path:
    sys.path.insert(0, PACKAGE_DIR)
