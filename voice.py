from transformers import pipeline
import torch
import librosa
import numpy as np

MODEL_NAME = "biodatlab/whisper-th-medium-timestamp"
lang = "thai"
device = 0 if torch.cuda.is_available() else "cpu"

# Initialize pipeline globally to avoid reloading
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

def load_audio_with_librosa(file_path, target_sr=16000):
    """Load audio file using librosa and transcribe it using Whisper"""
    try:
        # Load audio file
        audio, sr = librosa.load(file_path, sr=target_sr, mono=True)
        
        # Process with pipeline using numpy array instead of file path
        result = pipe(audio, return_timestamps=True)
        
        # Return just the text
        return result["text"]
        
    except Exception as e:
        print(f"Error in load_audio_with_librosa: {e}")
        return f"Transcription failed: {str(e)}"