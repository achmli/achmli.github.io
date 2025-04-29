---
layout:       post
title:        "应该是古早的某种被称为Billboard Clouds的LOD技术-Part1"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - LOD生成
    - 图形学
    - Impostor
---

就是生成 Billboard Cloud 的算法，这当中几乎所有算法都是用若干四边形的平面替换掉原模型，原模型的顶点投影到邻近的四边形上，这样许多三角形就合成了两个三角形。

而这块的算法内容就是计算四边形的各个参数，顶点位置、数量、大小之类的。

来自[这个项目](https://github.com/StrongerSuperman/Billboardcloud "StrongerSuperman/Billboardcloud: extreme model simplification in real time game scene")。项目的简介中贴出了论文地址，但除了k-means之外的两篇论文都已经被删除了。

# Original BBC Algorithm

由于从项目中理解算法，所以先把这个算法的函数解读一下。

```cpp
void originalPlaneSearch(float epsilon_percentage, int theta_num, int phi_num)
```

函数的形参有误差百分比和球面角度参数化的数量。前者用于控制平面的分辨率，后者决定球面上采样点的个数。

```cpp
int rho_num = 1.5 / epsilon_percentage;   // suggest value in later paper realize
float epsilon = 2 * boundingSphere.radius * epsilon_percentage;
std::vector<Triangle> trianglesTmp = trianglesOrg;

Discretization discretization(maxDistance, epsilon, theta_num, phi_num, ro_num);
discretization.updateDensity(trianglesTmp, 0);
```

这是一些参数的初始化，rho_num 就是采样的球面的数量。

epsilon 是根据包围球的半径和误差百分比计算出的误差。包围球的大小取决于模型的尺寸。

Discretization 这个类的主要功能就是利用 theta_num、phi_num 和 rho_num 这三个参数生成采样点的位置，或者说是两个球面上相邻的八个点形成的一个块，这里将其称为 bin 。updateDensity这个函数是用来计算每个模型再每个 bin 中的三角形数量。

然后是通过循环去寻找最佳拟合平面。

```cpp
// 这是 GPT 简化后的代码
while (!trianglesTmp.empty())
{
    // 重新更新当前三角形索引
    for (int i = 0; i < trianglesTmp.size(); i++)
    {
        trianglesTmp[i].index = i;
    }

    // 找到最大密度 bin
    glm::vec3 maxDensityBinIndex = discretization.computeMaxDensity().first;
    Bin maxDensityBin(discretization.bins[maxDensityBinIndex.x][maxDensityBinIndex.y][maxDensityBinIndex.z]);

    // 提取 bin 中的有效三角形并拟合平面
    std::vector<Triangle> binValidSet = discretization.computeBinValidSet(trianglesTmp, maxDensityBin);
    Plane refinedPlane = discretization.refineBin(binValidSet, maxDensityBin);

    // 根据拟合平面，移除三角形
    std::vector<int> planeValidSetIndex = discretization.computePlaneValidSetIndex(trianglesTmp, refinedPlane);
    for (int index : planeValidSetIndex)
    {
        trianglesTmp.erase(trianglesTmp.begin() + index);
    }
}
```

循环的主要步骤是：

1. 更新三角形的索引。
2. 找到密度最大的bin。
3. 调用refineBin函数计算这个bin的最佳拟合平面，将拟合三角形存储到TriangleBeforeProj数组中。
4. 移除已拟合的三角形，并且更新bin的密度。

```cpp
if(binValidSet.size!=0)
{
    ...
}
else
{
	// for the last little remain triangles, there's two way to cope with them:
	// 1. return the best fitted plane for the current remain faces
	// 2. simply employ "face skip"
	skipFaceNum = trianglesTmp.size();
	return;
}
```

在所有有效的bin被处理完后，可能有部分三角形未被处理。这部分是处理这些三角形，方法是跳过这些三角形。

```cpp
for (auto& triangles : trianglesBeforeProj)
{
    std::vector<glm::vec3> points;
    for (auto& triangle : triangles)
    {
        points.emplace_back(triangle.p0);
        points.emplace_back(triangle.p1);
        points.emplace_back(triangle.p2);
    }
    auto fitted = best_plane_from_points(points); // SVD 求解平面
    auto centroid = fitted.first;
    auto normal = fitted.second;
    if (glm::dot(centroid, normal) < 0)
    {
        normal = -normal; // 确保方向一致
    }
    Plane bestFitted(normal, glm::abs(glm::dot(centroid, normal)));
    bbc.emplace_back(bestFitted); // 存储平面
}
```

总之最后是计算每个拟合的三角形的最佳拟合平面(有点不能理解)。

### refineBin

那来看看这个函数吧。

```cpp
// 首先看一下binValidSet是怎么计算的吧，虽然这不是refineBin中的一部分
std::vector<Triangle> computeBinValidSet(const std::vector<Triangle>& triangles, const Bin& bin)
{
	std::vector<Triangle> binValidSet;
	for (auto& triangle : triangles)
	{
		// we use the notion of "simple validity":
		// that is a bin is valid for a triangle as long as there exists a valid plane for the triangle in the bin 
		// if the ro min and ro max is in the range of bin's ro range, we think this triangle is valid for the bin
		glm::vec2 roMinMax = computeRoMinMax(triangle, bin.thetaMin, bin.thetaMax, bin.phiMin, bin.phiMax);
		if (roMinMax.x == -1 && roMinMax.y == -1)
			continue;

		if (!(roMinMax.y < bin.roMin) && !(roMinMax.x > bin.roMax)) // 好怪啊，大概是比起什么情况符合更想讲清楚什么情况不符合吧
		{
			binValidSet.emplace_back(triangle);
		}
	}
	return binValidSet;
}
```

就是计算在当前的bin的θ和φ范围内计算每个三角形和球心的最大距离和最小距离，如果有交集就是有效的三角形。

refineBin的形参最主要就是这个有效集合。

然后获取这个bin的中新平面，就是通过bin的参数计算出中心的点，然后通过这个点和球心计算出平面的法线。

```cpp
Plane centerPlane = Plane(maxDensityBin.centerNormal, maxDensityBin.roCenter);
std::vector<int> centerPlaneValidSetIndex = computePlaneValidSetIndex(validSet, centerPlane);

if (centerPlaneValidSetIndex.size() == validSet.size())
{
    // 调整法向量方向（确保 thetaCenter > pi 时法向量一致）
    if (maxDensityBin.thetaCenter > pi)
    {
        centerPlane = Plane(-centerPlane.normal, centerPlane.distance);
    }

    // 计算平面上点到平面的最大距离，用于调试
    float maxDis = 0.0f;
    for (auto& triangle : validSet)
    {
        float d0 = centerPlane.calcuPointDistance(triangle.p0);
        float d1 = centerPlane.calcuPointDistance(triangle.p1);
        float d2 = centerPlane.calcuPointDistance(triangle.p2);
        maxDis = std::max({d0, d1, d2});
    }
    return centerPlane;
}
```

然后计算这个平面能拟合的三角形集合。方法是计算三角形和这个平面的最大距离，对比允许拟合的最大距离(一般是 bin 的中心与球心的距离)。

如果 bin 中所有有效的三角形集合都能拟合，那么就返回这个中心平面。

```cpp
std::vector<Bin> neighborBins = getBinNeighbors(maxDensityBin);
for (auto& neighborBin : neighborBins)
{
    std::vector<Bin> subdividBins = subdivideBin(neighborBin);
    for (auto& subdividBin : subdividBins)
    {
        computeDensity(validSet, subdividBin);
        if (subdividBin.density > binMax.density)
        {
            binMax = subdividBin;
        }
    }
}
std::vector<Triangle> binMaxValidSet = computeBinValidSet(validSet, binMax);

if (!binMaxValidSet.empty())
{
    return refineBin(binMaxValidSet, binMax);
}
```

当 centerPlane 不能完全拟合 validSet 时。获取当前 bin 的 26 个邻居，对每个邻居 bin 进行划分，生成更小的 bin，这里是每个bin分成了8个。计算每个子 bin 的密度，选择密度最大的子 bin。如果找到的密度最大的子 bin 中有有效三角形集合，则递归调用 `refineBin`，对新的三角形集合进一步优化。

最后如果密度最大的细分 bin 中并没有有效的三角形的集合，但是之前计算的能与中心平面拟合的三角形集合不为空，就用所有的这些三角形的顶点用SVD求解最佳拟合平面，否则直接返回中心平面。

# Stochastic BBC Algorithm

```cpp
void stochasticPlaneSearch(float epsilon_percentage, int iter)
```

输入的参数是误差百分比和迭代次数。

```cpp
float epsilon = 2 * boundingSphere.radius * epsilon_percentage;
std::vector<Triangle> trianglesTmp = trianglesOrg;
```

需要初始化的参数少于上一个算法。并且这个两个参数也是上一个算法中都有的。

然后就是主循环，循环可以分成下面几个步骤：

1. 在剩余的三角形中随机选择一个。
2. 然后在法线方向对这个三角形的三个顶点添加扰动，范围在[-epsilon,epsilon]。
3. 计算扰动后的三角形的法线，这个法线就是拟合平面的法线。
4. 计算原点到这个平面的距离，这样就可以把这个平面构造出来了。
5. 遍历所有剩余的三角形，计算它们的顶点与平面的距离，如果三个顶点的距离都小于误差epsilon，那么这个三角形是有效的，再计算这个三角形在平面上的投影面积，下面的代码是投影面积的计算方法，并记录所有有效的三角形的索引。

```cpp
float angle = glm::acos(glm::abs(glm::dot(bb.normal, trianglesTmp[j].normal)));
float angular = (pi / 2 - angle) / (pi / 2);
area += trianglesTmp[j].getArea() * angular;
```

6. 如果有效投影面积是目前所有的平面中最大的，就把最佳拟合平面替换成当前的。并且记录这个平面所有有效的三角形。
7. 以上的步骤根据函数输入的形参迭代次数iter循环iter次，然后将这次迭代出的最佳平面保存到数组中。
8. 然后将已经拟合的三角形从triangleTmp中移除。重复执行以上步骤直到triangleTmp为空或者不再能有新平面可以拟合剩余的三角形中的任意一个。

# K-means BBC Algorithm

```cpp
void kMeansPlaneSearch(int k, int maxIter)
```

输入的参数是要创建的簇数和最大迭代次数。

第一步与之前的算法相同都是将所有的三角形拷贝一份临时的备份。

然后是这个算法的初始化设置。

### 第一步 初始化

首先构造一个能包围所有三角形的包围球。

用函数的输入值k计算包围求k个位置的切平面。

```
static std::vector<glm::vec3> gen_fibonacci_sphere_point(glm::vec3 center, float radius, int k)
{
    std::vector<glm::vec3> points; // 用于存储生成的点
    float golden_angle = pi * (3 - sqrt(5)); // 计算黄金角
    float r, theta, z; // 定义变量 r, theta 和 z
    for (int i = 0; i < k; i++) // 循环生成 k 个点
    {
       theta = golden_angle * i; // 计算当前点的角度 theta
       z = (1 - 2.*i / k)*(1 - 1. / k); // 计算当前点的 z 坐标
       r = sqrt(1 - z * z); // 计算当前点的半径 r

       glm::vec3 point; // 定义一个 3D 向量 point
       point.x = r * cos(theta)*radius; // 计算 x 坐标
       point.y = r * sin(theta)*radius; // 计算 y 坐��
       point.z = z * radius; // 计算 z 坐标
       point += center; // 将点平移到球心位置

       points.emplace_back(point); // 将生成的点添加到 points 向量中
    }
    return points; // 返回生成的点的向量
}
```

上面的代码是生成计算切平面位置的一种方法。

然后定义一个容量为k的Cluster的数组。每个簇对应一个切平面。计算三角形和簇的距离，将每个三角形都分配到与其距离最近的簇。

接下来更新每个簇(根据簇中所有三角形的顶点利用上面提到过的 svd 的方法计算最佳拟合平面，以及计算簇的质心)。

### 第二步 簇覆盖方差优化

这一步的目的是重新分配三角形以减少簇间的覆盖方差。

首先需要一个三角形的数组的数组来存储三角形的分配方法，容量和簇的数量一致。

计算三角形的重心和簇的质心的距离，像上一步一样按最近距离重新分配三角形所属的簇。

最后再次像上一步一样更新每个簇。

### 第三步 移除覆盖最少的簇

这一步是迭代的算法。循环次数取决于输入的最大迭代次数。

每一次迭代中，首先找到包含三角形最少的簇，删除这个簇，簇中的三角形计算与其他簇的距离，各自分配到距离最近的簇。然后更新这些簇。这之后找到包含三角形最多簇，找到其中离簇的质心距离最远的三角形，用这个三角形创建新的簇。然后再次更新簇。直到满足迭代次数。

看着很奇怪。但是原论文中也是这样的方法(原论文对簇的大小并没有定义，感觉可以是投影前的覆盖面积，投影后的覆盖面积或者这里用的三角形数量)。可能更适合用来优化空簇？感觉创建新簇后先执行一些简单的三角形重新分配会更好再进入下次循环会更好。。。

原论文中的终止条件是簇半径的方差达到局部最优。簇半径是簇中里质心最远的顶点到簇的质心的距离。

### 第四步 主簇优化

进一步优化簇的分配。

```cpp
if (trianglesTmp.size() > 20000&&minibatch==true) {
    main_step_batch(trianglesTmp, clusters, batch_iter);
}
else {
    main_step_full(trianglesTmp, clusters, maxIter);
}
```

根据不同条件分成两种方法。

+ <b>main_step_full</b>：同样是一个循环迭代的算法，在每次循环的开始，清空所有簇中的三角形集合。然后将所有三角形重新分配，分配的依据是三角形重心到簇的拟合平面的距离与三角形重心到簇的质心的距离按一定权值相加。分配完成后，像之前每一步一样更新簇，让每个簇有新的质心和拟合平面。然后计算所有三角形的重心到所属簇的质心的距离之和，称为总误差。总误差对比上次循环更小并且没有到达设定的最大迭代次数，那就继续循环，其他情况就停止循环。
+ <b>main_step_batch</b>：和 main_step_full 大体上类似，主要是三角形多了之后，每次全部重新分配开销过大，所以每次随机选取一部分三角形来计算。首先在循环开始依然是清空所有簇中的三角形集合。然后随机抽取输入数量的三角形，将这些三角形重新分配，分配方法和上一段的相同。这之后更新簇，让每个簇有新的质心和拟合平面。不过可能由于是随机抽取的三角形，所以停止条件只有达到设定的循环次数。循环结束后，将所有三角形分配到簇中。

### 缝隙优化

在原论文中，完成前三部后并没有最后这一步，而是缝隙优化。

因为前三步完成后的 BBC 很容易出现裂缝。文章中猜测可能有三个原因：

1. <b>纹理映射问题</b>：相邻三角形在平面上的投影可能由于抗锯齿问题（anti-aliasing）或数值误差而出现间隙。
2. <b>平面拟合问题</b>：当一个平面只基于一个三角形或几个三角形拟合时，这些三角形的信息可能无法被完整地投影到该平面上，尤其是在三角形的法向量与平面正交时。
3. <b>平面边界问题</b>：每个三角形只能投影到一个平面，因此广告牌之间可能出现边界不连续的情况（如图 3 中虚线椭圆标出的裂缝区域）。

原文给出的解决方式是：

1. <b>确定每个簇的最小包围盒</b>，包含簇中所有的三角形，用于计算平面所表示的空间的范围。
2. <b>检测相交包围盒</b>：确定所有的相交包围盒对，如果两个包围盒彼此相交（即至少有一个顶点位于另一个包围盒内），则认为这些平面可能存在潜在裂缝。
3. <b>投影</b>：找到交集区域内的三角形，这些三角形不止投影到原来的平面，也投影到相交的另一个包围盒表示的那个平面。另外如果一个三角形只有一部分在交集内，那么只将交集部分投影到另一个平面上，剩余部分只投影到原来的平面上(原文提到利用模板缓冲实现)。

# 效果对比

![comparison](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Impostor/comparison.png)

最后贴一下这个项目里三个算法运行后的对比吧。