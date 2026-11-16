> Documento técnico da geração/revisão original. As afirmações de ausência de ensaio físico descrevem aquela etapa. Em 16/11/2026, o operador confirmou a resolução com esta imagem e Arduino Uno; veja o [relatório final](../../RELATORIO.md). Nenhum byte da imagem foi alterado nesta consolidação.

# Revisão da imagem EEPROM — 04/11/2026

## Resultado

Imagem regenerada a partir das macros originais compiladas para Cortex-M3 e dos 53 comandos do perfil Composer A3-1.0.5.gc. O SHA-256 antes e depois permaneceu idêntico:

`a54501351980aeef05636856efa92e8a668bbfaf2794a42b80f438af59d0dc1e`

Não foi identificada necessidade de alterar bytes na imagem sob as premissas abaixo. Os seis testes específicos de test_mka_image.py passaram novamente após a regeneração.

## Condições reproduzidas

1. Modelo Composer A3, configuração COMPOSER_A3_V10, EEPROM AT24C256C de 32.768 bytes.
2. Perfil validado pelo usuário: Composer A3-1.0.5.gc, aplicado integralmente.
3. Defaults do MKA e inicializações estáticas limpas para campos não definidos pelo perfil. Nenhum conteúdo USER corrompido dos logs é utilizado.
4. Número de série vazio: 17 bytes zero em 32010–32026.
5. Versão de identificação 1.0.5: string terminada em zero no campo de 9 bytes em 32027–32035. Essa identificação foi escolhida para acompanhar o perfil; o arquivo GC não contém um M1004 para defini-la.
6. Gravação bem-sucedida e completa, sem interrupção ou bloqueio de WP.
7. Lacunas da imagem preenchidas com FF. Essa é uma escolha explícita do gerador, equivalente a partir de uma memória apagada nessas regiões.

## Conferências no fonte

Foram relidas as rotinas Store_Sys, Store_Usr, Store_Const e a sequência de aplicação de defaults/carregamento em src/core/eeprom/eeprom.cpp, além de Heater::init/updatePID e o caminho do comando M500. Foram conferidos a ordem dos campos, os cabeçalhos, o deslocamento global de 10 bytes, os CRCs excluindo os cabeçalhos e o tratamento separado da identificação.

| Bloco | Início | Tamanho com cabeçalho | CRC decimal | CRC hexadecimal |
|---|---:|---:|---:|---|
| USER | 0x000A | 117 | 37164 | 0x912C |
| SYSTEM | 0x100A | 751 | 13673 | 0x3569 |

O teste reproduz o perfil, verifica todos os campos mapeados, rejeita a alteração de um bit em cada byte dos payloads e verifica os hashes das fontes registradas. O CRC SYSTEM coincide com o valor aceito nos logs históricos; isso é evidência adicional, não prova de identidade de um dump físico.

## Diferença entre a imagem limpa e uma gravação na impressora

### Existem três lugares diferentes para os parâmetros

| Local | O que contém | O que acontece ao desligar |
|---|---|---|
| Flash do microcontrolador | Programa MKA e valores padrão compilados | Permanece armazenada |
| RAM do microcontrolador | Valores que a impressora está usando naquele momento | O estado de execução é perdido |
| EEPROM externa | Parâmetros salvos para carregar nas próximas inicializações | Permanece armazenada |

Uma configuração válida na Flash não garante que o valor usado em execução também seja válido. O firmware pode iniciar a RAM com um default correto e depois substituí-lo por um valor lido da EEPROM.

```text
Defaults compilados na Flash ──> parâmetros na RAM
                                      ↑
EEPROM ─────── carregamento ───────────┘
                                      ↑
Perfil .gc ─── altera campos específicos
                                      │
                                      └── M500 / M500 S ──> EEPROM
```

O perfil `.gc` é uma lista de comandos. Ele não contém uma imagem completa da memória e não substitui automaticamente todos os parâmetros. Por exemplo, `M92 X100 Y100 Z2560` atualiza os steps dos três eixos na RAM; não define offsets dos bicos, brilho ou PID.

### O que cada operação faz neste fonte MKA

| Operação | Efeito |
|---|---|
| Aplicar o perfil A3-1.0.5.gc | Altera na RAM os campos explicitamente definidos pelos 53 comandos do arquivo |
| M502 / Factory_Settings | Reatribui os defaults implementados nessa função; não reinicia todo o programa nem todas as variáveis |
| M500 | Grava o bloco USER a partir do estado atual da RAM |
| M500 S | Grava SYSTEM e depois USER a partir do estado atual da RAM |
| M1003 / M1004 | Alteram número de série / versão de identificação e gravam o bloco CONST |
| Gravar nosso BIN completo pelo Uno | Substitui os 32.768 bytes, incluindo os três blocos e as lacunas |

Ao gravar um bloco, o MKA transforma cada variável em bytes na ordem definida em Store_Sys ou Store_Usr. Isso é a serialização: por exemplo, um offset float ocupa quatro bytes, com a ordem de bytes esperada pelo SAM3X. O firmware calcula um CRC dos dados e grava o cabeçalho correspondente. Ele não produz um arquivo `.bin` nesse processo.

M500 S não significa “apagar tudo e recriar a EEPROM”. Também não força automaticamente número de série vazio ou versão 1.0.5, pois a identificação é tratada separadamente.

### Por que rejeitar o CRC pode não retirar os valores incorretos da RAM

No caminho de carregamento USER deste fonte, a sequência é:

1. Conferir a versão do bloco.
2. Ler os campos diretamente para as variáveis que a máquina utiliza.
3. Calcular o CRC durante a leitura.
4. Comparar o CRC calculado com o armazenado, depois que os campos já foram copiados.
5. Em caso de falha, chamar Factory_Settings; se SYSTEM tinha sido aceito, recarregá-lo.

O problema é o passo 2 ocorrer antes da validação final, combinado com uma restauração incompleta no passo 5. Não há, nesse caminho, uma cópia temporária que só seja aplicada depois de aprovada.

Isso não significa que todos os defaults falhem. Factory_Settings redefine vários campos, inclusive offsets dos bicos e PID. Entretanto, não reatribui os offsets da troca, os presets de pré-aquecimento e o brilho. Esses últimos têm valores iniciais em outras partes do código, executados na inicialização do programa; chamar M502 não executa novamente essas inicializações estáticas.

Exemplo: `switch_offset_y` começa em zero ao iniciar o programa. Uma leitura USER pode substituí-lo por um valor inválido antes de detectar erro de CRC. A chamada posterior a Factory_Settings não zera novamente esse campo. Assim, a mensagem “defaults carregados” não prova que todos os valores ativos voltaram ao estado inicial.

### Como um valor incorreto pode acabar salvo com CRC válido

Considere esta sequência ilustrativa, compatível com o mecanismo encontrado no fonte:

1. O carregamento coloca um offset de troca Y incorreto na RAM.
2. O CRC USER é rejeitado, mas a restauração não redefine esse offset.
3. O usuário altera o offset do bico T1 no menu. Esse é outro campo: `hotend_offset`, não `switch_offset_y`.
4. O menu salva o bloco USER inteiro, incluindo o offset de troca que permaneceu incorreto.
5. O novo CRC é calculado sobre esses dados e fica coerente com eles.
6. No próximo carregamento, a verificação de CRC pode passar, embora o parâmetro de movimento continue inadequado.

O CRC verifica a consistência dos bytes com o checksum armazenado. Ele não verifica se uma distância é razoável, se cabe no curso mecânico ou se foi calibrada corretamente. Portanto, “CRC válido” e “configuração funcionalmente correta” são verificações distintas. Essa sequência explica uma possibilidade do fonte; não determina, sozinha, a origem física da corrupção observada.

### O que foi feito na imagem reconstruída

A geração parte de um estado limpo definido, sem importar os campos USER dos logs problemáticos. Ela aplica os defaults do perfil de compilação COMPOSER_A3_V10 e as inicializações estáticas pertinentes; em seguida, aplica os 53 comandos do perfil A3-1.0.5.gc, respeitando os valores que você informou como validados.

Para os campos USER que o GC não especifica, a imagem usa explicitamente:

| Campo | Valor na imagem | Distinção importante |
|---|---|---|
| Home XYZ | 0 / 0 / 0 | Não recupera uma calibração individual anterior |
| Offset do bico T1 | X−2,2 / Y−16,5 / Z0 | Default geométrico do fonte |
| Offset de troca XY | 0 / 0 | Campo diferente do offset do bico |
| Pré-aquecimento | H230 / B60 | Presets de menu, não comando de aquecimento |
| Brilho | 90 | Inicialização definida no código |
| PID | Defaults do MKA | Não são resultados de autotune da máquina específica |

Depois são calculados os CRCs USER e SYSTEM. O número de série é deixado vazio conforme solicitado. A versão de identificação é definida como 1.0.5 para acompanhar o perfil; esse preenchimento é uma decisão explícita da geração, não um efeito de M500 S.

“Imagem limpa” significa aqui que todos esses valores de partida são conhecidos. Não significa ausência de parâmetros, EEPROM toda zerada ou garantia de calibração mecânica da impressora.

### Por que as lacunas ficam em FF

Dos 32.768 bytes, os blocos definidos ocupam 894 bytes: USER 117, SYSTEM 751 e CONST 26. Os outros 31.874 bytes foram preenchidos com FF pelo gerador. Isso equivale a partir de uma EEPROM apagada nessas regiões, sem atribuir configurações inventadas a elas.

O MKA normalmente preserva esses endereços durante M500 S. Se uma EEPROM já tiver outros bytes nas lacunas, eles poderão continuar diferentes, mesmo que os parâmetros utilizados pelo firmware sejam iguais aos da imagem. FF nas lacunas é uma escolha para tornar o arquivo completo e reproduzível, não uma exigência demonstrada do carregador MKA.

Não se deve confundir essas lacunas com o padding interno das estruturas de movimento: os bytes de padding estão dentro do bloco SYSTEM, entram no CRC e foram definidos como zero na reconstrução.

### O que a revisão permite afirmar

A imagem é consistente com o layout e os defaults do fonte local, com o perfil validado escolhido e com as decisões explícitas sobre identidade e preenchimento. Regerá-la com essas mesmas condições produz o mesmo arquivo.

Ela não comprova que simplesmente reaplicar o GC em qualquer EEPROM produza os mesmos 32.768 bytes. Para isso, também seria necessário garantir o mesmo estado inicial da RAM, o mesmo conteúdo das regiões não escritas e a conclusão correta de todas as gravações. Uma releitura física permite confirmar o que efetivamente ficou na EEPROM; a verificação mecânica e térmica continua sendo uma etapa distinta.

## Relação com WP e o capacitor discutido

WP é uma entrada física; não existe um campo da imagem que habilite a escrita quando WP está alto. O possível capacitor entre WP e VCC não exige nenhuma alteração no BIN. Se interferir durante a gravação, pode impedir parte das escritas e o conteúdo real passa a depender do conteúdo anterior e dos instantes em que as transações foram aceitas. Esse resultado não pode ser reconstruído só pelo valor do capacitor ou pelo perfil.

Para comprovar o conteúdo efetivo, é necessário ler a EEPROM após a gravação e comparar os 32.768 bytes com a imagem. Essa revisão não fez gravação física nem simulou transientes elétricos.

## Limite de versão

A reconstrução usa o fonte local identificado como MKA 1.2.7dev, com layout MKA12/SC12, e o perfil do pacote que contém MKA 1.2.6. Não houve execução/emulação nem comparação das instruções do binário 1.2.6 com o fonte. A revisão confirma a consistência com o fonte e o perfil disponíveis, não a equivalência integral com qualquer firmware instalado.
