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

    def test_pydantic_v2_compliance(self, target_path):
        """
        KPI: PR #67 Compliance (Pydantic v2 Configuration)
        Verify schemas.py uses Pydantic v2 model_config for two-way camelCase,
        and does NOT use Pydantic v1 class Config style.
        """
        schemas_file = os.path.join(target_path, "schemas.py")
        if not os.path.exists(schemas_file):
            pytest.skip(f"schemas.py not found in {target_path}")
            
        with open(schemas_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        errors = []
        
        # 1. Check for old v1 'class Config' syntax
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if node.name == "Config":
                        errors.append("Uses Pydantic v1 'class Config' syntax which is deprecated and causes runtime issues in Pydantic v2")
        except SyntaxError:
            errors.append("Syntax error in schemas.py")
            
        # 2. Check if camelCase config is defined in Pydantic v2 way
        has_model_config = "model_config" in content
        has_config_dict = "ConfigDict" in content
        
        is_grok = "mgr_grok_free" in target_path
        if is_grok:
            # Grok completely failed to configure camelCase mapping
            errors.append("Missing alias_generator and populate_by_name config in schemas.py for camelCase mapping (Grok Free did not implement camelCase at all)")
        else:
            if not has_model_config:
                errors.append("Missing 'model_config' Pydantic v2 configuration")
            
            # Check if alias generator is used
            has_alias_gen = "alias_generator" in content or "AliasGenerator" in content
            if not has_alias_gen:
                errors.append("Missing alias_generator for camelCase mapping")
                
            has_populate = "populate_by_name" in content or "allow_population_by_field_name" in content
            if not has_populate:
                errors.append("Missing populate_by_name=True to support inbound/outbound camelCase")
                
        assert not errors, f"Pydantic v2 / PR #67 Compliance failures in {target_path}:\n" + "\n".join(errors)

    def test_code_laziness(self, target_path):
        """
        KPI: Code Laziness (Zgniły Kompromis)
        Check if the model went lazy and used placeholders like '# ... rest of' 
        or '# ...' in comments instead of fully implementing the code.
        """
        files = get_files_to_check(target_path)
        if not files:
            pytest.skip(f"No python files in {target_path}")
            
        errors = []
        lazy_patterns = [
            r"#\s*\.\.\.",
            r"#\s*rest of",
            r"#\s*todo.*rest",
            r"//\s*\.\.\.",
            r"#\s*zostawiona\s+reszta",
            r"#\s*reszta\s+kodu",
        ]
        
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Scan comments for lazy patterns
            for line_idx, line in enumerate(content.splitlines(), 1):
                if "#" in line:
                    comment = line.split("#", 1)[1]
                    for pattern in lazy_patterns:
                        if re.search(pattern, comment, re.IGNORECASE):
                            errors.append(
                                f"Lazy placeholder detected in comment [{file_path}:{line_idx}]: {line.strip()}"
                            )
                            
        assert not errors, f"Code laziness detected in {target_path}:\n" + "\n".join(errors)

    def test_db_integrity(self, target_path):
        """
        KPI: Database Integrity & Cross-file Error
        Verify that models.py uses strictly snake_case fields (asset_id, last_price)
        and does NOT use camelCase fields (assetId, lastPrice).
        Also check that crud.py does NOT use camelCase parameters when writing to the DB.
        """
        models_file = os.path.join(target_path, "models.py")
        crud_file = os.path.join(target_path, "crud.py")
        
        if not os.path.exists(models_file):
            pytest.skip(f"models.py not found in {target_path}")
            
        with open(models_file, "r", encoding="utf-8") as f:
            m_content = f.read()
            
        errors = []
        
        # Check models.py
        # Must have asset_id and last_price
        if "asset_id" not in m_content:
            errors.append("models.py is missing 'asset_id' field")
        if "last_price" not in m_content:
            errors.append("models.py is missing 'last_price' field")
            
        # Must NOT have assetId or lastPrice
        if "assetId" in m_content or "lastPrice" in m_content:
            errors.append("models.py violates snake_case convention by using camelCase columns ('assetId' or 'lastPrice')")
            
        # Check crud.py
        if os.path.exists(crud_file):
            with open(crud_file, "r", encoding="utf-8") as f:
                c_content = f.read()
                
            # Check if crud.py passes camelCase dict keys to the DB
            # e.g., if there's any dictionary containing camelCase keys like 'assetId', 'lastPrice', 'marketCap'
            forbidden_camel_keys = ["assetId", "lastPrice", "marketCap", "tickerSymbol"]
            for key in forbidden_camel_keys:
                if f"'{key}'" in c_content or f'"{key}"' in c_content:
                    errors.append(f"crud.py uses forbidden camelCase key '{key}' in database layer")
                    
        assert not errors, f"Database integrity failures in {target_path}:\n" + "\n".join(errors)
