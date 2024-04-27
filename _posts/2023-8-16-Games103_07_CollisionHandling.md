---
layout:       post
title:        "Games103笔记07——Collision Handling"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games103
    - 图形学
    - 物理模拟
---



# 碰撞检测

![image-20230725174545598](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/Pipeline.png)

碰撞检测的管线。

分为两步，第一步是广义的碰撞删除(culling)，第二步是狭义的碰撞测试。

那首先看到culling就想到face culling，既然face culling是渲染时删掉背面的面，那collision culling想必就是删掉没有必要的碰撞检测了。(而且光追里BVH也差不多是这个功能，先和大的包围盒求交，相交后再与包围盒下的子节点(小的包围盒)求交，减少计算量)(空间划分也是一样，不过BVH是把三角形划分，空间划分是划分空间，可能一个三角形会在多个划分后的空间里，光追里一般说八叉树、KD树，但是感觉不如BVH。。。用得多)。或者说粗略地去除掉不会碰撞地pairs(所以是三角形和三角形，或者点和点的碰撞，而不是宏观的物体和墙)。

然后Narrow-Phase Collision Test就是检测刷选后留下的pair是否有碰撞。

最后把碰撞的pairs输出。

## Spatial Partition(空间划分)

![image-20230725192410376](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/SpatialPartition.png)

空间划分是指将空间划分成网格，并且把三角形存储在网格中。比如t<sub>0</sub>同时存储在0，4，5号网格中。

然后判断三角形是否有可能碰撞，只需要检测三角形所在网格中是否存储了其他三角形。

![image-20230725193224875](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/SpatialPartition2.png)

运动的三角形就存储在运动过程中会经过的网格中。

![image-20230725194049549](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/SpatialPartition3.png)

在三维空间中，存储时会需要非常多的网格。并且空间划分的网格大小很难找到合适的，会出现一些网格中存了大量的三角形，同时有很多网格中一个三角形都没存，这种情况极大地浪费了内存。

不对网格分配内存，而是将三角形和它多所在的网格存成一对。比如将t<sub>0</sub>存储成{0,0},{4,0},{5,0}三个数对。然后将这些数对按网格编号排序，这样就能很快找到同网格中的三角形。这样没有存储三角形的网格就不会占用内存了。

![image-20230725200829945](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/MortonCode.png)

定义网格编号的方法。

## BVH

![image-20230725201524974](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/BVH.png)

简而言之，大盒子包小盒子，小盒子是大盒子的子节点。

![image-20230725202805958](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/BVH2.png)

判断碰撞的过程与光线追踪的BVH类似，先与大的包围盒求交，在与子节点的小包围盒求交。

但听描述，感觉上构造包围盒的过程是与光线追踪相反的。这里是找到每个物体的包围盒，再把相近的合并成大的包围盒。而光追里是线把所有三角形包围在一个大盒子中，，然后找到最中间的三角形来划分BVH。

![image-20230725203925627](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/BVH3.png)

BVH内的自相交。

先递归的检测子节点内是否有自相交。

然后再检测几个子节点之间是否相交。

而判断子节点之间是否相交，先判断两个包围盒之间是否相交，如果相交，在递归地去判断它们的子节点是否相交。

![image-20230725211755958](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/Paper.png)

在绝大多数情况下能有效剔除相距较远的那些三角形。

但是三角形附近地碰撞就很难剔除。

![image-20230725212346711](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/Comparison.png)

+ <strong>空间划分</strong>
  + 容易实现
  + 对GPU友好
  + 每次物体运动都需要重新计算。
+ <strong>BVH</strong>
  + 更复杂
  + 对GPU不友好，毕竟GLSL不能递归
  + 更新时只需要更新包围盒

## 离散碰撞检测

![image-20230725213004703](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/DCD.png)

DCD判断每个离散时间是否有相交发生。

对于三角形网格检测边和三角形是否相交。怎么检测，MT算法！

![image-20230725213707812](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/Tunneling.png)

相交检测可能会发生图中的情况。检测不到穿透。

## 持续碰撞检测

![image-20230725214428208](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/CCD.png)

检测在两个离散的时间之间是否相交。

对于三角形网格，检测顶点和三角形的相交以及边和边的相交，因为可能会发生点和三角形不相交但边和边相加的情况。

顶点和三角形检测，求出四个顶点在一个平面上的时候的时间。

图中第一步是就是计算在同一个平面的时间。

然后第二步看是不是在三角形内。

![image-20230725215805836](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/CCD2.png)

边和边的检测与点和三角形是类似的，因为都是四个点。

![image-20230725221215489](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/Issues.png)

<strong>CCD的问题</strong>

+ <strong>浮点精度的问题。</strong>
  + 可以放大区间，不需要绝对准确。
  + 游戏GPU以单精度为主
+ <strong>花费比DCD更大。</strong>
  + 但是有观点认为碰撞剔除才是最消耗算力的，是瓶颈，所以DCD还是CCD无所谓。
+ 实现有难度。

# Interior Point Method(内点法) 和 Impact Zone Optimization(撞击区法)

![image-20230725222349334](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/TwoWay.png)

<strong>x</strong><sup>[0]</sup>是初始位置，<strong>x</strong><sup>[1]</sup>是计算出来下一时刻的位置，蓝色区域内不会发生碰撞，所以需要将<strong>x</strong><sup>[1]</sup>更新到$\mathbf{\overline{x}}^{[1]}$来避免相交。

内点法：从<strong>x</strong><sup>[0]</sup>出发，向<strong>x</strong><sup>[1]</sup>方向运动，但一直保持在不会相交的区域内，直到离<strong>x</strong><sup>[1]</sup>最近的位置。

碰撞区法：从结果出发，反复地优化，最终直到在安全的区域内。

![image-20230725223617351](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/ProCon.png)

优缺点对比。

![image-20230725223904938](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/PointMethods.png)

通过两个点距离的对数给点施加能量，点就获得互斥的力。

![image-20230725224218869](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/InteriorPointMethods.png)

实现。

实际上还是优化问题，通过梯度下降实现。

碰撞区没有讲。

![image-20230725224752545](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/PracticalSystem.png)

# 相交解除

![image-20230725224829151](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/IntersectionElimination.png)

总之就是相交本身并不是灾难，有相交了，再去消除它。

![image-20230725225151038](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/IntersectionElimination2.png)

对于有体积的物体，只要将物体推出去就行了。

对于布料，就不能这样处理了，因为布没有内外。

![image-20230725225333395](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/Cloth.png)

利用相交，将布分段，上图就是分成了三段。

比较段的大小，最小的一段就是相交了。

不能很好地解决边界。

![image-20230725225926533](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games103/07/UntanglingCloth.png)

改良：让相交的曲线变短。