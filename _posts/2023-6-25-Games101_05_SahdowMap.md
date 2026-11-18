---
layout:       post
title:        "Games101笔记05——Shadow Map"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
series: "Games101"
series_order: 5
topic: "阴影"
---
# Shadow Mapping

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/05/image-20230625165952619.png" alt="image-20230625165952619" style="zoom:100%;" />

Shadow Mapping 可以用于方向光、聚光灯和点光源。全向点光源一般需要覆盖多个方向的深度图。

## 从光源渲染

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/05/image-20230625170350646.png" alt="image-20230625170350646" style="zoom:100%;" />

从光源看向场景，记录下每个像素的深度。

# 从相机渲染

![image-20230625170450732](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/05/image-20230625170450732.png)

将相机能看到的点投影回光源，可以了解点对应在上一步生成的深度图中的哪个像素。

比较当前点的光源空间深度和深度图记录的最前表面深度。在常规的深度约定下，前者超过后者加上偏移量时，当前点才处在阴影中。

# 缺点

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/05/image-20230625171457418.png" alt="image-20230625171457418" style="zoom:100%;" />
