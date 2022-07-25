import datetime
import getpass
import time
import re

from spade import quit_spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.message import Message

comunicacao_atual = ""
finalizou = False


def realiza_operacao(operacao: str) -> int:
    pos_operador = re.search("[^0-9]", operacao).span()[0]
    operandos = operacao.split(operacao[pos_operador])
    
    if comunicacao_atual == "agente_adicao":
        resposta = int(operandos[0]) + int(operandos[1])
    elif comunicacao_atual == "agente_subtracao":
        resposta = int(operandos[0]) - int(operandos[1])
    elif comunicacao_atual == "agente_multiplicacao":
        resposta = int(operandos[0]) * int(operandos[1])
    elif comunicacao_atual == "agente_divisao":
        resposta = int(operandos[0]) / int(operandos[1])
    elif comunicacao_atual == "agente_exponenciacao":
        resposta = int(operandos[0]) ** int(operandos[1])
    else:
        expoente = operandos[1]
        resposta = int(operandos[0]) ** (int(expoente[0])/int(expoente[-1]))
        
        """
        -------------- RAIZ ---------------
        
        Ex: 4^1/3 = raiz cúbica de 4.
        
        - base = primeiro_operando;
        - expoente = segundo_operando[0] / segundo_operando[2];
        
        * A divisão é feita no '^'.
        
        """

    return str(resposta)
    

def define_expressao_reduzida(pos_operador: int) -> str:
    expressao_reduzida = ""

    aux = pos_operador - 1  # procurando para a esquerda do operador
    while expressao[aux].isnumeric():
        expressao_reduzida += expressao[aux]
        aux -= 1

        if aux < 0:
            break

    expressao_reduzida = expressao_reduzida[::-1] + expressao[pos_operador]

    aux = pos_operador + 1  # procurando para a direita do operador
    while expressao[aux].isnumeric():
        expressao_reduzida += expressao[aux]
        aux += 1

        if aux > len(expressao) - 1:
            break

    return expressao_reduzida


class Gerente(Agent):
    class InformBehav(PeriodicBehaviour):
        async def run(self):
            global expressao, finalizou, comunicacao_atual

            pos_operador = 0
            print(f'\n{expressao}\n')
            
            if expressao.find('^') != -1:
                comunicacao_atual = 'agente_exponenciacao'
                pos_operador = expressao.find('^')
            elif expressao.find('*') != -1:
                comunicacao_atual = 'agente_multiplicacao'
                pos_operador = expressao.find('*')
            elif expressao.find('/') != -1:
                comunicacao_atual = 'agente_divisao'
                pos_operador = expressao.find('/')
            elif expressao.find('+') != -1:
                comunicacao_atual = 'agente_adicao'
                pos_operador = expressao.find('+')
            elif expressao.find('-') != -1:
                comunicacao_atual = 'agente_subtracao'
                pos_operador = expressao.find('-')

            msg = Message(to=self.get(comunicacao_atual))
            msg.body = define_expressao_reduzida(pos_operador)

            await self.send(msg)
            print(f"[gerente] -> enviando {msg.body} para [{comunicacao_atual}]")

            msg_resposta = await self.receive(timeout=10)  # receptor de mensagens
            expressao = expressao.replace(msg.body, msg_resposta.body)

            if expressao.isnumeric() or expressao[0] == '-':
                print(f'\nResposta = {expressao}')
                finalizou = True

    async def setup(self):
        print(f"[gerente] -> iniciando...")
        start_at = datetime.datetime.now() + datetime.timedelta(seconds=4)
        self.add_behaviour(self.InformBehav(period=2, start_at=start_at))


class AgenteOperador(Agent):
    class RecvBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # espera uma mensagem por 10 segundos (ciclos)

            if msg:  # se receber mensagem
                msg_resposta = Message(to="gerente@lightwitch.org")  # Instanciando a mensagem
                msg_resposta.body = realiza_operacao(msg.body)
                
                print(f'[{comunicacao_atual}] -> calculando {msg.body}')
                print(f'[{comunicacao_atual}] -> enviando {msg_resposta.body} para [gerente]')

                await self.send(msg_resposta)

    async def setup(self):
        self.add_behaviour(self.RecvBehav())


if __name__ == "__main__":
    agentes_operadores = list()
    nome_agentes = (
        'agente_adicao',
        'agente_subtracao',
        'agente_multiplicacao',
        'agente_divisao',
        'agente_exponenciacao',
        'agente_radiciacao'
    )
    servidor = {'host': 'lightwitch.org', 'senha': 'sy5xHtw8idA3HuG'}
    expressao = input('Digite uma expressao matematica: ').strip().replace(' ', '')

    for nome_agente in nome_agentes:
        agentes_operadores.append(AgenteOperador(f"{nome_agente}@{servidor['host']}", servidor['senha']))
        future = agentes_operadores[-1].start(auto_register=True)    # quando terminar, 'future' fica com o último elemento

    future.result()  # wait for receiver agent to be prepared. O gerente só inicia depois que todos os agentes estiverem prontos.

    agente_gerente = Gerente(f"gerente@{servidor['host']}", servidor['senha'])

    for agente_operador in agentes_operadores:
        agente_gerente.set(agente_operador.name, f"{agente_operador.name}@{servidor['host']}")

    agente_gerente.start(auto_register=True)

    while not finalizou:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            for agente in agentes_operadores:
                agente.stop()
            agente_gerente.stop()
            break

    quit_spade()
