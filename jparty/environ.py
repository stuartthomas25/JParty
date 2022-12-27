import sys

if getattr(sys, "frozen", False):
    root = getattr(sys, "_MEIPASS", ".")  # os.path.dirname(sys.executable)
else:
    root = ""
