import customtkinter as ctk
import threading
import math
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import io
import wave
import time
from brain import JarvisBrain

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class JarvisGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("J.A.R.V.I.S")
        self.geometry("650x720")
        self.resizable(False, False)
        self.configure(fg_color="#050b14")

        self.jarvis = JarvisBrain()
        self.recognizer = sr.Recognizer()

        self._setup_ui()

        self.angle = 0
        self.current_state = "ready"
        self._animate_hud()

        threading.Thread(target=self._initial_greeting, daemon=True).start()

    def _setup_ui(self):
        self.hud_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.hud_frame.pack(pady=(15, 5), fill="both", expand=True)

        self.canvas = ctk.CTkCanvas(
            self.hud_frame, 
            width=480, 
            height=480, 
            bg="#050b14", 
            highlightthickness=0
        )
        self.canvas.pack(expand=True)

        self.status_label = ctk.CTkLabel(
            self,
            text="SISTEMA ONLINE",
            font=("Consolas", 12, "bold"),
            text_color="#00d2ff"
        )
        self.status_label.pack(pady=(0, 10))

        self.input_frame = ctk.CTkFrame(self, fg_color="#0a1526", corner_radius=15, border_width=1, border_color="#00d2ff")
        self.input_frame.pack(padx=30, pady=(0, 20), fill="x")

        self.mic_button = ctk.CTkButton(
            self.input_frame,
            text="🎙️",
            command=self.listen_voice_input,
            font=("Segoe UI", 16),
            fg_color="#003366",
            hover_color="#005580",
            text_color="#00d2ff",
            height=38,
            width=45,
            corner_radius=10
        )
        self.mic_button.pack(side="left", padx=(10, 5), pady=5)

        self.entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Instrua o J.A.R.V.I.S ou clique no microfone...",
            font=("Segoe UI", 12),
            fg_color="transparent",
            border_width=0,
            text_color="#00d2ff",
            placeholder_text_color="#005580",
            height=40
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=5)
        self.entry.bind("<Return>", lambda event: self.send_text_message())

        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="ENVIAR",
            command=self.send_text_message,
            font=("Consolas", 11, "bold"),
            fg_color="#003366",
            hover_color="#005580",
            text_color="#00d2ff",
            height=35,
            width=80,
            corner_radius=10
        )
        self.send_button.pack(side="right", padx=(5, 10), pady=5)

    def _draw_hud(self):
        self.canvas.delete("all")
        cx, cy = 240, 240

        if self.current_state == "listening":
            primary_color = "#ff0055"
            secondary_color = "#80002a"
        elif self.current_state == "thinking":
            primary_color = "#ff9900"
            secondary_color = "#ff6600"
        elif self.current_state == "speaking":
            primary_color = "#00ffcc"
            secondary_color = "#009977"
        else:
            primary_color = "#00d2ff"
            secondary_color = "#005580"

        r_ext = 200
        self.canvas.create_oval(cx - r_ext, cy - r_ext, cx + r_ext, cy + r_ext, outline=secondary_color, width=1)
        self.canvas.create_arc(cx - r_ext, cy - r_ext, cx + r_ext, cy + r_ext, start=self.angle, extent=80, outline=primary_color, width=3, style="arc")
        self.canvas.create_arc(cx - r_ext, cy - r_ext, cx + r_ext, cy + r_ext, start=self.angle + 120, extent=80, outline=primary_color, width=3, style="arc")
        self.canvas.create_arc(cx - r_ext, cy - r_ext, cx + r_ext, cy + r_ext, start=self.angle + 240, extent=80, outline=primary_color, width=3, style="arc")

        r_mid = 160
        self.canvas.create_oval(cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid, outline=secondary_color, width=2)
        
        num_ticks = 36
        for i in range(num_ticks):
            rad = math.radians(i * (360 / num_ticks) - self.angle)
            x1 = cx + (r_mid - 8) * math.cos(rad)
            y1 = cy + (r_mid - 8) * math.sin(rad)
            x2 = cx + r_mid * math.cos(rad)
            y2 = cy + r_mid * math.sin(rad)
            self.canvas.create_line(x1, y1, x2, y2, fill=primary_color, width=2)

        r_in = 120
        self.canvas.create_oval(cx - r_in, cy - r_in, cx + r_in, cy + r_in, outline=primary_color, width=2)
        self.canvas.create_arc(cx - r_in, cy - r_in, cx + r_in, cy + r_in, start=-self.angle * 2, extent=140, outline=primary_color, width=4, style="arc")
        self.canvas.create_arc(cx - r_in, cy - r_in, cx + r_in, cy + r_in, start=-self.angle * 2 + 180, extent=140, outline=primary_color, width=4, style="arc")

        r_core = 85
        self.canvas.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core, outline=primary_color, width=3)
        
        self.canvas.create_text(
            cx, cy, 
            text="J.A.R.V.I.S", 
            font=("Consolas", 20, "bold"), 
            fill=primary_color
        )

    def _animate_hud(self):
        speed = 5 if self.current_state in ["thinking", "listening"] else (3 if self.current_state == "speaking" else 1)
        self.angle = (self.angle + speed) % 360
        self._draw_hud()
        self.after(30, self._animate_hud)

    def set_state(self, state: str, status_text: str):
        self.current_state = state
        colors = {
            "listening": "#ff0055",
            "thinking": "#ff9900",
            "speaking": "#00ffcc",
            "ready": "#00d2ff"
        }
        self.status_label.configure(
            text=status_text,
            text_color=colors.get(state, "#00d2ff")
        )

    def _initial_greeting(self):
        self.set_state("thinking", "A GERAR DIAGNÓSTICO...")
        greeting = self.jarvis.generate_contextual_greeting()
        self.set_state("speaking", "A FALAR...")
        self.jarvis.speak(greeting)
        self.set_state("ready", "SISTEMA ONLINE")

    def listen_voice_input(self):
        if self.current_state != "ready":
            return
        threading.Thread(target=self._capture_audio_thread, daemon=True).start()

    def _capture_audio_thread(self):
        self.set_state("listening", "A OUVIR...")
        
        sample_rate = 16000
        chunk_duration = 0.1  # Bloco de 100ms
        chunk_samples = int(sample_rate * chunk_duration)
        
        silence_threshold = 500   # Sensibilidade ao volume da voz
        silence_limit = 1.2       # Segundos de silêncio para encerrar a frase automaticamente
        max_duration = 15         # Limite máximo total de fala
        
        recorded_chunks = []
        has_spoken = False
        silence_start = None
        start_time = time.time()

        try:
            with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
                while True:
                    data, _ = stream.read(chunk_samples)
                    recorded_chunks.append(data.copy())
                    
                    # Calcula o volume do áudio capturado
                    volume = np.abs(data).mean()
                    
                    if volume > silence_threshold:
                        has_spoken = True
                        silence_start = None  # Reseta o contador de silêncio se estiver a falar
                    elif has_spoken:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start >= silence_limit:
                            # Pausa detetada após a fala: encerra a gravação de forma limpa
                            break

                    # Limite de tempo máximo de segurança
                    if time.time() - start_time > max_duration:
                        break

            if not has_spoken or len(recorded_chunks) == 0:
                self.set_state("speaking", "NENHUMA FALA DETETADA")
                self.jarvis.speak("Não ouvi nenhuma instrução, Sr. Parker.")
                self.set_state("ready", "SISTEMA ONLINE")
                return

            self.set_state("thinking", "A TRANSCREVER...")

            audio_data = np.concatenate(recorded_chunks, axis=0)

            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())
            
            wav_buffer.seek(0)

            with sr.AudioFile(wav_buffer) as source:
                audio_file = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_file, language="pt-PT")
                print(f"[Voz Capturada]: {text}")
                
                self._process_response(text)

        except sr.UnknownValueError:
            self.set_state("speaking", "ÁUDIO NÃO RECONHECIDO")
            self.jarvis.speak("Não consegui compreender o áudio, Sr. Parker.")
            self.set_state("ready", "SISTEMA ONLINE")
        except Exception as e:
            print(f"[Erro na captura de voz: {e}]")
            self.set_state("ready", "SISTEMA ONLINE")

    def send_text_message(self):
        user_text = self.entry.get().strip()
        if not user_text or self.current_state != "ready":
            return

        self.entry.delete(0, "end")
        threading.Thread(target=self._process_response, args=(user_text,), daemon=True).start()

    def _process_response(self, user_text: str):
        self.set_state("thinking", "A PROCESSAR...")
        
        response = self.jarvis.ask(user_text)

        self.set_state("speaking", "A FALAR...")
        self.jarvis.speak(response)

        self.set_state("ready", "SISTEMA ONLINE")

if __name__ == "__main__":
    app = JarvisGUI()
    app.mainloop()