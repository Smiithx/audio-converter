import argparse
import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from src.gui import AudioConverterApp
from src.processor import MediaProcessor
from src.providers import WhisperTranscriber, FFmpegConverter, GeminiVideoAnalyzer

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audio Converter & Transcriber")
    parser.add_argument("--mode", choices=["convert", "transcribe", "video_analysis"], help="Modo de operación")
    parser.add_argument("--input", help="Ruta de archivo o carpeta de entrada")
    parser.add_argument("--output", help="Ruta de archivo o carpeta de salida")
    parser.add_argument("--folder", action="store_true", help="Procesar carpeta completa")
    parser.add_argument("--options", default="-y", help="Opciones adicionales para ffmpeg (ej. '-b:a 192k')")
    parser.add_argument("--ext", default=".mp3", help="Extensión de salida para conversión de carpetas")
    parser.add_argument("--key", help="API Key de Google para análisis de video (por defecto usa GOOGLE_API_KEY de .env)")
    parser.add_argument("--prompt", help="Prompt para análisis de video")

    args = parser.parse_args()

    # Obtener API Key y nombre del modelo de los argumentos o del entorno
    google_api_key = args.key or os.getenv("GOOGLE_API_KEY", "")
    gemini_model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite-preview")

    if args.mode:
        # Modo CLI
        processor = MediaProcessor(
            transcriber=WhisperTranscriber(),
            converter=FFmpegConverter(),
            analyzer=GeminiVideoAnalyzer()
        )
        try:
            if args.folder:
                print(f"Procesando carpeta: {args.input} -> {args.output}")
                processor.process_folder(args.mode, args.input, args.output, args.options.split(), args.ext, google_api_key, args.prompt)
            else:
                if args.mode == "transcribe":
                    print(f"Transcribiendo: {args.input}")
                    text = processor.transcribe(args.input)
                elif args.mode == "video_analysis":
                    if not google_api_key:
                        print("Error: Se requiere API Key (vía --key o .env).")
                        sys.exit(1)
                    print(f"Analizando video ({gemini_model_name}): {args.input}")
                    text = processor.analyze_video(args.input, google_api_key, args.prompt or "Haz un resumen de este video.", gemini_model_name)
                
                if args.mode in ["transcribe", "video_analysis"]:
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
        app = AudioConverterApp(google_api_key=google_api_key)
        app.mainloop()
