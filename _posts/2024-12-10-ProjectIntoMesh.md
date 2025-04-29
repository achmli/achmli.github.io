---
layout:       post
title:        "应该是古早的某种被称为Billboard Clouds的LOD技术-Part3-生成网格"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - LOD生成
    - 图形学
    - Impostor
---

在将三角形分配完并且有了最佳拟合平面后，怎么把三角形投影到平面上，并且把平面变成我们想要的网格就是新的问题了。

# 投影

```cpp
void copyMeshIndicesIndex()
{
    for (auto& triangles : trianglesBeforeProj)
    {
       std::vector<unsigned int> indice(triangles.size() * 3);
       for (auto& triangle : triangles)
       {
          indice.emplace_back(triangle.indices.x);
          indice.emplace_back(triangle.indices.y);
          indice.emplace_back(triangle.indices.z);
       }
       bbcMeshIndicesIndex.emplace_back(indice);
    }
}
```

第一步如上。在之前划分平面或者簇的时候已经将三角形区分完成，所以相当于用一个数组保存要投影到这个平面的顶点（要按顺序，毕竟每三个顶点一组就是一个三角形），然后再用一个数组存储所有平面的这个顶点索引数组。

然后是遍历每个三角形，将每个顶点投影。

计算顶点到平面的投影的方法是：

$$ t=\frac{A \cdot X_0 + B \cdot Y_0 + C \cdot Z_0 + D}{A^2 + B^2 + C^2} $$

其中 A、B、C、D 都是用来定义平面的：

$$ A \cdot X + B \cdot Y + C \cdot Z + D = 0 $$

其中 (A, B, C) 是平面的法向量，D 是平面常数项，可以通过平面法向量和距离原点的距离得到。

```cpp
float D = -(normal.x * (normal * distance).x + 
            normal.y * (normal * distance).y + 
            normal.z * (normal * distance).z);
para = glm::vec4(normal, D);
```

这部分的代码是D的计算，具体normal的计算，前面提到的各种算法中都提及了法线的计算，但是距离没有详细说。

除了 Stochastic BBC Algorithm 外，其他算法都是拟合平面的法向量与 bin 或者 cluster 的质心的坐标的点积。 Stochastic BBC Algorithm 则是使用第一个三角形的扰动后的第一个顶点的位置取代其他算法中的质心来做点积。

这样就可以完成顶点的投影了。

# 构造矩形

在将三角形的顶点投影到各自的平面后，我们需要知道投影后的边界在何处，然后用一个矩形包住所有投影后的三角形。

### 初始化

初始化就两步，定义一个矩形的数组用来存储最后生成的各个矩形，以及一个二维坐标的动态数组，用于存储三角形顶点在平面局部坐标系下的 2D 投影。

接下来就是用循环依次完成每个平面的矩形的构建。

### 将三角形顶点转换到局部坐标系

```cpp
glm::vec3 z_axis = bbc[i].normal;
glm::vec3 x_axis_tmp = glm::vec3(0, 0, 1);
glm::vec3 y_axis = glm::normalize(glm::cross(z_axis, x_axis_tmp));
glm::vec3 x_axis = glm::normalize(glm::cross(y_axis, z_axis));
glm::mat4 rotateMat;
rotateMat[0] = glm::vec4(x_axis, 0.0f);
rotateMat[1] = glm::vec4(y_axis, 0.0f);
rotateMat[2] = glm::vec4(z_axis, 0.0f);
rotateMat[3] = glm::vec4(0.0f, 0.0f, 0.0f, 1.0f);
glm::mat4 rotateMatReverse = glm::transpose(rotateMat); 
```

首先是经典的旋转矩阵构造的方法，将平面的法线作为 z 轴，加上一个简单的临时的 x 轴，叉积获得 y 轴，然后 y 轴与 z 轴叉积获得真正的 x 轴。

然后使用三个方向轴就可以很轻松地构造出旋转矩阵，但这里我们需要的是它的逆矩阵，由于旋转矩阵必然是正交的，所以转置和逆相同，我们只需要求它的转置就行。

```
for (auto& triangleAfterProj : trianglesAfterProj[i])
{
    glm::vec4 p0_tmp = rotateMatReverse * glm::vec4(triangleAfterProj.p0, 1.0f);
    glm::vec4 p1_tmp = rotateMatReverse * glm::vec4(triangleAfterProj.p1, 1.0f);
    glm::vec4 p2_tmp = rotateMatReverse * glm::vec4(triangleAfterProj.p2, 1.0f);
    proPoints.emplace_back(glm::vec3(p0_tmp.x, p0_tmp.y, p0_tmp.z));
    proPoints.emplace_back(glm::vec3(p1_tmp.x, p1_tmp.y, p1_tmp.z));
    proPoints.emplace_back(glm::vec3(p2_tmp.x, p2_tmp.y, p2_tmp.z));
}
```

再接下来依次将平面中各个三角形的顶点与逆旋转矩阵相乘，然后将它们转换到局部坐标系后的顶点按顺序保存到一个数组中。

### 旋转卡壳算法

在这里可以分为两种情况，如果这个平面包含的顶点只有3个(也就是只有一个三角形，应该不会更少了)，那就直接用最长边作为矩形的一条边，这样能确定两个顶点，再用这条边上的高作为矩形的宽，这样就能计算出另外两个顶点了。

但毕竟一般不会这么少，就需要用到[旋转卡壳(Rotating Calipers)](https://oi.wiki/geometry/rotating-calipers/)算法，具体的可以点开前面的蓝字看一下 oi wiki 上详细的讲解。

在之前我们已经将所有顶点都转换到了局部空间，其中构造局部坐标系时，z 轴使用的是平面的法线，这意味着投影后的坐标再转换后 z 的值一定为0。所以这时候我们就可以只保留每个点的 x 和 y 的值了。

这么做是因为旋转卡壳是一个二维的算法。作用是找到二维点集的最小外接矩形。

+ <b>凸包</b>

首先是计算所有点的[凸包(Convex_Hull)](https://oi.wiki/geometry/convex-hull/)，感兴趣依然可以选择点开链接看 oi wiki 上详细的讲解。

这里用的是 graham's algorithm ，首先找到所有点中位于左下角的点(优先看 y 的值，有多个点的 y 同样是最小时选择其中 x 值最小的)作为基准点 x<sub>base</sub>，将剩余的点按照与基准点的极角的大小排序。点 (x<sub>i</sub>, y<sub>i</sub>)与基准点的极点用下面的方法计算：

$$ \theta = arctan \left(\frac{y_i - y_{base}}{x_i - x_{base}}\right) $$

排序后，所有的点按照逆时针顺序排列。

然后将极点和极角最小的点(排序后在除基准点外在最前的点)作为起始凸包顶点。按排序后的顺序遍历剩余的点。第二近加入凸包的点 P<sub>1</sub> ，最近加入凸包的点 P<sub>2</sub>，和遍历到的点P<sub>3</sub>，用geCross函数计算三个点组成的向量的叉积。

```cpp
float geCross(point2d p1, point2d p2, point2d p3) {
    return (p2.x - p1.x) * (p3.y - p1.y) - (p2.y - p1.y) * (p3.x - p1.x);
}
```

如果得到的结果大于0，说明 P<sub>3</sub> 在 (P<sub>2</sub> - P<sub>1</sub>) 的逆时针方向，将 P<sub>3</sub> 加入到凸包的顶点中，如果为0，就是三点共线，如果小于0，就是在顺时针方向，这两种情况依然会将 P<sub>3</sub> 加入顶点，但是会将 P<sub>2</sub> 从凸包中剔除。这样遍历完成后，就完成凸包的构建了。

+ <b>初始化</b>

`down, right, up, left`：四个关键点（分别表示矩形的下、右、上、左边缘上的点）。

`area`：当前最小矩形的面积，用于动态更新。

+ <b>旋转卡壳过程</b>

再循环的过程中，我们处理的是点集的凸包。

主循环的逻辑是遍历凸包的每一条边，作为矩形的底边。

然后遍历凸包中所有的点，找到与当前的边点积的只最大的点，作为当前底边的右边界点(right)。

然后计算找到凸包中所有点中与当前底边叉积最大的点，作为当前底边垂直方向的边界点(up)。

最后找到与当前底边点积最小的点，作为当前底边的左边界点(left)。

```cpp
temp.x = arr[right].x + arr[down].x - arr[left].x;	// down 是底边起始的点
temp.y = arr[right].y + arr[down].y - arr[left].y;
Y = getDot(arr[down], arr[down + 1], temp);
```

然后计算面积，高度是垂直方向的边界点到底边的距离，可以由之前计算出来的叉积值除以底边长度得到。宽度是右边界点到左边界点在底边方向上的投影长度，计算方法看上面的代码。

如果是当前的最小面积，就用当前的 down, right, up, left 四个点替换掉之前最小时的这四个点。

tips：计算三个边界点时，寻找的点可以接着上一次循环继续。第一次循环时，up 的位置一定在 right 后，可以从 right 开始遍历，而 left 也可以从 up 开始，所以也更建议按照先右边界点，然后上边节点，最后左边界点的顺序进行。每次计算最大值时，如果下一个点就变小了，那当前的点就已经是最大值了，找最小值时同理，所以同样更建议按照顺序来。

+ <b>计算顶点</b>

```cpp
if (arr[downlast + 1].y == arr[downlast].y) {
    // 水平边情况
    rectangle[0].x = arr[leftlast].x;
    rectangle[0].y = arr[downlast].y;
    rectangle[1].x = arr[rightlast].x;
    rectangle[1].y = arr[downlast].y;
    rectangle[2].x = arr[rightlast].x;
    rectangle[2].y = arr[uplast].y;
    rectangle[3].x = arr[leftlast].x;
    rectangle[3].y = arr[uplast].y;
} else if (arr[downlast + 1].x == arr[downlast].x) {
    // 垂直边情况
    rectangle[0].x = arr[downlast].x;
    rectangle[0].y = arr[leftlast].y;
    rectangle[1].x = arr[downlast].x;
    rectangle[1].y = arr[rightlast].y;
    rectangle[2].x = arr[uplast].x;
    rectangle[2].y = arr[rightlast].y;
    rectangle[3].x = arr[uplast].x;
    rectangle[3].y = arr[leftlast].y;
} else {
    // 一般倾斜情况
    k = (arr[downlast + 1].y - arr[downlast].y) / (arr[downlast + 1].x - arr[downlast].x);

    rectangle[0].x = (k * arr[leftlast].y + arr[leftlast].x - k * arr[downlast].y + k * k * arr[downlast].x) / (k * k + 1.0);
    rectangle[0].y = k * rectangle[0].x + arr[downlast].y - k * arr[downlast].x;

    rectangle[1].x = (k * arr[rightlast].y + arr[rightlast].x - k * arr[downlast].y + k * k * arr[downlast].x) / (k * k + 1.0);
    rectangle[1].y = k * rectangle[1].x + arr[downlast].y - k * arr[downlast].x;

    rectangle[2].x = (k * arr[rightlast].y + arr[rightlast].x - k * arr[uplast].y + k * k * arr[uplast].x) / (k * k + 1.0);
    rectangle[2].y = k * rectangle[2].x + arr[uplast].y - k * arr[uplast].x;

    rectangle[3].x = (k * arr[leftlast].y + arr[leftlast].x - k * arr[uplast].y + k * k * arr[uplast].x) / (k * k + 1.0);
    rectangle[3].y = k * rectangle[3].x + arr[uplast].y - k * arr[uplast].x;
}
```

直接看代码吧，似乎并不值得讲解了。

最后用着四个点组成矩形，保存起来就完成了。



这下似乎已经完成了几何的步骤了，接下来该继续学习一下最基本的贴图的烘焙了。