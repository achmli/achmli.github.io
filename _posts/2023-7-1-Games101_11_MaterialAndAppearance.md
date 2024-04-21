---
layout:       post
title:        "Games101笔记11——Materials and Appearance"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
---



# 材质

![image-20230629135211266](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629135211266.png)

材质就是BRDF。

## 漫反射材质

![image-20230629135304359](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629135304359.png)

假设所有方向的入射光的radiance相同，那么Li与入射的单位立体角无关，是常量，漫反射的BRDF也是常量。

cosθ的半球面积分等于pi。

在材质不吸收光的假设下，Li是和Lo相等的(毕竟假设所有方向的入射光的radiance相同)，那么fr就等于1/pi。
但是一般而言，材质都会吸收光，所以就会有反射率ρ，所以最终漫反射材质的BRDF为fr=ρ/pi。

## Glossy材质

![image-20230629141436934](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629141436934.png)

## 玻璃/水

![image-20230629141511640](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629141511640.png)

### 全镜面反射

![image-20230629141652857](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629141652857.png)

### 折射

![image-20230629142405929](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629142405929.png)

方位角与反射相同。

入射材质的折射率与入射角的正弦值的乘积等于出射材质的折射率与出射角的正弦值的乘积。

![image-20230629142426193](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629142426193.png)

由于求余弦需要开方，所以只要能求出实数的余弦值，折射就能发生，假如没有实数解，那么就是全反射，没有折射。所以求余弦是更简便的选项。

### BSDF

BSDF=BRDF(反射)+BTDF(折射)。

## 菲涅尔项(Fresnel Term)

![image-20230629143916624](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629143916624.png)

一般使用Schlicks‘s approximation。

## 微表面材质

![image-20230629144557465](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629144557465.png)

相当于把平面放到显微镜下放大，看到凹凸不平的表面，而这些表面法线分布的不同导致在宏观上感受到的材质的不同。

## 微表面BRDF

![image-20230629145033510](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629145033510.png)

菲涅尔项表示不同的入射方向有不同程度的反射。

法线分布表示能将入射方向的光反射到特定出射方向的微平面占所有微平面的比例。也即法向量与半程向量相同的微平面占所有微平面的比例。

阴影掩盖项(几何项)：微平面之间可能会有互相遮挡，因此有一部分微表面的反射光可能被遮挡从而失去作用。

## 各向同性/各向异性材质

![image-20230629152756557](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629152756557.png)

各向同性：微表面法线方向不能存在明显规律，积分上均匀随机分布

各向异性：微表面具有明确的方向性。

### brdf

![image-20230629153002691](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629153002691.png)

相同的材质，在确定入射光和出射光的夹角后，不同方向的入射光和折射方向的brdf不同，这就是各向异性材质。

各向异性的材质的BRDF不止与入射方向和出射方向的相对夹角有关，也与入射方向和出射方向本身的值有关。

## BRDF的属性

![image-20230629154037942](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629154037942.png)

+ BRDF的值是非负的
+ BRDF是线性的：可以把BRDF分成许多块，最终结果相加依然是正确的

![image-20230629154110957](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629154110957.png)

+ BRDF是可逆的：交换入射方向和初设方向结果是相同的
+ 能量守恒：BRDF不会让光照变强。

![image-20230629154204271](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629154204271.png)

+ 各向同性和各向异性

## 测量BRDF

![image-20230629154404478](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/11/image-20230629154404478.png)