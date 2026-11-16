"""Read-only comparison of EEPROM captures against the documented MKA layout."""
from pathlib import Path
import binascii
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT/'imagens'
REFERENCE = IMAGES/'AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.bin'
MANIFEST = IMAGES/'AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.json'


def compare():
    reference = REFERENCE.read_bytes()
    schema = json.loads(MANIFEST.read_text(encoding='utf-8'))['fields']
    files = sorted((IMAGES/'clones').glob('*.bin'))
    groups = {}
    captures = []
    for path in files:
        data = path.read_bytes()
        if len(data) != 32768:
            raise ValueError(f'{path.name}: tamanho {len(data)}, esperado 32768')
        digest = hashlib.sha256(data).hexdigest()
        groups.setdefault(digest, []).append(path.name)
        blocks = {}
        for name, start, end in [('USER',10,127),('SYSTEM',4106,4857)]:
            stored = struct.unpack_from('<H', data, start+6)[0]
            calculated = binascii.crc_hqx(data[start+8:end],0)
            blocks[name] = dict(version_hex=data[start:start+6].hex(), stored_crc=stored, calculated_crc=calculated, crc_ok=stored==calculated, identical_to_reference=data[start:end]==reference[start:end])
        fields = []
        for field in schema:
            offset, size = field['offset'],field['size']
            raw = data[offset:offset+size]
            expected = reference[offset:offset+size]
            if raw != expected:
                value = None if field['fmt']=='3x' else struct.unpack('<'+field['fmt'],raw)[0]
                fields.append(dict(name=field['name'],offset=offset,offset_hex=f'0x{offset:04X}',hex=raw.hex(),value=value,reference=field['value']))
        captures.append(dict(file=path.name,sha256=digest,blocks=blocks,dir_hex=data[4114:4120].hex(' '),serial_hex=data[32010:32027].hex(),version_hex=data[32027:32036].hex(),differences=fields,byte_differences=sum(a!=b for a,b in zip(data,reference)),unused_differences=sum(data[i]!=reference[i] for lo,hi in [(0,10),(127,4106),(4857,32010),(32036,32768)] for i in range(lo,hi))))
    report = dict(reference=REFERENCE.name,reference_sha256=hashlib.sha256(reference).hexdigest(),groups=groups,captures=captures)
    output = IMAGES/'comparacao'
    output.mkdir(exist_ok=True)
    (output/'comparacao.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines = ['# Comparação das duas EEPROMs — 04/11/2026','', 'Análise dos seis arquivos fornecidos, usando o layout MKA12/SC12 do projeto. Nenhum dump original ou imagem de referência foi alterado.','', '## Repetibilidade das leituras','']
    for digest,names in groups.items():
        lines.extend([f'- {len(names)} arquivos com SHA-256 `{digest}`: '+', '.join(f'`{name}`' for name in names)])
    lines.extend(['','A igualdade foi determinada sobre todos os 32.768 bytes. Isso demonstra repetibilidade entre as capturas fornecidas; não prova ausência de falhas intermitentes, retenção ao longo do tempo nem independência do método de leitura.','','## CRCs e direções','', '| Grupo | CRC USER armazenado/calculado | CRC SYSTEM armazenado/calculado | Direções X Y Z E U V | SYSTEM igual à referência |','|---|---|---|---|---|'])
    unique = [next(c for c in captures if c['sha256']==digest) for digest in groups]
    for c in unique:
        u,s=c['blocks']['USER'],c['blocks']['SYSTEM']
        lines.append(f"| {c['file']} | {u['stored_crc']} / {u['calculated_crc']} | {s['stored_crc']} / {s['calculated_crc']} | `{c['dir_hex']}` | {'Sim, byte a byte' if s['identical_to_reference'] else 'Não'} |")
    lines.extend(['','Os blocos SYSTEM completos, incluindo cabeçalho, CRC, flags e padding, são idênticos à referência em ambos os grupos. Portanto, os dumps não sustentam uma diferença persistida de inversão de motores entre essas duas EEPROMs. Isso não demonstra que o comportamento de movimento seja igual: USER, estado em execução, leitura no barramento da impressora e condições elétricas ainda podem interferir.','','## Campos diferentes da referência',''])
    for c in unique:
        lines.extend([f"### {c['file']}",'',f"Diferenças totais em relação à imagem de referência: **{c['byte_differences']} bytes**, sendo **{c['unused_differences']} em regiões não usadas** pelo layout selecionado.",'','| Endereço | Campo | Valor lido | Referência | Bytes lidos |','|---|---|---|---|---|'])
        for f in c['differences']:
            lines.append(f"| {f['offset_hex']} | {f['name']} | {f['value']} | {f['reference']} | `{f['hex']}` |")
        lines.extend(['',f"Campo SN bruto: `{c['serial_hex']}`.",f"Campo versão bruto: `{c['version_hex']}`.",''])
    lines.extend(['## Interpretação','', '- **Grupo erro_tamanho_offset:** o float32 em `0x0046–0x0049` tem bytes `04 01 85 DB` e representa exatamente **−74.874.577.188.028.416**. É o mesmo valor numérico anômalo registrado no histórico. O campo é o offset Y da troca, não o offset Y do bico.', '- Nesse mesmo grupo, os presets são **H8000/B56197**, o brilho é 64 e o offset X da troca tem um valor subnormal muito pequeno, com bytes `04 01 3C 00`. O padrão não permite atribuir a causa a WP, capacitor, retenção ou outro componente.', '- O CRC USER desse grupo é **24754**, confere e coincide com o log posterior à edição do menu. Os bytes demonstram a coexistência de checksum válido e parâmetros inadequados; não provam, isoladamente, a sequência exata que os produziu.', '- Os 17 bytes do SN desse grupo são `FF`: não há terminador NUL no campo. Isso explica a possibilidade de a impressão da identificação avançar para a string de versão adjacente, como aparece nos logs.', '- **Grupo erro_direcao:** o offset de troca X/Y está em zero e os valores USER diferentes são finitos e compatíveis com parâmetros personalizados: steps V416, home Z aproximadamente −3,8, offset T1 X−2/Y−17,7/Z2,9 e preset H215. Não é possível classificá-los como calibrações corretas ou incorretas apenas pelo dump.', '- O grupo erro_direcao contém SN **APCA331033**, terminado em NUL. Os dois grupos têm versão de identificação **1.0.4nw**. Essa string não identifica por si só o executável instalado nem determina os valores SYSTEM.', '- O fato de um arquivo estar nomeado erro_direcao não demonstra que os bits DIR estejam errados. Neste caso eles são iguais nos dois grupos e iguais ao perfil validado: X0 Y1 Z1 E1 U1 V1.','','## Consequência prática','', 'A anomalia de magnitude do grupo erro_tamanho_offset agora tem evidência direta no conteúdo fornecido. A causa do erro de direção do outro grupo continua sem determinação pelos dumps: não se deve inverter Y apenas para torná-lo diferente, pois os dois blocos SYSTEM já são iguais ao perfil validado.','', 'Não foi criada imagem corrigida automaticamente. A referência anterior continua com SN vazio e defaults USER, conforme autorizado; o SN e os possíveis ajustes individuais encontrados agora foram apenas registrados. Uma futura correção deve definir se preserva esses ajustes ou se utiliza os defaults.','', 'Para investigar diferença de comportamento na impressora, comparar o estado efetivamente carregado e o momento da anomalia (homing ou troca), com acionamento dos motores impedido, é mais informativo do que supor uma diferença nos seis bytes DIR. Leituras repetidas fora da impressora não validam seu barramento I2C durante o boot.'])
    (output/'COMPARACAO_EEPROMS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    for c in unique:
        print(c['file'],'diff_bytes',c['byte_differences'],'unused',c['unused_differences'],'system_identical',c['blocks']['SYSTEM']['identical_to_reference'])
    print('Report:',output/'COMPARACAO_EEPROMS.md')


if __name__=='__main__':
    compare()
