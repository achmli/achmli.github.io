---
layout:       post
title:        "《见证者》引擎技术博客——预计算光照"
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
>博客链接：http://the-witness.net/news/category/engine-tech
>  
> 原文链接：[Graphics Tech: Precomputed Lighting – The Witness](http://the-witness.net/news/2010/03/graphics-tech-precomputed-lighting/)
> 
> 作者：Jonathan Blow

在过去 15 年左右的时间里，游戏中的图形技术一直由射击游戏推动。大多数射击游戏通过大量动态灯光、大量使用凹凸贴图、移动阴影和粒子效果来在其场景中产生视觉趣味。

对于《见证者》，我想要开发一种更加重视简单的视觉风格，适用于相对柔和的环境，同时适用于室内和室外的场景。有一些全局光照的解决方案看上去能满足这个需求。

显然，完全实时的全局光照是效果最好最泛用的解决方案。我调研了提供这个功能的一些软件包，比如[Geomerics&#39; SDK](http://geomerics.com/)（译：网页已经打不开了）。但是这些解决方案都不约而同的使用大量的贴图空间，并且需要大量的处理时间（译：说实话我没有理解这里是每帧的渲染时间？还是烘焙贴图的时间？），而且它们的效果对这个游戏而言有些杀鸡用牛刀了——由于《见证者》是解谜游戏，基本上不会有很多可移动的光源。

所以，一些预计算的全局光照看上去是正确的选择。3D建模包有一些可以计算全局光照的插件，但是很难接口化，而且甚至离用于处理完整的游戏场景都还很遥远。唯一知道游戏世界中所有物体位于什么地方的只有游戏本身，所以开发我们自己的游戏内的全局光照系统看上去是最合适的。可以用radiosity(译：PRT之类的？不太了解这是什么)，也可以用蒙特卡洛路径追踪（译：啊？哦烘焙啊），但是[Charles Bloom](http://www.cbloom.com/)提出了一个简单的解决方案，那就是只需为lightmap中的每个像素渲染场景(just rendering the scene for every pixel in a lightmap，译：没太理解。)，这似乎是一个好主意。使用这种方法，就不必大费周章来使radiosity或者光线追踪与用于游戏场景的完全不同的实时渲染算法做匹配。光照传输使用相同的算法，所以本事就是匹配的，除非你瞎jb乱搞。

在过去几个月里， [Ignacio Castaño](http://castano.ludicon.com/blog/)一直在开发这个系统，他正在写一篇关于这个系统的高度技术化的文章，他说快完成了。而下面是一个简单的概述。

在预处理的阶段，我们只需要将摄像机移动到每个表面，将摄像机指向表面，并且将游戏场景渲染到一个半立方体上，并且存储在显存中。半立方体的render target纹理会被打包成地图集(atlas)，然后等到一个地图集被填满，就会被保存到系统内存中，对每个半立方体的值进行积分得到一个平均光照值，然后将这个值保存到lightmap中。下面的大部分图像是使用128x128立方体贴图和每个纹素多个样本生成的。

由于我们只是使用常规的渲染代码，所以这些预计算的过程默认都是GPU加速的。

**注意**：在下面的图像中，所有几何体和纹理都是占位符。与《Braid》一样，我们在构建核心玩法时使用了这些内容的草稿版本。这些图像不应被视为游戏的截图。它们目前并不需要看起来很好，它们只是用来展示预计算光照的效果。

首先是一些房屋的截图。房间内的大部分光照由预计算负责完成。除了太阳光直射的部分是动态的，其余的都是预计算的静态光照，如果没有预计算光照，整个房间除了太阳直射的光斑外都是漆黑的。

![thumbs_house1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/1/thumbs_house1.jpg)

![thumbs_house2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/1/thumbs_house2.jpg)

![thumbs_house3](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/1/thumbs_house3.jpg)

注意环境光遮蔽（ambient occlusion）、软阴影和其他有该系统自然产生的很棒的效果，第三张图中，墙上的画还没有经过lightmap的处理，所以

它会显得特别亮。

下面是一些主要由单一的材质和颜色构成的掩体的内部。

![thumbs_bunker1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/1/thumbs_bunker1.jpg)

![thumbs_bunker2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/1/thumbs_bunker2.jpg)

![thumbs_bunker3](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/1/thumbs_bunker3.jpg)

最后是塔楼。

![thumbs_tower1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/1/thumbs_tower1.jpg)

![thumbs_tower2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/1/thumbs_tower2.jpg)

![thumbs_tower3](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/1/thumbs_tower3.jpg)

这些图像还有许多问题。游戏使用HDR渲染，但是我们还没有平衡光照常数，也还没有做tone mapping，因此我对输出的图像做了不同程度的伽马校正。目前我们直只计算了光照的一次反射。在游戏的最终版本中，我们预计会计算光线跳跃2次或者3次的次级光照。完成后，我会发布一些对比图像。我认为我们的天空光照模型现在过于简单而且并不准确（尽管我需要与Ignacio确认，也许他已经修好了）。我还没有在户外的场景（比如有大量的小树枝和树叶）中测试现在系统运行的结果，如果发现了太多的走样之类的问题，我们可以在这些区域提高光照贴图的分辨率。

在那些门或者窗能开关的区域，我们计划添加一个补充的lightmap，这个lightmap会根据这个光圈（light aperture，译者：指门和窗开合的程度吧大概，总之应该不是作为摄像机的参数的那个光圈）的开放程度进行缩放，然后添加到基础的lightmap中。这将会提供一个非常好的对于光圈（译：这里只用了aperture，大概和前面是一个意思。他们当初为什么没有把引擎开源呢，想看源码）的开合对室内间接光照影响的近似。直接光照将会是完全正确的，因为我们用了动态的阴影系统。将来我会写一篇关于这个阴影系统的文章。
