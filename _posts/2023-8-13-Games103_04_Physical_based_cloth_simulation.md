---
layout:       post
title:        "Games103笔记04——Physical Based Cloth Simulation"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games103
    - 图形学
    - 物理模拟
---



# 弹簧质点系统

## 胡克定律

![image-20230720175333947](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230720175333947.png)

左半边是一端固定的情况，右边是两端都可拉伸的情况。

总的而言，能量是拉伸后长度与原长度的差的平方与刚性系数的积除以2 。

而力的大小是能量的导数。大小是拉伸后长度与原长度的差与负的刚性系数的积。

左边一维的情况力没有方向，右边二维的力有方向，所以最后要乘上里的方向。两个力大小相同，方向相反(牛顿第三定律)。

## 多根弹簧

![image-20230720191355754](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230720191355754.png)

能量的叠加和力的叠加。每根弹簧单独计算能量和力，然后叠加在一起。

## 结构化的弹簧网络

![image-20230720192816715](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230720192816715.png)

正方形的网格并且连接每个网格的对角线。并且为了防止弯折边界上的点也要隔着格子用弹簧相连。

可以简化对角线上的弹簧，把一个格子扩展成4个。既能减少弹簧数量，也能有格子间的差异，有的45°有的135°。

## 非结构化的弹簧网络

![image-20230720195157381](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230720195157381.png)

将非结构的三角形为基础的mesh转换成弹簧网络。

把每条边都当成弹簧。并每两个相邻的三角形跨过一条共享的边连接相对的两个点，产生弯曲的抵抗。

### 构造的方法

![image-20230720202327007](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230720202327007.png)

三角形网格的表示方法。用顶点位置的列表，和三角形有哪三个顶点的列表。

![image-20230720203212727](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230720203212727.png)

先构造一个列表，存储边的信息，数组的基础元素是三个数的数组或者向量，前两个数表示边的两个顶点的编号，编号小的在第一个位置，第三个数表示属于哪个三角形。这样一个三角形就会有三条边，共享的边也会多次存储。

然后将这个列表排序，三个数字优先级依次减小排序。然后共享的边就会在相邻的位置上。然后遍历一遍就可以找出所有的共享的边。

最后剔除掉这些重复的边，构造弹簧时就是剩下的边，最终存储时不需要三角形的编号。

而被剔除的边就可以用来构造抵抗弯曲的弹簧，可以存储相邻的三角形的编号的数对，也可以直接存储弹簧的顶点。

# 弹簧质点系统的求解

## 显式积分

![image-20230720205104901](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230720205104901.png)

右边是标准的粒子系统。

左边是弹簧系统的里的计算。

每根弹簧有列表存储了两个顶点的索引，另一个列表存储了弹簧的初始长度。

然后就可以计算力。

应该先把每个顶点的里都求出来，再更新每个粒子的位置。

![image-20230720211153237](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230720211153237.png)

显式的积分会导致数值上的不稳定。弹簧会有不合理的长度变化，如上图的长度变化过程。

尤其是在k或者时间步长非常大的情况下。

## 隐式积分

![image-20230720212111868](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230720212111868.png)

隐式积分有更好的稳定性，但需要用到在求解出的位置的力。这里需要假设力之和位置有关，而弹簧也确实是这种力(holonomic)。最大的问题是力与位置的关系不是线性的。

![image-20230720211654846](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230720211654846.png)

求解<strong>x<sup>[1]</sup></strong>的等式可以等价为<strong>x<sup>[1]</sup></strong>=argmin <em>F(<strong>x</strong>)</em> ，argmin表示<em>F(<strong>x</strong>)</em>取最小值时<strong>x</strong>的值。

<center>$F(\mathbf{x})=\frac{1}{2\triangle t^2}\vert \lvert \mathbf{x-x^{[0]}}-\triangle t\mathbf{v^{[0]}}\rvert \rvert^{2}_{\mathbf{M}}+E(\mathbf{x})$</center>

其中$\lvert \lvert \mathbf{x}\rvert \rvert|^2_{\mathbf M}$这个格式代表了<strong>x<sup>T</sup>Mx</strong>。

<strong>M</strong>是质量矩阵，一般来说是一个对角矩阵。是一个3N*3N的矩阵。

每个<strong>x</strong>都是3*N的向量，存储了所有顶点的位置。

<em>E</em>(<strong>x</strong>)是在<strong>x</strong>位置的能量。

推导：<em>F</em>(<strong>x</strong>)取最小值时，可以认为其梯度$\nabla F(\mathbf x)$为0 。

### 牛顿法

![image-20230720222029462](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230720222029462.png)

牛顿法的前提是函数连续。

牛顿法就是泰勒展开的近似。

<center>$F'(x) \approx F'(x^{(k)})+F''(x^{(k)})(x-x^{(k)})$</center>

函数的导数近似的等于任意位置二阶导数的值与x和当前位置的差的积加上当前位置一阶导数的值。

![image-20230720222905948](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230720222905948.png)

伪代码。

Δx是x与x<sup>(k)</sup>的差，通过上面的等式可以求出Δx，只要Δx足够小，就可以认为x<sup>(k+1)</sup>就是最终要求的x。

![image-20230721143802983](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721143802983.png)

有多个倒数为1的点时。

首先二阶导大于0，然后原函数的值最小的那个。

如果二阶导数恒大于0，那么没有极大值，且只有一个最小值。

![image-20230721144655954](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721144655954.png)

牛顿法在弹簧系统中的使用。

![image-20230721145248947](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721145248947.png)

牛顿法模拟过程。~~毫无疑问我是没看懂的~~

### Spring Hessian

![image-20230721150325917](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721150325917.png)

海森矩阵：在多元微分函数中，一个函数的二阶偏导数构成的矩阵，通常用于描述函数的曲率和凹凸性。

![image-20230721184100118](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721184100118.png)

弹簧被拉伸时，Hessian正定，而被压缩时，可能就不是正定的。

因为质量矩阵是正定的，所以在被压缩时Hessian也可能正定。

最终的正定性影响解的数量，如果正定，则有唯一解，相反，则解不一定唯一。

![image-20230721185021741](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721185021741.png)

压缩时非正定的现实解释。

以及一维的弹簧二阶导恒大于0，所以不会有非正定的情况。

![image-20230721185546269](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721185546269.png)

压缩时的应对方法，最粗暴的就是如果非正定，就把橙色框内的部分删除。

### Jacobi Method

![image-20230721185928114](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721185928114.png)

雅各比法的流程

首先让Δ<strong>x</strong>等于0，

然后求<strong>b-AΔx</strong>的值，赋给<strong>r</strong>，如果<strong>r</strong>的模足够小就停止。

否则，更新<strong>Δx</strong>，$\mathbf{\Delta x}\leftarrow \mathbf{\Delta x}+\alpha\mathbf{D^{-1}r}$，<strong>D</strong>是<strong>A</strong>的对角矩阵。

如果α等于1，要求<strong>A</strong>对角占优。

![image-20230721191048285](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721191048285.png)

解数值方法的两种方式的对比。

# 弯曲

![image-20230721205949030](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721205949030.png)

当布料几乎是平面时，弯曲的弹簧提抗弯曲的力十分微弱。

## 二面角模型

![image-20230721210252435](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721210252435.png)

二面角模型定义弯曲的力为关于两个面的夹角的函数。

1. <strong>u<sub>1</sub></strong>和<strong>u<sub>2</sub></strong>的方向应当于两个面的法线方向<strong>n<sub>1</sub></strong>和<strong>n<sub>2</sub></strong>相同。
2. 弯曲不应该导致边缘<strong>x<sub>3</sub> x<sub>4</sub></strong>的拉伸，所以<strong>u<sub>4</sub>-u<sub>3</sub></strong>应当于这条边正交，这意味着<strong>u<sub>3</sub>-u<sub>4</sub></strong>于<strong>n<sub>1</sub></strong>和<strong>n<sub>2</sub></strong>都在一个面上，<strong>u<sub>3</sub>-u<sub>4</sub></strong>是<strong>n<sub>1</sub></strong>和<strong>n<sub>2</sub></strong>的线性组合。
3. 四个力相加应该完全抵消。这意味着<strong>u<sub>3</sub></strong>和<strong>u<sub>4</sub></strong>是<strong>n<sub>1</sub></strong>和<strong>n<sub>2</sub></strong>的线性组合。

![image-20230721212131560](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721212131560.png)

四个力的求解结论。

这里的“法向量”并没有归一化。

![image-20230721212338291](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721212338291.png)

二面角模型的函数。

θ<sub>0</sub>是非平面情况下，静止状态的夹角大小。也可以认为平面状态下这个角是180度所以等于0。

## 二次的弯曲模型

![image-20230721212911513](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721212911513.png)

这个模型有两个前提：1. 平面情况，2.拉伸十分微小。

![image-20230721213311215](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721213311215.png)

+ 容易实现
+ 适合隐式迭代(因为是二次模型)
+ 如果布料弹性比较好就不再有效
+ 不适合非平面情况

# Locking Issue

![image-20230721213914509](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721213914509.png)

目前为止，我们认为平面的形变和弯曲的形变是独立的。

![image-20230721214115065](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/04/image-20230721214115065.png)

DoFs：degrees of freedoms

欧拉方程：边的数量=3x顶点数-3-3x独占的边的数量

如果所有边都是hard constraints(强约束？)，自由度只有3+独占的的边的数量。
