---
layout:       post
title:        "《见证者》引擎技术博客的扩展阅读——再探BC1压缩"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - 《见证者》博客翻译
    - 图形学
---

> 因为十分喜欢《见证者》，所以想试着翻译一下他们的技术博客。连翻三篇，说明我想到论文就烦，跳了。
>
> 发现Ignacio Castano的个人博客上也有一些技术文章，而且这个博客一直在更新，所以可能有些文章是值得参考的。
> 
> 这是他还在绿色显卡公司工作时的项目。后来大概也修改后应用在《见证者》中了。唉见证者的引擎好像基本上就是他写的。所以相比之下我这种垃圾显然不应该找到工作，就应该成为废人，最后被拉去垃圾处理厂。
>
> 这个博客的project页面里写了作者参与过的项目。令人不禁感叹这大概就是大神吧。但博客里技术分享的内容算不上多。目前好像就一篇介绍不同图形接口的压缩算法的我还没翻。。。。当然或许还有其他的我没找到。。。
>
> 这篇文章写于2022年，但我不懂压缩，nv的技术显然也不会是astc之类的移动端用的比较多的算法，而且BC1好像还挺古老的？所以我也不知道这篇文章的内容放现在是否有用。总之最后一段的第一句话“The BC1 format is not particularly relevant today”。
>
> 有用AI辅助翻译，AI真是我叠捏。
>
> 博客链接：[Ignacio Castaño](https://www.ludicon.com/castano/blog/)
>
> 原文链接：[BC1 Compression Revisited](http://www.ludicon.com/castano/blog/2022/11/bc1-compression-revisited/)
>
> 作者： Ignacio Castaño

[NVIDIA Texture Tools](https://github.com/castano/nvidia-texture-tools)（NVTT） 曾经拥有公开可用的最高质量的BC1编码器，但其余部分的代码质量比较平庸。其他的编码器没有收获很多关注，CUDA代码路径缺乏维护，配套的图像处理和序列化代码也较常规。有太多的不怎么有趣的代码了，也导致了构建繁琐且维护成本高。

这促使我将BC1编码器的部分单独打包为一个单头文件库：

https://github.com/castano/icbc

整理这部分代码也使得我有了机会重新回顾这个编码器，并且修改了其中向量化（vectorize）的实现方法。本文将详述这些改进，但首先概述BC1压缩器的工作原理。

## 概述

BC1的一个块是用2个16位的颜色和16个2位索引表示的4X4纹素（texel）组。其中颜色用R5G6B5格式编码，并且定义了一个4色或者3色的调色盘 （palette）。调色盘的条目是2种颜色的凸组合（convex combination），因此它们通常被称为端点。索引的作用是从调色盘中选取一种颜色。

Nathan Reed对[该格式及其他块压缩格式都有很好的概述](https://www.reedbeta.com/blog/understanding-bcn-texture-compression-formats/)，而Fabian Giesen则[讲述了更多的底层细节](https://fgiesen.wordpress.com/2021/10/04/gpu-bcn-decoding/)，描述了在不同架构的GPU上端点都是怎么插值的。

为了编码一个BC1的块，我们需要选择两个能使误差最小的端点a和b。可以将这个问题看作求解包含16个等式的方程组，每个纹素x<sub>i</sub>对应一个等式：

$$ \alpha_i a + \beta_i b = x_i $$

在4色块的模式（4 color block mode）下，α<sub>i</sub>和β<sub>i</sub>被限制在从{0, 1/3, 2/3, 1}中选择一个值，至于选择哪个值，取决于每个纹素被分配到的索引（或选择器）。

假如已经知道每个纹素分配到的索引，就能用最小二乘法求解上面讲的方程组（solve the above equation system in the least squares sense），获得a、b端点的最优值。也就是说，我们只需要求解下面这个等式：

$$ \begin{pmatrix}
a \\
b
\end{pmatrix} = 
\begin{pmatrix}
\sum \alpha_i^2 & \sum \alpha_i\beta_i \\
\sum \alpha_i\beta_i & \sum \beta_i^2 
\end{pmatrix}^{-1}
\begin{pmatrix}
\sum \alpha_i\mathbf{x}_i \\
\sum \beta_i\mathbf{x}_i
\end{pmatrix} $$

所以给定一组索引，需要我们计算颜色的两个加权和、权重的三个加权和以及一个2X2矩阵的逆矩阵。而如果能提前知道索引，权重的加权和就固定了，而矩阵的逆也能预计算了。

一个简单的BC1编码策略是使用一种简单的启发式算法（a simple heuristic）计算最初的索引，然后通过求解上述等式重新计算端点，最终根据最新的端点更新索引。重复这些步骤直到误差不在降低。这个策略被[stb_dxt.h](https://github.com/nothings/stb/blob/master/stb_dxt.h)所采用。Fabian Giesen也写了[一篇博客详细地阐述了这个实现](https://fgiesen.wordpress.com/2022/11/08/whats-that-magic-computation-in-stb__refineblock/)。

另一种方法是解决所有可能的索引组合的优化问题。在一个4X4的块中，每个纹素的索引占用2位，索引组合的总数是2<sup>32</sup>个，显然为每个组合都求解等式是不现实的。为了让这个问题变得简单一些，[Simon Brown提出了一个聪明的想法](https://www.sjbrown.co.uk/posts/dxt-compression-techniques/)，那就是只考虑那些保留“total order”的索引组合。将颜色投影到一条线上，将它们排序并分为4组，为每组分配一个索引。由于这样做之后，索引组合会受到那条线上的颜色排序的约束，所以会少很多。（应该是这么个意思，the number of ways in which we can do that is much smaller as the index assignment is now constrained by the order of the colors on the line，反正我没读懂）

为了计算和枚举16个索引和4种颜色可能的分组，我们可以使用与下面类似的算法：

``` python
cluster_count = 0
for c0 in 0..15:          # 第1个集群(c0)的纹素数
  for c1 in 0..(15 - c0): # 第2个集群(c1)的纹素数（剩余15-c0）
    for c2 in 0..(15 - c0 - c1): # 第3个集群(c2)的纹素数（剩余15-c0-c1）
      c3 = 16 - (c0 + c1 + c2)  # 第4个集群自动确定
      cluster_count += 1
      print(c0, c1, c2, c3)
```

最终得到的索引组合只剩下969种。求解这969个方程可得近似最优解。还是近似是因为端点a,b并非精确存储，而是被clamp和量化（quantized）的。实际上这是一个离散优化问题（box-constrained integer least squares，盒约束整数最小二乘），而我们通过解决一个连续优化问题来获得原问题的近似解，并对解做clamp和量化。

用来决定颜色的排序的线至关重要。最显而易见的选择是使用最佳拟合直线（best fit line），而它似乎在实践中也是效果最好的。再计算这条直线时必须要有足够高的精度。我提出使用幂迭代法（power iterations）来计算协方差矩阵的第一特征向量的方向（I proposed to use power iterations in order to compute the direction of the first eigenvector of the covariance matrix），但这个方法对初始的近似值十分敏感。在早期的实现中，我使用(1, 1, 1)向量，这在最佳拟合直线与亮度轴垂直时会完全失败。我有一个避免这个问题的改进策略，以后有机会我会详细地说明。

Simon Brown尝试通过使用端点间线段的方向迭代优化（大概是把端点间所有方向都试一遍？），但实践中，经常会出现第一次迭代得到的结果反而质量最好的情况，所以不推荐。

无论排序后分成多少组，后续的过程都是差不多的。比如，在3色模式中我们分成3组，权值有这三种选择：0，1/2和1。我们使用相同的流程去枚举等式：

```python
cluster_count = 0
for c0 in 0..15:          # 第1个集群(c0)的纹素数
  for c1 in 0..(15 - c0): # 第2个集群(c1)的纹素数（剩余15-c0）
      c2 = 16 - (c0 + c1 + c2)  # 第3个集群自动确定
      cluster_count += 1
      print(c0, c1, c2)
```

这种情况下，索引组合要少得多，只有153种。尽管优化的花销要小很多，三色模式也依然几乎不能产出比四色模式更高质量的结果。so the additional cost rarely justifies the effort unless you want to squeeze as much quality as possible out of the format.（我读不懂这句话了）

三色模式在块中存在颜色接近黑色的纹素时有不错的表现。在这个模式中，第四个颜色被用来表示透明度。alpha只需要被预乘（不是，怎么乘？），也因为这个原因，对应的RGB通道是黑色。通过忽略哪些接近黑色的纹素，我们可以计算一条最佳拟合直线，它对剩下的颜色的拟合要准确很多，并且得到的结果的误差也大幅下降。但是，这种策略下得到的纹理可能会出现不在预期中的alpha值。某些平台允许对alpha通道进行swizzle操作设置为255，但在其他的平台上，必须确保着色器没有假设为不透明。

对于其他有更多调色盘条目数的格式，这个优化策略不是也别有用，如下所示，条目数增长时，分组的数量会急剧增加：

```
2 ->      17
3 ->     153
4 ->     969
5 ->    4845
6 ->   20349
7 ->   74613
8 ->  245157
```

Rich的BC1压缩器（[rgbcx](https://github.com/richgel999/bc7enc_rdo/blob/master/rgbcx.cpp)）中的一个优化策略是，减少需要考虑的分组之间的组合的数量。如果你用直方图来可视化分组的分布，就能注意到有些分组间组合的出现频率明显更高。通过剪枝（pruning）分组列表，可以牺牲部分质量来提升编码速度。但是我也会在后文中讲解为什么我没有采用这个策略。

到目前为止，我都在假设硬件使用理想的权重{0, 1/3, 2/3, 1}来进行颜色插值。但在实践中，正如Fabian所说的，每个GPU都使用不同的近似值。若针对特定平台开发，在求解最小二乘问题时使用对应权重可获得更高质量的结果。

## 向量化

在最初的分组拟合实现（cluster fit implementation，比起聚类、簇之类的，分组至少好动一点，所以包括上面，分组指的就是cluster）中，我和Simon使用了SSE2和VMX指令来加速求解程序。这些向量指令可以同时操作4个float。我们通过将权重存放于 alpha 分量并与 RGB 一同处理来提高利用率。但这样做降低了代码的可读性，而且性能上也只比标量实现快了2.3倍。

在这个实现中，我们使用了三重嵌套循环来遍历所有可能的分组组合，并以增量方式计算（incrementally compute）求解最小二乘系统所需的颜色总和：

```glsl
vec4 x0 = 0;
for c0: 0..15 {
  vec4 x1 = 0;
  for c1: 0..15-c0 {
    vec4 x2 = 0;
    for c2: 0..15-c1-c0 {
      alphax_sum = x0 + x1 * (2.0f / 3.0f) + x2 * (1.0f / 3.0f);
      …
      x2 += color[c0+c1+c2];
    }
    x1 += color[c0+c1];
  }
  x0 += color[c0];
}
```

这种方法在当时效果尚可，但无法很好地扩展到如今的CPU中更大的向量寄存器，并且增量式计算的性质导致了大量的管线依赖，限制了性能提升。

在我的[CUDA实现](https://developer.download.nvidia.cn/compute/cuda/1.1-Beta/x86_website/projects/dxtc/doc/cuda_dxtc.pdf)中，我使用了一种不同的方法：为每种分组组合分配一个线程，预计算并加载所有分组索引，然后在各自线程中独立求解最小二乘系统。

在这种设置中，我之前使用的增量式方法是无法使用的，所以我通过循环遍历16种颜色来计算相应的总和：
``` c
parallel for i: 0..968 {
  indices = total_indices[i];
  alphax_sum = {0, 0, 0};
  for j: 0..15 {
    index = (indices >> (2*j)) & 0x3;
    alpha = weight(index);
    alphax_sum += alpha * colors[j];    
    ...
  }
  ...
}
```

在我回顾CPU实现时，我打算按照这些思路做一些事情。但是最终我选择了借鉴Rich Geldreich的技巧：使用前缀和表快速计算部分颜色和（partial color sums）。

首先计算排序后的颜色的总和：

```cpp
color_sum[0] = { .r = 0, .g = 0, .b = 0 };
for (int i = 1; i <= color_count; i++) {
    color_sum[i].r = color_sum[i - 1].r + colors[i].r;
    color_sum[i].g = color_sum[i - 1].g + colors[i].g;
    color_sum[i].b = color_sum[i - 1].b + colors[i].b;
}
```

接着，对于任意一个分组，通过从表中的两个条目相减，可以轻松地计算出颜色的部分和：

```cpp
parallel for i: 0..968 {
  c0, c1, c2 = total_clusters[i];
  x0 = color_sum[c0] - 0;
  x1 = color_sum[c1+c0] - color_sum[c0];
  x2 = color_sum[c2+c1+c0] - color_sum[c1+c0];
  alphax_sum = x0 + x1 * (2.0f / 3.0f) + x2 * (1.0f / 3.0f);
  ...
}
```

在实践中，直接读取分组对应的前缀和，这样计算颜色的总和就只需要两次减法：

```cpp
parallel for i: 0..968 {
  c0, c1, c2 = total_clusters[i];
  x0 = color_sum[c0];
  x1 = color_sum[c1];
  x2 = color_sum[c2];
  x2 -= x1;
  x1 -= x0;
  alphax_sum = x0 + x1 * (2.0f / 3.0f) + x2 * (1.0f / 3.0f);
  ...
}
```
(不是，你上面那段代码不是有个减0吗。。。所以也是两次减法吧。当然x之间相减应该能减少查表次数？)

注意我们不需要计算x<sub>3</sub>，也就是第四个分组颜色的总和。这是因为这个值只有在计算$ \sum \beta_i x_i $时是必要的，而我们已经知道了权重是对称的，所以计算可以被简化为：

```cpp
betax_sum = color_sum[16] - alphax_sum;
```
就用不上x<sub>3</sub>了。

为了向量指令能高效的执行计算，在查询前缀和表时必须要防止标量加载（In order to do this efficiently with vector instructions it’s necessary to lookup the values from the summation tables without falling back to scalar loads）。

这在使用AVX512指令集时能很轻松地完成。前缀和表有17个条目，其中第一个必然是0，所以一个512位的寄存器可以加载完整的前缀和表。索引值全部减一，如果索引是负的就把值设为0。并使用掩码化排列指令_mm512_maskz_permutexvar_ps直接索引，同时通过掩码将第一个索引归零。

```cpp
__m512 vfltmax = _mm512_set1_ps(FLT_MAX);
__m512 vr_sum = _mm512_mask_load_ps(vfltmax, loadmask, r_sum);
__m512 vg_sum = _mm512_mask_load_ps(vfltmax, loadmask, g_sum);
__m512 vb_sum = _mm512_mask_load_ps(vfltmax, loadmask, b_sum);

vx0.x = _mm512_maskz_permutexvar_ps(c0 >= 0, c0, vr_sum);
vx0.y = _mm512_maskz_permutexvar_ps(c0 >= 0, c0, vg_sum);
vx0.z = _mm512_maskz_permutexvar_ps(c0 >= 0, c0, vb_sum);

vx1.x = _mm512_maskz_permutexvar_ps(c1 >= 0, c1, vr_sum);
vx1.y = _mm512_maskz_permutexvar_ps(c1 >= 0, c1, vg_sum);
vx1.z = _mm512_maskz_permutexvar_ps(c1 >= 0, c1, vb_sum);

vx2.x = _mm512_maskz_permutexvar_ps(c2 >= 0, c2, vr_sum);
vx2.y = _mm512_maskz_permutexvar_ps(c2 >= 0, c2, vg_sum);
vx2.z = _mm512_maskz_permutexvar_ps(c2 >= 0, c2, vb_sum);
```

NEON没有打包的标量置换（packed scalar permutes）和512位的寄存器，但是支持[vqtbl4q_u8](https://developer.arm.com/architectures/instruction-sets/intrinsics/#q=vqtbl4q_u8)，这是一种TBL指令的形式，用于从4个源寄存器中执行向量查找。它不像AVX512那么方便，因为它在字节层面进行操作。但这只是意味着我们需要多做一些预计算，将分组总和的总和（the sums of cluster sums）转换成字节偏移量。而且有些地方还更加方便，比如如果索引越界，它会直接返回0，而不需要掩码和负索引。

```cpp
vx0.x = vreinterpretq_f32_u8(vqtbl4q_u8(r_sum, idx0));
vx0.y = vreinterpretq_f32_u8(vqtbl4q_u8(g_sum, idx0));
vx0.z = vreinterpretq_f32_u8(vqtbl4q_u8(b_sum, idx0));

vx1.x = vreinterpretq_f32_u8(vqtbl4q_u8(r_sum, idx1));
vx1.y = vreinterpretq_f32_u8(vqtbl4q_u8(g_sum, idx1));
vx1.z = vreinterpretq_f32_u8(vqtbl4q_u8(b_sum, idx1));

vx2.x = vreinterpretq_f32_u8(vqtbl4q_u8(r_sum, idx2));
vx2.y = vreinterpretq_f32_u8(vqtbl4q_u8(g_sum, idx2));
vx2.z = vreinterpretq_f32_u8(vqtbl4q_u8(b_sum, idx2));
```

最初我想用AVX2和SSE2指令来实现这个。

我最初尝试用AVX2来执行掩码查找，那时候用两个寄存器来加载前缀和表。在每个寄存器上都使用_mm256_permutevar8x32_ps，并且用_mm256_blendv_ps将结果结合，掩码用来处理0元素：

```cpp
vlo = _mm256_permutevar8x32_ps(vlo, idx);
vhi = _mm256_permutevar8x32_ps(vhi, idx);
v = _mm256_blendv_ps(vlo, vhi, idx > 7);
v = _mm256_and_ps(v, mask);
```

这样做的效果不错，但是Fabian Giesen指出这两个函数`permute`和`blend`指令会竞争同一个执行端口，他建议先在查询表的上半区时执行一次`XOR`操作：

```cpp
vhi = _mm256_xor_ps(vhi, vlo);
```

这样一来，就可以用一系列的`cmp`、`and`和`xor`来“模拟”原先的`blend`：

```cpp
vlo = _mm256_permutevar8x32_ps(vlo, idx);
vhi = _mm256_permutevar8x32_ps(vhi, idx);
v   = _mm256_xor_ps(vlo, _mm256_and_ps(vhi, idx > 7));
v   = _mm256_and_ps(v, mask);
```

这一改动带来了显著加速，更酷的是，同样的思路也可以扩展到表更大或寄存器更小的情况。例如，在 SSSE3 上，我们可以通过使用`pshufb`指令，沿用与VTL NEON代码路径中相同的表，但同样需要对表的上半区执行`xor`操作：

```cpp
tab3 = _mm_xor_ps(tab3, tab2);
tab2 = _mm_xor_ps(tab2, tab1);
tab1 = _mm_xor_ps(tab1, tab0);
```

然后在运行时，我们使用`pshufb`结合多个排列来模拟查表：

```cpp
v = _mm_shuffle_epi8(tab0, idx);
idx = _mm_sub_epi8(idx, _mm_set1_epi8(16));

v = _mm_xor_si128(v, _mm_shuffle_epi8(tab1, idx));
idx = _mm_sub_epi8(idx, _mm_set1_epi8(16));

v = _mm_xor_si128(v, _mm_shuffle_epi8(tab2, idx));
idx = _mm_sub_epi8(idx, _mm_set1_epi8(16));

v = _mm_xor_si128(v, _mm_shuffle_epi8(tab3, idx));
```

在第二个参数为负时，`pshufb`会把目标值设为0。这使得我们不需要像在使用AVX2时那样额外执行`and`和`cmp`操作，并且自动处理了前缀和表中零元素的索引。

为了将重点放在我认为有趣的地方，我跳过了很多实现细节。但如果你对此很感兴趣，这是[完整的实现](https://github.com/castano/icbc/blob/master/icbc.h#L2347)。

## 加权分组拟合（Weighted Cluster Fit）

ICBC（说实话有点出戏）压缩器与其他大多数压缩器有一个重要的差别，那就是它支持逐纹素权重。这意味着可以根据每个纹素关联的权重来缩放对应的等式（scale the equation corresponding to each texel with the associated weight，这里贴原文是我不知道缩放等式是什么意思。。。），而不是用常规的方法求解最小二乘等式。

这样做能显著提升alpha贴图（alpha map）的质量，使压缩器在近似不透明纹素时要比半透明纹素精确的多。这在压缩lightmap时也很重要，压缩器可以忽略位于chart footprint（？）之外的纹素。该方法还支持非严格4×4的块尺寸，这在压缩RGBM编码的纹理时很有用。由于RGBM编码中M用来是分别与RGB通道相乘的，M值较低的纹素的误差的重要性低于M值较高的纹素的误差。另一个应用合并了感知度量（perceptual metrics），基于平滑度和图像的其他特征来调整这些权重贴图（weight map，哪些？还是说是RGBM的M通道？）

但这样做也引入了一些额外的花销。不只是因为在计算最小二乘矩阵的总和时必须要缩放α<sub>i</sub>项和β<sub>i</sub>项，主要是如果没有纹素的权重，每个分组组合对应的最小二乘矩阵可以预计算并存储。使用固定权重时，求解方程组时只需要加载预计算的逆矩阵并执行向量或者矩阵乘法。

这个方法比实时求逆要快很多，因此我一度维护着两个版本的代码。一个用于输入值已经加权的情况，另一个用于输入值没有附带权值的情况。

然而，加权分组拟合方法有另外一个优势。那就是颜色块常包含一些有相同的值得纹素。在这些情况下，可以减少块中颜色的数量并相应地调整权重。这样做能显著提高性能。以为分组组合的数量取决于颜色的数量，而且随着颜色数量的增长，分组组合数量的增长速度远超线性增长：

![ClusterNum](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/14/ColorNum.png)

| Unique Colors | Cluster Combinations |
|---------------|----------------------|
| 1             | 3                    |
| 2             | 9                    |
| 3             | 19                   |
| 4             | 34                   |
| 5             | 55                   |
| 6             | 83                   |
| 7             | 119                  |
| 8             | 164                  |
| 9             | 219                  |
| 10            | 285                  |
| 11            | 363                  |
| 12            | 454                  |
| 13            | 559                  |
| 14            | 679                  |
| 15            | 815                  |
| 16            | 968                  |

例如，16种颜色时需处理969种组合，12种颜色时降至454种（约半数），8种颜色时仅164种（约17%）。预计算方法仅在颜色数严格为16时更快。当颜色数为15时，加权方法已具有相近速度，而实际含有16种不同颜色的色块极为罕见。

最后，加权分组拟合还有一个优势，那就是提供了一种简单的方法去调节输出的质量和减少编码一个块的时间。我们只需要对输入的颜色进行聚类（cluster）或吸附（snap）来减少块中的颜色总数就行。

下图展示了在调节分组阈值（clustering threshold）时，时间和压缩质量的变化：

![CompQuality](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/14/CompQuality.png)

该策略或许可能可以与Rich的方法结合，但他的方法要求预计算分组拟合中与特定颜色数对应的那部分子集（我忘了，但上文应该有讲）。当颜色数可变时，需要调整和预计算的数据量会显著增加。

## 最后的话

我的实现中也有很多比较粗糙的地方，我确信还能进一步压榨出一些性能。代码中的关键部分没有向量化，这在低质量设定下非常显眼（上面那张图中左侧的空白区域）。算法也还有改进空间，将来有机会我会讲一讲。

BC1格式放现在已经不是特别有价值了，但是其中有很多技术在别的设定下也依然在使用。在BC7和ASTC之类的现代格式中，搜索空间相比BC1而言十分巨大，以至于编码器不再花费巨大的代价针对特定的分区（partition）和模式做优化，这种时候这些技术就还有一部分仍然具有参考价值了。