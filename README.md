# fMRI 数据分析入门

这是一个面向初学者的轻量学习项目：从认识 fMRI 文件开始，逐步检查数据、理解预处理，再计算静息态 ROI 功能连接。示例使用 Nilearn 可按需下载的 ADHD-200 公开数据，每次只取 1 名受试者；数据保存在本机缓存，不会提交到仓库。

## 学习路线

1. [检查样例数据](tutorials/01_inspect_data.py)：下载一名受试者，查看 NIfTI 维度、体素大小、TR 和时间点数量。
2. [静息态功能连接](tutorials/02_resting_state_fc.py)：用 Harvard-Oxford 皮层图谱提取 ROI 时间序列，进行混杂回归、去趋势和带通滤波，计算并绘制 ROI-ROI Pearson 相关矩阵。

## 环境准备

建议使用 Python 3.10–3.13（科学计算库对最新 Python 版本的支持可能稍晚）。在项目目录中创建虚拟环境并安装依赖：

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

先运行数据检查，再运行功能连接脚本：

```bash
python tutorials/01_inspect_data.py
python tutorials/02_resting_state_fc.py
```

首次运行会联网下载样例数据和图谱；网络或磁盘空间不足时，可先只阅读脚本与本文。输出写入 `outputs/`，Nilearn 下载缓存通常位于用户目录下的 `nilearn_data`。

## fMRI 文件是什么

常见的影像文件是 NIfTI：`.nii` 或压缩后的 `.nii.gz`。单个静息态功能像通常是四维数组 `(x, y, z, time)`：前三维是脑空间位置，第四维是连续采集的 volume。NIfTI header 记录维度、体素尺寸、仿射坐标变换等信息；TR（repetition time，重复时间）描述相邻 volume 的采集间隔，单位为秒。不要仅凭文件名推断 TR 或空间方向，应读取 header 并核对数据集说明。

BIDS 是组织神经影像数据的命名和目录约定。常见文件包括 `sub-*/func/sub-*_task-rest_bold.nii.gz`（功能像）、对应的 `*_bold.json`（采集元数据，如 TR、相位编码方向）和 `*_events.tsv`（任务事件；静息态一般没有任务事件）。`*_bold.json` 不是 NIfTI header 的替代品，两者需要结合检查。样例数据由 Nilearn 提供，未要求学习者手工下载或解析完整 BIDS 目录。

## 分析步骤与目的

### 1. 质量检查与空间预处理

拿到原始数据后，先检查图像是否完整、方向与空间分辨率是否合理、时间点是否足够、头动和异常 volume 是否严重。典型空间预处理包含 slice-timing 校正（按采集顺序校正切片时间差）、motion correction（配准 volume 并估计头动）、畸变校正（有场图或反向相位编码图时）、配准到 T1w、标准空间归一化，以及按研究目的决定是否平滑。每一步都可能引入假设；例如空间平滑会提升信噪比，也会模糊相邻脑区边界。

本项目的 ADHD 样例已经过标准化处理，不是从原始扫描开始的完整预处理练习。真实项目通常应先按 BIDS 整理原始数据，再用经过验证的流程（例如 fMRIPrep）生成预处理结果，并检查 HTML 报告、头动、配准和有效数据。不要对已经预处理的样例再次做运动校正或空间归一化。

### 2. 时间序列清理与 ROI 提取

功能连接前通常要处理与神经信号无关或不感兴趣的变化：回归头动参数及其扩展项、白质/脑脊液信号等混杂变量；去除线性趋势；按研究问题进行时间滤波。随后用脑图谱将体素聚合成 ROI 时间序列。脚本用 `NiftiLabelsMasker` 把混杂回归、去趋势、滤波、标准化和图谱提取串在一起。示例带通范围是 0.01–0.1 Hz；这不是适用于所有研究的固定标准。

### 3. 静息态功能连接

对于每对 ROI，计算两条时间序列的 Pearson 相关系数，得到对称的 ROI × ROI 矩阵。正值表示样本中共同升降，负值表示相反变化；相关不代表因果。矩阵依赖图谱、去噪策略、时间滤波和扫描时长，不应脱离这些选择解释。跨受试者统计通常会对相关系数做 Fisher z 变换，并在组水平模型中处理协变量和多重比较；本项目只演示单人的描述性结果。

## 如何按实验设置调整

- **TR 不同：**脚本从 NIfTI header 读取 TR 并传给滤波器。确认 header 单位正确且与采集协议一致；若数据转换时 TR 丢失，应依据原始 DICOM/BIDS JSON 修正，而不是猜值。
- **关注频段不同：**在 `02_resting_state_fc.py` 调整 `HIGH_PASS` 和 `LOW_PASS`。低通必须低于 Nyquist 频率（$1/(2\,TR)$）；过窄频段、短扫描和滤波边缘效应会让有效时间信息不足。
- **图谱不同：**更换脚本中的图谱获取方式，并核实图谱与功能像在同一空间、分辨率兼容。ROI 定义会改变结果；基于体素的连接分析则需要另一套内存和统计方案。
- **混杂变量不同：**调整 `CONFOUND_CANDIDATES`，并依据预注册/领域方案选择头动、WM/CSF、全局信号等回归项。全局信号回归可能引入或增强负相关，不能不加说明地默认使用。
- **扫描或实验不同：**任务态数据还需建模任务事件和响应，不能直接套用静息态解释；多回波、场图、反向相位编码、不同相位编码方向等采集设置会改变预处理策略。始终以采集协议、BIDS 元数据和研究问题为准。

## 结果与边界

脚本会生成 `outputs/connectivity_matrix.csv` 和 `outputs/connectivity_matrix.png`。这是用于学习流程的单受试者演示，不是临床分析、研究结论或可直接发表的流水线。正式研究需要预先定义分析方案、完整质量控制、样本量与统计模型，并报告软件版本和所有处理参数。

## 参考资料

- [Nilearn 文档](https://nilearn.github.io/)
- [Nilearn ADHD 数据集说明](https://nilearn.github.io/stable/modules/generated/nilearn.datasets.fetch_adhd.html)
- [BIDS 规范](https://bids-specification.readthedocs.io/)
- [fMRIPrep 文档](https://fmriprep.org/)
