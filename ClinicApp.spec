# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all Flask application files and submodules
flask_imports = collect_submodules('flask')
sqlalchemy_imports = collect_submodules('sqlalchemy')
app_imports = collect_submodules('app')

a = Analysis(
    ['launcher.py'],
    pathex=[os.path.abspath(os.getcwd())],
    binaries=[],
    datas=[
        ('run.py', '.'),
        ('config.py', '.'),
        ('app', 'app'),
        ('instance', 'instance'),
        ('migrations', 'migrations'),
    ] + collect_data_files('flask') + collect_data_files('app'),
    hiddenimports=[
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'flask_migrate',
        'email_validator',
        'pdfkit',
        'psutil',
        'werkzeug',
        'jinja2',
        'sqlalchemy',
        'email_validator',
    ] + flask_imports + sqlalchemy_imports + app_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add additional data files for templates and static files
a.datas += Tree('app/templates', prefix='app/templates')
a.datas += Tree('app/static', prefix='app/static')

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ClinicApp',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
