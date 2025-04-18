---
layout:       post
title:        "《见证者》引擎技术博客——Shadow Map总结第一部分"
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
> 说是part1，但是并没有后续了。。。。这篇文章是2013年的。
>
> 博客链接：http://the-witness.net/news/category/engine-tech
>
> 原文链接：[Shadow Mapping Summary – Part 1 – The Witness](http://the-witness.net/news/2013/09/shadow-mapping-summary-part-1/)
>
> 作者： Ignacio Castaño

在最近几周，我在完善和优化阴影系统，到目前我觉得不会有什么大的改动了。在此期间，我查阅了大量的资料，然后我被shadow mapping相关知识的分散程度震惊了，它们散落在各种晦涩难懂的ppt、混乱的博客推文、来自微软和硬件供应商的SDK使用范例和各类ShaderX/GPU Gems/GPU Pro这样的书籍中。

![shot_2013.09.18__time_14_11_n09](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/4/shot_2013.09.18__time_14_11_n09.png)

我不打算在这里梳理这些知识，但恰好我在我些这篇文章时， [Matt Pettineo](https://mynameismjp.wordpress.com/2013/09/10/shadow-maps/)发布了一个关于这些不同的技术的概览，可以当作是一个不错的起点。与此不同，我会描述在实现和优化的过程中遇到的问题，也会在末尾提到我尝试过的技术和对我们而言最有效的解决方案。

尽管我知道还有很多技术我们试过，我们现在的解决方案也一定还有能提升的空间，但我也对现在我们实现的质量和新能非常满意。

几年前Jon（吹哥）写了我们最初版的阴影系统，再加上一些早先做的一些小优化，直到最近，它基本上没怎么被修改过，但显然现在shadow map的渲染和采样都过于慢了，迫切需要大幅提升它的性能。

总结一下老的系统，我们使用了稳定的CSM，分成4个区域，基于距离选择，并且用了一些创新性的技巧减少不使用的贴图空间。滤波方面，我们选择了随机的PCF采样，还用了一种混合梯度、坡度和常数偏移的方法来避免痤疮(acne)走样。

## 滤波

我在最初的实现上做的第一个修改是滤波的方法。最初我们用的是一种基于泊松分布的随机旋转PCF采样，类似于《孤岛危机》用的方法。这种方法有很多优点：它能有效地减少采样数量、滤波核半径能轻松调节，但是它太容易产生噪声而导致走样了。

在许多游戏中，这些走样会因为细节纹理(detailed texture)和法线贴图的存在而不那么惹人注目。但对于《见证者》的风格化的几何个平滑的预计算光照，这些走样会非常显眼。

我们试验了使用更多的采样数，但是在我们的案例中，通过提高采样数来获得平滑的结果不符合稀疏采样的目标。最终我们选择了Bunnell和Pellacini提出的箱式滤波(compact box filter)。箱式滤波能产出平滑的结果，但是对于那些由于低分辨率的shadow map产生的阶梯式的走样，平滑的效果就不太行。一种简单的对这种方法的拓展是对每个采样点用高斯曲线施加权重。

这种滤波器naive的实现方法是使用(N-1)x(N-1)的PCF纹理采样数量。在“Fast Conventional Shadow Filtering”这篇文章中，Holger Grün展示了怎么将盒式滤波器的采样数减小到(N/2)x(N/2)，但是认为分离滤波器需要(N-1)x(N/2)，使用Gather4将样本数量减少到(N/2)x(N/2)。我认为他在兜售Gather4的特性上费了太大的力气，以至于没有完全探索出双线性采样的可能性。他的方法相比双线性采样而言太复杂了，而且也没有得到最低采样数的结果。在这里，我会展示一种更加有效和简单的计算滤波器权值的方法。

首先让我们想象出一个对称的水平滤波核，有五个tap

```mathematica
q = {0, a, b, c, b, a, 0}
```

每个这里面的滤波核权重对应一个双线性的PCF样本，实际覆盖6个shadow map的像素，并且每一个滤波核的权重都是我们原始的滤波核权重的线性结合：

```mathematica
k[x_] := s*q[[x]] + (1 - s)*q[[x + 1]]	//就是上一个像素和下一个像素的线性插值
```

x是纹理的整数坐标，s是小数部分。

传统的使用这个滤波核的方法是简单的将q中的权重施加到五个双线性样本上。然而，你能通过将k中的因子施加到6个点样本上来获得相同的结果。

有一个重要的发现是我们可以通过间隔PCF采样使得足迹不重叠并且调整采样的子像素的位置和对应的权重因子来将采样数减半。对于每个样本，我们想要找到满足下面的约束的一个新的子像素坐标 <em>u</em>和对应得新的权值 <em>w</em>：

```mathematica
eq[1, x_] := (k[x] == (1 - u) w)
eq[2, x_] := (k[x + 1] == u*w)
```

在Mathematica中求解这个等式系统，可以得到3个样本中每一个的结果：

```mathematica
  Simplify[Solve[{eq[1, 1], eq[2, 1]}, {u, w}]]

    u -> (b + a s - b s)/(a + b - b s)
    w -> a + b - b s

  Simplify[Solve[{eq[1, 3], eq[2, 3]}, {u, w}]]

    u -> (b - b s + c s)/(b + c)
    w -> b + c

  Simplify[Solve[{eq[1, 5], eq[2, 5]}, {u, w}]]

    u -> (a s)/(a + b s)
    w -> a + b s
```

这个也许和Grün做的那个每行采样数减半的方法差不多。但与之不同的是，这个方法可以拓展到可分离的2d滤波器。

有如下的这样一个5x5的滤波器：

{% raw %}
```mathematica
  q = {{0, 0, 0, 0, 0, 0, 0},
    {0, a*a, a*b, a*c, a*b, a*a, 0},
    {0, b*a, b*b, b*c, b*b, b*a, 0},
    {0, c*a, c*b, c*c, c*b, c*a, 0},
    {0, b*a, b*b, b*c, b*b, b*a, 0},
    {0, a*a, a*b, a*c, a*b, a*a, 0},
    {0, 0, 0, 0, 0, 0, 0}}
```
{% endraw %}

在这个案例中，滤波器覆盖了6x6的采样范围，并且任意一个权重都是邻近的四个因子的线性结合：

```mathematica
  k[x_, y_] := s*t*q[[x, y]] +
    (1 - s)*t*q[[x + 1, y]] +
    s*(1 - t)*q[[x, y + 1]] +
    (1 - s)*(1 - t)*q[[x + 1, y + 1]]
```

我们可以用下面的等式找到新的子像素的坐标u和对应的权值w：

```mathematica
  eq[1, x_, y_] := (k[x, y] == (1 - u) (1 - v) w)
  eq[2, x_, y_] := (k[x + 1, y] == u (1 - v)*w)
  eq[3, x_, y_] := (k[x, y + 1] == (1 - u) v*w)
  eq[4, x_, y_] := (k[x + 1, y + 1] == u*v*w)
```

求解左上角的样本可得：

```mathematica
Solve[{eq[1, 1, 1], eq[2, 1, 1], eq[3, 1, 1], eq[4, 1, 1]}, {u, v, w}]

    u -> (b + a s - b s)/(a + b - b s) 
    v -> (b + a t - b t)/(a + b - b t) 
    w -> (a + b - b s) (a + b - b t)
```

对剩下的8个PCF样本重复这些操作来算出对应的纹理坐标和权重。通过观察结果我们能发现由于滤波核的对称性会出现一些相同的项。一旦我们将公用的子表达式分解并且用标量替换掉a、b、c这些常量，我们就能简化方程得到相对简单的表达式。在我们的案例中，我们将5x5的滤波核的常数设置为1，3，4来实现一个对高斯滤波器的粗暴的近似，这是得到的结果：

```mathematica
    float uw0 = (4 - 3 * s);
    float uw1 = 7;
    float uw2 = (1 + 3 * s);

    float u0 = (3 - 2 * s) / uw0 - 2;
    float u1 = (3 + s) / uw1;
    float u2 = s / uw2 + 2;

    float vw0 = (4 - 3 * t);
    float vw1 = 7;
    float vw2 = (1 + 3 * t);

    float v0 = (3 - 2 * t) / vw0 - 2;
    float v1 = (3 + t) / vw1;
    float v2 = t / vw2 + 2;

    float sum = 0;

    sum += uw0 * vw0 * do_pcf_sample(base_uv, u0, v0, z, dz_duv);
    sum += uw1 * vw0 * do_pcf_sample(base_uv, u1, v0, z, dz_duv);
    sum += uw2 * vw0 * do_pcf_sample(base_uv, u2, v0, z, dz_duv);

    sum += uw0 * vw1 * do_pcf_sample(base_uv, u0, v1, z, dz_duv);
    sum += uw1 * vw1 * do_pcf_sample(base_uv, u1, v1, z, dz_duv);
    sum += uw2 * vw1 * do_pcf_sample(base_uv, u2, v1, z, dz_duv);

    sum += uw0 * vw2 * do_pcf_sample(base_uv, u0, v2, z, dz_duv);
    sum += uw1 * vw2 * do_pcf_sample(base_uv, u1, v2, z, dz_duv);
    sum += uw2 * vw2 * do_pcf_sample(base_uv, u2, v2, z, dz_duv);

    sum *= 1.0f / 144;
```

相对与Gather4，PCF可分离采样的主要优点是能在更大范围的硬件上工作，同时还更高效。用PCF采样的话，我们需要计算新的采样坐标和权重。用Gather4的话我们必须执行深度对比，并且在shader中完成滤波。后者需要更少的指令但是更消耗ALU和纹理单元之间的带宽，更重要的是，他会需要更多的寄存器来保持纹理采样的结果。除了这些缺点，Gather4也有一些优点我们留在下一节探讨。

对那些只是想要使用我们的阴影采样代码而不像了解我们计算权值的这些方程式的，你可以找到集成在 [Matt&#39;s shadow mapping](http://mynameismjp.wordpress.com/2013/09/10/shadow-maps/)里的我们的实现，在OptimizedPCF文件里面。我在两个硬件上跑了它的demo，nvidia gtx480和intel hd4000，测试下来我们的方案能比Gather4快10%~20%。

## Acne

阴影痤疮是大多是shadow map实现的主要问题。消除acne是如此痛苦，以至于我不理解它为什么不够受关注。

在我们的案例中我最终使用了我认为是最普编的解决方案：结合了常数、坡度缩放、[法线](http://c0de517e.blogspot.com/2011/05/shadowmap-bias-notes.html)和接受平面偏差。找到正确的偏移量的值对其中任何一个都是非常复杂的，如果偏移值过大，就会出现阴影漂浮，如果过小，就不能解决acne的问题。

在 [Eliminating Surface Acne with Gradient Shadow Mapping](http://www.shaderx4.com/TOC.html) 这篇文章中Christian  Schuler提出了一种线性过滤深度值和模糊深度对比来减轻acne，但是这种方法与PCF不适配。

另一种替代是将背面渲染到shadow map中，但这种方法容易导致漏光，并且不能解决薄墙上的acne。双重shadow map或者midpoint shadow map看上去非常有趣，但是就带来更多的性能开销，而且并不能完全解决轮廓附近和非常薄的物体的acne的问题，还会带来额外的建模上的限制。

偏移量的大小与纹理像素的尺寸以及滤波核半径这两个变量正相关，所以最简单的解决方法是提高贴图的分辨率。但是更大的分辨率会降低性能。所以最终我们只能在漏光和acne之间寻求平衡，还要再必要的时候对建模添加约束来避免十分严重的走样。

阴影过滤方法的缺点之一就是我们会依赖硬件的纹理单元去同时采样4个shadow map像素并且执行深度比较。当我们使用接收平面偏移值时，可能针对每个shadow map的像素都有不同的值，但我们没有办法向纹理单元提供深度的梯度信息。所以在结果上，接受平面偏移值对于我们的方法不是很有效。实际上，效果非常差，所以我们补偿性地使用更大地法线和缩放偏差值。

为了这些偏差值能很好地运行，根据表面法线和光照方向正确地缩放偏差值是很重要的，特别是，坡度缩放偏差应该正比于法线(N)和光照方向(L)的夹角的正切值(tan)，并且发现偏差值应当与这个夹角的正弦值(sin)成正比。

![shadow_offsets](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/4/shadow_offsets.png)

```glsl
float2 get_shadow_offsets(float3 N, float3 L) {
    float cos_alpha = saturate(dot(N, L));
    float offset_scale_N = sqrt(1 - cos_alpha*cos_alpha); // sin(acos(L·N))
    float offset_scale_L = offset_scale_N / cos_alpha;    // tan(acos(L·N))
    return float2(offset_scale_N, min(2, offset_scale_L));
}
```

在最后，法线偏差的缺点是它不仅便宜深度，还会导致阴影的位置出现偏移。单独使用时这种偏移不会很明显，但是阴影的每个层级间的偏移值不同，所以不同层级间的阴影出现明显的位移。虽然混合不同层级能有一定帮助，但是我们在不同的层级间将偏移值的量级插值，使位移几乎不会被察觉。

## 后续（译：实际上并没有）

在part2，我们会讲述层级放置的算法并且会讲完我们在加速阴影渲染方面的优化。
