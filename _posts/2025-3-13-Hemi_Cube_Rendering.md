---
layout:       post
title:        "《见证者》引擎技术博客——半立方体渲染和积分"
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
> 博客链接：http://the-witness.net/news/category/engine-tech
>
> 原文链接：[[Hemicube Rendering and Integration – The Witness](http://the-witness.net/news/2010/09/hemicube-rendering-and-integration/)](http://the-witness.net/news/2010/04/graphics-tech-shadow-maps-part-2-save-25-texture-memory-and-possibly-much-more/)
>
> 作者：Ignacio Castaño

我们的全局渲染实现的目标之一是在保持简洁的同时获得良好的性能，并且我们希望用GPU来完成这些。尽管有许多种可以在GPU上计算全局光照的方法，但我们能想到的最简单的方案是使用我们现有的渲染引擎，用固定的一系列最终收集(Final Gathering)步骤来估算全局光照。具体来说，在lightmap上的每个像素渲染场景来收集这点上所有的输入irradiance，并将其积分得到输出的radiance，并且重复这些步骤数次直到lightmap收敛到一个近似解。这套方法和Hugo Elias描述的方法大体上相同(Hugo Elias的原文链接打不开，但搜了一下好像有人翻译了)。

![pretty_shot](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/7/pretty_shot.png)

使用相同的引擎使得将全局光照和游戏中的其余部分保持同步变得很容易。如果我们添加新的shader或者材质、更改几何表达或者调整场景，保持全局光照更新几乎不需要额外的工作。另外有一个有趣的益处是对渲染引擎的优化同样能提升全局光照的预计算。然而，在后面能看到，在实践中，每个应用都在不同的方面给系统压力，并且最终有不同的瓶颈，导致渲染时间的提升不是必然提升预计算的性能，反之亦然。

## 投影方法

我尝试了几种渲染场景和估算入射radiance的方法。其中最通用的方法是渲染半立方体：这种该方法要求将场景渲染到五个不同的视口。一些文章建议使用球面投影或者抛物面投影，但我的经验告诉我由于非线性的投影这些方法会产生糟糕的结果。除非又非常高的细分率，不然场景会产生不可接受的扭曲，导致产生物体间的间隙或者平行表面自相交的问题。

![spherical_paraboloid](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/7/spherical_paraboloid.png)

在《GPU Gems 2》中，Coombe等人提出了独立于(x, y)用正交投影单独投影z坐标的值的方法，以保持正确的深度顺序。如下图所示，这样能移除最显眼的那些瑕疵，注意塔里的楼梯不再能被看到了：

![paraboloid_orthographic](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/7/paraboloid_orthographic.png)

然而，尽管这样做在一些视点能有不错的效果，但在相机非常靠近一个表面时，失真会严重到不可接受，而我们经常会碰到这种情况。所以实践中这种方法不太实用。注意在我们采样塔楼内部的光照时外面的场景依然是可见的。

![paraboloid_artifacts](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/7/paraboloid_artifacts.png)

其他的实现使用单平面投影。这种投影不会捕获整个半球，但是使用一个广视角的FoV，有可能采样到半球的大约80%。我没有尝试过这种方法，但也大概知道结果看上去会是什么样。我修改了半球积分器，让它忽视地平线附近大约20%的采样，发现会引入对于高质量的结果来说不可接受的瑕疵。

[Pascal Gautron](http://www.graphics.cornell.edu/~jaroslav/papers/2008-irradiance_caching_class/08-pascal-gpu-notes.pdf)估算了这种方法在典型的场景中会引入18%的均方根误差，但也建议使用重新平衡立体角权重或者外推边界采样填补空洞的方法。这其中的后者能将误差降至大约6%。

然而，这些提升不能消除强光光源突然移除投影视锥而不可见时产生的带状的瑕疵。更糟糕的是，这种投影缺乏旋转不变性，在半立方体渲染时伴随有随机的旋转的情况下，问题会被放大。所以尽管在很多情况下结果会看起来不错，但是依然存在一些不能使用这个方法的情况。

另一个问题是广视角的视锥体的大小是等效的半立方体的4倍，还很容易和周围的几何体相交。在后文中我会讨论，这是我要解决的主要问题之一。

最终我还是为了简单选择了传统的半立方体。我觉得花式四面体或者3~4面的立方体投影，但考虑到改进的代价，它们并不值得尝试。

## 半立方体重叠

正如我刚才提到的，主要问题之一是我必须解决半立方体和集合体之间重叠的问题。这些重叠是不可避免的，除非对建模施加严格的限制，但这对生产来说是令人不满的。

当几何结构很好而且没有自相交的问题，这些重叠有时能通过质心采样来避免。如果没有采用质心采样，则用于渲染半立方体的位置位于包含样本的多边形之外，从而和另一个体积重叠。

![centroid21](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/7/centroid21.png)

使用质心采样时，半立方体的来源（译：大概是采样点的位置的意思吧）必然是在表面内部的。但是它可能会很接近表面的边界从而和附近的表面重叠。一个简单的解决方案是把附近重叠的表面朝向相机靠近的方向移动，直到不再重叠，但是离相机多近呢？离最近的边界的距离可以通过分析决定，但是限制在于多远的距离不会导致深度采样的瑕疵呢。一种简单的解决方案是在相同的位置嵌套渲染多个半立方体，每个半立方体的远平面与下一个半立方体的近平面重合。

![hemicubes1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/7/hemicubes1.png)

当几何体是紧密到滴水不漏（译：watertight在这不知道咋翻）且使用质心采样时，这样能解决大部分的问题。但是在大部分情况下，我们的资产并不会十分理想。所以我必须找到一些更通用的解决方案。我尝试了很多种启发式的方案，比如将背面渲染成黑色、填充平均颜色、外推邻近颜色等，但是这些方法都不能很好地应对所有情况。最终，我找到的能产出令人满意的结果的方法是，在积分半立方体时，用一个特殊的标签渲染背面以区分前面。如果半立方体的包含太多的被标记的像素，则丢弃这个采样点，取而代之的是，输出的radiance通过这个位置的邻近的有效采样点插值或者外推来获得。

外推并不总是正确的，有效的半立方体的检测也不是100%精确，但到目前为止，这是最令我满意的方法。在下篇文章中我会更多讨论外推的实现细节。

## 阴影渲染

尽管目标是使用同一个渲染引擎，但直接使用原来的阴影系统还是杀鸡用牛刀了。我们使用每帧实时更新的CSM，并且为了最大化Shadow Map的分辨率，shadow map都与视锥体切片对齐。当渲染半立方体时，shadow map的分辨率就没有这么重要了，而为了每个半立方体的表面重新渲染阴影是非必要的开销。为了尽可能简单，我仍然使用CSM，但是相比于从每个视角渲染，我选择每个物体只渲染一次，并且将分级的中心放在物体的中心，CSM的分级围绕着物体的中心。

## 光栅化

刚才我说明了怎么去捕获任意一点上场景的irradiance，对于lightmap上的每个像素，采样场景的irradiance都是必须的。我仅仅使用保守的光栅化器在lightmap的UV空间中光栅化几何体，在那些覆盖率超过阈值的片段（fragment）渲染半立方体。

用我们的光栅化器的有一个好处就是能分析出精确的覆盖率。由于参数化不会有重叠，覆盖率就是纹理像素正方形与被光栅化的多边形相交的面积。质心也是类似的情况，就是剪切后的多边形的质心。

这种方法可以给出渲染半立方体来源的位置和方向，但是我依然需要另外确定半立方体的朝向，起初我简单地选择使用传统的标准方法计算出来的任意方向，但是结果会有带状的瑕疵：

![banding_small_00](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/7/banding_small_00.png)

问题产生的根源是半立方体受限的分辨率，但惊人的是这个问题很难靠增加半立方体的尺寸来排除。更好的解决方案仅仅是使用随机的方向：

![noise_small_00](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/7/noise_small_00.png)

注意我是用噪声替代了带状瑕疵，但噪声更容易用一些平滑的方法排除。

## 积分

在半立方体被渲染之后，就有必要把采样的irradiance积分以计算输出的radiance。irradiance半立方体的积分就只是采样值的加权求和，权值为半立方体的像素在半球上的余弦加权投影面积，也就是像素的余弦加权立体角。这个权值是常数，所以可以被提前预计算。

在我在文章开头引用的Hugo Helias的文章中使用了相同的方法，并且将权值表成为“The Multiplier Map”。但是当心那篇文章中的这部分，他用的公式有bug，像素的立体角并不是相机的朝向与相机到像素的方向的夹角的余弦：

![global_illumiantion_compendium](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/7/global_illumiantion_compendium.png)

![texel_solid_angle_bad](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/7/texel_solid_angle_bad.gif)

这个式子需要除以相机位置和像素质心之间距离的平方：

![texel_solid_angle_good](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/7/texel_solid_angle_good.gif)

在[Global Illumination Compendium](http://people.cs.kuleuven.be/~philip.dutre/GI/)中的第25个公式中能找到更多细节。

由于这是预计算，所以精确计算立体角是有意义的，可以通过使用Girard的公式，或者[Manne Ohrstrom 的论文](http://www.fizzmoll11.com/thesis/)中的便捷公式得出，这样做能提高积分对半立方体旋转的不变性，能有效降低噪声。

最后，积分的计算操作起来十分简单，它可以在计算着色器中非常高效地完成，我将来可能会选择这么做。但在原型中，用CPU计算积分要容易实现很多。然而这就要求在总线上传输数据，所以如果处理不当，这会严重地降低性能。

## 异步内存传输

与流行的观点相悖，D3D9提供了一种异步执行内存复制的机制。在D3D10和OpenGL中，这是通过staging resource或者pixel buffer object完成的。在D3D9中，可以用offscreen plain surfaces实现类似的功能。问题是这种办法没有很好的文档，所以很容易就偏离最快的路径，而且对于每个IHV发生这种情况的情况也会略有不同。

首先，必须要创建两个Render Target和offscreen plain surfaces。

```cpp
dev->CreateRenderTarget(..., &render_target_0);
dev->CreateRenderTarget(..., &render_target_1);
 
dev->CreateOffscreenPlainSurface(..., &offscreen_surface_0);
dev->CreateOffscreenPlainSurface(..., &offscreen_surface_1);
```

如果你有超过两个目标，在一些系统中副本会变成同步的，但是对于并行处理内存传输有两个就已经足够。

最重要的观察结果是，看上去唯一一个异步执行的硬件函数是 `GetRenderTargetData`。在调用这个函数之后，其他的硬件函数都会阻塞直到复制完成。所以比起将内存传输与渲染代码并行执行，最好是找一些CPU的工作来和内存传输并行执行。我的方法是在在复制一个Render Target时，执行另一个Render Target的积分计算。

```cpp
while hemicubes left {
 
    [...] // Render hemicube to render_target_0
 
    // Initiate asynchronous copy to system memory.
    dev->GetRenderTargetData(render_target_0, offscreen_surface_0);
 
    // Lock offscreen_surface_1
    // at this point the corresponding async copy has finished already.
    offscreen_surface_1->LockRect(..., D3DLOCK_READONLY);
 
    [...] // Integrate hemicube.
 
    offscreen_surface_1->UnlockRect();
 
    swap(render_target_0, render_target_1);
    swap(offscreen_surface_0, offscreen_surface_1);
}
```

另一个问题是buffer应该足够大以跑满可用带宽，使得传输率能够饱和。为了实现这个我打包了多个半立方体在一张纹理图集中，如下图所示：

![hemicube_atlas-300x300](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/7/hemicube_atlas-300x300.png)

在实践中，我没有使用图中那样的十字布局来渲染半立方体，取而代之的是将每个面紧密地排列在一个3*1的矩形中，以尽可能少的浪费纹理空间，最大化的利用带宽。而十字布局对于在debug时可视化输出十分有用。

## 性能和结论

我们的全局光照解决方案有点令人失望。尽管我们把大多数工作放在GPU上，但是我们并没有真正高效的使用它。主要的GPU瓶颈是固定功能的几何管线。我们基本上是在一个小的Render Target上渲染大量的小三角形。

但这并不是主要的问题。在CPU端遍历场景并且提交渲染指令事实上比在GPU端执行指令和渲染场景耗费更多的时间，所以GPU是未被充分利用的。

我们的引擎是为了快速原型设计的，为了能够轻松地绘制各种不同材质的物体，而不是为了用最高效的方式做到这些。这些低效在lightmap烘焙器中会变得更加明显。

站在好的一面，一旦我们优化引擎CPU端的部分，性能就有可能提升。现代的GPU也能提供一次性渲染多个半立方体的面。我们期望这能显著地减少CPU的工作。

尽管通过复用我们的渲染引擎，很容易就能启动和运行我们的全局光照解决方案，但要将它的质量和性能提升到足够的水平需要大量的时间。在下一集，我会讲述一些我实现的用来修复一些残留的瑕疵和提高性能的技术和优化。
