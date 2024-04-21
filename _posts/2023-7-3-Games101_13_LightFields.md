---
layout:       post
title:        "Games101笔记13——Light fields"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
---



![image-20230701125848246](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701125848246.png)

成像可以用合成或者捕获。

# 视场(FOV)

![image-20230701145705691](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701145705691.png)

## 焦距

![image-20230701145939564](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701145939564.png)

焦距是等效到35mm的胶片时，聚焦的距离，所以**arctan(35/2*焦距)** 就是FoV。

## 传感器大小

![image-20230701150420456](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701150420456.png)

~~底大一级压死人吧~~

# 曝光

![image-20230701150515049](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701150515049.png)

曝光时一定时间积累的Irradiance，考虑到Irradiance是单位时间某个着色点的能量，即某个着色点在某个时刻的光照功率，那么曝光就是某个着色点在一段时间内的光能。

![image-20230701151006505](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701151006505.png)

曝光时间由快门控制。

Irradiance由光圈大小和焦距控制。

感光度：改变传感器的值和数字图像的值之间的放大关系。

![image-20230701151235602](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701151235602.png)

~~ISO听着就像是功放。。。~~

## ISO

![image-20230701151457114](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701151457114.png)

## 光圈

![image-20230701151538767](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701151538767.png)

F数简单理解就是光圈直径的倒数。

~~底大一级压死人好像是说这个？~~

## 快门

![image-20230701151746056](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701151746056.png)

![image-20230701151936272](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701151936272.png)

反走样？

不应该考虑信号处理或者说图像处理？

还是说反走样是从空间采样变成了时间采样？而空间采样的话锤子就变成弯的了？

![image-20230701152315326](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701152315326.png)

~~哦，真是弯的啊~~

![image-20230701152455914](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701152455914.png)

相同的曝光对应的光圈和快门的关系。

~~难不成我在学摄影？~~
~~法国哲学家：对摄影的热爱是对当下的不满。~~

# 薄透镜的近似

焦距是焦点到透镜中心的距离。

![image-20230701153100126](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701153100126.png)

理想的薄透镜：

1. 所有的平行光通过透镜都会聚集到一个焦点上。
2. 所有经过交点的光通过透镜都会变成平行光。
3. 薄透镜的焦距可以任意改变。

# 透镜等式

![image-20230701153434871](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701153434871.png)

*f*是焦距，*z*0是物距，即物体到透镜的垂直距离。*z*i是像距，即最终成像的位置到透镜的垂直距离。

### 景深

![image-20230701154113622](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701154113622.png)

~~CoC是克苏鲁的召唤~~

COC是传感器与透镜的垂直距离大于像距导致成像点投影到传感器成了一个圈，从而模糊了成像点在这个圈内的其他像，因此叫circle of confusion。

CoC大小与光圈成正比。

![image-20230701154750665](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701154750665.png)

看弹幕，ChatGPT翻译成混淆圈。

~~在ChatGPT发布后重温视频还能有新收获，说明Games101确实，啊，常看常新。~~

### F-Number

![image-20230701155037489](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701155037489.png)

F-Number是焦距除以光圈的直径。

![image-20230701155219897](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701155219897.png)

CoC大小的计算。

## 薄透镜下的光线追踪

![image-20230701155451913](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701155451913.png)

感觉。。。。算了，不懂。。。

简单地说，感觉也不是那么用得上的东西。。。

## 景深

![image-20230701155722709](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701155722709.png)

一定深度会有模糊。

![image-20230701155817956](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701155817956.png)

CoC比像素小或者和像素差不多大，就是锐利的。

![image-20230701155914732](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701155914732.png)

求解景深的方法。
~~所以景深就是场景深度啊，这of的习惯对中国人确实，啊，不友好。导致前面一直在想，啊，什么是深度场，想不明白。~~

# 光场

## 全光函数

![image-20230701163434191](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701163434191.png)

![image-20230701163751410](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701163751410.png)

光场就是物体表面各个位置朝各个方向的Radiance。

![image-20230701164143999](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701164143999.png)

光场是四维函数，给出任意方向观察看到的结果。

![image-20230701164447017](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701164447017.png)

光场的参数化。

![image-20230701164628494](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701164628494.png)

## 光场照相机

![image-20230701165112963](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/13/image-20230701165112963.png)

可以先拍照再调焦。

