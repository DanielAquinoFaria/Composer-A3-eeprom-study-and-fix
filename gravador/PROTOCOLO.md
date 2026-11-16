# Protocolo serial V1

115200 baud, 8 bits, sem paridade, 1 stop bit, sem controle de fluxo. Uma requisição por vez; aguarde a resposta antes da próxima. Ao abrir a porta, aguarde 2,2 s pelo reset do Uno e descarte os bytes antigos.

Quadro ASCII: `CORPO*CCCC\n`. Respostas terminam em CR LF (ambos aceitos pelo cliente). CRC de quatro dígitos hexadecimais sobre os bytes ASCII do CORPO, sem `*` nem terminadores: CRC-16/CCITT-FALSE, poly `0x1021`, init `0xFFFF`, refin/refout false, xorout `0`. Vetor `123456789` → `29B1`.

Campos separados por espaço. Números de comandos são **decimais**, exceto o payload e o CRC. `seq` é incrementado a cada requisição de 1 a 65535, retornando a 1. O firmware ecoa a sequência; não faz cache/deduplicação de gravações. Não retransmita WRITE automaticamente.

| Corpo enviado | Corpo de resposta |
|---|---|
| `seq HELLO` | `seq OK EEPROM_UNO_V1` |
| `seq PROBE dev` | `seq OK PROBE` |
| `seq READ dev addr n` | `seq OK HEX` |
| `seq WRITE dev addr n HEX` | `seq OK WRITTEN` |

`dev`: 80–87 (0x50–0x57). `addr`: 0–32767. `n`: 1–30, e `addr+n <= 32768`. WRITE também exige `(addr % 64)+n <= 64`. HEX tem exatamente `2*n` caracteres. WRITE só retorna sucesso após reler/comparar o bloco. READ é protegido por CRC na resposta, incluindo dados e sequência.

Falhas: `seq ERR CODIGO`, com `FRAME`, `CRC`, `ARGS`, `DEVICE`, `RANGE`, `HEX`, `PROBE`, `I2C_WRITE`, `I2C_READ`, `VERIFY`, `OVERFLOW`. Quando não há sequência confiável, usa `0`. Linha longa é descartada até LF; quadro parcial expira após 1 s sem bytes. Timeout Wire: 25 ms, com reset do periférico TWI; timeout serial no PC: 2 s.

O cliente fecha a porta em erro de protocolo/serial ou resposta ERR. Fechar a porta não desfaz uma gravação que já ocorreu. Reconecte e leia a memória para determinar seu estado. CRC é detecção de erros acidentais, não autenticação.
