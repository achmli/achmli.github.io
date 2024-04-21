---
layout:       post
title:        "Games202笔记07——Industry"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games202
    - 图形学
---



# 抗锯齿

## TAA

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/Industry/TAA.png" alt="TAA" />

重复利用上一帧对应像素的值来给当前帧做抗锯齿。和Temporal降噪几乎是一样的。

对之前的帧的像素的采样位置会发生改变。比如图中，这一帧采样像素的左上角，上一帧可能是右上角，再上一帧可能是右下角，而下一帧就是左下角。用这样的一个模式去采样几个固定的点。

## AA

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/Industry/MSAA.png" alt="TAA" />

SSAA和MSAA的差别：SSAA先超采样渲染，最后再降采样到输出的分辨率。MSAA同一个多边形只着色一次。上图左上角的一个像素中有两个多边形，并且对四个位置编号，SSAA就要四个位置都着色一次，而MSAA只着色两次。MSAA还会对采样复用，上图左下角，两个相邻像素不仅在内部有采样，在边界上也有采样，在效果上使得每个像素的采样数翻倍了，但是总的采样数却没有翻倍。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/Industry/FXAA.png" alt="TAA" />

左上角就是MLAA的算法，先是渲染出来的图像(1)，用一些匹配的算法找出想要的边(2)，(3)是最理想的情况，但是是不可能实现的，最后计算出每个像素应该的颜色写入(4)。

G-Buffer不能反走样。因为我们要G-Buffer里的像素具体的指向某个某个物体，它保存的几何信息才有意义。反走样事实上是场景中不同物体的属性插值，那就保存不了这个像素深度最浅的物体的准确的几何信息了。

# 超分辨率/超采样

这里似乎只讲了DLSS。

DLSS 1.0：几乎完全靠深度学习去猜多出来的像素的值。

DLSS 2.0：利用时域上的信息去推测。

## DLSS 2.0

DLSS 2.0使用的temporal的技术与之前讲的最重要的差别在于，失败的情况不能再依赖clamp。

如果继续用clamp，那就意味着使用周围的像素的值来得到新生成的像素，新生成的像素会与周围的像素过于接近，导致最后的结果很糊。

因此关键是怎么更加“聪明”地使用时域上地信息。

而DLSS 2.0中的深度学习也主要用来处理“怎么更合理地使用之前的帧的信息”这个问题。

实践的问题：必须要快。所以优化神经网络的推理性能十分重要。

DLSS的竞争对手：AMD的FSR，Facebook的Neural Supersampling for Real-time Rendering

# 延迟渲染

节省Shading的时间

传统的渲染管线中渲染的很多fragment最终根本不会被看到。

延迟渲染的目的就是只渲染看得见的片段。

延迟渲染的渲染流程：

做两遍光栅化：第一趟不做着色，只更新深度缓冲。第二趟就可以只对哪些深度与深度缓冲中相同的像素做着色。

这说明光栅化的开销小于对所有看不见的片段做着色的开销。

缺陷:做不了抗锯齿(其实只是MSAA做不了)。渲染不了透明物体。

## Tiled Shading

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/Industry/Tile.png" alt="TAA" />

延迟渲染减少了要渲染的片段数量，而我们想要更进一步，减少渲染的光源的数量。

将屏幕细分为例如32x32的Tile，然后为每个Tile添加着色

核心思路：不是所有光源都照到了特定的某个Tile。主要是由于随距离的平方衰减

认为每个光源影响范围都是一个球形，所以每个光源渲染时只需要考虑能被它影响到的Tile就行。

## Clustered Shading

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/Industry/Cluster.png" alt="TAA" />

进一步对Tile划分。

对Tile有影响不代表对Tile的每个段都影响。

所以每个光源渲染时只需要考虑能被它影响到的Segment就行。

# Level of Detail Solutions

类似于MIPMAP，选择要使用的正确的详细信息级别可以节约计算量。

在工业中把这种思路叫做Cascaded。

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games202/Industry/LOD.png" alt="TAA" />

右边：根据离镜头的距离生成不同级别的Shadow Map。

左边：LPV在一开始传播时，能量更多，能渲染出来的细节也更多，所以需要更精细的网格，到后来能量减少，就可以降低网格的分辨率。

LOD的主要挑战：层级之间的过渡。边界的重叠和混合。

LOD在几何上的应用：余弦生成不同精细度的模型。根据和摄像机的距离选用不同精细度的模型。Popping Artifact：随着摄像机距离改变，模型突然改变，可以用TAA改善。