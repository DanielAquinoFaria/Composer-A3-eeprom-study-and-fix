# Procedimento de recuperação com Arduino Uno

Este roteiro documenta o método associado à resolução informada pelo operador. As verificações pós-recuperação abaixo são propostas para reprodução e acompanhamento; não são uma lista de ensaios já realizados na máquina deste caso.

## 1. Identificar os três destinos

- **AT24C256C externa:** recebe a imagem `AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.bin`, de 32.768 bytes.
- **Arduino Uno R3/ATmega328P:** recebe `eeprom_uno.ino` compilado ou o HEX correspondente. Ele é o programador.
- **SAM3X da impressora:** executa MKA. O `MKA.bin` do Composer Flasher é outro arquivo, com outro destino.

Não é necessário regravar a Flash da impressora para realizar a escrita externa da EEPROM. Não usar binários A4, MK4duo genérico ou firmware de LCD como substitutos do programa da A3.

## 2. Preparar hardware e software

Materiais: Uno R3, cabo USB de dados, AT24C256C/adaptador apropriado, fios curtos, dois resistores de 4,7 kΩ, um de 10 kΩ e capacitor cerâmico de 100 nF. A orientação de pinos depende do encapsulamento; a tabela abaixo é para SOIC/TSSOP de oito pinos, vista superior.

| EEPROM | Uno / ligação |
|---|---|
| Pinos 1/2/3: A0/A1/A2 | GND, endereço I²C de sete bits `0x50` |
| Pino 4: GND | GND |
| Pino 5: SDA | A4/SDA; pull-up de 4,7 kΩ para 5 V |
| Pino 6: SCL | A5/SCL; pull-up de 4,7 kΩ para 5 V |
| Pino 7: WP | D7; pull-up de 10 kΩ para 5 V |
| Pino 8: VCC | 5 V; capacitor de 100 nF entre VCC e GND |

O [esquemático e guia de montagem](../gravador/hardware/MONTAGEM.md) explicam as ramificações dos resistores e a identificação do pino 1. **Não ligar WP diretamente a 5 V com D7 conectado.**

Esta montagem a 5 V destina-se à EEPROM isolada. Desligar impressora e USB antes de desconectar o módulo. Não deixar SDA/SCL/alimentação ligados simultaneamente à Ultratronics; não aplicar 5 V a um barramento de 3,3 V. A pinagem do conector do módulo precisa ser conferida por continuidade; ela não é necessariamente igual à ordem dos pinos do chip.

No computador:

1. Instalar Python 3.10+ com Tcl/Tk e Arduino IDE com Arduino AVR Boards 1.8.6.
2. Abrir `gravador/firmware/eeprom_uno/eeprom_uno.ino`, selecionar **Arduino Uno** e sua porta; compilar e carregar.
3. Fechar o Monitor Serial para liberar a porta.
4. Na raiz do pacote, executar:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r gravador/requirements.txt
.venv\Scripts\python.exe gravador/desktop/app.py
```

Na interface, selecionar a COM do Uno, endereço `0x50`, **Simulação desmarcada** e conectar. Se A0/A1/A2 não estiverem todos em GND, usar o endereço correspondente à montagem, sem alterar ligações desconhecidas.

## 3. Preservar o estado anterior

Selecionar **Leitura**, início `0x0000`, quantidade `32768`, e salvar um arquivo novo. Fazer outra leitura independente e comparar os hashes. Guardar os arquivos fora do caminho da imagem de referência, anotando placa, data e montagem.

Se as leituras diferirem sem escrita entre elas, investigar contato, alimentação e I²C antes de prosseguir. Se forem iguais, ainda é necessário avaliar CRC e parâmetros; igualdade não significa configuração funcionalmente correta.

Os dumps em `gravador/imagens/clones` são evidências anteriores à recuperação, **não imagens alternativas recomendadas para gravar**.

## 4. Conferir e gravar a imagem

Na raiz do pacote:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'gravador/imagens/AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.bin'
```

Resultado esperado, desconsiderando maiúsculas/minúsculas:

```text
a54501351980aeef05636856efa92e8a668bbfaf2794a42b80f438af59d0dc1e
```

Selecionar **Gravação**, endereço inicial `0x0000` e esse arquivo. A interface obtém o tamanho do arquivo; deve ser **32768 bytes**. Confirmar a operação na própria interface e aguardar o término da escrita e da verificação integral.

A imagem substitui a memória inteira, incluindo SN, versão e lacunas. O SN fica vazio; calibrações USER passam aos defaults descritos em [LEIA_ME.md](../gravador/imagens/LEIA_ME.md). Ela não restaura automaticamente ajustes exclusivos da máquina.

Depois, selecionar **Verificação** com o mesmo arquivo e endereço. Fazer também uma leitura completa para outro arquivo e comparar seu SHA-256 com o da imagem. Essa igualdade confirma os bytes do chip naquele momento, antes de qualquer nova gravação pela impressora.

Em falha ou cancelamento, considerar a EEPROM parcialmente escrita. Preservar uma nova leitura e analisar a divergência. Regravar a imagem conhecida ou restaurar o backup é uma nova operação completa; não há rollback automático. A restauração de um backup problemático também restaura sua configuração problemática.

## 5. Reinstalar e validar na impressora

Desconectar o USB do Uno e remontar o módulo com a impressora sem alimentação. O firmware pode fazer homing e troca durante o boot; preparar a bancada considerando o histórico de movimento anômalo. Desconexões de motores ou aquecedores devem ocorrer com tudo desligado.

Após restabelecer um estado seguro para teste, registrar progressivamente:

1. Boot e mensagens de USER/SYSTEM; os CRCs da imagem inicial são USER 37164 e SYSTEM 13673.
2. Valores efetivamente carregados, particularmente offset de troca X/Y, presets, offsets dos bicos e configuração de endstops.
3. Sentido e parada de homing, depois troca de ferramenta e acesso normal à interface.
4. Calibrações geométricas e térmicas requeridas pela máquina antes de impressão.
5. Desligar/ligar e repetir a conferência; em seguida, realizar impressão de teste apropriada.
6. Salvar um novo backup identificado após a calibração e registrar os parâmetros e resultados.

Os CRCs e o hash integral podem mudar legitimamente depois que a impressora salvar calibrações. Comparar uma imagem pós-calibração com a imagem inicial exige interpretar quais campos foram alterados; não assumir corrupção apenas porque os hashes diferem.

## 6. Se houver recorrência

| Situação | Próxima verificação |
|---|---|
| Não conecta ao Uno | Cabo, porta, firmware e Monitor Serial fechado |
| PROBE/I²C falha | Endereço A0–A2, SDA/SCL, pull-ups, alimentação e isolamento |
| Gravação não altera os bytes | WP/D7, montagem, contatos e resultado da verificação |
| CRC passa, mas parâmetros não fazem sentido | Layout, versão, floats e limites por campo |
| Conteúdo muda após boot | Comparar dumps antes/depois e identificar escritas do MKA |
| Conteúdo muda sem escrita conhecida | Investigar alimentação, transporte e retenção com condições controladas |
| Movimento continua incorreto com SYSTEM igual | Conferir RAM carregada, fase do movimento, endstops, mecânica e circuito |

O relatório final não identifica um componente elétrico como causa comprovada. Essas verificações servem para produzir evidência caso o problema volte.
