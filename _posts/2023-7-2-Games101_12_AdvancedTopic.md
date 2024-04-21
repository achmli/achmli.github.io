---
layout:       post
title:        "Games101笔记12——Advanced topics"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
---



# 高级光线传播

## 无偏差的光线传播方法

![image-20230629160523503](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629160523503.png)

蒙特卡洛积分估计出的期望与积分的正确值一致，就是无偏。

其他的情况就是有偏。

有偏的蒙特卡洛积分采样了无限个值后得到正确的结果叫一致。

### 双向路径追踪

![image-20230629160932916](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629160932916.png)

分别从光源和相机出发获得半路径，最终两条半路径的端点在一个点相连获得一条路径，就叫双向路径追踪(BDRT)。

### Metropolis光线传播

![image-20230629161400022](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629161400022.png)

马尔可夫链蒙特卡洛积分的应用
根据当前的样本生成与它靠近的下一个样本。

### 光子映射

![image-20230629162209589](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629162209589.png)

有偏的估计

适合做聚焦

![image-20230629162307127](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629162307127.png)

1. 从光源出发追踪，直到追踪到漫反射表面。
2. 从相机出发，同样追踪到漫反射表面。

![image-20230629162502097](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629162502097.png)

3. 计算局部密度估计：对于任何一个着色点，找到附近最近的n个光子，计算这n个光子所占的面积，n/面积 就是密度了。

光子越多，n越大，质量越好。

光子少，n小，噪声多。光子少，n大，模糊。

### VCM

![image-20230629163133865](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629163133865.png)

结合BDPT和光子映射。

BDPT可能会产生两条半路径的端点不能相连但很接近的情况。利用光子映射将两个点融合/结合在一起。

### 实时辐射度(IR)

![image-20230629163357477](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629163357477.png)

(简写成IR的东西可真多啊，你说是吧，脉冲响应......)

也叫很多光源的方法。

已经被照亮的表面也被视作光源。

首先一个光源射出许多子路径，并且把子路径的终点视为虚拟的点光源。
利用这些虚拟的点光源渲染场景。

# 高级外观建模

## 非表面模型

### 散射介质

![image-20230629164317534](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629164317534.png)

光在传播介质中，可能随机地被吸收或者散射。

![image-20230629164414674](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629164414674.png)

利用相位函数定义光线散射的特性。与BRDF类似，但用于散射。

![image-20230629164604661](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629164604661.png)

### 头发

#### Kajiya-Kay模型

![image-20230629165017762](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629165017762.png)

#### Marschner模型

![image-20230629165034488](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629165034488.png)

![image-20230629165110545](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629165110545.png)

#### 双层圆柱模型(闫模型？)

![image-20230629165534468](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629165534468.png)

![image-20230629165550045](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629165550045.png)

### Granular(颗粒)模型

![image-20230629165914881](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629165914881.png)

## 表面模型

### 类似玉石的半透明材质

![image-20230629170104654](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629170104654.png)

次表面散射

![image-20230629170143425](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629170143425.png)

BSSRDF(有BURDF吗？)

![image-20230629170309260](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629170309260.png)

近似的方法

### 布料

![image-20230629170552296](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629170552296.png)

![image-20230629170904135](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629170904135.png)

当成表面来渲染。

![image-20230629170736334](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629170736334.png)

当成散射介质来渲染。

![image-20230629170841236](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/12/image-20230629170841236.png)

当成纤维来渲染。