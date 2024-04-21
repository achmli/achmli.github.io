---
layout:       post
title:        "Games101笔记04——Geometry"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
---



## 表示几何的方式

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230624165352388.png" alt="image-20230624165352388" style="zoom:100%;" />

### 隐式

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230624165418765.png" alt="image-20230624165418765" style="zoom:100%;" />

用函数来表示点，而不是直接表示点的位置。

容易判断点是否在表面上，容易做与光线的求交。

适合简单表面。

不容易找到表面上的点。

不适合复杂表面。

+ 代数表面
+ 构造刚体几何：通过几何体之间的并交补之类的运算得到复杂图形
+ 距离函数：不直接描述表面，而是描述任意一点到物体表面的最短距离

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230624170810190.png" alt="image-20230624170810190" style="zoom:50%;" />

+ 水平集：找到填满数的格子中值(或插值)为0的地方作为边界或表面。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230624171556858.png" alt="image-20230624171556858" style="zoom:100%;" />

+ 分形

### 显式

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230624165947986-2.png" alt="image-20230624165947986" style="zoom:100%;" />

直接存储点的位置，或者通过参数映射的方式存储点的位置。

优缺点与隐式相反。

+ 点云：点的列表。
+ 多边形面：三角形。

## 曲线

### 贝塞尔曲线

用一系列的控制点定义一条曲线。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230624200139483-2.png" alt="image-20230624200139483" style="zoom:100%;" />

t是从0到1的任意时刻，b0‘的位置在b0b1长度的t倍处，b1’在b1b2长度的t倍处，将两个点相连，取长度的t倍处的点，就是t时刻贝塞尔曲线上的点。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230624211816667.png" alt="image-20230624211816667" style="zoom:100%;" />

点的数量越多，需要计算的次数越多，知道最后只剩下一个点。

### 贝塞尔曲线线性方程表示

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230624212331686.png" alt="image-20230624212331686" style="zoom:100%;" />

n+1个控制点。

### 贝塞尔曲线性质

+ 起点是第一个控制点，终点是最后一个控制点。
+ 四个点时，起点的斜率是3(b1-b0),终点的斜率是3(b3-b2)。
+ 仿射变换时用四个点表示和直接用曲线不会发生结果的差异。
+ 曲线一定在控制点形成的凸包内。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230624213410377.png" alt="image-20230624213410377" style="zoom:100%;" />

## 逐段的贝塞尔曲线

一般而言用四个点定义一段贝塞尔曲线。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230624213742282.png" alt="image-20230624213742282" style="zoom:100%;" />

第四个点是上一段的终点和下一段的起点，第三个点和第五个点与第四个点应当在同一条直线上，并且第三个点与第四个点的长度应当和第四个点与第五个点的长度相同。用以保证整条贝塞尔曲线的平滑。

## 其他曲线

### Spline

一条经过一系列给定的点的平滑的连续曲线，可控。

### B-spline

对贝塞尔曲线的扩展

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230624214747434.png" alt="image-20230624214747434" style="zoom:100%;" />

对一个点的调整只影响范围内一部分曲线。

## 贝塞尔曲面

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230624215113629.png" alt="image-20230624215113629" style="zoom:100%;" />

首先，16个点按行/列分成四组，可以定义四条贝塞尔曲线。同时四条曲线上在相同t时刻的四个点可以产生一条贝塞尔曲线，t从0到1，就可以形成一个面。

### 贝塞尔曲面上的点

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230624215644904.png" alt="image-20230624215644904" style="zoom:100%;" />

可以通过二维的值找到贝塞尔曲面上的任意点。

## 曲面细分

### Loop细分

增加三角形的数量。调整顶点的位置。

分别改变旧顶点和新顶点的位置。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230625155641132.png" alt="image-20230625155641132" style="zoom:100%;" />

新顶点的位移。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230625155843215.png" alt="image-20230625155843215" style="zoom:100%;" />

旧顶点的更新。

### Catmull-Clark细分

可惜细分非三角形的面。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230625160543265.png" alt="image-20230625160543265" style="zoom:100%;" />

把面分为四边形面和非四边形面。

通过顶点的度分辨，度为4的点是非奇异点，其余的点为奇异点。新增的点位奇异点相邻的变的中点以及相邻非四边形面的中间点，将新顶点相连。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230625160923746.png" alt="image-20230625160923746" style="zoom:100%;" />

新增的奇异点的数量等于细分前非四边形面的数量，但是细分后不再有非四边形面。之后再进行细分就不会新增奇异点数量，同时也不会有非四边形面。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230625161519681.png" alt="image-20230625161519681" style="zoom:100%;" />

## 曲面简化

与细分相反，减少三角形。

### 边坍缩

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230625162214419.png" alt="image-20230625162214419" style="zoom:100%;" />

新增的点到被优化的点的相关的面的距离的平方和最小。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/04/image-20230625163040519.png" alt="image-20230625163040519" style="zoom:100%;" />

边的坍缩指将边坍缩成点。也因此计算每条边坍缩后的二次度量误差，坍缩二次度量误差最小的边。

如此往复到想要的结果。一般使用最小堆或者优先队列存储。贪心算法，不是最优解，但毕竟效果性能都不错。
