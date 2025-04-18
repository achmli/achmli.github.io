---
layout:       post
title:        "《见证者》引擎技术博客——Shadow Map第二部分"
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
> CSM优化技巧part2。看了下rtr4里阴影的部分，发现吹哥2004年那个阴影系统反而被提了一嘴。Valient被提到的是却是阴影预计算相关的。
>
> 博客链接：http://the-witness.net/news/category/engine-tech
>
> 原文链接：[Graphics Tech: Shadow Maps (part 2): Save 25% texture memory, and possibly much more. – The Witness](http://the-witness.net/news/2010/04/graphics-tech-shadow-maps-part-2-save-25-texture-memory-and-possibly-much-more/)
>
> 作者：Jonathan Blow

在之前的部分中，我讨论了想要使用CSM的原因（其中最重要的是图像的稳定性），然后提到了我们已经实现了Michal Valient版本的CSM，我们很喜欢它，但是还是想要尽可能地减少内存使用。

这篇文章，我会展示怎么在支持非二次幂纹理（译：上一篇提过二次幂纹理，大概就是就是一个纹理上放4、8、16。。。个纹理？吧大概）的硬件上减少25%的内存占用。而在那些支持的硬件上，在原来只能存放4张纹理的空间里可以多存一张shadow map到5张。

Valient的阴影系统可以产生非常稳定的shadow map，但会消耗大量的纹理内存。回想一下需要真么多内存的原因：你需要把视锥体切片包裹在一个圆中，再把这个圆包裹在一个正方形纹理中。

![1slice](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/3/1slice.png)

在实现CSM时，你会用到不止一个视锥体切片，可能是四个或者五个。Valient在ShaderX 6上的文章提出了一种在一个shader中采样四张不同的shadow map的方法，就是把四张shadow map打包到一张图集(atlas)纹理中，大概像这样：

![thumbs_atlas2048x2048](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/3/thumbs_atlas2048x2048.png)

这是我们最开始实现的方式，但是很快我就意识到这样做会导致缺乏灵活性。如果你的图形硬件支持非二次幂纹理，你大概会希望shadow map的数量是可调节的，但如果纹理是被打包到一个正方形上，那就很难再把第五张塞进去。所以把图集的布局改成了这样：

![atlas4096x1024](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/3/atlas4096x1024.png)

这种形式依然能在只支持二次幂纹理的硬件上工作（二次幂纹理不是必须是正方形）。并且在那些更加灵活的硬件上，我们能轻松地将新的纹理添加到末尾。

当你的图集是这样布局成一行的，如果你对你的游戏添加了一些runtime的可视化，你就能非常清晰地看到纹理空间中有多少部分是未被使用的。下面是一张《见证者》的shadow map的截图：

![green_frusta_1_0](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/3/green_frusta_1_0.png)

视锥体切片被标注成绿色的。显然在它们之间有大量的空白的空间（为了视觉化，我们用shadow map的数据填充了空白空间，实际上没有被绿色覆盖的部分永远不可能在游戏中被看到，所以如果我们剔除这些部分，游戏能运行得更快）。

由于有这么多空白，我们可以把shadow map排列得更加紧密，就能减少内存占用。但是要注意：这个算法的核心是我们依然需要足够的空间来处理最糟糕的情况。例如，稍微旋转一下摄像机，你能得到这个：

![green_frusta_2_0](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/3/green_frusta_2_0.png)

现在贴图见的空隙变得非常小了，所以你不能将它们挤得更近。并且空白的空间几种在底部，不清楚怎么提高利用率。

但是我们有一个可以使用的技巧。尽管所有的shadow map被打包成了一个图集，它们在shader中依然作为独立的单元被索引，这意味着我们可以对它们单独的进行变换。所以我们为什么不将每张shadow map独立地旋转90度呢？下面就是这样做之后得到的图片：

![green_frusta_3](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/3/green_frusta_3.png)

现在有足够多的水平空间了，我们可以把它们打包到一起了！（当然我们不需要渲染shadow map，然后在之后的一个pass中复制和旋转它们。我们只需要在渲染shadow map时旋转相机朝上的向量(up-vector)，所以这个旋转对我们而言几乎是没有代价的）

在我们这样旋转shadow map后，我们的shader必须知道它们被旋转了。幸运的是Valient的系统已经提供了基于贴图索引变换shadow map坐标的方法，所以旋转纹理可以直接适配这个方案。此外，如果我们使用任何过滤偏移量(filter offset，这tm什么意思啊)来索引shadow map，我们需要确保这些偏移量也被旋转（可以选择在将偏移量常量上传到shader前，预先将其旋转，或者在将贴图的坐标转换到图集之前，先将偏移量添加上去，这取决于系统具体的实现方式）。

那么我们怎么把这些视锥体切片打包到一起呢？我们的实现是将它们尽可能的向左移动。第一步，我们计算出能包围这些视锥体切片的矩形（下图中黄色的部分）：

![yellow_rectangles](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/3/yellow_rectangles.png)

这些矩形都有相同的朝向，所以我们只需要将它们都移到左边直到差不多快挤在一起：

![yellow_rectangles_packed](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/3/yellow_rectangles_packed.png)

我们通过一种对某一个视锥体进行暴力的uv包围计算获得矩形方向，并且其他所有的视锥体切片也使用相同方向。“暴力的uv包围计算”的意思是，我尝试一堆角度，然后看哪个贴合得最紧密。在我们现在的实现中，我们用了100个方向，都分布在90度的范围中，所以我们找到的最佳方向的误差在一度以内。（90度是因为超过90度旋转之后计算出来的矩形你之前已经用过了。）

一开始的直觉是选择最初层级的shadow map来计算矩形的方向，但这样做效果并不好。由于第一个视锥体切片过于尖锐了（译：比玩家的声音更尖锐吗），有时候我们计算出来的矩形方向对其他shadow map十分不适合。用其他任何一张shadow map都能解决这个问题。（因为相邻的视锥体切片是共用边界处的平面的。）

到目前位置，除了将后面的shadow map向左移之外，我们并没有做其他的移动。接下来如下图，我们通过将第一张shadow map也稍稍向左移进一步节省空间，移动距离基于视锥体最左侧的顶点位置。（不是基于矩形是因为矩形已经戳破图集来到外面的空间了，我们不需要保持矩形始终在图集内，只需要保证视锥体不出图集就行。记住矩形只是帮助我们打包的工具。）然后我们就得到这个：

![yellow_rectangles_packed_left](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/3/yellow_rectangles_packed_left.png)

我们还可以挤压出更多的空间，最右侧的shadow map可以沿着矩形的方向向上或向下移动，就可以离左边更加近（在这个案例中，是向下：）

![yellow_rectangles_packed_right](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/3/yellow_rectangles_packed_right.png)

显然我们已经节约了大量的空间了，对于这个观察角度，节约了差不多一半。但我们也需要为最差的情况预留足够的空间，那么问题来了，最糟糕的情况是什么样的？经过测试，对于我们这个游戏的FOV，在最差的情况下，依然能节约大概25%的纹理空间。

如果你的硬件支持非二次幂贴图，你能减小贴图的大小，所以你很开心。其他的设备上，你确实做不到这件事，但是你能把你的视锥体切成5份了，要记得你之前只能有4份。

## 解决重叠的问题

你可以随意所欲地打包这些矩形，只要它们不重叠——在场景渲染时，你的shader不知道也不关心这些区域之间的距离。尽管最初构建shadow map就已经非常棘手了。当每个shadow map都在自己的独立正方形区域时，我们为它设置一个viewport（渲染区域，一般来说我们看到的渲染图像是视口，所以这里就是shadow map实际渲染的区域），清空原有的内容后将深度信息渲染上去。但现在，假设我们从左往右渲染shadow map：在我们渲染第二张时，它的viewport不可避免地回合第一张存在重叠。我们必须十分小心避免渲染到第一张shadow map有效的部分，不然我们渲染的场景将会是一团糟。

在我们现在的实现中，我们使用DX9提供的裁剪平面(clipping planes)来解决这个问题（矩形的长边精确地指示了裁剪平面的位置）。可惜在将来的图形API中，裁剪平面会被抛弃，所以我们可能需要改成用模板测试(stencil test)或者一些其他的操作，自己在着色器中完成裁剪的操作。

下图展示了最坏情况的邻近区域：

![worst_case](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/3/worst_case.png)

这种情况会在你大致朝着光源方向，但是偏转角度足够大（译者：我的理解是，看着光源，但是光照是另一个方向，光源到相机和光照方向并不是同一个向量）时出现，这时视锥体会旋转到大致上成为纹理空间坐标轴对角线。（如果直接沿着光源方向，那么视锥体应该是和纹理空间坐标轴平行。）

## 对于还没有做的事情的更深入的思考

我们通过一些基本上都在图像空间执行的操作节约了纹理空间。但我在思考是否能将这些才做投影回3D空间，在我们一开始计算包围球时，使用一些方法来生成更小的包围球。旋转纹理贴图的操作意味着我们将输出空间折叠了，折叠到它自身，只用了一半可能的方向。包围球的核心则是可以使用任意的方向，而我们在回顾时清晰地认识到，这是不需要的。所以可能可以重新组织这个算法，改成包围的半球的形式（或者是一些类型的性转，并且允许视锥体边角的突起戳破它）。

## 节约更多的内存，如果你愿意复制你的贴图或者将它们渲染到许多片(piece)上

我们的系统之所以有效，是因为一旦shadow map被打包进图集，着色器就不知道也不关心这些shadow map的边界在哪里。我们可以自由地寻址整个图集，因为实际上它是一个连续的纹理贴图。这意味着我们还可以更进一步：通过让某些阴影贴图跨越图集边界并自动环绕到另一侧的方式排列图集。这种方式在视觉上看似不连续，但如果场景渲染时的着色器采用环绕模式（wrapping mode）进行纹理寻址，那么就不会受到影响。下面是一个手工制作的示意图（并非实际运行版本，因为我们尚未实现该功能）：

未环绕、便于观察的纹理空间版本：

![wrap_1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/3/wrap_1.jpg)

垂直环绕：

![wrap_2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/3/wrap_2.jpg)

水平环绕：

![wrap_3](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/3/wrap_3.jpg)

在我手工制成的模拟图中，只需要Valient的算法的默认打包方式所需内存的46%

但是代价是：虽然不需要额外的代价就能轻松使用这种映射，但是也以为着这更难生成。要么你先生成一个非环绕的版本，然后将它复制到图集中多个目标位置。要么你用多个pass来生成一张shadow map（总是能安排一张shadow 马匹不用被分割的，但是拿分成4份的情况举例，你可能需要额外的3个pass。每个pass要渲染的量会减少，所以也可能，不会很糟糕）（译：但是图形学不就讲究一个减少drawcall吗）

如果你使用了预滤波的shadow map，那么滤波本身也算是一种复制，你就有可能在基本上免费的情况下完成这种打包。我们在《见证者》中没有做任何的预滤波，但如果我们做了，或许就会迁移到这种打包方案。节约这么多内存，我们怎么能拒绝呢？

但我要重申我们没有实现这种环绕式shadow map的方案，所以我们不知道这里面有没有什么潜在的隐患。我们现在只实现了上文最坏情况节约25%的那种方案。（移动shadow map，不环绕。）
