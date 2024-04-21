---
layout:       post
title:        "Games101笔记07——Raytrcing Pt.2"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
---

# BRDF(双向反射分布函数)

![image-20230627210401719](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/07/image-20230627210401719.png)

不得不说，想了快5分钟才把这页想得差不多明白。

首先ωi是入射方向(的单位立体角)，ωr就是出射方向了。
同时微分的入射的Irradiance的计算应该是由Radiance的定义反推求得。
而出射方向Radiance也是微分是因为这是ωi一个方向的Irradiance所求得的Radiance，还有其他方向的，所以是微分。

![image-20230627211817775](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/07/image-20230627211817775.png)

BRDF代表了从入射方向ωi来的光会有多少从出射方向ωr反射出去。
Φi和Φr分别代表x轴与ωi和ωr在xOz平面的投影的夹角。
θi和θr分别代表y轴与ωi和ωr的夹角。

### 反射方程

![image-20230627212804121](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/07/image-20230627212804121.png)

所有方向入射光的Radiance(即Irradiance)与BRDF的乘积的积分就是这个反射方向的Radiance。

![image-20230627213339177](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/07/image-20230627213339177.png)

但是一个的出射的Radiance也会成为其他点的入射的Radiance。所以一般需要递归定义。

## 渲染方程

![image-20230627213535262](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/07/image-20230627213535262.png)

所以，渲染方程就是像素自己发出的光加上反射方程。

![image-20230627214649907](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/07/image-20230627214649907.png)

相对简单的表达方式。

![image-20230627214804504](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/07/image-20230627214804504.png)

简化成线性方程。

![image-20230627214955022](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/07/image-20230627214955022.png)

最终就实现了对方程的求解。

### 非递归解

![image-20230627215130274](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/07/image-20230627215130274.png)

光栅化适合用来实现直接光照。

## 全局光照

渲染方程最终的解就是全局光照了。