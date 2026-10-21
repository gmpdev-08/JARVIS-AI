import ollama
import random
import asyncio
import edge_tts
from playsound3 import playsound
import os
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

class JarvisBrain:
    def __init__(self, memory_file="memory.json"):
        self.memory_file = memory_file
        self.memory = self._load_memory()
        self.tz = ZoneInfo("Europe/Lisbon")

        self.system_prompt = self._build_system_prompt()
        self.history = [{"role": "system", "content": self.system_prompt}]

        self.voice = "pt-BR-AntonioNeural"

    def _load_memory(self) -> dict:
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Aviso de memória: Erro ao ler ficheiro - {e}]")
        return {"user_name": "Guilherme", "title": "Sr. Parker", "facts": []}

    def save_fact(self, fact: str):
        if "facts" not in self.memory:
            self.memory["facts"] = []
            
        if fact not in self.memory["facts"]:
            self.memory["facts"].append(fact)
            try:
                with open(self.memory_file, "w", encoding="utf-8") as f:
                    json.dump(self.memory, f, ensure_ascii=False, indent=2)
                
                self.system_prompt = self._build_system_prompt()
                self.history[0] = {"role": "system", "content": self.system_prompt}
                print(f"\n[Memória Atualizada: '{fact}']")
            except Exception as e:
                print(f"[Erro ao guardar memória: {e}]")

    def _get_weather_info(self) -> str:
        """Obtém o clima e localização aproximada sem necessidade de API key."""
        try:
            res = requests.get("https://wttr.in/Sao_Joao_da_Madeira?format=%C+%t", timeout=3)
            if res.status_code == 200:
                return f"Localização: São João da Madeira / Aveiro, Clima: {res.text.strip()}"
        except Exception:
            pass
        return "Localização: São João da Madeira, Portugal"

    def _build_system_prompt(self) -> str:
        facts_str = "\n".join([f"- {fact}" for fact in self.memory.get("facts", [])])
        memory_context = f"\nFACTOS CONHECIDOS SOBRE O SR. PARKER:\n{facts_str}" if facts_str else ""

        return (
            "És o JARVIS, um assistente virtual pessoal de elite e altamente inteligente, inspirado no mordomo digital de Tony Stark. "
            "Tratas o utilizador SEMPRE por 'senhor' ou 'Sr. Parker'. "
            "A tua personalidade é a de um mordomo britânico extremamente eficiente, refinado, seco e com uma pitada sutil de ironia inteligente. "
            "EVITA parecer excessivamente entusiasmado ou demasiado simpático/servil. Sê direto, inteligente e sarcástico na medida certa. "
            f"{memory_context}\n\n"
            "REGRAS DE CONVERSAÇÃO E NÃO-REPETIÇÃO:\n"
            "1. Não repitas informações de contexto (como clima, data ou boas-vindas) no meio da conversa. A saudação inicial já cumpriu esse papel.\n"
            "2. Responde de forma extremamente concisa, pragmática e elegante.\n"
            "3. RESPONDE 100% EM PORTUGUÊS.\n\n"
            "INSTRUÇÃO ESPECIAL DE MEMÓRIA:\n"
            "Se o utilizador te pedir para guardar ou lembrar uma informação, confirma com elegância e inclui no FINAL: [MEMORIA: texto do facto a guardar]."
        )

    def generate_contextual_greeting(self) -> str:
        """Gera uma saudação única e contextual baseada em tempo, clima e memória."""
        now = datetime.now(self.tz)
        dias_semana = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
        dia_str = dias_semana[now.weekday()]
        hora_str = now.strftime("%H:%M")
        clima = self._get_weather_info()

        prompt_saudacao = (
            f"Gera uma saudação inicial elegante e curta (máximo 2 frases) para o Sr. Parker.\n"
            f"Contexto Atual:\n"
            f"- Dia da semana: {dia_str}\n"
            f"- Horário exato: {hora_str}\n"
            f"- {clima}\n\n"
            f"Regras: Mencione subtilmente o dia, a hora ou o clima de forma elegante/irónica e pergunte como pode ajudar. Não use inglês."
        )

        try:
            response = ollama.chat(
                model='llama3',
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt_saudacao}
                ]
            )
            return response['message']['content'].strip()
        except Exception:
            return "Sistemas operacionais, Sr. Parker. Em que posso ser útil hoje?"

    async def _generate_and_play_audio(self, text: str):
        file_path = "speech.mp3"
        max_retries = 2

        for attempt in range(max_retries):
            try:
                communicate = edge_tts.Communicate(text, self.voice, rate="-3%")
                await communicate.save(file_path)

                playsound(file_path)

                if os.path.exists(file_path):
                    os.remove(file_path)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise e

    def speak(self, text: str):
        try:
            asyncio.run(self._generate_and_play_audio(text))
        except Exception as e:
            print(f"[Aviso de áudio: {e}]")

    def ask(self, user_input: str) -> str:
        # Injeta a data/hora exata de Portugal no contexto de cada pergunta
        now = datetime.now(self.tz)
        current_time_str = now.strftime("%H:%M de %d/%m/%Y")
        
        prompt_with_time = f"[Horário atual em São João da Madeira/Portugal: {current_time_str}]\nPerguntas do utilizador: {user_input}"

        self.history.append({"role": "user", "content": prompt_with_time})
        
        response = ollama.chat(model='llama3', messages=self.history)
        reply = response['message']['content']

        if "[MEMORIA:" in reply and "]" in reply:
            try:
                start = reply.find("[MEMORIA:") + len("[MEMORIA:")
                end = reply.find("]", start)
                fact_to_save = reply[start:end].strip()
                
                self.save_fact(fact_to_save)
                reply = reply[:reply.find("[MEMORIA:")].strip()
            except Exception as e:
                print(f"[Erro ao processar tag de memória: {e}]")

        self.history.append({"role": "assistant", "content": reply})
        return reply