import os
import sys
from pathlib import Path
import win32com.client


def main():
    python_exe = Path(sys.executable)
    script_dir = Path(__file__).parent.resolve()
    main_script = script_dir / "main.py"
    pythonw = python_exe.parent / "pythonw.exe"
    target = pythonw if pythonw.exists() else python_exe

    shell = win32com.client.Dispatch("WScript.Shell")
    desktop = Path(os.environ["USERPROFILE"]) / "Desktop"

    shortcut = shell.CreateShortCut(str(desktop / "实验记录管理器.lnk"))
    shortcut.Targetpath = str(target)
    shortcut.Arguments = f'"{main_script}"'
    shortcut.WorkingDirectory = str(script_dir)
    shortcut.Description = "实验记录管理器 - 动态Latent研究"
    shortcut.save()

    print(f"桌面快捷方式: {desktop / '实验记录管理器.lnk'}")


if __name__ == "__main__":
    main()
