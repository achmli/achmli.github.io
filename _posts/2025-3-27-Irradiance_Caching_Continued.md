---
layout:       post
title:        "《见证者》引擎技术博客——Irradiance缓存 续"
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
> 这篇并没有发布在见证者的博客上，但是吹哥在博客上发了链接。估计这个时候Ignacio Castaño已经跳槽去最大的显卡公司了？还是说见证者对他来说只是兼职罢了，不然为什么他那时候发明的alpha mipmap技术就已经在最大的显卡公司的官方接口里了。
>
> 博客链接：http://the-witness.net/news/category/engine-tech
>
> 原文链接：[the conclusion of his series on irradiance caching](http://www.ludicon.com/castano/blog/2014/07/irradiance-caching-continued/)
>
> 以及这篇文章他们惊人地发布了代码。
>
> 代码链接： [the source code of our implementation](https://gist.github.com/castano/5f7c8847f82e45cb56d0)
>
> 作者：Ignacio Castaño

看来我已经养成了开一个系列然后写完第一篇就弃坑的习惯。我几年前写的irradiance caching的第二部分在哪？我是时候结束它了，在我开下一个新坑之前。

在最后一部分中，物品打算详细阐述我们的记录替换策略(Record Replacement strategy)。核心思想是使用irradiance梯度来控制记录密度。这里面没什么新的东西，在[Making Radiance and Irradiance Caching Practical](http://dcgi.felk.cvut.cz/publications/2006/krivanek-egsr-mricp)中，Krivanek等人也提出了基于irradiance变化率的记录分布。

但是，有趣的现象是，梯度的幅度(the scale of the gradient)并不关键，我们对变化最关心的是变化率，也就是二阶的微分。当一个采样点的梯度值很小，而它相邻的采样点的梯度值很大，这说明这两个采样点的irradiance发生了突变，因此可能需要在他们之间插入一些些新的采样点。

在构建我们自己的记录分布时，我实现这个的方法是类似于上面的论文中描述的"neighbor clamping"算法。当一个新的记录插入到cache中，我查找邻近的记录，并且如果它们的梯度值有着显著的差异，我会缩小记录的覆盖范围以避免重叠，并且留出在它们之间插入采样点的空间。下面的图片展示了应用这个策略的结果，你能将鼠标悬停在上面查看具体的记录它们的半径.

![neighbor_clamping_01](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/10/neighbor_clamping_01.jpg)
![neighbor_clamping_02](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/10/neighbor_clamping_02.jpg)

左侧展示的是仅使用球面分割启发式方法(split sphere heuristic)，梯度幅度决定了记录的位置和半径。右侧则展示了我使用的方法，基于梯度的差调整记录幅度。你能看到左侧会因为记录过大而忽视墙面的遮挡，结果就是分布过于系数，并且产生不稳定的(choppy)的结果。这些artifact可以通过增加全局记录幅度来消除，但是在相同的采样数的情况下，图片右边产生了更加准确的结果。

我也可以深入讲解更多的实现细节，但是如果你实现过Krivanek的记录替换策略并且对neighbor clamping很熟悉，我希望这个改进方案会相对直观。回想当初我实现这些算法的时候，我就失去了描述更多细节的动力。因为这些技术，以及我做的这些提升由于这篇新发布的论文[Practical Hessian-Based Error Control for Irradiance Caching](http://zurich.disneyresearch.com/~wjarosz/publications/schwarzhaupt12practical.html)（译：链接挂了捏）变得过时了。

这篇论文提出了一种新的半球积分计算方案来估算irradiance梯度。他们的核心思想是将半球采样（颜色和深度）转换到三角形环境(triangulated environment)，在积分产生出相同的irradiance时。这种三角化具有任意性，这意味着他们的方法适用于任意的采样分布而不需要[像我之前的文章](https://zhuanlan.zhihu.com/p/30265118810)一样重新推导公式。更进一步来说，他们的方法不仅适用于估算irradiance梯度，也能用于求解Hessian(求解Hessian矩阵吧大概)，这使得它们能够直接基于irradiance的二阶导来引导记录分布，不需要像我的实现一样在一个原始的分布的基础上做修正。

尽管我也很想改用这个方法，但是我们的方法的效果已经足够好了，没有再投入更多资源转向其他方案的余裕了。如果有一个可用于参考的实现，或许就是另一个故事了。所以，我决定[发布我们的实现的代码](https://gist.github.com/castano/5f7c8847f82e45cb56d0)。

在[hemicube.h](https://gist.github.com/castano/5f7c8847f82e45cb56d0#file-hemicube-h)中，你能看到持有用于加速半立方体积分的预计算数据的数据结构。[hemicube.cpp](https://gist.github.com/castano/5f7c8847f82e45cb56d0#file-hemicube-cpp)则展示了这些数据是怎么计算出来的，最后[hemicube_integrate.cpp](https://gist.github.com/castano/5f7c8847f82e45cb56d0#file-hemicube_integrate-cpp)展示了怎么使用预计算数据高效地执行半立方体积分并计算irradiance梯度。
