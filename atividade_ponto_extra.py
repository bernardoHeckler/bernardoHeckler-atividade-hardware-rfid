import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import csv
from datetime import datetime

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Portas mantidas
LED_VERDE = 17      # pino físico 11
LED_VERMELHO = 27   # pino físico 13
BUZZER = 22         # pino físico 15

GPIO.setup(LED_VERDE, GPIO.OUT)
GPIO.setup(LED_VERMELHO, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)

GPIO.output(LED_VERDE, GPIO.LOW)
GPIO.output(LED_VERMELHO, GPIO.LOW)
GPIO.output(BUZZER, GPIO.LOW)

buzzer_pwm = GPIO.PWM(BUZZER, 440)
leitor_rfid = SimpleMFRC522()

# Substitua pelos IDs reais das tags
COLABORADORES = {
    498103025204: {"nome": "Bernardo", "autorizado": True},
    693825048343: {"nome": "Samuel", "autorizado": False}
}

registros_diarios = {}
tentativas_nao_autorizadas = {}
tentativas_invasao = 0
log_eventos = []

ultima_leitura = {"tag": None, "instante": 0}
JANELA_ANTI_REPETICAO = 2.0


def apagar_leds():
    GPIO.output(LED_VERDE, GPIO.LOW)
    GPIO.output(LED_VERMELHO, GPIO.LOW)


def tocar_tom(frequencia, duracao, pausa=0.05):
    buzzer_pwm.ChangeFrequency(frequencia)
    buzzer_pwm.start(50)
    time.sleep(duracao)
    buzzer_pwm.stop()
    time.sleep(pausa)


def som_entrada_autorizada():
    tocar_tom(700, 0.12)
    tocar_tom(900, 0.12)


def som_tentativa_nao_autorizada():
    tocar_tom(350, 0.20)
    tocar_tom(350, 0.20)
    tocar_tom(350, 0.20)


def som_tentativa_invasao():
    for _ in range(4):
        tocar_tom(950, 0.10, 0.03)
        tocar_tom(550, 0.10, 0.03)


def acender_led(pin, duracao=5):
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(duracao)
    GPIO.output(pin, GPIO.LOW)


def piscar_led(pin, vezes=10, tempo_on=0.25, tempo_off=0.25):
    for _ in range(vezes):
        GPIO.output(pin, GPIO.HIGH)
        time.sleep(tempo_on)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(tempo_off)


def formatar_tempo(segundos):
    total = int(round(segundos))
    horas, resto = divmod(total, 3600)
    minutos, segundos = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


def registrar_evento(tag_id, nome, tipo_evento, autorizado, detalhe=""):
    agora = datetime.now()
    log_eventos.append({
        "timestamp": agora.strftime("%Y-%m-%d %H:%M:%S"),
        "data": agora.strftime("%Y-%m-%d"),
        "hora": agora.strftime("%H:%M:%S"),
        "tag_id": tag_id,
        "nome": nome,
        "tipo_evento": tipo_evento,
        "autorizado": "sim" if autorizado else "nao",
        "detalhe": detalhe,
    })


def obter_registro_do_dia(tag_id, nome, autorizado):
    data_hoje = datetime.now().strftime("%Y-%m-%d")

    if data_hoje not in registros_diarios:
        registros_diarios[data_hoje] = {}

    if tag_id not in registros_diarios[data_hoje]:
        registros_diarios[data_hoje][tag_id] = {
            "nome": nome,
            "autorizado": autorizado,
            "entrou_hoje": False,
            "dentro_sala": False,
            "entrada_atual": None,
            "quantidade_entradas": 0,
            "quantidade_saidas": 0,
            "tempo_total_segundos": 0.0,
            "tentativas_nao_autorizadas": 0,
        }

    return registros_diarios[data_hoje][tag_id], data_hoje


def ler_tag():
    tag = leitor_rfid.read_id_no_block()
    if tag is None:
        return None

    agora = time.time()
    if ultima_leitura["tag"] == tag and (agora - ultima_leitura["instante"]) < JANELA_ANTI_REPETICAO:
        return None

    ultima_leitura["tag"] = tag
    ultima_leitura["instante"] = agora
    return tag


def processar_tag(tag):
    global tentativas_invasao

    colaborador = COLABORADORES.get(tag)

    if colaborador is None:
        print("Identificação não encontrada!")
        registrar_evento(tag, "DESCONHECIDO", "tentativa_invasao", False, "Tag não cadastrada")
        tentativas_invasao += 1
        apagar_leds()
        som_tentativa_invasao()
        piscar_led(LED_VERMELHO, vezes=10, tempo_on=0.20, tempo_off=0.20)
        return

    nome = colaborador["nome"]
    autorizado = colaborador["autorizado"]
    registro, _ = obter_registro_do_dia(tag, nome, autorizado)

    if not autorizado:
        print(f"Você não tem acesso a este projeto, {nome}")
        registro["tentativas_nao_autorizadas"] += 1

        if nome not in tentativas_nao_autorizadas:
            tentativas_nao_autorizadas[nome] = 0
        tentativas_nao_autorizadas[nome] += 1

        registrar_evento(tag, nome, "tentativa_nao_autorizada", False, "Colaborador sem permissão")
        apagar_leds()
        som_tentativa_nao_autorizada()
        acender_led(LED_VERMELHO, duracao=5)
        return

    agora = datetime.now()

    if not registro["dentro_sala"]:
        primeira_entrada_no_dia = not registro["entrou_hoje"]
        registro["dentro_sala"] = True
        registro["entrada_atual"] = agora
        registro["entrou_hoje"] = True
        registro["quantidade_entradas"] += 1

        if primeira_entrada_no_dia:
            print(f"Bem-vindo, {nome}")
            registrar_evento(tag, nome, "entrada", True, "Primeira entrada do dia")
        else:
            print(f"Bem-vindo de volta, {nome}")
            registrar_evento(tag, nome, "reentrada", True, "Retorno ao ambiente")

        apagar_leds()
        som_entrada_autorizada()
        acender_led(LED_VERDE, duracao=5)
    else:
        tempo_permanencia = (agora - registro["entrada_atual"]).total_seconds()
        registro["tempo_total_segundos"] += tempo_permanencia
        registro["entrada_atual"] = None
        registro["dentro_sala"] = False
        registro["quantidade_saidas"] += 1

        print(f"Saída registrada, {nome}")
        registrar_evento(tag, nome, "saida", True, f"Permanência {formatar_tempo(tempo_permanencia)}")
        time.sleep(1)


def fechar_permanencias_abertas():
    agora = datetime.now()

    for data, colaboradores in registros_diarios.items():
        for tag_id, registro in colaboradores.items():
            if registro["dentro_sala"] and registro["entrada_atual"] is not None:
                tempo_permanencia = (agora - registro["entrada_atual"]).total_seconds()
                registro["tempo_total_segundos"] += tempo_permanencia
                registro["entrada_atual"] = None
                registro["dentro_sala"] = False
                registro["quantidade_saidas"] += 1

                registrar_evento(
                    tag_id,
                    registro["nome"],
                    "saida_automatica",
                    registro["autorizado"],
                    f"Encerramento do sistema após {formatar_tempo(tempo_permanencia)}"
                )


def mostrar_relatorio():
    print("\n" + "=" * 70)
    print("RELATÓRIO DE ACESSO À SALA DO PROJETO")
    print("=" * 70)

    if not registros_diarios:
        print("Nenhum registro de permanência encontrado.")
    else:
        for data, colaboradores in registros_diarios.items():
            print(f"\nData: {data}")
            print("-" * 70)

            houve_registro = False
            for tag_id, registro in colaboradores.items():
                if registro["autorizado"]:
                    houve_registro = True
                    print(
                        f"Nome: {registro['nome']:<15} "
                        f"Tag: {tag_id:<12} "
                        f"Entradas: {registro['quantidade_entradas']:<3} "
                        f"Saídas: {registro['quantidade_saidas']:<3} "
                        f"Tempo: {formatar_tempo(registro['tempo_total_segundos'])}"
                    )

            if not houve_registro:
                print("Nenhum colaborador autorizado acessou a sala nesta data.")

    print("\n" + "=" * 70)
    print("TENTATIVAS DE COLABORADORES NÃO AUTORIZADOS")
    print("=" * 70)

    if tentativas_nao_autorizadas:
        for nome, quantidade in tentativas_nao_autorizadas.items():
            print(f"{nome}: {quantidade} tentativa(s)")
    else:
        print("Nenhuma tentativa de colaborador não autorizado.")

    print("\n" + "=" * 70)
    print("TENTATIVAS DE INVASÃO")
    print("=" * 70)
    print(f"Total de tentativas de invasão: {tentativas_invasao}")


def salvar_csvs():
    sufixo = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    arquivo_resumo = f"relatorio_acessos_{sufixo}.csv"
    arquivo_eventos = f"log_eventos_{sufixo}.csv"

    with open(arquivo_resumo, mode="w", newline="", encoding="utf-8") as csvfile:
        campos = [
            "data",
            "tag_id",
            "nome",
            "autorizado",
            "entrou_hoje",
            "quantidade_entradas",
            "quantidade_saidas",
            "tempo_total_segundos",
            "tempo_total_horas",
            "tentativas_nao_autorizadas",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=campos)
        writer.writeheader()

        for data, colaboradores in registros_diarios.items():
            for tag_id, registro in colaboradores.items():
                writer.writerow({
                    "data": data,
                    "tag_id": tag_id,
                    "nome": registro["nome"],
                    "autorizado": "sim" if registro["autorizado"] else "nao",
                    "entrou_hoje": "sim" if registro["entrou_hoje"] else "nao",
                    "quantidade_entradas": registro["quantidade_entradas"],
                    "quantidade_saidas": registro["quantidade_saidas"],
                    "tempo_total_segundos": int(round(registro["tempo_total_segundos"])),
                    "tempo_total_horas": round(registro["tempo_total_segundos"] / 3600, 2),
                    "tentativas_nao_autorizadas": registro["tentativas_nao_autorizadas"],
                })

    with open(arquivo_eventos, mode="w", newline="", encoding="utf-8") as csvfile:
        campos = ["timestamp", "data", "hora", "tag_id", "nome", "tipo_evento", "autorizado", "detalhe"]
        writer = csv.DictWriter(csvfile, fieldnames=campos)
        writer.writeheader()

        for evento in log_eventos:
            writer.writerow(evento)

    print("\nArquivos CSV gerados:")
    print(f"- {arquivo_resumo}")
    print(f"- {arquivo_eventos}")


print("Sistema de controle de acesso iniciado.")
print("Aproxime a tag do sensor para entrada ou saída.")
print("Pressione Ctrl+C para encerrar e gerar o relatório.")

try:
    while True:
        tag = ler_tag()
        if tag is not None:
            processar_tag(tag)

        time.sleep(0.2)

except KeyboardInterrupt:
    print("\nEncerrando sistema...")

finally:
    fechar_permanencias_abertas()
    mostrar_relatorio()
    salvar_csvs()
    apagar_leds()
    buzzer_pwm.stop()
    GPIO.cleanup()
    print("Sistema encerrado com sucesso.")
