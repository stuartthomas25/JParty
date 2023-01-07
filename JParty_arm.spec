# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
DISTPATH = "./dist_arm"


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
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
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
app = BUNDLE(exe,
             name='JParty.app',
             version='2.1',
             icon='resources/icon.icns',
             bundle_identifier='us.stuartthomas.jparty')