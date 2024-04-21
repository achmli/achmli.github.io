---
layout:       post
title:        "Games101笔记06——Raytracing Pt.1"
author:       "Fon"
header-style: text
catalog:      true
tags:

   - Games101
     - 图形学
---



# 基础光线追踪算法

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230626212531239-2.png" alt="image-20230626212531239"  />

从相机追踪到一个像素，如果有物体，则追溯到光源，已验证是否有阴影。

## 递归(whitted)光线追踪

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230626213122580.png" alt="image-20230626213122580"  />

光线在经过折射和反射后与物体的焦点依然要判断光源的可见性。

## 光线和物体表面的相互

光线：光源(vec3),方向(vec3)

###  球

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230626213656519.png" alt="image-20230626213656519"  />

### 其他隐式表面

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230626214049156.png" alt="image-20230626214049156"  />

### 平面

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230626215047697-2.png" alt="image-20230626215047697"  />

平面可以用一条法线和平面内任意一点定义。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230626215502683-2.png" alt="image-20230626215502683"  />

通过重心坐标，使用平面上三个点，解线性方程组。可以获得t，b1，b2的值，进一步计算出交点坐标。

### 三角形

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230626214442138-2.png" alt="image-20230626214442138"  />

三角形刚好有三个顶点，可以通过求平面交点的MT算法求三角形所在平面的交点。重心坐标b1，b2和1-b1-b2如果存在至少一项小于0，则交点就不在三角形内。

# 加速光线和表面求交

## 包围盒

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230626220429196.png" alt="image-20230626220429196"  />

将物体用包围盒包裹，先与包围盒求交，如果相交，在于物体的三角形面求交。

### 包围盒与光线求交

一般使用AABB包围盒，因为AABB包围盒的面都与坐标轴平行或者正交。所以对光线而言，三维向量也只需要考虑其中一个变量，相当于线性方程。以平行于yz轴的平面的面为例，只需要考虑x方向即可

平面的x减去光源的x除以归一化的方向的x就是相交的时间了，非常简单。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230626220955478.png" alt="image-20230626220955478"  />

首先与平面求交，成组，六个平面分成三组，平行的面为一组。光线分别与每组平面求交，计算出相交的时间t，较小的t是进入两个平面中间的空间的时间，较大的是离开的时间。
三个进入时间中取最大值，离开时间中取最小值，如果光线与包围盒相交，这分别是光线进入包围盒的时间和离开包围盒的时间。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230626220938649.png" alt="image-20230626220938649"  />

由于包围盒的空间是三组平面之间的空间的交集，所以如果不相交，就必然是三组平面依次依次与光线相交，而不是先与一组中的一个平面相交，然后再与另一组中的一个平面相交，再与下个平面相交才进入包围盒，然后与第三组中另一个平面相交离开包围盒，与第二组平面相交，最后与第一组相交。
所以如果不相交，我们获得的光线进入包围盒时间会晚于出包围盒的时间。以此来判断，光线是否与包围盒相交。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230626222644654-2.png" alt="image-20230626222644654"  />

离开包围盒时间小于0：不相交，包围盒在光线方向的背面。

离开时间大于0且进入时间大于0：相交，光线起点在包围盒内。

### 相交的条件

进入时间<离开时间 且 离开时间为正。

## 包围盒加速

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230627115505840.png" alt="image-20230627115505840"  />

1. 给整个场景建立包围盒
2. 创建网格
3. 标记和物体表面相交的格子。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230627121218036.png" alt="image-20230627121218036"  />

光线穿过网格，与相交的网格中的物体表面求交。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230627122131080.png" alt="image-20230627122131080"  />

网格太稀疏会导致没怎么优化。

网格太密集会浪费太多计算在光线与网格的求交上。

经验性的结论：网格数量=27*物体数量。

## 空间划分

### 八叉树

将空间分成八份，如果某几块中依然有较多物体，就将这些快继续划分，知道，块中物体足够少或者为空。

### BSP-树

不沿着坐标轴划分的KD-Tree，所以其实不太好用。

### KD-树

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230627123248882.png" alt="image-20230627123248882"  />

本质上是二叉树，先把空间分成包含物体很少和包含物体较多两块，然后如果划分后依然包含较多的物体，继续这样划分，直到最后两块包含的物体都较少。

划分的方向要有规律，一般是先沿着x轴方向，然后y轴方向，再z轴方向，之后重复直到划分完成。

并不是如图中这样只划分包含物体较多的一边，二叉树的两个子节点都可以继续划分。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230627124322711.png" alt="image-20230627124322711"  />

#### KD树数据结构

##### 内部节点存储：

+ 划分方向
+ 划分位置：与划分的平面正交的方向的值。
+ 子节点

内部节点不存储物体

##### 叶子节点存储：

物体的列表。

### KD树求交过程

首先和根节点求交，如果相交，则继续依次与子节点求交，如果子节点是叶子节点，则与节点中所有物体求交。

## 物体划分和BVH

由于划分后的空间可能导致物体被多个空间存储，并且判定物体与划分的空间相交亦有难度，所以就有了与划分空间思路相对的划分物体。

### BVH

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230627130240606.png" alt="image-20230627130240606"  />

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230627130812074-2.png" alt="image-20230627130812074"  />

第一步，建立包围所有物体的包围盒，作为根节点。

第二部，把包围盒划分为较为均衡，重叠较少的两部分，重叠是指空间上的重叠，实际物体并不能被两个子树同时存储。

然后，重复第二部，知道划分相对完善。

### 划分技巧

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230627130904403.png" alt="image-20230627130904403"  />

+ 像KD树一样依次沿着某个方向划分。
+ 沿着与最长的轴正交的方向划分。
+ 选择中间的物体划分：利用三角形的重心，沿着某个方向排序，找到第n/2个三角形，划分，利用快速划分算法，可以在O(n)时间内找到第n/2个三角形。

一般而言，节点中的三角形数量小于等于 5 时就停止划分。

### BVH的数据结构

#### 内部节点：

+ 包围盒
+ 子节点

#### 叶子节点：

+ 包围盒
+ 物体的列表

### 求交过程

![image-20230627131946591](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/06/image-20230627131946591.png)

```
Intersect(Ray ray, BVH node) {
 if (ray misses node.bbox) return;
 if (node is a leaf node)
 test intersection with all objs;
 return closest intersection;
 hit1 = Intersect(ray, node.child1);
 hit2 = Intersect(ray, node.child2);
 return the closer of hit1, hit2;
}
```

