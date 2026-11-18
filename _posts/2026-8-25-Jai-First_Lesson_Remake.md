---
layout:       post
title:        "Jai学习第一课重制版——声明与类型"
author:       "deepseek_v4_pro"
header-style: text
catalog:      true
tags:
    - Jai
series: "Jai 学习"
series_order: 1
topic: "Jai 编程"
---

> 重制版，之前写到第二课感觉ai设计的课程不太合理，所以让gpt重新设计了一版
> 
> 但是写笔记比写代码痛苦多了，尤其是这种初学用的代码，所以差不多的内容不想再写一遍了
> 
> 所以除了开头这一段，所有的内容都是ai大人的作品
> 
> 我没有看内容，所以希望你们不喜欢

## 本课学习目标

+ 理解 `:`、`:=`、`::` 的区别；
+ 理解显式类型、类型推导和编译期常量；
+ 熟悉 Jai 的整数和浮点类型；
+ 理解字面量的默认类型；
+ 使用 `type_of` 检查表达式类型；
+ 理解 Jai 为什么尽量统一声明语法。

---

## 先修知识

本来想写“这节课没有吧，毕竟是第一节课捏”，但 ai 大人说这一栏不能空着。

这是第一课，所以确实没有 Jai 层面的前置知识。默认你已经会写一点 C/C++：知道什么是变量、类型、整数、浮点数和除法，也知道“编译”这件事大概在干嘛，就够了。Jai 自己的写法从这一课开始从零讲。

唯一要提前记在心里的一条是：Jai 是强静态类型语言，类型在编译期就确定下来，数值之间的转换基本都要显式写。后面那些“为什么不能隐式缩窄”的失败样例，根源都在这句话里。

---

## 最小实验

只使用标量，不使用数组、循环、随机数或 polymorphism。

实验内容：

```jai
explicit: s32 = 10;
inferred := 10;

EXPLICIT_CONSTANT: s32 : 10;
INFERRED_CONSTANT :: 10;

print("% %\n", type_of(explicit), type_of(inferred));
```

再验证：

```jai
runtime_value := 10;
// narrowed_runtime: s8 = runtime_value; // 取消注释会因位宽不足编译失败

COMPILE_TIME_VALUE :: 10;
narrow: u8 = COMPILE_TIME_VALUE; // 应通过
```

---

## 聚焦作业

输入：

```text
图像宽高
像素坐标 x、y
曝光档数（比如 +1 档）
```

输出：

```text
归一化并应用曝光后的 RGB
转换后的 u8 RGB
用 `type_of` 检查的表达式类型
```

要求：

- 宽高使用编译期常量；
- x、y 使用显式整数类型；
- 中间值至少一处使用类型推导；
- 归一化时先显式转换成浮点数，再做除法；
- 使用 `type_of` 输出至少四种表达式类型。

### 必须使用

```text
:
:=
::
=
cast
type_of
s32 或 s64
float32
float64
u8
```

### 禁止使用

```text
数组
循环
动态数组
Random
$T
文件 IO
String_Builder
```

### 必须证明

- `:=` 得到运行时变量；
- `::` 右侧必须在编译期成立；
- 普通运行时 `s64` 不会自动缩窄为 `s8`；
- 可表示的编译期整数常量可以用于 `u8`；
- 整数除法与浮点除法结果不同。

### 非本课目标

- 常量最终位于指令、只读段还是没有独立存储；
- 数组和 slice；
- allocator；
- 完整编译期执行。

### 完成条件

- 正式作业完全不依赖后续课程；
- 所有转换都写明意图；
- README 能用自己的语言解释五种声明形式。

---

## 目标——代码证据

把学习目标逐条对到代码上，省得写完才发现某个目标其实没有证据。

### 1. `:`、`:=`、`::` 的区别

在 `experiment.jai` 里把几种声明形式一次写全：

```jai
explicit: s32 = 10;          // `:` + `=`：显式类型，运行时变量
inferred := 10;              // `:=`：类型推导，运行时变量

EXPLICIT_CONSTANT: s32 : 10; // `:` + `:`：显式类型，编译期常量
INFERRED_CONSTANT :: 10;     // `::`：类型推导，编译期常量
```

运行输出是：

```text
the value of explicit is 10, and its type is s32
the value of inferred is 10, and its type is s64
the value of EXPLICIT_CONSTANT is 10, and its type is s32
the value of INFERRED_CONSTANT is 10, and its type is s64
```

差异很直白：`explicit` 和 `inferred` 是运行时变量，`EXPLICIT_CONSTANT` 和 `INFERRED_CONSTANT` 是编译期常量；而 `s32` / `s64` 的差别说明 `:` 后面的类型名是显式写的，`:=` / `::` 则完全靠右侧推导。

### 2. 显式类型、类型推导和编译期常量

上面四条声明正好覆盖三件事：

- 显式类型：`explicit: s32`、`EXPLICIT_CONSTANT: s32`，类型名写在 `:` 后面；
- 类型推导：`inferred := 10`、`INFERRED_CONSTANT :: 10`，不写类型名，由 `10` 推导成 `s64`；
- 编译期常量：`EXPLICIT_CONSTANT: s32 : 10`、`INFERRED_CONSTANT :: 10`，右侧必须在编译期可求值。

`experiment2` 进一步证明“变量”和“常量”不是一回事：

```jai
runtime_value := 10;      // 运行时变量
COMPILE_TIME_VALUE :: 10; // 编译期常量

narrow: u8 = COMPILE_TIME_VALUE; // 通过：常量 10 能塞进 u8
```

### 3. Jai 的整数和浮点类型

文末的作业示例里整数和浮点都摸了一遍。

- `int`（即 `s64`）：`calc_pixel_color` 的 `x`、`y`、`exposure` 参数；
- `float`（即 `float32`）：`EV`、`r_float`、`g_float`、`b_float`；
- `float64`：`cast(float64) exposure`；
- `u8`：最终颜色分量 `r_u8`、`g_u8`、`b_u8`。

### 4. 字面量的默认类型

`INFERRED_CONSTANT :: 10` 打印出来是 `s64`，所以整数数字默认是 `s64`。浮点字面量（比如 `2.0`）默认是 `float32`，这条在“完成结论”里再展开。本课靠 `experiment.jai` 的输出就能拿到整数默认类型的直接证据。

### 5. `type_of` 检查表达式类型

实验和作业都用 `type_of` 看实际的类型。作业里一共检查了六个表达式。

```jai
print("type of width: %\n", type_of(WIDTH));               // s64
print("type of coordinate: %\n", type_of(x));              // int，打印为 s64
print("type of exposure scale: %\n", type_of(EV));         // float，打印为 float32
print("type of exponent: %\n", type_of(cast(float64) exposure)); // float64
print("type of color: % %\n", type_of(r_float), type_of(r_u8)); // float32, u8
```

文末的示例调用 `calc_pixel_color(114, 514, 1)`，会打印下面这几行。

```text
color in float: 0.222656 1.003906 0.613281
color in u8: 57 255 156
type of width: s64
type of coordinate: s64
type of exposure scale: float32
type of exponent: float64
type of color: float32 u8
```

两个值得记的观察：

+ `type_of` 打印的是规范类型名：声明里写 `int` 打印 `s64`，写 `float` 打印 `float32`。因为 `int` / `float` 只是 `s64` / `float32` 的别名，`type_of` 拿到的是别名指向的那个类型本身。
+ 中间绿色分量 `g_float` 是 `1.003906`，已经超过 `1.0`，`cast_float_to_u8` 里的 `clamp` 把它压回 `1.0`，所以 `g_u8` 是 `255`。这也是为什么要先 clamp 再 `cast(u8)`。

### 6. 统一声明语法

这一条没有单独的实验，而是体现在上面所有声明长得一样：常量、变量、过程都用“名字在前、声明信息在后”的形式：

```jai
WIDTH :: 1024;                                    // 常量
cast_float_to_u8 :: (value: float) -> u8 { ... }  // 过程
calc_pixel_color :: (x: int, y: int, exposure: int) { ... }
```

`::` 把名字绑定到编译期已知的东西——不只是数值，还有过程本身。这大概就是为什么声明过程也用 `::`，而不是单独发明一个 `func` 关键字。

---

## 主动制造的失败

按 v3 的要求，失败的例子要单独记下来，不能混进正式程序里。

### 失败一：运行时的 s64 不能隐式缩窄成 s8

单独拿下面两行来试。

```jai
runtime_value := 10;
// narrowed_runtime: s8 = runtime_value; // 取消注释会编译失败
```

`runtime_value` 是 `s64`，两边都是有符号整数。编译器报的是 64 位往 8 位里塞会丢信息。要主动做这个转换，可以写 `cast(s8)`。

### 失败二：`::` 的右侧必须在编译期成立

这条来自 001 笔记里的教训（当时直接写进了正式代码）：

```jai
max :: cast(s32) random_get_within_range(10.0, 100.0); // 编译失败
```

`::` 声明的是编译期常量，右侧必须能在编译期算出来。而 `random_get_within_range` 是运行时随机过程，编译期根本不知道结果，所以直接报错；改成 `:=`（运行时变量）就对了。

### 失败三（顺手记一下）：失败要失败在你想失败的那件事上

我最早把那一行写成了 `narraw: u8 = runtime_value`。变量名只是拼漏了一个字母，编译器实际先报的是两边的符号性不同。上面改用 `s8`，就能单独看位宽检查。制造失败时，先确认失败的是目标行为本身。

---

## 本课涉及的生命周期

基本没有。

这一课只用了标量（整数、浮点、u8），全部按值存局部变量、按值传参，没有指针、没有 slice、没有动态数组、没有 allocator，所以不存在“借用”“所有权”或“释放”的问题。

编译期常量（`WIDTH :: 1024` 这类）最终落在指令里、只读段里还是没有独立存储，属于“非本课目标”，这里不展开，等学到内存和编译期执行再说。

---

## 值得记录的跨语言差异（可选）

只挑和本课直接相关的几条，不为了凑数硬写：

+ 类型推导：C++ 从 C++11 才有 `auto`，还附带一堆“什么时候该用 auto”的争论；Jai 从一开始就把 `:=` / `::` 当成默认写法，没有额外关键字。
+ 声明顺序：Jai 是“名字在前、类型在后”（`a: s64 = 10`），C++ 是“类型在前”（`int64_t a = 10;`）。单看这一条只是语法位置不同，但配合“统一声明”再看，Jai 是想让变量、常量、过程、类型共用同一套“名字 + 声明信息”的形状。
+ 位宽默认值：`int` 在 Jai 是 `s64`，在 C++ 通常是 32 位且长度随平台飘；`float` 两边都是 32 位。所以 Jai 是“整数往宽了默认、浮点往窄了默认”，挺游戏向的。
+ 浮点后缀：Jai 的浮点字面量不用加 `f`，`3.14` 默认就是 `float32`；C++ 里 `3.14` 是 double，想要 float 得写 `3.14f`。
+ 常量语义：Jai 的 `::` 更接近 C++ 的 `constexpr`（强调“编译期已知”），而不是主要表达“只读”的 `const`。
+ 打印：Jai 的 `print("%", x)` 所有类型共用 `%`；C 的 `printf` 要背 `%d/%u/%f/...`，背错就是未定义行为。

---

## 提前借用但暂不展开的内容

作业能跑起来，其实已经提前用了几样后面的东西：

- `#import` 用来引入 `Basic` 和 `Math` 两个模块，细节留到第 25 课（module）。之前用来把实验和作业拼起来的 `#load` 会在第 11 课（scope 与多文件组织）再讲。
- 过程：`cast_float_to_u8`、`calc_pixel_color` 都是过程，而过程的完整语义（参数、返回值、多返回值）要第 3 课才讲。这里只用到“声明、调用、返回一个值”这种最小子集。
- `clamp` 来自 `Basic`，`floor` 和 `pow` 来自 `Math`。这几个都是别人写好的过程，这里直接调用。
- `print` 的 `%` 格式化：真正讲格式化输出是第 8 课，这里只用到最基础的打印。

这些属于“为了把本课知识用起来而借的工具”，不算违反“不依赖后续课程”，因为作业真正要证明的知识点（五种声明、类型推导、字面量默认类型、显式转换）都在本课范围内。

---

## 完成结论

### `:`、`:=`、`::` 的区别

说到底是五种声明形式，全都能用“名字在前、类型/值在后”这一条串起来：

1. `a: s64` —— 显式类型的运行时变量（不写初值就是零值）；
2. `a: s64 = 10` —— 显式类型的运行时变量，顺带初始化；
3. `a: s64 : 10` —— 显式类型的编译期常量；
4. `a := 10` —— 省略类型名，运行时变量，类型由右侧推导（`10` → `s64`）；
5. `a :: 10` —— 省略类型名，编译期常量，类型同样由右侧推导。

记忆口诀大概就是：`:` 负责“这是声明”，`=` 负责“运行时初始化/赋值”，第二个 `:` 负责“编译期常量”，而 `:=` / `::` 只是把类型名省掉之后的简写。所以 `:=` 是“运行时变量 + 推导”，`::` 是“编译期常量 + 推导”。

### 显式类型、类型推导和编译期常量

- 显式类型：声明时把类型名写在 `:` 后面，编译器不猜；
- 类型推导：不写类型名，编译器根据右侧值/表达式的类型来决定；
- 编译期常量：用 `::`（或 `: T :`）绑定，右侧必须编译期可求值，之后就能当作字面量一样参与窄化（见 `narrow: u8 = COMPILE_TIME_VALUE`）。

### Jai 的整数和浮点类型

整数是 `s8/u8/s16/u16/s32/u32/s64/u64`，浮点是 `float32/float64`。两个常用别名：`int` 是 `s64`，`float` 是 `float32`。

### 字面量的默认类型

- 整数数字默认 `s64`（`INFERRED_CONSTANT :: 10` 打印为 `s64`）；
- 浮点数字默认 `float32`，精度明显超过 `float32` 时编译器会退到 `float64`（这条记自 001 笔记）；
- 给一个声明了具体类型的变量赋字面量时，字面量会“适配”目标类型（只要值能表示）。这也是为什么 `narrow: u8 = COMPILE_TIME_VALUE` 能通过——编译器知道 `10` 这个编译期常量放进 `u8` 不会溢出。

### `type_of` 检查表达式类型

`type_of` 返回的不是字符串，而是类型本身（一个 `Type` 值），可以直接用 `%` 打印，也能比较和传递。本课里全靠它把“推导出了什么类型”变成看得见的输出，而不是脑补。

### 为什么尽量统一声明语法

说实话还是没完全想通“统一”这个说法，但至少能观察到：变量、常量、过程、类型都用“名字在前、声明信息在后”，而且 `::` 一个符号就承担了“绑定到编译期已知的东西”这一件事——无论是数值还是过程。所以不是“每种东西都发明一套关键字”，而是“一种形式 + 少量符号”覆盖掉大部分声明。先记下这个观察，后面学 module 和类型时再回来看。

### 运行方式

想复现上面那组结果，把下面的作业示例存成 `assignment.jai`，用 `jai assignment.jai` 编译后运行生成的程序就行。

比如直接算 `114 / 1024` 会得到整数 `0`。示例把坐标和宽高转成浮点数再相除，然后用 `2` 的曝光档数次方乘上结果。

```jai
#import "Basic";
#import "Math";

WIDTH :: 1024;
HEIGHT :: 1024;

cast_float_to_u8 :: (value: float) -> u8 {
    scaled := clamp(value, 0.0, 1.0) * 255.0;
    return cast(u8) floor(scaled + 0.5);
}

calc_pixel_color :: (x: int, y: int, exposure: int) {
    EV: float = cast(float) pow(cast(float64) 2.0, cast(float64) exposure);
    r_float := (cast(float) x / cast(float) WIDTH) * EV;
    g_float := (cast(float) y / cast(float) HEIGHT) * EV;
    b_float := (r_float + g_float) / 2.0;

    r_u8 := cast_float_to_u8(r_float);
    g_u8 := cast_float_to_u8(g_float);
    b_u8 := cast_float_to_u8(b_float);

    print("color in float: % % %\n", r_float, g_float, b_float);
    print("color in u8: % % %\n", r_u8, g_u8, b_u8);
    print("type of width: %\n", type_of(WIDTH));
    print("type of coordinate: %\n", type_of(x));
    print("type of exposure scale: %\n", type_of(EV));
    print("type of exponent: %\n", type_of(cast(float64) exposure));
    print("type of color: % %\n", type_of(r_float), type_of(r_u8));
}

main :: () {
    x: int = 114;
    y: int = 514;
    calc_pixel_color(x, y, 1);
}
```
