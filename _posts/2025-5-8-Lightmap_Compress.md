---
layout:       post
title:        "《见证者》引擎技术博客——《见证者》中的Lightmap压缩"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - 《见证者》博客翻译
    - 图形学
---

> 因为十分喜欢《见证者》，所以想试着翻译一下他们的技术博客。
>
> 发现Ignacio Castano的个人博客上也有一些技术文章，而且这个博客一直在更新，所以可能有些文章是值得参考的。
> 
> 不过这篇依然是见证者中使用的技术，文章发布时间是2016年，所以大概依然是现在用不上的技术。
>
> 有用AI辅助翻译，AI真是我叠捏。（有趣的是第一遍把文章内容总结了一下，然后我让它保留原文的格式来翻译，结果把之前的总结1：1地翻译成了英语。。。。。）
>
> 博客链接：[Ignacio Castaño](https://www.ludicon.com/castano/blog/)
>
> 原文链接：[Lightmap Compression in The Witness](https://www.ludicon.com/castano/blog/2016/09/lightmap-compression-in-the-witness/)
>
> 作者： Ignacio Castaño

在我实现的lightmap的初始版本中，使用了RGBA16F作为lightmap纹理的格式。这样做可以有很好的效果，但是内存占用过于大了。所以之后换成了R10G10B10A2定点格式，但是由于精度下降，会带来一些artifact。看上去为了获得平滑的梯度，lightmap纹理的每个通道必须要超过10bit才行。

RGBM色彩变换是当时主流的lightmap编码方法，我试了一下感觉效果还是不够好，但是确实有显著的提升，所以我又想了几个可能加强这个编码器的方法。我花了点时间测试了其中一些想法，设法提高质量的同时降低lightmap数据的大小。在这篇文章中，我会通过一些实例来描述其中一些想法。

![RGBM](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/12/RGBM.png)

我印象里RGBM变换最早是卡普空在CEDEC上的[这个幻灯片](https://game.watch.impress.co.jp/docs/20070131/3dlp113.htm)中提出的。尽管卡普空用它来编码漫反射纹理，但这个技术反而成为了编码lightmap的主流方法。RGBM和一些它的变种被商业引擎广泛地使用，比如unity、UE还有生化奇兵无限的引擎等等等等。而卡普空最初的用法，也就是编码标准的色彩纹理，并没有被广泛使用，但是Shane Calimlim发现这种用法十分适用于[《唐老鸭俱乐部》的风格化渲染](https://shaneycg.github.io/ducktales-remastered-texture-compression/)并表示这是一种很好的格式。但是我很震惊这么广泛使用的编码器居然没有被更加深入地分析。

lightmap压缩的主要挑战是比常规的漫反射纹理更大的动态范围。这个范围确实比不上典型的HDR纹理，但是使用常规的LDR格式已经会导致明显的artifact了。lightmap通常不会有太多高频细节，一般来说接近于灰阶，并且色度上也只有平滑的变化。

针对我们的情况，lightmap的值基本上都在[0, 16]之间，只有很少的情况会在这个范围之外，我们在保留色相(hue)的同时通过clamp色彩(color)来限制它们。Brian Karis也提出过[对范围的上半部分进行tonemapping的方法](http://graphicrants.blogspot.com/2013/12/tone-mapping.html)，用来避免锋利的不连续性（sharp discontinuities），但是我发现只有光源强度大得十分不合理时才会出现这个问题。

lightmap色彩分布的形状有很大差异。室内的lightmap的色彩分布大部分地方是黑的，有一处高光之后拖出一条长长的尾巴：

![interior](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/12/tunnel.histogram.png)

室外的lightmap的色彩分布接近钟形的正态分布。下面这张色彩分布来自于一张受秋天的树木影响的lightmap，有明显的橙色色调：

![outdoor](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/12/hut.histogram.png)

并非所有lightmap都会用到所有可用的范围，所以在tone mapping之后，我们要做的下一件事就是把范围缩小到[0, 1]。

所以，为什么RGBM是压缩这类数据的理想选择？用RGBM表示的数值分布如下图所示：

![rgbm distribution](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/12/rgbm.histogram.png)

它在靠近0的部分提供了更高的精度，而在靠近1的部分精度较低。这对经过多重曝光后的图像来说十分适合。我们想要获得平滑的lightmap，没有量化导致的artifact，也不受相机曝光的影响。但是在下文中可以看到，这种方法在0附近的精度过于高了，远超实际所需。

## Naive的RGBM编码

我最初的实现中使用的是RGBA8纹理，将颜色平方实现伽马校正。标准的rgb到RGBM变化如下：

``` hlsl
m = max(r, g, b)
R = r / m
B = b / m
A = a / m
M = m
```

我之前[已经实现的提升](http://the-witness.net/news/2011/09/a-pleasant-lightmapping-update/)只有将量化区间（quantization interval）二分。这是[微软这篇论文](https://www.ppsloan.org/publications/HDRComp.pdf)中展示的想法的一个变种，与原文中使用一张额外的纹理不同，我只使用了RGB和alpha（M）通道。

[Shane Calimlim](https://shaneycg.github.io/ducktales-remastered-texture-compression/)也完成了类似的观察：

> color map中的灰色会被编码成纯白，但这并不总是最优的。灰色在大多数时候是一种边缘情况，但是更智能的编码算法可以极大地提升这种处理。在算法的简单版本中，表示灰色的负担完全在multiply map上。实际上可以把表示灰色的负担拆分到两种贴图中，在color map具备无损容纳额外数据的场景下，可以大幅提升编码精度。

但是我们的情况是，灰色并非是边缘情况！lightmap基本上都是有轻微的平滑色彩变化的灰色。

我通过选择一个明确的阈值t来实现这个算法。对于m的值小于t的情况，色彩的编码只使用RGB通道，如下所示：

``` hlsl
R = r / t
B = b / t
A = a / t
M = 0
```

而对于m的值大于t的情况，归一化的色彩在RGB通道中编码，而归一化因子m则被偏移（biased）并缩放，以使用更高的精度存储它：

``` hlsl
R = r / m
B = b / m
A = a / m
M = (m - t) / (1 - t)
```

综合一下就是：

``` hlsl
m = max(r, g, b, t)
R = r / m
B = b / m
A = a / m
M = (m - t) / (1 - t)
```

这么做有几个原因。正如Shane指出的，将表示亮度的功能拆分到RGB和M的map中，可以获得更高的精度并且减小量化区间的大小。

当然要说明清楚，这样做会减小0附近的精度，但正如上文所说的，实际上我们本来就不需要在0附近有那么高的精度，毕竟游戏中的相机永远不会有足够长的曝光时间。biased RGBM的灰阶分布如下图所示：

![rgbmt](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/12/rgbmt.histogram.png)

选择不同的t的值使得我们能针对色彩动态范围的不同部分使用不同的量化区间。t的最优选取决于lightmap的色彩分布和纹理的每个通道占用的bit数。对于我们的lightmap，0.3左右是在使用RGBA8格式时的最优解。

## 优化的RGBM编码

使用这些提升后，RGBM已经能产出非常好的结果了。我的肉眼无法找到RGBM的lightmap和原生的半浮点数的lightmap之间有任何差别。但是这样并不能将lightmap的大小减小很多，所以我想要进一步压缩它们。

我尝试的下一件事是用一种能最小化量化误差（quantization error）的方法选择M。我使用了暴力搜索，尝试所有可能的M的值并计算对应的RGB的值，最终选择其中能使MSE(某种误差度量吧大概)的值最小M的值：

``` hlsl
for (int m = 0; m < 256; m++) {
    // Decode M
    float M = float(m) / 255.0f * (1 - threshold) + threshold;

    // Encode RGB.
    int R = ftoi_round(255.0f * saturate(r/ M));
    int G = ftoi_round(255.0f * saturate(g / M));
    int B = ftoi_round(255.0f * saturate(b / M));

    // Decode RGB.
    float dr = (float(R) / 255.0f) * M;
    float dg = (float(G) / 255.0f) * M;
    float db = (float(B) / 255.0f) * M;

    // Measure error.
    float error = square(r-dr) + square(g-dg) + square(b-db);

    if (error < bestError) {
        bestError = error;
        bestM = M;
    }
}
```

这样做能大幅减小误差，但是会引入插值导致的artifact。RGBM编码并不是线性的，所以RGBM色彩的插值并不正确。在naive的方法中，这不是什么很严重的问题，因为邻近的纹素的M值通常都是十分接近的。但通过优化的流程获得的M值不再是必然相近的了。

不过这个问题解决起来也很简单，只要将搜索范围限制到幼稚方法得到的M值的附近就行了：

``` hlsl
float M = max(max(R, G), max(B, threshold));
int iM = ftoi_ceil((M - threshold) / (1 - threshold) * 255.0f);

for (int m = max(iM-16, 0); m < min(iM+16, 256); m++) {
    ...
}
```

这个限制几乎不会降低结果的质量，但能完全消除插值导致的artifact。

尽管这个想法展现了naive方法还有很大的优化潜力，但也没有让我们更加接近我们的目标：减小lightmap的大小。我尝试使用像RGBA4之类的像素打包格式，但即使使用了优化的编码，也不能产出质量足够高的结果。为了进一步减小lightmap的大小，我们只好使用DXT的块压缩（DXT block compression）了。

## RGBM-DXT5

直接压缩RGBM数据效果差，使用上优化的RGBM也无济于事，甚至效果还更差。

这种情况下暴力的压缩器是没有用的，因为当同时处理4X4颜色的块时，搜索空间要大得多。

一种改进方案是：首先使用标准DXT1压缩器通过naive流程获得压缩的RGB值，然后选择一个M值来补偿DXT1压缩器在量化和压缩时产生的误差。

也就是说，我们想要计算出M的值使得：

``` hlsl
M * (R, G, B) == (r, g, b)
```

这就给我们提供了三个等式，可通过最小二乘法原理最小化其总体误差。误差最小的M值为：

``` hlsl
M = dot(rgb, RGB) / dot(RGB, RGB)
```

在我的测试中，alpha map中M的压缩效果非常好，并且能显著地减小误差。

我也尝试了使用新获得的M来再次给RGB编码并压缩，但在大多数情况下并不能降低误差（improve the error，结合上下文来说应该是降低误差吧）。实际效果良好的方法是在初始压缩阶段直接根据M值对RGB误差进行加权处理。

RGB通道和M通道的bit数分布于初始的RGBA8格式纹理有很大区别，所以需要重新选择阈值t。这种情况下t的值在0.15左右时能获得最佳的效果。我猜是因为编码后，每像素RGB通道的bit数减少。

## 结果

在已经描述过的格式之外，我还添加了这些方法和BC6的对比。BC6是一种专为HDR纹理设计的编码方法，还没有任何硬件支持（即使2016年也不至于吧。。。可能是说他们的目标硬件不支持？）我们的优化版RGBM-DXT5方案提供了与BC6几乎相同的质量：

![rmse](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/12/rmse.png)

上图展示了色彩空间转换和范围重新缩放后的最终图像的RMSE（应该是某种误差）的值。

为了了解到编码器的效率，更好的方法是查看重新缩放前的图像的误差值。这看上去要均匀很多，但是不能和BC6相提并论了，因为这种情况下调整输入值的范围通常并不能降低压缩带来的误差：

![normalized rmse](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/12/normalized-rmse.png)

最后，我想试着用RGBM-DXT5压缩标准的图像，并用它和YCoCg-DXT5作比较。下图展示了压缩kodim图集中前八张的结果：

![RGBM YCoCg](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/12/RGBM-YCoCg.png)

显然在压缩LDR色彩纹理时，YCoCg-DXT5比RGBM-DXT5要好得多。

## 结论与展望

我们提出的RGBM编码器对于我们的lightmap而言已经足够好了，但我相信依然还有很大的提升空间。

首先就是针对不同的纹理可以使用不同的阈值t。在使用普通RGBM线性格式编码时，找到要编码的纹理的最佳阈值比较简单，但是在使用块压缩时不那么明显。

RGB分量通过标准加权的DXT1压缩器编码。若使用专门针对M分量可修正误差的RGB值的定制压缩器将更有意义。例如：通过最小二乘法得到的M值有时会超过1，但需clamp到[0, 1]范围，应能通过约束RGB端点来避免此问题。也可能选择使最小二乘拟合M的误差尽可能小的RGB端点。

最后，DXT5在多数移动GPU上不可用。我尚未尝试，但ETC2 EAC_RGBA8格式似乎广泛支持且适合本文技术。将我们的方法与打包浮点格式（如R11G11B10_FLOAT、R9G9B9E5_SHAREDEXP）及ASTC的HDR模式进行对比也将很有趣。

## 表

在所有情况下，我使用RMSE（均方根误差）指标测量误差，该指标与指导块压缩器的度量标准相同。更合理的做法是采用一种能考虑lightmaps在游戏中实际可视化效果的误差指标。我正是这样操作的：对lightmaps进行不同曝光下的tonemapping，并在后色调映射空间（post-tone-mapping space）中计算误差。下图展示了结果数值，它们与原始RMSE指标大致相关。

```
               Tone mapped error
            e=2.2   e=1.0   e=0.22     average   rmse

RGBM8 naive:

hallway:    0.00026 0.00045 0.00089 -> 0.00053 | 0.00007
hut:        0.00100 0.00102 0.00082 -> 0.00095 | 0.00609
archway:    0.00114 0.00141 0.00190 -> 0.00148 | 0.00818
windmill:   0.00102 0.00133 0.00185 -> 0.00140 | 0.00083
shaft:      0.00201 0.00228 0.00214 -> 0.00214 | 0.00798
hub:        0.00151 0.00182 0.00191 -> 0.00175 | 0.00267
tower:      0.00153 0.00200 0.00299 -> 0.00217 | 0.00160
tunnel:     0.00094 0.00123 0.00171 -> 0.00129 | 0.00093
mine:       0.00105 0.00120 0.00141 -> 0.00122 | 0.00640
theater:    0.00099 0.00126 0.00160 -> 0.00128 | 0.00129

RGBM8 optimized:

hallway     0.00010 0.00015 0.00030 -> 0.00018 | 0.00004
hut         0.00049 0.00043 0.00031 -> 0.00041 | 0.00543
archway     0.00044 0.00060 0.00122 -> 0.00075 | 0.00595
windmill    0.00020 0.00026 0.00036 -> 0.00027 | 0.00024
shaft       0.00059 0.00066 0.00102 -> 0.00076 | 0.00501
hub         0.00038 0.00051 0.00085 -> 0.00058 | 0.00099
tower       0.00060 0.00072 0.00082 -> 0.00072 | 0.00112
tunnel      0.00025 0.00031 0.00042 -> 0.00033 | 0.00048
mine:       0.00044 0.00049 0.00083 -> 0.00058 | 0.00467
theater:    0.00061 0.00076 0.00087 -> 0.00075 | 0.00095

RGBM4 optimized:

hallway:    0.00169 0.00259 0.00562 -> 0.00330 | 0.00063
hut:        0.00932 0.00899 0.00773 -> 0.00868 | 0.08317
archway:    0.00906 0.01287 0.02616 -> 0.01603 | 0.09614
windmill:   0.00424 0.00562 0.00830 -> 0.00606 | 0.00402
shaft:      0.01103 0.01314 0.01978 -> 0.01465 | 0.08204
hub:        0.00868 0.01160 0.01848 -> 0.01292 | 0.01722
tower:      0.01004 0.01217 0.01466 -> 0.01229 | 0.01835
tunnel:     0.00516 0.00687 0.01066 -> 0.00757 | 0.00764
mine:       0.00871 0.01044 0.01742 -> 0.01219 | 0.07510
theater:    0.00683 0.00840 0.00963 -> 0.00829 | 0.01057

DXT5 naive:

hallway:    0.00155 0.00249 0.00570 -> 0.00325 | 0.00048
hut:        0.00487 0.00536 0.00564 -> 0.00529 | 0.02119
archway:    0.00500 0.00656 0.01039 -> 0.00731 | 0.01949
windmill:   0.00214 0.00287 0.00444 -> 0.00315 | 0.00177
shaft:      0.01062 0.01339 0.01977 -> 0.01459 | 0.03412
hub:        0.00616 0.00796 0.01130 -> 0.00848 | 0.01481
tower:      0.00551 0.00712 0.01019 -> 0.00761 | 0.00735
tunnel:     0.00235 0.00308 0.00451 -> 0.00331 | 0.00285
mine:       0.00471 0.00589 0.00877 -> 0.00646 | 0.01809
theater:    0.00332 0.00412 0.00496 -> 0.00413 | 0.00498

DXT5 optimized:

hallway:    0.00125 0.00199 0.00456 -> 0.00260 | 0.00041
hut:        0.00336 0.00373 0.00408 -> 0.00372 | 0.01529
archway:    0.00353 0.00460 0.00719 -> 0.00511 | 0.01285
windmill:   0.00134 0.00180 0.00280 -> 0.00198 | 0.00116
shaft:      0.00801 0.01016 0.01507 -> 0.01108 | 0.02437
hub:        0.00469 0.00602 0.00846 -> 0.00639 | 0.01241
tower:      0.00421 0.00544 0.00781 -> 0.00582 | 0.00599
tunnel:     0.00157 0.00206 0.00306 -> 0.00223 | 0.00193
mine:       0.00338 0.00428 0.00646 -> 0.00471 | 0.01178
theater:    0.00245 0.00302 0.00357 -> 0.00301 | 0.00382

DXT5 optimized with M-weighted RGB:

hallway:    0.00114 0.00184 0.00430 -> 0.00243 | 0.00038
hut:        0.00338 0.00382 0.00443 -> 0.00388 | 0.01478
archway:    0.00356 0.00464 0.00725 -> 0.00515 | 0.01271
windmill:   0.00134 0.00180 0.00281 -> 0.00198 | 0.00113
shaft:      0.00804 0.01023 0.01522 -> 0.01116 | 0.02382
hub:        0.00472 0.00611 0.00868 -> 0.00650 | 0.01088
tower:      0.00421 0.00544 0.00787 -> 0.00584 | 0.00597
tunnel:     0.00157 0.00206 0.00306 -> 0.00223 | 0.00193
mine:       0.00337 0.00428 0.00648 -> 0.00471 | 0.01170
theater:    0.00245 0.00302 0.00356 -> 0.00301 | 0.00382
```