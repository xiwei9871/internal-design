#!/usr/bin/env python3
"""失效源检测: 篡改源文件后, 提取器标记 STALE → 生成器 BLOCK"""
import json, shutil, subprocess, sys
from pathlib import Path

CAD = Path(__file__).resolve().parent
ROOT = CAD.parents[3]
PY = sys.executable
FC = ROOT / 'projects/c_type_home/cad/C型_原始户型数字化基准模型.FCStd'
BAK = CAD / 'derived' / 'prop_test' / 'BASELINE_BACKUP.FCStd'
BAK.parent.mkdir(exist_ok=True)

shutil.copy(FC, BAK)
try:
    # 篡改: 追加一个字节 → sha256 变化
    with open(FC, 'ab') as f: f.write(b'\x00')
    r1 = subprocess.run([PY, str(CAD/'extract_anchors_v02.py')], cwd=CAD,
                        capture_output=True, text=True)
    stale_flag = 'STALE' in r1.stdout or 'baseline_fcstd' in r1.stdout
    g = json.loads((CAD/'derived'/'geometry_v02.json').read_text())
    state = g['sources']['baseline_fcstd']['state']
    r2 = subprocess.run([PY, str(CAD/'make_a103_poc_v2.py')], cwd=CAD,
                        capture_output=True, text=True)
    blocked = r2.returncode != 0 and 'BLOCK' in (r2.stdout + r2.stderr)
    print('extractor state:', state, '| generator returncode:', r2.returncode,
          '| BLOCK:', blocked)
    assert state != 'FRESH', 'extractor did not flag stale source'
    assert blocked, 'generator did not BLOCK on stale source'
    print('PASS: tampered source detected and generation blocked')
    (CAD/'derived'/'stale_test_result.json').write_text(json.dumps(
        {'test': 'stale_source', 'extractor_state': state,
         'generator_blocked': blocked, 'status': 'PASS'}, indent=1))
finally:
    shutil.copy(BAK, FC)   # 恢复原文件 (manifest hash 重新匹配)
    print('source restored')
