---
layout:       post
title:        "《见证者》引擎技术博客——Lightmap 参数化"
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
> 原文链接：[Lightmap Parameterization – The Witness](http://the-witness.net/news/2010/03/graphics-tech-texture-parameterization/)
>
> 作者： Ignacio Castaño

正如Jon在之前的推文中说的，我们在《见证者》中使用预计算的全局光照，并且我最初的几个任务中就有实现这个系统。

我已经开发了一些有趣的技术分别用来计算自动的元素化，制定可以轻松映射到GPU的光照计算，以及通过irradiance缓存加速它们在低频部分的计算。这些技术算不上前沿，但是我还是遇到了一些经常被文献忽视的问题，然后我总结了一些有我认为很有趣的创造性的解决方案来分享出来。然而在回顾是，我发现我依然犯了一些错误，但我希望我诚实地面对它们可以让我在将来不再犯相同的错误。

在第一篇推文中我会描述我已经完成了的lightmap元素化算法。后续的推文中，我打算谈论我们光照系统中的其他细节，例如用半立方体表现最终的收集（译：的光照吧大概）和我们的irradiance缓存的实现。

为了使用预计算光照我们需要一种将光照计算映射到表面上的方法。一种可能的方法是逐像素存储，但是在许多案例中这样的分辨率会过低并且光照的插值会使得网格的三角形的划分过于明显。许多游戏用较高的纹理和法线贴图细节来补偿光照上细节的缺失，但这种方法与Jon想要的实现的风格不适配。所以，我们决定用物体的完全参数化来将预计算光照存储到lightmap纹理上。

手动创建这些元素化是有可能的，但这很消耗时间并且我也想要让我们的美工能使用更加享受的工具。所以我们决定自动创建元素化。然而，我犯了最大的错误，在寻找现有的解决方案时不够仔细。我有一些已经可用的实现，而且我高估了整合它们并产生健壮的结果所需的努力。在GDC上我和一些朋友讨论这件事，他们中有一个人问我为什么不用微软的UVAtlas工具 （译：找不到，大概微软删库跑路了？感觉不如xatlas），沮丧和尴尬的我只能回答“我不到啊”。我认为这说明了对于一个向我们这样的小团队而言，开发时保持开放非常重要。

现在我解决了这个问题，谈论一下这个技术吧。我们只用lightmap表示间接光照和静态面光源的直接光照。因此，我们预期lightmap会比较平滑，并且缝隙不会是很大的问题。因此我们不到算尝试保证无缝的解决方案，而是用相对传统的方法：首先我们将输入的集合体划分为具有圆盘拓扑(disk topology)的图表，将它们单独参数化，最终打包进一张矩形纹理。

## 分块(Segmentation)

将网格划分近图表是过程中最复杂的步骤。过去我试过分层次(hierarchical)的簇(clustering)，但是不怎么成功，所以这一次我决定用一种类似于Lloyd's algorithm的迭代的clustering算法，我们都受到了 [Multi-chart geometry images (MCGI)](http://research.microsoft.com/en-us/um/people/hoppe/proj/mcgim/)这篇论文的启发。

与Lloyd的算法类似，MCGI算法通过迭代进行图表扩展和reseeding(大概就是重新选定每个cluster初始的三角形)。图表增长是每个三角形的质心距离最近和法线偏差最小（译：法线偏差也算是一种距离）的种子，然后就将这个三角形划分到这个种子的图表中。每次图表增长完成后重新选定每个chart中央的三角形作为下一次迭代的种子，直到迭代到种子不会变化了。

我事实现的MCGI算法效果还行，但是并不总是产生正确的结果。可以通过调整种子的数量和位置来获得想要的结果，但这需要一定程度的用户介入，这是我们不想要的。

问题是对“好”的定义是主观的。通常意味着图表形状合理、贴合表面、产生的参数化结果失真小，边界平直凸出以及尺寸均衡。

为了让这个算法满足我们的目标，我做了两件事，一是修改了引导的方法让初始的种子数可以被自动选择，二是用混合的指标来划分图表以获得对结果的更强的控制。

为了选择初始的种子数量，我只是简单地一个一个插入种子，然后增长各自的图表直到达到阈值。然后选择任意一个未被分配的三角形作为种子然后重复。当所有三角形都已经被分配，就从每个种子同步重新开始分配三角形，这里是重复原来的MCGI算法。

一种移除对初始情况的敏感度的算法的共同策略是farthest point启发式(大概就是选离所有图表最远的吧)。然而，我发现将已选择的图表的最差候选的三角形作为下一个种子有很好的效果。

第二个重要的改变是这个算法用了一组不同的指标。MCGI的论文中的指标是法线偏差和质心间的距离。我发现完全使用距离使得这个算法非常依赖于网格的分布(tessellation，按理说是细分)，并且用质心计算距离的方式会更偏向低长宽比的三角形。

取代三角形中的距离，我考虑只用法线偏差，然后和一些类似 [D-Charts: Quasi-Developable Mesh Segmentation](http://www.cs.ubc.ca/labs/imager/tr/2005/Vlad_DCharts/)中提出的指标结合，将圆度(roundness)和平直度(straightness)纳入考虑。

这些指标依然有它们自己的问题，我必须用不同的方式调整它们。最重要的问题是它们用不符合预期的方式限制了图表的增长。例如，你更重视图表的凸包性然后用一个高相关的因素作为相关的指标，但这可能得到一大堆勉强凸包的图表，一旦形成凸包，就不再向图表中添加额外的三角形。所以比起用这些指标限制增长，我只用它们引导增长偏向于最凸包或者最平直。这会允许图表自由地增长，但仍然尽可能保持最凸包和最平直。

有一个在很多案例中都有帮助的技巧：在不给艺术家增加额外负担的前提下，融入他们的创作意图。一种做到这件事的简单的方法是将网格中已有的参数化内容保留下来。我们的模型已经有用于纹理的参数化，并且美工更倾向于将纹理的接缝放在不容易看到的地方。将这些接缝放在我们的图表的边缘不止会减少总体上接缝的数量，还会使得图表的增长更加匹配美工的手工制作。

![charts02-300x168](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/5/charts02-300x168.png)

我独立地考虑纹理和法线的接缝。由于我们的参数化是用于光照，所以我对法线接缝的处理会更严格，我会根据接缝处相邻面的夹角动态调整其约束强度(Since our parameterization is used for lighting I follow normal seams more strictly and proportionally to their angle，不知道咋翻，问了ds)。如果不这么做，模型转角处的光照过渡会因参数化扭曲而显得模糊不清（尤其是硬边结构的棱角细节会丢失锐利感）。这种方法也会帮助加速那些有大量硬边（墙体转折、门窗边缘等）的网格上，比如建筑模型。

![charts00-300x168](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/5/charts00-300x168.png)

最后，我并没有加强人格图表拓扑的约束。我想要图表只要指标还没到预期的阈值就围绕着网格上的洞来增长。我也尝试过更精确的代理曲面拟合指标(proxy fitting metric)替代法线偏差指标，但这样会生成需要手动切割的柱状和锥状的图表，我不想处理这些。另一边的网格闭合则相对简单，只需要检测所有的边界并且将它们闭合，除了最长的那个。

![charts01-300x168](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/5/charts01-300x168.png)

## 参数化

对于图表参数化算法，我们只是简单地使用了[Least Squares Conformal Maps](http://alice.loria.fr/index.php/publications.html?Paper=lscm@2002)，因为我已经有一个能用的实现了。我的实现主要基于[SIGGRAPH 2007 Mesh Parameterization course](http://www.inf.usi.ch/hormann/parameterization/index.html)的[笔记](http://www.inf.usi.ch/hormann/parameterization/CourseNotes.pdf)中的算法，我发现比原论文中的算法更易读，特别是其中关于数值优化的章节特别好用，如果让我重新写一个稀疏矩阵的求解器，我可能更愿意使用OpenNL。

LSCM并非最佳的参数化算法/、。它在绝大多数情况都有很好的表现，但是在很少的一些情况它的结果可能有一些小的自重叠。它会在这两种情况出现：

+ 输入的零面积的三角形有时会在参数化时反转。
+ 有复杂边界的图表在参数化时可能自相交。

第一种情况是输入的网格被检测为洞并且被退化的三角形填充（games104：因为一边被细分后写边上就有顶点了，有直接读取的高度而另一边是斜边原先的两个顶点插值的高度，大概率是不一样的，这种情况被称为T-junction）。在实践中，参数化过程中的这些小重叠算不上真正的问题，所以我们没有选择修复输入，而是将输出的这些问题报告给美工，让他看是不是会产生artifact，如果会，那么就让他手动修。

第二种情况，在划分簇时增加凸包性指标的权重可以防止这些错误。所以我解决这个问题时并没有做任何事，但它确实不是个问题了。

这样之后我们依然还有一些有问题的情况。我注意到Blender中的实现没有这些问题，还处理的十分优雅。所以我问了Brecht Van Lommel，他建议我使用基于LSCM的ABF公式的替代矩阵权重(alternate matrix weights)，并且这看上去确实解决了这些问题。

尽管LSCM非常容易实现，它肯定不是最好的方法。如果我打算实现一些更好的方法，我可能会选择[LinABF](http://alice.loria.fr/index.php/publications.html?Paper=LinABF@2007)或者[Fitting to Guidance Gradient Fields](http://mgarland.org/files/papers/param.pdf)。然而，因为现在参数化的步骤是最快的，所以也可能可以研究更昂贵的变形分析方法(expensive deformation analysis methods)。

## 打包

我们的打包算法相对简单。和其他很多实现一样，我们首先按参数化面积排序图表，旋转它们适应最佳矩阵并对齐，用贪心算法一张张插入图集(atlas)。理想情况下我应该测试四种可能的方向，但是目前我只是简单地随机选择其中一个方向。

我没有使用类似于俄罗斯方块的方案来找到每个图表的最佳位置，反而用了一种更加暴力的方法，这种方法会考虑所有可能的位置。我用一个保守的光栅化渲染器实现它，用tag标记图表覆盖的所有纹理上的像素，另外加上一个额外的像素作为填充。在新图表被插入时，我激进地增加了纹理尺寸。如果插入时能找到可容纳的位置，就直接插入到那里，否则通过评估一个指标来找到增加尺寸最少的位置来插入。由于我使用了贪心算法，单纯地最小化面积会导致图集地宽高比会非常大，所以我选择的指标结合了尺寸和周长，能得到最接近正方形的图集。

这里是一些结果的举例：

![packing_cottage00](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/5/packing_cottage00.png)

![packing_tower00](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/5/packing_tower00.png)

如果我们使用了lightmap压缩，将图表和DXT块边界对齐可能是有意义的，以防止渗色(bleeding)。

## 未来的提升

这是我认为还有很多提升空间的领域之一。但与此同时，但是投入更多的时间提升效果的性价比（译：!/$是性价比啊，感谢ds）并不高。尽管目前还没有在生产环境中实际测试过，我感觉我们现在的解决方案已经相当不错了。更大的图表有更小的失真和更少的缝隙当然很好，我也很乐意将工作投入这些方面。但是这不会让游戏跑得更快或看上去戏剧性般的更好。我们打算发布这些算法的源码，所以我期待社区开发者能进一步提升它（译者：在哪呢？）。

如果要我说哪个领域值得研究，我认为是信号专用参数化(signal specialized parameterizations)的使用。这个主题的论文（[Signal-specialized parametrization](http://research.microsoft.com/en-us/um/people/hoppe/proj/ssp/)和[Signal-specialized parameterization for piecewise linear reconstruction](http://research.microsoft.com/en-us/um/people/hoppe/proj/ssplinear/)）对我们而言有些杀鸡用牛刀了，并且我也不能保证对于我们的低分辨率模型，它会有很好的效果。

《半条命2》中实现了艺术家手动指定不同表面的采样率，不过我认为使用类似于 [棒鸡提出的方法](http://www.bungie.net/images/Inside/publications/presentations/Lightmap_Compression_2008_02_22.pptx)来自动化这件事是值得一试的。这看上去相对简单并且能提供使用复杂的方法能得到的大部分的效果。

我预期目前的实现不会再经历什么特别大的改变了，除了一些小的调整用以解决一些将来可能会出现问题。如果有人对这类算法有经验，我很乐意听到你的分享。特别是我想知道是不是有什么地方你实现的方法不一样，或者你认为有什么被我忽视而你认为值得考虑的优化和提升。
