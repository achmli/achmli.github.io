---
layout:       post
title:        "Games101笔记10——Pathtracing"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
---



# 蒙特-卡洛积分

Monte-Carlo积分是用来算一些复杂的函数的定积分的方法。

![image-20230628194441261](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628194441261.png)

# 路径追踪

传统的whitted-style RT不适合glossy材质。并且追踪到漫反射平面就停止了。不够全局光照。

![image-20230628202058542](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628202058542.png)

由于在半球面上积分，所以在均匀采样的时候，pdf恒等于1/2pi，毕竟半球面的面积是2pi。

需要随机采样的变量是ωi，因为每次采样的ωi是下一条的ωr，而第一条的ωr是相机与像素的向量，也是固定的，所以ωr实际上是常量。

![image-20230628202911508](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628202911508.png)

这里的伪代码只考虑了直接光照。

## 全局光照

![image-20230628203411985](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628203411985.png)

就加了一行反射的情况，根据采样的入射方向，找到上一次反射的位置，递归地求出这一点的着色，用作入射的radiance。

## 问题

### 问题一

![image-20230628203859712](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628203859712.png)

光线数量太多了，计算不过来。

![image-20230628204029164](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628204029164.png)

只采样一个方向就完事了。。。只采样一条才是路径追踪。

![image-20230628204329219](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628204329219.png)

虽然每条路径每次采样都只取一个方向，但是一个像素可以有多条路径，一条路径上采样多个方向着色会导致计算需求成指数上升，但是一个像素采样多条路径就会是路径数量的倍数。

![image-20230628204703450](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628204703450.png)

### 问题二

递归没有终止条件，算法停不下来。

![image-20230628205038594](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628205038594.png)

定一个概率p，有p的概率有下一跳并获得下一个点的着色Lo，但返回的结果是Lo/p，而1-p的概率没有下一跳，那下一跳的着色就是0 。

而这样获得的期望就是Lo。

![image-20230628205723154](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628205723154.png)

随机生成一个0到1的值，大于俄罗斯轮盘赌的概率就返回0，否则返回的着色除以俄罗斯轮盘赌的概率。

## 提高效率

### 重要性采样

总之就是直接采样光源。

![image-20230628210438943](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628210438943.png)

在光源上采样最大的难点在于将渲染方程的积分从着色点的半球面转换成光源。这样的情况下PDF更好求更直观。

![image-20230628210814032](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628210814032.png)

转换的重点在于找到光源面积的微分dA与单位立体角dω的关系。
通过求dA在半球上的投影求dω。θ‘是采样方向与光源法向量之间的夹角。

![image-20230628210354194](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628210354194.png)

转换后的方程。

![image-20230628211345154](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628211345154.png)

对光源的采样不需要俄罗斯轮盘赌。
对其余的反射则需要。

![image-20230628211529790](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628211529790.png)

### 但是如果光源被阻挡了呢

![image-20230628211715967](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628211715967.png)

# 其他的现代光追

![image-20230628212044060](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628212044060.png)

# 没讲的内容

![image-20230628212240805](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628212240805.png)

![image-20230628212251296](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/10/image-20230628212251296.png)