import subprocess
import os
import sys
import re

def run_tests(path, name):
    print(f"Testing {name}...", end=" ", flush=True)
    
    python_exe = sys.executable
    
    # Run pytest and capture output as bytes to avoid decoding issues
    try:
        result = subprocess.run(
            [python_exe, "-m", "pytest", path, "-v", "--tb=line"],
            capture_output=True,
            text=False # Get bytes
        )
        
        # Decode manually with replacement for unknown characters
        stdout = result.stdout.decode('utf-8', errors='replace')
        stderr = result.stderr.decode('utf-8', errors='replace')
        
        failures = []
        if result.returncode != 0:
            print("[FAIL]")
            for line in stdout.splitlines():
                if line.startswith("FAILED "):
                    failure_info = line[7:].strip()
                    failures.append(failure_info)
            
            if not failures:
                # Fallback for collection errors or runtime errors
                for line in stderr.splitlines():
                    if any(err in line for err in ["ImportError", "SyntaxError", "ModuleNotFoundError", "AssertionError"]):
                        failures.append(line.strip())
                if not failures:
                    # Look for error lines in stdout if stderr is empty
                    for line in stdout.splitlines():
                        if "ERROR " in line:
                            failures.append(line.strip())
                    if not failures:
                        failures.append(f"Exit Code {result.returncode} - check manual output")
        else:
            print("[OK]")
        
        return failures
    except Exception as e:
        print(f"[ERROR] Runner failed: {str(e)}")
        return [f"Runner error: {str(e)}"]

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(root_dir)
    
    experiments = [
        ("experiments/mgr_gpt_free", "GPT Free"),
        ("experiments/mgr_gemini_flash", "Gemini Flash"),
        ("experiments/mgr_deepseek_free", "DeepSeek Free"),
        ("experiments/mgr_pro_gemini", "Gemini Pro"),
        ("experiments/mgr_grok_free", "Grok Free"),
        ("validator", "Global Validators")
    ]
    
    report = {}
    
    print("\n" + "="*60)
    print(" STARTING MASTER THESIS VALIDATION SUITE")
    print("="*60 + "\n")
    
    for path, name in experiments:
        if os.path.exists(path):
            model_failures = run_tests(path, name)
            if model_failures:
                report[name] = model_failures
        else:
            print(f"Skipping {name} (path not found)")

    print("\n" + "="*60)
    print(" FINAL VALIDATION SUMMARY")
    print("="*60)
    
    if not report:
        print("\nALL TESTS PASSED! All models are compliant.")
    else:
        for model_name, issues in report.items():
            print(f"\nFAILED: {model_name}")
            for issue in issues:
                if " - " in issue:
                    try:
                        test_name, err = issue.split(" - ", 1)
                        test_parts = test_name.split("::")
                        clean_name = f"{test_parts[0].split('/')[-1]}::{test_parts[-1]}"
                        print(f"  * {clean_name}")
                        print(f"    Error: {err}")
                    except:
                        print(f"  * {issue}")
                else:
                    print(f"  * {issue}")

    print("\n" + "="*60)
    
    if report:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
