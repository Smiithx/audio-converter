from abc import ABC, abstractmethod

class TranscriberProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path):
        pass

class ConverterProvider(ABC):
    @abstractmethod
    def convert(self, in_path, out_path, options=None):
        pass

class VideoAnalyzerProvider(ABC):
    @abstractmethod
    def analyze_video(self, video_path, api_key, prompt, model_name="gemini-1.5-flash", callback=None):
        pass
