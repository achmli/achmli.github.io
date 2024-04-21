---
layout:       post
title:        "Games202笔记03——Environment"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games202
    - 图形学
---



# 环境光

用图片表示的各个方向来自无穷远的光照。有两种主流方法表示环境光，球面贴图和立方体贴图(Sky Box)。

被非官方地称为IBL(Image-Based Lighting)。

而渲染的工作就是解渲染方程。而环境光就是其中的入射光项。

一般而言，对于积分，最优的做法是蒙特卡洛积分，可以得到无偏的结果，但是需要非常多的采样。所以蒙特卡洛积分的效率很低。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/BRDF.png" alt="BRDF" />

渲染方程中积分部分，除了入射光项和一般不考虑的可见度项，还有BRDF项，当材质偏向镜面反射时，积分范围较小，而材质偏向漫反射时，函数曲线比较光滑，非常适合Recap那节课讲的积分的近似方法。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/Equation.png" alt="IBL" />

上面是环境光的计算，下面是阴影的计算。

框出来的部分已经与BRDF无关了，就是对环境光积分并且归一化，而环境光是固定的，已经不会变了。所以可以对环境光部分做提前的处理。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/Prefilter.png" alt="LUT" />

对环境光帖图做预滤波，得到每个方向积分后的Radiance，同时可以用不同的滤波核得到模糊程度不同的预滤波环境光，以适应材质不同的粗糙度，通过插值可以获得所有粗糙度对应的环境光Radiance。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/Query.png" alt="LUT" />

由于已经保存了滤波后的结果，不同的材质查询环境光时，都只需要查询镜面反射方向的预滤波环境光的值，材质只决定查询的贴图的模糊程度。

在解决了入射光项之后，BRDF项的积分依然亟待解决。也可以用预计算的方法去解决，但是会十分消耗存储空间。

复习：微表面BRDF

菲涅尔项：入射光角度与反射能量的关系

阴影遮盖：自遮挡

法线分布：能将光线从入射方向反射到反射方向的微表面占所有微表面的比例。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/Microfacet.png" alt="BRDF" />

菲涅尔项和法线分布常用的数学模型。

schlick近似中，R<sub>0</sub>是初始反射率，θ是入射角。

Beckmann分布中：α是粗糙度参数，θ是半程向量与法线的夹角

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/SplitSum.png" alt="BRDF" />

使用Schlick近似将菲涅尔项在渲染方程中展开，这样就可以将变量之一的基础反射率(基础颜色)R<sub>0</sub>放到积分外，只剩下了粗糙度和入射角两个变量(几个角度之间转化相对容易)，就可以相对容易的做预计算了。

这一系列拆解积分的方法被称为Split Sum。

# 环境光阴影

对于实时渲染很难实现。

对于多光源的情况，需要每个光源都生成各自的Shadow Map，开销会十分大。同时环境光照下可视度项会很复杂，不容易从积分中分离出来。

工业上的方法是只生成最亮光源的Shadow Map。

## 背景知识

两个函数乘积的积分可以被视为滤波。

低频就是光滑的函数。

积分后的频率是两个函数中最低的频率。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/BasicFunc.png" alt="Basis" />

基函数通常是一组相互独立的函数，它们可以通过线性组合来表示其他函数。

## Spherical Harmonics(球谐函数)

是一系列定义在球面上的二维的基函数。定义在球面上的二维函数可以表示方向，在球面坐标系中，一个点的位置不再由直角坐标 (x, y, z) 来描述，而是由球坐标 (r, θ, φ) 来描述，其中：r 是点到球心的距离（半径），θ 是与正 x 轴的夹角，φ 是与正 z 轴的夹角。而θ和phi就可以用来表示方向了。

与一维的傅里叶函数非常相似。

球谐函数每一阶代表一种频率，阶越高，频率就越高，基函数的项数就越多。阶为*l*时，项数为2*l*+1，前*l*阶总共有*l<sup>2</sup>*个基函数。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/SphericalHarmonics.png" alt="Basis" />

球面谐波（Spherical Harmonics）是一组用于表示在球面上的函数的基函数。它们通常用于描述球对称问题和球面上的函数分布。球面谐波是三维笛卡尔坐标系中角度部分的解，其基本形式由雅克比多项式和勒让德多项式组成。

计算球谐函数的基函数的系数被称为投影，是原函数与当前所求系数对应的基函数的乘积的积分

用*l*<=3的球谐函数复原函数，相当于抛弃了频率高于3阶的频率的原函数。也就是还原是抛弃哪一阶，原函数就过滤掉了那一阶对应的频率。

上图右下角图中理解：蓝色越偏白表示值越大，偏黑表示接近0，黄色部分是负值，越偏白，绝对值越大，偏黑表示表示接近0，以*l*=1，*m*=0为例，北极表示最大的值，南极表示最小的值，赤道黄蓝相接的部分表示0。值的变化的剧烈程度表示频率高低，所以黄色或者蓝色部分的形状越尖，越偏离标准的园，频率越高。

## 使用球谐函数

首先，预滤波+单次查询的效果与不滤波但往各个反射方向多次查询的效果相同

漫反射BRDF的效果与低通滤波器十分类似。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/L3SH.png" alt="Basis" />

漫反射时，任何的光照，只要用3阶的球谐函数描述，就能达到误差很小的效果。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/SHUse.png" alt="Basis" />

球谐函数表示漫反射材质的环境光照着色最终可以化为上面的公式。

但到这里，依然没有环境光的阴影。

# Precompute Radiance Transfer

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/PRT.png" alt="Basis" />

渲染方程中反射部分的3项：光照：环境光照毫无疑问可以用环境光贴图表示，可见项，可以通过着色点，往各个方向测试可见性，可见距离设定一个阈值，大于这个值表示没有遮挡，相反就是被遮挡，也可以得到一张贴图，同理也可以得到BRDF项的贴图，因此三项都可以表示成二维的球面函数。

但是直接这样做消耗很大。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/PRTBI.png" alt="Basis" />

渲染方程中可见项和BRDF项对每个着色点都是固定的(在光照之外其他什么都不变时)，所以可以把渲染方程分成两部分，光照部分和光照传输的部分。

光照部分近似地用一组基函数来表示。然后将光照传输的部分先通过预计算得到并且保存起来。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/DiffuseCase.png" alt="Basis" />

在漫反射的情况下，先将光照部分近似地用一组基函数表示，系数*l*~i~就是光照函数在基函数上的投影，然后将基函数的系数和求和符号放到积分外(转换成先积分后求和，实时渲染里大多数时候不在乎这个顺序，怎么好算怎么来)，这样以后积分部分就自然而然地成为了光照传输部分在基函数上的投影(前面求基函数系数的部分)，所以整个渲染方程都可以预计算得到。

积分部分的预计算可以看作将基函数作为固定的光照去计算得到着色点的值。

这样的话环境光可以发生切换，只要切换过去的光源也已经经过预计算就行，但是光源不能发生连续的变化，或者说光源不能超过预计算能保存的限度

## 基函数

球谐函数有一些优秀的性质

+ 正交：SH的一个基函数投影到另一个基函数上，得到的系数为0。
+ 容易计算投影
+ 容易旋转：我们用SH表示环境光，当环境光发生旋转，我们可以将其转化为SH的基函数的旋转，而SH旋转后的基函数，可以用同阶的其他基函数的线性组合得到。
+ 容易卷积(?)
+ 用很少的基函数表示低频

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/AnotherDiff.png" alt="Basis" />

另外一种分解的方法，那就是将光照和光照传输都使用SH表示。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/AnotherDiffuse.png" alt="Basis" />

于是就得到了上图的的式子，积分内变成了两个基函数的乘积，看似复杂度变高了，但是由于SH的性质，两个不同的基函数是正交的，所以相当于只需要求矩阵的对角线部分，所以复杂度依然相同。

# Glossy Case

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/GlossyCase.png" alt="Basis" />

镜面反射与漫反射的差别就在于BRDF，漫反射的BRDF是常数，而镜面反射的BRDF就与入射角出射角都相关，渲染方程也是真正的四维函数，所以每更换一个入射角，都需要重新计算SH的投影。

所以，先计算关于入射角的SH的投影，再计算出射角的投影，得到系数的矩阵。

最终总的反射radiance的系数用计算光照在SH的投影得到的系数向量与光照传输的系数矩阵相乘得到。

这样做的缺点在于，生成矩阵的要比生成向量计算量大得多，向量和矩阵的乘法也比向量点乘计算量大得多。

由于镜面反射需要更多的高频信号，所以往往需要球谐函数保留更多高阶的基函数。5阶都嫌少。假设在4阶的情况下，漫反射每个着色点需要计算16维向量的点乘，而镜面反射需要计算16维向量和16阶矩阵的乘法。

# 多次反射

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/Bounce.png" alt="Basis" />

右下角是光线传输的正则表达式。从代表光源L出发，到代表眼睛的E，这样表达是传输过程无论多复杂，都可以表示成光照部分和传输部分，PRT就可以用与计算处理。

# 总结

将光照和光线的传输都用SH的基函数近似。

预计算并且存储光线传输。

漫反射是向量的点乘。

镜面反射是向量与矩阵相乘。

缺点：只适合用于表示低频。虽然光源可以是动态的，但是只能用于静态的场景和材质。大量的预计算数据。

# 更多的基函数

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/EnvironmentMapping/Wavelet.png" alt="Basis" />

这里用的是Haar小波函数。

是定义在图中这些方块上的函数。保留了少量的非零系数。

是非线性的映射，因为有些过于小的可以视作0的系数会被抛弃。

可以表示所有的频率。

由于是定义在方块上，所以一般都用cubemap。

过程：将每张图分成四块，将高频信息留在左下、右上、右下，低频信息放在左上。然后不断对左上继续这样的操作。

缺陷：不支持光源快速的旋转。因为Wavelet的基函数不是正交的，光源旋转后就等于做一次新的光源的计算。