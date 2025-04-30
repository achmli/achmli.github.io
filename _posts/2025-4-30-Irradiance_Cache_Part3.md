---
layout:       post
title:        "《见证者》引擎技术博客的扩展阅读——Occlusion Hessian"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - 《见证者》博客翻译
    - 图形学
---

> 这篇是在之前的[Irradiance Cache续](https://zhuanlan.zhihu.com/p/1888626331421475570)中提到的 <em>the witness</em>中没采用的更先进的误差控制方法的论文。
>
> 翻译论文感觉没什么意义，就简单地读一下，这篇就当是笔记吧（但似乎写着写着又变成翻译了，只能说没有静下心来阅读和总结的能力和心情。。。）。是12年的论文，按理说放现在应该不算很有价值，所以定位依然是看着图一乐。当然如果意料之外地对您能有所启发那是最好不过了。
> 
> 前两天看了下我的爱抖露之一的杀手aery的博客，发现surfel gi大概率也是基于radiosity的，说明辐射度算法这个gi路径是有比较新的算法的，那大概这些比较老的论文应该是没什么实用价值了吧。。。
>
> 之所以在宣布堂堂完结后又更一篇，是因为毕业论文被打了C要改了之后复审所以很不爽，暂时不想改所以又要逃避现实了。虽然我知道我写的很水,但是论文不水那还是科软吗（自嘲性质的玩笑，别太当真，虽然我是辣鸡但是科软还是有很多大神的捏。。。。
>
> 然后简历改了几周都没改完，想不到怎么包装了，当初虽然在藤子实习了一年但真是啥都没做成，啥也没学会。唉我真是垃圾中的垃圾啊。
>
> 依然有大量的内容靠我的AI叠来解读，总之AI真是我叠捏。
>
> 论文链接：[Practical Hessian-Based Error Control for Irradiance Caching](https://studios.disneyresearch.com/2012/11/01/practical-hessian-based-error-control-for-irradiance-caching/)

## Split Sphere
实际上之前那两篇里面我翻的那些b话我自己都看不懂。“irradiance缓存的基础思想是基于一种预测由于靠近遮挡物或者反射物而产生的irradiance的变化的度量(metric)的自适应的irradiance采样。”简直是b话中的b话，能看明白这句话的真是神人了。当然这么翻的我更是神人中的神人。

之前那篇的原文中是“The basic idea behind irradiance caching is to sample the irradiance adaptively based on a metric that predicts changes in the irradiance due to proximity to occluders and reflectors.”简单说应该就是比起缓存irradiance的值，更重要的是缓存irradiance的变化或者梯度。

但是在这篇论文中对irradiance cache的描述是：在渲染每个需要着色的点时查询缓存，如果附近有有效的记录，那就通过插值获得这个点的间接光照，否则就通过暴力的蒙特卡洛光追来计算。

传统的控制缓存的记录点分布的方法就是之前的《irradiance缓存续》中的方法，被称为“split sphere”，不过那篇文章其实没怎么具体展开讲，可能因为给了源码吧。。。

于是我问了我叠deepseek，它的回答是：

假设场景中存在一个“分裂球体”（Split-Sphere），由全亮的上半球和全暗的下半球组成，用于估计irradiance变化的最大可能速率。

Split-Sphere 的核心思想是通过几何曲率（Geometry Curvature）和辐照度梯度（Irradiance Gradient）的联合分析，确定缓存记录的​​有效半径​​（Valid Radius）。其核心假设是：

+ ​​表面几何曲率​​越大（弯曲程度高），缓存记录的覆盖范围越小；

+ irradiance梯度​​越大（光照变化剧烈），缓存记录的覆盖范围也越小。

通过这两个因素的平衡，Split-Sphere 动态决定在场景中何时需要插入新的缓存记录，以避免插值误差。

呃可以看的出来很科学，但是一般来说从逻辑推断，啊，作为被淘汰的传统方法肯定有其弊端。我的好兄弟deepseek是这么说的：对遮挡（Occlusion）和间接光照剧烈变化的场景并且依赖几何假设，无法适应复杂光照变化。

然后这个方法第一次发展是，记录点不止存储irradiance本身，还要存储irradiance的位移梯度和旋转梯度。这个方法首次引入导数信息，减少对均匀光照假设的依赖，但对遮挡变化仍处理不足。

然后接下来就是在《见证者》游戏中使用的方法，在《irradiance缓存 续》的那篇文章中提到的使用neighbor clamping的方法，这个方法就是强制使用三角形不等式（triangle inequality）约束和neighbor clamping，我的好伙计deepseek对这两者的解释是：

+ ​三角形不等式约束​​：强制相邻缓存点的半径重叠，避免插值间隙。
+ 邻居钳制（Neighbor Clamping）​​：限制新缓存点半径不超过相邻点，防止过大插值误差。

也可以看在《irradiance缓存 续》的那篇文章中的贴出来的[源码链接](https://gist.github.com/castano/5f7c8847f82e45cb56d0)（笑了。这里我也贴一下），不知道有没有这部分内容，应该有吧，唉最近不太想看。

然后进一步的发展就是各向异性缓存，以我浅薄的理解大概是保存各个方向的梯度，并且根据梯度方向压缩缓存记录，使得记录覆盖区域成为椭圆。

## 光照导数和误差控制
这里就不讲整个发展过程了，与这篇论文最直接相关的研究是一项2D光线传输的理论，推导irradiance的Hessian矩阵，但是occlusion-unaware，也就是忽略遮挡变化。这个研究也提出了运用Hessian矩阵作为irradiance cache的误差控制方法的想法，因为irradiance hessian提供了足够多的信息来同时获得椭圆缓存记录的方向和偏心率，从而最佳地适应局部各向异性irradiance曲率。

然后就是这篇论文讲的东西了，主要有以下几个方面：

+ 有遮挡感知的Hessian计算，用于误差项，解释有遮挡的场景中的irradiance变化。
+ 可以自动获得具有遮挡感知的梯度值，可以轻松地用于任意的半球采样分布。
+ 推导出一个更加感知驱动（perceptually-motivated）的误差公式，基于相对误差而非绝对误差，可以进一步减少。我的好朋友deepseek是这么解释perceptually-motivated的：使缓存分布更符人类视觉对亮度对比的敏感性。
+ 提出首个在辐射度量学中意义明确且实用的irradiance cache的误差度量，使得辐射度量学（radiometric）（and not geometric，并非几何）（其实我不知道为什么要特意强调不是几何）的误差度量robust（应该都知道这词什么意思，那就用英语吧）。
+ 考虑到表面法线的旋转，并且得到一个完整且使用的误差控制公式。
+ 并且在复杂场景（指Cornell Box、Sponza等）中验证。

## 背景知识
然后这篇论文详细地讲解了以下上面提到的部分内容。

irradiance cache利用了漫反射表面上的反射radiance <em>L</em><sub>o</sub> 可以用irradiance <em>E</em> 表示的事实：

$$ L_o(\mathbf{x},\vec{\omega}_o) = \frac{\rho(\mathbf{x})}{\pi}E(\mathbf{x},\vec{\mathbf{n}}) $$

其中$\rho \in [0, 1)$，用于表示漫反射的反射率。$\vec{\mathbf{n}}$则是用来表示表面法线。而irradiance用蒙特卡洛积分计算：

$$ E(\mathbf{x},\vec{\mathbf{n}}) = \int_\Omega L_i(\mathbf{x},\vec{\omega}_i)(\vec{\mathbf{n}} \cdot \vec{\omega}_i) $$

$$ \approx \frac{1}{N} \sum_{i=1}^N \frac{L(\mathbf{x},\vec{\omega}_i)(\vec{\mathbf{n}} \cdot \vec{\omega}_i)}{\rm{pdf}(\vec{\omega}_i)} $$

$$ =\frac{\pi}{N} \sum_{i=1}^N L(\mathbf{x},\vec{\omega}_i) $$

其中半球 Ω 上的方向 $ \vec{\omega}_i $遵循余弦权重分布（概率分布函数 $\rm{pdf}(\vec{\omega}_i)=(\vec{\mathbf{n}} \cdot \vec{\omega}_i)/\pi$），可以抵消分子中的余弦项。

然后依照上文中提到的无遮挡感知的hessian方法，通过将缓存点i的总误差$\epsilon_i^t$定义为正确的irradiance和在该缓存点支持域内通过外推得到的irradiance的差的积分，用来控制缓存记录的分布：

$$ \epsilon_i^t = \iint_A|E(\mathbf{x}_i+\Delta\mathbf{x})-E^{\prime}(\mathbf{x}_i+\Delta\mathbf{x})|d\Delta\mathbf{x} $$

其中A是缓存点的支持域的面积，$ \Delta\mathbf{x} $是切平面上的二维偏差。

而$ E^{\prime}(\mathbf{x}_i+\Delta\mathbf{x}) $

 $ = E_i(\mathbf{x}_i) + \nabla_\mathbf{x}E_i(\mathbf{x}_i) $

其中$ \Delta\mathbf{x} $是irradiance的一阶泰勒展开。

为了让irradiance缓存更加高效，目标是使用尽可能大的支持域A，将误差限制到某个阈值$\epsilon^t$。

由于这个表达式依赖于ground truth的irradiance $E$，但是计算真实的irradiance显然过于复杂和低效，所以通过irradiance的二阶的泰勒展开来估算这个值，最终的表达式中可以将缓存点的误差与irradiance的Hessian矩阵直接关联起来：

$$ \epsilon_i^t = \frac{1}{2}\iint_A|\Delta\mathbf{x^T H_x}(E_i)\Delta\mathbf{x}| d\Delta\mathbf{x} $$

$$ = \frac{1}{2}\iint_A(|\lambda_1|x^2 + |\lambda_2|y^2)dydx$$

其中irradiance的Hessian矩阵是一个2x2的矩阵，用于定义表面切线空间的二阶导数。表达式的第二行是第一行在由缓存点附近的irradiance的主曲率定义的坐标系中的重新表达（Hessian矩阵的特征向量$ \mathbf{v}^{\lambda_1}, \mathbf{v}^{\lambda_2} $对应特征值/曲率$ \lambda_1 , \lambda_2 $）。

转换到极坐标并执行积分，可以将上面的表达式简化为一个误差函数，该误差函数沿主方向$ \mathbf{v}^{\lambda_1}, \mathbf{v}^{\lambda_2} $的偏差的四次方增长。通过反转此误差函数，最终得到一个椭圆形的缓存点，其半径公式为：

$$ (R_i^{\lambda_1},R_i^{\lambda_2}) \approx \sqrt[4]{\frac{4\epsilon^t}{\pi}}(\sqrt[4]{\frac{1}{\lambda_1}},\sqrt[4]{\frac{1}{\lambda_2}}) $$

其中$ \epsilon^t $是用户设置的误差阈值。

在不考虑遮挡的Hessian矩阵的论文中他们推导了2D场景中的irradiance cache，并且提出了基于Hessian矩阵的误差控制策略，在假设场景中无遮挡的情况下推导出了一个irradiance的Hessian矩阵。虽然这种基于Hessian矩阵的误差度量方法未来可期，但是在存在遮挡的场景中，它的精度会显著下降。因此他们提出了几何Hessian（Geometric Hessian），这个方法忽视实际的radiance的值，而是提供整个场景的平滑的缓存分布。

几何Hessian在大多数场景中都有很好的表现，但是与split-sphere启发式算法类似，在简介光照发生显著变化时无法自适应地调整采样密度。

假设场景中有地板与墙壁相邻的部分，如果墙壁是暗色，那么该部分仅需要较低密度的采样，如果墙壁是亮色，那么就需要较高密度的采样。但是几何Hessian与Split-Sphere方法在两种情况下均采用完全相同的采样密度。

使用辐射度误差度量（radiometric error metric）就能实现对采样必要的动态调整，并且能对外推的（extrapolated）irradiance的实际误差有更加精确的控制，从而能实现更高质量的整个场景的irradiance评估。

## 实用的基于Hessian的辐射度误差（Practical Radiometric Hessian-based Error）

### 感知遮挡的平移Hessian

![SceneWithOcclusions](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/SceneWithOcclusions.png)

这篇论文的方法的核心是获得能精确场景中的遮挡的irradiance梯度和Hessian矩阵，比如上图所示的那样的场景。

![StrataArea](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/StrataArea.png)

在最初的irradiance缓存的论文中，如上图所示，通过半球采样粗略地获得附近场景的几何，并且分析位移时分层面积的变化，以此来获得感知遮挡的irradiance梯度。（没太理解说实话）

接下来的发展就是就是基于场景几何的近似，计算每个分层贡献的Hessian。也就是无视遮挡的Hessian的那篇论文的工作，他们忽视了层间的遮挡，这使得计算变得相对简单，但是获得的结果也就不太让人满意。（这论文怎么一直在总结过去的工作）

这个问题实际上与计算多边形成分层的遮挡感知形状因子Hessian（occlusion-aware form-factor Hessian each polygonal stratum，是我不懂的捏）是相同的，这在之前的Radiosity中已有研究。但是上图中的几何近似具有不连续性，所以没法给irradiance导，所以不能直接使用。

<b>半球采样的几何解释</b>

![SceneWithoutOcclusion](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/SceneWithoutOcclusions.png)

解决问题的关键是将场景转换成一个在x点处辐射度相同（radiometrically equivalent）的无遮挡场景，如上图所示。经过这样的转换，修改后的场景中，x点处的irradiance、irradiance梯度以及irradiance的hessian都仍然与原场景相同。

这种等效成立的原因是，x点的irradiance与其可见的均匀漫反射体（uniform diffuse emitter）所张开的立体角直接成正比。因此，当x点发生位移时，irradiance的梯度和hessian都与这个立体角的变化率成正比。上图中，emitter张开的立体角Ω和Ω’都与原场景中相同，所以irradiance和其梯度以及Hessian都必然没有发生改变。对于非常大的位移这不一定是对的，但是这里只考虑微分尺度。

![SceneApproximation](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/SceneApproximation.png)

了解了这一点之后，就能阐述基本的流程了：

首先处理半球采样，构建一个对周围环境几何的连续的分段线性近似，如上图所示，当半球采样射线转换为​​三角化的几何环境​​时，每个相邻采样点会连接形成三角形网格，这些三角形模拟了场景中遮挡和非遮挡区域的辐射贡献。从x点的视角看，这是没有遮挡的。（没太理解，应该是说每个分段都没有被遮挡？）然后就能计算出这个三角化的场景的irradiance梯度和hessian，并且结果中包含了物理场景中的遮挡关系，尽管这个过程没有显示地处理这些遮挡。

假设已构建三角化的半球环境吗，那么上面计算irradiance的表达式在这个几何近似中可以被表述成：

$$ E(\mathbf{x},\mathbf{\vec{n}}) \approx \sum_{j=1}^M L_{\Delta_j} F_{\Delta_j}(\mathbf{x}) $$

其中M​代表​三角化环境中的三角形面片的数量，$ L_{\Delta_j} $表示第j个三角形面片的radiance，$ F_{\Delta_j} $则表示点x到该面片的​​形式因子（form-factor）。

这样x点的irradiance梯度和Hessian就能通过累加形式因子的梯度和Hessian来获得：

$$ \nabla_{\mathbf{x}}E \approx \nabla_{\mathbf{x}}\left(\sum_{j=1}^M L_{\Delta_j} F_{\Delta_j}(\mathbf{x})\right) = \sum_{j=1}^M L_{\Delta_j} \nabla_{\mathbf{x}} F_{\Delta_j}(\mathbf{x}) $$

$$ \mathbf{H}_{\mathbf{x}}E \approx \mathbf{H}_{\mathbf{x}}\left(\sum_{j=1}^M L_{\Delta_j} F_{\Delta_j}(\mathbf{x})\right) = \sum_{j=1}^M L_{\Delta_j} \mathbf{H}_{\mathbf{x}} F_{\Delta_j}(\mathbf{x}) $$

幸运的是，这样对分层采样的处理不会在位移时引起遮挡变化，因此可以独立地为每个三角形计算形式因子的导数而不用考虑它们相互遮挡带来的影响。（原文中在附录中贴了计算形式因子梯度和Hessian的原论文，我在这里贴一下链接吧。。。分别是[The Irradiance Jacobian for Partially Occluded Polyhedral Sources](https://www.graphics.cornell.edu/pubs/1994/Arv94.pdf)和[ Anexhaustive  error-boundingalgorithmforhierarchical radiosity](https://inria.hal.science/file/index/docid/98630/filename/HS98.pdf)）

通过上面的表达式计算得到的Hessian是三维的，但我们实际关注的是该矩阵在表面切线空间上的投影（我的好哥哥deepseek翻译的，我确实不是很能理解“whereas we are interested only in the Hessian across the surface on which it was computed”这句话）。为了将3x3的Hessian矩阵投影到这个平面上，定义$ \mathbf{a} = \mathbf{H_x}E(\mathbf{x})\mathbf{u}_1 $ 和 $ \mathbf{b} = \mathbf{H_x}E(\mathbf{x})\mathbf{u}_2 $，其中<b>u</b><sub>1</sub>和<b>u</b><sub>2</sub>是表面切线空间的正交基向量，那么切线空间的Hessian矩阵为：

$$ \mathbf{H_x}^{2 \times 2} =\begin{bmatrix}
    \mathbf{u}_1 \cdot \mathbf{a} & \mathbf{u}_1 \cdot \mathbf{b} \\
    \mathbf{u}_2 \cdot \mathbf{a} & \mathbf{u}_2 \cdot \mathbf{b}
\end{bmatrix} $$

<b>构建三角化环境</b>

![triangulate](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/Triangulation.png)

在构建三角化环境时，需要考虑的是每条采样光线的命中距离和命中位置。遍历所有样本，每两个相邻的样本相连与对应的两条采样光线组成一个三角形。利用上图中的分层中包含的邻接信息可以加速这一过程。网格和入射的radiance信息结合，就能获得x处的三维场景快照（snapshot）。下图展示了cornell box中在红点处构建的采样网格。

![Cornell Box](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/CornellBoxTriangulate.png)

上图中最重要的特征是链接连接遮挡物的几何表面和墙面的大型三角形。这些多边形编码了采样点x视角中的场景的遮挡信息。尽管这些三角形在空间上跨度较大，但是它们做组成的立体角与其他三角形近似，所以不会导致这部分采样贡献比例过大的情况。然而当x发生位移时，这些大型三角形的立体角会更快地扩大或者缩小，所以存在遮挡变化时会产生较大的梯度和Hessian。

为了计算irradiance的梯度和Hessian，需要定义刚刚构建的网格体中每个三角形的入射radiance $L_\Delta$。在二维的情况（就半球采样的几何解释中第二张图那样）下，这个值对应于三角形三个顶点中离着色点x最远的顶点中存储的入射radiance。在三维场景中也是同理，但是要选择三角形三个顶点中最远的那一个（2D情况下是两个）（感觉有点诺言诺语了吧。。。不知道2D情况的两个是一个三角形选两个顶点还是两个三角形选一个顶点。。。当然最可能的解释是三角化的Mesh并不包含连接到x的三角形，而是采样点之间连接成的，所以2维情况是，就像图里那样，是虚线线段，所以是两个顶点里选一个，而3D场景就像这部分的第一张图这样，能连成三角形，所以是三个顶点里选一个。）。直观上来说，离x最远的顶点决定了x位移时被移除遮挡的物体的颜色。最早的split-sphere启发式算法用了类似的方法估算层级间遮挡的微分变化，这种方法能够很好地近似真实场景中（存在显著遮挡时）irradiance的一阶与二阶导数。。而不出意外，不考虑遮挡的Hessian的那种方法就与真实情况差别较大。

本文的方法能后隐式地在梯度与Hessian计算中包含遮挡变化，而无需依赖显式处理遮挡的复杂的形式因子计算，同时也能避免因为病理情况（pathological cases）导致结果不可用的情况。同时本文的方法还有一个优势，那就是可以直接使用现成的任意半球采样分布，无需因为采样分布的改变而重新推导算法。另外尽管尝试过标准的经纬度分层采样，当时最后选择了同心映射，因为其生成的采样模式更规则，可以产生更好的结果。

### 缓存记录有效区域

为了计算缓存记录的各向异性的有效区域，需要定义一个相对误差项，而不是irradiance的绝对误差，这样做有这么几个好处：

1. 更符合人类视觉系统对对比度比对亮度绝对变化更敏感的感知。
2. 使误差独立于场景绝对尺度与光源强度，增强参数跨场景普适性。

为了完成这些，通过将Hessian矩阵除以采样点处的间接irradiance来修改误差公式：

$$ \epsilon^r_i \approx \frac{1}{2} \iint_A \frac{\mathbf{\Delta x^{\top}}\mathbf{H}_\mathbf{x}^{2 \times 2}(E_i)\mathbf{\Delta x}}{E_i} d\mathbf{\Delta x} $$

$$ = \frac{1}{2} \iint_A \left(\frac{|\lambda_1|}{E_i}x^2 + \frac{|\lambda_2|}{E_i}y^2 \right) dydx $$

在极坐标系下积分并求逆，得到各向异性的缓存记录的半径方程：

$$ \left(R_i^{\lambda_1}, R_i^{\lambda_2} \right) = \sqrt[4]{\frac{4\epsilon^r E_i}{\pi}} \left(\sqrt[4]{\frac{1}{\lambda_1}},  \sqrt[4]{\frac{1}{\lambda_2}} \right) $$

![Error Comparison](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/Figure7.png)

其中$ \epsilon^r $是核心误差控制参数。与之前的半径方程的关键差异在于使用了感知遮挡的Hessian，并且缓存被间接irradiance的四次方根缩放（场景中的亮处能比暗处忍受更多的绝对误差）。上图中展示了在Sponza场景中使用相对误差与绝对误差的半径对比。场景中庭院内的墙面有着更亮的间接光照，这使得再计算半径时这部分可以接受更大的误差。对于绝对误差而言，加倍光照的强度就必须要修改采样分布（强制用户手动操作误差阈值才能获得相同的图片），而这在相对误差的方法中是不需要的。在下图中，对比了各向异性的记录和各向同性（通过强制使用两个半径的最小值得到）的记录。各向异性的记录根据局部irradiance曲率自适应调整偏心率，使得在相同的误差阈值下可以使用更少的记录。在实践中，将椭圆缓存记录的长轴限制在短轴的两倍，用来防止irradiance的Hessian矩阵在某一方向曲率几小时可能出现的artifact。

![Anisotropic Comparison](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/Figure8.png)

<b>病理情况</b>

任何radiometric的方法都会遇到一个根本性的问题，大多数甚至所有的采集光线（gather ray）都返回黑色，会导致半径未定义或者无限大。在计算有许多次bounce的完整的全局光照时，这基本上不会出现，但是在只计算一次bounce的见解光照时，这就很常见了。那个不考虑遮挡的Hessian的方法就是因为这个问题才被迫转向完全几何的方法的。为了保留radiometric方法的优点，本文的方法是在计算Hessian前，向所有三角形的radiance的值$ L_{\Delta_j} $添加间接irradiance的值$ E_i $的1%。当所有的采集光线都返回黑色时，就设置所有三角形的radiance值$ L_{\Delta_j} = 1 $。这使得Hessian仅在这种情况下切换到一种的感知遮挡的几何Hessian。注意这样做仅仅是在Hessian计算时增加了1%，并且没有修改存储在缓存中的irradiance值。

<b>评估</b>

![Measure](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/Figure9.png)

上图展示了结合了这些改进措施（使用相对误差替代绝对误差和添加irradiance值的1%）的效果，上排是这些改进应用于无遮挡的radiometric Hessian的效果，下排是讲这些改进应用于遮挡感知的Hessian的效果。这些改进对两种Hessian的效果都有所提升。但最重要的提升是让Hessian感知遮挡这件事本身。由于在陡峭局部梯度的区域进行差值，radiometric hessian会产生干扰性的artifact。这是因为这种方法的误差控制对遮挡的变化oblivious（什么意思捏，事大祥老师吗，那她太坏了），导致缓存记录对于局部irradiance曲率而言过于大了（很奇怪，看不懂，deepseek的翻译是“导致缓存记录在局部irradiance曲率过大的区域尺寸过大”）。使用遮挡Hessian就能使这些artifact消失。

![gather rays comparison](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/FigureX.png)

为了验证这个半径计算方法足够robust，即使采集光线数量很少也能有不错的效果，所以在上图中对比了不同采集光线数量时Cornell Box中的缓存点分布情况，左边是256条采集光线，右边是4096条。即使少了这么多采集光线，缓存点分布依然没有差不多（原文是quatitatively the same，从定性分析看是相同的，没有质的差别）。

![simple scene](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/FigureXI.png)

上图中对比了在一个带有间接遮挡物的简单场景中radiometric hessian和遮挡hessian的表现。遮挡hessian成功地将采样点集中在由于遮挡导致irradiance频繁变化的区域（半影（penumbra）区域）。

### 旋转误差

可以用相似的流程推导出旋转的irradiance hessian。由于旋转导数仅与表面法线旋转后导致的余弦衰减项（cosine foreshortening term）的变化有关，而不会发生遮挡变化，所以计算可以简化为求余弦的一二阶导数。但是这种方法效果并不好。问题就是遮挡事实上是会发生改变的，对于任何显著的旋转，与下半球解除遮挡对irradiance造成的影响相比，余弦因子的变化都显得微不足道。换言之，当法线旋转时，原本位于上半球之外的几何体可能进入可见区域，这会剧烈改变irradiance。由于只能可靠地对上半球进行采样，因此几乎无法预测这些下半球区域的遮挡变化对irradiance的实际影响。

解决方法既简单又直观，那就是强制限制表面法线在外推过程中的最大偏差角$ \Delta \mathbf{\vec{n}_{max}}$，例如禁止缓存记录在表面法线偏差超过10°的情况下进行外推（no cache records are allowed to extrapolate beyond an e.g. 10° deviation in surface normal），将最大偏差角默认设置为0.2弧度，并且允许用户修改。

### irradiance的存储与插值

每个缓存点i需要存储的内容有：位置和法线$(\mathbf{x}_i,\mathbf{\vec{n}}_i)$、

irradiance的值$E_i$、

irradiance的梯度$(\nabla_\mathbf{x}E_i,\nabla_\mathbf{\vec{n}}E_i)$、

两个各向异性的半径$(R_i^{\lambda_1},R_i^{\lambda_2})$

以及对应的特征向量$(\mathbf{v}_i^{\lambda_1},\mathbf{v}_i^{\lambda_2})$。

之前计算出的$\mathbf{H_x^{2 \times 2}}$特征值分解后得到的特征向量$\mathbf{v}_i^\prime$是由正交基向量$ \mathbf{u_1,u_2} $在切线空间定义的，需要将其转换到世界空间：$ \mathbf{v}_i = [\mathbf{u}_1 \cdot \mathbf{v}_i^\prime,\mathbf{u}_2 \cdot \mathbf{v}_i^\prime] $。

缓存记录的插值使用修改了权重函数的一阶外推策略（first-order extrapolation strategy）：

$$ E(\mathbf{x,\vec{n}}) \approx \frac{\sum_{i \in S} \mathrm{w}_i(\mathbf{x})(E_i+\nabla_\mathbf{x}E_i \cdot \Delta\mathbf{x}_i + \nabla_\mathbf{\vec{n}}E_i \cdot \Delta\mathbf{\vec{n}}_i)}{\sum \mathrm{w}_i(\mathbf{x})} $$

其中$\Delta \mathbf{x}_i = \mathbf{x-x_i}$和$ \Delta \mathbf{\vec{n}}_i = \mathbf{\vec{n}} \times \mathbf{\vec{n}}_i $分别是着色点x的平移偏差和法线旋转偏差。

集合S中包含了所有有效的缓存记录，缓存记录有效的条件是与当前着色点x重合且法线偏差不超过最大偏差角$ \Delta \mathbf{\vec{n}_{max}}$。为了计算缓存记录的权重，本文提出一种结合了位移和旋转的权重函数，并在边界时降至0（deepseek的说法是“权重函数$ \mathrm{w}_i(\mathbf{x}) $结合平移误差与旋转误差，采用帐篷滤波器（Tent Filter）平滑衰减至零”）：

$$ \mathrm{w}_i(\mathbf{x}) = k(1-t_\mathbf{x},0,1) \times k(t_\mathbf{\vec{n}},cos\Delta\mathbf{\vec{n}_{max}},1) $$

其中k就是一个简单的帐篷滤波器，$ k(t,t_{min},t_{max}) = \frac{t-t_{min}}{t_{max}-t_{min}} $。并且

$$ t_\mathbf{x} = \sqrt{\left[ \frac{\Delta \mathbf{x}_i \cdot \mathbf{v}_i^{\lambda_1}}{R_i^{\lambda_1}} \right]^2 + \left[ \frac{\Delta \mathbf{x}_i \cdot \mathbf{v}_i^{\lambda_2}}{R_i^{\lambda_2}} \right]^2 + \left[ \frac{\Delta \mathbf{x}_i \cdot \mathbf{n}_i}{R_i^{\lambda_1}} \right]^2} $$

$$ t_\mathbf{\vec{n}} = (\mathbf{\vec{n}} \cdot \mathbf{\vec{n}}_i) $$

这两个值分别是位移和旋转的距离。只有在$ \mathrm{w}_i(\mathbf{x}) $的值大于0时，缓存记录才参与插值。帐篷滤波器也可以被替换成其他的更高阶的平滑滤波器，但是测试下来并没有发现有显著的提升。

<b>扩展到radiance caching中</b>

将本文的方法扩展到radiance caching也相对直接。由于radiance caching也使用了Split-sphere来进行误差控制，所以可以轻松地将其替代为本文的遮挡Hessian项。对于标准的极坐标分层（polar stratification），可以将radiance和其梯度一同投影到球谐函数上。如果使用同心映射（concentric mapping），radiance的投影同样会非常简单，但需要额外工作来推导平移randiance梯度（translational radiance gradient）到球谐函数的投影形式。

## 结果

（这部分就用deepseek的翻译了，反正差不多就是测试）

| 方法 | Cornell Box | Sponza | San Miguel |
|------|-------|------|------|
| Split-sphere | 01:02.3 | 53:08.4 | 07:15:22.4 |
| Radiometric Hessian | 01:06.5 | n/a | n/a |
| Geometric Hessian | 01:04.7 | n/a | n/a |
| Occlusion Hessian | 01:16.5 | 54:35.6 | 07:17:43.7 |

我们通过修改PBRT（Pharr和Humphreys，2010）第二版中原生的辐照度缓存实现，集成了新的误差度量方法。所有结果均在一台配备2.66GHz Intel Core i7-920 CPU的计算机上渲染，每像素使用4个采样。我们的Split-Sphere启发式实现遵循Ward（1988）的原始公式，并使用调和平均距离（harmonic mean distance）。对于Bounded Split-Sphere，我们将半径限制为最大像素尺寸，并根据计算的irradiance梯度调整采样密度（在梯度幅值超过Split-Sphere预测的区域增加采样密度）。所有方法均使用每个irradiance采样4096条光线，且除非特别说明，我们强制缓存点半径至少为采样位置处1像素的投影尺寸。对于基于Hessian的方法，缓存点半径无上限。所有基于Hessian的结果均使用默认$ \Delta \mathbf{\vec{n}_{max}}=0.2$弧度作为最大法线偏差角。渲染时间见上面的表。

![cornell box compariaon](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/Figure1.png)

上图比较了Occlusion Hessian误差控制方法与Split-Sphere启发式，以及Jarosz等人（2012）定义的Geometric Hessian和Radiometric Hessian度量。所有图像以1800×1800像素分辨率渲染，仅包含单次间接光照反弹。针对每种方法调整误差阈值，以使用1700±2%的缓存记录。仅使用1700条缓存记录时，Split-Sphere方法显示出严重的插值artifact。即使最大半径限制为150像素（在1700条记录下无法设置更低阈值），Bounded Split-Sphere方法在整个渲染图像中仍存在显著误差。Radiometric Hessian在光照区域表现良好，但在阴影区域存artifact。Geometric Hessian在大部分场景中效果良好，但在墙面和天花板上显示出插值失真。Occlusion Hessian产生最佳整体结果，既解析了阴影细节，又在墙面和天花板上保持了足够的采样密度以重建irradiance。在此简单几何场景中，Occlusion Hessian增加了约20%的计算时间开销；但在更复杂场景中，由于光线追踪占据主导时间，此开销可忽略不计。

![test2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/FigureXII.png)

上图中比较了Occlusion Hessian方法与Bounded Split-Sphere启发式在缓存点密度递增时的表现。所有图像使用4096条gather光线，Split-Sphere方法的最大半径设为150像素（在极低缓存点数情况下无法设置更严格的限制）。值得注意的是，即使仅使用500条缓存记录，Occlusion Hessian仍能生成高质量结果，而Split-Sphere即使在1000条记录下仍存在大幅artifact。这些artifact源于记录数量的严格限制迫使误差阈值设置过高，导致天花板的缓存记录被错误复用于墙面，反之亦然。

![test3](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/FigureXIII.png)

上图中，我们通过渐进式细化（progressive refinement）、邻域截断（neighbor clamping）和预计算阶段（overture pass）（Křivánek等，2006）扩展了Split-Sphere方法。增强版Split-Sphere的渲染时间为123.4秒，而带有预计算阶段的Occlusion Hessian渲染时间为122.6秒。尽管Split-Sphere的改进显著，但Occlusion Hessian的质量仍明显更优。需注意，预计算阶段对Occlusion Hessian的影响较小，因其误差度量更贴近irradiance的实际误差。

![test4](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/FigureXIIII.png)

上图展示了修改后的Cornell Box场景的irradiance渲染结果（后墙反照率设为0）。Geometric Hessian未考虑场景的radiometry，其缓存点分布与原Cornell Box相同，导致次优结果。我们的Occlusion Hessian则根据新配置的radiometry动态调整分布，生成更高质量的结果。注意，差异图的颜色范围已缩放以便于比较。

![test5](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/FigureXV.png)

这张图展示了使用Occlusion Hessian和Split-Sphere启发式（无限制及最大半径20像素）渲染的Sponza场景特写。此场景使用光子贴图（photon map）添加多次间接光照反弹。辐照度缓存用于收集视线首次接触的漫反射表面的irradiance，全图使用32,000±1%的缓存记录。结果显示，Split-Sphere启发式在柱体阴影区域存在插值artifact，而Occlusion Hessian能更精确地重建光照细节。

![test6](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/FigureXVI.png)

这张图直接可视化了Sponza场景中不同方法的缓存记录半径（顶部）和记录覆盖范围（底部）。注意，对于各向异性方法，我们展示了两半径的几何均值，且缓存记录轮廓以最大尺寸的45%绘制以避免重叠。Split-Sphere图像显示，通过真实一阶梯度额外限制缓存点半径后，在irradiance高变化区域（如柱基的间接半影）半径更小。此行为与Occlusion Hessian一致，后者根据irradiance变化率定义半径。然而，Split-Sphere图像的对比度更高（半径变化更大），导致更差的结果（例如，在半影区域外采样会产生极大半径的缓存点，而半影区域采样不足）。

![test7](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/11/FigureXVII.png)

这张图展示了PBRT San Miguel场景的视图。各方法调整至生成50,000±1%的缓存记录。次级光照反弹使用存储了100万个光子的光子贴图。我们的Occlusion Hessian方法能正确定义图像中所有间接阴影，并在irradiance缓变区域（如平坦墙面）表现出更少的插值伪影。Bounded Split-Sphere与Occlusion Hessian的渲染时间差异小于0.5%。

## 结论和进一步的工作

（这部分依然直接用deepseek的翻译，终于结束了，能专心改论文了捏）

在本文中，我们提出了一种控制辐照度缓存近似误差的新方法。新方法基于计算辐照度的二阶导数——平移Hessian——同时考虑物体间的相互遮挡。我们使用辐照度的二阶泰勒展开作为真实辐照度的预测器，以估计一阶泰勒展开在渲染过程中引入的误差。该Hessian天然支持各向异性缓存点。因此，记录密度能够紧密贴合场景中辐照度的变化速率，与所有先前方法相比，显著减少了渲染图像的误差。此外，我们的方法不严重依赖用户定义的最小/最大缓存点半径，提供了更直观的用户控制。新Occlusion Hessian方法的鲁棒性也最大程度减少了对其他矫正技术（如渐进式细化、邻域截断或预计算阶段）的需求，使实现更为简洁。

尽管我们的方法显著改进了辐照度缓存的误差控制，仍有以下研究方向值得探索：

+ <b>高阶导数</b>：将框架扩展至包含更高阶导数（如三阶项），可能进一步减少辐照度高度非线性变化场景中的插值伪影。
+ <b>动态场景</b>：使Occlusion Hessian适应处理含移动物体或可变形几何的动态场景仍是一个开放挑战。
+ <b>其他缓存技术的泛化</b>：将遮挡感知Hessian框架应用于其他缓存方法（如radiance缓存或光子映射），可能提升其在复杂场景中的鲁棒性。
+ <b>感知误差度量</b>：将人类视觉感知模型集成至误差度量中，可能实现数值误差阈值与视觉质量间更好的对齐。
+ <b>GPU加速</b>：在现代GPU架构上实现Occlusion Hessian可能降低计算开销并实现实时性能。

我们的结果表明，基于Hessian的误差控制是提升全局光照算法质量与效率的潜力方向。我们相信该方法能启发自适应采样与误差驱动渲染技术的进一步创新。

