import customtkinter as ctk
import threading
import math
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import io
import wave
import time
import psutil
from datetime import datetime
from zoneinfo import ZoneInfo
from brain import JarvisBrain
from tools import SystemTools

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class JarvisGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("J.A.R.V.I.S — Tactical Command Center v3.0")
        self.geometry("1150x820")
        self.resizable(True, True)
        self.configure(fg_color="#030712")

        self.jarvis = JarvisBrain()
        self.recognizer = sr.Recognizer()
        self.tz = ZoneInfo("Europe/Lisbon")

        self.angle = 0
        self.current_state = "ready"

        self._setup_ui()
        self._animate_hud()
        self._update_telemetry()

        threading.Thread(target=self._initial_greeting, daemon=True).start()

    def _setup_ui(self):
        # Header / Barra Superior Sci-Fi
        self.header_frame = ctk.CTkFrame(self, fg_color="#0b132b", height=40, corner_radius=0)
        self.header_frame.pack(fill="x", side="top")

        self.title_lbl = ctk.CTkLabel(
            self.header_frame, 
            text="SYSTEM STATUS: ONLINE // TACTICAL CONTROL v3.0", 
            font=("Consolas", 11, "bold"), 
            text_color="#00d2ff"
        )
        self.title_lbl.pack(side="left", padx=20)

        self.time_lbl = ctk.CTkLabel(
            self.header_frame, 
            text="00:00:00", 
            font=("Consolas", 11, "bold"), 
            text_color="#00d2ff"
        )
        self.time_lbl.pack(side="right", padx=20)

        # Content Layout
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=15, pady=10)

        # Painel Esquerdo: Telemetria Completa & Métricas de Hardware
        self.left_panel = ctk.CTkFrame(self.main_container, fg_color="#080f21", border_width=1, border_color="#005580", width=240)
        self.left_panel.pack(side="left", fill="y", padx=(0, 10))

        ctk.CTkLabel(self.left_panel, text="[ TELEMETRIA DO SISTEMA ]", font=("Consolas", 12, "bold"), text_color="#00d2ff").pack(pady=(15, 10))
        
        self.location_lbl = ctk.CTkLabel(self.left_panel, text="LOC: S. João da Madeira", font=("Consolas", 10), text_color="#70a1ff", anchor="w")
        self.location_lbl.pack(fill="x", padx=15, pady=4)

        self.weather_lbl = ctk.CTkLabel(self.left_panel, text="CLIMA: Carregado", font=("Consolas", 10), text_color="#70a1ff", anchor="w")
        self.weather_lbl.pack(fill="x", padx=15, pady=4)

        self.facts_lbl = ctk.CTkLabel(self.left_panel, text=f"MEMÓRIAS: {len(self.jarvis.memory.get('facts', []))} factos", font=("Consolas", 10), text_color="#70a1ff", anchor="w")
        self.facts_lbl.pack(fill="x", padx=15, pady=4)

        # Separador Sci-Fi
        ctk.CTkFrame(self.left_panel, fg_color="#005580", height=1).pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(self.left_panel, text="[ RECURSOS DE HARDWARE ]", font=("Consolas", 11, "bold"), text_color="#00d2ff").pack(pady=(5, 5))

        self.cpu_lbl = ctk.CTkLabel(self.left_panel, text="CPU: 0%", font=("Consolas", 10), text_color="#00ffcc", anchor="w")
        self.cpu_lbl.pack(fill="x", padx=15, pady=2)
        self.cpu_bar = ctk.CTkProgressBar(self.left_panel, height=8, progress_color="#00ffcc", fg_color="#002244")
        self.cpu_bar.pack(fill="x", padx=15, pady=(0, 8))
        self.cpu_bar.set(0)

        self.ram_lbl = ctk.CTkLabel(self.left_panel, text="RAM: 0%", font=("Consolas", 10), text_color="#00ffcc", anchor="w")
        self.ram_lbl.pack(fill="x", padx=15, pady=2)
        self.ram_bar = ctk.CTkProgressBar(self.left_panel, height=8, progress_color="#00ffcc", fg_color="#002244")
        self.ram_bar.pack(fill="x", padx=15, pady=(0, 8))
        self.ram_bar.set(0)

        self.status_state_lbl = ctk.CTkLabel(self.left_panel, text="ESTADO: PRONTO", font=("Consolas", 10, "bold"), text_color="#00ffcc", anchor="w")
        self.status_state_lbl.pack(fill="x", padx=15, pady=15)

        # Painel Central: Arc Reactor HUD + Legendas
        self.center_panel = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.center_panel.pack(side="left", fill="both", expand=True)

        self.canvas = ctk.CTkCanvas(
            self.center_panel, 
            width=500, 
            height=480, 
            bg="#030712", 
            highlightthickness=0
        )
        self.canvas.pack(expand=True, pady=(0, 5))

        # Sub-Legendas Dinâmicas Sci-Fi
        self.subtitles_frame = ctk.CTkFrame(self.center_panel, fg_color="#080f21", border_width=1, border_color="#005580", corner_radius=10)
        self.subtitles_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.subtitle_lbl = ctk.CTkLabel(
            self.subtitles_frame, 
            text="J.A.R.V.I.S pronto para receber instruções, Sr. Parker.", 
            font=("Consolas", 11), 
            text_color="#00d2ff",
            wraplength=550,
            justify="center"
        )
        self.subtitle_lbl.pack(padx=15, pady=10)

        # Painel Direito: Controlo Tático & Multimédia
        self.right_panel = ctk.CTkFrame(self.main_container, fg_color="#080f21", border_width=1, border_color="#005580", width=260)
        self.right_panel.pack(side="right", fill="y", padx=(10, 0))

        ctk.CTkLabel(self.right_panel, text="[ ROTINAS TÁTICAS ]", font=("Consolas", 12, "bold"), text_color="#00d2ff").pack(pady=(15, 8))

        ctk.CTkButton(
            self.right_panel, text="💻 Dev & Code", 
            command=lambda: self._quick_action("Ativa o modo de trabalho"),
            font=("Consolas", 11, "bold"), fg_color="#003366", hover_color="#005580", text_color="#00d2ff"
        ).pack(fill="x", padx=15, pady=4)

        ctk.CTkButton(
            self.right_panel, text="🛡️ Cyber Security", 
            command=lambda: self._quick_action("Ativa a rotina cyber security"),
            font=("Consolas", 11, "bold"), fg_color="#003366", hover_color="#005580", text_color="#00d2ff"
        ).pack(fill="x", padx=15, pady=4)

        ctk.CTkButton(
            self.right_panel, text="🎮 Gaming Zone", 
            command=lambda: self._quick_action("Ativa o modo gaming"),
            font=("Consolas", 11, "bold"), fg_color="#003366", hover_color="#005580", text_color="#00d2ff"
        ).pack(fill="x", padx=15, pady=4)

        # Separador Sci-Fi
        ctk.CTkFrame(self.right_panel, fg_color="#005580", height=1).pack(fill="x", padx=15, pady=12)

        ctk.CTkLabel(self.right_panel, text="[ MULTIMÉDIA HUD ]", font=("Consolas", 12, "bold"), text_color="#00d2ff").pack(pady=(0, 8))

        # Frame de botões perfeitamente centralizado
        media_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        media_frame.pack(anchor="center", pady=4)

        ctk.CTkButton(media_frame, text="⏮️", width=42, height=32, command=lambda: SystemTools.media_control_async("prev"), fg_color="#002244", hover_color="#004477").pack(side="left", padx=3)
        ctk.CTkButton(media_frame, text="⏯️", width=42, height=32, command=lambda: SystemTools.media_control_async("play"), fg_color="#004477", hover_color="#0066aa").pack(side="left", padx=3)
        ctk.CTkButton(media_frame, text="⏭️", width=42, height=32, command=lambda: SystemTools.media_control_async("next"), fg_color="#002244", hover_color="#004477").pack(side="left", padx=3)
        ctk.CTkButton(media_frame, text="🔇", width=42, height=32, command=lambda: SystemTools.media_control_async("mute"), fg_color="#550000", hover_color="#880000").pack(side="left", padx=3)

        vol_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        vol_frame.pack(fill="x", padx=15, pady=8)

        ctk.CTkButton(vol_frame, text="🔊 Vol +", command=lambda: SystemTools.media_control_async("vol_up"), font=("Consolas", 10, "bold"), fg_color="#003366", hover_color="#005580").pack(side="left", expand=True, fill="x", padx=2)
        ctk.CTkButton(vol_frame, text="🔉 Vol -", command=lambda: SystemTools.media_control_async("vol_down"), font=("Consolas", 10, "bold"), fg_color="#003366", hover_color="#005580").pack(side="left", expand=True, fill="x", padx=2)

        # Separador Sci-Fi
        ctk.CTkFrame(self.right_panel, fg_color="#005580", height=1).pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(
            self.right_panel, text="📸 Capturar Ecrã", 
            command=lambda: self._quick_action("Tira um screenshot"),
            font=("Consolas", 11), fg_color="#002244", hover_color="#004477", text_color="#00d2ff"
        ).pack(fill="x", padx=15, pady=4)

        # Barra de Entrada Inferior
        self.input_frame = ctk.CTkFrame(self, fg_color="#080f21", corner_radius=12, border_width=1, border_color="#00d2ff")
        self.input_frame.pack(padx=20, pady=(0, 15), fill="x", side="bottom")

        self.mic_button = ctk.CTkButton(
            self.input_frame,
            text="🎙️",
            command=self.listen_voice_input,
            font=("Segoe UI", 16),
            fg_color="#003366",
            hover_color="#005580",
            text_color="#00d2ff",
            height=40,
            width=50,
            corner_radius=8
        )
        self.mic_button.pack(side="left", padx=(10, 5), pady=8)

        self.entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Instrua o J.A.R.V.I.S ou clique no microfone...",
            font=("Consolas", 12),
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
            height=36,
            width=90,
            corner_radius=8
        )
        self.send_button.pack(side="right", padx=(5, 10), pady=8)

    def update_subtitles(self, text: str):
        self.subtitle_lbl.configure(text=text)

    def _quick_action(self, text: str):
        if self.current_state != "ready":
            return
        threading.Thread(target=self._process_response, args=(text,), daemon=True).start()

    def _update_telemetry(self):
        now = datetime.now(self.tz)
        self.time_lbl.configure(text=now.strftime("%H:%M:%S | %d/%m/%Y"))
        
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent

        self.cpu_lbl.configure(text=f"CPU: {cpu_usage:.1f}%")
        self.cpu_bar.set(cpu_usage / 100.0)

        self.ram_lbl.configure(text=f"RAM: {ram_usage:.1f}%")
        self.ram_bar.set(ram_usage / 100.0)

        self.after(1000, self._update_telemetry)

    def _draw_hud(self):
        self.canvas.delete("all")
        cx, cy = 250, 240

        if self.current_state == "listening":
            primary_color = "#ff0055"
            secondary_color = "#660022"
        elif self.current_state == "thinking":
            primary_color = "#ff9900"
            secondary_color = "#663d00"
        elif self.current_state == "speaking":
            primary_color = "#00ffcc"
            secondary_color = "#006652"
        else:
            primary_color = "#00d2ff"
            secondary_color = "#004080"

        # Anel Exterior
        r_ext = 210
        self.canvas.create_oval(cx - r_ext, cy - r_ext, cx + r_ext, cy + r_ext, outline=secondary_color, width=1)
        self.canvas.create_arc(cx - r_ext, cy - r_ext, cx + r_ext, cy + r_ext, start=self.angle, extent=60, outline=primary_color, width=3, style="arc")
        self.canvas.create_arc(cx - r_ext, cy - r_ext, cx + r_ext, cy + r_ext, start=self.angle + 120, extent=60, outline=primary_color, width=3, style="arc")
        self.canvas.create_arc(cx - r_ext, cy - r_ext, cx + r_ext, cy + r_ext, start=self.angle + 240, extent=60, outline=primary_color, width=3, style="arc")

        # Anel de Marcações
        r_mid = 165
        self.canvas.create_oval(cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid, outline=secondary_color, width=1)
        num_ticks = 48
        for i in range(num_ticks):
            rad = math.radians(i * (360 / num_ticks) - self.angle)
            x1 = cx + (r_mid - 10) * math.cos(rad)
            y1 = cy + (r_mid - 10) * math.sin(rad)
            x2 = cx + r_mid * math.cos(rad)
            y2 = cy + r_mid * math.sin(rad)
            self.canvas.create_line(x1, y1, x2, y2, fill=primary_color, width=1)

        # Anel Interno
        r_in = 120
        self.canvas.create_oval(cx - r_in, cy - r_in, cx + r_in, cy + r_in, outline=secondary_color, width=2)
        self.canvas.create_arc(cx - r_in, cy - r_in, cx + r_in, cy + r_in, start=-self.angle * 2, extent=100, outline=primary_color, width=4, style="arc")
        self.canvas.create_arc(cx - r_in, cy - r_in, cx + r_in, cy + r_in, start=-self.angle * 2 + 180, extent=100, outline=primary_color, width=4, style="arc")

        # Núcleo Central
        r_core = 80
        self.canvas.create_oval(cx - r_core, cy - r_core, cx + r_core, cy + r_core, outline=primary_color, width=2)

        # Texto Central
        self.canvas.create_text(
            cx, cy, 
            text="J.A.R.V.I.S", 
            font=("Consolas", 20, "bold"), 
            fill=primary_color
        )

    def _animate_hud(self):
        speed = 4 if self.current_state in ["thinking", "listening"] else (2 if self.current_state == "speaking" else 1)
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
        color = colors.get(state, "#00d2ff")
        self.status_state_lbl.configure(text=f"ESTADO: {status_text}", text_color=color)

    def _initial_greeting(self):
        self.set_state("thinking", "DIAGNÓSTICO...")
        greeting = self.jarvis.generate_contextual_greeting()
        self.update_subtitles(greeting)
        self.set_state("speaking", "A FALAR...")
        self.jarvis.speak(greeting)
        self.set_state("ready", "PRONTO")

    def listen_voice_input(self):
        if self.current_state != "ready":
            return
        threading.Thread(target=self._capture_audio_thread, daemon=True).start()

    def _capture_audio_thread(self):
        self.set_state("listening", "A OUVIR...")
        
        sample_rate = 16000
        chunk_duration = 0.1
        chunk_samples = int(sample_rate * chunk_duration)
        
        silence_threshold = 500
        silence_limit = 1.2
        max_duration = 15
        
        recorded_chunks = []
        has_spoken = False
        silence_start = None
        start_time = time.time()

        try:
            with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16') as stream:
                while True:
                    data, _ = stream.read(chunk_samples)
                    recorded_chunks.append(data.copy())
                    
                    volume = np.abs(data).mean()
                    
                    if volume > silence_threshold:
                        has_spoken = True
                        silence_start = None
                    elif has_spoken:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start >= silence_limit:
                            break

                    if time.time() - start_time > max_duration:
                        break

            if not has_spoken or len(recorded_chunks) == 0:
                self.set_state("speaking", "SEM ÁUDIO")
                no_audio_msg = "Não ouvi nenhuma instrução, Sr. Parker."
                self.update_subtitles(no_audio_msg)
                self.jarvis.speak(no_audio_msg)
                self.set_state("ready", "PRONTO")
                return

            self.set_state("thinking", "TRANSCREVENDO...")

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
                self.update_subtitles(f"Instrução: \"{text}\"")
                self._process_response(text)

        except sr.UnknownValueError:
            self.set_state("speaking", "NÃO ENTENDIDO")
            err_msg = "Não consegui compreender o áudio, Sr. Parker."
            self.update_subtitles(err_msg)
            self.jarvis.speak(err_msg)
            self.set_state("ready", "PRONTO")
        except Exception as e:
            print(f"[Erro de captura: {e}]")
            self.set_state("ready", "PRONTO")

    def send_text_message(self):
        user_text = self.entry.get().strip()
        if not user_text or self.current_state != "ready":
            return

        self.entry.delete(0, "end")
        self.update_subtitles(f"Instrução: \"{user_text}\"")
        threading.Thread(target=self._process_response, args=(user_text,), daemon=True).start()

    def _process_response(self, user_text: str):
        self.set_state("thinking", "PROCESSANDO...")
        
        response = self.jarvis.ask(user_text)

        self.facts_lbl.configure(text=f"MEMÓRIAS: {len(self.jarvis.memory.get('facts', []))} factos")
        self.update_subtitles(response)

        self.set_state("speaking", "A FALAR...")
        self.jarvis.speak(response)

        self.set_state("ready", "PRONTO")

if __name__ == "__main__":
    app = JarvisGUI()
    app.mainloop()