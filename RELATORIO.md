# Relatório de investigação e resolução — Anisoprint Composer A3

**Edições profissionais em PDF:** [Português brasileiro](docs/relatorios/Relatorio_Recuperacao_EEPROM_Composer_A3_PT-BR.pdf) | [English](docs/relatorios/EEPROM_Recovery_Report_Composer_A3_EN.pdf).

**Consolidação:** 16 de novembro de 2026.  
**Equipamento:** Composer A3, controladora Ultratronics/SAM3X e EEPROM externa AT24C256C.  
**Resultado:** resolução informada pelo operador após gravar a imagem reconstruída na EEPROM com o gravador Arduino Uno.

## 1. Resultado e alcance da conclusão

A intervenção que resolveu o problema foi substituir o conteúdo da EEPROM externa pela imagem completa `AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.bin`, usando Arduino Uno e o software de leitura/gravação desenvolvido no projeto. O operador confirmou expressamente tanto o sucesso quanto esse nome de arquivo nesta consolidação.

O diagnóstico encontrou um parâmetro de movimento inadequado no bloco USER: `switch_offset_y`, offset Y aplicado durante a troca de ferramenta. Nos dumps associados ao erro de magnitude, seus quatro bytes representam exatamente **−74.874.577.188.028.416**, valor registrado no comportamento da máquina. O CRC desse bloco era válido. Portanto, a verificação de checksum não era suficiente para aprovar o uso dos parâmetros.

A reconstrução restabeleceu uma configuração completa, com offsets de troca zerados, parâmetros USER definidos, SYSTEM correspondente ao perfil Composer A3-1.0.5 e identificação consistente. A intervenção alterou vários campos ao mesmo tempo; o sucesso não demonstra que a alteração isolada de `switch_offset_y` seria suficiente em todas as condições.

**A origem inicial dos bytes inadequados permanece indeterminada.** Não há comprovação de defeito físico da EEPROM, problema de retenção, capacitor defeituoso ou falha específica de alimentação. O sucesso da recuperação comprova o resultado informado para este equipamento, não uma correção definitiva de todos os caminhos de falha do firmware.

## 2. Como ler a cronologia

A organização é semi cronológica: os marcos datados vêm dos logs e relatórios; acontecimentos descritos sem data são agrupados pela sequência relatada. Datas em nomes de arquivo são identificadas como tal. A data de 16/11/2026 registra a confirmação do resultado, não necessariamente o dia da gravação física.

| Marco | Evidência disponível | Evolução do entendimento |
|---|---|---|
| Uso inicial após gravação, sem data exata | Dossiê inicial | Calibrações e uma primeira impressão funcionam; a falha aparece depois de desligar/ligar |
| 27/08/2026, 10:54 e 11:21 | Dois logs do Composer Flasher | Flash gravada segundo o aplicativo, mas retorno a `Status:I` não ocorre; boot acusa erro USER |
| Edição dos offsets e reinicializações; captura nomeada `log29-10v1.md` | Dossiê e log posterior | Alerta desaparece, porém permanece `M217 Yovf`, agora com CRC USER aceito |
| Troca da placa externa, sem data exata | Dossiê | Comportamento de movimento muda; conteúdo da memória passa a ser objeto direto da investigação |
| 30/10/2026 | Diagnóstico técnico | Fonte explica carga antes do CRC, defaults incompletos e uso do offset de troca no boot |
| 04/11/2026 | Revisão da imagem, comparação dos dumps e validação do gravador | Reconstrução reproduzível; dumps localizam o valor anômalo e revisam a hipótese sobre direção |
| 16/11/2026 | Confirmação do operador | Imagem identificada e resolução com Arduino Uno confirmada |

## 3. Primeira etapa — sintomas e tentativa de recuperação por firmware

O [dossiê inicial](evidencias/dossie_inicial.md) descreve uma máquina que completava homing, calibração e uma primeira impressão após gravação, mas apresentava comportamento anômalo em inicializações posteriores. Durante a troca de ferramenta, Y assumia uma magnitude incompatível com o curso mecânico. A interface permanecia na tela de início e a emergência serial ainda respondia.

Havia razões para investigar firmware, configuração persistida e hardware: o problema surgia depois de um ciclo de alimentação; a tela reportava falha ao ler USER; e outra placa de EEPROM alterava o comportamento percebido.

Nos dois [logs de 27/08](evidencias/logs/), o Flasher informa gravação e verificação bem-sucedidas de **236.720 bytes** no microcontrolador. Em seguida espera por `Status:I` e aborta após aproximadamente um minuto. O log do boot contém:

```text
SC12 stored system settings retrieved (751 bytes; crc 13673)
EEPROM usercfg CRC mismatch - (stored) 64898 != 14619 (calculated)
M217 X0.000 Yovf
M145 H8000 B56197
```

O cabeçalho dessas tentativas cita `Composer A3-1.0.3nw`; a identificação impressa no boot cita `1.0.4nw`; o perfil escolhido mais tarde para reconstrução foi `1.0.5`. Esses registros pertencem a etapas diferentes. A string de identificação não deve ser tratada como prova da versão exata do executável.

**Problema possível:** falha na instalação do firmware ou na comunicação com a máquina.  
**Sugestão à época:** verificar o resultado da Flash e separar o timeout posterior do ato de programar o MCU.  
**Conclusão:** os logs relatam êxito na Flash, mas a configuração USER continuava problemática. Regravar o programa não demonstrou reconstruir todos os dados da EEPROM externa.

Os logs registram modo de desenvolvedor com verificações de prontidão/modelo ignoradas. Isso é informação histórica, não recomendação para repetir esse modo.

## 4. Segunda etapa — alteração no menu e desaparecimento do alerta

Após o alerta de EEPROM, o menu ainda mostrava offsets de bico X −2,2 / Y −16,5 / Z 0. Esses valores também existem nos defaults do fonte, portanto sua presença não comprovava leitura correta da memória. O operador zerou os offsets pelo menu; o alerta deixou de aparecer, mas o comportamento anômalo continuou.

O [log posterior](evidencias/logs/log29-10v1.md) mostra USER aceito com **117 bytes e CRC 24754**, ao mesmo tempo em que registra:

```text
M218 T1 X0.000 Y0.000 Z0.000
M217 X0.000 Yovf
M145 H8000 B56197
```

**Problema identificado:** offset do bico e offset de troca são campos distintos. `M218` altera a geometria entre os bicos; não corrige `switch_offset_y`.

O [diagnóstico de 30/10](evidencias/diagnostico_2026-10-30.md) descreve a cadeia no fonte MKA:

1. `Load_Usr()` lê diretamente para variáveis de execução e só depois compara o CRC.
2. A restauração por `Factory_Settings()` não redefine todos os campos, entre eles offsets de troca, presets e brilho.
3. A edição pelo menu salva o bloco USER inteiro, podendo gravar novamente parâmetros inadequados com um novo CRC coerente.
4. O boot prossegue para homing e troca conforme o sucesso de SYSTEM; a validação de USER não impede necessariamente essa sequência.
5. O offset de troca é somado aos pontos marcados `K1`, alimentando o destino de movimento.

Esse mecanismo explica como o aviso pode sumir sem eliminar o problema. A sequência é compatível com logs e dumps, mas não reconstitui cada transação física que originou a alteração inicial.

**Sugestão diagnóstica:** verificar o valor efetivo do offset de troca e a configuração inteira antes de persistir. No parser do fonte analisado, `M217 A0 B0` altera offsets de troca; a apresentação `M217 X/Y` no relatório não corresponde diretamente a esses argumentos. Isso é referência técnica, não um comando de recuperação a executar indiscriminadamente.

**Solução adotada:** reconstrução integral fora da impressora, com valores conhecidos. As melhorias no firmware mencionadas ao final deste relatório são propostas; não foram implementadas neste pacote.

## 5. Terceira etapa — EEPROM externa, hipóteses elétricas e aquisição

A EEPROM fica em uma placa externa à Ultratronics. A marcação `2ECL` foi associada ao AT24C256C nos documentos consultados: capacidade de **256 kbits = 32.768 bytes**. Foram preparados recursos para aquisição externa, incluindo um [leitor ESP32-C3](evidencias/leitor_esp32c3/README.md), e posteriormente um gravador completo para Uno.

Há seis dumps disponíveis, três por grupo de comportamento. Não foi encontrado neste pacote um manifesto de aquisição que permita atribuir com certeza cada dump a uma sessão/dispositivo específico; o nome do arquivo identifica o grupo, não comprova sozinho seu método de leitura.

A troca da placa foi inicialmente interpretada no dossiê como evidência de configuração de direção diferente. Essa conclusão precisava ser testada nos bytes. A comparação posterior mostrou **SYSTEM idêntico nos dois grupos e na referência**. Logo, a mera mudança de comportamento ao trocar a placa não confirma diferença persistida de inversão de motores, nem defeito físico do chip.

Foram consideradas alimentação, contatos, I²C, WP, retenção e conteúdo/layout. O roteiro recomendado foi preservar dumps, repetir leituras, conferir CRC e parâmetros e só então programar. Medições elétricas e testes de retenção não foram documentados como causa comprovada.

O circuito de bancada do Uno usa WP em D7 com pull-up, pull-ups em SDA/SCL e desacoplamento entre VCC/GND. Um capacitor hipotético entre WP e VCC não substitui pull-up e não exige uma alteração específica no BIN. O comportamento elétrico dessa montagem original não foi demonstrado por oscilograma ou medições anexas.

Também foi revista a identificação dos botões: no encapsulamento SAM3X LQFP144 analisado, pino 130 é PC0/ERASE, enquanto NRST e NRSTB ocupam outros terminais. Acionar ERASE não apaga a EEPROM I²C. Essa observação evita confundir reset, apagamento da Flash e reconstrução da configuração externa.

## 6. Quarta etapa — confirmação nos dumps

A [comparação de 04/11](gravador/imagens/comparacao/COMPARACAO_EEPROMS.md) está acompanhada dos [seis binários originais](gravador/imagens/clones/). A conferência independente desta consolidação reproduziu os resultados centrais.

| Grupo de dumps | Repetição integral | CRC USER | CRC SYSTEM | Resultado relevante |
|---|---|---:|---:|---|
| `erro_direcao_v1/v2/v3` | Três arquivos iguais | 59322, válido | 13673, válido | SYSTEM igual à referência; USER contém ajustes individuais |
| `erro_tamanho_offset_v1/v2/v3` | Três arquivos iguais | 24754, válido | 13673, válido | Offset Y de troca com valor anômalo; presets inadequados |

No segundo grupo:

| Campo | Endereço inicial | Conteúdo observado | Imagem reconstruída |
|---|---|---|---|
| Offset X da troca | `0x0042` | Float subnormal; bytes `04 01 3C 00` | 0 |
| Offset Y da troca | `0x0046` | Bytes `04 01 85 DB`; −74.874.577.188.028.416 | 0 |
| Preset do hotend | `0x004A` | 8000 | 230 |
| Preset da mesa | `0x004C` | 56197 | 60 |
| Brilho | `0x004E` | 64 | 90 |
| Identificação SN | `0x7D0A`, 17 bytes | Todos `FF`, sem terminador NUL | String vazia terminada em zero |

Os presets são parâmetros de menu; sua presença não demonstra que o aquecimento a esses valores tenha sido executado.

**Mudança importante no diagnóstico:** a relação entre a magnitude observada e os bytes deixou de ser apenas uma hipótese do fonte. O valor está diretamente presente no dump, no campo esperado. Em contrapartida, a hipótese de inversões de motor diferentes entre os dois conteúdos não foi sustentada.

Leituras repetidas iguais demonstram repetibilidade das capturas disponíveis; não certificam o barramento da impressora durante o boot nem retenção por tempo indefinido.

## 7. Quinta etapa — reconstrução do binário de configuração

A imagem foi produzida pelo [gerador incluído](gravador/tools/gerar_imagem_mka.py), usando o snapshot MKA e os **53 comandos** do perfil `Composer A3-1.0.5.gc`. Campos não definidos pelo perfil receberam defaults e inicializações do fonte, sem importar USER dos dumps problemáticos.

| Região | Faixa inclusiva | Tamanho | Conteúdo |
|---|---|---:|---|
| USER | `0x000A–0x007E` | 117 bytes | `MKA12`, CRC `0x912C` / 37164 e parâmetros USER |
| SYSTEM | `0x100A–0x12F8` | 751 bytes | `SC12`, CRC `0x3569` / 13673 e perfil SYSTEM |
| CONST | `0x7D0A–0x7D23` | 26 bytes | SN vazio e versão de identificação `1.0.5` |
| Lacunas | Demais endereços | 31.874 bytes | Preenchimento `FF` |

O CRC é calculado sobre o payload de cada bloco, excluindo o cabeçalho de oito bytes, com polinômio `0x1021` e início zero. Esse CRC difere na inicialização do CRC usado pelo protocolo serial do gravador.

A [revisão técnica](gravador/imagens/REVISAO.md), o [mapa CSV](gravador/imagens/AT24C256C_Composer_A3_1.0.5_MKA_sem_SN_mapa.csv) e o [manifesto da imagem](gravador/imagens/AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.json) preservam os campos, origens e hashes. A avaliação das macros usou ABI ARM, floats little-endian de 32 bits e padding de estruturas explicitamente definido.

O fonte local identifica-se como **1.2.7dev**; o pacote de firmware é rotulado **1.2.6**. O layout e os registros sustentaram a reconstrução, e o operador agora confirmou a recuperação com a imagem. Não foi demonstrada equivalência integral entre o fonte disponível e todas as instruções do executável instalado. A entrega não apresenta o fonte 1.2.7dev como uma reprodução comprovada do MKA.bin 1.2.6.

## 8. Sexta etapa — gravador Arduino Uno e resolução

O [gravador](gravador/README.md) contém firmware C++ para Uno R3/ATmega328P e interface Python/Tkinter. Permite leitura, gravação e comparação por endereço, com backup integral, SHA-256 e modo de simulação.

O software limita os blocos de escrita aos buffers Wire e às páginas da EEPROM, espera o término da escrita por ACK polling, controla WP, relê os blocos e executa verificação integral ao final. Erros encerram a operação sem repetir cegamente a escrita. Cancelamento pode deixar conteúdo parcial; por isso backup e releitura fazem parte do procedimento.

**Confirmação do operador, registrada em 16/11/2026:** usar o novo binário na EEPROM com o gravador em Arduino Uno resolveu o problema. Em resposta à identificação do arquivo, confirmou `AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.bin`.

O hash da cópia entregue foi conferido:

```text
a54501351980aeef05636856efa92e8a668bbfaf2794a42b80f438af59d0dc1e
```

Não foi fornecido um dump pós-gravação, log final de boot ou contagem de ciclos de alimentação/impressões. Portanto, não se atribui à confirmação uma campanha de ensaios que não foi relatada. A [validação do pacote](docs/VALIDACAO_PACOTE.md) separa testes automatizados, compilação e resultado físico informado.

## 9. Matriz de problemas, sugestões e soluções

| Problema ou hipótese | Evidência/status | Sugestão ou ação correspondente | Resultado neste caso |
|---|---|---|---|
| Flash incorreta/incompleta | Flasher relatou programação concluída; boot ainda falhava | Separar programa, RAM e EEPROM; preservar os logs | Regravação da Flash não solucionou o conteúdo USER observado |
| USER com CRC rejeitado | 64898 armazenado contra 14619 calculado | Inspecionar dump, layout, transporte e parâmetros | Diagnóstico direcionado à configuração persistida |
| CRC válido com parâmetros inadequados | Dump com CRC 24754 e Y anômalo | Validar faixas e semântica além do checksum | Imagem reconstruída substituiu o bloco inadequado |
| Zerar offsets do bico não corrige a troca | `M218` zerado e `M217 Yovf` persistente | Distinguir `hotend_offset` de `switch_offset` | Reconstrução restabeleceu ambos conforme defaults |
| Direção diferente ao trocar EEPROM | Relato de movimento; SYSTEM igual nos dumps | Conferir fase do movimento, RAM carregada, endstops e barramento | Causa específica não determinada; não se inverteu Y por suposição |
| Espera na tela inicial | Fluxo do boot ativa status depois de homing/troca | Investigar destino/planner antes de atribuir defeito ao LCD | Mecanismo do fonte compatível com o sintoma |
| WP, contato, alimentação, retenção | Hipóteses sem medição conclusiva anexada | Isolar EEPROM, medir sinais, repetir leituras e verificar escrita | Não classificados como causa comprovada |
| SN sem terminador | 17 bytes `FF` no grupo anômalo | Definir identidade de modo explícito | Imagem usa SN vazio; não restaura número de série individual |
| Defaults incompletos e erros I²C mal propagados | Observados no fonte analisado | Corrigir software e testar falhas de carga/gravação | Recomendações futuras; firmware da impressora não foi alterado nesta entrega |

## 10. Melhorias recomendadas e manutenção

Para o firmware MKA, recomenda-se ler para uma estrutura temporária; validar transporte, versão, CRC, finitude e limites; aplicar à execução somente depois de aceitar o bloco; e redefinir todos os campos em uma restauração. O boot deve impedir movimentos quando a configuração necessária for rejeitada.

Também convém propagar NACK, leituras curtas e erros acumulados, interromper escritas que falharam e corrigir a divergência entre argumentos e apresentação de `M217`. Limites de movimento devem considerar a rota real de troca, que pode sair da área útil de impressão, e a representação de passos no planner.

Para a máquina recuperada, preservar um backup posterior à calibração, acompanhado de data e hash, permite distinguir futuras alterações de configuração de falhas de retenção/transporte. O [procedimento](docs/PROCEDIMENTO.md) propõe conferir boot, parâmetros, endstops, homing, troca, calibração e ciclos de energia de forma progressiva. Essas etapas são recomendações de acompanhamento, não ensaios declarados como já concluídos.

## 11. Fontes e rastreabilidade

- [Dossiê inicial](evidencias/dossie_inicial.md): sintomas e intervenções relatadas, antes da revisão pelas capturas.
- [Logs originais](evidencias/logs/): duas tentativas de agosto, captura USER rejeitada e captura posterior com CRC válido.
- [Diagnóstico de 30/10](evidencias/diagnostico_2026-10-30.md): referências de funções e linhas do fonte, hipóteses e plano de testes.
- [Comparação de 04/11](gravador/imagens/comparacao/COMPARACAO_EEPROMS.md): seis dumps, campos, igualdade SYSTEM e CRCs.
- [Revisão da imagem](gravador/imagens/REVISAO.md): reconstrução, defaults, serialização e limites de versão.
- [Fonte MKA incluído](gravador/dependencies/firmwares/firmware%20codigo%20fonte/MKA-firmware/): snapshot utilizado pelo gerador.
- [Confirmação da resolução](docs/CONFIRMACAO_OPERADOR.md): registro textual da informação fornecida nesta consolidação.
- [Proveniência por arquivo](docs/PROVENIENCIA.json) e [manifesto da entrega](MANIFESTO_SHA256.json): origem relativa, tamanho e SHA-256 para auditoria.
