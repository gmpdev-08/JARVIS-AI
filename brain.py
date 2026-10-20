import ollama
import random
import asyncio
import edge_tts
from playsound3 import playsound
import os
import json

class JarvisBrain:
    def __init__(self, memory_file="memory.json"):
        self.memory_file = memory_file
        self.memory = self._load_memory()

        self.system_prompt = self._build_system_prompt()
        self.history = [{"role": "system", "content": self.system_prompt}]

        self.greetings = [
            "Sistemas operacionais, senhor. Em que posso ser útil hoje?",
            "Todos os sistemas online, Sr. Parker. À sua inteira disposição.",
            "Diagnóstico concluído, senhor. Pronto para os desafios do dia.",
            "Sistemas prontos e a funcionar a cem por cento, Sr. Parker. Qual é o plano?",
            "Ao seu dispor, senhor. Por onde gostaria de começar hoje?",
            "Módulos primários ativos, Sr. Parker. Como posso ajudar?"
        ]

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

    def _build_system_prompt(self) -> str:
        facts_str = "\n".join([f"- {fact}" for fact in self.memory.get("facts", [])])
        memory_context = f"\nFACTOS CONHECIDOS SOBRE O SR. PARKER:\n{facts_str}" if facts_str else ""

        return (
            "És o JARVIS, um assistente virtual pessoal de elite e altamente inteligente, inspirado no mordomo digital de Tony Stark. "
            "Tratas o utilizador SEMPRE por 'senhor' ou 'Sr. Parker'. "
            "A tua personalidade é uma mistura refinada de mordomo britânico dedicado, eficiência técnica exemplar e uma pitada sutil de ironia fina e bom humor. "
            "Conheces o teu criador profundamente e demonstras proximidade e lealdade. "
            f"{memory_context}\n\n"
            "INSTRUÇÃO ESPECIAL DE MEMÓRIA:\n"
            "Se o utilizador te pedir explicitamente para guardar ou lembrar uma informação, "
            "deves responder confirmando de forma elegante e incluir no FINAL da tua resposta a tag estrita: [MEMORIA: texto do facto a guardar].\n\n"
            "REGRAS CRÍTICAS DE IDIOMA E ESTILO:\n"
            "1. RESPONDE 100% EM PORTUGUÊS. É ESTRITAMENTE PROIBIDO USAR INGLÊS.\n"
            "2. Usa 'senhor' ou 'Sr. Parker' para o tratamento formal.\n"
            "3. Sê extremamente conciso, direto e eficiente nas respostas.\n"
            "4. Nunca quebres a personagem em momento algum."
        )

    def get_random_greeting(self) -> str:
        return random.choice(self.greetings)

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
                    await asyncio.sleep(1) # Aguarda 1 segundo antes de tentar novamente
                else:
                    raise e

    def speak(self, text: str):
        try:
            asyncio.run(self._generate_and_play_audio(text))
        except Exception as e:
            print(f"[Aviso de áudio: Falha na ligação de rede ao gerar voz - {e}]")

    def ask(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})
        
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