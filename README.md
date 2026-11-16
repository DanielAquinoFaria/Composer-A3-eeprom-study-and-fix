# Composer A3 EEPROM Study and Fix

**Issue resolved via external programming of the AT24C256C EEPROM using an Arduino Uno.** On 11/16/2026, the machine operator confirmed the resolution and identified the file used as `AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.bin`.

This repository compiles the investigation process, evidence, available firmwares, and complete programmer software. The success report comes from the operator; the automated tests in this release verify files and software without operating the printer.

## Summary of the Operation Performed

The Composer A3 exhibited anomalous Y-axis movement during tool changes, froze on the boot screen, and displayed EEPROM configuration error messages. Reflashing the controller firmware and zeroing the nozzle offsets via the menu did not eliminate the observed issue.

1. **Investigation:** Boot and flashing logs, MKA source code, configuration profiles, and hardware documentation were gathered to distinguish the program stored in Flash from the parameters persisted in the external EEPROM.
2. **Preservation and comparison:** Six 32,768-byte dumps, split into two groups of three identical captures, made it possible to locate the `switch_offset_y` field at address `0x0046`. In the group with the magnitude error, the bytes `04 01 85 DB` represent **−74,874,577,188,028,416**, even with a valid USER CRC. The SYSTEM blocks were identical across both groups and the reference.
3. **Reconstruction:** A complete AT24C256C image was generated from the MKA source defaults and initializations, applying the 53 commands from the `Composer A3-1.0.5.gc` profile. Tool-change offsets were set to zero, presets and remaining parameters were reconstructed, CRCs were calculated, and the serial number was left blank.
4. **External programming:** The image was flashed onto the EEPROM with an **Arduino Uno**, using the programmer firmware and Python/Tkinter interface included in this project. The software provides backup, read, write, read-back, and full comparison features.
5. **Result:** The operator confirmed that flashing this image resolved the issue and explicitly identified the file used. Software and file integrity tests are documented separately from the reported physical outcome.

The core conclusion is that **a valid CRC does not guarantee valid motion parameters**. The recovery restored a known configuration; the initial root cause of the byte alteration remains undetermined. Suggested improvements for MKA are recommendations and were not implemented as part of this recovery.

**Resumo em português:** Este projeto documenta a recuperação de uma Anisoprint Composer A3 realizada por meio da gravação externa de uma imagem reconstruída da EEPROM AT24C256C com Arduino Uno. Seis dumps da EEPROM revelaram um offset de troca no eixo Y inválido, mesmo com CRC USER válido. Uma imagem completa de configuração foi reconstruída a partir dos defaults do MKA e do perfil Composer A3-1.0.5, e o operador confirmou a recuperação. A causa original da alteração dos bytes permanece indeterminada. Os relatórios completos estão disponíveis em português brasileiro e inglês abaixo.

## Where to Start

- **Professional PDF Reports:** [Brazilian Portuguese](docs/relatorios/Relatorio_Recuperacao_EEPROM_Composer_A3_PT-BR.pdf) and [English](docs/relatorios/EEPROM_Recovery_Report_Composer_A3_EN.pdf), nine pages each.
- [Investigation and Resolution Report](RELATORIO.md): timeline of events, hypotheses, evidence, fixes, and open questions.
- [Recovery Procedure](docs/PROCEDIMENTO.md): wiring, backup, flashing, and verification.
- [EEPROM Image Used in the Solution](gravador/imagens/AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.bin).
- [Complete Programmer](gravador/README.md): Python/Tkinter interface, Uno firmware, protocol, tests, and tools.
- [Inventory and Versions](docs/INVENTARIO.md), [Package Validation](docs/VALIDACAO_PACOTE.md), and [GitHub Publishing](docs/PUBLICACAO.md).

## Correct File for Each Target

| Artifact | Target | Purpose |
|---|---|---|
| `gravador/imagens/AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.bin` | External AT24C256C EEPROM, starting at `0x0000` | Reconstructed configuration that resolved this case; 32,768 bytes |
| `gravador/firmware/eeprom_uno/eeprom_uno.ino` | Arduino Uno R3 / ATmega328P | Reader/programmer source code |
| `gravador/firmware/precompilado/eeprom_uno.hex` | Arduino Uno Flash, preserving its bootloader | Convenience precompiled binary of the same programmer |
| `firmwares/Composer Flasher/Composer A3/.../MKA.bin` or `.fw2` | Printer controller, via the Composer Flasher workflow | Executable MKA firmware; not an EEPROM image |
| `Composer A3-1.0.5.gc` | Parameters parsed by MKA | Profile used to reconstruct the configuration |

**Do not mix up these targets.** The confirmed recovery consisted of writing the configuration image to the EEPROM. The historical Flasher package is included for documentation/reproduction purposes, not as a mandatory step for reflashing the controller.

EEPROM image SHA-256:

```text
a54501351980aeef05636856efa92e8a668bbfaf2794a42b80f438af59d0dc1e
