import datetime
import getpass
import time

from spade import quit_spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message

finalizou = False

def define_expressao_reduzida(pos_operador: int):
    global expressao
    expressao_reduzida = ''
    
    aux = pos_operador - 1                # procurando para a esquerda do operador
    while expressao[aux].isnumeric():
        expressao_reduzida += expressao[aux]
        aux -= 1
        
        if aux < 0:
            break
    
    expressao_reduzida = expressao_reduzida[::-1] + expressao[pos_operador]
    
    aux = pos_operador + 1                # procurando para a direita do operador
    while expressao[aux].isnumeric():
        expressao_reduzida += expressao[aux]
        aux += 1
        
        if aux > len(expressao) - 1:
            break
    
    return expressao_reduzida


class Gerente(Agent):
    class InformBehav(PeriodicBehaviour):
        async def run(self):
            global expressao, finalizou
            
            pos_operador = 0
            destino_msg = ''
            
            print(f'\n{expressao}\n')
            
            if expressao.find('*') != -1:
                destino_msg = 'agente_multiplicacao'
                pos_operador = expressao.find('*')
            elif expressao.find('/') != -1:
                destino_msg = 'agente_divisao'
                pos_operador = expressao.find('/')
            elif expressao.find('+') != -1:
                destino_msg = 'agente_soma'
                pos_operador = expressao.find('+')
            elif expressao.find('-') != -1:
                destino_msg = 'agente_subtracao'
                pos_operador = expressao.find('-')
                
            msg = Message(to=self.get(destino_msg))
            msg.body = define_expressao_reduzida(pos_operador)
            
            await self.send(msg)
            print(f"[gerente] -> enviando {msg.body} para [{destino_msg}]")
      
            msg_resposta = await self.receive(timeout=10)             # receptor de mensagens
            expressao = expressao.replace(msg.body, msg_resposta.body)

            if expressao.isnumeric() or expressao[0] == '-':
                print(f'\nResposta = {expressao}')
                finalizou = True
                self.kill()
                
        async def on_end(self):
            await self.agent.stop()                    # stop agent from behaviour

    async def setup(self):
        print(f"[gerente] -> iniciando...")
        start_at = datetime.datetime.now() + datetime.timedelta(seconds=3)
        self.add_behaviour(self.InformBehav(period=2, start_at=start_at))


class AgenteSoma(Agent):        
    class RecvBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            
            if msg:
                operandos = msg.body.split('+')
                msg_resposta = Message(to="gerente@lightwitch.org")     # Instantiate the message
                msg_resposta.body = str(int(operandos[0]) + int(operandos[1]))
                
                print(f'[agente_soma] -> enviando {msg_resposta.body} para [gerente]')
                
                await self.send(msg_resposta)
                
        async def on_end(self):
            await self.agent.stop()

    async def setup(self):
        print("[agente_soma] -> iniciando...")
        self.add_behaviour(self.RecvBehav())


class AgenteSubtracao(Agent):        
    class RecvBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            
            if msg:
                operandos = msg.body.split('-')
                msg_resposta = Message(to="gerente@lightwitch.org")     # Instantiate the message
                msg_resposta.body = str(int(operandos[0]) - int(operandos[1]))
                
                print(f'[agente_subtracao] -> enviando {msg_resposta.body} para [gerente]')
                
                await self.send(msg_resposta)
                
        async def on_end(self):
            await self.agent.stop()

    async def setup(self):
        print("[agente_subtracao] -> iniciando...")
        self.add_behaviour(self.RecvBehav())


class AgenteMultiplicacao(Agent):        
    class RecvBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            
            if msg:
                operandos = msg.body.split('*')
                msg_resposta = Message(to="gerente@lightwitch.org")     # Instantiate the message
                msg_resposta.body = str(int(operandos[0]) * int(operandos[1]))
                
                print(f'[agente_multiplicacao] -> enviando {msg_resposta.body} para [gerente]')
                
                await self.send(msg_resposta)
                
        async def on_end(self):
            await self.agent.stop()

    async def setup(self):
        print("[agente_multiplicacao] -> iniciando...")
        self.add_behaviour(self.RecvBehav())
        

class AgenteDivisao(Agent):        
    class RecvBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            
            if msg:
                operandos = msg.body.split('/')
                msg_resposta = Message(to="gerente@lightwitch.org")     # Instantiate the message
                msg_resposta.body = str(int(operandos[0]) // int(operandos[1]))        # divisao inteira (int)
                
                print(f'[agente_divisao] -> enviando {msg_resposta.body} para [gerente]')
                
                await self.send(msg_resposta)
                
        async def on_end(self):
            await self.agent.stop()

    async def setup(self):
        print("[agente_divisao] -> iniciando...")
        self.add_behaviour(self.RecvBehav())


if __name__ == "__main__":
    future = None
    agentes = list()
    servidor = {'host': 'lightwitch.org', 'senha': 'sy5xHtw8idA3HuG'}
    
    expressao = input('Digite uma expressao matematica: ').strip().replace(' ', '')
    
    agentes.append(AgenteSoma(f"adicao@{servidor['host']}", servidor['senha']))
    agentes.append(AgenteSubtracao(f"subtracao@{servidor['host']}", servidor['senha']))
    agentes.append(AgenteMultiplicacao(f"multiplicacao@{servidor['host']}", servidor['senha']))
    agentes.append(AgenteDivisao(f"divisao@{servidor['host']}", servidor['senha']))
    agente_gerente = Gerente("gerente@lightwitch.org", "sy5xHtw8idA3HuG")
    
    for agente in agentes:
        future = agente.start(auto_register=True)       # quando terminar, future fica com o último elemento
        
    future.result()              # wait for receiver agent to be prepared. O gerente só inicia depois que todos os agentes estiverem prontos.

    agente_gerente.set("agente_soma", "adicao@lightwitch.org")
    agente_gerente.set("agente_subtracao", "subtracao@lightwitch.org")
    agente_gerente.set("agente_multiplicacao", "multiplicacao@lightwitch.org")
    agente_gerente.set("agente_divisao", "divisao@lightwitch.org")
    
    agente_gerente.start(auto_register=True)

    while not finalizou:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            for agente in agentes:
                agente.stop()
            agente_gerente.stop()
            break
        
    quit_spade()
