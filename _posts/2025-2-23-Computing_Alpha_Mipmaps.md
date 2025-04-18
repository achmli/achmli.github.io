---
layout:       post
title:        "《见证者》引擎技术博客——计算alpha mipmap"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - 《见证者》博客翻译
    - 图形学
---
> 因为十分喜欢《见证者》，所以想试着翻译一下他们的技术博客。
>
> 总之它们博客上Engine Tech这个tag里的更新基本上都在2010年到2014年，所以这里面的技术很大可能都已经落后了，突出一个学了可能没啥用。
>
> yysy，这篇文章在rtr4中也被提到了，总之在这本实时渲染的经典中看到<em>the witness</em>的截图感觉还蛮神奇的。
>
> 博客链接：http://the-witness.net/news/category/engine-tech
>
> 原文链接：[Computing Alpha Mipmaps – The Witness](http://the-witness.net/news/2010/09/computing-alpha-mipmaps/)
>
> 作者： Ignacio Castaño

在开始树木和植被的制作后，我们发现了一个问题，那就是那些使用alpha test的纹理，传统的mipmap算法会意外地产生一些比较坏的效果。当我们把镜头拉远后，树叶会消失以至于看上去非常稀疏。

下面是一个例子。在树离摄像头很近时，看上去很OK：

![near_nocoverage-512x320](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/6/near_nocoverage-512x320.png)

但当我们离远一点，树叶开始消失，看上变得稀疏：

![mid_nocoverage-512x320](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/6/mid_nocoverage-512x320.png)

直到几乎完全消失：

![far_nocoverage-512x320](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/6/far_nocoverage-512x320.png)

我之前没有遇到过这个问题，也没听说过类似的情况。但谷歌了一下就发现美工经常被这个问题困扰，并且用各种各样的hack来规避问题。下面是几种常见的方法：

+ 在Photoshop中手动调节mipmap的alpha通道的对比度和锐度
+ 在shader中根据距离或者根据基于纹理梯度的LOD因子来缩放alpha值。
+ 限制mipmap的数量，防止在游戏中使用最低级的mipmap。

这些方法能以某种形式规避问题，但是没有一个是完全正确的，有时还会添加过大的开销。

为了定位问题，理解为什么这些几何体会消失至关重要。在标准的mipmap的alpha通道的计算算法中，每张mipmap的alpha test覆盖率都不一样，就是通过alpha test的像素的比例变化了，在大多数情况下这个比例都是在降低，导致纹理变得透明。

> <em>real-time rendering 4th</em>: 这可以用这样一个例子来进行解释：假设我们现在有一个具有四个alpha值的一维纹理，即(0.0,1.0,1.0,0.0)；而在平均之后，下一个mipmap层级所对应的纹素值会变为(0.5,0.5)，最高层级mipmap所对应的纹素值为(0.5)。现在，假设我们现在使用\alpha_t = 0.75来作为alpha测试的阈值。当访问第0级的mipmap时，4个纹素中的2个可以通过alpha测试，不会被丢弃。但是，当访问剩下两个mipmap层级时，由于0.5 < 0.75，因此所有纹素都会被丢弃。

一个简单的解决方案是找到使alpha test的覆盖率尽可能接近最初的纹理的缩放因子。首先我们定义第一张mipmap的覆盖率：

```mathematica
coverage=Sum(a_i > A_r) / N
```

其中 `A_r`是alpha test的阈值，`a_i`是mipmap上第i个像素的alpha值，N是mipmap的总像素数。(a_i > A_r)的结果是0或者1。

然后对于后面的mipmap，你想要找到一个使得覆盖率保持相同的缩放因子：

```mathematica
Sum(scale * a_i > A_r) / N == coverage
```

然而由于这是一个离散的问题，所以直接求解这个 `scale`比较棘手。通常来说这没有精确的解，并且 `scale`是没有边界的。相反你能做的事是找一个新的alpha阈值 `a_r`来保持覆盖率。

```mathematica
Sum(a_i > a_r) / N == coverage
```

这个求解就容易很多，因为 `a_r`是有边界的，在0~1之间。所以用一个简单的二分搜索就能找到最优的解。一旦计算出 `a_r`就能很简单地计算出 `scale`的值了：

```mathematica
scale = A_r / a_r
```

这个算法的实现已经在[NVTT](http://code.google.com/p/nvidia-texture-tools/)公开。相关的代码能在下面两个[FloatImage](http://code.google.com/p/nvidia-texture-tools/source/browse/trunk/src/nvimage/FloatImage.cpp)类中的函数中找到：

```cpp
float FloatImage::alphaTestCoverage(float alphaRef, int alphaChannel) const;
void FloatImage::scaleAlphaToCoverage(float desiredCoverage, float alphaRef, int alphaChannel);
```

以下是通过NVTT API使用的简单示例：

```cpp
// Output first mipmap.
context.compress(image, compressionOptions, outputOptions);

// Estimate original coverage.
const float coverage = image.alphaTestCoverage(A_r);

// Build mipmaps and scale alpha to preserve original coverage.
while (image.buildNextMipmap(nvtt::MipmapFilter_Kaiser))
{
    image.scaleAlphaToCoverage(coverage, A_r);
    context.compress(tmpImage, compressionOptions, outputOptions);
}
```

正如下面的截图所示，这能彻底地解决这个问题：

![mid_coverage-512x320](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/6/mid_coverage-512x320.png)

即使是树离摄像机很远：

![far_coverage-512x320](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/6/far_coverage-512x320.png)

注意这个问题不止在使用alpha test时出现，在使用alpha to coverage（就像截图中那样）（译：没能理解，只是计算覆盖率？还是反向的alpha test？）或者普通的alpha blending也会有这个问题。在这些情况下，虽然没有alpha阈值，但只要选择一个接近于1的值，这个算法依然有效——因为本质上你想要的是保持像素的比例接近于不透明。

（译：还是看看rtr4怎么解释alpha to coverage吧。。。。）

![coverage](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/6/coverage.png)

译：以及对这一整篇的内容，还是看看远处的rtr4吧家人们

![rtr4](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/6/rtr4.png)
