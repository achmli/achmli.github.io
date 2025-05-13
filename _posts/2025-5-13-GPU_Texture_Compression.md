---
layout:       post
title:        "《见证者》引擎技术博客的扩展阅读——各个图形接口的GPU纹理压缩"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - 《见证者》博客翻译
    - 图形学
---


> 因为十分喜欢《见证者》，所以想试着翻译一下他们的技术博客。
>
> 发现Ignacio Castano的个人博客上也有一些技术文章，而且这个博客一直在更新，所以可能有些文章是值得参考的。
>
> 这个博客的project页面里写了作者参与过的项目。令人不禁感叹这大概就是大神吧。但可惜博客里技术分享的内容算不上多。
>
> 这篇文章发布于2025年2月20日，但我不懂压缩，所以我不是很能判断这篇文章是否有用。
>
> 有用AI辅助翻译，AI真是我叠捏。
>
> 博客链接：[Ignacio Castaño](https://www.ludicon.com/castano/blog/)
>
> 原文链接：[GPU Texture Compression Everywhere](http://www.ludicon.com/castano/blog/2025/02/gpu-texture-compression-everywhere/)
>
> 作者： Ignacio Castaño

在我2005年加入绿色核弹公司时，我的主要目标之一是参与制作纹理和网格处理工具。NVIDIA Texture Tools被广泛使用了，而 Cem Cebenoyan、Sim Dietrich和Clint Brewer在网格处理和优化方面做出了很多有趣的工作（nvtristrip和nvmeshmender）。这实际上正是我想做的东西。

但是，tools team的优先工作与此不同，所以我最终的工作是参与制作FX Composer。我对此不是很感兴趣，所以2006年，我转到了Developer Technology group。

那时，nv还在和ATI竞争GPU市场的主导地位。虽然又稳固的市场份额，但是nv的真正目标是扩大整个市场。相比于吃到一块蛋糕，更想把蛋糕做大。想象一下如果一个玩家攒机的预算有限，nv的目标是让他把把更多的预算分配到GPU上而不是CPU上。实现这一目标的一种方法是鼓励开发者将工作负载从 CPU 转移到 GPU。（即使只是翻译，我都不想直接翻译这段里面使用的第一人称，太罪恶了黄狗，唉资本。不过其他段落第一人称我都直接翻的，所以文中的“我”都是原作者）

这种推动是更广泛的GPGPU（通用GPU计算）运动的一部分。那时CUDA才刚刚发布，还没有集成到图形接口中，而计算着色器更是还没影。吸引到我们的关注的工作负载中有一个就是GPU纹理压缩。

另一个受到关注的是运行时纹理压缩。

2004年4月，Farbrausch发布了.kkrieger，一个打包后大小只有96KB的FPS游戏，因为关卡、模型和纹理都用了程序化生成。但是直到2007年在[fr-041: debris]{https://www.pouet.net/prod.php?which=30244}开发的后期，他们才开始使用实时的DXT压缩来减少显存占用和提升性能。

差不多在相同的时间，Allegorithmic正在开发ProFx，这是Substance Designer的前身，一个用于实时程序化纹理生成的中间件。ProFX也包含了一个快速的DXT编码器，使程序纹理在加载时能转换成对GPU友好的格式。

[Simon Brown](https://sjbrown.co.uk/)那时正在开发PlayStation Home，索尼的3D社交虚拟世界，玩家在其中可以创造和定制他们的化身（avatar，我超，元。。。宇宙）。为了实现这个目标，他写了一个为PS3的SPU优化的快速DXT编码器，展示了将纹理压缩卸载到并行处理器的潜力。

约翰卡马克一直在谈论megatexture技术，但在2006年，[Jan Paul van Waveren](https://mrelusive.com/)在Intel Software Network上发布他们的[实时DXT压缩实现](https://mrelusive.com/publications/papers/Real-Time-Dxt-Compression.pdf)的细节时，nv的同事们注意到了一个潜在的问题：如果《狂怒》的最终性能是CPU瓶颈，可能会促使玩家升级CPU而不是GPU。这使得GPU上的实时纹理压缩成为了我们的战略重点。

我们遇到的第一个问题是，在D3D 10中，更新一张DXT纹理而不把数据传输回CPU是不可能的。所幸，那段时间OpenGL刚好推出了PBO（pixel buffer object）。尽管不是为我们的目标设计的，PBO提供了一种变通的方法，我们可以将每个块都渲染到一张integer render target上，然后将内容复制到一个PBO中，最后从从PBO中压缩数据，转换成一个DXT压缩纹理。

这是我在与 Jan Paul 共同撰写的论文中使用的技术，这些论文的示例仍可在线找到：

+ [Compress YCoCg-DXT](https://developer.download.nvidia.com/SDK/10/opengl/samples.html#compress_YCoCgDXT)
+ [Compress Normal-DXT](https://developer.download.nvidia.cn/SDK/10/opengl/samples.html#compress_NormalDXT)

这些实例使得我们展示GPU纹理压缩成为可能，也能展示GPU纹理压缩的潜力。

## Direct3D 10

然后我就推动了图形接口的变化，让它们更好地支持这个用例。第一个支持直接从未压缩纹理复制到压缩纹理的图形接口是D3D 10.1。从这个版本开始放松了[CopyResource](https://learn.microsoft.com/en-us/windows/win32/api/d3d10/nf-d3d10-id3d10device-copyresource)和[CopySubresourceRegion](https://learn.microsoft.com/en-us/windows/win32/api/d3d10/nf-d3d10-id3d10device-copysubresourceregion)两个接口的限制，允许具有相同位宽的预结构化纹理和块压缩纹理之间的复制。

更多的细节见：[ Format Conversion Using Direct3D 10.1](https://learn.microsoft.com/en-us/windows/win32/direct3d10/d3d10-graphics-programming-guide-resources-block-compression#format-conversion-using-direct3d-101)

主机上也通过一些硬件供应商提供的底层API实现了这个功能。这个[GDC演讲](https://www.gdcvault.com/play/1012254/Texture-compression-in-real-time)中，来自Volition公司的Jason Tranchida谈论了使用这些API和D3D 10.1实现实时DXT压缩的经验。

## OpenGL

过了一年，OpenGL通过[NV_copy_image](https://github.com/KhronosGroup/OpenGL-Registry/blob/main/extensions/NV/NV_copy_image.txt)也支持了这个特性。然而直到2012年，也就是D3D10支持这个功能的六年后，才在OpenGL4.3中通过[ARB_copy_image](https://github.com/KhronosGroup/OpenGL-Registry/blob/main/extensions/ARB/ARB_copy_image.txt)更加广泛地支持这个功能。

在OpenGL中，与D3D的`CopySubresourceRegion`等效的接口是[glCopyImageSubData](https://registry.khronos.org/OpenGL-Refpages/gl4/html/glCopyImageSubData.xhtml)。与D3D 10中对应的功能类似，它允许从未压缩纹理复制数据到块压缩纹理中，前提是格式兼容，这通常意味着纹素的大小与块的大小相匹配。

这个特性本应该促进GPU纹理压缩在id Tech 5中的使用，使《狂怒》把更多工作负载从CPU转移到GPU上。但是《狂怒》在发行时没有使用GPU纹理压缩，用还是的Jan Paul的论文中描述的基于CPU的方法。

那是我已经开始参与《见证者》的开发了，所以是NVIDIA开发者技术团队的Evan Hart重新审视了这个问题并实现了id Tech 5的GPU纹理压缩，基于我所做的基础工作，并解决了将实时GPU压缩集成到引擎中时遇到的所有实际挑战。

## OpenGL ES

在我开发[Spark](https://ludicon.com/spark/)之前，我都没有太关注这些特性。由于我把注意力转移到了移动端，我才开始对OpenGL ES特别感兴趣，他通过[GL_EXT_copy_image](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_copy_image.txt)扩展来支持这个功能，并且在OpenGL ES 3.2中已经成为了一个核心特性。

在测试这个特性时，我遇到了一个意外的限制：OpenGL ES不支持rg32ui输出图像布局。在输出64位的块时，必须使用rgba16ui：

```glsl
layout(rgba16ui) uniform restrict writeonly highp uimage2D dst;
```

这需要在将数据传递给`imageStore`之前，必须手动将64位的`uvec2`块打包：

```glsl
uvec4 pack_uvec2(uvec2 v) {
    return uvec4(v.x & 0xFFFFu, v.x >> 16, v.y & 0xFFFFu, v.y >> 16);
}
...
imageStore(dst, uv, pack_uvec2(block));
```

这说明，在一个计算着色器普及的世界中，有一个更加简单的方法可以完成相同的任务。通过使用一个计算着色器将压缩的数据写入一个临时的buffer中，我们可以将这个buffer绑定到GL_PIXEL_UNPACK_BUFFER目标，并通过使用[glCompressedTexSubImage2D](https://registry.khronos.org/OpenGL-Refpages/gl4/html/glCompressedTexSubImage2D.xhtml)从中直接获取数据：

```glsl
glBindBuffer(GL_PIXEL_UNPACK_BUFFER, tmp_buffer);
glBindTexture(GL_TEXTURE_2D, dst_texture);
glCompressedTexSubImage2D(GL_TEXTURE_2D, dst_level, dst_x, dst_y, width, height, 
    gl_format, tmp_buffer_size, (const void*)tmp_buffer_offset);
```

在所有设备上，这样做都有很好的效果，并且性能相似。

## Vulkan

（这章好长，符合我对vulkan的刻板印象了。即使只是纹理压缩功能简介，也得是写得最长的。。。）

与OpenGL类似，Vulkan支持从未压缩纹理复制数据到块压缩纹理中。从Vulkan 1.0开始就通过[vkCmdCopyImage](https://registry.khronos.org/vulkan/specs/latest/man/html/vkCmdCopyImage.html)接口支持这个功能了。

所以想象一下当我测试这个功能，发现大多数设备并没有正确实现这个功能时，我有多震惊。下面的截图展示了在Adreno、PowerVR和Mali设备上测试的结果。只有Mali能产出正确的结果！

![vulkan test](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/15/Android-Vulkan-CmdCopyImage-700x581.png)

最初，我觉得我试着将实时纹理压缩引入android vulkan的努力白费了。所幸还有一些希望。我发现了[KHR_maintenance2](https://registry.khronos.org/vulkan/specs/latest/man/html/VK_KHR_maintenance2.html)扩展，允许创建压缩image的非压缩image view，从而完全消除了复制的需要。这个功能在后续的Vulkan 1.1中被推广为核心特性，而Vulkan 1.1恰号是我们的最低要求，所以这看上去是有前景的方案。

可惜，实际才做起来并不简单。由于文档过于简略，我最初的尝试结果是validation error，但在一些努力后，我成功地让它在PC上正确运行了。然而我的乐观没有持续多久，当我开始在移动端开始测试时，结果是灾难性的。下图中左边的两张图来自两个不同的Adreno设备，最右侧的来自一个PowerVR设备：

![vulkan test 2](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/witness/15/Android-Vulkan-RenderToBlockTexelView-700x516.png)

这时，离我开始开发spark已经大概六个月了，感觉一切的努力都要付之东流了。而且这还不是唯一的问题。在Vulkan环境下，我的大多数编解码器都输出不正确，还有编译失败和设备直接崩溃之类的问题。只有最简单的内核能够正确工作，即便如此，它们的性能也远低于OpenGL ES上等效的版本。

感谢我的固执和坚持，我又花了几个月来缩小每个问题的范围。向IHV提交重现案例并尝试每个可能的解决方法。这些努力赢得了回报，几个月后，Spark的所有编解码器都能正常工作了，并且性能都能与GLES版本相当，甚至更好。

这其中许多问题的根源都是我最初对片段着色器的依赖。在当时，我使用的Hype Engine的版本缺乏对计算着色器的支持，所以我第一个集成实验是使用片段着色器运行编解码器，这意味着我不能像在OpenGL中一样，将压缩后的块输出到buffer中，只能将其渲染到纹理上，必须要使用到`vkCmdCopyImage`。

然而，vulkan也允许使用`vkCmdCopyBufferToImage`来升级块压缩纹理。 实际上，这与上传块压缩纹理的命令是相同的，这意味着这个代码路径在多个供应商的设备上已经经过了充分测试，毫无意外地，它能够完美工作。

当使用块压缩纹理imageview时纹理损坏的问题也与片段着色器的使用相关。特别是`VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT`的使用，将这个标志替换为`VK_IMAGE_USAGE_STORAGE_BIT`就完全解决了这个问题。

使这一切正常工作确实充满挑战，并且挑战还被我永远不知道我做错了什么、验证层没有捕捉到错误、不知道是硬件还是软件的问题加强了。所以我将详细解释这个过程：

要创建块-纹素imageview，首先要要用下面几个标志创建一个image：

+ <b>`EXTEND_USAGE`</b>：这允许创建带有`VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT`标志位的块压缩image，尽管这个usage不能正常支持压缩的格式，只要它从块压缩视图中删除即可。
+ <b>`MUTABLE_FORMAT`</b>：这允许我们创建具有不同但兼容格式的image view。
+ <b>`BLOCK_TEXEL_VIEW_COMPATIBLE`</b>：这扩展了兼容格式的列表，包含那些纹素大小与块大小匹配的非压缩格式。

这是一个实例：

```cpp
VkFormat compressed_format = VK_FORMAT_ASTC_4x4_UNORM_BLOCK;
VkFormat uncompressed_format = VK_FORMAT_R32G32B32A32_UINT;

VkImageCreateInfo image_info = { VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO };
image_info.imageType = VK_IMAGE_TYPE_2D;
image_info.format = compressed_format;
image_info.extent = { w, h, 1 };
image_info.mipLevels = 1;
image_info.arrayLayers = 1;
image_info.samples = VK_SAMPLE_COUNT_1_BIT;
image_info.tiling = VK_IMAGE_TILING_OPTIMAL;
image_info.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;

// Note, we create the compressed image with the *STORAGE* usage flag. This is only allowed thanks to EXTENDED_USAGE image flag.
image_info.usage = 
    VK_IMAGE_USAGE_SAMPLED_BIT | 
    VK_IMAGE_USAGE_TRANSFER_DST_BIT | 
    VK_IMAGE_USAGE_STORAGE_BIT;

// Provide the required flags:
image_info.flags = 
    VK_IMAGE_CREATE_EXTENDED_USAGE_BIT | 
    VK_IMAGE_CREATE_BLOCK_TEXEL_VIEW_COMPATIBLE_BIT | 
    VK_IMAGE_CREATE_MUTABLE_FORMAT_BIT;
```

然后你就能正常地分配和创建image并正常的上传数据。

为了创建一个在着色器中采样纹理的imageview，使用压缩格式，但为了成功，必须显式移除VK_IMAGE_USAGE_STORAGE_BIT标志：

```cpp
VkImageViewCreateInfo sample_view_info = {};
sample_view_info.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
sample_view_info.image = image;
sample_view_info.viewType = VK_IMAGE_VIEW_TYPE_2D;
sample_view_info.format = compressed_format;
sample_view_info.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
sample_view_info.subresourceRange.levelCount = 1;
sample_view_info.subresourceRange.layerCount = 1;

// Remove the STORAGE usage flag from this view.
VkImageViewUsageCreateInfo sample_view_usage_info = {};
sample_view_usage_info.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_USAGE_CREATE_INFO;
sample_view_usage_info.usage = image_info.usage & ~VK_IMAGE_USAGE_STORAGE_BIT;
sample_view_info.pNext = &sample_view_usage_info;

VkImageView sample_view = VK_NULL_HANDLE;
vkCreateImageView(device, &sample_view_info, nullptr, &sample_view);
```

为了创建一个image view用来将纹理作为计算着色器中的存储，使用未压缩格式。为了最大化兼容性，你也应该移除`VK_IMAGE_USAGE_SAMPLED_BIT`标志：

```cpp
// Create texel view for storage:
VkImageViewCreateInfo store_view_info = {};
store_view_info.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
store_view_info.image = image;
store_view_info.viewType = VK_IMAGE_VIEW_TYPE_2D;
store_view_info.format = uncompressed_format;
store_view_info.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
store_view_info.subresourceRange.levelCount = 1;
store_view_info.subresourceRange.layerCount = 1;

// Remove the SAMPLED usage flag from this view.
VkImageViewUsageCreateInfo store_view_usage_info = {};
store_view_usage_info.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_USAGE_CREATE_INFO;
store_view_usage_info.usage = image_info.usage & ~VK_IMAGE_USAGE_SAMPLED_BIT;
store_view_info.pNext = &store_view_usage_info;

VkImageView store_view = VK_NULL_HANDLE;
VK_CHECK(vkCreateImageView(device, &image_view_create_info, nullptr, &store_view));
```

Vulkan也提供了`KHR_image_format_list`扩展，在Vulkan1.2中开始支持。这允许你在创建时提供兼容格式的列表。并没有严格要求使用这个扩展，但由于在一些设备上可以提供一些优化，所以推荐使用。

这时一个用法示例：

```cpp
VkImageFormatListCreateInfo format_list_info = {
    VK_STRUCTURE_TYPE_IMAGE_FORMAT_LIST_CREATE_INFO_KHR 
};

VkFormat view_formats[2];
if (physical_device_properties.apiVersion >= VK_API_VERSION_1_2 || supported_extensions.KHR_image_format_list)
{
    view_formats[0] = compressed_format;
    view_formats[1] = uncompressed_format;
    format_list_info.viewFormatCount = 2;
    format_list_info.pViewFormats = view_formats;
    image_info.pNext = &format_list_info;
}
```

你可以用`VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT`标志在相同的流程下创建一个render target纹理，然后在对应的用于采样的压缩的imageview中移除它。然而尽管看上去非常简单，这个方法在很多设备上会失效。因此，我强烈推荐在计算着色器中运行编解码器。

## Direct3D 12

D3D 12也支持D3D 10.1的`CopyResource`接口。但是D3D 12.1中另外提供了创建一个压缩的一个快压缩纹理的Unordered Access View（UAV）。要使用这个功能，首先需要检查设备是否支持`RelaxedFormatCastingSupported`特性：

```cpp
D3D12_FEATURE_DATA_D3D12_OPTIONS12 feature_options12 = {};
hr = device->CheckFeatureSupport(D3D12_FEATURE_D3D12_OPTIONS12,
                                 &feature_options12, sizeof(feature_options12));
if (SUCCEEDED(hr)) {
    supports_relaxed_format_casting = feature_options12.RelaxedFormatCastingSupported;
}
```

相比于Vulkan，这十分简单。唯一的额外要求是使用`ID3D12Device10`中的`CreateCommittedResource3`方法，并且在开头提供兼容格式的列表：

```cpp
DXGI_FORMAT format_list[2] = {
    DXGI_FORMAT_BC7_UNORM, DXGI_FORMAT_R32G32B32A32_UINT
};
hr = device10->CreateCommittedResource3(
    &heap_properties,
    D3D12_HEAP_FLAG_NONE,
    &texture_desc,
    D3D12_BARRIER_LAYOUT_COMMON,
    nullptr,
    nullptr,
    countof(format_list),
    format_list,
    IID_PPV_ARGS(bc_texture));
```

然后你只需要使用列表中的格式创建shader resource views和UAV即可。

## Metal

与Vulkan和D3D 12不同，Metal不支持直接从未压缩纹理复制数据到压缩纹理中。唯一可靠的方法是使用一个计算着色器将压缩的数据写入buffer，然后使用一个位块传输（blit）编码器将buffer中的内容传输到纹理中：

```cpp
let blitEncoder = commandBuffer.makeBlitCommandEncoder()

blitEncoder.copy(
    from: buffer, 
    sourceOffset: bufferOffset, 
    sourceBytesPerRow: bufferRowLength, 
    sourceBytesPerImage: 0, 
    sourceSize: MTLSize(width:width, height:height, depth:1), 
    to: outputTexture, 
    destinationSlice: 0, 
    destinationLevel: 0, 
    destinationOrigin: MTLOrigin(x: 0, y: 0, z: 0))

blitEncoder.endEncoding()
```

如果因为什么原因，编码器将压缩后的数据传递到了一个未压缩的纹理中，则需要两次额外的复制操作：先从纹理复制到buffer中，在从buffer复制到压缩的纹理中。推荐的方法是编码器直接将压缩的块写入buffer中，这样就只需要一次复制了。

很可惜Metal缺乏Vulkan和Direct3D 12中提供的资源类型转换功能。然而，iOS 设备通常在性能上远超 Android 设备，因此在实际应用中，即使存在这一限制，它们也不会落后。主要挑战在于维护一个高效的跨图形接口的抽象，以在各个平台上实现最佳性能，因为这需要略有不同的代码路径和着色器变体。

## 结论

让这一切在各个平台上正常工作就像坐过山车一样。如果我是在一份常规工作中做这件事，那将是一段有趣的旅程；但由于我是在投资自己的资源，这令人非常紧张。很长一段时间，我甚至不确定是否能让Spark在我大多数的目标设备上可靠运行。

最初，我选择将这些细节保密，仅与客户分享，以协助他们的集成工作。然而，我逐渐意识到，许多开发者并未完全理解为了确保Spark在各个平台上良好运行所投入的大量工作，或者我为此承担的风险。

希望这不仅能帮助其他面临类似挑战的人，也能让大家更好地理解 Spark 背后的努力。