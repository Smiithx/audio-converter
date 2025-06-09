import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import os
import tempfile

try:
    import whisper
except ImportError:
    whisper = None

# Dependencias para grabación por micrófono
import sounddevice as sd
import scipy.io.wavfile as wavfile
import numpy as np
import torch

class AudioConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Audio Converter & Transcriber")
        self.geometry("600x500")
        self.resizable(False, False)

        # Variables de estado
        self.mode = tk.StringVar(value="transcribe")  # "convert" o "transcribe"
        self.process_folder = tk.BooleanVar(value=False)
        self.use_mic = tk.BooleanVar(value=False)
        self.recording = False
        self.recorded_frames = []
        self.stream = None

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.ffmpeg_options = tk.StringVar(value="-y")
        self.output_ext = tk.StringVar(value=".mp3")

        # Configuración de modelo Whisper
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # compute_type: usar FP16 en GPU, FP32 en CPU
        self.compute_type = "float16" if self.device == "cuda" else "float32"
        self.model = None

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

        # Procesar carpeta
        tk.Checkbutton(self, text="Procesar carpeta", variable=self.process_folder,
                       command=self._update_mode).pack(anchor="w", pady=(10, 0), padx=10)
        # Usar micrófono
        tk.Checkbutton(self, text="Usar micrófono", variable=self.use_mic,
                       command=self._update_mode).pack(anchor="w", pady=(5, 0), padx=10)

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

        # Área de texto para transcripciones
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
        # Mostrar u ocultar config de conversión
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

        # Ajustar etiquetas y controles
        if mode == "transcribe" and self.use_mic.get():
            self.input_label.config(text="Grabación desde micrófono:")
            self.btn_select_input.config(state="disabled")
            self.btn_select_output.config(state="disabled")
            self.btn_execute.config(text="Iniciar")
        else:
            # habilitar selección
            self.btn_select_input.config(state="normal")
            self.btn_select_output.config(state="normal")
            # texto botón
            self.btn_execute.config(text="Ejecutar")
            # etiquetas rutas
            if self.process_folder.get():
                self.input_label.config(text=("Carpeta de entrada:" if mode == "convert" else "Carpeta de audio:"))
                self.output_label.config(text="Carpeta de salida:")
            else:
                self.input_label.config(text="Archivo de entrada:")
                self.output_label.config(text=("Archivo de salida:" if mode == "convert" else "Archivo de texto de salida:"))

    def select_input(self):
        if self.mode.get()=="transcribe" and self.use_mic.get(): return
        if self.process_folder.get():
            path = filedialog.askdirectory(title="Selecciona la carpeta de entrada")
        else:
            path = filedialog.askopenfilename(
                title="Selecciona el archivo de entrada",
                filetypes=[("Audio files", "*.opus *.mp3 *.wav *.aac *.flac *.m4a *.webm *.ogg *.amr *.mp4"),
                           ("All files", "*.*")]
            )
        if path: self.input_path.set(path)

    def select_output(self):
        if self.mode.get()=="transcribe" and self.use_mic.get(): return
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
        # Decide entre grabar o procesar archivos
        if self.mode.get()=="transcribe" and self.use_mic.get():
            if not self.recording:
                self.start_recording()
            else:
                self.stop_recording_and_process()
        else:
            self.process_files()

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status)
        # almacenar copia de datos
        self.recorded_frames.append(indata.copy())

    def start_recording(self):
        try:
            fs = 16000
            self.recorded_frames = []
            self.stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', callback=self.audio_callback)
            self.stream.start()
            self.recording = True
            self.btn_execute.config(text="Detener")
            # animación de grabación
            self.progressbar.pack(fill='x', padx=10)
            self.progressbar.start(10)
        except Exception as e:
            messagebox.showerror("Error de grabación", str(e))

    def stop_recording_and_process(self):
        try:
            # detener grabación
            self.stream.stop()
            self.stream.close()
            self.recording = False
            self.btn_execute.config(text="Iniciar")
            self.progressbar.stop()
            self.progressbar.pack_forget()

            # combinar frames y guardar WAV temporal
            audio_data = np.concatenate(self.recorded_frames, axis=0)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wavfile.write(tmp.name, 16000, audio_data)
                audio_path = tmp.name

            # cargar modelo si es necesario
            if whisper is None:
                messagebox.showerror("Error", "El paquete 'whisper' no está instalado.")
                return
            if self.model is None:
                self.model = whisper.load_model("base", device=self.device, compute_type=self.compute_type)

            # transcribir
            result = self.model.transcribe(audio_path)
            text = result.get("text", "")

            # mostrar en UI
            self.txt_output.config(state="normal")
            self.txt_output.delete("1.0", "end")
            self.txt_output.insert("1.0", text)
            self.txt_output.config(state="disabled")
            messagebox.showinfo("Éxito", "Transcripción completada desde micrófono.")
        except Exception as e:
            messagebox.showerror("Error de procesamiento", str(e))

    def process_files(self):
        mode = self.mode.get()
        in_path = self.input_path.get()
        out_path = self.output_path.get()
        options = self.ffmpeg_options.get().split()
        ext = self.output_ext.get().strip()

        if not in_path or not out_path:
            messagebox.showerror("Error", "Selecciona rutas de entrada y salida.")
            return

        if mode == "transcribe" and whisper is None:
            messagebox.showerror("Error", "El paquete 'whisper' no está instalado.")
            return

        audio_exts = (".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".mpga", ".opus", ".flac", ".webm", ".ogg", ".amr")

        if mode == "transcribe":
            if self.model is None:
                self.model = whisper.load_model("base", device=self.device, compute_type=self.compute_type)
            if self.process_folder.get():
                if not os.path.isdir(in_path) or not os.path.isdir(out_path):
                    messagebox.showerror("Error", "Carpeta de entrada/salida inválida.")
                    return
                for root, _, files in os.walk(in_path):
                    for file in files:
                        if not file.lower().endswith(audio_exts):
                            continue
                        src = os.path.join(root, file)
                        base = os.path.splitext(file)[0]
                        dest = os.path.join(out_path, base + ".txt")
                        try:
                            result = self.model.transcribe(src)
                            with open(dest, "w", encoding="utf-8") as f:
                                f.write(result["text"] or "")
                        except Exception as e:
                            messagebox.showerror("Error de transcripción", f"No se pudo procesar '{src}':\n{e}")
                            return
                messagebox.showinfo("Éxito", f"Transcripción de carpeta completada:\n{out_path}")
            else:
                if not os.path.isfile(in_path):
                    messagebox.showerror("Error", "Archivo de entrada no existe.")
                    return
                base = os.path.splitext(os.path.basename(in_path))[0]
                dest = out_path if out_path.lower().endswith(".txt") else out_path + ".txt"
                try:
                    result = self.model.transcribe(in_path)
                    with open(dest, "w", encoding="utf-8") as f:
                        f.write(result["text"] or "")
                    messagebox.showinfo("Éxito", f"Transcripción completada:\n{dest}")
                except Exception as e:
                    messagebox.showerror("Error de transcripción", f"No se pudo procesar el archivo:\n{e}")
        else:
            if self.process_folder.get():
                if not os.path.isdir(in_path) or not os.path.isdir(out_path):
                    messagebox.showerror("Error", "Carpeta de entrada/salida inválida.")
                    return
                for root, _, files in os.walk(in_path):
                    for file in files:
                        if not file.lower().endswith(audio_exts):
                            continue
                        src = os.path.join(root, file)
                        base = os.path.splitext(os.path.basename(file))[0]
                        dest = os.path.join(out_path, base + ext)
                        cmd = ["ffmpeg"] + options + ["-i", src, dest]
                        try:
                            subprocess.run(cmd, check=True)
                        except subprocess.CalledProcessError as e:
                            messagebox.showerror("Error de ffmpeg", f"Error al convertir '{src}':\n{e}")
                            return
                messagebox.showinfo("Éxito", f"Conversión de carpeta completada:\n{out_path}")
            else:
                if not os.path.isfile(in_path):
                    messagebox.showerror("Error", "Archivo de entrada no existe.")
                    return
                cmd = ["ffmpeg"] + options + ["-i", in_path, out_path]
                try:
                    subprocess.run(cmd, check=True)
                    messagebox.showinfo("Éxito", f"Conversión completada:\n{out_path}")
                except subprocess.CalledProcessError as e:
                    messagebox.showerror("Error de ffmpeg", f"Ocurrió un error:\n{e}")

if __name__ == "__main__":
    app = AudioConverterApp()
    app.mainloop()
