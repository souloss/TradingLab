
import os
from pathlib import Path

ROOT_DIR = Path(os.path.abspath('.'))

block_cipher = None

# 收集所有策略和指标模块
hidden_imports = [
    # 策略模块
    'tradingapi.strategy.base',
    'tradingapi.strategy.config_manager',
    'tradingapi.strategy.exceptions',
    'tradingapi.strategy.manager',
    'tradingapi.strategy.indicators.base',
    'tradingapi.strategy.indicators.momentum',
    'tradingapi.strategy.indicators.trend',
    'tradingapi.strategy.indicators.volatility',
    'tradingapi.strategy.indicators.volume',
    'tradingapi.strategy.strategies.base',
    'tradingapi.strategy.strategies.mean_reversion',
    'tradingapi.strategy.strategies.momentum',
    'tradingapi.strategy.strategies.trend_following',
    
    # 数据源模块
    'tradingapi.fetcher.base',
    'tradingapi.fetcher.interface',
    'tradingapi.fetcher.manager',
    'tradingapi.fetcher.datasources.eastmoney',
    'tradingapi.fetcher.datasources.exchange',
    'tradingapi.fetcher.datasources.legulegu',
    
    # 其他可能动态导入的模块
    'tradingapi.core.context',
    'tradingapi.core.db',
    'tradingapi.core.initializer',
    'tradingapi.core.metrics',
    
    # 第三方库可能需要的隐藏导入
    'uvicorn.workers',
    'uvicorn.loops',
    'uvicorn.protocols',
    'loguru',
    'yaml',
    'sqlalchemy',
    'pydantic',
    'fastapi',
    'akshare',
    'akshare.futures.cons',
    'aiosqlite',
]

# 收集所有数据文件
datas = [
    # 静态文件
    (str(ROOT_DIR / "static"), "static"),
    # 其他可能需要的文件
    (str(ROOT_DIR / "migrations"), "migrations"),
]

# 尝试找到 akshare 的资源文件并添加
try:
    import akshare
    akshare_path = Path(akshare.__file__).parent
    calendar_file = akshare_path / "file_fold" / "calendar.json"
    if calendar_file.exists():
        datas.append((str(calendar_file), "akshare/file_fold"))
        print(f"Found akshare calendar file: {calendar_file}")
    else:
        print(f"Warning: akshare calendar file not found at {calendar_file}")
except ImportError:
    print("Warning: akshare not found during build")

a = Analysis(
    ['main.py'],
    pathex=[str(ROOT_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='tradingapi',
    debug=False,
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
    icon=None,
)