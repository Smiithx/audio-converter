import PyInstaller.__main__
import os
import sys

# Determinar si hay soporte para GPU
try:
    import torch
    has_cuda = torch.cuda.is_available()
except ImportError:
    has_cuda = False

print(f"CUDA disponible: {has_cuda}")

params = [
    'audio_converter_gui.py',
    '--name=AudioConverterTranscriber',
    '--onefile',
    '--windowed', # Inicia como ventana, pero argparse permite usarlo en consola
    '--collect-all=whisper',
    '--collect-all=torch',
    '--hidden-import=sounddevice',
    '--hidden-import=scipy.special._cdflib',
    '--clean',
]

# Si queremos que la consola sea visible siempre para ver mensajes de error/logs:
# Quitamos --windowed si queremos que actúe 100% como app de consola cuando sea necesario,
# pero para una "app nativa" solemos preferir windowed. 
# Nota: En Windows, una app --windowed no muestra stdout a menos que se redirija.
# Para soportar ambos mundos (GUI y CLI) de forma amigable en Windows, 
# a veces se prefiere NO usar --windowed o usar técnicas para detectar la consola.

# Para simplificar y que el usuario vea el output de CLI:
params.remove('--windowed')
params.append('--console')

PyInstaller.__main__.run(params)
