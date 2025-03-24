import os
import json
import requests
from uuid import uuid4 as u4
from ojitos369_postgres_db.postgres_db import ConexionPostgreSQL
from ojitos369.utils import printwln as pln

DB_DATA = {
    "host": "localhost",
    "user": "llmemory",
    "password": "Contra12345$",
    "name": "llmemory",
    "port": "5436",
}
class LLMemory:
    def __init__(self):
        self.create_conexion()
        self.link = "http://localhost:11434/api/generate"
        self.model = "gemma3:1b"
        self.conversacion = []

    def __del__(self):
        self.close_conexion()
        self.kill_ollama()
    
    def kill_ollama(self):
        os.system(f"ollama stop {self.model}")

    def create_conexion(self):
        self.close_conexion()
        self.conexion = ConexionPostgreSQL(DB_DATA)
        self.conexion.mode = "dict"

    def close_conexion(self):
        try:
            self.conexion.close()
        except:
            pass
    
    def stream_responses(self, data, print_response = False):
        response = requests.post(self.link, json=data, stream=True)
        if print_response:
            print(response)

        for line in response.iter_lines():
            if line:
                yield line.decode('utf-8')
    
    def get_response(self, prompt, print_response = True, memory_option = False):
        self.kill_ollama()
        instrucciones = "Tu eres llmemory, solo daras la respuesta, los roles los manejo por fuera\n"
        if memory_option:
            instrucciones += "Hay acceso a la memoria de los chats. Si quieres acceder a la base de datos solo responde \"Requiero Memoria\". Trata de no hacerlo, solo en caso que sea muy requerido\n"
        data = {
            "model": self.model,
            "prompt": f"{instrucciones}Prompt: {prompt}"
        }

        pensamiento = ""
        respuesta = ""
        pensando = False
        if print_response:
            pln("promting")
        for response in self.stream_responses(data, print_response=print_response):
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
        msg = self.save_message('user', prompt)
        self.conversacion.append(
            {"tipo_usuario": "user", "mensaje": str(msg)}
        )
        self.conversacion.append(
            { "tipo_usuario": "llmemory", "mensaje": ""}
        )
        pensamiento, respuesta = self.get_response(str(self.conversacion), print_response = True, memory_option = True)
        if "requiero memoria" in respuesta.lower():
            self.conversacion.pop()
            self.conversacion.pop()
            self.conversacion.append(
                {"tipo_usuario": "user", "mensaje": str(msg)}
            )
            memorias = self.upgrade_memory()
            if memorias:
                self.conversacion.append(
                    {"tipo_usuario": "user", "mensaje": str(msg)}
                )
            self.conversacion.append(
                { "tipo_usuario": "llmemory", "mensaje": ""}
            )
            pensamiento, respuesta = self.get_response(str(self.conversacion), print_response = True)
        msg = self.save_message('llmemory', respuesta, pensamiento)
        self.conversacion[-1]["mensaje"] = str(msg)
        return pensamiento, respuesta

    def upgrade_memory(self):
        pln("Actualizando memoria")
        historial = str(self.conversacion)
        palabras = self.extraer_palabras(historial)
        pln("palabras de memoria: ", palabras)
        query = """select *
                    from mensajes
                    where id_mensaje in (select distinct ms.id_mensaje
                    from mensajes ms
                    inner join uniones un on ms.id_mensaje = un.mensaje_id
                    and un.palabra in (%s))
                    order by fecha_mensaje"""
        data = tuple(palabras)
        mensajes = self.conexion.consulta_asociativa(query, data)
        added = 0
        pln("Mensajes: ", len(mensajes))
        if mensajes:
            prompt = f"Conversacion actual: {historial}\n"
            prompt += f"Memoria: {str(mensajes)}\n"
            prompt += f"En base a la conversacion actual, revisa que mensajes son relevantes de la memoria para la conversacion y regresame el id de los mensajes separados por coma: id1, id2, ..., idn\n"
            pensamiento, respuesta = self.get_response(prompt)
            pln("ids raw", respuesta)
            ids = respuesta.replace("\n", ", ").replace(" ", "").split(",")
            ids = [id for id in ids if id != ""]
            ids = [id for id in ids if id != " "]
            pln("id clean", ids)
            
            query = """select *
                        from mensajes
                        where id_mensaje in (%s)"""
            data = tuple(ids)
            mensajes = self.conexion.consulta_asociativa(query, data)
            for mensaje in mensajes:
                added += 1
                tipo_usuario = mensaje["tipo_usuario"]
                self.conversacion.append(
                    {"tipo_usuario": tipo_usuario, "mensaje": str(mensaje)}
                )
        return added

    def extraer_palabras(self, to_extract):
        promt = "Dame una lista de palabras que engloben lo importante del mensaje asi como sinonimos para facilitar la localizacion de las memorias\n"
        promt += "Ejemplo: Esta tarde comí sopa con arroz y pollo\n"
        promt += "Tu respuesta sería:\n"
        promt += "tarde, comer, sopa, arroz, pollo, alimento, ingerir, comi\n"
        promt += "Solo una vez cada palabra (dia, dia, dia) -> (dia). Las palabras no deben tener acentos ni caracteres especiales. Solo regresaras la lista de palabras, nada mas, son formato ni nada solo palabras separadas por \",\"\n\n\n"
        promt += "Para Extraer:\n"
        promt += to_extract
        pensamiento, respuesta = self.get_response(promt)
        remplazos = {
            "á": "a",
            "é": "e",
            "í": "i",
            "ó": "o",
            "ú": "u"
        }
        pln("Palabras Raw: ", respuesta)
        palabras = respuesta.replace(", ", ",").replace("\n", ",").lower()
        for o, r in remplazos.items():
            palabras = palabras.replace(o, r)
        palabras = respuesta.split(",")
        palabras = [palabra.strip() for palabra in palabras]
        palabras = list(set(palabras))
        palabras = [palabra for palabra in palabras if palabra != ""]
        palabras = [palabra for palabra in palabras if palabra != " "]
        pln("Palabras: ", palabras)
        return palabras
    
    def save_message(self, tipo_usuario, mensaje, pensamiento = None):
        id = str(u4())
        query = """INSERT INTO mensajes
                    (id_mensaje, fecha_mensaje, tipo_usuario, pensamiento, mensaje)
                    VALUES (%s, now(), %s, %s, %s)"""
        data = (id, tipo_usuario, pensamiento, mensaje)
        self.conexion.ejecutar(query, data)
        self.conexion.commit()
        self.save_palabras(mensaje, id)
        query = """SELECT fecha_mensaje, tipo_usuario, pensamiento, mensaje FROM mensajes WHERE id_mensaje = %s"""
        data = (id,)
        mensaje = self.conexion.consulta_asociativa(query, data)
        return mensaje[0]

    def save_palabras(self, mensaje, id):
        palabras = self.extraer_palabras(mensaje)
        
        for palabra in palabras:
            query = """INSERT INTO uniones
                        (id_union, mensaje_id, palabra)
                        VALUES (%s, %s, %s)"""
            data = (str(u4()), id, palabra)
            self.conexion.ejecutar(query, data)
            self.conexion.commit()


def main():
    os.system("clear")
    llm = LLMemory()
    while True:
        mensaje = input("Mensaje: ")
        p, r = llm.consultar(mensaje)
        pln("Pensamiento: ", p)
        pln("Respuesta: ", r)
        pln("\n\n")


if __name__ == "__main__":
    main()
