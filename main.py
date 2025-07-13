import customtkinter as ctk
import pyaudio
import wave
import threading
from datetime import datetime
import os
import requests
import json
from voice import load_audio_with_librosa

class RecordingApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Audio Recording App")
        self.root.geometry("600x750")
        
        # Recording variables
        self.is_recording = False
        self.audio_frames = []
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1  # Changed to mono for better compatibility
        self.rate = 44100
        
        # Check audio devices on startup
        self.check_audio_devices()
        
        # Initialize data from API
        self.fetch_school_data()
        
        # Default subjects (fallback if API doesn't provide)
        self.subjects = ["math", "phy", "chem", "bio", "his", "thai", "eng", "com"]
        
        self.setup_ui()
        
    def fetch_school_data(self):
        """Fetch school data from API endpoint"""
        try:
            print("Fetching school data from API...")
            response = requests.get(
                "http://127.0.0.1:8690/school-data",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"API Response: {data}")
                
                # Check if system is available
                if data.get("data", {}).get("system_status") == "on":
                    # Extract room IDs (1 to room_length)
                    room_length = int(data["data"].get("room_length", 5))
                    self.room_ids = list(range(1, room_length + 1))
                    
                    # Extract year IDs (1 to year_length)
                    year_length = int(data["data"].get("year_length", 6))
                    self.year_ids = list(range(1, year_length + 1))
                    
                    # Extract teacher names
                    teachers = data["data"].get("teacher", [])
                    self.teacher_names = teachers if teachers else ["System Not Available"]
                    
                    print(f"Successfully loaded: {len(self.room_ids)} rooms, {len(self.year_ids)} years, {len(self.teacher_names)} teachers")
                else:
                    print("System status is off, using fallback data")
                    self.use_fallback_data()
            else:
                print(f"API returned status code: {response.status_code}")
                self.use_fallback_data()
                
        except requests.exceptions.RequestException as e:
            print(f"API Request failed: {e}")
            self.use_fallback_data()
        except Exception as e:
            print(f"Error parsing API response: {e}")
            self.use_fallback_data()
    
    def use_fallback_data(self):
        """Use fallback data when API is not available"""
        print("Using fallback data - System Not Available")
        self.room_ids = [1]
        self.year_ids = [1]
        self.teacher_names = ["System Not Available"]
        
    def check_audio_devices(self):
        """Check available audio devices and adjust settings"""
        try:
            device_count = self.audio.get_device_count()
            print(f"Found {device_count} audio devices:")
            
            default_input = None
            for i in range(device_count):
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    print(f"  Input Device {i}: {info['name']} - {info['maxInputChannels']} channels")
                    if default_input is None:
                        default_input = i
                        
            if default_input is not None:
                # Test with the default input device
                device_info = self.audio.get_device_info_by_index(default_input)
                if device_info['maxInputChannels'] == 1:
                    self.channels = 1
                else:
                    self.channels = min(2, device_info['maxInputChannels'])
                print(f"Using device: {device_info['name']} with {self.channels} channel(s)")
            else:
                print("No input devices found!")
                
        except Exception as e:
            print(f"Error checking audio devices: {e}")
            self.channels = 1  # Default to mono
        
    def setup_ui(self):
        # Main title
        title_label = ctk.CTkLabel(
            self.root, 
            text="Audio Recording System", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Recording controls frame
        controls_frame = ctk.CTkFrame(self.root)
        controls_frame.pack(pady=20, padx=20, fill="x")
        
        # Recording status
        self.status_label = ctk.CTkLabel(
            controls_frame, 
            text="Ready to Record", 
            font=ctk.CTkFont(size=16)
        )
        self.status_label.pack(pady=10)
        
        # Recording buttons
        buttons_frame = ctk.CTkFrame(controls_frame)
        buttons_frame.pack(pady=10)
        
        self.start_button = ctk.CTkButton(
            buttons_frame,
            text="Start Recording",
            command=self.start_recording,
            font=ctk.CTkFont(size=14),
            height=40,
            width=150
        )
        self.start_button.pack(side="left", padx=10)
        
        self.stop_button = ctk.CTkButton(
            buttons_frame,
            text="Stop Recording",
            command=self.stop_recording,
            font=ctk.CTkFont(size=14),
            height=40,
            width=150,
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=10)
        
        # Metadata frame (initially hidden)
        self.metadata_frame = ctk.CTkFrame(self.root)
        
        metadata_title = ctk.CTkLabel(
            self.metadata_frame,
            text="Recording Metadata",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        metadata_title.pack(pady=10)
        
        # Room ID dropdown
        room_frame = ctk.CTkFrame(self.metadata_frame)
        room_frame.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(room_frame, text="Room ID:", font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        self.room_var = ctk.StringVar(value=str(self.room_ids[0]) if self.room_ids else "1")
        self.room_dropdown = ctk.CTkComboBox(
            room_frame,
            values=[str(room) for room in self.room_ids] if self.room_ids else ["1"],
            variable=self.room_var,
            width=200
        )
        self.room_dropdown.pack(side="right", padx=10, pady=10)
        
        # Year ID dropdown
        year_frame = ctk.CTkFrame(self.metadata_frame)
        year_frame.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(year_frame, text="Year ID:", font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        self.year_var = ctk.StringVar(value=str(self.year_ids[0]) if self.year_ids else "1")
        self.year_dropdown = ctk.CTkComboBox(
            year_frame,
            values=[str(year) for year in self.year_ids] if self.year_ids else ["1"],
            variable=self.year_var,
            width=200
        )
        self.year_dropdown.pack(side="right", padx=10, pady=10)
        
        # Subject dropdown
        subject_frame = ctk.CTkFrame(self.metadata_frame)
        subject_frame.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(subject_frame, text="Subject:", font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        self.subject_var = ctk.StringVar(value=self.subjects[0])
        self.subject_dropdown = ctk.CTkComboBox(
            subject_frame,
            values=self.subjects,
            variable=self.subject_var,
            width=200
        )
        self.subject_dropdown.pack(side="right", padx=10, pady=10)
        
        # Teacher Name dropdown
        teacher_frame = ctk.CTkFrame(self.metadata_frame)
        teacher_frame.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(teacher_frame, text="Teacher Name:", font=ctk.CTkFont(size=12)).pack(side="left", padx=10)
        self.teacher_var = ctk.StringVar(value=self.teacher_names[0] if self.teacher_names else "System Not Available")
        self.teacher_dropdown = ctk.CTkComboBox(
            teacher_frame,
            values=self.teacher_names if self.teacher_names else ["System Not Available"],
            variable=self.teacher_var,
            width=200
        )
        self.teacher_dropdown.pack(side="right", padx=10, pady=10)
        
        # Save button
        save_button = ctk.CTkButton(
            self.metadata_frame,
            text="Save Recording",
            command=self.save_recording,
            font=ctk.CTkFont(size=14),
            height=40,
            width=200
        )
        save_button.pack(pady=20)
        
    def start_recording(self):
        """Start audio recording"""
        try:
            self.is_recording = True
            self.audio_frames = []
            
            # Try to find a working audio device configuration
            try:
                # Configure audio stream
                self.stream = self.audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk
                )
            except Exception as audio_error:
                # If stereo fails, try mono
                if self.channels == 2:
                    self.channels = 1
                    self.stream = self.audio.open(
                        format=self.format,
                        channels=self.channels,
                        rate=self.rate,
                        input=True,
                        frames_per_buffer=self.chunk
                    )
                else:
                    raise audio_error
            
            # Update UI
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.status_label.configure(text="Recording... 🔴")
            
            # Start recording thread
            self.recording_thread = threading.Thread(target=self.record_audio)
            self.recording_thread.start()
            
        except Exception as e:
            self.is_recording = False
            error_msg = str(e)
            if "Invalid number of channels" in error_msg:
                self.status_label.configure(text="Error: No compatible audio input device found")
            elif "Invalid sample rate" in error_msg:
                self.status_label.configure(text="Error: Audio device doesn't support 44100 Hz")
            else:
                self.status_label.configure(text=f"Error: {error_msg}")
            print(f"Audio error details: {e}")
            
    def record_audio(self):
        """Record audio in separate thread"""
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk)
                self.audio_frames.append(data)
            except Exception as e:
                print(f"Recording error: {e}")
                break
                
    def stop_recording(self):
        """Stop audio recording and show metadata form"""
        self.is_recording = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            
        # Update UI
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_label.configure(text="Recording Stopped - Please fill metadata")
        
        # Show metadata form
        self.metadata_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
    def save_recording(self):
        """Save the recording with metadata, transcribe, send to API, and clean up"""
        try:
            # Create recordings directory if it doesn't exist
            if not os.path.exists("recordings"):
                os.makedirs("recordings")
                
            # Generate filename with timestamp and metadata
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            room_id = self.room_var.get()
            year_id = self.year_var.get()
            subject = self.subject_var.get().replace(" ", "_")
            teacher = self.teacher_var.get().replace(" ", "_").replace(".", "")
            
            filename = f"recordings/R{room_id}_Y{year_id}_{subject}_{teacher}_{timestamp}.wav"
            
            # Update UI - processing
            self.status_label.configure(text="Processing recording...")
            
            # Save audio file
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.rate)
                wf.writeframes(b''.join(self.audio_frames))
                
            # Save metadata file
            metadata_filename = filename.replace('.wav', '_metadata.txt')
            with open(metadata_filename, 'w') as f:
                f.write(f"Recording Metadata\n")
                f.write(f"==================\n")
                f.write(f"Room ID: {room_id}\n")
                f.write(f"Year ID: {year_id}\n")
                f.write(f"Subject: {self.subject_var.get()}\n")
                f.write(f"Teacher Name: {self.teacher_var.get()}\n")
                f.write(f"Recording Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Audio File: {filename}\n")
            
            # Update UI - transcribing
            self.status_label.configure(text="Transcribing audio...")
            
            # Transcribe audio using the voice module
            try:
                transcribed_result = load_audio_with_librosa(filename)
                print(f"Raw transcription result type: {type(transcribed_result)}")
                print(f"Raw transcription result: {transcribed_result}")
                
                # Convert to string if it's a numpy array or other non-string type
                if hasattr(transcribed_result, 'tolist'):
                    transcribed_text = str(transcribed_result.tolist())
                elif isinstance(transcribed_result, dict) and 'text' in transcribed_result:
                    transcribed_text = str(transcribed_result['text'])
                else:
                    transcribed_text = str(transcribed_result)
                print(f"Transcribed text: {transcribed_text}")
            except Exception as e:
                print(f"Transcription error: {e}")
                transcribed_text = "Transcription failed"
            
            # Calculate recording duration
            recording_duration = len(self.audio_frames) * self.chunk / self.rate
            duration_formatted = f"{int(recording_duration//60):02d}:{int(recording_duration%60):02d}:00"
            
            # Prepare API payload with proper string formatting
            current_time = datetime.now()
            api_payload = {
                "content": {
                    "teacher_name": str(self.teacher_var.get()),
                    "teacher_subject": str(self.subject_var.get()),
                    "time_summit": current_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "time_of_record": duration_formatted,
                    "student_year": int(year_id),
                    "student_room": int(room_id),
                    "content": transcribed_text
                }
            }
            
            # Update UI - sending to API
            self.status_label.configure(text="Sending to API...")
            
            # Send to API
            try:
                response = requests.post(
                    "http://127.0.0.1:8690/add-document",
                    json=api_payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                if response.status_code == 200:
                    print("Successfully sent to API")
                    self.status_label.configure(text="Successfully sent to API")
                else:
                    print(f"API Error: {response.status_code} - {response.text}")
                    self.status_label.configure(text=f"API Error: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"API Request failed: {e}")
                self.status_label.configure(text=f"API Request failed: {str(e)}")
            
            # Clean up - delete recording files
            try:
                if os.path.exists(filename):
                    os.remove(filename)
                    print(f"Deleted audio file: {filename}")
                    
                if os.path.exists(metadata_filename):
                    os.remove(metadata_filename)
                    print(f"Deleted metadata file: {metadata_filename}")
                    
                self.status_label.configure(text="Recording processed and files cleaned up")
                
            except Exception as e:
                print(f"File cleanup error: {e}")
                self.status_label.configure(text="Recording processed but cleanup failed")
            
            # Hide metadata form
            self.metadata_frame.pack_forget()
            
        except Exception as e:
            self.status_label.configure(text=f"Save error: {str(e)}")
            print(f"Save recording error: {e}")
            
    def run(self):
        """Start the application"""
        self.root.mainloop()
        
    def __del__(self):
        """Cleanup audio resources"""
        if hasattr(self, 'audio'):
            self.audio.terminate()

if __name__ == "__main__":
    app = RecordingApp()
    app.run()