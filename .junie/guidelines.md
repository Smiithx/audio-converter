# Project Development Guidelines

This document provides project-specific information for developers working on the Audio Converter & Transcriber.

## 1. Build and Configuration

### Requirements
- **Python 3.10+** (tested with 3.10.11)
- **FFmpeg**: Must be installed and available in the system `PATH`.
- **NVIDIA GPU (Optional but Recommended)**: For faster transcription with Whisper.

### Dependency Setup
Specific dependencies are required for GPU-accelerated transcription (Whisper).
1. **Install PyTorch with CUDA support** (Example for CUDA 11.8):
   ```bash
   pip install torch torchvision torchaudio --find-links https://download.pytorch.org/whl/nightly/cu118/torch_stable.html
   ```
2. **Install Whisper from source**:
   ```bash
   pip install git+https://github.com/openai/whisper.git
   ```
3. **Other dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 2. Testing Information

### Strategy
Since the application is a GUI built with `tkinter`, testing should focus on mocking the UI components and external processes (FFmpeg, Whisper).

### Running Tests
Use `pytest` or `unittest`. In headless or development environments, ensure dependencies like `sounddevice`, `numpy`, and `tkinter` are mocked if not fully configured.

### Example Test (Demonstration)
Create a file named `test_logic.py`:
```python
import unittest
from unittest.mock import MagicMock, patch
import sys

# Mocking GUI to run in headless environments
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['sounddevice'] = MagicMock()

import audio_converter_gui

class TestAudioConverter(unittest.TestCase):
    def test_audio_ext_list(self):
        """Verify the logic or simple presence of key components."""
        # Simple test to confirm the app structure is intact
        self.assertTrue(hasattr(audio_converter_gui, 'AudioConverterApp'))

if __name__ == '__main__':
    unittest.main()
```
Run it with:
```bash
python test_logic.py
```

## 3. Additional Development Information

### Code Style
- **Naming**: Use `snake_case` for methods and variables, and `PascalCase` for classes.
- **GUI structure**: Keep UI building logic in `_build_widgets` and event handlers separate.
- **Error Handling**: Always use `tkinter.messagebox` to report errors to the user, as it's a desktop application.

### Key Implementation Details
- **FFmpeg Integration**: The application uses `subprocess.run` with a list of arguments. Be careful when passing custom `ffmpeg_options` as they are split by spaces.
- **Whisper Model**: The `base` model is used by default. It's loaded only when needed and stays in memory for subsequent operations.
- **Audio Recording**: Uses `sounddevice` and `scipy.io.wavfile`. Ensure your system has a default input device configured.
