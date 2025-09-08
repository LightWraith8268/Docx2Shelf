# Placeholder PyInstaller spec; customize during packaging
# Usage: pyinstaller packaging/docx2shelf.spec

block_cipher = None

a = Analysis([
    'src/docx2shelf/cli.py',
], pathex=[], binaries=[], datas=[('src/docx2shelf/assets', 'docx2shelf/assets'), ('src/docx2shelf/templates', 'docx2shelf/templates')],
   hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
          name='docx2shelf', debug=False, bootloader_ignore_signals=False,
          strip=False, upx=True, console=True)
