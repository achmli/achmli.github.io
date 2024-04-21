---
layout:       post
title:        "Games101笔记02——Rasterize"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
---

# 三角形

## 视口变换

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230622160257648.png" alt="image-20230622160257648"  />

视口变换就是将坐标轴原点从左下角到中心，将-1到1的范围变成0到width和0到height。

## 采样

获得一个函数在某点的值叫做采样。
对屏幕的采样就是利用像素中心进行采样。

## 光栅化三角形

遍历所有像素，利用线性代数中提到过的判断点是否在三角形内的方法，判断像素中心是否在三角形内，设置像素的颜色等属性。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230622191933685.png" alt="image-20230622191933685"  />

### 优化

只遍历三角形AABB包围盒内的像素，而不是整个屏幕。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230622193758445.png" alt="image-20230622193758445"  />

# 反走样(抗锯齿)

信号变化速度大于采样速度导致走样。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230622202256034.png" alt="image-20230622202256034"  />

先对信号进行模糊，再进行采样。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230622202346156.png" alt="image-20230622202346156"  />

反过来，先采样再模糊不行。

## 滤波

### 过滤低频信号(高通滤波)

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230622203659931.png" alt="image-20230622203659931"  />

提取边界

### 过滤高频信号(低通滤波)

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230622203804578.png" alt="image-20230622203804578"  />

模糊

### 同时过滤高频和低频信号

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230622204026255.png" alt="image-20230622204026255"  />

## 卷积

滤波=卷积=平均

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230622205814917.png" alt="image-20230622205814917"  />

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230622210132046.png" alt="image-20230622210132046"  />

时域的卷积相当于频域的乘积。

### 滤波核

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230622210409878.png" alt="image-20230622210409878"  />

低通滤波器

## 采样

采样=重复频域上的内容

## 走样

走样=复制频率时，频谱上的内容发生了混叠

## 反走样操作

### MSAA

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230622211903334.png" alt="image-20230622211903334"  />

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230622211926350.png" alt="image-20230622211926350"  />

### 现代反走样

#### FXAA

找到图像边界，替换成没有锯齿的图像。

#### TAA

混合上一帧的图像和当前帧。

### DLSS

深度学习超采样。

# 深度缓冲

## 可见性算法

### 画家算法

先光栅化远处的物体，再光栅化近处的，覆盖住远处的物体。

光栅化立方体时，先光栅化背面，然后光栅化周围四个面，在最后光栅化正面。

但是光栅化周围四个面时，虽然深度相同，但依然需要排序。

无法解决物体之间相互遮挡的问题，所以画家算法只在一个物体相对深度完全相同的情况

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230623105140759.png" alt="image-20230623105140759"  />

## 深度缓冲

每个片段找到这个片段中最近的物体，并渲染这个片段，并不一次性光栅化整个物体。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/02/image-20230623105202615.png" alt="image-20230623105202615"  />