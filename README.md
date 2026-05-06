# Sistema de Controle de Acesso com RFID

## Objetivo do projeto

Este projeto foi desenvolvido como uma atividade ponto extra com foco em integrar hardware e software para registrar entrada e saida de pessoas em um ambiente usando RFID de aproximacao curta.

A proposta do trabalho e demonstrar, na pratica:

- montagem de um circuito com Raspberry Pi, leitor RFID, LEDs e buzzer;
- leitura de tags RFID por meio de Python;
- identificacao de acessos autorizados, nao autorizados e desconhecidos;
- registro de eventos e geracao de relatorios em CSV;
- configuracao basica do ambiente na Raspberry Pi para executar o sistema.

## O que o sistema faz

O sistema fica em execucao continua aguardando a aproximacao de uma tag RFID no leitor.

Quando uma tag e detectada, o programa verifica se ela esta cadastrada e qual e o seu tipo de acesso:

- `Autorizado`: registra entrada, reentrada ou saida.
- `Nao autorizado`: registra tentativa de acesso negada.
- `Desconhecido`: registra tentativa de invasao ou uso de uma tag nao cadastrada.

O retorno ao usuario acontece de forma visual e sonora:

- LED verde para acesso liberado;
- LED vermelho para acesso negado ou tentativa invalida;
- buzzer com sons diferentes para cada situacao.

## Como o fluxo funciona

O arquivo principal do projeto e `atividade_ponto_extra.py`.

Nele, o funcionamento segue esta logica:

1. configura os pinos GPIO da Raspberry Pi;
2. inicializa o leitor RFID MFRC522;
3. carrega as tags cadastradas em memoria;
4. aguarda a leitura de uma tag;
5. identifica se a pessoa esta autorizada, nao autorizada ou se a tag e desconhecida;
6. registra o evento com data, hora, tipo de ocorrencia e detalhe;
7. controla LEDs e buzzer conforme o resultado;
8. ao encerrar o sistema, fecha permanencias abertas e gera os arquivos CSV.

O codigo tambem possui uma protecao contra repeticao imediata de leitura, evitando que a mesma tag seja processada varias vezes em poucos segundos.

## Regras de acesso implementadas

### Pessoa autorizada

Se a tag pertence a uma pessoa autorizada:

- na primeira leitura do dia, o sistema registra a entrada;
- se a pessoa sair e voltar depois, registra reentrada;
- quando a mesma tag e aproximada novamente enquanto a pessoa esta dentro da sala, o sistema registra a saida;
- o tempo de permanencia no ambiente e acumulado.

### Pessoa nao autorizada

Se a tag existe no cadastro, mas nao possui permissao:

- o acesso nao e liberado;
- o sistema registra a tentativa;
- o LED vermelho e acionado;
- o buzzer toca um alerta especifico.

### Tag desconhecida

Se a tag nao estiver cadastrada:

- o sistema trata como tentativa invalida ou invasao;
- o evento fica registrado no log;
- o LED vermelho pisca;
- o buzzer emite um alerta mais forte.

## Componentes e tecnologias envolvidos

### Hardware

- Raspberry Pi
- leitor RFID RC522 / MFRC522
- tags RFID
- LED verde
- LED vermelho
- buzzer
- jumpers e protoboard

### Software

- Python
- biblioteca `RPi.GPIO`
- biblioteca `mfrc522`
- modulo `csv`
- modulo `datetime`

## Como preparar o ambiente

Para executar este projeto corretamente, o ideal e usar uma Raspberry Pi com o leitor RFID e os demais componentes fisicamente conectados.

Antes de rodar o sistema:

- instale e configure o Raspberry Pi OS;
- habilite a interface SPI da Raspberry Pi;
- conecte corretamente o leitor RFID, os LEDs e o buzzer;
- tenha o Python instalado no sistema.

## Dependencias do projeto

As principais bibliotecas usadas no codigo sao:

- `RPi.GPIO`
- `mfrc522`

Em uma Raspberry Pi, uma forma comum de preparar o ambiente e:

```bash
python -m venv env
source env/bin/activate
pip install RPi.GPIO mfrc522
```

Se o ambiente virtual nao for necessario, tambem e possivel instalar diretamente no sistema:

```bash
pip install RPi.GPIO mfrc522
```

## Como rodar o projeto

Depois de instalar as dependencias e montar o hardware, execute os arquivos na Raspberry Pi dentro da pasta do projeto.

### 1. Testar apenas a leitura RFID

Use este arquivo para validar se o leitor esta conseguindo detectar a tag:

```bash
python teste.py
```

Se tudo estiver correto, o terminal devera exibir os dados da tag lida.

### 2. Rodar o sistema principal

Para iniciar o controle de acesso completo:

```bash
python atividade_ponto_extra.py
```

Quando o sistema iniciar, ele ficara aguardando a aproximacao de uma tag RFID.

Durante a execucao:

- tags autorizadas registram entrada e saida;
- tags nao autorizadas geram alerta de acesso negado;
- tags desconhecidas geram registro de tentativa invalida;
- LEDs e buzzer informam o resultado da leitura.

Para encerrar o programa, use:

```bash
Ctrl + C
```

Ao finalizar, o sistema gera automaticamente os arquivos CSV com o resumo de acessos e o log de eventos.

## Observacoes importantes para execucao

- Este projeto depende de hardware real, entao nao funciona corretamente em um computador comum sem Raspberry Pi e sem leitor RFID.
- O arquivo principal usa GPIO, portanto deve ser executado no ambiente correto da Raspberry Pi.
- As tags RFID precisam estar cadastradas no dicionario `COLABORADORES` dentro do arquivo `atividade_ponto_extra.py`.
- Caso uma nova tag precise ser usada, primeiro e necessario ler seu identificador e depois cadastrar o valor no codigo.

## Arquivos do projeto

- `atividade_ponto_extra.py`: programa principal de controle de acesso.
- `teste.py`: teste simples para validar a leitura de uma tag RFID.
- `log_eventos_...csv`: exemplo de log detalhado dos eventos lidos.
- `relatorio_acessos_...csv`: exemplo de relatorio resumido com entradas, saidas e tempo de permanencia.

## Relatorios gerados

Quando o sistema e encerrado, ele salva dois tipos de arquivo CSV:

### 1. Relatorio de acessos

Esse arquivo resume por pessoa:

- data;
- identificacao da tag;
- nome cadastrado;
- status de autorizacao;
- quantidade de entradas;
- quantidade de saidas;
- tempo total de permanencia;
- quantidade de tentativas nao autorizadas.

### 2. Log de eventos

Esse arquivo registra cada ocorrencia individualmente, incluindo:

- data e hora completas;
- tag lida;
- nome identificado;
- tipo de evento;
- autorizacao;
- detalhe do ocorrido.

## O que foi aprendido com a atividade

Esta atividade permitiu praticar conceitos importantes de um projeto embarcado com integracao de software:

- montagem fisica do hardware;
- configuracao da Raspberry Pi para interagir com perifericos;
- desenvolvimento de logica de controle de acesso em Python;
- uso de sinais visuais e sonoros para feedback;
- persistencia simples de dados em arquivos CSV;
- organizacao de um fluxo real de monitoramento de entrada e saida.

## Resumo

Este projeto simula um sistema de controle de acesso para uma sala ou ambiente restrito usando RFID. A ideia central e registrar quem entrou, quem saiu, quem tentou acessar sem permissao e quem usou uma tag desconhecida, deixando essas informacoes documentadas para consulta posterior.

Nomes: Bernardo Antunes Heckler | Samuel Nunes
RA: 1137118, 1136923
