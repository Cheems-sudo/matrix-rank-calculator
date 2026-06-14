"""源码仓库兼容启动入口。

新安装推荐使用 ``matrix-rank-gui``；保留本文件以支持
``python matrix_rank_calculator.py`` 的原有运行方式。
"""

from __future__ import annotations

import sys

from matrix_rank.app import main


if __name__ == "__main__":
    sys.exit(main())
