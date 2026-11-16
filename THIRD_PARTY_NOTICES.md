# Proveniência e avisos de terceiros

Este conjunto organiza os materiais locais da investigação. Não se atribui uma nova licença universal aos firmwares, executáveis, documentos ou dados de terceiros.

| Material | Origem registrada | Licença/aviso preservado |
|---|---|---|
| Gravador Uno e ferramentas | Projeto local `leitor_eeprom` | Texto GPLv3 existente em `gravador/LICENSE`; avisos anteriores em `gravador/THIRD_PARTY_NOTICES.md` |
| MKA-firmware | Snapshot associado a `https://github.com/anisoprint/MKA-firmware`, revisão `6e02973b1b8f325040cc3dbf66ac545ffc5c06b3` | `gravador/dependencies/firmwares/firmware codigo fonte/MKA-firmware/LICENSE` e cabeçalhos originais |
| MK4duo | Repositório local da base de firmware, revisão `0d8ee93b259bdfb2fb36487488f15d7e27ffb950` | `firmwares/MK4duo/LICENSE` e avisos internos |
| Composer Flasher, bossac, bibliotecas, perfis e pacotes MKA | Pasta local recebida `Composer Flasher` | Arquivos, configurações e comentários distribuídos foram mantidos; não se presume que a licença do gravador Python cubra esse pacote |
| Datasheets | Quatro PDFs locais usados na investigação | Copyright e avisos internos dos documentos preservados |
| Guia de flashing | DOCX local indicado como fornecido pela Anisoprint | Cópia integral do documento recebido |
| Imagem reconstruída e dumps | Arquivos do projeto, com hashes em manifestos | Dumps sem alteração, inclusive identificação da máquina; imagem reconstruída com SN vazio |

A organização anterior do gravador optava por não incluir os executáveis do Flasher e o PDF AT24C256C. Esta nova pasta os inclui para atender ao pedido de reunir o material completo. Os avisos daquela publicação permanecem como registro do escopo anterior, acompanhados de nota editorial.

Não foi identificada nos registros desta consolidação uma licença de redistribuição que abranja conjuntamente todos os executáveis proprietários, PDFs e o guia recebido. A presença de um arquivo nesta pasta não equivale a uma autorização adicional do titular nem altera seus avisos. Este registro documenta a proveniência, sem declarar que tais permissões inexistam em outros documentos.

Python/Tk, pyserial, Pillow, Arduino IDE/cores, compiladores e .NET são dependências externas, com seus próprios termos. Instalações locais, fontes Windows e ambientes de execução não foram copiados. O HEX do Uno deriva do sketch e do core AVR/Wire; sua receita de compilação e versões estão preservadas.

`docs/PROVENIENCIA.json` permite relacionar cada cópia à origem local. `MANIFESTO_SHA256.json` identifica os bytes finais entregues. Não foram publicados repositórios remotos nesta atividade.
