import json
import os
import subprocess
import sys

def find_test_command(root_dir):
    package_json = os.path.join(root_dir, "package.json")
    pyproject = os.path.join(root_dir, "pyproject.toml")
    setup_cfg = os.path.join(root_dir, "setup.cfg")
    setup_py = os.path.join(root_dir, "setup.py")
    cargo_toml = os.path.join(root_dir, "Cargo.toml")
    go_mod = os.path.join(root_dir, "go.mod")
    pom_xml = os.path.join(root_dir, "pom.xml")
    gradle_kts = os.path.join(root_dir, "build.gradle.kts")
    gradle = os.path.join(root_dir, "build.gradle")
    makefile = os.path.join(root_dir, "Makefile")

    if os.path.exists(package_json):
        with open(package_json, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        scripts = data.get("scripts", {})
        if "test" in scripts:
            return ["npm", "test"]

    if os.path.exists(pyproject) or os.path.exists(setup_cfg) or os.path.exists(setup_py):
        return [sys.executable, "-m", "pytest"]

    if os.path.exists(cargo_toml):
        return ["cargo", "test"]

    if os.path.exists(go_mod):
        return ["go", "test", "./..."]

    if os.path.exists(pom_xml):
        return ["mvn", "test"]

    if os.path.exists(gradle_kts) or os.path.exists(gradle):
        return ["gradle", "test"]

    if os.path.exists(makefile):
        return ["make", "test"]

    return None

def run_tests():
    root_dir = os.getcwd()
    command = find_test_command(root_dir)
    if not command:
        print("No test command detected")
        return 0
    result = subprocess.run(command, cwd=root_dir)
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
