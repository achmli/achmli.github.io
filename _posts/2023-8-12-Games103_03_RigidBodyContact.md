---
layout:       post
title:        "Games103笔记03——Rigid Body Contact"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games103
    - 图形学
    - 物理模拟
---



# 粒子碰撞

## 碰撞检测

### 有符号的距离函数(Signed Distance Function)

![image-20230717220049075](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230717220049075.png)

在曲面外的点距离为正，在曲面内距离为负，在平面上距离为0.

![image-20230717222007599](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230717222007599.png)

如果是平面，距离函数<em>Φ</em>(<strong>x</strong>)=(<strong>x-p</strong>)·<strong>n</strong>，即平面上任意一点与<strong>x</strong>的向量点乘这个平面的法向量，得到的值就是带符号的距离。这种情况把法线方向视作平面外，法线负方向视作平面内。

如果是球，距离函数<em>Φ</em>(<strong>X</strong>)=<strong>||x-c||</strong>-<em>r</em>，即<strong>x</strong>与圆心的距离减去半径，得到的值就是带符号的距离

如果是圆柱，距离函数$ \phi(\mathbf{x})=\sqrt{\lvert \lvert \mathbf{x-p} \rvert \rvert^2-(\mathbf{(x-p)\cdot n})^2}-r $，根号内求的是<strong>x</strong>到圆柱中心轴的距离<strong>||x-p||</strong>是斜边长度<strong>(x-p)·n</strong>是<strong>(x-p)</strong>在中心轴上投影的长度，利用勾股定理，就可以求得<strong>x</strong>到中心轴的距离，再减去半径r得到的值就是带符号的与曲面的距离。

![image-20230717223822423](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230717223822423.png)

对于由三个曲面相交而成的面，只要点和三个曲面的距离函数都小于0，那么就在面内。

点与面的距离取绝对值最小的那个。

在面外时的距离不能简单的通过三个曲面的距离函数获得，但是现在在做碰撞检测，所以也不重要。

![image-20230717223751196](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230717223751196.png)

对于两个曲面合并而成的面。只要点与两个曲面中的一个的距离函数小于0，点就在面的内部。

点在内部时的距离并不好求，可能与距离函数无关，约等于距离函数中较小的那个。

点在外部时，点与面的距离等于点与较近的曲面的距离。

## 碰撞处理

### Penalty Method

![image-20230717225626032](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230717225626032.png)

Penalty方法是当距离函数小于0时，在下一次刷新施加一个与“距离”反方向的力(距离函数的梯度)，力的大小与曲面的远近有关，越近，施加的力越小，越远，施加的力越大。

这种方法只有在粒子已经在曲面内部时才生效。可能会导致一些错误。

![image-20230717230347064](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230717230347064.png)

增加一个长度为<em>ε</em>的缓冲，不需要距离小于0，而是小于<em>ε</em>时，就对粒子施加补偿的力。

虽然解决了对粒子施加力过晚的问题，但是k值依然比较难去设定。过小导致物体可能依然延原方向运动，过大可能导致过度的反弹。

![image-20230717231039003](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230717231039003.png)

利用了距离函数的倒数，当距离越近，力就越大。

但是前提是距离始终为正，因此为了实现这种方法，必须调整好步长<em>Δt</em>。

不过还是会over-shooting。

![image-20230717231622265](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230717231622265.png)

+ 必须要调整步长。

1. 避免overshooting
2. 避免在log-barrier方法中穿透曲面。

+ log-barrier也可以试着加上buffer来优化。
+ 摩擦接触很难解决。

### Impulse Method

![image-20230718094830622](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718094830622.png)

脉冲方法(?)就是把在曲面内部的粒子沿法线方向移动到表面上。

![image-20230718100437996](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718100437996.png)

如果速度方向已经朝向表面外部(<strong>v·N</strong>>0),则不需要对速度进行改动。

反之，将速度分解为法线方向的分量和垂直法线方向的分量。

法线方向的分量$\mathbf{v_N=(v\cdot N)N}$，即速度在法线方向上的投影乘上法线方向。

垂直法线方向的分量$\mathbf{v_T=v-v_N}$，向量的分解。。。

在刷新时，两个方向都需要与一个系数相乘。

法线方向：$\mathbf{v_N^{new}}\leftarrow - \mu_N\mathbf{v_N}$，法线方向的分量刷新时需要乘上一个负的系数，由于要符合能量守恒，所以<em>μ</em><sub>N</sub>一般在0到1之间

垂直法线方向：$\mathbf{v_T^new}\leftarrow a\mathbf{v_T}$，切线方向的分量只需要乘上一个正的系数，是摩擦导致的切方向的衰减。a的求解应该符合库仑定律，$a\leftarrow max(1-\mu _\mathbf{T}(1+\mu_\mathbf{N})\mathbf{\lvert \lvert v_N \rvert \rvert / \lvert \lvert v_T \rvert \rvert},0)$，<em>μ<sub>T</sub></em>应该是摩擦系数之类的值。

# 刚体碰撞

## 碰撞检测

![image-20230718112133372](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718112133372.png)

检测刚体上的每个顶点是否与表面碰撞。点的位置是<strong>x<sub>i</sub></strong> ⬅ <strong>x+Rr<sub>i</sub></strong>。

## 碰撞响应

![image-20230718113243889](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718113243889.png)

对于每个顶点碰撞时状态的描述，并没有提及怎么去刷新变量。位置变量和速度变量

![image-20230718170531920](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718170531920.png)

速度的刷新。

给碰撞时的速度施加一个新的脉冲速度<strong>j</strong>，同时<strong>j</strong>也会有旋转方向的分量，这样就可以刷新顶点的速度。

![image-20230718114955284](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718114955284.png)

可以用矩阵乘法替换叉乘。

![image-20230718165218677](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718165218677.png)

<strong>K</strong>可以求解，现在只剩下求解<strong>j</strong>。

![image-20230718115600745](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718115600745.png)

碰撞相应过程。灰色框计算想要的刷新后的<strong>v<sub>i</sub></strong>，但是这不是一个应用到顶点上的结果，因为对刚体的描述并不包含顶点，这个值我们用作中间值来求出施加到整个刚体上的冲量<strong>j</strong>。

### 实现时的细节

![image-20230718120049479](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718120049479.png)

+ 有许多顶点时，求平均值。
+ 可以使用一个补偿<em>μ</em><sub>N</sub>来减少抖动。

## Shape Mapping

![image-20230718120426400](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718120426400.png)

首先让每个顶点都自由运动。

然后在约束成原来形状的刚体。

![image-20230718120548043](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718120548043.png)

求质心<strong>c</strong>和旋转矩阵<strong>R</strong>的方法。

argmin表示使目标函数取最小值时的变量值。

首先将旋转矩阵<strong>R</strong>扩展为任意矩阵，也就可以将<strong>A</strong>设定为常数矩阵。

由于要求最小值，所以求导，在其导数为0时，能求出最小值。

最终求得质心坐标与四个自由运动的顶点<strong>y<sub>i</sub></strong>的质心相同。

![image-20230718122341164](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718122341164.png)

然后相同的方法求解<strong>A</strong>。

然后<strong>R</strong>通过极分解求得，<strong>S</strong>是一个形变矩阵。

![image-20230718122739547](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718122739547.png)

分解<strong>A</strong>的原理。

![image-20230718122841670](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718122841670.png)

Shape Mapping流程。

![image-20230718122937010](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/03/image-20230718122937010.png)

+ 容易实现，并且容易和基于点的模拟结合
+ 不容易满足约束和摩擦。