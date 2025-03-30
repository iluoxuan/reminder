# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['reminder_app.py'],
    pathex=[],
    binaries=[],
    datas=[('language.json', '.')],
    hiddenimports=['datetime', 'zipfile'],
    hookspath=[],
    hooksconfig={
        'pyside6': {
            'modules': ['QtCore', 'QtGui', 'QtWidgets'],
            'plugins': ['platforms', 'styles'],
        }
    },
    runtime_hooks=[],
    excludes=[
        # Qt Modules
        'PySide6.QtNetwork', 'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtSql', 'PySide6.QtXml',
        'PySide6.QtOpenGL', 'PySide6.QtTest', 'PySide6.QtHelp', 'PySide6.QtMultimedia',
        'PySide6.QtPrintSupport', 'PySide6.QtWebChannel', 'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets', 'PySide6.QtWebSockets', 'PySide6.Qt3DCore',
        'PySide6.Qt3DExtras', 'PySide6.Qt3DInput', 'PySide6.Qt3DLogic', 'PySide6.Qt3DRender',
        'PySide6.QtBluetooth', 'PySide6.QtConcurrent', 'PySide6.QtDataVisualization',
        'PySide6.QtDesigner', 'PySide6.QtHttpServer', 'PySide6.QtLocation',
        'PySide6.QtMultimediaWidgets', 'PySide6.QtNfc', 'PySide6.QtOpenGLWidgets',
        'PySide6.QtPositioning', 'PySide6.QtQmlWorkerScript', 'PySide6.QtQuickControls2',
        'PySide6.QtQuickWidgets', 'PySide6.QtRemoteObjects', 'PySide6.QtScxml',
        'PySide6.QtSensors', 'PySide6.QtSerialPort', 'PySide6.QtSpeech', 'PySide6.QtStateMachine',
        'PySide6.QtTextToSpeech', 'PySide6.QtUiTools', 'PySide6.QtWaylandClient',
        'PySide6.QtWaylandCompositor', 'PySide6.QtWebChannel', 'PySide6.QtWebEngineQuick',
        'PySide6.QtWebSockets', 'PySide6.QtWebViewWidgets',
        # Python Standard Library
        'tkinter', 'unittest', 'email', 'html', 'http', 'xml', 'pydoc', 
        'doctest', 'argparse', 'py',
        'distutils', 'lib2to3', 'pkg_resources', 'pydoc_data', 'test',
        'curses', 'idlelib', 'tty', 'optparse', 'bdb', 'pdb', 'pywin', 'win32com',
        'pythoncom', 'PIL', 'numpy', 'pandas', 'scipy', 'matplotlib'
    ],
    noarchive=False,
)
pyz = PYZ(a.pure, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='生活工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',
        'msvcp140.dll',
        'ucrtbase.dll',
        'VCRUNTIME140.dll',
        'MSVCP140.dll',
        'python*.dll',
        'api-ms-win*.dll'
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
