"""Interface desktop AT24C256C — execute: python desktop/app.py."""
import hashlib
import os
from pathlib import Path
import queue
import tempfile
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

from eeprom import (SIZE, SerialDevice, SimulatedDevice, Cancelled,
                    validate_range, read_memory, write_memory, verify_memory)


def atomic_save(path, data):
    path = Path(path)
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temp = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if temp and temp.exists():
            temp.unlink()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('AT24C256C | Leitor e gravador')
        self.geometry('940x740')
        self.minsize(850, 660)
        self.device = None
        self.busy = False
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.controls = []
        self.port = tk.StringVar()
        self.i2c = tk.StringVar(value='0x50')
        self.simulate = tk.BooleanVar(value=False)
        self.mode = tk.StringVar(value='Leitura')
        self.start = tk.StringVar(value='0x0000')
        self.length = tk.StringVar(value='32768')
        self.path = tk.StringVar()
        self.status = tk.StringVar(value='Desconectado')
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TButton', padding=7)
        style.configure('Title.TLabel', font=('Segoe UI', 22, 'bold'))
        style.configure('Sub.TLabel', foreground='#526378')
        main = ttk.Frame(self, padding=22)
        main.pack(fill='both', expand=True)
        ttk.Label(main, text='EEPROM Studio', style='Title.TLabel').pack(anchor='w')
        ttk.Label(main, text='AT24C256C • Arduino Uno R3 • 32 KiB • I²C', style='Sub.TLabel').pack(anchor='w', pady=(0, 16))
        connection = ttk.LabelFrame(main, text='1  Conexão', padding=12)
        connection.pack(fill='x')
        ttk.Label(connection, text='Porta serial').grid(row=0, column=0, sticky='w')
        self.ports = ttk.Combobox(connection, textvariable=self.port, width=15, state='readonly')
        self.ports.grid(row=1, column=0, padx=(0, 8))
        self.controls.append(self.ports)
        self.button(connection, 'Atualizar', self.refresh_ports).grid(row=1, column=1, padx=4)
        ttk.Label(connection, text='Endereço I²C').grid(row=0, column=2, sticky='w', padx=10)
        address = ttk.Combobox(connection, textvariable=self.i2c, values=[f'0x{x:02X}' for x in range(80, 88)], state='readonly', width=8)
        address.grid(row=1, column=2, padx=10)
        self.controls.append(address)
        demo = ttk.Checkbutton(connection, text='Simulação (sem hardware)', variable=self.simulate)
        demo.grid(row=1, column=3, padx=8)
        self.controls.append(demo)
        self.connect_button = self.button(connection, 'Conectar', self.connect)
        self.connect_button.grid(row=1, column=4, padx=4)
        operation = ttk.LabelFrame(main, text='2  Operação', padding=12)
        operation.pack(fill='x', pady=14)
        for i, mode in enumerate(('Leitura', 'Gravação', 'Verificação')):
            radio = ttk.Radiobutton(operation, text=mode, value=mode, variable=self.mode, command=self.mode_changed)
            radio.grid(row=0, column=i, sticky='w', pady=(0, 10))
            self.controls.append(radio)
        ttk.Label(operation, text='Endereço inicial (decimal ou 0x)').grid(row=1, column=0, sticky='w')
        ttk.Label(operation, text='Bytes a ler').grid(row=1, column=1, sticky='w')
        for col, variable in enumerate((self.start, self.length)):
            entry = ttk.Entry(operation, textvariable=variable, width=26)
            entry.grid(row=2, column=col, sticky='ew', padx=(0, 12), pady=5)
            self.controls.append(entry)
            if col == 1:
                self.length_entry = entry
        self.button(operation, 'Memória inteira', self.whole_memory).grid(row=2, column=2, sticky='ew')
        ttk.Label(operation, text='Arquivo binário (.bin)').grid(row=3, column=0, sticky='w', pady=(8, 0))
        file_entry = ttk.Entry(operation, textvariable=self.path)
        file_entry.grid(row=4, column=0, columnspan=2, sticky='ew', padx=(0, 12), pady=5)
        self.controls.append(file_entry)
        self.button(operation, 'Selecionar arquivo…', self.choose_file).grid(row=4, column=2, sticky='ew')
        self.hint = ttk.Label(operation, text='', style='Sub.TLabel')
        self.hint.grid(row=5, column=0, columnspan=3, sticky='w', pady=8)
        operation.columnconfigure(0, weight=1)
        operation.columnconfigure(1, weight=1)
        actions = ttk.Frame(main)
        actions.pack(fill='x')
        self.button(actions, 'Executar operação', self.execute).pack(side='left')
        self.cancel_button = ttk.Button(actions, text='Cancelar', command=self.cancel.set, state='disabled')
        self.cancel_button.pack(side='left', padx=8)
        ttk.Label(actions, textvariable=self.status).pack(side='right')
        self.progress = ttk.Progressbar(main, maximum=100)
        self.progress.pack(fill='x', pady=12)
        self.log = ScrolledText(main, height=13, font=('Consolas', 10), state='disabled', wrap='word')
        self.log.pack(fill='both', expand=True)
        self.append('Conecte o Uno com o firmware eeprom_uno.ino ou selecione Simulação.\nFaça um backup antes de gravar. A gravação verifica todos os bytes.')
        self.refresh_ports()
        self.mode_changed()
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        self.after(60, self.poll)

    def button(self, parent, text, command):
        button = ttk.Button(parent, text=text, command=command)
        self.controls.append(button)
        return button

    def append(self, text):
        self.log.configure(state='normal')
        self.log.insert('end', text + '\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def refresh_ports(self):
        try:
            from serial.tools import list_ports
            ports = list(list_ports.comports())
            self.ports['values'] = [p.device for p in ports]
            if ports and self.port.get() not in self.ports['values']:
                self.port.set(ports[0].device)
            if not ports:
                self.port.set('')
            self.append('Portas: ' + (', '.join(f'{p.device} ({p.description})' for p in ports) or 'nenhuma detectada'))
        except ImportError:
            self.append('Instale pyserial: python -m pip install -r requirements.txt. Simulação disponível.')

    def mode_changed(self):
        reading = self.mode.get() == 'Leitura'
        self.length_entry.configure(state='normal' if reading else 'disabled')
        self.hint.configure(text='Leitura: salva apenas a faixa escolhida em um arquivo .bin.' if reading else 'Gravação/verificação: usa o tamanho do arquivo, a partir do endereço inicial.')

    def whole_memory(self):
        self.start.set('0x0000')
        self.length.set(str(SIZE))

    def choose_file(self):
        options = dict(filetypes=[('Imagem binária', '*.bin'), ('Todos os arquivos', '*.*')])
        if self.mode.get() == 'Leitura':
            path = filedialog.asksaveasfilename(defaultextension='.bin', **options)
        else:
            path = filedialog.askopenfilename(**options)
        if path:
            self.path.set(path)

    def set_busy(self, busy):
        self.busy = busy
        for widget in self.controls:
            widget.configure(state='disabled' if busy else ('readonly' if isinstance(widget, ttk.Combobox) else 'normal'))
        self.cancel_button.configure(state='normal' if busy else 'disabled')
        if not busy:
            self.mode_changed()

    def run_job(self, work, success):
        self.cancel.clear()
        self.set_busy(True)
        self.progress['value'] = 0
        def worker():
            try:
                result = work()
                self.events.put(('success', (success, result)))
            except Exception as error:
                self.events.put(('error', error))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'progress':
                    self.progress['value'] = value
                elif kind == 'success':
                    self.set_busy(False)
                    callback, result = value
                    callback(result)
                else:
                    self.set_busy(False)
                    if isinstance(value, Cancelled):
                        self.status.set('Cancelado')
                        self.append(str(value))
                    else:
                        self.disconnect()
                        self.append(f'ERRO: {value}\nSe estava gravando, a memória pode ter sido parcialmente alterada.')
                        messagebox.showerror('Operação interrompida', str(value))
        except queue.Empty:
            pass
        self.after(60, self.poll)

    def disconnect(self):
        if self.device:
            self.device.close()
        self.device = None
        self.connect_button.configure(text='Conectar')
        self.status.set('Desconectado')

    def connect(self):
        if self.device:
            self.disconnect()
            return
        simulation, port, address = self.simulate.get(), self.port.get(), int(self.i2c.get(), 16)
        if not simulation and not port:
            messagebox.showerror('Porta serial', 'Selecione uma porta COM.')
            return
        self.status.set('Conectando…')
        def connected(device):
            self.device = device
            self.connect_button.configure(text='Desconectar')
            label = 'SIMULAÇÃO • memória volátil' if simulation else f'{port} • I²C 0x{address:02X}'
            self.status.set(label)
            self.append('Conectado: ' + label)
        self.run_job(lambda: SimulatedDevice() if simulation else SerialDevice(port, address), connected)

    def execute(self):
        if not self.device:
            messagebox.showerror('Conexão', 'Conecte o dispositivo primeiro.')
            return
        try:
            text = self.start.get().strip()
            start = int(text, 16 if text.lower().startswith('0x') else 10)
            if not self.path.get().strip():
                raise ValueError('Selecione um arquivo .bin.')
            path = Path(self.path.get()).expanduser().resolve()
            mode = self.mode.get()
            data = None
            if mode == 'Leitura':
                length = int(self.length.get())
                validate_range(start, length)
                if not path.parent.is_dir() or path.is_dir():
                    raise ValueError('Selecione um arquivo em uma pasta existente.')
                if path.exists() and not messagebox.askyesno('Substituir arquivo', f'Substituir {path.name}?'):
                    return
            else:
                with path.open('rb') as stream:
                    data = stream.read(SIZE + 1)
                length = len(data)
                validate_range(start, length)
            if mode == 'Gravação' and not messagebox.askyesno('Confirmar gravação', f'Gravar {length} bytes em 0x{start:04X}–0x{start+length-1:04X}?\n\nOs dados dessa faixa serão substituídos. Você já salvou um backup?'):
                return
        except (ValueError, OSError) as error:
            messagebox.showerror('Dados inválidos', str(error))
            return
        device = self.device
        simulation = isinstance(device, SimulatedDevice)
        self.append(f'{mode}{" [SIMULAÇÃO]" if simulation else ""}: {length} bytes a partir de 0x{start:04X}.')
        self.status.set(mode + ' em andamento…')
        def progress(done, total):
            if mode == 'Gravação':
                percent = 100 * done / (2*length)
            else:
                percent = 100 * done / total
            self.events.put(('progress', percent))
        def work():
            if mode == 'Leitura':
                result = read_memory(device, start, length, progress, self.cancel.is_set)
                if self.cancel.is_set():
                    raise Cancelled('Leitura cancelada; nenhum arquivo foi salvo.')
                atomic_save(path, result)
                return result
            if mode == 'Gravação':
                write_memory(device, start, data, progress, self.cancel.is_set)
            else:
                verify_memory(device, start, data, progress, self.cancel.is_set)
            return data
        def completed(result):
            self.progress['value'] = 100
            self.status.set('Concluído' + (' • SIMULAÇÃO' if simulation else ''))
            self.append(f'{mode} concluída. SHA-256: {hashlib.sha256(result).hexdigest()}')
            if mode == 'Leitura':
                self.append(f'Arquivo salvo: {path}')
                self.append('Prévia (primeiros 256 bytes):')
                for offset in range(0, min(len(result), 256), 16):
                    row = result[offset:offset+16]
                    ascii_text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
                    self.append(f'{start+offset:04X}  {row.hex(" ").upper():47}  {ascii_text}')
            elif mode == 'Gravação':
                self.append('Verificação integral concluída: todos os bytes conferem.')
        self.run_job(work, completed)

    def on_close(self):
        if self.busy:
            self.cancel.set()
            messagebox.showinfo('Aguarde', 'Cancelamento solicitado. Aguarde o término do bloco atual e feche novamente.')
            return
        self.disconnect()
        self.destroy()


if __name__ == '__main__':
    App().mainloop()
