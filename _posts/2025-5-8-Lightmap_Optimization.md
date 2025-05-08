---
layout:       post
title:        "《见证者》引擎技术博客——为iOS优化Lightmap"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - 《见证者》博客翻译
    - 图形学
---

> 因为十分喜欢《见证者》，所以想试着翻译一下他们的技术博客。连翻两篇，说明我极其不想改论文。
>
> 发现Ignacio Castano的个人博客上也有一些技术文章，而且这个博客一直在更新，所以可能有些文章是值得参考的。
> 
> 不过这篇依然是见证者中使用的技术，文章发布时间是2017年，所以大概依然是现在用不上的技术。
>
> 有用AI辅助翻译，AI真是我叠捏。
>
> 博客链接：[Ignacio Castaño](https://www.ludicon.com/castano/blog/)
>
> 原文链接：[Lightmap optimizations for iOS](https://www.ludicon.com/castano/blog/2017/10/lightmap-optimizations-ios/)
>
> 作者： Ignacio Castaño

将《见证者》移植到iOS的只要挑战之一是减少应用内存占用。PC版本使用的lightmap完全超出了iOS平台的内存预算。

如上一篇文章中所述，在PC上我们使用RGBM-DXT5来压缩lightmap。但是iOS不支持DXT5纹理压缩格式，所以第一个问题就是找到合适的替代品。

iOS上最流行的纹理压缩格式是PVR，但这并不是一个特别好的选择。它有一些烦人的尺寸限制的同时还不支持独立的alpha通道。这意味着使用一种RGBM的方案会要求从多张纹理上进行采样。

由于我们用metal作为图形接口，所以所有我们的目标设备都支持ETC2，这种格式有一个类似DXT5的模式，即用一个块表示RGB色彩以及用另一个块表示alpha值。这与我们使用的RGBM lightmap更加适配。

对于RGB通道，我只是简单地使用了Rich Geldreich的ETC压缩器（[(rg-etc1](https://github.com/richgel999/rg-etc1)）。这个压缩器只支持ETC1的块模式，而没有ETC2的扩展。由于lightmap通常较平滑，所以我希望ETC2的planar模式能够高效的表示它们。我通过最小二乘拟合（least squares fitting）实现了近乎最优的planar压缩器，但是有趣的是，标准的ETC1模式在大多数情况下有更小的误差，最后仅有4%的块使用了planar模式。

![etc rgbm](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/13/etc-rgbm-chart-2.png)

如上图所示，ETC2-RGBM的质量稍低于DXT5-RGBM。不过实际上尽管误差更大，但是实际应用中几乎无法察觉到有任何差异。增加对T和H模式的支持可能会缩小ETC2-RGBM和DXT5-RGBM之间的差距，但是毕竟我还有其他更重要的问题要处理，所以这么做不值得。

经过这些调整，移动端lightmap的大小就与PC端相同了，但是我们的目标是进一步减小lightmap的大小。其中最简单的方案就是直接降低lightmap的分辨率。这是有效的，但是由于lightmap打包效率的问题，体积与分辨率并不是直接成正比的。分辨率越低，效率也越低。所以单独使用这个方法会导致收益递减。例如下图中右侧的lightmap的面积只有左侧的四分之一，但是像素数量只减少了一半。

![lightmap](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/13/charts.png)

为了解决这个问题我们使用一种稍显激进的打包方案，但最有效的方法是通过最小二乘顶点烘焙（[least squares vertex baking](https://cal.cs.umbc.edu/Papers/Kavan-2011-LSV/)，原文中的链接似乎被重定向去“精彩视频”了，笑），计算逐顶点lightmap。

![shot1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/13/File-Oct-05-11-13-20-PM.png)

![shot2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/13/File-Oct-05-11-12-45-PM.png)

![shot3](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/13/File-Oct-05-11-12-03-PM.png)

最小二乘顶点烘焙对大量实例化的小型网格（如鹅卵石和小岩石）特别有效，但也引发了一些新问题。

在早期关于[《见证者》的lightmap](https://zhuanlan.zhihu.com/p/1883677873090569010)技术的文章中，我描述了无效采样的检测方法：渲染半立方体时统计背面朝向的纹素数。数量超过阈值则判定为无效采样，其颜色由周围采样插值。这个方法效果很好，但是我们设定的阈值有点过于保守，因为我们的网格并非是滴水不漏或者正确的闭合的。这导致了一些误报，也就是说，有一些无效的采样被当成有效了。这通常来讲不是大问题，因为这些采样位置从玩家视角基本上是不可见的，往往都被一些其他的几何体遮挡住（比如说，在地下）。但是，当使用最小二乘顶点烘焙，这些采样会影响所属三角形的顶点，而这些顶点往往对玩家是可见的。

我能想到的唯一解决方案是收紧验证阈值，但这会导致出现许多新的由模型瑕疵（应该就是上文中说的没有正确闭合和不够滴水不漏的模型）产生的artifact，这就需投入大量美术时间修复。

尽管额外工作繁重，但是获得的成果对得起这些付出。在花销最大的场景中，lightmap内存占用降至原版的25%：

```
PC: 234 MB  
iOS: 60 MB  
```

而在可分发包中，lightmap资源体积仅剩17%：

```
PC: 1781 MB  
iOS: 304 MB  
```