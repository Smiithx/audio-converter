# Audio Converter & Transcriber 📡📝

**Audio Converter & Transcriber** es una aplicación de escritorio con interfaz gráfica (Tkinter) que permite:

* **Convertir** archivos o carpetas de audio entre distintos formatos (MP3, WAV, etc.) usando **FFmpeg**.
* **Transcribir** archivos o carpetas de audio a texto (".txt") con **OpenAI Whisper**.

---

## 📋 Características

* Conversión de un solo archivo o carpetas completas recursivas.
* Soporte para múltiples formatos de entrada: `.opus`, `.mp3`, `.wav`, `.aac`, `.flac`, `.m4a`, `.webm`, `.ogg`, `.amr`, `.mp4`, etc.
* Opciones avanzadas de FFmpeg configurables (por ejemplo, calidad, bitrate).
* Transcripción local con Whisper (`base` model) sin necesidad de API externa.
* Interfaz intuitiva para seleccionar rutas de entrada y salida.

---

## 🚀 Instalación

1. Clona este repositorio:

   ```bash
   git clone https://github.com/tu-usuario/audio-converter.git
   cd audio-converter
   ```

2. Crea y activa un entorno virtual (opcional pero recomendado):

   ```bash
   python -m venv .venv
   source .venv/bin/activate    # Linux/macOS
   .\.venv\Scripts\activate  # Windows PowerShell
   ```

3. Instala dependencias:

   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

4. Asegúrate de tener **FFmpeg** instalado y accesible en tu PATH:

   * **Windows**: instala con Chocolatey (`choco install ffmpeg`) o descarga binarios de [FFmpeg.org](https://ffmpeg.org).
   * **macOS**: `brew install ffmpeg`
   * **Linux**: `sudo apt install ffmpeg` (o equivalente).

---

## 🛠 Uso

### 🖥️ Interfaz Gráfica (GUI)
Inicia la aplicación sin argumentos para abrir la ventana:
```bash
python audio_converter_gui.py
```

1. Elige entre **Convertir audio** o **Transcribir audio**.
2. Activa **Procesar carpeta** para operaciones por lotes.
3. Selecciona rutas de entrada y salida.
4. Haz clic en **Ejecutar**.

### ⌨️ Línea de Comandos (CLI)
La aplicación ahora soporta comandos de consola para automatización:

**Transcripción:**
```bash
# Transcribir y mostrar en pantalla
python audio_converter_gui.py --mode transcribe --input archivo.mp3

# Transcribir y guardar en .txt
python audio_converter_gui.py --mode transcribe --input archivo.mp3 --output resultado.txt

# Transcribir carpeta completa
python audio_converter_gui.py --mode transcribe --input ./audios --output ./textos --folder
```

**Conversión:**
```bash
# Convertir archivo
python audio_converter_gui.py --mode convert --input cancion.wav --output cancion.mp3

# Convertir archivo con opciones de bitrate
python audio_converter_gui.py --mode convert --input input.wav --output output.mp3 --options "-b:a 192k"

# Convertir carpeta completa a un formato específico
python audio_converter_gui.py --mode convert --input ./wavs --output ./mp3s --folder --ext .mp3
```

**Ayuda:**
```bash
python audio_converter_gui.py --help
```

---

## 📦 Crear Ejecutable para Windows (.exe)

Para convertir esta aplicación en una app nativa de Windows que no requiera tener Python instalado globalmente:

1. Instala PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Ejecuta el script de construcción:
   ```bash
   python build_exe.py
   ```
3. El ejecutable se encontrará en la carpeta `dist/AudioConverterTranscriber.exe`.

---

## 📝 Estructura de archivos

```plaintext
audio-converter/
├── audio_converter_gui.py   # Código principal de la aplicación
├── requirements.txt         # Dependencias Python
└── README.md                # Este archivo
```

---

## 🔧 Dependencias

* Python 3.7+
* [Tkinter](https://docs.python.org/3/library/tkinter.html)
* [OpenAI Whisper](https://github.com/openai/whisper)
* [FFmpeg](https://ffmpeg.org)

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

> Hecho con ❤️ por **Andrés González**
