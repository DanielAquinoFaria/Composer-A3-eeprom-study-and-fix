# Validação da entrega — 16/11/2026

## Resultado físico informado

O responsável pela máquina confirmou que a gravação da nova imagem com Arduino Uno resolveu o problema e identificou o arquivo pelo nome. Veja [CONFIRMACAO_OPERADOR.md](CONFIRMACAO_OPERADOR.md).

Esta sessão de organização não abriu portas seriais, não gravou hardware e não movimentou a impressora. Não foi anexado dump pós-recuperação ou log de ensaio final. A confirmação operacional e os testes abaixo são evidências de naturezas diferentes.

## Testes executados na nova pasta

| Verificação | Resultado |
|---|---|
| `python -B -m unittest discover -s gravador/tests -v` | **16 testes aprovados**: protocolo, memória simulada, interface, perfil, mapa, CRC e hashes das fontes |
| `python -B -m unittest discover -s evidencias/leitor_esp32c3 -v` | **14 testes aprovados**: parser, truncamento, CRC32, erros e preservação das aquisições |
| Compilação do sketch Uno | **Aprovada**, 8.466 bytes de programa e 721 bytes de RAM estática |
| Imagem de recuperação | **32.768 bytes**, SHA-256 esperado confirmado |
| CRC independente usando `binascii.crc_hqx` | USER **37164** e SYSTEM **13673**, iguais aos cabeçalhos |
| Seis dumps históricos | Dois grupos de três arquivos idênticos; CRCs válidos; SYSTEM igual à referência byte a byte |
| Float anômalo | `04 01 85 DB` no endereço `0x0046`, decodificado como **−74.874.577.188.028.416** |
| Perfil duplicado no pacote Flasher | Igual byte a byte ao perfil das dependências do gerador |
| Proveniência | Arquivos copiados comparados aos hashes de origem; alterações editoriais explicitamente listadas |

Os testes do gravador usam transporte simulado e exercitam o fluxo conectar/gravar/verificar/ler da interface Tk. Não substituem medições elétricas ou teste do protocolo no Uno físico. Os 721 bytes são uso estático, sem estimativa da pilha dinâmica.

## Ambiente e compilação

Ambiente usado: Windows, Python **3.10.10**, pyserial **3.5**, Tk **8.6**, Arduino AVR Boards **1.8.6**, avr-gcc **7.3.0-atmel3.6.1-arduino7**.

Comando de compilação equivalente, substituindo o caminho da instalação local:

```powershell
python gravador/tools/build_firmware.py --arduino-packages "C:/CAMINHO/Arduino15/packages/arduino"
```

O script apenas compila; não carrega firmware em dispositivo. O resultado `gravador/build/eeprom_uno.hex` foi copiado para `gravador/firmware/precompilado/eeprom_uno.hex`. Os intermediários foram retirados da pasta de entrega.

SHA-256 do HEX compilado:

```text
e61d928a9e7432a3c4a4fbf56c2bad197fab0b5a767a5ab2f22f0f13c14dcde0
```

Não foram recompilados nem executados MKA, MK4duo, firmware Nextion ou Composer Flasher. A geração original da imagem via ARM GCC está documentada nos registros de 04/11. Nesta entrega, os testes repetiram a aplicação do perfil aos defaults registrados e a montagem da imagem, além de validar as fontes, sem refazer a extração das macros pelo ARM GCC.

## Integridade do conjunto

`MANIFESTO_SHA256.json` registra os arquivos finais, seus tamanhos e hashes. Ele não inclui a si próprio para evitar autorreferência. O verificador é somente leitura e não abre portas de hardware:

```powershell
python tools/verificar_pacote.py
```

O manifesto não é assinatura digital e não atesta autenticidade perante terceiros. Alterar arquivo e manifesto conjuntamente impede detectar a alteração por esse mecanismo. Sua finalidade é detectar perda ou modificação acidental na cópia/publicação.

O `.gitattributes` preserva bytes de texto e binários para evitar que a conversão de finais de linha no Git invalide os hashes. O pacote não contém históricos `.git`, ambientes virtuais ou caches de compilação.
