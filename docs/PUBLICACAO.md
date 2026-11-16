# Publicar a pasta no GitHub

A pasta `composer-a3-recuperacao-eeprom` é a raiz do projeto **Composer A3 eeprom study and fix**. O repositório público está em [DanielAquinoFaria/Composer-A3-eeprom-study-and-fix](https://github.com/DanielAquinoFaria/Composer-A3-eeprom-study-and-fix).

O relatório e os links internos usam caminhos relativos. O software do gravador inclui sua fonte MKA e seu perfil; não depende das pastas antigas `leitor_eeprom`, `eeprom-publication-*` ou `REA` ao lado do projeto.

## Conferência local

Dentro da pasta:

```powershell
python tools/verificar_pacote.py
python -B -m unittest discover -s gravador/tests -v
```

O primeiro comando usa apenas a biblioteca padrão Python e confere os arquivos contra o manifesto. O segundo requer pyserial e Tk. Não abre porta serial física.

## Obter o projeto usando Git

Para obter uma cópia local:

```powershell
git clone https://github.com/DanielAquinoFaria/Composer-A3-eeprom-study-and-fix.git
cd Composer-A3-eeprom-study-and-fix
python tools/verificar_pacote.py
```

O conteúdo inclui arquivos binários de firmware, Flasher e recursos históricos Nextion. Usar Git no computador facilita o envio do conjunto. O ZIP de entrega deve ficar fora do repositório para evitar duplicação do conteúdo.

O manifesto corresponde à entrega inicial. Alterações futuras em documentação, calibração ou código fazem a comparação reportar diferenças; isso é esperado. Atualizar um manifesto deve ser uma ação explícita após revisar essas mudanças, não uma correção automática das divergências.

## Dados e autoria preservados

Os seis dumps históricos foram preservados integralmente e incluem identificação de máquina. Isso é explicitado no relatório; a imagem de recuperação tem SN vazio. A pasta contém materiais de terceiros com licenças e avisos próprios, descritos em [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). O inventário não atribui uma licença única a todo o conjunto.

O pacote de publicação não inclui credenciais, ambientes virtuais ou históricos `.git` das fontes. O `.gitignore` evita adicionar arquivos de execução e caches usuais.

O código-fonte MKA também está publicado diretamente em `firmwares/MKA-firmware/`,
como arquivos normais, sem dependência de submódulo. Seus 661 arquivos de conteúdo
foram comparados por SHA-256 e são idênticos à cópia mantida em
`gravador/dependencies/firmwares/firmware codigo fonte/MKA-firmware/`.
O histórico Git independente dessa cópia foi preservado fora da pasta publicada.
