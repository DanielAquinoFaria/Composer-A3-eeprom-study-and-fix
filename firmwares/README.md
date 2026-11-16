# Firmwares e Composer Flasher

Esta pasta preserva os pacotes usados como referência durante a investigação. **A solução confirmada usa o BIN de configuração da EEPROM em `../gravador/imagens/`, não os executáveis desta pasta.**

- [Composer Flasher](Composer%20Flasher/): pacote local completo, com aplicação Windows, bossac, dependências distribuídas e pacotes Composer A3/A4.
- [MKA-firmware](MKA-firmware/): código-fonte completo, configurações, perfis e licença do MKA usado como referência na reconstrução. A [cópia nas dependências do gravador](../gravador/dependencies/firmwares/firmware%20codigo%20fonte/MKA-firmware/) também foi mantida para preservar os caminhos do gerador e seus testes.
- [MK4duo](MK4duo/): snapshot histórico da base de firmware; não foi compilado/instalado como parte da recuperação.
- [Inventário e hashes](../docs/INVENTARIO.md): versões e identificação dos principais binários.

O Flasher requer o runtime Windows Desktop .NET 8 declarado no arquivo `FlasherWin.runtimeconfig.json`. Ele não foi executado nesta consolidação. O [guia recebido](../referencias/Firmware%20Flashing%20Guide%20for%20Composer.docx) foi preservado para consulta.

Não usar pacotes A4 ou firmware Nextion/MK4duo genérico na A3. A existência desses arquivos no arquivo histórico não comprova compatibilidade com a máquina recuperada. O fonte MKA 1.2.7dev disponível não foi demonstrado como reprodução binária exata do MKA 1.2.6 distribuído.
