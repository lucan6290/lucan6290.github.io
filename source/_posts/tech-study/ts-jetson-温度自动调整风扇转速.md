---
title: "根据温度自动调整风扇转速"
date: 2025-11-18 10:00:00
categories:
  - [技术研习, 系列专题]
tags: [jetson, orin-nano, 风扇, 温度监控, systemd, bash, 散热]
series: "Jetson Orin NANO 开发板使用笔记"
series_order: 8
description: 编写自动风扇控制脚本，根据 Jetson Orin NANO 的 GPU 和 SOC 温度实时调整 PWM 风扇转速，并部署为 systemd 服务。
cover: /img/covers/tech-study.svg
slug: ts-jetson-auto-fan-control
status: published
lang: zh-CN
---

## 前言

Jetson Orin NANO 在高负载运行（如 YOLO 训练、LLM 推理）时，温度会显著升高。虽然系统自带风扇控制，但默认策略可能不够激进。本文介绍如何编写一个自动风扇控制脚本，根据温度实时调整转速。

---

## 一、查询风扇控制接口

首先确认风扇控制和温度传感器的系统路径：

```bash
# 查找风扇控制核心接口
ls -la /sys/devices/platform/pwm-fan/hwmon/

# 查看控制文件
ls -la /sys/devices/platform/pwm-fan/hwmon/hwmon0/

# 查看所有温度传感器类型
for i in /sys/class/thermal/thermal_zone*/type; do
    echo "文件: $i, 内容: $(cat $i)"
done
```

{% asset_img 'ts-jetson-温度自动调整风扇转速-img1.png' '温度传感器查询结果' %}

### 关键路径

根据查询结果，得到以下关键路径：

| 组件 | 系统中的路径 |
|------|------------|
| **风扇速度控制文件** | `/sys/devices/platform/pwm-fan/hwmon/hwmon0/pwm1` |
| **CPU 温度传感器** | `/sys/class/thermal/thermal_zone0/temp` |
| **GPU 温度传感器** | `/sys/class/thermal/thermal_zone1/temp` |
| **SOC 温度传感器**（关键） | `/sys/class/thermal/thermal_zone5/temp` |

> 对于 AI 训练，**GPU** 和 **SOC** 的温度通常最为关键。本脚本将监控两者并取较高值来控制风扇。

---

## 二、自动风扇控制脚本

将以下内容保存为 `/opt/fan.sh`：

```bash
#!/bin/bash

# ============================================
# Jetson Orin Nano Super 自动风扇控制脚本
# 根据 GPU 和 SOC 温度自动调整 PWM 风扇转速
# 版本: 1.0 (验证路径)
# ============================================

# 设置风扇速度函数
set_fan_speed() {
    echo $1 | sudo tee /sys/devices/platform/pwm-fan/hwmon/hwmon0/pwm1 > /dev/null 2>&1
}

# 读取温度函数 (返回摄氏度)
read_temp() {
    local temp_path=$1
    if [ -f "$temp_path" ]; then
        local raw_temp=$(cat "$temp_path" 2>/dev/null)
        echo $((raw_temp / 1000))
    else
        echo ""
    fi
}

# 温度传感器路径
GPU_TEMP_PATH="/sys/class/thermal/thermal_zone1/temp"
SOC_TEMP_PATH="/sys/class/thermal/thermal_zone5/temp"
CPU_TEMP_PATH="/sys/class/thermal/thermal_zone0/temp"

LOG_FILE="/var/log/fan_control.log"
echo "$(date): 风扇控制服务启动。监控GPU和SOC温度。" | sudo tee -a $LOG_FILE

while true; do
    # 读取关键传感器温度
    GPU_TEMP=$(read_temp "$GPU_TEMP_PATH")
    SOC_TEMP=$(read_temp "$SOC_TEMP_PATH")

    # 确定最高温度
    MAX_TEMP=""
    if [ -n "$SOC_TEMP" ] && [ -n "$GPU_TEMP" ]; then
        if [ "$SOC_TEMP" -ge "$GPU_TEMP" ]; then
            MAX_TEMP=$SOC_TEMP
            SOURCE="SOC"
        else
            MAX_TEMP=$GPU_TEMP
            SOURCE="GPU"
        fi
    elif [ -n "$SOC_TEMP" ]; then
        MAX_TEMP=$SOC_TEMP
        SOURCE="SOC"
    elif [ -n "$GPU_TEMP" ]; then
        MAX_TEMP=$GPU_TEMP
        SOURCE="GPU"
    else
        CPU_TEMP=$(read_temp "$CPU_TEMP_PATH")
        if [ -n "$CPU_TEMP" ]; then
            MAX_TEMP=$CPU_TEMP
            SOURCE="CPU(备用)"
        else
            echo "$(date): 错误：无法从任何传感器读取温度。" | sudo tee -a $LOG_FILE
            sleep 30
            continue
        fi
    fi

    # 根据温度设置风扇 PWM 值 (0-255)
    if [ "$MAX_TEMP" -ge 75 ]; then
        set_fan_speed 255  # 全速 100%
        SPEED="100%"
    elif [ "$MAX_TEMP" -ge 70 ]; then
        set_fan_speed 220  # 高速 ~86%
        SPEED="86%"
    elif [ "$MAX_TEMP" -ge 65 ]; then
        set_fan_speed 180  # 中高速 ~70%
        SPEED="70%"
    elif [ "$MAX_TEMP" -ge 60 ]; then
        set_fan_speed 140  # 中速 ~55%
        SPEED="55%"
    elif [ "$MAX_TEMP" -ge 55 ]; then
        set_fan_speed 100  # 中低速 ~39%
        SPEED="39%"
    elif [ "$MAX_TEMP" -ge 50 ]; then
        set_fan_speed 70   # 低速 ~27%
        SPEED="27%"
    else
        set_fan_speed 60   # 最低温 ~20%
        SPEED="20%"
    fi

    # 每30分钟记录一次日志
    CURRENT_MINUTE=$(date +%M)
    if [ "$CURRENT_MINUTE" = "00" ] || [ "$CURRENT_MINUTE" = "30" ]; then
        echo "$(date): 温度源=${SOURCE}, 最高温度=${MAX_TEMP}°C, 风扇=${SPEED}" | sudo tee -a $LOG_FILE
    fi

    sleep 10
done
```

---

## 三、部署与验证

### 第一步：创建并测试脚本

```bash
# 创建脚本文件
sudo vim /opt/fan.sh

# 赋予执行权限
sudo chmod +x /opt/fan.sh

# 手动测试风扇控制是否生效
echo 200 | sudo tee /sys/devices/platform/pwm-fan/hwmon/hwmon0/pwm1
# 在另一个终端用 jtop 观察风扇转速是否提高

echo 80 | sudo tee /sys/devices/platform/pwm-fan/hwmon/hwmon0/pwm1
# 观察风扇转速是否下降
```

### 第二步：创建 systemd 服务

```bash
sudo vim /etc/systemd/system/fan_control.service
```

写入以下配置：

```ini
[Unit]
Description=Automatic Fan Control for Jetson Orin Nano
After=multi-user.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=5
User=root
ExecStart=/opt/fan.sh
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 第三步：启用并启动服务

```bash
# 启用服务
sudo systemctl enable fan_control.service

# 启动服务
sudo systemctl start fan_control.service

# 检查服务状态
sudo systemctl status fan_control.service

# 查看实时日志
sudo journalctl -u fan_control.service -f
```

---

## 四、重要提醒与微调

1. **不要混合使用**：启用此服务后，不要再使用 `sudo jetson_clocks --fan`，以免控制冲突
2. **温度阈值微调**：如果温度经常超过 75°C，可以：
   - 加强物理散热（改善风道、清灰）
   - 调低脚本中的温度阈值（如把 `-ge 70` 改为 `-ge 68`）
   - 调高 PWM 值（如把 `220` 改为 `240`）
3. **调试**：如果服务启动失败，运行 `sudo bash /opt/fan.sh` 在前台执行，观察终端报错信息
