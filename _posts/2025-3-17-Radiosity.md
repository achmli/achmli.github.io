---
layout:       post
title:        "《见证者》引擎技术博客的扩展阅读——辐射度算法"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - 《见证者》博客翻译
    - 图形学
---
> 这篇是在半立方体渲染和积分那篇中提到的Hugo Elias的文章。
>
> 实际上那几篇文章我个人最大的疑惑就是半立方体渲染到底是个什么东西。
>
> 这篇文章有人翻译，但是图全都挂了。之前那篇文章中贴的原文的链接也挂了。所幸原文并没有在互联网上完全消失。
>
> 接下来依然是叠甲。这是古早的技术，大概率不能帮助到现在的游戏开发。当然如果能真的启发到您那是再好不过了，然而比起我这不如AI的翻译，更建议看原文捏。这篇大部分还都是在喝了酒头有点痛的情况下翻的。
>
> 这两天看了下我的爱抖露之一的KillerAery的surfel gi的博客，才惊人地知道surfel gi也是基于radiosity的。
>
> 原文链接：[TGLTLSBFSSP: Radiosity](https://www.jmeiners.com/Hugo-Elias-Radiosity/)
>
> 作者：Hugo Elias
>
> 老前辈的翻译的链接：[辐射度算法详解-CSDN博客](https://blog.csdn.net/pizi0475/article/details/7933752?utm_medium=distribute.pc_relevant.none-task-blog-2~default~baidujs_baidulandingword~default-0-7933752-blog-100211943.235^v43^pc_blog_bottom_relevance_base4&spm=1001.2101.3001.4242.1&utm_relevant_index=3)

光照和阴影投射算法可以非常粗略的分成两类：直接光照和全局光照。许多人对前者以及相关的问题会比较熟悉。本文将对两种方法做一些简要的探讨，然后对一种全局光照的方法给出深入的研究。

## 直接光照

直接光照是老派的渲染引擎比如3D Studio和POV等使用的主要的光照方法。一个场景由两种类型的实体组成：物体和光源。光源可以将光线投射到物体上，除非投射的路径上有另一个物体，这种情况下会留下阴影。

### 直接光照的优缺点

|                         | 优点                                                                             | 缺点                                               |
| ----------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------- |
| `<b>`光线追踪`</b>` | 无论是数学描述的物体还是多边形的网格体都能渲染<br />可以用来做一些很酷的体积特效 | 速度慢<br />非常锐利的阴影和反射                   |
| `<b>`阴影体积`</b>` | 可以用来实现软阴影                                                               | 很难实现<br />非常锐利的阴影<br />只支持多边形网格 |
| `<b>`Z-Buffer`</b>` | 易于实现<br />快，能实时渲染                                                     | 锐利的阴影还伴随有走样的问题                       |

| ![cuisine_t](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/cuisine_t.jpg) | ![g002hi_t](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/g002hi_t.jpg) | ![silver_chess_b_t](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/silver_chess_b_t.jpg) |
| -------------------------------- | ------------------------------ | ---------------------------------------------- |

需要考虑的最重要的是，尽管这些方法可以生成超现实的图像，但他们只能处理那些只有点光源并且物体都是完美的镜面反射或者漫反射的场景。除非你是地主家的傻儿子，你的房子里大概不会全是点光源和完美的镜面反射的球。实际上，除非你生活在另一个物理规律完全不同的宇宙，不然你的房子里基本上不会有任何超级锐利的阴影。

人们通常会声称光追器和一些其他的渲染器会生成“照片级真实”的图像。但想象一下如果有人给你看一张典型的光追生成的图像，然后对你说这是一张照片，你大概会说那个人是瞎了。

另外还要注意，在真实世界中，那些没有被直接照射的物体依然是可见的，阴影也不会是完全的黑色。直接光照的渲染器依靠添加氛围光(Ambient Light)项来处理这种情况。所以所有物体都接收一个最低限度的单项光。

## 全局光照

全局光照尝试去克服光线追踪相关的一些问题。光追仅模拟光线在漫反射表面的一次反射。全局光照的渲染器模拟光线在场景中的许多次反射。

每个在光线追踪场景中的物体为了能可以被看到必须被一些光源照亮，而在全局光照场景中的物体可以是只被周围环境照亮的。（译：这真的是我知道的光追吗？）

### 全局光照的优缺点

由全局光照生成的图像看上去会很有说服力。相比之下，老派的渲染器就只能产出悲伤的卡通。但是，这里必须有一个大写的但是，全局光照很慢。就像你整天放着你的光追器不管，让它独自渲染，然后你回来的时候会被它生成的图像震惊，全局光照的渲染器也是一样的。

|                       | 优点                                                                                 | 缺点                                                                                                       |
| --------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| 辐射度算法(Radiosity) | 对于漫反射表面有非常真实的光照<br />概念易于理解，程序容易实现<br />易于用3D硬件优化 | 慢<br />不擅长处理点光源<br />也不擅长处理镜面反射的表面<br />在资料中往往被讲得过于复杂又很少被很好地解释 |
| 蒙特卡洛方法          | 可以生成非常非常非常好的结果<br />可以很好地模拟几乎所有的光学现象                   | 慢<br />稍微有些复杂<br />优化的时候需要一些智慧<br />在资料中往往被讲得过于复杂又很少被很好地解释         |

### 用直接光照照亮一个简单场景

![room01t](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/room01t.jpg)

我在3D Studio中搭建了这个场景。我想要这个这个场景看上去像是被透过窗户的太阳光照亮。

所以我设置了一个聚光灯照射进来。这时我渲染时，除了地板上被照亮的两块，整个房间都是近乎黑色的。

将氛围光加强也仅仅是让房间呈现均匀的灰色，除了不均匀的红色地板和光斑。

在房间的中央添加点光源可以照亮更多细节，但房间中不会有那种阳光充满房间的明亮光芒。

最后我将背景设置为白色，来呈现明亮的天空。

### 用全局光照照亮一个简答的场景

![room01r](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/room01r.jpg)

我在我自己的辐射度算法的渲染器中搭建了相同的场景。为了提供光源，我用[Terragen](https://www.jmeiners.com/web/20130114040312/http://www.planetside.co.uk/)渲染了一张天空的图像，并且将它放置在窗户外面。没有使用其他的光源。没有做其他多余的事情，房间的光照看上去就已经很真实了。

有一些有趣的地方值得注意:

+ 整个场景都被照亮并且可见，尽管有些表面背对着阳光。
+ 软阴影
+ 场景中左侧的墙的亮度是渐变的
+ 灰色的墙壁不再是灰色(?)，而是带有一些暖色调。天花板甚至可以说是稍微有一些粉色

## 辐射度算法渲染器的工作原理

首先清空你脑子所有知道的常规渲染方法。你过去的经验可能会误导你。

我现在假装再问一个阴影相关的专家，他会向你解释他知道这个科目的一切。我的专家是我面前的墙上的一小块油漆。（译：难道那个年代的人喜欢这种“幽默”吗）

`<b>`Hugo`</b>`：“为什么你在阴影中，而你附近和你很像的另一块尤其却站在光里？”

`<b>`油漆`</b>`：“你什么意思？”

`<b>`Hugo`</b>`：“你是怎么知道什么时候再阴影中，什么时候不在的呢？关于阴影投射算法你又知道什么呢？你只是一块油漆？”

`<b>`油漆`</b>`：“听好了伙计。我根本听不懂你在说什么。我所做的只有简单的一件事，那就是任何光照射到我的时候，我把它散射回去。“

`<b>`Hugo`</b>`：“任何？”

`<b>`油漆`</b>`：“对，任何光照。我不偏食。“

所以现在你知道了辐射度算法的基本前提。任何光线打到表面上，都会被反射回场景中。这里提到的任意光线，不只是从光源来的那些光线。任意光线。这就是现实中的油漆的思考方式，也是辐射度算法的渲染器的工作方式。

在我的下一篇文章中，我会讲解怎么制作会说话的油漆（译：？）。

因此，辐射度算法的基本原理就是移除光源和物体的区别。现在你要想象所有的一切都是潜在的光源。

任意一个可见的能发光或者能反射都是光源。你能看到的一切都是光源。所以当我们思考有多少光到达场景中的任意一部分时，我们必须小心地将来自所有可能的光源的光都累加起来。

## 基础前提

1. 光源和物体没有区别。
2. 场景中的一个表面被场景中所有对它可见的部分照亮。

## 一个简单的场景

![2viewsb](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/2viewsb.gif)

我们先从一个简单的场景开始：一个有三个窗户的房间。有一对柱子和一些壁龛，用来提供有趣的阴影效果。

它会被窗外的场景照亮，我暂时假设窗外除了有一个又小又亮的太阳外一片漆黑。

![view03b](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/view03b.gif)

然后选择房间中的一个表面，并且思考它上面的光照。

![view05bb](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/view05bb.gif)

与许多其他计算机图形学中的难题一样，我们将它划分为许多（油漆的）小块（patches(of paint)），并且尝试着从他们的视点看这个世界。从现在开始我会把这些油漆块简单地成为块。

![view06bb](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/view06bb.gif)

选择这些块中的一个。然后想象你就是这个块。在这个视角下世界看上去会是什么样的呢？

![fisheye8](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/fisheye8.gif)

非常小心的将眼睛放到这个块上，我就能看到它所能看到的了。房间非常黑，因为目前还没有光进入。但我为了方便你们查看把边缘勾勒出来了。将能看到的所有光照叠加起来，我们就能计算出场景中所有到达这个块的光照的总量了，我会把它称为总入射光（total incident light）。

这个块只能看到房间和外面的黑暗。叠加所有的入射光，我们能看到没有光到达这里。这个块依然是黑色的。

![fisheye7](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/fisheye7.gif)

挑选一个柱子上更低位置的块。这个块可以看见窗外明亮的太阳。这一次，将所有的入射光叠加起来，就能看到有大量的光到达这里（尽管这个太阳看上去非常小，但是非常亮）。这个块就被照得明亮了。

![view10](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/view10.gif)

为柱子上所有的块重复这个过程，并且每次都叠加所有的入射光，我们可以重新看向柱子，查看光照是什么样的。

那些靠近柱子顶部的块，不能看到太阳，所以再阴影中。而有一些由于遮挡只能再窗户边缘看到部分的太阳的，则是被照得半亮，有点昏暗。还有的则是被完全照亮。

辐射度算法以大致相同的方向运行。正如你能看到的，阴影在场景中不能看到光源的部分自然而然地出现了。

![view11](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/view11.gif)

第一个pass之后整个房间的光照。

对场景中每个块重复这个过程，就能得到这个场景，除了能接收到太阳的光照的表面，一切都是漆黑的。

这看上去并不是一个被很好地照亮的场景。忽略掉光照看上去呈块状（锯齿状）的事实，我们可以通过划分更多的块来优化这一点。更重要的是除了能看到太阳的区域，其余所有地方都是完全黑暗的。到目前为止，相对于其他的渲染器没有任何提升。所以，一切都还没有结束。目前房间中的一些部分已经被照亮了，它们自身就已经是光源了，所以可以很好地将光投射到场景中的其它部分。

![fisheye10](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/fisheye10.gif)

看不到太阳的块，再上一个pass接收不到任何光照，现在可以看到其他表面上闪烁的光了。所以在这个pass结束的时候，这个块会比现在完全漆黑的样子要稍微亮一些。

![view12](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/view12.gif)

这一次当你计算场景中的每个块的入射光，许多之前是漆黑的块现在被照亮了。这个房间开始有一个更加有现实感的外观了。发生的事情就是太阳光在地板和墙面上反射了一次，到达了其他的表面上。

![view13](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/view13.gif)

第三个pass生成了光线在场景中反射了两次的效果，一切看上去都是相同的，只是稍稍变得更加明亮。

![view14](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/view14.gif)

这是第4个pass的效果。

![view15](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/view15.gif)

这是第16个pass的效果。

## 算法的更多细节：块

### 发光量(Emission)

虽然我说了我们把光源和物体看作基本上是一样的，但是场景中必须有一些光源。在现实世界中，有些物体是会发光的，而又一些不会，并且所有物体都会一定程度上吸收光。我们必须将场景中能发光的和不能发光的部分区分开。在辐射度算法中，我们通过假设所有块都发光来处理这个问题，只不过大多数块的发光量为0。块的这个属性，我们称之为 `emission`。

### 反射度(Reflectance)

当光打到一个表面，一些光会被吸收并且变成热。而其余的则是被反射。我将一个块反射光的比例称为 `reflectance`。

### 入射光和出射光(Incident and Excident Light)

在每个pass中，都有必要记录两个其他的值。每个块能有多少光到达和每个块有多少块离开。我将这两个值称为 `incident_light`和 `excident_light`。其中出射光是块的衡量可见性的属性。当我们看向一个块时，出射光就是我们能看到的东西。

```cpp
incident_light = sum of all light that a patch can see;
excident_light = (incident_light*reflectance) + emmision;
```

### 块的数据结构

现在我们了解了一个块所有必要的属性，是时候定义一个块了。稍后我会解释这四个变量的细节。

```cpp
struct Patch
{
    emission;
    reflectance;
    incident;
    excident;
};
```

## 伪代码：第一级

现在我已经解释了算法的基础知识，接下来我会用伪代码的形式，使其具体化。当然这已然是非常靠近顶层的设计，不过之后我会解释更多的细节。

```pseudocode
load scene

  divide each surface into roughly equal sized patches


  initialise_patches:
  for each Patch in the scene
    if this patch is a light then
      patch.emmision = some amount of light
    else
      patch.emmision = black
    end if
    patch.excident = patch.emmision
  end Patch loop
  


  Passes_Loop:

  each patch collects light from the scene
  for each Patch in the scene
    render the scene from the point of view of this patch
    patch.incident = sum of incident light in rendering
  end Patch loop


  calculate excident light from each patch:
  for each Patch in the scene
    I = patch.incident
    R = patch.reflectance
    E = patch.emmision
    patch.excident = (I*R) + E
  end Patch loop

  Have we done enough passes?
    if not then goto Passes_Loop
```

### initialise patches

`<em>`初始化块`</em>`：在最初，除了能自发光的块之外，其余所有的块都是漆黑的。那些能够自发光的块用一些 `emission`的值初始化，这些值已经由场景指定了。其余的所有块这个值都设置成0，也就是黑色。

### Passes Loop

代码需要多次重复这个循环，这对于在场景中产生可接受的光照是必要的。每多一次循环，代码能模拟光在场景中多反射一次的效果。

### each patch collects light from the scene

`<em>`每一个块从场景中收集光照`</em>`：正如我之前在文章中解释的，每个块被周围它能看到的部分照亮。这是通过在这个块所造的视点渲染场景实现的，并且将能它看到的光叠加起来。在下一节我会更加详细地讲解这部分。

### calculate excident light from each patch

`<em>`计算每个块的出射光`</em>`：已经计算出了每个块会有多少光到达，我们就能计算出每个块有多少光会离开了。这个过程需要被循环许多次才能获得好的效果。如果渲染器需要一个新的pass，就跳回到Passes Loop这一步。

## 实现辐射度算法：半立方体

实现辐射度算法的第一个要解决的问题，就是怎么从每个块的视点去渲染世界。在之前的部分中，我用一个鱼眼的视角来表示一个块的视野中的场景，但是这样做既不容易也不实用。有一种好得多的方法，那就是半立方体！

### 半球

![hemisph1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/hemisph1.gif)

想象一个被半球包裹的鱼眼镜头。在块（上图中红色的部分）上放置一个半球，从这个块的视点，场景被包裹在一个半球中看上去就和从这个视点看这个场景差不多，没什么差别。

将一个相机放在半球的中央，你能看到的就和你其他方法渲染的场景几乎一样，如下图。

![in_sphr](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/in_sphr.gif)

如果你能找到一种轻松地渲染鱼眼镜头的方法，就能将每个像素的亮度叠加用来计算这个块的总入射光了，但是渲染鱼眼镜头是困难的，所以我们必须找到其他的方法来计算入射光。

### 半立方体

![hemicub1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/hemicub1.gif)

令人震惊（但也没那么令人震惊，取决于你的数学水平），半立方体和半球在相同的视点看上去是一样的！

![in_cube](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/in_cube.gif)

### 展开半立方体

![fold_2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/fold_2.gif)

想象着将半立方体展开。你还剩下什么呢？一个正方形的图像和四个矩形的图像。中间的正方形图像是从块的视点向正前方渲染的图像。而半立方体其余的四部分分别是将视野方向向上、向下、向左和向右旋转90°。

所以通过将相机放在块的位置，你能很轻松地渲染这些图像，只要将相机的朝向分别向前、向上、向下、向左和向右然后渲染就行。四个边上的图像是被切掉一般的，所以，只需要渲染一半就行了。

## 半立方体图形的补偿

![3_balls](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/3_balls.gif)

这一张包含三个球的图像，使用90°的FoV。三个球离相机的距离是相同的，但由于透视投影的特性，靠近图像边缘的物体看上去被拉伸了，会比图像中间的物体看着要大一些。

如果这就是半立方体中间的图像，并且三个球是光源，这样的话靠近图像边缘的光源就会向块投射更多的光，而且会比它应该投射的光要多。这时光照就不准确了，所以我们必须对此做出一些补偿。

如果你尝试用一个半立方体去计算一个块上的总入射光，并且只是将半立方体上渲染的所有像素的亮度叠加，你就要用一个可能不合理的权值给到那些在图像边角的物体上。它们会投射过多的光到块上。

为了补偿这个，对在边角的像素做一个除法是有必要的，这样所有的物体对入射光的贡献会是平等的，无论他们在半立方体中的什么地方。

比起给出一个详细的解释，我更倾向于讲解具体应该怎么做。

![hemicomp](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/hemicomp.gif)

每个半球立方体表面像素需乘以"摄像机视线方向与相机到像素的方向的夹角"的余弦值(Pixels on a surface of the hemicube are multiplied by the cosine of the angle between the direction the camera is facing in, and the line from the camera to the pixel. 译：直接复制了ds的翻译，这句话总感觉又歧义，可能还是我英语水平太糟糕了)。

上图就是用于补偿失真的映射。

### Lambert的余弦定律(Lambert's Cosine Law)

![lambert01](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/lambert01.gif)

任何一个即使是初出茅庐的图形程序员都知道Lambert余弦定律：表面的亮度与表面法线和光照方向的夹角的余弦值成正比。因此在这里我们应该应用相同的定律。这一步只是简单地将半立方体上的像素与相关的数值相乘。

上图是将lambert余弦定律应用到半立方体上的映射。

### 将两者结合：乘数映射

现在集中注意力，这很`<b>`重要`</b>`：

将两个映射图逐像素相乘得到这个。这个映射对于生成一个精确的辐射度算法的解决方案是至关重要的。这是用来调整透视投影产生的失真的，上文中已经提过了，这会导致半立方体边角位置的物体会投射过多的光到块上。他还将Lambert余弦定律带了进来。

在创建了这张贴图之后，在中心的值应该是1.0，而在远处的角落，这个值应该是0.0。

在使用这张帖图之前，应该将其归一化：贴图中所有像素的总和应该是1.0。

将乘数映射图中的所有像素的值相加得到它们的总和。然后每个像素的值除以这个总和。当然这时候，贴图中央的值会远小于1.0。

![3hemis](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/3hemis.gif)

## 计算入射光

```pseudocode
  procedure Calc_Incident_Light(point: P, vector: N)  

    light TotalLight
    hemicube H, R, M
    H = empty
    M = Multiplier Hemicube
    R = empty

    div = sum of pixels in M

    camera C
    C.lens = P

    C.direction = N
    H.front = RenderView(C, N, Full_View)

    C.direction = N rotated 90° down
    H.down = RenderView(C, N, Top_Half)

    C.direction = N rotated 90° up
    H.up = RenderView(C, N, Bottom_Half)

    C.direction = N rotated 90° left
    H.left = RenderView(C, N, Right_Half)

    C.direction = N rotated 90° right
    H.right = RenderView(C, N, Left_Half)

    multiply all pixels in H by corresponding
    pixels in M, storing the results in R

    TotalLight = black

    loop p through each pixel in R
      add p to TotalLight 
    end loop
  
    divide TotalLight by div

    return TotalLight
  end procedure
```

这个程序选取了场景中的一个点（通常是一个块），沿着发现方向，并且计算到达这个点的光的总数。

首先它使用了函数**RenderView**(point, vector, part)渲染半立方体的五个面。函数的参数，`point`是相机的位置、`vector`是相机应该指向的方向，而另一个参数则用于告诉函数应该渲染最终的图像中的哪一部分。这五张半立方体的图像的存储的结构称为`<b>`H`</b>`（下图中最左侧的一列）。

在半立方体`<b>`H`</b>`渲染完成后，它就要与乘数映射图的半立方体`<b>`M`</b>`（下图中的中间一列）相乘，并且将结果存储在半立方体`<b>`R`</b>`（下图中最右侧的一列）中。

![hemis](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/hemis.gif)

### 伪代码中变量类型的解释

`<b>`light`</b>`：用于存储任意的光照值。例如：

```pseudocode
  structure light
    float Red
    float Green
    float Blue
  end structure
```

`<b>`hemicube`</b>`：用于存储场景中一些点的视点出发下的场景的图像。一个半立方体由5张图像组成，正如上图中绘制的，其中每个像素都是一种光。如果是乘数图的半立方体，用于存储乘数的值而不是光照的值，也在上图中绘制了。

```pseudocode
  structure hemicube
    image front
    image up
    image down
    image left
    image right
  end structure
```

`<b>`camera`</b>`：例如：

```pseudocode
  structure camera
    point  lens
    vector direction
  end structure
```

## 提高解决方案的准确度

你可能会思考：“淦！这看起来需要大量渲染，这种方法下处理器的负载简直高到要爆炸！”你是对的，你必须啊渲染一张用于映射场景的纹理成千上万次，而这个成千上万次你可能也要重复很多次。

所幸有些事从时间的开始人类就一直在做。自从光栅显示器诞生之初，就有许多尽可能快地将渲染影射了场景的纹理的工作。我不打算在这篇文章中讲述有关这部分内容的过多的细节，我肯定不是谈论渲染优化的最佳人选。我自己的渲染器慢到你可能想要问候它。这个算法本身就适合用显卡优化，尽管你可能需要做一些调整和裁剪才能使它渲染 3*32 位的纹理。

我在这篇文章中打算讨论的速度的优化并不关心每个半立方体渲染的时间，而是减少需要渲染的半立方体的数量。你可能已经注意到了，上面的图中渲染的光照有些锯齿存在，由于低分辨率。别怕，它们的分辨率可以提升到任何你想要的程度。

![red_outline](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/red_outline.jpg)

看一下上图红色框中的表面。上面的光照基本上非常简单，存在亮的区域和暗的区域，而它们之间有一条锐利的边缘将它们分开。要精确地重现这种锐利的边缘，你一般需要一张极高分辨率的lightmap，以及相应地，需要渲染非常多的半立方体。但是为了填充几乎只是纯色的明亮或者较暗的区域而渲染如此多的半立方体怎么看都是不太划算的。更好的方法是在锐利的边缘渲染更多的半立方体，而在其他区域只渲染较少的半立方体。

很好，这时可行的，并且方法也很直接。我在下文中描述的算法现在表面上分散地渲染较少的半立方体，然后再边缘的附近渲染较多的半立方体，并且用线性插值填充lightmap种剩余的部分。

### 算法

左侧的图中左边的部分展示了过程中生成的lightmap，右边红色标记表示通过半球立方体计算的像素，绿色表示线性插值得出的像素。右侧的图则是放大的计算过程。

| ![adap1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/adap1.gif) | ![grid1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/grid1.gif) |
| ------------------------ | ------------------------ |

每4个像素渲染一个半立方体。

| ![adap2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/adap2.gif) | ![grid2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/grid2.gif) |
| ------------------------ | ------------------------ |

第一类Pass：检测像素，找到上一步的找到的两个垂直或者水平相邻的像素之间的中间的像素，如果两个像素之间的差大于设定的阈值，那就在中间的像素渲染一般半立方体，如果小于阈值，那就用两个像素的线性插值计算这个像素的值。

| ![adap3](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/adap3.gif) | ![grid3](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/grid3.gif) |
| ------------------------ | ------------------------ |

第二类Pass：检测像素，找到四个已经有值的像素中间位置的像素，如果这四个像素的值差异较大，就在这个中间像素渲染半立方体，否则就双线性插值计算出这个像素的值。

| ![adap4](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/adap4.gif) | ![grid4](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/grid4.gif) |
| ------------------------ | ------------------------ |

重复第一类Pass，但是间隔减半。

| ![adap5](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/adap5.gif) | ![grid5](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/grid5.gif) |
| ------------------------ | ------------------------ |

重复第二类Pass，但是间隔减半。

从左侧贴图可见，大部分光照贴图通过线性插值生成。事实上，总共有1769个像素，只有563个是通过渲染半立方体计算的，其余的1206个都是通过插值得到的。由于渲染半立方体需要大量的时间，远超过可忽略的插值时间，所以该方法实现了约60%的速度提升！

目前这个算法依然不够完美，它偶尔会在lightmap中遗漏掉一些小细节，但在大多数情况下，它的表现都非常好。也有能用于帮助它捕获小细节的简单的方法，但这就留给你自行去探索吧。

```pseudocode
####  CODE EDITING IN PROGRESS - BIT MESSY STILL ####

 float ratio2(float a, float b)
 {
     if ((a==0) && (b==0))    return 1.0;
     if ((a==0) || (b==0))    return 0.0;

     if (a>b)    return b/a;
     else        return a/b;
 }

 float ratio4(float a, float b, float c, float d) 
 {
     float q1 = ratio2(a,b);
     float q2 = ratio2(c,d);

     if (q1<q2)    return q1;
     else          return q2;
 }


 procedure CalcLightMap()

 vector  normal = LightMap.Surface_Normal
 float   Xres   = LightMap.X_resolution
 float   Yres   = LightMap.Y_resolution
 point3D SamplePoint
 light   I1, I2, I3, I4

 Accuracy = Some value greater than 0.0, and less than 1.0.  
            Higher values give a better quality Light Map (and a slower render).
            0.5 is ok for the first passes of the renderer.
            0.98 is good for the final pass.

 Spacing = 4     Higher values of Spacing give a slightly faster render, but
                 will be more likely to miss fine details. I find that 4 is
                 a pretty reasonable compromise. 


 // 1: Initially, calculate an even grid of pixels across the Light Map.
 // For each pixel calculate the 3D coordinates of the centre of the patch that
 // corresponds to this pixel. Render a hemicube at that point, and add up
 // the incident light. Write that value into the Light Map.
 // The spacing in this grid is fixed. The code only comes here once per Light
 // Map, per render pass. 

 for (y=0; y<Yres; y+=Spacing)
     for (x=0; x<Xres; x+=Spacing)
     {
         SamplePoint = Calculate coordinates of centre of patch
         incidentLight = Calc_Incident_Light(SamplePoint, normal)
         LightMap[x, y] = incidentLight
     }

 // return here when another pass is required
 Passes_Loop:
     threshold = pow(Accuracy, Spacing)


     // 2: Part 1.
     HalfSpacing = Spacing/2;
     for (y=HalfSpacing; y<=Yres+HalfSpacing; y+=Spacing)
     {
         for (x=HalfSpacing; x<=Xres+HalfSpacing; x+=Spacing)
         {
             // Calculate the inbetween pixels, whose neighbours are above and below this pixel
             if (x<Xres)    // Don't go off the edge of the Light Map now
             {
                 x1 = x
                 y1 = y-HalfSpacing

                 // Read the 2 (left and right) neighbours from the Light Map
                 I1 = LightMap[x1+HalfSpacing, y1]
                 I2 = LightMap[x1-HalfSpacing, y1]

                 // If the neighbours are very similar, then just interpolate.
                 if ( (ratio2(I1.R,I2.R) > threshold) &&
                      (ratio2(I1.G,I2.G) > threshold) &&
                      (ratio2(I1.B,I2.B) > threshold) )
                 {
                     incidentLight.R = (I1.R+I2.R) * 0.5
                     incidentLight.G = (I1.G+I2.G) * 0.5
                     incidentLight.B = (I1.B+I2.B) * 0.5
                     LightMap[x1, y1] = incidentLight
                 }
                 // Otherwise go to the effort of rendering a hemicube, and adding it all up.
                 else
                 {
                     SamplePoint = Calculate coordinates of centre of patch
                     incidentLight = Calc_Incident_Light(SamplePoint, normal)
                     LightMap[x1, y1] = incidentLight
                 }
             }
           

             // Calculate the inbetween pixels, whose neighbours are left and right of this pixel
             if (y<Yres)    // Don't go off the edge of the Light Map now
             {
                 x1 = x-HalfSpacing
                 y1 = y
            
                 // Read the 2 (up and down) neighbours from the Light Map
                 I1 = LightMap[x1,y1-HalfSpacing];
                 I2 = LightMap[x1,y1+HalfSpacing];

                 // If the neighbours are very similar, then just interpolate.
                 if ( (ratio2(I1.R,I2.R) > threshold) &&
                      (ratio2(I1.G,I2.G) > threshold) &&
                      (ratio2(I1.B,I2.B) > threshold) )
                 {
                     incidentLight.R = (I1.R+I2.R) * 0.5
                     incidentLight.G = (I1.G+I2.G) * 0.5
                     incidentLight.B = (I1.B+I2.B) * 0.5
                     LightMap[x1,y1] = incidentLight
                 }
                 // Otherwise go to the effort of rendering a hemicube, and adding it all up.
                 else
                 {
                     SamplePoint = Calculate coordinates of centre of patch
                     incidentLight = Calc_Incident_Light(SamplePoint, normal)
                     LightMap[x1, y1] = incidentLight
                 }

             }//end if

         }//end x loop
     }//end y loop



     // 3: Part 2
     // Calculate the pixels, whose neighbours are on all 4 sides of this pixel
  
     for (y=HalfSpacing; y<=(Yres-HalfSpacing); y+=Spacing)
     {
         for (x=HalfSpacing; x<=(Xres-HalfSpacing); x+=Spacing)
         {
             I1 = LightMap[x, y-HalfSpacing]
             I2 = LightMap[x, y+HalfSpacing]
             I3 = LightMap[x-HalfSpacing, y]
             I4 = LightMap[x+HalfSpacing, y]

             if ( (ratio4(I1.R,I2.R,I3.R,I4.R) > threshold) &&
                  (ratio4(I1.G,I2.G,I3.G,I4.G) > threshold) &&
                  (ratio4(I1.B,I2.B,I3.B,I4.B) > threshold) )
             {
                 incidentLight.R = (I1.R + I2.R + I3.R + I4.R) * 0.25
                 incidentLight.G = (I1.G + I2.G + I3.G + I4.G) * 0.25
                 incidentLight.B = (I1.B + I2.B + I3.B + I4.B) * 0.25
                 LightMap[x,y] = incidentLight
             }
             else
             {
                 SamplePoint = Calculate coordinates of centre of patch
                 incidentLight = Calc_Incident_Light(SamplePoint, normal)
                 LightMap[x, y] = incidentLight;
             }
         }
     }


     Spacing = Spacing / 2
     Stop if Spacing = 1, otherwise go to Passes_Loop
```

## 点光源

![spotlight_b_05](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/spotlight_b_05.jpg)

通常认为辐射度算法不能很好的处理点光源。这在某种程度上是正确的，但是在场景中放置合理的点光源也并非不可能。我尝试在我的场景中添加一个明亮的，一个点大小的物体，并将其渲染为wu像素（译：什么东西？）。当渲染半立方体时，它们会作为明亮的点出现在半立方体中，从而将光投射到块上。这种方法基本上可行的，但是会产生一些让人无法接受的瑕疵。上图中的场景被三个点聚光灯光源照亮了，其中两个在柱子的背面，还有一个在左侧的顶部并指向相机。这个场景在这个角度看上去很不错，但如果旋转相机的角度，一些令人不快的瑕疵就会出现。

![spotlight_b_02](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/spotlight_b_02.jpg)

在上图中能看到，墙上和地面上出现了三条黑线。这是由于光源似乎在半立方体的边缘丢失了。如果数学计算完全精确且半立方体边缘完美匹配，情况或许不会如此糟糕，但我确信依然有一些注意得到的瑕疵会出现。

因此，相比于将点光源渲染到半立方体上，你最好还是用光追来处理点光源，将点光源的光投射到面片上。

## 用3D渲染硬件优化

辐射度算法的一个优点是，它可以很轻松地使用32位的3D渲染硬件来优化。只需要让硬件执行纹理映射就行，不需要着色、抗锯齿或者mipmap之类的其他的功能。

这种优化的实现方式可能和你想象的不太一样，但效果很好，能让CPU和GPU并行地工作。GPU处理纹理映射以及通过z-buffer移除被遮挡的表面。而CPU负责处理辐射度算法的其余部分（译：啊？这河里吗）。

据我所知，目前没有GPU能处理浮点光照值，甚至无法处理超过255的光照值（译：啊？）。因此试图让GPU直接渲染包含这种光照的场景没什么意义。但通过巧妙设计，可以让GPU执行纹理映射和和移除被遮挡的表面，通过一个简单快速的循环补回光照计算。

如果GPU可以向屏幕写入32位像素，那它就能写入表示我们需要的任何内容的32的值。3D硬件无法直接向屏幕写入浮点RGB值，但可以写入32位指针，指向应被渲染的块。完成后，只需读取每个像素的32位值作为地址，定位到对应的块。

![tex_flot](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/tex_flot.jpg)

上图展示了场景中的一个块的贴图。每个像素的红、绿、蓝通道均为浮点值，因此GPU无法直接处理。

![tex_pntr](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/tex_pntr.jpg)

这是另一张贴图。它看起来非常怪异，但暂时忽略其外观。图中每个像素实际上是一个32位值，对应上面的贴图中相应像素的地址。之所以显示颜色，是因为地址的最低三个字节被解析为颜色值。

![scn_ptr](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/9/scn_ptr.jpg)

一旦制作完成一整套指针纹理（场景中每个表面对应一张），即可交给GPU进行渲染。渲染出的场景会呈现类似上图的效果。

场景看起来非常奇怪，但能辨认出表面覆盖着类似上图的图案。这些像素不应被解析为颜色，而应视为指针。如果显卡使用32位纹理，其格式可能类似ARGB，其中A、R、G、B各占8位。忽略这种结构，将每个像素视为一个32位值。将它们作为内存指针，指向应当这个位置的块，从而正确重建场景。

重要提示：必须确保场景渲染仅采用纯纹理映射。这意味着：禁用线性插值、禁用抗锯齿、禁用运动模糊、禁用着色和光照、禁用Mipmap、禁用雾、禁用伽马校正或其他任何非直接纹理映射的功能。若不遵守此要求，生成的地址将指向错误位置，代码几乎必定崩溃。

这种优化辐射度计算的原理应已清晰。若仍有疑问，请告知，我将尝试进一步解释。

（译：这一段中的硬件感觉太古早了，很难说在今天这么写是合理的。这段翻译基本上照抄ds了，实在没有任何参考价值。）

## 误解与困惑

### 渲染完成后如何处理图像

辐射度渲染器的输出是一个图像，其中每个像素包含三个浮点数值，分别对应红、绿、蓝通道。该图像的亮度值范围可能非常广阔。如前所述，天空的亮度远高于室内普通表面的亮度。而太阳的亮度又是天空的数千倍。该如何处理这样的图像？

普通显示器最多只能发出微弱的光线，其亮度甚至不比室内表面高多少。显然无法直接在显示器上呈现这样的图像。要做到这一点，需要能发出太阳般亮度的显示器，以及每通道32位的显卡。这类设备目前不存在，技术问题暂且不论，安全性也成问题。那么我们能做什么？

大多数人似乎乐于接受照片作为现实的忠实再现。这种观点是错误的。照片在显示真实世界的高亮度图像方面并不比显示器强。照片无法发出太阳般的光亮，但人们从不质疑它们的真实性。此时困惑便产生了。

### 人类视觉

视觉是我们最重要的感官。我每天都依赖它保命，至今它从未让我丧生。它无数次拯救了我的性命和肢体。对我们的祖先而言，视觉同样至关重要——从最早的鱼类或其他进化源头便是如此。眼球经历了漫长的进化，对生存至关重要，因此它们已变得极其精妙。它们对极弱光敏感（人眼能感知的最暗闪光仅相当于5个光子），同时也能适应观察明亮的天空。眼球并非视觉的全部，更重要的是其背后的脑部处理。大脑是一个极度复杂、尚不为人完全理解的神经网络，通过多层处理将眼球输入转化为对前方真实存在的感知。大脑必须能在任何光照条件下识别相同物体，并出色地补偿不同光照环境的影响。当我们从阳光明媚的室外走进昏暗的黄光灯室内时，甚至察觉不到差异。若尝试在这两种环境下拍照，可能需要更换胶片类型以避免照片发黄或过暗。

尝试以下实验：在一个完全阴天走到室外，站在白色物体前。若望向云层，会看到它们呈灰色；但注视白色物体时，它仍呈现白色。这说明什么？白色物体受灰色云层光照，亮度不可能超过云层（实际会更暗），但我们仍将其感知为白色。若不信，可拍摄一张以天空为背景的白色物体照片，会发现白色物体比云层显得更暗。

不要相信你的眼睛：它们比你聪明得多。

那么我们能做些什么？既然人们愿意接受照片作为现实的再现，我们可以将渲染器的输出（即场景光线的物理模型）通过类似相机胶片的粗略近似进行处理。我已就此撰写过文章： [Exposure](https://www.jmeiners.com/web/20130114040312/http://freespace.virgin.net/hugo.elias/graphics/x_posure.htm)，此处不再赘述。

（译：这段同样照抄ds，基本是废话，没啥值得看的。）

## 参考文献

**[The Solid Map: Methods for Generating a 2­D Texture Map for Solid Texturing](https://www.jmeiners.com/web/20130114040312/http://graphics.cs.uiuc.edu/~jch/papers/pst.pdf)**

如果你想实现你自己的辐射度算法渲染器，这篇论文会非常有用。它探讨了如何将纹理映射均匀且无失真地应用到任意多边形物体表面——这正是辐射度渲染器需要解决的问题。

**[Helios32](https://www.jmeiners.com/web/20130114040312/http://www.helios32.com/)**

为寻求辐射度渲染功能的开发者提供跨平台解决方案。

**[Radiosity In English](https://www.jmeiners.com/web/20130114040312/http://www.flipcode.com/tutorials/tut_rad.shtml)**

如标题所示，这是一篇用英语词汇解释辐射度的文章。我并未理解其内容。

**[Real Time Radiosity](https://www.jmeiners.com/web/20130114040312/http://www.gamedev.net/reference/programming/features/rtradiosity2/)**

这听起来更有吸引力，但似乎没有提供Demo。

**[An Empirical Comparison of Radiosity Algorithms](https://www.jmeiners.com/web/20130114040312/http://www.cs.cmu.edu/~radiosity/emprad-tr.html)**

一篇优秀的技术文章，对比了矩阵法、渐进法和小波法辐射度算法，由该领域的权威专家撰写。

**[A Rapid Hierarchical Radiosity Algorithm](https://www.jmeiners.com/web/20130114040312/http://graphics.stanford.edu/papers/rad/)**

本文提出了一种快速层次化辐射度算法，用于包含大型多边形面片的场景光照计算。

**[KODI&#39;s Radiosity Page](https://www.jmeiners.com/web/20130114040312/http://ls7-www.informatik.uni-dortmund.de/~kohnhors/radiosity.html)**

汇集了大量优质的辐射度相关资源链接。

**[Graphic Links](https://www.jmeiners.com/web/20130114040312/http://web.tiscalinet.it/GiulianoCornacchiola/Eng/GraphicLinks6.htm)**

包含更多优质链接。

**[Rover: Radiosity for Virtual Reality Systems ](https://www.jmeiners.com/web/20130114040312/http://www.scs.leeds.ac.uk/cuddles/rover/)**

（*强烈推荐*）一篇关于辐射度的学位论文，收录了大量优质文章和该领域论文摘要。

**[Daylighting Design](https://www.jmeiners.com/web/20130114040312/http://www.arce.ukans.edu/book/daylight/daylight.htm)**

一篇关于自然光的深度研究文章。

（译：这段同样照抄ds，反正链接基本都挂了。）
