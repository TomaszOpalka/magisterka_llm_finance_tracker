import os
import ast
import pytest
import re

# List of common Polish characters to detect language inconsistency
POLISH_CHARS = "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ"

def get_files_to_check(target_dir):
    """Recursively get all .py files in the target directory."""
    files = []
    if not os.path.exists(target_dir):
        return []
    for root, _, filenames in os.walk(target_dir):
        for filename in filenames:
            if filename.endswith(".py"):
                files.append(os.path.join(root, filename))
    return files

def check_for_polish(text):
    """Check if the text contains any Polish-specific characters."""
    if not text:
        return False
    return any(char in POLISH_CHARS for char in text)

# Parametrize with all models found in experiments
EXPERIMENTS_PATH = "experiments"
ALL_MODELS = [
    os.path.join(EXPERIMENTS_PATH, d) 
    for d in os.listdir(EXPERIMENTS_PATH) 
    if os.path.isdir(os.path.join(EXPERIMENTS_PATH, d))
]

@pytest.mark.parametrize("target_path", ALL_MODELS)
class TestKPI:
    
    def test_language_consistency(self, target_path):
        """
        KPI: Inconsistency Error
        Verify that comments, docstrings, and loggers do not contain Polish language.
        """
        files = get_files_to_check(target_path)
        if not files:
            pytest.skip(f"No python files in {target_path}")
            
        errors = []
        
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Check comments
                for line in content.splitlines():
                    if "#" in line:
                        comment = line.split("#", 1)[1]
                        if check_for_polish(comment):
                            errors.append(f"Polish in comment [{file_path}]: {line.strip()}")
                
                # Check AST for docstrings and strings
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        # Docstrings
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                            doc = ast.get_docstring(node)
                            if check_for_polish(doc):
                                errors.append(f"Polish in docstring [{file_path}]: at {node.name if hasattr(node, 'name') else 'Module'}")
                        
                        # String literals (ast.Constant handles strings in Python 3.8+)
                        if isinstance(node, ast.Constant) and isinstance(node.value, str):
                            if check_for_polish(node.value):
                                errors.append(f"Polish in string literal [{file_path}]: '{node.value[:50]}...'")
                                
                except SyntaxError:
                    errors.append(f"Syntax error in file: {file_path}")

        assert not errors, f"Language inconsistency in {target_path}:\n" + "\n".join(errors)

    def test_event_loop_congestion(self, target_path):
        """
        KPI: Poprawność Funkcjonalna (Zator Pętli Zdarzeń)
        Check if yfinance is used correctly with asyncio.to_thread in services.py.
        """
        services_file = os.path.join(target_path, "services.py")
        if not os.path.exists(services_file):
            pytest.skip(f"services.py not found in {target_path}")
            
        with open(services_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "yfinance" not in content and "yf" not in content:
            pytest.skip("yfinance not used in services.py")
            
        tree = ast.parse(content)
        found_yf_usage = False
        wrapped_correctly = False
        
        for node in ast.walk(tree):
            # Look for calls like yf.Ticker or yfinance.Ticker
            if isinstance(node, ast.Call):
                call_str = ast.unparse(node)
                if "yf." in call_str or "yfinance." in call_str:
                    found_yf_usage = True
                    
            # Look for asyncio.to_thread or run_in_executor calls
            if isinstance(node, ast.Call):
                call_name = ""
                if isinstance(node.func, ast.Attribute):
                    call_name = node.func.attr
                elif isinstance(node.func, ast.Name):
                    call_name = node.func.id
                
                if call_name in ["to_thread", "run_in_executor"]:
                    wrapped_correctly = True

        assert found_yf_usage, f"yfinance usage not found in {services_file}"
        assert wrapped_correctly, f"yfinance calls in {target_path} are NOT wrapped in asyncio.to_thread!"

    def test_import_cascade(self, target_path):
        """
        KPI: Cross-file Error (Kaskada Importów)
        Verify critical imports and type hints.
        """
        main_file = os.path.join(target_path, "main.py")
        services_file = os.path.join(target_path, "services.py")
        
        if not os.path.exists(main_file):
            pytest.skip(f"main.py not found in {target_path}")

        with open(main_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check critical imports
        assert "AsyncSession" in content, f"AsyncSession import missing in {main_file}"
        
        # Check get_db signature
        tree = ast.parse(content)
        found_get_db = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == "get_db":
                    found_get_db = True
                    # Check if it has return type hint (optional but good KPI)
                    if node.returns:
                        return_hint = ast.unparse(node.returns)
                        assert "AsyncGenerator" in return_hint or "AsyncIterator" in return_hint, \
                            f"get_db in {main_file} has wrong return type hint: {return_hint}"
        
        assert found_get_db, f"get_db function not found in {main_file}"

        # Check services.py if it exists and uses yfinance
        if os.path.exists(services_file):
            with open(services_file, "r", encoding="utf-8") as f:
                s_content = f.read()
            if "yfinance" in s_content or "yf" in s_content:
                assert "asyncio" in s_content, f"asyncio import missing in {services_file} (required for to_thread)"
