import os
import json
import requests
from uuid import uuid4 as u4
from ojitos369.utils import printwln as pln
class LLMemory:
    def __init__(self):
        # os.system("curl https://tfgsccw6-11434.use2.devtunnels.ms")
        self.link = "http://localhost:11434/api/generate"
        # self.link = "https://tfgsccw6-11434.use2.devtunnels.ms/api/generate"
        # self.link = "http://192.168.82.55:11434/api/generate"
        self.model = "gemma3:4b"
        # self.model = "qwen2.5:3b"
        # self.model = "deepseek-r1:1.5b"
        self.conversacion = []

    def __del__(self):
        self.kill_ollama()
    
    def kill_ollama(self):
        os.system(f"ollama stop {self.model}")
    
    def stream_responses(self, data):
        response = requests.post(self.link, json=data, stream=True)
        # print("response")
        # print(response)
        try:
            for line in response.iter_lines():
                if line:
                    yield line.decode('utf-8')
        except Exception as e:
            print(f"Error in stream_responses: {e}")
            rs = json.loads(response)
            pln(rs)
    
    def get_response(self, prompt, print_response = True):
        self.kill_ollama()
        instrucciones = "Tu eres llmemory, solo daras la respuesta, los roles los manejo por fuera\n"
        data = {
            "model": self.model,
            "prompt": f"{instrucciones}Prompt: {prompt}"
        }

        pensamiento = ""
        respuesta = ""
        pensando = False
        for response in self.stream_responses(data):
            rs = json.loads(response)
            try:
                done = rs["done"]
            except Exception as e:
                pln(rs)
                raise e

            if not done:
                message = rs["response"]
                if "<think>" in message:
                    if print_response:
                        print("pensando: ")
                    pensando = True
                    message = message.replace("<think>", "").replace("\n", "")
                
                if not pensando:
                    respuesta += message

                if "</think>" in message:
                    pensando = False
                    message = message.replace("</think>", "").replace("\n", "")
                    pensamiento += message
                    if print_response:
                        print(message, end="")
                        print(f"\n{'-'*50}")
                        print(f"Respondiendo:")
                else:
                    if print_response:
                        print(message, end="")
                if pensando:
                    pensamiento += message
        self.kill_ollama()
        return pensamiento, respuesta

    def consultar(self, prompt):
        self.conversacion.append(
            {"tipo_usuario": "user", "mensaje": prompt}
        )
        self.conversacion.append(
            { "tipo_usuario": "llmemory", "mensaje": ""}
        )
        pensamiento, respuesta = self.get_response(str(self.conversacion), print_response = True)

        self.conversacion[-1]["mensaje"] = str(respuesta)
        return pensamiento, respuesta


def main():
    os.system("clear")
    llm = LLMemory()
    while True:
        mensaje = input(">: ")
        p, r = llm.consultar(mensaje)
        # pln("Pensamiento: ", p)
        # pln("Respuesta: ", r)
        # pln("\n\n")


if __name__ == "__main__":
    main()
