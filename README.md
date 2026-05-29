# Matrix Rank Calculator

Matrix Rank Calculator 是一个用于计算矩阵秩的 Python 小工具。项目提供 tkinter 图形界面，支持逐步展示计算过程，适合线性代数学习、作业核对和算法验证。

项目目前支持三种计算方式：高斯消元法、子行列式法和 SVD 数值秩。高斯消元法和子行列式法用于精确秩计算，SVD 用于数值参考。

## 功能亮点

- 支持整数、小数、负数、分数和科学计数法输入。
- 使用 `sympy` 保留精确分数计算，减少浮点误差影响。
- 高斯消元法会展示行变换过程。
- 子行列式法适合小规模矩阵的理论验证。
- SVD 方法可作为浮点矩阵的数值秩参考。
- 提供 tkinter 图形界面，无需命令行交互。

## 安装依赖

建议使用 Python 3.11 或更新版本。

```bash
pip install -r requirements.txt
```

也可以手动安装依赖：

```bash
pip install numpy sympy pytest
```

## 运行方式

从源码运行：

```bash
git clone https://github.com/Cheems-sudo/matrix-rank-calculator
cd matrix-rank-calculator
python matrix_rank_calculator.py
```

## 界面说明

启动程序后，按界面提示选择计算方法、输入矩阵行数和列数，再逐行输入矩阵元素。

输入示例：

```text
1 2 3
4 5 6
7 8 9
```

支持的元素格式示例：

```text
2
-3
0.5
-2/5
1e-3
```

![Input](assets/input.png)

![Result](assets/output.png)

## 方法说明

### 高斯消元法

高斯消元法通过初等行变换把矩阵化为行阶梯形矩阵，再根据非零行数量判断矩阵秩。该方法是项目默认推荐的精确计算方式。

### 子行列式法

子行列式法通过寻找最高阶非零子行列式来确定矩阵秩。由于需要枚举子矩阵，矩阵规模较大时计算量会快速增加，因此更适合小矩阵验证。

### SVD 数值秩

SVD 方法通过奇异值分解判断数值秩。它适合浮点数据和工程场景中的参考判断，但在精确数学结论上应以高斯消元法或子行列式法为准。

## 项目结构

```text
.
├── matrix_rank_calculator.py      # 程序入口
├── matrix_rank/
│   ├── app.py                     # 应用启动逻辑
│   ├── calculator.py              # 矩阵秩计算核心
│   ├── delayed_output.py          # GUI 延迟输出控制
│   ├── gui.py                     # tkinter 图形界面
│   ├── parsing.py                 # 矩阵元素解析
│   ├── workflow.py                # 计算流程和结果复核
│   └── __init__.py
├── assets/
│   ├── input.png                  # README 输入界面截图
│   └── output.png                 # README 输出界面截图
├── tests/                         # pytest 单元测试
├── requirements.txt               # Python 依赖
├── LICENSE
└── README.md
```

## 常见问题

### 为什么 SVD 结果可能和精确秩不同？

SVD 是数值方法，会根据阈值判断奇异值是否视为 0。对于病态矩阵、尺度差异很大的矩阵，或存在非常小但非零奇异值的矩阵，SVD 数值秩可能与精确秩不同。

### GUI 无法启动怎么办？

请确认当前 Python 环境支持 `tkinter`。部分精简 Python 发行版可能没有包含 tkinter，需要单独安装或更换 Python 版本。

### 如何运行测试？

```bash
python -m pytest -q
```

## 后续计划

- 改进矩阵输入体验。
- 增加更多边界情况测试。
- 优化计算过程展示文本。
- 在保持项目简洁的前提下完善打包发布流程。

## License

MIT License

## 作者信息

- GitHub: [https://github.com/Cheems-sudo](https://github.com/Cheems-sudo)
