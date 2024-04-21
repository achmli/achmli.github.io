---
layout:       post
title:        "Games202笔记06——Real-Time Ray Tracing"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games202
    - 图形学
---

RTX做了什么？

每秒钟10G的光线，但是每个像素依然只可以采样一条光路。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/RayTracing/SPP.png" alt="SPP" />

首先定义一下光路(SPP)：光线追踪第一步是向每个着色点发出一条光线，和光栅化几乎是一样的，所以用光栅化替代首要光线，由于是传统光追，所以要测试可见性，一个SPP就是首要光线+次要光线+首要光线交点的可见性测试光线+次要光线交点的可见性测试光线。

只用1SPP意味着会有很多的噪声。所以实时光线追踪最重要的内容就是降噪。

降噪的目标：1.高质量(没有overblur，没有artifact)。2.要快。

用传统的降噪方法几乎是不可能的。

所以时间上的滤波是目前最好的解决方法。

关键思路：假设前一帧已经完成降噪了所以可以重复利用，使用运动矢量找出当前像素在前一帧的位置，这样就在事实上增加了SPP。

# G-Buffer

几何缓冲。

用于存储几何信息。一般是延迟渲染存储每个像素的深度、世界坐标、法线和材质信息。一般是在延迟渲染，所以是深度最浅的像素，可以看作是屏幕空间。

# Back Projection

找出当前帧某个像素所代表的在场景中的点在上一帧所在的像素。

步骤：如果像素所代表的点的世界坐标已经保存在G-Buffer里了，那就直接拿出来用。如果没有，就经过一系列变换(从世界坐标投影到屏幕空间的变换是已知的，反过来经过逆变换就能得到世界坐标)得到。因为我们拥有整个渲染的过程，因此也必然知道上一帧经过什么变换从而能渲染这一帧，所以利用这个变换的逆变换就可以通过这一帧的坐标计算出上一帧的位置。最后讲上一帧的位置再经过MVPE(E是视口变换)投影到屏幕空间，得到上一帧这个点所在的像素。

# 色彩混合

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/RayTracing/Temporal.png" alt="SPP" />

先对当前帧做一次空间上的滤波，然后在与上一帧找到的对应的像素做一个线性混合，并且上一帧的颜色占绝大部分(80%~ 90%，也就是α在0.1~0.2)。

# Temporal Failure

有几种失败的情况：1.场景的变化。2.在走廊里向后走(屏幕空间的问题：会有越来越多的信息)。3.被遮挡的背景突然出现(不再被遮挡)，容易出现拖影。4.即使没有几何信息发生变化时，光源的移动造成的阴影变化依然可能出现拖影，或者反射出来的信息也会与物体的移动不同步。

调整方法：1.将上一帧的颜色尽可能地变得和当前帧相似：clamp函数，给上一帧与这一帧地差别规定一个上下限。2.检测：用一个object ID来分辨这一帧的像素表示的物体和上一帧找的像素找到的物体是否是同一个，如果不是同一个，调整alpha的值，或者干脆不适用上一帧的信息，也可以加强空间上的滤波。

# 滤波的实现

滤波(通常是低通)的目标：过滤掉(通常是高频的)噪声，这一部分是只在空域上滤波。

输入是一张充满噪声的图片和一个滤波核来改变每个像素。输出一张滤波后的图像。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/RayTracing/Gaussian.png" alt="SPP" />

最常见的滤波核大概就是高斯滤波了，像素i周围的每个像素都会参与到滤波中，影响的大小取决于两个像素的距离。

下半部分是滤波的伪代码，就是一个加权平均数的计算。

用一些其他的滤波核时在最后求平均是要判断总权重是否为0。

## 双边滤波

高斯滤波的缺陷：会模糊掉类似于边界这种我们想要保留的高频信息。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/RayTracing/Bilateral.png" alt="SPP" />

边界就是颜色剧烈的改变。

双边滤波的核心思想：周围的某个像素j是否和要滤波的像素i的差异特别大，如果特别大就不用这个像素了。

PPT底部时双边滤波的滤波核，i和j时当前滤波的像素的坐标，k和l时周围的某个像素的坐标，颜色差别越大，对滤波的影响越小。图中是指数函数，实际就是两个函数相乘，影响大小取决于各自σ的大小。

## 联合双边滤波

高斯滤波用距离作为标准来判断一个像素在滤波中的影响。

而双边滤波引入了色彩间的差异作为另一个标准。

而联合双边滤波引入了更多的特征作为标准，而且联合双边滤波十分适合给光线追踪生成的图像降噪。

渲染使用联合双边滤波的优势：G-Buffer里保存了每个像素的许多特征，而且G-Buffer里保存的内容是没有噪声的(毕竟保存的几何信息，没有经过渲染)。

联合双边滤波也不需要计算周围每个像素的时候都归一化一下，毕竟最后相加的值除以一个总的权重就完事了。

滤波核也不是非得是高斯滤波核，只要影响大小随着距离增大减小就行。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/RayTracing/Joint.png" alt="SPP" />

假设G-Buffer中存储了深度、法线和颜色。

在做联合双边滤波时，除了像素间的距离，计算A的颜色时，通过深度的“距离”减小B的影响。计算B时，通过法线的“距离”减小C的影响，而D和E之间颜色的“距离”比较大，通过颜色相互之间最终结果的影响就减小。

# 大滤波核的实现

滤波的算法要循环N*N次，在N还算小的时候，性能还说得过去，但是N很大时，完成一幅图像的滤波就会很慢。

## Separate Passes

将一幅图像水平地滤波，然后再做一次竖直的滤波。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/RayTracing/Separate.png" alt="SPP" />

为什么能这么做？

因为2维的高斯函数可以被分解为垂直的一维高斯函数和水平的一维高斯函数的乘积。

由于滤波=卷积。所以就是二重积分的一种计算方法。对x积分时与y无关(反过来也一样)，所以可以对积分的顺序做出调整(但是，高数已经忘得差不多了)。

但是Separate Passes要求滤波核可拆分。(双边滤波核理论上就不能拆分，但是实际使用时，只要滤波核没有过分的大，都可以强行拆分成水平和垂直两趟)。

## Progressively Growth

用不同大小的滤波核滤波多次。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/RayTracing/Growth.png" alt="SPP" />

图中是一种叫a-trous wavelet的滤波方法。

每一次滤波都是5*5的滤波核。但每次滤波都会增加采样的像素之间的间隔。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/RayTracing/PGS.png" alt="SPP" />

更大的滤波核意味着去除更低的频率。

采样相当于复制一部分的频谱。

第一次滤波时，就已经把最高频的信息去除了。而第二趟在更大的范围内用了与第一趟采样相同的频率，相当于把低频部分的信号搬移到了被第一趟过滤掉的高频部分。之后的第三趟第四趟也是这个道理。

缺点是：用双边滤波或者联合双边滤波这些方式滤波后会保留一部分高频信息，导致这样处理后高频会有混叠，可能会出现一些格子状的Artifact。

# Outlier Removal(离群值移除)

滤波不是全能的：滤波后可能依然有很多噪声，甚至扩散成了一块，基本上都是因为过于亮的噪声。

所以要把这些点在滤波前就移除。

outlier detection：对每个像素，扫描它周围7*7的区域，计算出均值μ和方差σ。如果像素的值不在 [ μ-kσ,μ+kσ ]范围内，那就认为它是outlier(k是一个常数，一般取1~3)。

然后把这个像素的值clamp到 [ μ-kσ,μ+kσ ]这个范围。

Temporal滤波时两个像素颜色差别过大时，上一帧的像素也先用这个方法clamp后再混合，均值和方差是用当前帧计算的。

# Spatiotemporal Variance-Guided Filtering

与普通的时间-空间滤波方法大同小异。

但有一些附加的方差计算和一些小技巧。

用三个因素去指导滤波。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/RayTracing/Depth.png" alt="SPP" />

深度：是一个指数函数，不是高斯函数。分母中的ε是防止分母为0。A、B在同一平面，并且颜色相近，所以它们之间的滤波应当对彼此有较大的影响。但是这两个点的深度差值较大，可能影响就会减小。所以考虑它们在法线方向上的深度变化。具体实现是在分母中包含计算的点的深度的梯度与两个点距离的乘积，得到的是垂直法线方向的深度变化，可以解决图中的情况。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/RayTracing/Normal.png" alt="SPP" />

法线：同样不是高斯函数，通过计算法线之间的点乘来计算法线的距离的影响，σ主要控制法线间的夹角对最后结果影响的程度。即使使用了法线贴图，在这里计算时也不使用法线贴图储存的偏移量。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/RayTracing/Color.png" alt="SPP" />

求颜色的差异时，如果计算的点刚好是噪声，那就会造成偏差。所以在分母中包含了计算的点与周围的一系列点的方差，如果方差较大，就能减小这个点最终的影响。

方差的计算方法：先计算7 * 7范围内的方差，同时利用temporal的一些方法，记录下时域上这个范围的方差的平均值，最后对这个方差做一个3 * 3的滤波。

# RAE

基本思想：利用Recurrent去噪自动编码器对蒙特卡罗图像序列的交互式重构。

输入是蒙特卡洛路径追踪得到的充满噪声的图片和G-Buffer，利用神经网络自动完成时域上的积累。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/RayTracing/RAE.png" alt="SPP" />

关键的架构设计：自动解码器的结构、recurrent卷积块(recurrent指每一层神经网络不止连向下一层，也连向自己)

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/RayTracing/Comparison.png" alt="SPP" />

两种滤波方式的对比。