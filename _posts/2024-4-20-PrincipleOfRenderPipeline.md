---
layout:       post
title:        "Games106笔记1——绘制流水线原理"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games106
    - Vulkan
    - 图形学
---

# 传统RHI和现代RHI的区别
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/Differ.png" style="zoom:75%" />

主要是PPT中这些。
传统的RHI都是状态机的模式，OpenGL的Context是隐式的，DX的Context是显式的，这个模式使得许多内容对程序员透明，内部无法感知外部的修改，可能在资源的调用上出现错误。
传统的RHI会在内部做好同步，有些时候会导致效率下降，而现代RHI需要程序员去做同步。
如果程序卡在CPU调用而不是GPU的话，使用现代RHI会有更好的效果，因为OpenGL每帧的绘制都会将每个绘制命令调用一次，相比之下Vulkan引入了Command Buffer来解决这个问题。

# Vulkan程序的基本结构
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/Pipeline.png" style="zoom:75%" />

## 初始化
### 创建窗口
通常需要关心窗口的类型是什么Win32，XCB还是WAYLAND。后续创建SwapChain会需要这些信息。
SDL，GLFW等一些窗口第三方库会很方便的获得这些信息。甚至可以帮你完成很多Vulkan的初始化。
### Vulkan层次
![Structure](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/Layers.png)
图中是一个相对复杂的Vulkan程序的结构。一般而言就是一个实例、一个物理设备、一个逻辑设备。这样设计的目的是为了较好地分配多张显卡的任务。

### VKInstance
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/VKInstance.png" style="zoom:75%" />

### Layer
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/Layer.png" style="zoom:75%" />

相当于重载或者获取调试信息的Hook。

### 物理设备
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/PhysicalDevice.png" style="zoom:75%" />

### 队列簇
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/QueueFamily.png" style="zoom:75%" />

### 逻辑设备
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/LogicDevice.png" style="zoom:75%" />

### 交换链
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/SwapChain.png" style="zoom:75%" />

Swapchain是扩展功能，而不是核心渲染功能，因为输出到屏幕并不是必须的。

## 渲染主循环
### 绘制管线
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/RenderingPipline.png" style="zoom:75%" />

### 顶点输入

+ 顶点数据缓存
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/InputAssembly.png" style="zoom:75%" />
顶点输入的一般输入的内容
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/VertexFormat.png" style="zoom:75%" />
顶点输入缓存的布局，顶点坐标和法线由于可能会变化，所以另外用一个buffer存放。

+ 索引缓存
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/VertexIndex.png" style="zoom:75%" />
顶点获取相应的顶点数据需要索引，同时顶点往往被多个三角形公用，同一个顶点的数据会被多次读取，所以索引的分布也会一定程度上影响性能。这部分的影响一般要大于计算的消耗。
+ 图元拓扑类型
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/PrimitiveType.png" style="zoom:75%" />
不同的顶点间的绘制方式，只绘制点，或者绘制线，或者绘制三角型……
+ DrawCall
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/DrawCall.png" style="zoom:75%" />
调用drawcall的方式。如果没有索引缓存就调用Draw，如果有就调用Draw Index，而在顶点数量或者顶点属性未知需要另外计算时，就需要indirect，将direct draw的返回值作为缓存输入GPU。
### 光栅化
+ 顶点着色器编译
  <img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/Compiler.png" style="zoom:75%" />
  顶点着色器通过编译生成SPIR-V才能使用。glsl和hlsl都行。
+ 坐标系
  <img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/Coordinate.png" style="zoom:75%" />
  Vulkan的坐标系，可以看出来是右手系，x轴朝左，y轴朝下。目的是为了Z轴朝向屏幕内，OpenGL的z轴朝向屏幕外，所以裁剪空间现在-1到0计算，再移动到0到1，而计算机浮点数计算的误差导致这里可能出现偏差（离零近精度高，离1近精度低），所以Vulkan做出了这个调整。
+ 绘制的一些属性设置
  <img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/States.png" style="zoom:75%" />
+ 视口
  <img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/ViewPort.png" style="zoom:75%" />

  <img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/Viewport2.png" style="zoom:75%" />
+ Scissor

 
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/Scissor.png" style="zoom:75%" />


### 片段着色器


<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/FragmentShader.png" style="zoom:75%" />

移动端浮点数精度一般16位就足够，如果有些不够，就把那些设置为32位。

### Fragment Buffer输出
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/FragmentBuffer.png" style="zoom:75%" />

### Render Pass
<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/RenderPipeline.png" Style="zoom:75%" />

<img src="https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Pics-Games106/RenderPass.png" style="zoom:75%" />
