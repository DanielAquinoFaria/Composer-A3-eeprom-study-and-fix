# Composer A3 eeprom study and fix

**Problema resolvido com a gravação externa da EEPROM AT24C256C usando Arduino Uno.** Em 16/11/2026, o responsável pela máquina confirmou a resolução e identificou o arquivo usado como `AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.bin`.

Este repositório reúne o caminho da investigação, as evidências, os firmwares disponíveis e o software completo do gravador. O relato de sucesso é do operador; os testes automatizados desta entrega verificam arquivos e software, sem operar a impressora.

## Resumo da operação realizada

A Composer A3 apresentava movimento anômalo no eixo Y durante a troca de ferramenta, permanência na tela de inicialização e mensagens de erro de configuração da EEPROM. Regravar o firmware da controladora e zerar os offsets dos bicos pelo menu não eliminou o problema observado.

1. **Investigação:** foram reunidos logs de boot e gravação, código-fonte MKA, perfis de configuração e documentação do hardware para distinguir o programa na Flash dos parâmetros persistidos na EEPROM externa.
2. **Preservação e comparação:** seis dumps de 32.768 bytes, em dois grupos de três capturas idênticas, permitiram localizar o campo `switch_offset_y` no endereço `0x0046`. No grupo com erro de magnitude, os bytes `04 01 85 DB` representam **−74.874.577.188.028.416**, mesmo com CRC USER válido. Os blocos SYSTEM eram iguais entre os dois grupos e a referência.
3. **Reconstrução:** uma imagem completa da AT24C256C foi gerada a partir dos defaults e inicializações do fonte MKA, aplicando os 53 comandos do perfil `Composer A3-1.0.5.gc`. Os offsets de troca foram definidos em zero, os presets e demais parâmetros foram reconstruídos, os CRCs foram calculados e o número de série foi deixado vazio.
4. **Gravação externa:** a imagem foi gravada na EEPROM com **Arduino Uno**, usando o firmware do gravador e a interface Python/Tkinter incluídos neste projeto. O software oferece backup, leitura, escrita, releitura e comparação integral.
5. **Resultado:** o operador confirmou que a gravação dessa imagem resolveu o problema e identificou expressamente o arquivo utilizado. Os testes do software e da integridade dos arquivos estão documentados separadamente do resultado físico informado.

A conclusão central é que **CRC válido não garante parâmetros de movimento válidos**. A recuperação restabeleceu uma configuração conhecida; a origem inicial da alteração dos bytes continua indeterminada. As melhorias sugeridas para o MKA são recomendações e não foram implementadas como parte desta recuperação.

**English summary:** This project documents an Anisoprint Composer A3 recovery achieved by externally programming a reconstructed AT24C256C EEPROM image with an Arduino Uno. Six EEPROM dumps revealed an invalid tool-change Y offset despite a valid USER CRC. A complete configuration image was rebuilt from MKA defaults and the Composer A3-1.0.5 profile, and the operator confirmed recovery. The original cause of the altered bytes remains undetermined. Full reports are available in Brazilian Portuguese and English below.

## Por onde começar

- **Relatórios profissionais em PDF:** [Português brasileiro](docs/relatorios/Relatorio_Recuperacao_EEPROM_Composer_A3_PT-BR.pdf) e [English](docs/relatorios/EEPROM_Recovery_Report_Composer_A3_EN.pdf), nove páginas em cada versão.
- [Relatório da investigação e resolução](RELATORIO.md): sequência dos acontecimentos, hipóteses, evidências, correções e questões ainda abertas.
- [Procedimento de recuperação](docs/PROCEDIMENTO.md): montagem, backup, gravação e verificação.
- [Imagem EEPROM usada na solução](gravador/imagens/AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.bin).
- [Gravador completo](gravador/README.md): interface Python/Tkinter, firmware Uno, protocolo, testes e ferramentas.
- [Inventário e versões](docs/INVENTARIO.md), [validação da entrega](docs/VALIDACAO_PACOTE.md) e [publicação no GitHub](docs/PUBLICACAO.md).

## Arquivo correto para cada destino

| Artefato | Destino | Finalidade |
|---|---|---|
| `gravador/imagens/AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.bin` | EEPROM externa AT24C256C, início `0x0000` | Configuração reconstruída que resolveu este caso; 32.768 bytes |
| `gravador/firmware/eeprom_uno/eeprom_uno.ino` | Arduino Uno R3 / ATmega328P | Código-fonte do leitor/gravador |
| `gravador/firmware/precompilado/eeprom_uno.hex` | Flash do Arduino Uno, mantendo seu bootloader | Compilação de conveniência do mesmo gravador |
| `firmwares/Composer Flasher/Composer A3/.../MKA.bin` ou `.fw2` | Controladora da impressora, pelo fluxo do Composer Flasher | Firmware executável MKA; não é imagem EEPROM |
| `Composer A3-1.0.5.gc` | Parâmetros interpretados pelo MKA | Perfil usado para reconstruir a configuração |

**Não trocar esses destinos.** A recuperação confirmada foi a escrita da imagem de configuração na EEPROM. O pacote histórico do Flasher está incluído para documentação/reprodução, não como uma etapa obrigatória de nova gravação da controladora.

SHA-256 da imagem EEPROM:

```text
a54501351980aeef05636856efa92e8a668bbfaf2794a42b80f438af59d0dc1e
```

Ela contém número de série vazio, perfil de identificação `1.0.5` e defaults USER. Não preserva calibrações individuais anteriores. Sua aplicação a outra máquina exige conferir modelo, hardware, layout e calibrações.

## Executar o gravador

Python 3.10+ com Tcl/Tk e Arduino IDE/Arduino AVR Boards 1.8.6 são instalados separadamente. Na raiz deste repositório:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r gravador/requirements.txt
.venv\Scripts\python.exe gravador/desktop/app.py
```

O firmware é carregado pelo Arduino IDE a partir de `gravador/firmware/eeprom_uno/eeprom_uno.ino`, selecionando **Arduino Uno**. A montagem está em [MONTAGEM.md](gravador/hardware/MONTAGEM.md). O modo Simulação permite experimentar a interface sem hardware.

## Organização

```text
RELATORIO.md             Relatório final, com referências às evidências
docs/                    Recuperação, inventário, validação e publicação
gravador/                Projeto completo, imagem final, dumps e fonte MKA
firmwares/               MKA-firmware, Composer Flasher completo e snapshot MK4duo
evidencias/              Logs, diagnósticos históricos e leitor ESP32-C3
referencias/             Datasheets e guia de flashing recebido
tools/verificar_pacote.py Verificação de integridade sem hardware
MANIFESTO_SHA256.json     Tamanho e hash dos arquivos da entrega
THIRD_PARTY_NOTICES.md    Proveniência e escopo das licenças
```

Os documentos históricos mantêm suas conclusões e limites da época. O relatório final atualiza o estado do caso. Os dumps históricos contêm identificação da máquina; a imagem destinada à recuperação está sem SN.

Para conferir os arquivos: `python tools/verificar_pacote.py`. O manifesto é local e não constitui assinatura digital. As fontes MKA necessárias estão incluídas diretamente; não é necessário clonar dependências ou o projeto REA.
