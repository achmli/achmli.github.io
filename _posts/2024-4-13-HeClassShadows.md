---
layout:       post
title:        "何同学寒假小课堂——阴影"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
---



# Shadow Map

![BasicShadowMap](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/BasicShadowMap.png)

最经典的算法，具体实现很清楚。

主要是分辨率的问题，在入射角很大的时候，精度会导致较大的问题，产生仿佛摩尔纹一样的阴影，称为Shadow acne。(类似在入射角小时，粗糙度低的材质bloom会闪烁)。

浮点精度会导致self shadowing之类的问题。

解决方法都是通过添加偏移bias，但是bisa的数值没选好容易产生阴影悬浮也被称为Peter Panning的问题。

还有最后就是Shadow map不支持半透明物体。估计和半透明物体计算阴影的方法也有关系，但是最主要的原因估计还是和深度检测类似半透明需要深度图存储多个深度，而且数量是不可知的，这就没办法解决了。

![ShadowFiltering](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/ShadowFiltering.png)

具体算法还是看Games202吧，反正何同学用的图也是202的实验。

并不是对已经产生的阴影滤波，也不是对Shadow Map滤波，而是对深度和Shadow Map对应的像素附近的滤波核内的像素对比的结果(1和0)求平均。

硬件PCF是设置时使用Compare Func和linear sampling，一次采样就能得出结果。缺点是固定2x2的滤波核，不能完全消除锯齿。在手游上使用较多。

![Vsm](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/Vsm.png)

vsm也是202中讲过的算法，具体的算法也得去看202.

msm就是拟合的阶数的不同，低阶是vsm，高阶就是msm了。工业界用vsm更多，但因为阶数低，所以会容易有漏光的现象。

![CSM](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/CSM.png)

按距离区分精度生成多张shadow map。比如*The Witness*用了四层Shadow map最后存储在一张纹理中。每层Shadow map的分辨率相同但是覆盖的范围不同。

![VirtualShadowMap](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/VirtualShadowMap.png)

我去，又是VSM。UE的SM5和SM6的的一个差别好像就是VSM。

应该是一张巨大的virtual Shadow Map覆盖住整个场景，同时将场景划分为许多快，当需要某一块的Shadow map时先查询显存(?)，如果已经有了就直接使用，没有就需要一些其他的操作(看PS中的内容，应该是缺块就在显存空闲块上或者需要被替换的快上绘制这一块的深度，而不是类似于虚拟内存通过CPU与硬盘换块，不需要有GPU与CPU的数据传输，速度可以更快)

![PerObjShadow](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/PerObjShadow.png)

最大的问题在于阴影的receiver要采样两次Shadow map，传统的和角色单独的Shadow map都需要采样。

一种解决方法是角色附近采样两次，其他地方只采样传统的Shadow Map。

还有就是Self Shadow，何同学没仔细说，我猜测是把阴影当作角色本身的一部分去渲染，在渲染角色的pass而不单独在阴影的pass里去渲染。

# Shadow Map通用优化技巧

核心是要减少Shadow Map需要的Draw call

![SetCasterAndReceiver](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/SetCasterAndReceiver.png)

UE中每个Actor都可以设置投射阴影之类的选项。

![PrecomputedShadow](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/PrecomputedShadow.png)

预计算的Shadow Map，针对静态光源+静态场景，就不需要去每帧draw call 重新生成了，在游戏开始运行的时候从硬盘读到显存就行。

相应的预计算的Shadow Map的压缩也很重要。和上面手动设置Caster的结合，只记录caster的深度，其余部分记为0，这样就可以有很高的压缩率。

![PVS](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/PVS.png)

烘焙Shadow Map需要消耗比较大的存储空间，所以可以划分区域，记录每个区域中的物体的ID，当玩家走到这块区域时，生成这些物体的Shadow Map，

然后重点在于区域大小的划分，如果划分大了，那生成一次Shadow Map需要的Drawcall依然会很多，二划分小了，会相对浪费存储空间，并且定位玩家在哪个区域的开销也会增大。

![ShadowCache](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/ShadowCache.png)

当玩家移动时，shadow map会有部分重叠，这部分就不变，只更新变化的部分。

具体的操作是检测需要计算Shadow Map的区域里有哪些物体，记录它们的深度。

在UE里无论VSM还是CSM都使用了这种优化方法。

![Culiing](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/Culiing.png)

类似于深度测试。

软件光栅化的方法是从光源摄像机生成一张深度图，这张深度图用的是物体的aabb包围盒，后续物体计算Shadow Map的时候就可以剔除掉那些深度大于这张深度图的物体。

正常渲染一个场景，要设置很多东西，比如纹理就有很多设置，但是生成Shadow Map不需要，所以Shadow Map更适合GPU Driven

![FrustumCulling1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/FrustumCulling1.png)

光源的特点使得光源摄像机的覆盖范围堪称无限大，导致如果从光源摄像机做视锥剔除那几乎剔除不了多少东西。

所以Shadow Map的视锥剔除依然是从玩家摄像机，因为视锥体外的物体其实没有渲染出Shadow Map的必要。但是有些物体虽然本身不在视锥体内，但是阴影会投射到视锥体内，所以与传统的视锥剔除相比，不仅要考虑物体本身，也要考虑物体的阴影体积。物体的阴影体积就是光源朝物体的射线方向的无限延伸，然后阴影体积和物体就组成了一个形状，拿这个形状去和视锥体求交。但是复杂的mesh和它的阴影体积去和视锥体检测是否相交，复杂度太高，所以往往会对模型做一些简化，比如用一个球包围住物体，加上球的阴影体积，可以看作一个无限长的胶囊体，去和视锥体求交。

![FrustumCulling2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/FrustumCulling2.png)

朝光源方向也就是光照反方向延长视锥体，检测那些物体与之相交。

# Shadow Ray

![DFSS](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/DFSS.png)

就是面光源的端点和物体连线可以有一个四面体，那么每个平面都会有顶点在物体的角，然后通过ray marching的方法去获得不被遮挡的最大的角和三角形顶点角的比值，就可以获得软阴影。

![ContactShadows](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/ContactShadows.png)

一般是Shadow Map的补充。

工业界一般是固定大步长，而不是202中那种Hi-Z的方法。(因为是Shadow Ray，不需要知道具体的Hit Point，只需要知道是否相交)

![HeightField](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/HeightField.png)

应该是一张Texture保存高度信息，然后从观察方向射出光线用ray marching的方式和高度场求交，来看是否被遮蔽。

适合一些大地图。

**何同学说还有一种叫Hybrid Frustum-traced Shadows的技术他来不及准备就不讲了**

# Shadow Volumes

![ShadowVolumes1](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/ShadowVolumes1.png)

和上面提过的阴影体积是一个东西，而一个点是否被阴影覆盖也就是这个点是否在阴影体积内。

就是任意一个点朝任意方向发射射线，与物体相交次数为奇数就是在多边形内，偶数就是在多边形外。

![ShadowVolumes2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/ShadowVolumes2.png)

与正面比一次深度，与背面比一次深度，实际上是上面Ray cast的方法的一种适合光栅化的实现。

![ZFail](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/ZFail1.png)

![Kamac](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/Kamac.png)

上图是失败的情况，其实就是近平面阴影体积內时，射线就无法射出阴影体积了，相交册数就会比正确情况少1，奇偶判断就会出错。

约翰卡马克则是换了个思路，将测试成功和失败的对应的操作交换一下，就相当于朝相当于无限深的远平面投射线了，结果就正确了。

但是游戏画面质量提升后，mesh数量很多，然后产生的阴影体积每个都要两遍draw call，需要深度测试和模板测试的功能高强度运作，所以对于现代的游戏，这样的效率是非常低的。

![CCShadowVolumes](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/CCShadowVolumes.png)

第一步是将在阴影体积内的物体和视锥体内不可能是Caster的物体剔除。

然后对阴影体积想方设法裁剪？说实话没太看懂，何同学说的也没太听懂。第二步应该是从玩家摄像机对阴影体积做深度测试，将被大块遮挡的部分剔出

第三步对视锥体分层，如果同一层已经有更浅的阴影体积，就把后面更深的剔除。

事实上，即使如此，Shadow Volumes依然性能不高，无论culling还是clamping对cpu的要求都较高。

# Shadow PipeLine

![CCShadowVolumes](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/ClassmateHe/Shadow/ShadowPipeline.png)