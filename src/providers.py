import subprocess
import time
import torch
import os
import tempfile

try:
    import whisper
except ImportError:
    whisper = None

try:
    from google import genai
except ImportError:
    genai = None

from src.interfaces import TranscriberProvider, ConverterProvider, VideoAnalyzerProvider

class WhisperTranscriber(TranscriberProvider):
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

class FFmpegConverter(ConverterProvider):
    def convert(self, in_path, out_path, options=None):
        if options is None:
            options = ["-y"]
        cmd = ["ffmpeg"] + options + ["-i", in_path, out_path]
        subprocess.run(cmd, check=True)

class GeminiVideoAnalyzer(VideoAnalyzerProvider):
    def analyze_video(self, video_path, api_key, prompt, model_name=None, callback=None):
        if genai is None:
            raise ImportError("El paquete 'google-genai' no está instalado.")

        def log(msg):
            if callback:
                callback(msg)
            else:
                print(msg)

        # Obtener el nombre del modelo desde el entorno si no se proporciona
        if model_name is None:
            model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite-preview")

        # El nuevo SDK usa un cliente en lugar de configuración global
        client = genai.Client(api_key=api_key)

        temp_video_path = None
        try:
            # Pre-procesamiento con FFmpeg (NVIDIA NVENC)
            log("Comprimiendo video con la GPU (RTX NVENC)...")
            temp_video_path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
            
            cmd = [
                "ffmpeg", "-hwaccel", "cuda", "-i", video_path, 
                "-vf", "scale=-2:720", "-r", "1", 
                "-c:v", "h264_nvenc", "-preset", "fast", 
                "-c:a", "aac", "-b:a", "64k", 
                "-y", temp_video_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)

            # Subida del archivo (usando el temporal comprimido)
            log(f"Subiendo video comprimido: {temp_video_path}...")
            video_file = client.files.upload(file=temp_video_path)
            log(f"Estado inicial de la subida: {video_file.state.name}")

            # Bucle para esperar a que el estado pase de PROCESSING a ACTIVE
            while video_file.state.name == "PROCESSING":
                log("Esperando a que el video termine de procesarse en Google Cloud...")
                time.sleep(10)
                video_file = client.files.get(name=video_file.name)

            if video_file.state.name == "FAILED":
                raise ValueError("La subida del video falló en los servidores de Google.")

            # Generación de contenido con el nuevo formato
            log("Iniciando análisis de contenido con Gemini...")
            response = client.models.generate_content(
                model=model_name,
                contents=[video_file, prompt]
            )

            # Eliminación del archivo del servidor
            log("Análisis finalizado. Procediendo a borrar el archivo del servidor...")
            client.files.delete(name=video_file.name)

            return response.text

        finally:
            # Eliminación del video temporal local
            if temp_video_path and os.path.exists(temp_video_path):
                log("Limpiando archivos temporales...")
                os.remove(temp_video_path)