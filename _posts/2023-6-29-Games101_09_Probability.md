---
layout:       post
title:        "Games101笔记09——Probability"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
series: "Games101"
series_order: 9
topic: "图形学基础"
---



# 随机变量

![image-20230627215728140](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/09/image-20230627215728140.png)

随机变量表示潜在值的分布。

离散随机变量的概率质量函数（PMF）给出每个取值的概率。比如公平六面骰子的每个点数都以 1/6 的概率出现。

# 概率

![image-20230627220118262](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/09/image-20230627220118262.png)

# 期望

![image-20230627220204189](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/09/image-20230627220204189.png)

期望是所有可能的值的加权平均，权值是随机到这个值的概率。

# 连续的情况

![image-20230627220619151](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/09/image-20230627220619151.png)

连续随机变量在区间内的概率等于其概率密度函数（PDF）在该区间上的积分。累积分布函数（CDF）表示 $P(X\le x)$，离散随机变量也有 CDF。

## 求函数的期望

![image-20230627220859966](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/09/image-20230627220859966.png)

把原来的变量x替换成函数f(x)即可。