> Avisos da publicação anterior do gravador. A pasta consolidada agora inclui também o pacote Flasher, MK4duo e referências recebidas; os avisos de escopo atual estão em [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). As exclusões e caminhos externos descritos abaixo são históricos.

# Proveniência e redistribuição

A licença GPLv3 existente no repositório remoto foi preservada em `LICENSE`.
As licenças e avisos dos componentes de terceiros continuam aplicáveis.

## MKA-firmware

- Origem: https://github.com/anisoprint/MKA-firmware
- Revisão: `6e02973b1b8f325040cc3dbf66ac545ffc5c06b3`.
- Snapshot dos arquivos rastreados, sem alterações, em
  `dependencies/firmwares/firmware codigo fonte/MKA-firmware`.
- GPLv3: texto integral em `dependencies/firmwares/firmware codigo fonte/MKA-firmware/LICENSE`.
  Cabeçalhos e avisos de componentes incorporados foram preservados.
- A cópia contém o fonte, configurações e recursos rastreados. Não depende de
  submódulo. O repositório original, inclusive `.git`, foi mantido no disco.

## Perfil e dados

O perfil Composer A3-1.0.5.gc veio do pacote local de configuração Anisoprint
MKA_1.2.6_ComposerA3_v1.0.x_15-05-2024. Seus comentários de autoria foram
preservados. É uma tabela de parâmetros/comandos, publicada para reproduzir os
valores, sem atribuir a ela uma nova licença. O pacote Composer Flasher e seus
executáveis não são necessários e não foram copiados.

A imagem gerada, mapas e seis dumps EEPROM são dados do projeto. Os dumps são
publicados sem alteração e podem conter identificação da máquina (ver relatório
de comparação). Não são executáveis MKA.bin. A imagem gerada tem SN vazio.

## Datasheet

Veja `datasheets/README.md`. O PDF local não declara uma permissão expressa para
redistribuição. Foi mantido localmente e referenciado por URL/revisão/hash.
Sua inclusão futura exige confirmar autorização/licença; não se afirma aqui que
uma permissão inexista fora do documento consultado.

## Ferramentas externas e REA

Python/Tk, pyserial, Pillow, Arduino AVR Boards e GNU Arm Embedded GCC são
instalados separadamente; não se incluem ambientes, compiladores nem dependências
instaladas. `requirements*.txt` e `REPRODUZIR.md` registram o necessário.

REA está fora da pasta solicitada, em `../REA`, origem https://github.com/morluto/rea,
revisão local `250dc81cd6b887f41a4078b65ca7a78628d1c541`, licença MIT.
A inspeção encontrou alterações nos submódulos third_party/unblob e third_party/wakaru.
Não é chamado pelo gravador, gerador ou testes. Por isso não foi incorporado,
nem convertido em submódulo, e nenhum metadado ou alteração local foi removido.
MK4duo separado, outros datasheets e firmwares da pasta pai também não são entradas
deste projeto; o fonte MKA necessário já está incluído.

## Exclusões de publicação

- `build/`, `__pycache__/`, ambientes virtuais e dependências instaladas: regeneráveis.
- `tools/mka_build/*.o` e `*.raw`: intermediários regeneráveis; fontes `.cpp` preservadas.
- Credenciais, `.env`, chaves e temporários: excluídos pelos padrões do `.gitignore`.
- PDF AT24C256C: decisão de redistribuição pendente conforme descrito acima.

Os arquivos locais excluídos do Git não foram apagados.
