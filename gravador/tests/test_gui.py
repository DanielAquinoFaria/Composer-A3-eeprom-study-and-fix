from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from app import App


class GuiTests(unittest.TestCase):
    def test_simulated_connect_write_verify_read_disconnect(self):
        app = App()
        app.withdraw()
        def finish():
            deadline = time.monotonic() + 8
            while app.busy and time.monotonic() < deadline:
                app.update()
                time.sleep(0.01)
            self.assertFalse(app.busy, 'Operação não terminou')
        try:
            with tempfile.TemporaryDirectory() as folder, patch('app.messagebox.askyesno', return_value=True), patch('app.messagebox.showerror') as error:
                app.simulate.set(True)
                app.connect()
                finish()
                self.assertIsNotNone(app.device)
                source = Path(folder) / 'source.bin'
                source.write_bytes(bytes(range(256)))
                app.start.set('0x003F')
                app.path.set(str(source))
                app.mode.set('Gravação')
                app.execute()
                finish()
                self.assertEqual(app.device.memory[63:319], bytes(range(256)))
                app.mode.set('Verificação')
                app.execute()
                finish()
                dest = Path(folder) / 'read.bin'
                app.path.set(str(dest))
                app.mode.set('Leitura')
                app.length.set('256')
                app.execute()
                finish()
                self.assertEqual(dest.read_bytes(), source.read_bytes())
                error.assert_not_called()
                app.disconnect()
                self.assertIsNone(app.device)
        finally:
            app.destroy()


if __name__ == '__main__':
    unittest.main()
