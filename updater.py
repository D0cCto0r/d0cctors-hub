import os
import sys
import time
import subprocess

old_exe = sys.argv[1]
new_exe = sys.argv[2]

print("Esperando cierre del launcher...")

time.sleep(2)

# Esperar que el exe deje de existir como proceso
while True:
    try:
        os.rename(old_exe, old_exe)
        break
    except PermissionError:
        time.sleep(1)

print("Reemplazando launcher...")

backup = old_exe + ".old"

try:
    os.rename(old_exe, backup)
except:
    pass

os.rename(new_exe, old_exe)

try:
    os.remove(backup)
except:
    pass

print("Reiniciando launcher...")

subprocess.Popen(old_exe)

time.sleep(1)