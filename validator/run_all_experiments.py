import subprocess
import os
import sys

def run_tests(path, name):
    print(f"\n{'='*60}")
    print(f" RUNNING TESTS FOR: {name}")
    print(f"{'='*60}")
    
    # Run pytest for the specific experiment
    result = subprocess.run(
        ["pytest", path, "-v"],
        capture_output=False,
        text=True
    )
    
    if result.returncode == 0:
        print(f"\n✅ {name}: ALL TESTS PASSED")
    else:
        print(f"\n❌ {name}: SOME TESTS FAILED (Exit Code: {result.returncode})")
    
    return result.returncode

def main():
    # Root directory of the project
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(root_dir)
    
    experiments = [
        ("experiments/mgr_gpt_free", "GPT Free"),
        ("experiments/mgr_gemini_flash", "Gemini Flash"),
        ("experiments/mgr_deepseek_free", "DeepSeek Free"),
        ("experiments/mgr_pro_gemini", "Gemini Pro"),
        ("validator", "Global Validators")
    ]
    
    failures = 0
    for path, name in experiments:
        if os.path.exists(path):
            exit_code = run_tests(path, name)
            if exit_code != 0:
                failures += 1
        else:
            print(f"\n⚠️ Skipping {name}: Path {path} not found.")

    print(f"\n{'='*60}")
    if failures == 0:
        print("🎉 ALL MODELS AND VALIDATORS PASSED!")
    else:
        print(f"🛑 {failures} MODULE(S) FAILED.")
    print(f"{'='*60}")
    
    sys.exit(failures)

if __name__ == "__main__":
    main()
