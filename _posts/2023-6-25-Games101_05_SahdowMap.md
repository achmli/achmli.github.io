---
layout:       post
title:        "Games101笔记05——ShaowMap"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
---
# Shadow Mapping

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/05/image-20230625165952619.png" alt="image-20230625165952619" style="zoom:100%;" />

 Shadow Mapping只能处理点光源。

## 从光源渲染

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/05/image-20230625170350646.png" alt="image-20230625170350646" style="zoom:100%;" />

从光源看向场景，记录下每个像素的深度。

# 从相机渲染

![image-20230625170450732](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/05/image-20230625170450732.png)

将相机能看到的点投影回光源，可以了解点对应在上一步生成的深度图中的哪个像素。

对比点的深度和深度图的深度，如果相等，则不在阴影中，深度不同，则光源被阻挡，在阴影中。

# 缺点

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/05/image-20230625171457418.png" alt="image-20230625171457418" style="zoom:100%;" />
