---
layout:       post
title:        "Games202笔记04——Global Illumination"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games202
    - 图形学
---



# 实时全局光照

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/GlobalIllumination/SecondarySource.png" alt="SecondarySource" />

被光源直接光照的表面也会扮演光源的作用，我们将它们称为次级光源。所以次级光源照射一个物体才是间接光照，这之后在反射一次就是1跳的间接光照，实时全局光照就是追求简单快速的解决1跳的间接光照。

# Reflective Shadow Map

实时全局光照有两个问题，一是哪些表面直接地被光源照亮，二是所有表面对当前着色点p的影响。

第一个问题可以通过传统的Shadow Map解决。Shadow Map上的每个像素都可以视作是一个表面。

对于任何一个次级光源，在已知观察方向时，可以计算出着色的结果。但是现在我们需要的是在着色点获得的次级光源的出射Radiance，所以观察方向是未知的。

只要假设所有的反射物都是diffuse的就行，无论从camera看过去还是着色点看过去都是一样的。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/GlobalIllumination/SolidAngle.png" alt="SecondarySource" />

第二个问题，所有射向这个表面的单位立体角的radiance的积分，可以转化为单位面积的积分。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/GlobalIllumination/Integrate.png" alt="SecondarySource" />

上半部分就是把各个表面的单位面积的入射光对应的着色点的出射光的Radiance的积分，得到最终的着色的结果，就是渲染方程从单位立体角的积分转化为单位面积的积分。

下半部分就是上半部分公式中*L<sub>i</sub>*项的计算方法，也就是次级光源对当前着色点的入射光，*f<sub>r</sub>*是次级光源的BRDF(我们假设次级光源总是diffuse的)，Φ是功率，单位面积的功率就是irradiance，并且最终代入回上面的式子，可以把微分的dA消去，这样就可以只存储功率，不需要表面的面积。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/GlobalIllumination/NoContribution.png" alt="SecondarySource" />

不是RSM上的每个像素都影响着色点：1. 可见性：不好解决，但毕竟已经是间接光照了，所以影响不大。2. 方向：比如图中桌子上的点只会向上反射，不会影响低于它的着色点。3. 距离：距离远的次级光源影响已经很小，可以忽略，将点投影到Shadow Map，通过对比深度的差距来假定距离的差距。

RSM加速：不去查找Shadow Map上的每一个像素，而是项PCSS一样在一个范围内查找或者采样。

总结：依然是Shadow Map，但是要多存一些东西，除了深度，还有世界坐标、法线、功率。

适合用于手电筒的效果。

优点：易于实现

缺点：性能与直接光源线性相关。没有间接光照可见性测试。做了过多的假设。采样率和质量之间的冲突。

# Light Propagation Volumes(LPV)

间接光照最核心的问题在于当前着色点接收来自各个方向的Radiance是多少。

关键idea：Radiance是沿直线传播并且一次传播中量不会改变。

解决方法：将空间划分为网格，一般将其称为体素(Voxel)，并且用体素来传播次级光源到任意位置的Radiance。

步骤：1.生成次级光源的场景表示。2.将虚拟次级光源“注入”到体素中。3.在网格中传播Radiance。4.用最终传播的体积进行场景光照的渲染。

## 第一步：生成

找出次级光源。

依然是用RSM找出次级光源。同样有多少光源就要多少Shadow Map。

可以采用采样等方法适当减少次级光源的数量。

## 第二步：注入

 将空间划分为3维的网格(工业上一般用纹理来处理，存储点对应的网格)。

找到每个网格中包含的虚拟光源。

将它们的各个方向的Radiance分别相加。

将结果投影到前两阶的SH上。

## 第三步：传播

对于每个网格，收集从它的六个面获得的Radiance。

全部相加，并且再次投影到SH上。

重复这些操作，直到稳定。(一般四五次就能达到稳定)。

## 第四步：渲染

确定着色点所在的网格。

抓取网格中所有方向的incident radiance。

着色。 



缺点，同一个网格中出现遮挡的话，无法处理，可能出现背面被照亮的情况。也有可能传播过程一直稳定不下来。

# Voxel Global Illumination(VXGI)

是一个两趟的算法。

与RSM的区别：1. RSM使用的是次级光源，延申开来讲，也就是每个像素表示的表面，而VXGI使用的是已经离散化表示的网格。2.RSM是在Shadow Map上采样，而VXGI是从camera出发，根据材质，追踪一个圆锥体范围内的Radiance。

第一趟：从光源出发，找到哪些体素被直接照射，并且记录入射的光源和法线的分布。更新分层(类似于八叉树的分层，总之有光照的部分分层肯定要详细一些)

第二趟：如果材质是Glossy的，就沿着反射的cone追溯，每个被覆盖到的voxel都被认为是影响到当前着色点的着色的，voxel根据hierarchy的层级决定大小。对于Diffuse物体，可以从个各个方向追溯圆锥体的范围，最后相加。

# Screen Space Ambient Occlusion

什么是屏幕空间的全局光照：只使用屏幕空间的信息，相当于对屏幕呈现出的图像做一个后期处理。

环境光遮蔽实现起来比较容易，并且能增强物体的相对位置感。

SSAO是对全局光照的一种近似。

关键的假设：1.完全不清楚间接光照，所以假设所有间接光照是一个常数，对任何一个着色点，任意方向，间接光照都是同一个常数。2.但是与blinn-phong的区别在于考虑到了遮挡关系，引入了可见性，对于一个着色点，不是所有方向的间接光照都能照射到。3.假设所有材质都是diffuse的。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/GlobalIllumination/SSAO.png" alt="SecondarySource" />

利用之前的课程中近似的渲染方程，提取出来的是可见性这一项。经过计算可知可见性部分(蓝色框部分)表示的就是一个着色点各个方向可见性的加权平均。由于我们假设间接光照是常数，材质全都是diffuse，所以黄色框部分就是常数。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/GlobalIllumination/Deep1.png" alt="SecondarySource" />

深入理解1：求函数乘积的积分的近似方法，将*f(x)*提取出来相当于在*g(x)*的覆盖范围上求*f(x)*的平均值。对于环境光遮蔽，*g(x)*都是常数，所以这个近似是准确的。

深入理解2：为什么在拆分积分地时候，微分项保留了*cosθ<sub>i</sub>*d*ω<sub>i</sub>*而不是只有d*ω<sub>i</sub>*。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/GlobalIllumination/Deep2.png" alt="SecondarySource" />

d*ω*是单位立体角，立体角在单位球上所占的面积，θ是立体角与地面法线方向的夹角，所以*cosθ*d*ω*就是单位立体角在半球底面的投影。所以积分范围就从单位半球转化到了单位圆。单位立体角投影的积分就等于单位圆的面积。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/GlobalIllumination/SSAO2.png" alt="SecondarySource" />

假设间接光照是常数*L<sub>i</sub>*，假设材质都是diffuse的，所以BRDF项*f<sub>r</sub>*=*ρ/π*，也是常数，最终的方程就如上图所示。

## 实现

传统的AO：对于遮挡的判断限定在一个距离为R的半球里，一般而言这个半球的底面垂直于这个着色点的法向量，R过大，那么所有光都会被遮挡，R过小，那有一些必要的遮挡可能被忽视。在封闭空间效率更高并且效果更好。

SSAO：从观察方向产生场景的深度缓存。在着色点周围半径为R的球内随机采样点，使用深度缓存判断点是否被遮挡，计算出被遮挡的比例，通过被遮挡的比例算出可见性。

事实上与法线相背的方向的半球是不必要的，那里的光照必然被遮挡，但是屏幕空间无法获得法线信息，所以使用完整的球而不是半球，然后只有在看不到的采样点超过采样点的一半时，才考虑AO的问题，并且使用的被遮挡的采样点的数量是被遮挡采样点的数量与全部采样点数量的一半的差。

采样的方法：1.采样越多，越准确。2.但是性能的要求导致一般采样16个点。3.在对AO的结果降噪。

## Horizon Based Ambient Occlusion

同样在屏幕空间进行。

在深度缓存中近似光线追踪。

要求知道着色点的法向量，所以可以只在半球中采样，并且知道法线后，可以对不同的方向通过乘上夹角的余弦值来加权。

# Screen Space Directional Occlusion

是对SSAO的一种提高。

对于SSAO将所有的间接光照都假设为是常数，SSDO认为是没有必要的。

用到的直接光源信息来源于屏幕空间，而不是RSM。

与路径追踪十分相似：在着色点随机射出一条光线，如果与障碍物相交，那么计算间接光照，如果没有，着色点就是接收直接光照。

在思路上甚至与SSAO相反：SSAO被遮挡的方向没有间接光照，不被遮挡的方向接收间接光照。

因为SSAO假设间接光照来自于无限远处，所以近处的障碍使得这部分光被遮挡了，而SSDO的间接光照是近处的障碍的反射。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/GlobalIllumination/SSDO.png" alt="SecondarySource" />

将可见项离散成了两种情况，如果可见，计算直接光照，如果不可见，计算间接光照。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/GlobalIllumination/SSDO2.png" alt="SecondarySource" />

与HBAO类似，在着色点的半球范围内随机采样点，然后从Camera视角判断可见性。

如果可见，计算直接光照，如上图左边情况的c点，沿PC方向查询环境贴图。然后被遮挡的点，找到它们与Camera相连的方向不被遮挡的点，通过点的法线判断能否影响到着色点，如果能影响到，计算间接光照，如中间的图所示。

右边的图展示了出错的情况，PA方向并没有遮挡，但是SSDO会判断出被遮挡，而PB的情况正相反，PB方向的直接光照毫无疑问被遮挡了，但是SSDO会认为没有被阻挡。

SSDO的质量可以接近离线渲染。但是只能表示小范围的全局光照，并且有上面说的可见性问题，而且作为屏幕空间算法，丢失了屏幕外看不见的信息。

# Screen Space Reflection

在屏幕空间做光线追踪。

但是不需要3D多边形。

基本任务：任意光线和场景的求交。相交的像素对着色点的影响。

## 基本的SSR算法——镜面反射

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/GlobalIllumination/SSR.png" alt="SecondarySource" />

计算反射的光线，利用深度缓存追踪光线方向，用相交的点的颜色作为反射光的颜色。

说是镜面反射，但是根据材质，可以采样不同数量的光线以实现不同材质的效果。

## ray march

怎么利用深度缓存获取相交的信息呢。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/GlobalIllumination/RayMarch.png" alt="SecondarySource" />

沿着反射方向每次前进一定距离，然后从camera看向当前点所在位置，比较深度缓存的深度，如果深度小于深度缓存，继续前进，直到camera看向当前的位置会被遮挡(然后使用这个方向的像素作为颜色？)。

但是每次前进的步长怎么确定呢。

首先生成深度图的MipMap，但是生成下一层的一个像素不再是当前层4个像素的平均值，而是它们当中的最小值。

这样做就是类似于BVH或者KD树这样的加速结构。

假如当前的步长前进后不会与深度最小的像素相交，那就不会和这个像素包含的其他的深度更深的像素相交。如果相交了，再去MipMap中找分辨率更高的层，与四个像素做相交的判断，就这样下去，可以跳过很多完全不可能相交的像素的相交判断。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/GlobalIllumination/Step.png" alt="SecondarySource" />

具体实现时，先用小步长，不相交的话慢慢增大步长，如果相交了，再逐渐减小步长，直到确定像素。

SSR依然时屏幕空间，会丢失看不到的信息。其他都很好，毕竟光线追踪就是物理正确的。

## 着色

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/GlobalIllumination/Shade.png" alt="SecondarySource" />

着色上与路径追踪没有区别。

优点：镜面反射和光泽度比较高的反射下，性能很好。质量好，毕竟光追是物理正确的。很自然地生成阴影。

缺点：漫反射材质比较慢(但现在有解决的方法)，屏幕空间丢失信息。
