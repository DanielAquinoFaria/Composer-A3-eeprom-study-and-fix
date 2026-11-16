from pathlib import Path
from html import escape
from PIL import Image, ImageDraw, ImageFont

OUT=Path(__file__).resolve().parents[1]/'hardware'
OUT.mkdir(exist_ok=True)
W,H=1500,1340
im=Image.new('RGB',(W,H),'white'); d=ImageDraw.Draw(im)
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', '<title>Gravador AT24C256C com Arduino AVR 5 V</title>', '<desc>Esquema elétrico de SDA, SCL, WP, alimentação, pull-ups e desacoplamento, com tabela Uno, Nano clássico e Mega 2560.</desc>', '<rect width="1500" height="1340" fill="white"/>']
INK='#172B40'; MUTED='#4F6376'; POWER='#B42318'; GND='#334155'; SDA='#006D77'; SCL='#1D4ED8'; WP='#8A3C99'
def line(points,color=INK,width=3):
 d.line(points,fill=color,width=width)
 svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in points)+f'" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>')
def rect(box,fill='white',stroke=INK,width=2):
 x,y,x2,y2=box; d.rectangle(box,fill=fill,outline=stroke,width=width)
 svg.append(f'<rect x="{x}" y="{y}" width="{x2-x}" height="{y2-y}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
def text(x,y,s,size=21,color=INK,bold=False):
 font=ImageFont.truetype('C:/Windows/Fonts/'+('segoeuib.ttf' if bold else 'segoeui.ttf'),size)
 d.text((x,y),s,font=font,fill=color)
 svg.append(f'<text x="{x}" y="{y+size}" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" fill="{color}"'+(' font-weight="700"' if bold else '')+'>'+escape(s)+'</text>')
def dot(x,y,color):
 d.ellipse((x-5,y-5,x+5,y+5),fill=color)
 svg.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{color}"/>')
def ground(x,y):
 line([(x,y),(x,y+15)],GND)
 for dy,half in [(15,18),(23,12),(31,6)]: line([(x-half,y+dy),(x+half,y+dy)],GND)
def power(x,y):
 line([(x,y),(x,y-18)],POWER)
 line([(x-9,y-9),(x,y-18),(x+9,y-9)],POWER)
 text(x-22,y-48,'+5 V',18,POWER,True)
def pullup(x,y,name,value,color):
 line([(x,y),(x,y-15)],color); rect((x-9,y-48,x+9,y-15),stroke=color)
 line([(x,y-48),(x,y-62)],color); line([(x-7,y-55),(x,y-62),(x+7,y-55)],POWER); text(x-22,y-87,'+5 V',18,POWER,True)
 text(x+20,y-49,name+'  '+value,19,color,True); dot(x,y,color)

text(60,35,'AT24C256C  |  Leitor e gravador',38,bold=True)
text(60,90,'Esquema de bancada • Arduino AVR de 5 V • EEPROM isolada da impressora',23,MUTED)
rect((60,135,1440,185),fill='#FFF4E5',stroke='#D99A32')
text(78,145,'Use UMA placa Arduino por vez. Monte com a alimentação desligada. Não use este esquema em barramento de 3,3 V.',19)

rect((90,340,440,730),fill='#F0F7FA')
text(115,355,'ARDUINO',29,bold=True)
text(115,397,'USB → computador',21,MUTED)
text(115,435,'Uno / Nano / Mega',20,MUTED)
# signal lines with separate pull-up branches (no crossing nets)
for y,label,pin,color,name,value in [(500,'SDA','5',SDA,'R1','4,7 kΩ'),(590,'SCL','6',SCL,'R2','4,7 kΩ'),(680,'D7 / WP','7',WP,'R3','10 kΩ')]:
 text(295,y-29,label,22,color,True)
 line([(440,y),(900,y)],color)
 pullup(650,y,name,value,color)
 text(850,y-28,pin,20,color,True)
# EEPROM functional symbol
rect((900,300,1160,760),fill='#F7F8FC')
text(925,320,'U1',23,bold=True)
text(925,355,'AT24C256C',26,bold=True)
text(925,396,'32.768 bytes',19,MUTED)
for y,label,color in [(500,'SDA',SDA),(590,'SCL',SCL),(680,'WP',WP)]: text(920,y-15,label,23,color,True)
text(1008,308,'VCC',19,POWER)
line([(1030,300),(1030,245),(1270,245)],POWER); power(1030,245)
text(1045,265,'8',20,POWER)
# Decoupling branch
line([(1270,245),(1270,270)],POWER); dot(1270,245,POWER)
line([(1250,270),(1290,270)],POWER,4)
line([(1250,282),(1290,282)],POWER,4)
line([(1270,282),(1270,300)],GND); ground(1270,300)
text(1300,257,'C1',20,bold=True); text(1300,285,'100 nF',20)
text(1200,353,'Próximo aos pinos 8 e 4',16,MUTED)
# Address pins and common ground
for y,pin,label in [(440,1,'A0'),(520,2,'A1'),(600,3,'A2'),(720,4,'GND')]:
 text(1090,y-17,label,20)
 text(1170,y-28,str(pin),19)
 line([(1160,y),(1240,y)],GND); dot(1240,y,GND)
line([(1240,440),(1240,770)],GND); ground(1240,770)
text(1280,470,'A0/A1/A2 = GND',19,bold=True)
text(1280,503,'Endereço: 0x50',19)
text(1280,545,'São pinos do CI,',17,MUTED)
text(1280,571,'não do Arduino.',17,MUTED)
# Arduino power nets
line([(170,340),(170,285)],POWER); power(170,285)
text(190,295,'Pino 5V',20,POWER)
line([(190,730),(190,770)],GND); ground(190,770)
text(225,747,'Pino GND',20)
text(90,830,'Todos os símbolos +5 V estão conectados entre si; todos os GND também.',21,bold=True)
text(90,862,'R1/R2/R3 são ramificações para +5 V. Os sinais Arduino ↔ EEPROM são ligações diretas.',20,MUTED)
# Mapping table
text(60,915,'Pinos a utilizar em cada Arduino',26,bold=True)
headers=['Sinal','Uno R3','Nano clássico','Mega 2560','EEPROM']
xs=[80,305,555,860,1170]
rect((60,960,1440,1000),fill='#E9EFF5',stroke='#CBD5E1')
for x,h in zip(xs,headers): text(x,966,h,20,bold=True)
rows=[['SDA','A4 / SDA','A4','D20 / SDA','5'],['SCL','A5 / SCL','A5','D21 / SCL','6'],['WP','D7','D7','D7','7'],['Alimentação','5V e GND','5V e GND','5V e GND','8 e 4']]
for i,row in enumerate(rows):
 y=1000+i*43; rect((60,y,1440,y+43),fill='white' if i%2 else '#F8FAFC',stroke='#E2E8F0',width=1)
 for x,t in zip(xs,row): text(x,y+6,t,20)
text(60,1195,'WP alto: gravação bloqueada. WP baixo: gravação permitida. A leitura funciona nos dois estados.',21,bold=True)
text(60,1233,'R3 mantém a proteção no reset. D7 libera cada escrita. Não substitua R3 por um capacitor.',20,MUTED)
text(60,1271,'Símbolo funcional, não vista física do CI. Veja MONTAGEM.md para orientação, componentes e sequência de uso.',19,MUTED)
svg.append('</svg>')
(OUT/'esquematico_arduinos_at24c256c.svg').write_text('\n'.join(svg),encoding='utf-8')
im.save(OUT/'esquematico_arduinos_at24c256c.png')
