---
layout:       post
title:        "Games101笔记1——transform"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
---



# 变换

## 缩放

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230620203705360.png" alt="image-20230620203705360" style="zoom:50%;" />

缩放矩阵是对角矩阵，相应的行(列)上的值代表在这一方向上缩放的倍数。

### 翻转

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230620204327965.png" alt="image-20230620204327965" style="zoom:50%;" />

想要在特定的坐标轴上翻转，只要将缩放矩阵上该轴对应的行(列)上的值取负。

### 切变

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230620204755937.png" alt="image-20230620204755937" style="zoom:50%;" />

## 二维旋转

默认围绕原点逆时针旋转。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230620211649316.png" alt="image-20230620211649316" style="zoom:50%;" />

## 平移

### 齐次坐标

平移变换需要引入齐次坐标。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230620213626281.png" alt="image-20230620213626281" style="zoom:50%;" />

向量+向量=向量

点-点=向量

点+向量=点

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230620214146409.png" alt="image-20230620214146409" style="zoom:50%;" />

点+点=两个点的中点

### 仿射变换(齐次坐标下的变换)

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230620214315722.png" alt="image-20230620214315722" style="zoom:50%;" />

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230620214506980.png" alt="image-20230620214506980" style="zoom:50%;" />

## 逆变换

乘上变换矩阵的逆矩阵即可

## 组合变换

一般而言，变换顺序是缩放->旋转->平移。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230620215408645.png" alt="image-20230620215408645" style="zoom:50%;" />

一系列的组合变换可以表示成一个矩阵。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230620215428897.png" alt="image-20230620215428897" style="zoom:50%;" />

同理，变换也可以被分解。

## 三维变换

三维变换与二维变换大体上相同。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230620215838518.png" alt="image-20230620215838518" style="zoom:50%;" />

### 三维旋转(矩阵、右手系)

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230621120240946.png" alt="image-20230621120240946" style="zoom:50%;" />

### 三维旋转(欧拉角)

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230621121109337.png" alt="image-20230621121109337" style="zoom:50%;" />

### 三维旋转(罗德里格斯旋转公式)

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230621121233422.png" alt="image-20230621121233422" style="zoom:50%;" />

## MVP变换

### 视图变换(View)

默认摄像机在原点，方向朝向-z。因此视图变换需要将摄像机移至原点，并且旋转至以y轴朝上，朝向-z，整个场景也要跟着做相应的变换。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230621132453953.png" alt="image-20230621132453953" style="zoom:50%;" />

平移部分相对简单，旋转部分先求出摄像机从目标位置旋转到当前位置的旋转矩阵，因为目标位置的三个坐标轴相对简单，在求出这个矩阵的逆矩阵，由于坐标轴之间相互正交，所以逆矩阵等于转置矩阵，就得到了旋转变换的矩阵。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230621133052277.png" alt="image-20230621133052277" style="zoom:50%;" />

### 投影变换

#### 正交投影

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230621153511562.png" alt="image-20230621153511562" style="zoom:50%;" />

移动到原点，并缩放成1：1：1 。

#### 透视投影

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230621162220935.png" alt="image-20230621162220935" style="zoom:50%;" />

首先通过三角形相似的性质获得x‘和y'。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230621164321520.png" alt="image-20230621164321520" style="zoom:50%;" />

通过特殊情况（在近平面和远平面上）来求出矩阵未知的第三行。由于近平面和远平面的情况z’都只与z相关，而和x、y无关，所以第三行假设为(0 0 A B) 。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/01/image-20230621164924352.png" alt="image-20230621164924352" style="zoom:50%;" />

解二元一次方程组。