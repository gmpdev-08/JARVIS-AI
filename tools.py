import os
import subprocess
import webbrowser
import urllib.parse
from datetime import datetime
import pyautogui
import time
import threading

class SystemTools:
    @staticmethod
    def _open_spotify(query: str = None):
        """Abre o Spotify e força a reprodução da faixa ou pesquisa solicitada."""
        try:
            if query:
                encoded_query = urllib.parse.quote(query)
                os.system(f"start spotify:search:{encoded_query}")
                time.sleep(2.0)
                pyautogui.press("enter")
                time.sleep(0.5)
                pyautogui.press("space")
            else:
                os.system("start spotify:")
                time.sleep(1.5)
                pyautogui.press("playpause")
        except Exception:
            webbrowser.open("https://open.spotify.com")

    @staticmethod
    def media_control_async(action: str):
        """Executa comandos multimédia numa thread separada para não bloquear a GUI."""
        def _exec():
            action_lower = action.lower()
            if "play" in action_lower or "pause" in action_lower or "tocar" in action_lower:
                pyautogui.press("playpause")
            elif "next" in action_lower or "proxima" in action_lower or "avançar" in action_lower:
                pyautogui.press("nexttrack")
            elif "prev" in action_lower or "anterior" in action_lower or "recuar" in action_lower:
                pyautogui.press("prevtrack")
            elif "vol_up" in action_lower or "aumentar" in action_lower:
                for _ in range(4):
                    pyautogui.press("volumeup")
            elif "vol_down" in action_lower or "baixar" in action_lower:
                for _ in range(4):
                    pyautogui.press("volumedown")
            elif "mute" in action_lower or "silenciar" in action_lower:
                pyautogui.press("volumemute")

        threading.Thread(target=_exec, daemon=True).start()
        return "Comando multimédia processado."

    @staticmethod
    def open_app(app_name: str) -> str:
        app_name_lower = app_name.lower()
        
        if "vscode" in app_name_lower or "vs code" in app_name_lower:
            subprocess.Popen("code", shell=True)
            return "Visual Studio Code operacional, Sr. Parker."
        elif "spotify" in app_name_lower:
            clean_query = app_name_lower.replace("spotify", "").replace("tocar", "").replace("toca", "").replace("música", "").strip()
            if clean_query:
                threading.Thread(target=SystemTools._open_spotify, args=(clean_query,), daemon=True).start()
                return f"A procurar e reproduzir '{clean_query}' no Spotify."
            else:
                threading.Thread(target=SystemTools._open_spotify, daemon=True).start()
                return "Spotify iniciado."
        elif "browser" in app_name_lower or "chrome" in app_name_lower or "navegador" in app_name_lower:
            webbrowser.open("https://www.google.com")
            return "Navegador aberto."
        elif "cmd" in app_name_lower or "terminal" in app_name_lower:
            os.system("start cmd")
            return "Terminal de comandos pronto."
        else:
            try:
                os.system(f"start {app_name}")
                return f"A iniciar {app_name}."
            except Exception:
                return f"Não foi possível localizar {app_name}."

    @staticmethod
    def set_routine(mode: str) -> str:
        mode_lower = mode.lower()
        if "work" in mode_lower or "trabalho" in mode_lower or "code" in mode_lower:
            current_dir = os.getcwd()
            subprocess.Popen(f'code "{current_dir}"', shell=True)
            threading.Thread(target=SystemTools._open_spotify, args=("Lo-Fi Beats",), daemon=True).start()
            return "Ambiente de desenvolvimento configurado, Sr. Parker. VS Code e frequência Lo-Fi ativos."
        elif "cyber" in mode_lower or "estudo" in mode_lower or "tryhackme" in mode_lower:
            webbrowser.open("https://tryhackme.com")
            os.system("start cmd")
            return "Protocolo de cibersegurança iniciado. TryHackMe e consola ativos."
        elif "gaming" in mode_lower or "jogo" in mode_lower:
            threading.Thread(target=SystemTools._open_spotify, daemon=True).start()
            return "Modo tático de entretenimento ativado."
        return "Rotina desconhecida."

    @staticmethod
    def search_web(query: str, platform: str = "google") -> str:
        encoded_query = urllib.parse.quote(query)
        if "youtube" in platform.lower():
            webbrowser.open(f"https://www.youtube.com/results?search_query={encoded_query}")
            return f"Pesquisa enviada ao YouTube: '{query}'."
        else:
            webbrowser.open(f"https://www.google.com/search?q={encoded_query}")
            return f"Pesquisa enviada ao Google: '{query}'."

    @staticmethod
    def take_screenshot() -> str:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            pyautogui.screenshot(filename)
            return f"Captura de ecrã registada: {filename}."
        except Exception as e:
            return f"Falha na captura: {e}"

    @staticmethod
    def read_local_file(filepath: str) -> str:
        if not os.path.exists(filepath):
            return f"Ficheiro '{filepath}' não encontrado."
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read(2000)
                return f"Ficheiro {filepath} analisado:\n\n{content}"
        except Exception as e:
            return f"Erro na análise: {e}"