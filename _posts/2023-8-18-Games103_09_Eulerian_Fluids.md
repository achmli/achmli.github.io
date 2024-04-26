---
layout:       post
title:        "Games103笔记09——Eulerian Fluids"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games103
    - 图形学
    - 物理模拟
---



# A Grid Representation(网格式的表示)

![image-20230810135543748](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810135543748.png)

将空间用网格划分。

网格就可以拥有一些属性，比如密度、压力、温度等的这类标量，也可以是速度这样的矢量。

每个网格就形成了场。便于计算微分之类的

## Central Differencing

![image-20230810150420013](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810150420013.png)

这是上节课的内容，最终得到的微分是二阶精确的。

![image-20230810152406555](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810152406555.png)

根据Central Differencing，求在网格上的微分时，只要两个相邻网格的值的差除以网格的边长。

![image-20230810153416202](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810153416202.png)

同理，在计算出周围的一阶导数后，就可以用同样的方法求二阶导。

![image-20230810155855589](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810155855589.png)

两个二阶导数相加就是周围四个网格的值相加再减去网格值的四倍除以网格的面积，称为拉普拉斯算子。

## 边界的情况

![image-20230810160920429](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810160920429.png)

与上节课讲的基本上是相同的。

## 拉普拉斯方程

![image-20230810162928601](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810162928601.png)

与流体模拟无关，但是是数值计算经典的问题。

每个网格的拉普拉斯算子都等于0。

至少有一个边界是Dirichlet，因为Neumann边界的拉普拉斯算子少了一个变量，矩阵的秩小于矩阵的行数，线性系统就会有无数个解。

拉普拉斯平滑在模拟里被称为diffusion(扩散？)。

## Central Differencing的问题

![image-20230810170002561](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810170002561.png)

问题在于一阶导数。

一阶导数求出的值在格子的边上，但这里是没有办法存储的，因为不存在这个点。

不是不能算，但是用到了左边的网格，用到了右边的网格，要换个方向，上下的也能用到，唯独没用到自己的值。

![image-20230810171007010](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810171007010.png)

解决方法，不是把所有变量的值都定义在网格中间，而是把一些值定义在网格的边上，在流体模拟中把速度定义在网格的边上。速度可以分解为x方向的速度和y方向的速度，x方向的速度定义在竖的边上，y方向定义在横的边上。(是不是也和速度是位置关于时间的一阶导有关。。。)

这种方法被称为Staggered Grid。

可以通过四条边上的速度计算单位时间净流出量。右边+上边-左边-下边。

![image-20230810172906415](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810172906415.png)

不可压缩的流体等价于单位时间净流出量为0的流体。

Divergence是关于x的微分与关于y的微分的和。等于0时等价于净流出量，所以体积不变不可压缩的情况被称为Divergence-free。

![image-20230810174118163](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810174118163.png)

双线性插值。这是默认h=1了吗，为什么不用除边长。。。

# Navier-Stokes Equations

![image-20230810180035055](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810180035055.png)

方程的配方。

Navier-Stokes方程组有两个等式。描述运动场的更新。

由于是计算不可压缩的流体，所以Divergence应当为0 。

同时，速度的更新应当满足动量的函数。

## Step 1. 外部的加速度

![image-20230810180844143](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810180844143.png)

把y方向的速度记为<strong>v</strong>，速度的更新就是原速度与<strong>g</strong> <em>Δt</em>相加。

## Step 2. Advection

![image-20230810185021107](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810185021107.png)

用图中公式与时间步长的积加到速度上就完成了速度的更新。

但这种解决方案容易导致不稳定。

Advection是流动、对流、导流的意思。毕竟速度归根结底还是粒子的速度，所以拉格朗日方法就不会有这里的问题。

### Semi-Lagrangian Method

![image-20230810210421714](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810210421714.png)

![image-20230810210447674](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810210447674.png)

思路是找到流到当前位置的粒子，通过当前的速度回溯到上一时间步长，计算出速度。

有位置就能通过插值获得速度。

![image-20230810210623748](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810210623748.png)

可以通过细分时间步长获得更精确的结果。

## Step 3. Diffusion

![image-20230810210955139](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810210955139.png)

就是前面提过的拉普拉斯平滑。但是时间步长太大，依然会不稳定。

![image-20230810211155045](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810211155045.png)

解决方法与半拉格朗日类似，将时间步长进一步细分。

## Step 4. Pressure Projection

![image-20230810211559405](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810211559405.png)

压强定义在各自中间，而速度在网格的边上，所以相邻网格压强central differencing就是在边上的，可以直接应用到速度上。

![image-20230810212122790](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810212122790.png)

压强是因为不可压缩产生的。

通过不可压缩等价的Divergence-Free的特性，可以获得上面的方程。

![image-20230810212235907](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810212235907.png)

整理后可以得到上面的方程组。

# 空气和烟

![image-20230810212452752](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810212452752.png)

首先更新速度，然后通过半拉格朗日方法获得其他的物理属性。

开放空间用Dirichlet边界，封闭容器用Neumann边界。

水下环境也同样适用。

# 水模拟

![image-20230810213042757](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/09/image-20230810213042757.png)

+ <strong>两种表示方法</strong>
  + 流体占网格的体积。
  + 距离场：存储当前网格到水面的距离

+ <strong>怎么计算导流</strong>
  + 半拉格朗日
  + Level set method：针对距离场的方法
  + 这两种方法都会导致体积的损失，需要校正。

