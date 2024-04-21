---
layout:       post
title:        "Games101笔记08——Radiometry"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
---



# 辐射度量学——概念

光照的衡量方法。

给光各种空间中的属性。

在物理上准确地定义光照地方法。

# 物理量

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/08/image-20230627171112826.png" alt="image-20230627171112826"  />

Radiant Energy：电磁辐射的能量。符号是Q，单位是焦耳。

Radiant Flux：功率，单位时间里光散发，反射，传输或者吸收的能量。 符号是Φ，单位是瓦特，也可以用流明。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/08/image-20230627172207579.png" alt="image-20230627172207579"  />

Radiant Intensity:光源在单位时间内在单位立体角发出的光的能量。相当于单位方向上的光强度/功率。符号是I。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/08/image-20230627172433416.png" alt="image-20230627172433416" />

立体角是角度在三维的延申，立体角的大小是弧面面积/半径的平方，符号是ω。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/08/image-20230627172819942.png" alt="image-20230627172819942"  />

单位立体角(微分立体角)： θ和Φ分别是单位立体角ω与x轴y轴的夹角。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/08/image-20230627173345053.png" alt="image-20230627173345053"  />

各向同性的点光源情况下，总的Intensity和Flux的换算，整个球面的立体角是4*pi。

以及I(ω)=dΦ/dω。

![image-20230627203443244](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/08/image-20230627203443244.png)

Irradiance：单位面积的功率(Flux)(不管是吸收的还是反射的，就是不考虑怎么用，单纯收到的所有能量)

E(x) 恒等于dΦ(x)/dA，单位是W/m^2(或者lux=lm/m^2)。

### Irradiance Fallout

![image-20230627204135584](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/08/image-20230627204135584.png)

### Radiance

![image-20230627204327673](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/08/image-20230627204327673.png)

Radiance：某个单位面积收到来自某个方向的单位立体角的功率(Flux)。即某个方向的单位立体角的Irradiance。或者是某个单位面积收到的Intensity。

符号是L，单位是W/sr m^2(或者nit=lux/sr=cd/m^2)。

### Incident Radiance

![image-20230627204859531](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/08/image-20230627204859531.png)

单位面积里从某个方向到达的功率(Flux)。

### Exiting Radiance

![image-20230627205038448](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/08/image-20230627205038448.png)

单位面积上从某个方向离开的功率(Flux)。

### Irradiance和Radiance对比

![image-20230627205201935](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/08/image-20230627205201935.png)

Irradiance是Radiance的半球面积分。可以说Irradiance是这个点上所有Radiance的总和。

Radiance有明确的方向，Irradiance是所有方向上的总和，所以不考虑方向。

