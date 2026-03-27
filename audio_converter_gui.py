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
import argparse
import sys

import warnings

# --- Lógica de Procesamiento ---

class AudioProcessor:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None

    def _ensure_model(self):
        if self.model is None:
            if whisper is None:
                raise ImportError("El paquete 'whisper' no está instalado.")
            self.model = whisper.load_model("base", device=self.device)

    def transcribe(self, audio_path):
        self._ensure_model()
        result = self.model.transcribe(audio_path)
        return result.get("text", "")

    def convert(self, in_path, out_path, options=None):
        if options is None:
            options = ["-y"]
        cmd = ["ffmpeg"] + options + ["-i", in_path, out_path]
        subprocess.run(cmd, check=True)

    def process_folder(self, mode, in_dir, out_dir, options=None, output_ext=".mp3"):
        audio_exts = (".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".mpga", ".opus", ".flac", ".webm", ".ogg", ".amr")
        if not os.path.isdir(in_dir) or not os.path.isdir(out_dir):
            raise ValueError("Carpeta de entrada/salida inválida.")

        results = []
        for root, _, files in os.walk(in_dir):
            for file in files:
                if not file.lower().endswith(audio_exts):
                    continue
                src = os.path.join(root, file)
                base = os.path.splitext(os.path.basename(file))[0]
                
                if mode == "transcribe":
                    dest = os.path.join(out_dir, base + ".txt")
                    text = self.transcribe(src)
                    with open(dest, "w", encoding="utf-8") as f:
                        f.write(text)
                    results.append(dest)
                else:
                    dest = os.path.join(out_dir, base + output_ext)
                    self.convert(src, dest, options)
                    results.append(dest)
        return results

# --- Interfaz Gráfica ---

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

        # Configuración de dispositivo para Whisper
        self.processor = AudioProcessor()

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
                self.output_label.config(
                    text=("Archivo de salida:" if mode == "convert" else "Archivo de texto de salida:"))

    def select_input(self):
        if self.mode.get() == "transcribe" and self.use_mic.get(): return
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
        # Decide entre grabar o procesar archivos
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

            # Guardar WAV temporal
            audio_data = np.concatenate(self.recorded_frames, axis=0)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wavfile.write(tmp.name, 16000, audio_data)
                audio_path = tmp.name

            text = self.processor.transcribe(audio_path)

            self.txt_output.config(state="normal")
            self.txt_output.delete("1.0", "end")
            self.txt_output.insert("1.0", text)
            self.txt_output.config(state="disabled")
            messagebox.showinfo("Éxito", "Transcripción completada desde micrófono.")
            
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception as e:
            messagebox.showerror("Error de procesamiento", str(e))

    def process_files(self):
        mode = self.mode.get()
        in_path = self.input_path.get()
        out_path = self.output_path.get().strip()
        options = self.ffmpeg_options.get().split()
        ext = self.output_ext.get().strip()

        if not in_path:
            messagebox.showerror("Error", "Selecciona ruta de entrada.")
            return

        if mode != "transcribe" or self.process_folder.get():
            if not out_path:
                messagebox.showerror("Error", "Selecciona ruta de salida.")
                return

        try:
            if self.process_folder.get():
                self.processor.process_folder(mode, in_path, out_path, options, ext)
                messagebox.showinfo("Éxito", f"Procesamiento de carpeta completado:\n{out_path}")
            else:
                if mode == "transcribe":
                    text = self.processor.transcribe(in_path)
                    if out_path:
                        dest = out_path if out_path.lower().endswith(".txt") else out_path + ".txt"
                        with open(dest, "w", encoding="utf-8") as f:
                            f.write(text)
                        messagebox.showinfo("Éxito", f"Transcripción completada:\n{dest}")
                    else:
                        self.txt_output.config(state="normal")
                        self.txt_output.delete("1.0", "end")
                        self.txt_output.insert("1.0", text)
                        self.txt_output.config(state="disabled")
                        messagebox.showinfo("Éxito", "Transcripción completada en pantalla.")
                else:
                    self.processor.convert(in_path, out_path, options)
                    messagebox.showinfo("Éxito", f"Conversión completada:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio Converter & Transcriber")
    parser.add_argument("--mode", choices=["convert", "transcribe"], help="Modo de operación")
    parser.add_argument("--input", help="Ruta de archivo o carpeta de entrada")
    parser.add_argument("--output", help="Ruta de archivo o carpeta de salida")
    parser.add_argument("--folder", action="store_true", help="Procesar carpeta completa")
    parser.add_argument("--options", default="-y", help="Opciones adicionales para ffmpeg (ej. '-b:a 192k')")
    parser.add_argument("--ext", default=".mp3", help="Extensión de salida para conversión de carpetas")

    args = parser.parse_args()

    if args.mode:
        # Modo CLI
        processor = AudioProcessor()
        try:
            if args.folder:
                print(f"Procesando carpeta: {args.input} -> {args.output}")
                processor.process_folder(args.mode, args.input, args.output, args.options.split(), args.ext)
            else:
                if args.mode == "transcribe":
                    print(f"Transcribiendo: {args.input}")
                    text = processor.transcribe(args.input)
                    if args.output:
                        dest = args.output if args.output.lower().endswith(".txt") else args.output + ".txt"
                        with open(dest, "w", encoding="utf-8") as f:
                            f.write(text)
                        print(f"Guardado en: {dest}")
                    else:
                        print("-" * 20)
                        print(text)
                        print("-" * 20)
                else:
                    print(f"Convirtiendo: {args.input} -> {args.output}")
                    processor.convert(args.input, args.output, args.options.split())
            print("Operación completada con éxito.")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Modo GUI
        app = AudioConverterApp()
        app.mainloop()
