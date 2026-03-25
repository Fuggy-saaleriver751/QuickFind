"""QuickFind Launcher"""
import os, sys, ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("dgknk.QuickFind.1")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import main
main()
