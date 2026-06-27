---
title: "深度学习环境搭建与验证"
date: 2025-11-03 10:00:00
categories:
  - [技术研习, Jetson_Orin_NANO]
tags: [jetson, orin-nano, 深度学习, pytorch, ultralytics, numpy, opencv, 环境搭建]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 6
description: 在 Jetson Orin NANO 上搭建深度学习环境，验证 Ultralytics、PyTorch、Torchvision、NumPy、OpenCV 等核心库的安装状态。
cover: /img/covers/tech-study.svg
slug: ts-jetson-deeplearning-env
status: published
lang: zh-CN
---

## 前言

在 Jetson Orin NANO 上完成基础环境配置后，下一步是搭建深度学习环境。本文记录了验证各核心库安装状态的命令。

---

## 一、验证 Ultralytics

```bash
python3 -c "import ultralytics; print(ultralytics.__version__)"
```

---

## 二、验证 PyTorch（Torch）

```bash
# 验证版本
python3 -c "import torch; print(torch.__version__)"

# 验证 CUDA 是否可用
python3 -c "import torch; print(torch.cuda.is_available())"
```

> Jetson 上应输出 `True`，表示 PyTorch 可以使用 GPU 加速。

---

## 三、验证 Torchvision

```bash
python3 -c "import torchvision; print(torchvision.__version__)"
```

---

## 四、验证 NumPy

```bash
python3 -c "import numpy; print(numpy.__version__)"
```

---

## 五、验证 OpenCV

```bash
# 验证 OpenCV 版本及 GStreamer 支持
python3 -c "import cv2; print(cv2.getBuildInformation())" | grep GStreamer
```

> OpenCV 的 GStreamer 支持对 Jetson 上的摄像头视频流处理非常重要。

---

## 六、参考：完整环境版本

| 组件 | 版本 |
|------|------|
| Python | 3.10.19 |
| PyTorch | 2.5.0a0+872d972e41.nv24.08 |
| Torchvision | 0.20.0a0+afc54f7 |
| CUDA | 12.6 |
| cuDNN | 已启用 |
| OpenCV | 4.12.0 |
| Ultralytics | 8.3.232 |
