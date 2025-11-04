#!/usr/bin/python3

from subprocess import run as exe_cmd, PIPE, CalledProcessError
import os
import platform
import shutil

# Colors Definitions:
RED = "\u001B[1;31m"
GREEN = "\u001B[1;32m"
BLUE = "\u001B[1;34m"
RESET = "\u001B[0m"

def execute_cmd(command: list[str]) -> str:
    """
    Execute a command. Any errors will cause the program to stop describing the
    abnormal event.

    Args:
        command (list[str]): The command to execute.
    
    Returns:
        str: Command output if no error is raised.
    """
    try:
        result = exe_cmd(
            command,
            stdout=PIPE,
            stderr=PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except CalledProcessError as e:
        print(f"There was an error executing a command ({' '.join(command)}):")
        print(f" Return Code:\t {e.returncode}.")
        print(f" STDOUT:\t \"{e.stdout}\".")
        print(f"STDERR:\t \"{e.stderr}\".")
        exit(1)

def create_venv(venv_path: str = "./venv"):
    """
    Create Python Virutal Environment to specified path.

    Args:
        venv_path (str, optional): Path to Venv. Defaults to "./venv".
    """
    python_exec = "python3" if shutil.which("python3") else "python"
    command: list[str] = [python_exec, "-m", "venv", venv_path]
    execute_cmd(command)

def push_src_to_env(venv_path: str = "./venv") -> bool:
    """
    Pushes source directory to Python Virtual Environment.

    Returns:
        bool: The result outcome of the copy.
    """
    # Copy src folder to Virtual Environment (cross-platform):
    src_path = "./src"
    if os.path.exists(src_path):
        dst_path = os.path.join(venv_path, "src")
        # shutil.copytree works cross-platform (Windows/Linux/macOS)
        if os.path.exists(dst_path):
            shutil.rmtree(dst_path)
        try:
            shutil.copytree(src_path, dst_path)
            return True
        except Exception as e:
            print(f"{RED}Error copying src directory{RESET}: {e}")
            return False
    return False

def install_requirements(venv_path: str = "./venv", requirements_path: str = "./requirements.txt") -> bool:
    """
    Install requirements from the specified file.

    Args:
        requirements_path (str): The path to the requirements txt file.

    Returns:
        bool: The result outcome of the install process.
    """

    # Determine OS type:
    system_name = platform.system().lower()

    # Compute pip executable path depending on OS:
    if system_name == "windows":
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")

    # Check if pip exists:
    if not os.path.exists(pip_path):
        return False

    # Upgrade pip to latest version:
    execute_cmd([pip_path, "install", "--upgrade", "pip"])

    # Install requirements if provided:
    if requirements_path and os.path.exists(requirements_path):
        execute_cmd([pip_path, "install", "-r", requirements_path])
        return True
    if requirements_path:
        print(f"{RED}Warning:{RESET} requirements file not found: {requirements_path}")
    return False

def setup_venv(path: str = "./venv", requirements_path: str = None) -> bool:
    """
    Create Python Virtual Environment in the specified path (if the directory
    doesn't exists). Install requirements if a path to a txt is specified and
    copies src directory inside venv.

    Args:
        path (str, optional): Virtual Environment path. Defaults to "./venv".
        requirements_path (str, optional): Requirements File path. Defaults to
        None (no requirements).
    
    Returns:
        bool: The result outcome of the setup process.
    """

    res: bool = True

    # Create Python Virtual Environment:
    create_venv(path)

    # Install requirements (if any):
    if requirements_path:
        res = res and install_requirements(venv_path=path, requirements_path=requirements_path)

    # Copy src to venv:
    res = res and push_src_to_env(venv_path=path)

    return res


def main():
    """
    Starts main menu.
    """
    while True:
        print(f"\u001B[H\u001B[2J{GREEN} IXH25 - Italian XRPL Hackathon - UNIPG MSC Team{RESET}")
        print(f"{BLUE}1{RESET}) Setup Python Virtual Environment (All-in-One Command).")
        print(f"{BLUE}2{RESET}) Create Python Virtual Environment.")
        print(f"{BLUE}3{RESET}) Install Requirements.")
        print(f"{BLUE}4{RESET}) Push Code to Virtual Environment.")
        print(f"{RED}0{RESET}) Exit.")

        choice = input("Your choice[Enter = 4]: ")
        if choice == "":
            choice = 4

        try:
            choice = int(choice)
        except ValueError:
            print("You must insert a number! Press enter to retry.")
            input()
            continue

        match choice:
            case 1:
                # Requirements path (if any):
                req: str | None = None
                # Detect any requirements.txt in local folder:
                if os.path.exists("./requirements.txt"):
                    req = "./requirements.txt"
                # Create Environment:
                if setup_venv("./venv", req):
                    print(f"{GREEN}Setup Completed Successfully{RESET}! Press Enter to Continue.", end="")
                else:
                    print(f"{RED}Setup Error{RESET}! Press Enter to Continue.", end="")
                input()
            case 2:
                venv_path = input("Enter Virtual Environment Path[Enter=\"./venv\"]:")
                if venv_path == "":
                    venv_path = "./venv"
                if create_venv(venv_path):
                    print(f"{GREEN}Virtual Environment Created Successfully{RESET}! Press Enter to Continue.", end="")
                else:
                    print(f"{RED}Virtual Environment Creation Error{RESET}! Press Enter to Continue.", end="")
                input()
            case 3:
                req = input("Enter \"requirements.txt\" Path[Enter=\"./requirements.txt\"]:")
                if req == "":
                    req = "./requirements.txt"
                if install_requirements():
                    print(f"{GREEN}Requirements Installed Successfully{RESET}! Press Enter to Continue.", end="")
                else:
                    print(f"{RED}Error Installing Requirements{RESET}! Press Enter to Continue.", end="")
                input()
            case 4:
                venv_path = input("Enter Virtual Environment Path[Enter=\"./venv\"]:")
                if venv_path == "":
                    venv_path = "./venv"
                if push_src_to_env(venv_path=venv_path):
                    print(f"{GREEN}Source Pushed to Virtual Environment{RESET}! Press Enter to Continue.", end="")
                else:
                    print(f"{RED}Error Copying{RESET}! Press Enter to Continue.", end="")
                input()
            case 0:
                break

if __name__ == "__main__":
    main()
