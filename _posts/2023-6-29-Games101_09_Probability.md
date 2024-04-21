---
layout:       post
title:        "Games101笔记09——Probability"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - Games101
    - 图形学
---



# 随机变量

![image-20230627215728140](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/09/image-20230627215728140.png)

随机变量表示潜在值的分布。

概率密度函数(PDF)描述一个随机过程选择值的相对概率。就是随机到某个值的概率。比如投六面骰子，那么六个值的PDF的值都是1/6 。

# 概率

![image-20230627220118262](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/09/image-20230627220118262.png)

# 期望

![image-20230627220204189](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/09/image-20230627220204189.png)

期望是所有可能的值的加权平均，权值是随机到这个值的概率。

# 连续的情况

![image-20230627220619151](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/09/image-20230627220619151.png)

连续的情况PDF(概率密度函数)就变成了PDF(概率分布函数)。令人感叹。

## 求函数的期望

![image-20230627220859966](https://raw.githubusercontent.com/achmli/achmli.github.io/master/img/Games101/09/image-20230627220859966.png)

把原来的变量x替换成函数f(x)即可。