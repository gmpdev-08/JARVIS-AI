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
from tools import SystemTools

class JarvisBrain:
    def __init__(self, memory_file="memory.json"):
        self.memory_file = memory_file
        self.memory = self._load_memory()
        self.tz = ZoneInfo("Europe/Lisbon")
        self.tools = SystemTools()

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
            except Exception as e:
                print(f"[Erro ao guardar memória: {e}]")

    def _get_weather_info(self) -> str:
        try:
            res = requests.get("https://wttr.in/Sao_Joao_da_Madeira?format=%C+%t", timeout=3)
            if res.status_code == 200:
                return f"Localização: São João da Madeira, Clima: {res.text.strip()}"
        except Exception:
            pass
        return "Localização: São João da Madeira, Portugal"

    def _build_system_prompt(self) -> str:
        facts_str = "\n".join([f"- {fact}" for fact in self.memory.get("facts", [])])
        memory_context = f"\nREPOSITÓRIO DE DADOS SOBRE O SR. PARKER:\n{facts_str}" if facts_str else ""

        return (
            "És o J.A.R.V.I.S., a inteligência artificial omnisciente e assistente pessoal de elite do Sr. Parker (Guilherme). "
            "Inspirado no mordomo digital de Tony Stark: extremamente sofisticado, incrivelmente perspicaz, articulado, elegante e com um toque sutil de sarcasmo refinado. "
            "Tratas o utilizador rigorosamente por 'Sr. Parker' ou 'senhor'. "
            "NUNCA soes robótico ou genérico. Mantém respostas inteligentes, fluidas, ricas em conteúdo e totalmente contextualizadas. "
            f"{memory_context}\n\n"
            "TAGS DE EXECUÇÃO DE SISTEMA (Injeta discreetamente quando necessário):\n"
            "1. Rotinas: [TOOL:ROUTINE: trabalho/cyber/gaming]\n"
            "2. Spotify: [TOOL:OPEN_APP: spotify nome_da_musica]\n"
            "3. Aplicação Generalizada: [TOOL:OPEN_APP: nome_da_app]\n"
            "4. Multimédia/Volume: [TOOL:MEDIA: play/next/prev/vol_up/vol_down/mute]\n"
            "5. Pesquisas Web: [TOOL:SEARCH_GOOGLE: termo] ou [TOOL:SEARCH_YOUTUBE: termo]\n"
            "6. Screenshot: [TOOL:SCREENSHOT]\n"
            "7. Análise Ficheiro Local: [TOOL:READ_FILE: nome_ficheiro]\n\n"
            "REGRAS PERMANENTES:\n"
            "1. Mantém a dicção refinada em Português europeu/neutro de elite.\n"
            "2. Responde com clareza cristalina, perspicácia e elegância verbal.\n"
            "3. Se o Sr. Parker te instruir a memorizar algo, responde com elegância e anexa no FINAL: [MEMORIA: facto a guardar]."
        )

    def generate_contextual_greeting(self) -> str:
        now = datetime.now(self.tz)
        dias_semana = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
        dia_str = dias_semana[now.weekday()]
        hora_str = now.strftime("%H:%M")
        clima = self._get_weather_info()

        prompt_saudacao = (
            f"Gera uma saudação tática e extremamente elegante (máximo 2 frases) para o Sr. Parker.\n"
            f"Dados Atuais:\n"
            f"- Dia: {dia_str}, Horário: {hora_str}\n"
            f"- {clima}\n\n"
            f"Exemplo de tom: 'Sistemas a 100%, Sr. Parker. O clima em São João da Madeira está favorável. Como posso ser-lhe útil nesta tarde?'"
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
            return "Todos os sistemas operacionais, Sr. Parker. Em que posso auxiliá-lo?"

    async def _generate_and_play_audio(self, text: str):
        file_path = "speech.mp3"
        max_retries = 2

        for attempt in range(max_retries):
            try:
                communicate = edge_tts.Communicate(text, self.voice, rate="-2%")
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

    def _execute_tools(self, reply: str) -> (str, str):
        tool_result = ""
        
        if "[TOOL:ROUTINE:" in reply:
            start = reply.find("[TOOL:ROUTINE:") + len("[TOOL:ROUTINE:")
            end = reply.find("]", start)
            mode = reply[start:end].strip()
            tool_result = self.tools.set_routine(mode)
            reply = reply[:reply.find("[TOOL:ROUTINE:")] + reply[end+1:]
        elif "[TOOL:OPEN_APP:" in reply:
            start = reply.find("[TOOL:OPEN_APP:") + len("[TOOL:OPEN_APP:")
            end = reply.find("]", start)
            app = reply[start:end].strip()
            tool_result = self.tools.open_app(app)
            reply = reply[:reply.find("[TOOL:OPEN_APP:")] + reply[end+1:]
        elif "[TOOL:MEDIA:" in reply:
            start = reply.find("[TOOL:MEDIA:") + len("[TOOL:MEDIA:")
            end = reply.find("]", start)
            act = reply[start:end].strip()
            tool_result = self.tools.media_control_async(act)
            reply = reply[:reply.find("[TOOL:MEDIA:")] + reply[end+1:]
        elif "[TOOL:SEARCH_GOOGLE:" in reply:
            start = reply.find("[TOOL:SEARCH_GOOGLE:") + len("[TOOL:SEARCH_GOOGLE:")
            end = reply.find("]", start)
            query = reply[start:end].strip()
            tool_result = self.tools.search_web(query, platform="google")
            reply = reply[:reply.find("[TOOL:SEARCH_GOOGLE:")] + reply[end+1:]
        elif "[TOOL:SEARCH_YOUTUBE:" in reply:
            start = reply.find("[TOOL:SEARCH_YOUTUBE:") + len("[TOOL:SEARCH_YOUTUBE:")
            end = reply.find("]", start)
            query = reply[start:end].strip()
            tool_result = self.tools.search_web(query, platform="youtube")
            reply = reply[:reply.find("[TOOL:SEARCH_YOUTUBE:")] + reply[end+1:]
        elif "[TOOL:SCREENSHOT]" in reply:
            tool_result = self.tools.take_screenshot()
            reply = reply.replace("[TOOL:SCREENSHOT]", "").strip()
        elif "[TOOL:READ_FILE:" in reply:
            start = reply.find("[TOOL:READ_FILE:") + len("[TOOL:READ_FILE:")
            end = reply.find("]", start)
            filename = reply[start:end].strip()
            tool_result = self.tools.read_local_file(filename)
            reply = reply[:reply.find("[TOOL:READ_FILE:")] + reply[end+1:]

        return reply.strip(), tool_result

    def ask(self, user_input: str) -> str:
        now = datetime.now(self.tz)
        current_time_str = now.strftime("%H:%M de %d/%m/%Y")
        
        prompt_with_time = f"[Horário atual em Portugal: {current_time_str}]\nInstrução do Sr. Parker: {user_input}"

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
                print(f"[Erro de memória: {e}]")

        clean_reply, tool_output = self._execute_tools(reply)

        if tool_output:
            final_response = f"{clean_reply} {tool_output}".strip()
        else:
            final_response = clean_reply

        self.history.append({"role": "assistant", "content": final_response})
        return final_response