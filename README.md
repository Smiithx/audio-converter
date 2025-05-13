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

Inicia la aplicación con:

```bash
python audio_converter_gui.py
```

1. Elige entre **Convertir audio** o **Transcribir audio**.
2. Activa la casilla **Procesar carpeta** si quieres aplicar la operación a todos los archivos dentro de una carpeta.
3. Selecciona la ruta de entrada (archivo o carpeta).
4. Selecciona la ruta de salida (archivo o carpeta).
5. Configura opciones de FFmpeg (sólo en modo conversión) y la extensión de salida si es carpeta.
6. Haz clic en **Ejecutar** y revisa los mensajes de éxito o error.

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
