from transformers import pipeline
import torch
import librosa
import numpy as np

MODEL_NAME = "biodatlab/whisper-th-medium-timestamp"
lang = "th"
device = 0 if torch.cuda.is_available() else "cpu"

# Load audio using librosa instead of ffmpeg
def load_audio_with_librosa(file_path, target_sr=16000):
    """Load audio file using librosa and convert to the format expected by Whisper"""
    audio, sr = librosa.load(file_path, sr=target_sr, mono=True)
    return audio

pipe = pipeline(
    task="automatic-speech-recognition",
    model=MODEL_NAME,
    chunk_length_s=30,
    device=device,
    return_timestamps=True,
)
pipe.model.config.forced_decoder_ids = pipe.tokenizer.get_decoder_prompt_ids(
    language=lang,
    task="transcribe"
)

# Load audio file using librosa
audio_file = "./recordings/R1_Y1_math_Dr_Smith_20250702_231824.wav"
audio_data = load_audio_with_librosa(audio_file)

# Process with pipeline using numpy array instead of file path
result = pipe(audio_data, return_timestamps=True)
text, timestamps = result["text"], result["chunks"]

print("Transcribed text:", text)
print("Timestamps:", timestamps)