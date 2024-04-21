---
layout:       post
title:        "Games101笔记15——Animation"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
---



# 关键帧动画

![image-20230701220020494](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701220020494.png)

实际上就是在关键帧之间插值

![image-20230701220048842](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701220048842.png)

不过不是线性插值。

# 物理模拟

![image-20230701220227278](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701220227278.png)

不过与其这么去算，不如先用加速度求出下一时刻的速度，再用下一时刻的速度求出下一时刻的位置。(半隐式)

# 弹簧质点系统

把物体用由弹簧连接的质点模拟。

![image-20230701220707332](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701220707332.png)

理想的弹簧。

![image-20230701220803917](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701220803917.png)

没有设置摩擦力，会一直弹。

![image-20230701220957763](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701220957763.png)

表示不了弹簧内部的损耗。

![image-20230701221047200](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701221047200.png)

![image-20230701221424691](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701221424691.png)

其他的弹簧质点系统

![image-20230701221755464](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701221755464.png)

模拟布料。

# 粒子系统

![image-20230701222145119](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701222145119.png)

## 粒子系统过程

![image-20230701222327782](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701222327782.png)

## 粒子系统的力

![image-20230701222424619](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701222424619.png)

### 引力

![image-20230701222450582](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701222450582.png)

# 运动学

![image-20230701222823905](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701222823905.png)

![image-20230701222955653](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701222955653.png)

## 优缺点

![image-20230701223039717](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701223039717.png)

## 逆运动学

![image-20230701223111973](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701223111973.png)

![image-20230701223125661](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701223125661.png)

### 求解

![image-20230701223205747](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701223205747.png)

# Rigging

![image-20230701223511453](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701223511453.png)

逆运动学的运用。

# 动作捕捉

![image-20230701223759510](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701223759510.png)

## 优缺点

![image-20230701223827050](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230701223827050.png)

# 单粒子模拟

![image-20230702132048054](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230702132048054.png)

## 常微分方程

![image-20230702132208588](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230702132208588.png)

## 欧拉方法

![image-20230702132322998](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230702132322998.png)

显然是显式的。

### 错误

![image-20230702132712786](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230702132712786.png)

精确度取决于步长的大小。

### 稳定性

![image-20230702132818831](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230702132818831.png)

![image-20230702132934672](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230702132934672.png)

# 对抗不稳定性

![image-20230702135427372](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230702135427372.png)

先利用当前的速度计算步长一半时间后的位置。

再通过计算出来位置的速度场的速度计算一个完整步长后的位置。

(相当于给两个时间的速度插值？)

### 自适应步长

![image-20230702135913497](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230702135913497.png)

### 隐式欧拉方法

![image-20230702140113780](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230702140113780.png)

### 龙格-库塔方法

![image-20230702140747490](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230702140747490.png)

## 基于位置/采样积分

![image-20230702141125521](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230702141125521.png)

# 刚体模拟

![image-20230702141154672](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230702141154672.png)

# 流体模拟

![image-20230702141259927](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230702141259927.png)

## 欧拉vs拉格朗日

![image-20230702141324768](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/15/image-20230702141324768.png)