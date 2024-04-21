---
layout:       post
title:        "Games103笔记01——Mathematics"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games103
    - 图形学
    - 物理模拟
---



# 向量

向量的表示一般用黑体，而标量一般用斜体。

![Vector](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/Vector.png)

stacked vector：向量可以叠成一个高维的向量，常用来表示一个物体的状态。

## 向量加法

![VecAdd](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/VecAdd.png)

### 线性表示

![LinearAdd](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/LinearAdd.png)

<strong>p</strong>(t)=(1-t)<strong>p</strong>+t<strong>q</strong> 是<strong>p</strong>和<strong>q</strong>插值，权重是t。

## 矢量大小

![VecNorm](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/VecNorm.png)

各种矢量大小的定义，一般而言用第一种2-norm。

## 点乘(内积)

![VecDotProduct](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/VecDotProduct.png)

出了图中两种表示方法，还可以用<<strong>p</strong>,<strong>q</strong>>表示。

### 平面的表示

![Plane](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/Plane.png)

给定法向量，并且规定法向量的方向就是朝上的方向。

法向量与平面的交点是<strong>c</strong>，取任一点<strong>p</strong>，求(<strong>p</strong>-<strong>c</strong>)*<strong>n</strong>的值，即<strong>p</strong>-<strong>c</strong>在方向n上的投影长度 <em>s</em>。

如果s>0，<strong>p</strong>点的位置高于平面。
如果s=0，<strong>p</strong>点的是位于平面上的点。
如梭s<0，<strong>p</strong>点的位置低于平面。

同时所有满足s=0的点，构成了平面。可以用这种方法定义平面。

### 射线与球面求交

![ParticleSphereCollision](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/ParticleSphereCollision.png)

总之就是向量<strong>p</strong>上存在一点，使得<strong>p</strong>(<em>t</em>)与<strong>c</strong>的距离等于半径<em>r</em>，从而进一步联立方程，而有没有解有几个解就是中学数学了。

~~实际上一直很好奇为什么不通过<em>t</em>=(<strong>c</strong>-<strong>p</strong>)<strong>∙</strong><strong>v</strong>求出来与<strong>v</strong>正交的向量(<strong>p</strong>(<em>t</em>)-<strong>c</strong>)，用它的长度和<em>r</em>作比较来判断是否相交，从games101就开始好奇，实际上是从<em>Ray Tracing In One Weekend</em>开始好奇的，因为games101第一次看的时候根本没有认真学~~

## 叉乘

![CrossProduct](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/CrossProduct.png)

### 三角形表面的面积和法向量

![TriangleArea](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/TriangleArea.png)

两个向量叉乘毕竟得出的向量方向与两个向量都正交，然后再归一化就是法向量了。

至于面积，面积是边长乘以这条边上的高除以2。而高是另一条边的边长乘上两条边的夹角的正弦值。
刚好两个向量叉乘得到的向量的长度刚好是两个向量的长度相乘再乘上两条向量夹角的正弦。所以两条边用它们的公共顶点作为起点，长度是边长，方向是边的方向的向量叉乘求模再除以2就是三角形的面积了。

~~数学真是神奇啊~~

![Quiz](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/Quiz.png)

叉乘为<strong>0</strong>就是在一条线上嘛。。。

### 点在三角形的内外

![InsideOrOutsideTriangle](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/InsideOrOutsideTriangle.png)

_Games101_就提过还写过作业，就当复习吧，实际上就是三次叉乘的方向全都相同就在三角形内，而假如有一次与另外两次方向相反，那么就在三角形外面。

![InsideOrOutsideTriangle2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/InsideOrOutsideTriangle2.png)

不过点乘个<strong>n</strong>也很合理，毕竟判断数字正负还是更简单。

### 重心坐标

![Barycentric](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/Barycentric.png)

![GouraudShading](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/GouraudShading.png)

Gouraud着色通过三角形顶点的颜色的插值获得像素的颜色。

### 四面体体积

![TetrahedralVolume](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/TetrahedralVolume.png)

底面面积就是求三角形面积。而高是四面体比三角形多的那条边在底面法向量上的投影长度。而地面的法向量也已经知道怎么求了。法向量必然是已经归一化了的向量，所以只要新的边的向量与法向量点乘就求出了高的长度。而后体积就只要底面积*高/3就完事了

![TetrahedralVolume2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/TetrahedralVolume2.png)

体积的定义。

### 四面体的重心坐标

![BarycentricWeight](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/BarycentricWeight.png)

### 射线与三角形求交

![ParticlePlaneIntersection](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/ParticlePlaneIntersection.png)

<em>Games101</em>里使用的是MT算法，给定平面上任意三个能组成三角形的点，可以解出t和交点的重心坐标，并可以借由重心坐标判断交点是否在三角形内。

![MollerTrumbore](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230626215502683-2.png)

# 矩阵

## 概念

![Matrix](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/Matrix.png)

大概就是一些基本概念。

![MatMultiply](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/MatMultiply.png)

矩阵乘法

### 正交矩阵

![Orthogonality](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/Orthogonality.png)

正交矩阵的转置等于正交矩阵的逆

## 矩阵变换

### 旋转

![RotationMat](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/RotationMat.png)

### 缩放

![ScaleMat](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/ScaleMat.png)

### 奇异值分解

![SingularValue](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/SingularValue.png)

所有的线性变换都可以分解成三部分，即旋转->缩放->旋转。

### 特征值分解

![EigenValue](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/EigenValue.png)

特征值分解是奇异值分解的特殊情况，矩阵<strong>U</strong>不仅是正交矩阵，同时也应该是对称矩阵。

### 对称正定性

![SPD1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/SPD1.png)

![SPD2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/SPD2.png)

正定意味着特征值均为正。

可以用对角占优来判断是否是正定，但这只是充分条件。

s.p.d.必然是可逆的。

# 线性系统

![LinearSolver](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/LinearSolver.png)

许多数值问题最终要解一个线性系统。

求解<strong>A</strong><sup>-1</sup>的代价是是很大的，尤其当是<strong>A</strong>巨大又稀疏所以不能简单地通过求逆来求解。

## Direct Linear Solver

![DirectLinearSolver](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/DirectLinearSolver.png)

基于LU分解，或者是它的变种。主要区别在于占用内存。LU分解一般是最占内存的，然后是LDL<sup>T</sup> , Cholesky一般最节省内存。

LU分解：将矩阵分解成<strong>L</strong>和<strong>U</strong>两部分。分别只有下半三角和上半个三角。

第一步通过下三角矩阵求解<strong>Ly=b</strong>，从上往下解出向量<strong>y</strong>
第二步通过上三角矩阵求解<strong>Ux=y</strong>，从下往上求出最终的解<strong>x</strong>

~~那么问题来了，<strong>b</strong>是从哪来的？~~

哦，<strong>b</strong>就是原来原来线性方程的常量，由于是线性，可以先通过下三角矩阵求出中间解，然后再通过中间解和上三角矩阵最终求得<strong>x</strong>。

![DLS](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/DLS.png)

+ 如果<strong>A</strong>是稀疏的，那么<strong>L</strong>和<strong>U</strong>不是稀疏的。它们的稀疏性取决于排列。
+ 计算由两部分构成：

1. 分解
2. 求解

+ 如果必须要用相同的<strong>A</strong>求解许多个线性系统，那么分解只需要做一次，尽管求解依然要进行许多次。
+ 不容易用并行运算。(但不是不行，比如Intel MKL PARDISO库)。

## Iterative Linear Solver(迭代法)

迭代法通常的形式：$\mathbf{x}^{[k+1]}=\mathbf{x}^{[k]}+\alpha\mathbf{M^{-1}}(\mathbf{b-Ax}^{[k]})$

其中<strong>x</strong><sup>[k+1]</sup>为这一次迭代的结果，<strong>x</strong><sup>[k]</sup>为上一次迭代的结果，α是系数，<strong>M</strong><sup>-1</sup>是迭代矩阵，<strong>b-Ax</strong><sup>[k]</sup>是残差，即上一次迭代的结果与最终结果之间的误差。

![IterativeLinearSolver](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/IterativeLinearSolver.png)

spectral radius：谱半径，绝对值最大的特征值。

![ILS](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/ILS.png)

**M**必须是容易求解的

1. Jacobi方法：<strong>A</strong>的对角矩阵
2. Gauss-Seidel方法：<strong>A</strong>的下三角矩阵。

### 迭代法的优点

+ 容易实现
+ 在精度要求不高时，可以快速得出非精确解。
+ 容易并行计算

### 迭代法的缺点

+ 并非所有矩阵都可以收敛
+ 求出精确解非常慢。

# Tensor Calculus(张量计算？)

## 一阶导数

![TensorCalc1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/TensorCalc1.png)

对矢量求导等于对x、y、z的每一项求导。横着写是偏微分，竖着写是梯度。

对于上升的<em>f</em>，梯度是最陡峭的方向，与等值面(等高线？)垂直。

![TensorCalc2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/TensorCalc2.png)

当函数是一个矢量时。

散度(Divergence)：Jacobian矩阵对角线的和。

Curl：流体中做漩涡？

## 二阶导数

![SecondOrderDerivatives](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/SecondOrderDerivatives.png)

## 泰勒展开

![Taylor](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/Taylor.png)

## 向量长度的求导

![VecLength](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/VecLength.png)

### 举例：弹簧

一个点：

![Spring1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/Spring1.png)

两个点：

![Spring2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/01/Spring2.png)
