# Comparação das duas EEPROMs — 04/11/2026

Análise dos seis arquivos fornecidos, usando o layout MKA12/SC12 do projeto. Nenhum dump original ou imagem de referência foi alterado.

## Repetibilidade das leituras

- 3 arquivos com SHA-256 `dfe768e3078328d2a3c783744fbd9d8190fc748eb013eaefdcd05ce41cbe8b01`: `chip_placa_original_erro_direcao_v1.bin`, `chip_placa_original_erro_direcao_v2.bin`, `chip_placa_original_erro_direcao_v3.bin`
- 3 arquivos com SHA-256 `47c8eaa84ba48d42a29601730fbf2f5f8050b40334c50fe399c77595b171add8`: `chip_placa_original_erro_tamanho_offset_v1.bin`, `chip_placa_original_erro_tamanho_offset_v2.bin`, `chip_placa_original_erro_tamanho_offset_v3.bin`

A igualdade foi determinada sobre todos os 32.768 bytes. Isso demonstra repetibilidade entre as capturas fornecidas; não prova ausência de falhas intermitentes, retenção ao longo do tempo nem independência do método de leitura.

## CRCs e direções

| Grupo | CRC USER armazenado/calculado | CRC SYSTEM armazenado/calculado | Direções X Y Z E U V | SYSTEM igual à referência |
|---|---|---|---|---|
| chip_placa_original_erro_direcao_v1.bin | 59322 / 59322 | 13673 / 13673 | `00 01 01 01 01 01` | Sim, byte a byte |
| chip_placa_original_erro_tamanho_offset_v1.bin | 24754 / 24754 | 13673 / 13673 | `00 01 01 01 01 01` | Sim, byte a byte |

Os blocos SYSTEM completos, incluindo cabeçalho, CRC, flags e padding, são idênticos à referência em ambos os grupos. Portanto, os dumps não sustentam uma diferença persistida de inversão de motores entre essas duas EEPROMs. Isso não demonstra que o comportamento de movimento seja igual: USER, estado em execução, leitura no barramento da impressora e condições elétricas ainda podem interferir.

## Campos diferentes da referência

### chip_placa_original_erro_direcao_v1.bin

Diferenças totais em relação à imagem de referência: **31 bytes**, sendo **0 em regiões não usadas** pelo layout selecionado.

| Endereço | Campo | Valor lido | Referência | Bytes lidos |
|---|---|---|---|---|
| 0x001A | steps_V | 416.0 | 410.0 | `0000d043` |
| 0x0026 | home_Z | -3.7999982833862305 | 0.0 | `2c3373c0` |
| 0x002E | hotend_1_X | -2.0 | -2.200000047683716 | `000000c0` |
| 0x0036 | hotend_1_Y | -17.700000762939453 | -16.5 | `9a998dc1` |
| 0x003E | hotend_1_Z | 2.9000000953674316 | 0.0 | `9a993940` |
| 0x004A | preheat_hotend | 215 | 230 | `d700` |

Campo SN bruto: `4150434133333130333300000000000000`.
Campo versão bruto: `312e302e346e770000`.

### chip_placa_original_erro_tamanho_offset_v1.bin

Diferenças totais em relação à imagem de referência: **40 bytes**, sendo **0 em regiões não usadas** pelo layout selecionado.

| Endereço | Campo | Valor lido | Referência | Bytes lidos |
|---|---|---|---|---|
| 0x002E | hotend_1_X | 0.0 | -2.200000047683716 | `00000000` |
| 0x0036 | hotend_1_Y | 0.0 | -16.5 | `00000000` |
| 0x0042 | switch_offset_X | 5.510494107080197e-39 | 0.0 | `04013c00` |
| 0x0046 | switch_offset_Y | -7.487457718802842e+16 | 0.0 | `040185db` |
| 0x004A | preheat_hotend | 8000 | 230 | `401f` |
| 0x004C | preheat_bed | 56197 | 60 | `85db` |
| 0x004E | lcd_brightness | 64 | 90 | `40` |

Campo SN bruto: `ffffffffffffffffffffffffffffffffff`.
Campo versão bruto: `312e302e346e770000`.

## Interpretação

- **Grupo erro_tamanho_offset:** o float32 em `0x0046–0x0049` tem bytes `04 01 85 DB` e representa exatamente **−74.874.577.188.028.416**. É o mesmo valor numérico anômalo registrado no histórico. O campo é o offset Y da troca, não o offset Y do bico.
- Nesse mesmo grupo, os presets são **H8000/B56197**, o brilho é 64 e o offset X da troca tem um valor subnormal muito pequeno, com bytes `04 01 3C 00`. O padrão não permite atribuir a causa a WP, capacitor, retenção ou outro componente.
- O CRC USER desse grupo é **24754**, confere e coincide com o log posterior à edição do menu. Os bytes demonstram a coexistência de checksum válido e parâmetros inadequados; não provam, isoladamente, a sequência exata que os produziu.
- Os 17 bytes do SN desse grupo são `FF`: não há terminador NUL no campo. Isso explica a possibilidade de a impressão da identificação avançar para a string de versão adjacente, como aparece nos logs.
- **Grupo erro_direcao:** o offset de troca X/Y está em zero e os valores USER diferentes são finitos e compatíveis com parâmetros personalizados: steps V416, home Z aproximadamente −3,8, offset T1 X−2/Y−17,7/Z2,9 e preset H215. Não é possível classificá-los como calibrações corretas ou incorretas apenas pelo dump.
- O grupo erro_direcao contém SN **APCA331033**, terminado em NUL. Os dois grupos têm versão de identificação **1.0.4nw**. Essa string não identifica por si só o executável instalado nem determina os valores SYSTEM.
- O fato de um arquivo estar nomeado erro_direcao não demonstra que os bits DIR estejam errados. Neste caso eles são iguais nos dois grupos e iguais ao perfil validado: X0 Y1 Z1 E1 U1 V1.

## Consequência prática

A anomalia de magnitude do grupo erro_tamanho_offset agora tem evidência direta no conteúdo fornecido. A causa do erro de direção do outro grupo continua sem determinação pelos dumps: não se deve inverter Y apenas para torná-lo diferente, pois os dois blocos SYSTEM já são iguais ao perfil validado.

Não foi criada imagem corrigida automaticamente. A referência anterior continua com SN vazio e defaults USER, conforme autorizado; o SN e os possíveis ajustes individuais encontrados agora foram apenas registrados. Uma futura correção deve definir se preserva esses ajustes ou se utiliza os defaults.

Para investigar diferença de comportamento na impressora, comparar o estado efetivamente carregado e o momento da anomalia (homing ou troca), com acionamento dos motores impedido, é mais informativo do que supor uma diferença nos seis bytes DIR. Leituras repetidas fora da impressora não validam seu barramento I2C durante o boot.
