---
layout:       post
title:        "Games103笔记02——Rigid Body"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games103
    - 图形学
    - 物理模拟
---



# 刚体动力学

![image-20230717160831444](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/Simulation.png)

模拟的目标是经过时间更新物体的状态变量<strong>s</strong><sup>[k]</sup>。

![image-20230717161104981](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/Motion.png)

刚体不能形变，运动只有两个部分：平移和旋转。

## 平移运动

![image-20230717164749925](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/Translation.png)

<strong>M</strong>是质量，因为加速度$\mathbf{a}=\frac{\mathbf{f}}{\mathbf{m}}$,所以速度的更新是上一次的速度与加速度的积分相加。

同理位置的更新是上一次更新的位置与位置的积分相加。

### 积分方法

![image-20230717171006811](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/ExplicitEuler.png)

显式欧拉：一阶准确的，使用t<sub>0</sub>时刻的速度v<sub>0</sub>当作t<sub>0</sub>到t<sub>1</sub>这段时间的恒定的速度求出运动的距离。

![image-20230717171454083](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/ImplicitEuler.png)

隐式欧拉：同样是一阶准确的，将t<sub>1</sub>时刻的速度v<sub>1</sub>看作t<sub>0</sub>到t<sub>1</sub>时间段的恒定的速度求出运动的距离。

![image-20230717171748065](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/SemiEuler.png)

中点方法：二阶准确，将t<sub>0</sub>到t<sub>1</sub>时间内的运动视作匀速运动，速度为中间时刻的速度。

~~不过这三种方法都像是只采样一次的蒙特卡洛积分~~

![image-20230717172610644](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/Translation2.png)

总的来说可以是半隐式方法。

![image-20230717172751919](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/LeapFrog.png)

可以看作是将速度的更新和位置的更新分开。

### 力

![image-20230717172953949](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/ForceType.png)

重力和阻力。但阻力可以简单地用一个常量作为系数去近似。

### 更新函数(只有平移运动)

![image-20230717173232295](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/TranslationSimulation.png)

## 旋转运动

![image-20230717173819198](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/RotationMatrix.png)

矩阵旋转不适合模拟

1. 太多的冗余，毕竟一个矩阵有9个元素。
2. 不直观，看了不知道怎么转。
3. 难以计算时间倒数(旋转的速度)。

![image-20230717174259439](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/RotationEulerAngle.png)

欧拉角在设计和控制中常用，但依然不适合模拟

1. 万向节死锁。
2. 也难以计算旋转的速度。

### 四元数

![image-20230717174741598](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/RotationQuat.png)

四元数被用于表示三维空间中的点。中间的图是四元数乘法表。

![image-20230717175332849](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/QuatArith.png)

四元数由两部分组成，实数部分s和虚数部分<strong>v</strong>，<strong>v</strong>是一个向量。

图中是四元数的运算法则。

### 四元数表示旋转

![image-20230717175703953](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/RotationQuat2.png)

<strong>v</strong>表示旋转轴，旋转的角度是θ，长度为1。因此<strong>V<sup>2</sup></strong>的长度是$\sin^2\frac{\theta}{2}$

![image-20230717180558225](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/Rotation.png)

用四元数表示旋转的姿势。

我们一般用三维向量<strong>ω</strong>表示角速度。

<strong>ω</strong>的方向是旋转轴，大小是旋转的速率。

![image-20230717182707361](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/Torque.png)

在旋转中等效于力的物理量称为力矩(Torque)，用<strong>τ</strong>表示。

<strong>r<sub>i</sub></strong>是原点到旋转点的向量。<strong>Rr<sub>i</sub></strong>是旋转后的点，<strong>f<sub>i</sub></strong>是这个点上施加的力。

在旋转中等效于质量的物理量成为惯性(还是惰性？Inertia)，用<strong>I</strong>表示。

Inertia是一个矩阵，首先计算出在旋转前(Reference)状态下的矩阵。

<center>$\mathbf{I_{ref}=\sum{m_i(\mathbf{r^T_{i}r_{i}1-r_{i}r^T_i})}}$</center>

m<sub>i</sub>是质点的质量？ <strong>1</strong>是单位矩阵。

然后计算旋转后的Inertia。<strong>I=RI<sub>ref</sub>R<sup>T</sup></strong>

## 运动方程

![image-20230717191328840](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/TranslationWithRotate.png)

![image-20230717192617487](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/Simulation2.png)

![image-20230717192837206](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/Implementation.png)

具体计算时，<strong>v、x、ω、q</strong>更新后只需要将原来的覆盖就行。

## 力矩

![image-20230717212556736](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/Torque2.png)

力矩在旋转中相当于力，它被用来形容一个力所造成的旋转的趋势，用**τ**表示。

之前已经了解$\mathbf{\tau_i=(Rr_i)\times f_i}$

所以<strong>τ<sub>i</sub></strong>与**<strong>Rr<sub>i</sub></strong>**以及<strong>f<sub>i</sub></strong>都垂直。

并且<strong>τ<sub>i</sub></strong>的长度与<strong>||Rr<sub>i</sub>||</strong>以及<strong>||f<sub>i</sub>||</strong>成正比，也与<strong>Rr<sub>i</sub></strong>和<strong>f<sub>i</sub></strong>的夹角的正弦sinθ成正比。

## 惯性(惰性)

![image-20230717214141865](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/Inertia.png)

与质量相似。

惯性力描述了对力矩造成的旋转趋势的抵抗。

与质量的不同在于，inertia不是一个常量。

![image-20230717214323716](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/02/Inertia2.png)

<center>$\mathbf{I_{ref}=\sum{m_i(\mathbf{r^T_{i}r_{i}1-r_{i}r^T_i})}}$</center>