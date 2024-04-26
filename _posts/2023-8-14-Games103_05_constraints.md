---
layout:       post
title:        "Games103笔记05——Constraints"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games103
    - 图形学
    - 物理模拟
---



# 应变极限和Position Based Dynamics(PBD)

![image-20230721220747811](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721220747811.png)

真实世界的纺织物对拉伸反抗强烈，一旦拉伸超过了一个明确的限制

但是，增加刚性会导致问题

对显式积分，会导致不稳定。对隐式积分会导致ill-conditioned(病态？)。

都有办法解决，但都会大大增加计算量。

## 一根弹簧

![image-20230721221306129](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721221306129.png)

假设一根弹簧的刚性是无限的，就可以把长度当义成约束，并且定义一个投影函数。

拉伸时，让两个顶点相互靠拢，压缩时，让两个顶点互相远离。

修改顶点，使得满足约束。

![image-20230721221923142](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721221923142.png)

理解成六维空间，把弹簧的两个顶点理解成六维空间中的一个点。要做的投影就是修改<strong>x</strong>,让它落到符合约束的范围中去。而投影的位置应该是整个区域离当前的点最近的点(最近的表面上的点)。

![image-20230721222710278](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721222710278.png)

修改的方法。

## 多根弹簧

### 高斯-塞德尔方法

![image-20230721222938362](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721222938362.png)

先让一根满足约束，然后再修改另一根，如此往复。

![image-20230721223132862](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721223132862.png)

+ 不能保证所有约束都得到满足。
+ 与顺序有关。会影响误差和收敛速度。

### Jacobi Approach

![image-20230721223402553](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721223402553.png)

减少边的顺序所造成的影响，同时更容易实现并行。

先把更新的位置保存下来，每个顶点可能会有很多个更新，最后取平均。

但是收敛速度较慢，并且也是迭代次数越多越准确。

## PBD

![image-20230721231655046](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721231655046.png)

首先是顶点自由运动。

然后施加约束，通过投影更新<strong>x</strong>，然后使用新位置减旧位置除以时间步长当作这个时间片里的速度变化更新速度。

+ 没有物理要素。刚性通过迭代次数和网格数间接实现。
+ 速度更新对动态效果十分重要。
+ 这个方法可以实现一些其他的约束。比如三角形约束、体积约束。

![image-20230721232349596](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721232349596.png)

优点

+ 容易并行 
+ 容易实现
+ 在分辨率低的时候很快
+ 通用性较强

缺点

+ 物理上不正确
+ 高分辨率时效率低

## 应变极限(strain limiting)

![image-20230721233118615](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721233118615.png)

流程看上去和PBD是一样的，但是第一步粒子依然在做物理上的模拟，而不是自由运动。

![image-20230721233237907](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721233237907.png)

设定拉伸比例，并且拉伸比例有上下限。

在拉伸或压缩后，只要求弹簧长度回复到一定的范围内，而不是严格的原长

![image-20230721233458163](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721233458163.png)

先计算拉伸比。

然后设定目标拉伸比：设定一个范围，让拉伸比在这个范围内。

位置更新时用σ<sub>0</sub>L替换掉PBD中的L就好了。

可以认为PBD就是σ<sub>0</sub>恒等于1的情况。

### 三角形面积Limit

![image-20230721233947517](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721233947517.png)

想要的面积除以当前的面积就得到缩放比例，然后对原三角形缩放，就得到了更新后的三角形。

![image-20230721234320704](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721234320704.png)

1. 求出当前面积
2. 计算缩放比例
3. 计算质心
4. 以质心为中心缩放。

### strain limiting 在模拟中的用处

![image-20230721234247665](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230721234247665.png)

+ 避免不稳定和artifact
+ 对非线性表现很有用。
+ 可以帮助解决locking issue。

# Project Dynamics

![image-20230722105156237](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230722105156237.png)

project dynamics用投影去定义能量。

经过计算后，无论是能量还是力都与弹簧直接模拟相同。只是多了中间变量$\mathbf{x}\_{e,i}^{new}-\mathbf{x}\_{e,j}^{new}$。

![image-20230722112401819](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230722112401819.png)

只是Project Dynamics的Hessian最终会是一个常数矩阵。

![image-20230722112653104](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230722112653104.png)

projective dynamics的模拟过程。

![image-20230722112944026](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230722112944026.png)

相当于预计算了Hessian。

性能表现取决于Hessian矩阵的近似程度。

![](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230722113526420.png)

优点

+ 有物理含义
+ 在CPU上快
+ 在最初几次迭代快

缺点

+ 不适合GPU
+ 次数多了就满了
+ 不能很好的处理约束的变化。

# Constrained Dynamics

![image-20230722113856722](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230722113856722.png)

对于刚性十分强的情况。

![image-20230722114549165](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230722114549165.png)

获得了一个线性系统。

![image-20230722114727466](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/05/image-20230722114727466.png)

求解线性系统。

