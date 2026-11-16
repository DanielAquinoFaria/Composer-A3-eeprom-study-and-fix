> Registro histórico de 04/11/2026. Os limites abaixo se referem àquela sessão. A compilação e os testes foram repetidos na entrega consolidada; o operador confirmou posteriormente a recuperação física. Veja [validação atual](../docs/VALIDACAO_PACOTE.md).

# Validação — 04/11/2026

## Executado

`python -m unittest discover -s tests -v`: **10 testes aprovados**.

- CRC com vetor de referência e quadros inválidos.
- Fracionamento em limites de página de 64 bytes e blocos Wire de até 30 bytes.
- Rejeição de faixas vazias, negativas e fora da capacidade.
- Leitura/gravação/verificação integral de 32.768 bytes por transporte serial simulado.
- Preservação dos bytes fora de uma gravação parcial desalinhada.
- Falhas de CRC, sequência, timeout e verificação: fechamento da conexão, sem repetir escrita.
- Cancelamento entre blocos e leitura cancelada.
- Localização do endereço exato de divergência.
- Memória simulada e substituição atômica do arquivo de leitura.
- Interface Tkinter: conectar em simulação, gravar, verificar, ler para arquivo e desconectar.

`python tools/build_firmware.py`: **compilação e link aprovados** com Arduino AVR Boards 1.8.6 e avr-gcc 7.3.0-atmel3.6.1-arduino7, destino ATmega328P/Uno, clock de 16 MHz.

- Programa: **8.466 bytes** (cabe no espaço de 32.256 bytes disponível com bootloader padrão do Uno).
- RAM estática: **721 bytes** de 2.048; não inclui uso dinâmico da pilha durante execução.
- Resultado: `build/eeprom_uno.hex`, sem bootloader.

## Limites

Não foi feito upload nem acesso a uma EEPROM física. Testes com transporte simulado exercitam o cliente Python; não comprovam temporização elétrica ou execução do firmware no hardware. A interface foi instanciada e exercitada por teste funcional; não houve inspeção visual manual em diferentes escalas de tela.

## Roteiro para bancada

1. Confira a orientação do CI, 5 V/GND, pull-ups e capacitor antes de alimentar.
2. Carregue o sketch no Uno. Confira WP alto em repouso/reset (pull-up externo).
3. Conecte pela interface no endereço dos pinos A0–A2.
4. Faça duas leituras completas em arquivos diferentes. Compare os hashes SHA-256; guarde o backup fora da pasta de trabalho.
5. Em uma EEPROM de teste, grave um arquivo conhecido em `0x003F` com pelo menos 100 bytes, cruzando páginas. Confira a verificação e faça nova leitura completa para confirmar que o restante foi preservado.
6. Teste o último byte em `0x7FFF` e uma imagem completa de 32.768 bytes.
7. Para conferir proteção, desligue o circuito, desconecte D7 de WP e ligue WP a VCC. Uma tentativa de gravar conteúdo diferente deve resultar em VERIFY. Restaure as ligações com a alimentação desligada.
8. Em memória de teste, cancele uma gravação e confira a condição parcial; restaurar exige regravar o backup.

Não use a memória original como primeiro teste de gravação.
