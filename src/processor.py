import os
from src.interfaces import TranscriberProvider, ConverterProvider, VideoAnalyzerProvider

class MediaProcessor:
    def __init__(self, transcriber: TranscriberProvider, converter: ConverterProvider, analyzer: VideoAnalyzerProvider = None):
        self.transcriber = transcriber
        self.converter = converter
        self.analyzer = analyzer

    def transcribe(self, audio_path):
        return self.transcriber.transcribe(audio_path)

    def convert(self, in_path, out_path, options=None):
        return self.converter.convert(in_path, out_path, options)

    def analyze_video(self, video_path, api_key, prompt, model_name=None, callback=None):
        if not self.analyzer:
            raise ValueError("Analizador de video no configurado.")
        return self.analyzer.analyze_video(video_path, api_key, prompt, model_name, callback=callback)

    def process_folder(self, mode, in_dir, out_dir, options=None, output_ext=".mp3", api_key=None, prompt=None, callback=None):
        audio_exts = (".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".mpga", ".opus", ".flac", ".webm", ".ogg", ".amr")
        video_exts = (".mp4", ".mpeg", ".mov", ".avi", ".wmv", ".webm", ".flv")
        
        if not os.path.isdir(in_dir) or not os.path.isdir(out_dir):
            raise ValueError("Carpeta de entrada/salida inválida.")

        files_to_process = []
        for root, _, files in os.walk(in_dir):
            for file in files:
                if mode == "transcribe" and file.lower().endswith(audio_exts):
                    files_to_process.append((root, file))
                elif mode == "video_analysis" and file.lower().endswith(video_exts):
                    files_to_process.append((root, file))
                elif mode == "convert" and file.lower().endswith(audio_exts):
                    files_to_process.append((root, file))

        total_files = len(files_to_process)
        results = []
        
        for i, (root, file) in enumerate(files_to_process, 1):
            src = os.path.join(root, file)
            base = os.path.splitext(os.path.basename(file))[0]
            
            if callback:
                callback(f"Procesando {i} de {total_files}: {file}...")

            if mode == "transcribe":
                dest = os.path.join(out_dir, base + ".txt")
                text = self.transcribe(src)
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(text)
                results.append(dest)
            elif mode == "video_analysis":
                # El método analyze_video de MediaProcessor ya maneja la obtención del modelo del entorno si se pasa None
                text = self.analyze_video(src, api_key, prompt, callback=callback)
                
                # Try to extract the suggested name from the first line: SUGGESTED_FILENAME: [Name]
                suggested_base = base
                if text.startswith("SUGGESTED_FILENAME:"):
                    name_line = text.split("\n", 1)[0]
                    extracted_name = name_line.replace("SUGGESTED_FILENAME:", "").strip()
                    if extracted_name:
                        # Remove invalid characters for Windows filenames
                        import re
                        sanitized_name = re.sub(r'[<>:"/\\|?*]', "", extracted_name)
                        if sanitized_name:
                            suggested_base = sanitized_name
                
                dest = os.path.join(out_dir, suggested_base + ".md")
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(text)
                results.append(dest)
            elif mode == "convert":
                dest = os.path.join(out_dir, base + output_ext)
                self.convert(src, dest, options)
                results.append(dest)
        return results
