import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import tempfile
import threading
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
from src.providers import WhisperTranscriber, FFmpegConverter, GeminiVideoAnalyzer
from src.processor import MediaProcessor


class AudioConverterApp(tk.Tk):
    def __init__(self, google_api_key=""):
        super().__init__()
        self.title("Audio Converter & Transcriber")
        self.geometry("600x650")
        self.resizable(False, False)

        # Cargar llaves desde entorno
        self.api_key_paid = os.getenv("GOOGLE_API_KEY", "")
        self.api_key_free = os.getenv("GOOGLE_API_KEY_FREE", "")

        # Variables de estado
        self.mode = tk.StringVar(value="transcribe")
        self.process_folder = tk.BooleanVar(value=False)
        self.use_mic = tk.BooleanVar(value=False)
        self.use_free_tier = tk.BooleanVar(value=True)
        self.recording = False
        self.recorded_frames = []
        self.stream = None

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.ffmpeg_options = tk.StringVar(value="-y")
        self.output_ext = tk.StringVar(value=".mp3")
        self.analysis_prompt = tk.StringVar(value="""
Actúa como un Arquitecto de Software y Analista Técnico Funcional Senior. Analiza el video de esta reunión y extrae toda la información técnica y de negocio. 

Genera tu respuesta estrictamente con la siguiente estructura:

**1. PRIMERA LÍNEA OBLIGATORIA**
SUGGESTED_FILENAME: [Nombre_Corto_Descriptivo_Separado_Por_Guiones_Bajos]

**2. ANÁLISIS FUNCIONAL (Módulos y Formularios)**
Por cada módulo, pantalla o formulario discutido o mostrado, documenta:
* **Nombre del Módulo/Formulario.**
* **Propósito:** ¿Para qué sirve dentro del sistema?
* **Funcionamiento:** Explicación paso a paso de su flujo de uso.
* **Campos y Validaciones:** Inputs requeridos, reglas de negocio y outputs esperados.

**3. ARQUITECTURA DE DATOS (Modelos de Base de Datos)**
A partir de la conversación o de lo mostrado en pantalla (código, consultas SQL, interfaces), identifica y lista:
* **Entidades/Modelos:** Nombre de las tablas o colecciones.
* **Campos:** Lista de atributos identificados para cada modelo, infiriendo su tipo de dato (String, Int, Boolean, Foreign Key) si es posible.
* **Relaciones:** Conexiones mencionadas entre diferentes entidades.

**4. REGISTRO CRONOLÓGICO TÉCNICO**
Genera una bitácora con marcas de tiempo (ej.), aplicando estas reglas estrictas:
* Omite saludos y conversaciones no relacionadas con el proyecto.
* Registra decisiones arquitectónicas, requerimientos técnicos y bugs discutidos.
* Cuando se comparta pantalla, inserta la etiqueta **[CONTEXTO VISUAL: <descripción detallada>]**.
* Si se muestra código (PHP, JavaScript, SQL, etc.) o infraestructura (AWS, Docker, terminales), transcribe o reconstruye los bloques exactos dentro de bloques de código markdown.
* Si se muestran diagramas de arquitectura o flujos de negocio (ej. ERP, facturación), describe cada paso visualizado.

**5. INSTRUCCIONES Y PRÓXIMOS PASOS (Action Items)**
* **Instrucciones de configuración/despliegue:** Si se explicaron pasos para ejecutar o probar algo, lístalos como un mini-tutorial.
* **Tareas:** Lista de pendientes técnicos (To-Dos), requerimientos nuevos y responsables (si se mencionan).""")

        # Configuración de procesador con sus proveedores
        self.processor = MediaProcessor(
            transcriber=WhisperTranscriber(),
            converter=FFmpegConverter(),
            analyzer=GeminiVideoAnalyzer()
        )

        self._build_widgets()
        self._update_mode()

    def _build_widgets(self):
        # Operación
        tk.Label(self, text="Operación:").pack(anchor="w", pady=(10, 0), padx=10)
        frame_mode = tk.Frame(self)
        frame_mode.pack(fill="x", padx=10)
        tk.Radiobutton(frame_mode, text="Transcribir audio", variable=self.mode, value="transcribe",
                       command=self._update_mode).pack(side="left")
        tk.Radiobutton(frame_mode, text="Convertir audio", variable=self.mode, value="convert",
                       command=self._update_mode).pack(side="left")
        tk.Radiobutton(frame_mode, text="Analizar Reunión (Video)", variable=self.mode, value="video_analysis",
                       command=self._update_mode).pack(side="left")

        # Procesar carpeta
        tk.Checkbutton(self, text="Procesar carpeta", variable=self.process_folder,
                       command=self._update_mode).pack(anchor="w", pady=(10, 0), padx=10)
        # Usar micrófono
        self.chk_mic = tk.Checkbutton(self, text="Usar micrófono", variable=self.use_mic,
                                      command=self._update_mode)
        self.chk_mic.pack(anchor="w", pady=(5, 0), padx=10)

        # Selector de capa gratuita para Gemini
        self.chk_free_tier = tk.Checkbutton(self, text="Usar capa gratuita (Datos públicos)",
                                            variable=self.use_free_tier)

        self.gemini_prompt_label = tk.Label(self, text="Prompt de Análisis:")
        self.gemini_prompt_entry = tk.Text(self, height=8)
        self.gemini_prompt_entry.insert("1.0", self.analysis_prompt.get())

        # Etiquetas y entradas
        self.input_label = tk.Label(self, text="Archivo de entrada:")
        self.input_label.pack(anchor="w", pady=(10, 0), padx=10)
        frame_in = tk.Frame(self)
        frame_in.pack(fill="x", padx=10)
        self.entry_input = tk.Entry(frame_in, textvariable=self.input_path, state="readonly")
        self.entry_input.pack(side="left", fill="x", expand=True)
        self.btn_select_input = tk.Button(frame_in, text="Seleccionar...", command=self.select_input)
        self.btn_select_input.pack(side="right")

        self.output_label = tk.Label(self, text="Archivo de salida:")
        self.output_label.pack(anchor="w", pady=(10, 0), padx=10)
        frame_out = tk.Frame(self)
        frame_out.pack(fill="x", padx=10)
        self.entry_output = tk.Entry(frame_out, textvariable=self.output_path, state="readonly")
        self.entry_output.pack(side="left", fill="x", expand=True)
        self.btn_select_output = tk.Button(frame_out, text="Seleccionar...", command=self.select_output)
        self.btn_select_output.pack(side="right")

        # Extensión y opciones FFmpeg (solo en conversión)
        self.ext_label = tk.Label(self, text="Extensión de salida (solo carpeta):")
        self.ext_entry = tk.Entry(self, textvariable=self.output_ext)
        self.ffmpeg_label = tk.Label(self, text="Opciones adicionales de ffmpeg:")
        self.ffmpeg_entry = tk.Entry(self, textvariable=self.ffmpeg_options)

        # Área de texto para transcripciones / análisis
        self.txt_output = tk.Text(self, height=8, state="disabled")
        self.txt_output.pack(fill="both", padx=10, pady=(10, 0), expand=True)

        # Progress bar de grabación
        self.progressbar = ttk.Progressbar(self, mode='indeterminate')

        # Botón principal
        self.btn_execute = tk.Button(self, text="Ejecutar", command=self.toggle_action,
                                     bg="#4CAF50", fg="white")
        self.btn_execute.pack(pady=20)

    def _update_mode(self):
        mode = self.mode.get()
        if mode == "convert":
            self.ext_label.pack(anchor="w", pady=(10, 0), padx=10)
            self.ext_entry.pack(fill="x", padx=10)
            self.ffmpeg_label.pack(anchor="w", pady=(10, 0), padx=10)
            self.ffmpeg_entry.pack(fill="x", padx=10)
        else:
            self.ext_label.pack_forget()
            self.ext_entry.pack_forget()
            self.ffmpeg_label.pack_forget()
            self.ffmpeg_entry.pack_forget()

        if mode == "video_analysis":
            self.chk_free_tier.pack(anchor="w", pady=(10, 0), padx=10)
            self.gemini_prompt_label.pack(anchor="w", pady=(10, 0), padx=10)
            self.gemini_prompt_entry.pack(fill="x", padx=10)
            self.chk_mic.pack_forget()
            self.use_mic.set(False)
        else:
            self.chk_free_tier.pack_forget()
            self.gemini_prompt_label.pack_forget()
            self.gemini_prompt_entry.pack_forget()
            self.chk_mic.pack(anchor="w", pady=(5, 0), padx=10)

        if mode == "transcribe" and self.use_mic.get():
            self.input_label.config(text="Grabación desde micrófono:")
            self.btn_select_input.config(state="disabled")
            self.btn_select_output.config(state="disabled")
            self.btn_execute.config(text="Iniciar")
        else:
            self.btn_select_input.config(state="normal")
            self.btn_select_output.config(state="normal")
            self.btn_execute.config(text="Ejecutar")
            if self.process_folder.get():
                self.input_label.config(text=("Carpeta de entrada:" if mode != "transcribe" else "Carpeta de audio:"))
                self.output_label.config(text="Carpeta de salida:")
            else:
                self.input_label.config(text="Archivo de entrada:")
                if mode == "convert":
                    self.output_label.config(text="Archivo de salida:")
                elif mode == "video_analysis":
                    self.output_label.config(text="Archivo de reporte (.txt):")
                else:
                    self.output_label.config(text="Archivo de texto de salida:")

    def select_input(self):
        if self.mode.get() == "transcribe" and self.use_mic.get(): return
        if self.process_folder.get():
            path = filedialog.askdirectory(title="Selecciona la carpeta de entrada")
        else:
            if self.mode.get() == "video_analysis":
                ftypes = [("Video files", "*.mp4 *.mpeg *.mov *.avi *.wmv *.webm *.flv"), ("All files", "*.*")]
            else:
                ftypes = [("Audio files", "*.opus *.mp3 *.wav *.aac *.flac *.m4a *.webm *.ogg *.amr *.mp4"),
                          ("All files", "*.*")]
            path = filedialog.askopenfilename(title="Selecciona el archivo de entrada", filetypes=ftypes)
        if path: self.input_path.set(path)

    def select_output(self):
        if self.mode.get() == "transcribe" and self.use_mic.get(): return
        if self.process_folder.get():
            path = filedialog.askdirectory(title="Selecciona la carpeta de salida")
        else:
            if self.mode.get() == "convert":
                path = filedialog.asksaveasfilename(
                    title="Selecciona la ruta de salida",
                    defaultextension=self.output_ext.get(),
                    filetypes=[("MP3", "*.mp3"), ("WAV", "*.wav"), ("All files", "*.*")]
                )
            else:
                path = filedialog.asksaveasfilename(
                    title="Selecciona la ruta de texto de salida",
                    defaultextension=".txt",
                    filetypes=[("Text", "*.txt"), ("All files", "*.*")]
                )
        if path: self.output_path.set(path)

    def toggle_action(self):
        if self.mode.get() == "transcribe" and self.use_mic.get():
            if not self.recording:
                self.start_recording()
            else:
                self.stop_recording_and_process()
        else:
            self.process_files()

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.recorded_frames.append(indata.copy())

    def start_recording(self):
        try:
            fs = 16000
            self.recorded_frames = []
            self.stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', callback=self.audio_callback)
            self.stream.start()
            self.recording = True
            self.btn_execute.config(text="Detener")
            self.progressbar.pack(fill='x', padx=10)
            self.progressbar.start(10)
        except Exception as e:
            messagebox.showerror("Error de grabación", str(e))

    def stop_recording_and_process(self):
        try:
            self.stream.stop()
            self.stream.close()
            self.recording = False
            self.btn_execute.config(text="Iniciar")
            self.progressbar.stop()
            self.progressbar.pack_forget()

            audio_data = np.concatenate(self.recorded_frames, axis=0)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wavfile.write(tmp.name, 16000, audio_data)
                audio_path = tmp.name

            text = self.processor.transcribe(audio_path)
            self._display_text(text)
            messagebox.showinfo("Éxito", "Transcripción completada desde micrófono.")

            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception as e:
            messagebox.showerror("Error de procesamiento", str(e))

    def _display_text(self, text):
        self.txt_output.config(state="normal")
        self.txt_output.delete("1.0", "end")
        self.txt_output.insert("1.0", text)
        self.txt_output.config(state="disabled")
        self.txt_output.see("end")

    def _log_to_gui(self, message):
        def _append():
            self.txt_output.config(state="normal")
            self.txt_output.insert("end", f"{message}\n")
            self.txt_output.config(state="disabled")
            self.txt_output.see("end")

        self.after(0, _append)

    def process_files(self):
        mode = self.mode.get()
        in_path = self.input_path.get()
        out_path = self.output_path.get().strip()
        api_key = self.api_key_free if self.use_free_tier.get() else self.api_key_paid

        if not in_path:
            messagebox.showerror("Error", "Selecciona ruta de entrada.")
            return

        if mode == "video_analysis" and not api_key:
            messagebox.showerror("Error",
                                 "La API Key de Google (Gratuita o Pago) no está configurada en las variables de entorno.")
            return

        if (mode != "transcribe" and mode != "video_analysis") or self.process_folder.get():
            if not out_path:
                messagebox.showerror("Error", "Selecciona ruta de salida.")
                return

        # Deshabilitar UI e iniciar hilo
        self.btn_execute.config(state="disabled")
        self.txt_output.config(state="normal")
        self.txt_output.delete("1.0", "end")
        self.txt_output.config(state="disabled")

        thread = threading.Thread(target=self._process_thread)
        thread.daemon = True
        thread.start()

    def _process_thread(self):
        mode = self.mode.get()
        in_path = self.input_path.get()
        out_path = self.output_path.get().strip()
        options = self.ffmpeg_options.get().split()
        ext = self.output_ext.get().strip()
        api_key = self.api_key_free if self.use_free_tier.get() else self.api_key_paid
        prompt = self.gemini_prompt_entry.get("1.0", "end-1c").strip()

        try:
            if self.process_folder.get():
                results = self.processor.process_folder(mode, in_path, out_path, options, ext, api_key, prompt,
                                                        callback=self._log_to_gui)
                self.after(0, lambda: messagebox.showinfo("Éxito", f"Procesamiento de carpeta completado:\n{out_path}"))
            else:
                if mode == "transcribe":
                    text = self.processor.transcribe(in_path)
                    if out_path:
                        dest = out_path if out_path.lower().endswith(".txt") else out_path + ".txt"
                        with open(dest, "w", encoding="utf-8") as f:
                            f.write(text)
                        self.after(0, lambda: messagebox.showinfo("Éxito", f"Transcripción completada:\n{dest}"))
                    else:
                        self.after(0, lambda: self._display_text(text))
                        self.after(0, lambda: messagebox.showinfo("Éxito", "Transcripción completada en pantalla."))
                elif mode == "video_analysis":
                    text = self.processor.analyze_video(in_path, api_key, prompt, callback=self._log_to_gui)

                    # Try to extract the suggested filename
                    suggested_base = os.path.splitext(os.path.basename(in_path))[0]
                    if text.startswith("SUGGESTED_FILENAME:"):
                        import re
                        name_line = text.split("\n", 1)[0]
                        extracted_name = name_line.replace("SUGGESTED_FILENAME:", "").strip()
                        sanitized_name = re.sub(r'[<>:"/\\|?*]', "", extracted_name)
                        if sanitized_name:
                            suggested_base = sanitized_name

                    if out_path:
                        # Si es una carpeta, usar el nombre sugerido. Si es un archivo, respetar la elección pero quizás sugerir cambiarlo (aunque aquí simplemente guardamos).
                        if os.path.isdir(out_path):
                            dest = os.path.join(out_path, suggested_base + ".md")
                        else:
                            # Si out_path ya es un archivo completo, lo usamos, pero aseguramos la extensión .md
                            dest = out_path if out_path.lower().endswith(".md") else out_path + ".md"

                        with open(dest, "w", encoding="utf-8") as f:
                            f.write(text)
                        self.after(0, lambda d=dest: messagebox.showinfo("Éxito", f"Análisis completado:\n{d}"))
                    else:
                        self.after(0, lambda: self._display_text(text))
                        self.after(0, lambda: messagebox.showinfo("Éxito", "Análisis completado en pantalla."))
                else:
                    self.processor.convert(in_path, out_path, options)
                    self.after(0, lambda: messagebox.showinfo("Éxito", f"Conversión completada:\n{out_path}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, lambda: self.btn_execute.config(state="normal"))
