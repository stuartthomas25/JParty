import sys, platform
sys.path.append('')
from jparty.version import version

uname = platform.uname()

a = Analysis(['run.py'],
             pathex=['.'],
             binaries=[],
             datas=[
                 ("jparty/data/*", "data"),
                 ("jparty/buzzer", "buzzer"),
             ],
             hiddenimports=["qrcode"],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=None)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='JParty',
          debug=False,
          bootloader_ignore_signals=False,
          target_arch='arm64',
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False , icon='resources/icon.icns')

if uname.system == "Darwin":
    app = BUNDLE(exe,
                 name='JParty.app',
                 version=version,
                 icon='resources/icon.icns',
                 bundle_identifier='us.stuartthomas.jparty')
