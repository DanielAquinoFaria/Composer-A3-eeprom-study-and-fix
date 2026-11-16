> Documento técnico da geração/revisão original. As afirmações de ausência de ensaio físico descrevem aquela etapa. Em 16/11/2026, o operador confirmou a resolução com esta imagem e Arduino Uno; veja o [relatório final](../../RELATORIO.md). Nenhum byte da imagem foi alterado nesta consolidação.

# Imagem EEPROM — Composer A3 / perfil 1.0.5

## Arquivo para gravação

**`AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.bin`**

- Tamanho: **32.768 bytes**, imagem completa da AT24C256C.
- Na interface do leitor: **Gravação**, endereço inicial **`0x0000`**, selecione este arquivo e execute. O tamanho é obtido automaticamente do arquivo.
- Faça antes uma leitura completa da EEPROM atual para preservar um backup. A gravação completa substitui também identificação e áreas não usadas.
- Após gravar, a interface faz verificação integral. Uma leitura de volta deve produzir o SHA-256 abaixo.
- Este arquivo contém configuração EEPROM; não é o `MKA.bin` executável do microcontrolador e não deve ser enviado ao gravador de Flash/bossac.

```text
SHA-256: a54501351980aeef05636856efa92e8a668bbfaf2794a42b80f438af59d0dc1e
```

## Conteúdo

| Região | Endereços inclusivos | Bytes | Conteúdo |
|---|---|---:|---|
| USER | `0x000A–0x007E` | 117 | `MKA12\0`, CRC little-endian `2C 91`, parâmetros USER |
| SYSTEM | `0x100A–0x12F8` | 751 | `SC12\0\0`, CRC little-endian `69 35`, parâmetros SYSTEM |
| Número de série | `0x7D0A–0x7D1A` | 17 | Zeros: string vazia, conforme solicitado |
| Versão da configuração/máquina | `0x7D1B–0x7D23` | 9 | `1.0.5` com terminador e preenchimento zero |
| Demais endereços | Todas as lacunas | 31.874 | `FF`, preenchimento de área não usada pelo layout selecionado |

CRC-16, polinômio `0x1021`, valor inicial zero, somente sobre o payload de cada bloco. Os cabeçalhos de 8 bytes ficam fora do cálculo. Este CRC tem inicialização diferente do CRC do protocolo serial do leitor.

A versão `1.0.5` acima identifica o perfil selecionado; não altera nem declara a versão do firmware na Flash.

## Origem dos valores

O perfil **Composer A3-1.0.5.gc**, selecionado pelo usuário como validado, foi aplicado integralmente: **53 comandos**, sem parâmetros ignorados. Todos os valores persistidos estão relacionados no arquivo `_mapa.csv`, com endereço, representação hexadecimal e origem. O `.json` inclui também defaults anteriores à aplicação do perfil, hashes das fontes e os comandos consumidos.

Os campos que o perfil não define vêm do código local **MKA-firmware / COMPOSER_A3_V10** e das inicializações estáticas correspondentes. O fonte se identifica como `1.2.7dev`; o pacote do gravador contém MKA `1.2.6`. Ambos são associados nos arquivos locais aos identificadores de persistência `SC12`/`MKA12`, mas este trabalho não executou nem descompilou o binário MKA para comprovar equivalência completa. A estrutura foi conferida pelo fonte, pelo ABI ARM e pelos tamanhos/CRC registrados nos logs.

Principais parâmetros USER completados a partir do fonte:

| Parâmetro | Valor |
|---|---|
| Steps E / U / V | 410 / 98,5 / 410 |
| Home X / Y / Z | 0 / 0 / 0 |
| Offset do hotend T0 | X0 / Y0 / Z0 |
| Offset do hotend T1 | X−2,2 / Y−16,5 / Z0 |
| Offset de troca X / Y | **0 / 0** |
| Preset de pré-aquecimento | Hotend 230 °C / mesa 60 °C |
| Brilho | 90 |
| PID H0 | 6,86 / 0,52 / 22,62 |
| PID H1 | 9,494 / 0,63 / 35,408 |
| PID mesa | 79,8 / 16,2 / 98,06 |
| PID câmara | 10 / 0,1 / 300 (PID desativado no default da câmara) |

Os presets são configurações de menu; o arquivo não é um comando para aquecer. Calibrações particulares da máquina não podem ser recuperadas a partir dos defaults; esta é uma imagem de inicialização com o perfil escolhido, não uma cópia da EEPROM anterior.

A inversão dos motores, steps XYZ, velocidades, acelerações, sensores, ventiladores, caminhos de troca, carga/descarga e cartões SD seguem o perfil. Para M39 foi seguida a implementação do parser: **U = pino SS, D = divisor SPI, C = pino de detecção**, pois a apresentação nos logs troca os rótulos D/C. Os bytes finais são `3E FF 15 FF FF 08`, correspondentes ao perfil original, sem corrigir ou reinterpretar seus valores.

## Verificação realizada

- Macros originais avaliadas com o compilador ARM para Cortex-M3, sem execução do firmware e sem conexão à impressora.
- ABI confirmado: float32 little-endian, bool de 1 byte, enum Heater_type de 1 byte e ToolSwitchPos de 16 bytes (incluindo 3 bytes de padding). O padding foi inicializado em zero.
- 109 bytes de payload USER e 743 bytes de payload SYSTEM, totalizando os blocos de 117 e 751 bytes registrados pelo MKA.
- CRC USER **37164 / 0x912C** e SYSTEM **13673 / 0x3569** recalculados com dois algoritmos.
- O CRC SYSTEM coincide com **13673** nos logs locais de carga aceita. Isso reforça a consistência, mas um CRC de 16 bits não prova sozinho identidade de todos os bytes.
- Testes de corrupção em cada byte dos dois payloads, cobertura do mapa, finitude dos floats, repetição integral dos comandos do perfil, integridade das fontes e identidade vazia.
- Não houve gravação física, inicialização da impressora ou teste de movimentos. Como o MKA pode fazer homing e troca ao ligar, a primeira validação em bancada deve considerar esse comportamento já registrado no diagnóstico do projeto.

## Reproduzir

Na pasta `leitor_eeprom`:

```powershell
python tools/gerar_imagem_mka.py
python -m unittest discover -s tests -v
```

O gerador usa o ARM GCC existente no Sloeber; outro diretório pode ser informado com `--toolchain`. Não instala firmware, não abre portas seriais e não grava hardware. Os testes do arquivo pronto não exigem o compilador. A interface gráfica é exercitada pelos demais testes e exige Tk.
