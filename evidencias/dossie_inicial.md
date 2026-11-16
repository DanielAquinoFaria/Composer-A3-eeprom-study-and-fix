> Documento histórico anterior à comparação dos dumps. A atribuição inicial do erro de direção à EEPROM foi revista: os blocos SYSTEM disponíveis são iguais. Consulte o [relatório final](../RELATORIO.md).

# Dossiê de Engenharia Reversa - Anisoprint Composer A3

## 1. Visão Geral do Projeto

* **Objetivo**: Identificar causador de falhas na execução de tarefas da impressora 3D Anisoprint Composer A3.
* **Método**: Engenharia Reversa (REA) e análise estática/dinâmica de firmware e processo de gravação.

## 2. Recursos e Arquivos

* **Binário/Configuração**: Arquivo de firmware compilado com extensões `.FW2` e configurações.
* **Código-Fonte Base**: Firmware MK4duo ("raiz\firmwares\firmware codigo fonte\MK4duo" e  "raiz\firmwares\firmware codigo fonte\MKA-firmware").
* **Código-Fonte Alvo**: Firmware MKA (versão instalada e modificada para a máquina).
* **Ferramenta de Gravação**: `flasherWin.exe` (localizado na pasta "composer flash"). Selecionado o perfil `Composer A3-1.0.5.gc`.
* **Documentação**: Manual da placa de controle e datasheet do microcontrolador.

## 3. Arquitetura de Hardware Relevante

* **Placa Controladora**: Ultratronics.
* **Módulo de EEPROM Externo**: A memória EEPROM **não** está localizada na placa principal Ultratronics. Ela reside em uma placa externa conectada ao sistema.
* **Chip da EEPROM**: ATMLH 2ECL.
* **Pinagem de Reset (Botões)**:
  * **Pino 47**: Conectado fisicamente a um botão de reset.
  * **Pino 130**: Conectado a um segundo botão, também identificado como reset. O acionamento deste botão em específico já foi realizado durante as tentativas de restabelecer a máquina nos ciclos de falha.

## 4. Comportamento Anômalo e Histórico de Falhas

### 4.1. Sintoma Inicial (Pós-Gravação)

* A máquina realiza a rotina de *homing* como esperado.
* Durante a etapa de **troca de ferramenta** (inclusa na rotina de inicialização), o **eixo Y assume um valor de `-74874577188028416.00`**.
* A máquina deixa de obedecer a outros comandos, respondendo apenas a uma Parada de Emergência via porta serial.

### 4.2. Cronologia e Evolução do Erro

* **Primeiro Uso Pós-Gravação**: As calibrações de temperatura e mecânicas são feitas sem problemas. A primeira impressão (G-code) é concluída com sucesso.
* **Gatilho da Falha (Boot)**: Após o término bem-sucedido da primeira impressão, ao **ligar a máquina** novamente (processo de inicialização do zero), a falha de *homing* no eixo Y (valor astronômico) se manifesta.
* **Erro de EEPROM na Inicialização**: Após algumas reinicializações da máquina, o LCD passou a exibir a seguinte mensagem de erro no boot:
  > *"Failed to read User Config from EEPROM. Default settings were loaded. Buildplate and printhead re-calibration may be needed. If the error persists, please contact Support. <<OK>>"*

### 4.3. Intervenção nos Offsets e Congelamento do Sistema (Atual)

* **Ação Executada**: Os motores foram desconectados fisicamente por precaução. O aviso de erro de EEPROM foi ignorado pressionando "<<OK>>". Acessou-se o menu de manutenção para alterar os *offsets* da ferramenta.
* **Estado Encontrado**: O menu exibia os valores antigos de *offset* (X: -2.2, Y: -16.5, Z: 0), apesar do alerta de falha de leitura da EEPROM (origem dos dados incerta entre Flash ou EEPROM corrompida).
* **Alteração Realizada**: Os offsets de ferramenta foram alterados para X: 0, Y: 0 e Z: 0.
* **Novo Comportamento Observado**:
  1. O erro de EEPROM no LCD parou de ser exibido nas reinicializações seguintes.
  2. A rotina de *homing* de X, Y e Z é completada aparentemente de forma normal.
  3. Imediatamente após o *homing*, a máquina inicia movimentação na direção errada.
  4. A tela do LCD congela na logomarca de inicialização.
  5. Os menus tornam-se inacessíveis, indicando travamento da interface ou laço infinito (*infinite loop*) no firmware.

### 4.4. Teste de Hardware (Substituição da EEPROM)

* **Ação Executada**: Troca da placa externa de EEPROM (ATMLH 2ECL) por uma segunda unidade idêntica.
* **Resultado Observado**: O sintoma de movimentação muda. Com a segunda placa de EEPROM, a impressora apresenta movimento no **eixo Y na direção errada logo durante a fase inicial de homing**. Isso confirma que os dados armazenados (ou a falta deles/dados corrompidos) neste chip externo afetam diretamente a lógica de inversão/direção dos motores ou os limites (*endstops*).