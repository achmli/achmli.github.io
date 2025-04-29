---
layout:       post
title:        "应该是古早的某种被称为Billbaord Clouds的LOD技术-Part4-纹理生成"
author:       "Fon"
header-style: text
catalog:      true
tags:
    - LOD生成
    - 图形学
    - Impostor
---

在完成了几何上的简化后，也需要生成简化后的模型能使用的纹理。

大体上是三个步骤：

1. 生成 UV 映射。
2. 将贴图渲染到纹理。
3. 从帧缓冲区读取像素生成最终纹理图像。

依然是读代码而不是其他的学习方法。

# 生成 UV 映射

```cpp
for (int i = 0; i < bbc.size(); i++)
{
	v.push_back(bbcRectangle[i].p0.x);
	v.push_back(bbcRectangle[i].p0.y);
	v.push_back(bbcRectangle[i].p0.z);
	...         
	v.push_back(bbcRectangle[i].p3.z);
}
for (int i = 0; i < bbc.size(); i++)
{
	faceVcount.push_back(4);					// number of vertex
}
for (int i = 0; i < bbc.size(); i++)
{
	index_t idx0, idx1, idx2, idx3, idx4, idx5;
	idx0.vertex_index = i * 4;					// first triangle
	idx1.vertex_index = i * 4 + 1;
	idx2.vertex_index = i * 4 + 2;
	idx3.vertex_index = i * 4;					// second triangle
	idx4.vertex_index = i * 4 + 2;
	idx5.vertex_index = i * 4 + 3;

	indices.push_back(idx0);
	...
	indices.push_back(idx5);
}
```

首先要构造顶点列表，并不是原来的三角形的顶点，而是组成投影后平面的矩形的顶点。实际上就是组织VBO和VAO之类的格式，依次构造每个矩形的顶点位置、索引和 tex_coord ，就是 传到 GPU 里的数据。也是 obj 文件里的内容。

```
xatlas::Atlas* atlas = xatlas::Create();

// Add meshes to atlas.
uint32_t totalVertices = 0, totalFaces = 0;
xatlas::MeshDecl meshDecl;
meshDecl.vertexCount = (uint32_t)v.size() / 3;
meshDecl.vertexPositionData = v.data();
meshDecl.vertexPositionStride = sizeof(float) * 3;
meshDecl.indexCount = (uint32_t)indices.size();
Eigen::Matrix<uint32_t, -1, -1, Eigen::RowMajor> Frowmajor(indices.size() / 3, 3);
for (int r = 0; r < indices.size() / 3; r++)										// typedef struct {
{																					//     int vertex_index;
	Frowmajor(r, 0) = indices[3 * r].vertex_index;									//     int normal_index;
	Frowmajor(r, 1) = indices[3 * r + 1].vertex_index;								//     int texcoord_index;
	Frowmajor(r, 2) = indices[3 * r + 2].vertex_index;								// } index_t
}
meshDecl.indexData = Frowmajor.data();
meshDecl.indexFormat = xatlas::IndexFormat::UInt32;
meshDecl.faceVertexCount = (uint8_t*)faceVcount.data();
meshDecl.faceCount = (uint32_t)bbcRectangle.size();
```

在这部分用到了 `xatlas` 这个库，上面的部分不只是生成新的 obj 文件必需，同时也是我们使用 xatlas 库需要的。

```cpp
int shape = 1;
xatlas::AddMeshError error = xatlas::AddMesh(atlas, meshDecl, (uint32_t)shape);
if (error != xatlas::AddMeshError::Success) {
    xatlas::Destroy(atlas);
    printf("\rError adding mesh\n");
}
```

之后调用 `xatlas::AddMesh` 将构造的 `meshDecl` 添加到 `xatlas::Atlas` 中。

```
xatlas::ChartOptions co;
co.maxIterations = 10;
xatlas::PackOptions pack;
pack.resolution = IMG_WIDTH-1;

xatlas::Generate(atlas,co,pack);
```

然后就可以生成 UV 了。上面的两个设置分别是用于优化图块布局的最大迭代次数和生成的 UV 贴图的分辨率。

```cpp
for (int i = 0; i < bbc.size(); i++) {
    bbcRectangle[i].t0.x = mesh.vertexArray[4 * i].uv[0] / atlas->width;
    bbcRectangle[i].t0.y = mesh.vertexArray[4 * i].uv[1] / atlas->height;
    bbcRectangle[i].t1.x = mesh.vertexArray[4 * i + 1].uv[0] / atlas->width;
    bbcRectangle[i].t1.y = mesh.vertexArray[4 * i + 1].uv[1] / atlas->height;
    bbcRectangle[i].t2.x = mesh.vertexArray[4 * i + 2].uv[0] / atlas->width;
    bbcRectangle[i].t2.y = mesh.vertexArray[4 * i + 2].uv[1] / atlas->height;
    bbcRectangle[i].t3.x = mesh.vertexArray[4 * i + 3].uv[0] / atlas->width;
    bbcRectangle[i].t3.y = mesh.vertexArray[4 * i + 3].uv[1] / atlas->height;
}
xatlas::Destroy(atlas);
```

提取 UV 数据，然后将 UV 坐标归一化到0到1的范围内。

最后释放`xatlas::Atlas`。

# 将贴图渲染到纹理

```cpp
float heightResolution = max(abs(bbcRectangle[i].t2.x - bbcRectangle[i].t1.x), abs(bbcRectangle[i].t2.y - bbcRectangle[i].t1.y)) * (IMG_HEIGHT-1);
float widthResolution =max(abs(bbcRectangle[i].t0.x - bbcRectangle[i].t1.x), abs(bbcRectangle[i].t0.y - bbcRectangle[i].t1.y)) * (IMG_WIDTH-1);
bbsWidthResolution.emplace_back(widthResolution);
bbsHeightResolution.emplace_back(heightResolution);
```

首先要计算每个矩形的宽高，计算对应的纹理的分辨率。计算的分辨率乘以全局分辨率比例，确保单位像素的物理尺寸相等。

```cpp
Billboard tmp(bbcRectangle[i], glfw);
bbs.emplace_back(tmp);

for (auto& indiceIndex : bbcMeshIndicesIndex[i])
{
    float indice = mesh->m_indices[indiceIndex];
    verticesTmp.emplace_back(mesh->vertices[indice]);
}
Mesh meshTmp(verticesTmp, mesh->textures);
bbMeshes.emplace_back(meshTmp);
```

`bbcMeshIndicesIndex` 是之前用来保存投影前的三角形的顶点的。是每个平面包含的三角形的顶点的索引的数组，一个存储的单元对应一个平面。

`mesh` 是就是原模型，所以这一步是读取原模型中每个平面的包含三角形的顶点 。然后使用顶点和纹理信息，生成与 BBC 对应的几何网格。

```cpp
bbs[i].setTextureFromFrameBuffer(bbsWidthResolution[i], bbsHeightResolution[i]);
glBindFramebuffer(GL_FRAMEBUFFER, bbs[i].frameBuffer);
glViewport(0, 0, bbsWidthResolution[i], bbsHeightResolution[i]);
```

动态设置帧缓冲的分辨率，与计算的宽高分辨率一致。将当前帧缓冲绑定到 BBC 的帧缓冲对象。

```cpp
float rectangle_x_length = bbcRectangle[i].axisXLength;
float rectangle_y_length = bbcRectangle[i].axisYLength;
glm::vec3 camPosition = glm::vec3(0, 0, 100);
glm::mat4 bbTexGenProjection = glm::ortho(-rectangle_x_length / 2, rectangle_x_length / 2, -rectangle_y_length / 2, rectangle_y_length / 2, 0.1f, 1000.0f);
glm::mat4 bbTexGenView = glm::lookAt(camPosition, glm::vec3(0, 0, 0), glm::vec3(0, 1, 0));
glm::mat4 bbTexGenModel = bbcRectangle[i].getTransMat(bbc[i].normal);
glm::vec3 lightPos = glm::vec3(10, 15, 10);
textureGenShader.use();
textureGenShader.setMat4("projection", bbTexGenProjection);
textureGenShader.setMat4("view", bbTexGenView);
textureGenShader.setMat4("model", bbTexGenModel);
textureGenShader.setVec3("lightPos", lightPos);
textureGenShader.setVec3("viewPos", camPosition);
textureGenShader.setBool("blinn", false);
textureGenShader.setBool("alphaTest", true);
bbMeshes[i].render(textureGenShader);
```

在接下来就是利用上一步的纹理和顶点信息将每个平面的三角形渲染到各自的 framebuffer 中。

# 读取像素生成最终纹理

```cpp
if (!saveComplete)
{
    for (auto& d : textureAtlas)
    {
       if (d != nullptr)
       {
          free(d);
       }
    }
}
textureAtlas.resize(bbs.size());
```

如果上一次生成的数据尚未保存，就释放掉之前生成的已有的内容。

```cpp
glBindFramebuffer(GL_FRAMEBUFFER, bbs[i].frameBuffer);
textureAtlas[i] = (BYTE *)malloc((int)(bbsWidthResolution[i] * bbsHeightResolution[i] * 4));
if (textureAtlas[i] != nullptr)
{
    glReadPixels(0, 0, bbsWidthResolution[i], bbsHeightResolution[i], GL_RGBA, GL_UNSIGNED_BYTE, textureAtlas[i]);
}
glBindFramebuffer(GL_FRAMEBUFFER, 0);
```

这之后就是图形库的调用了。

```cpp
// Method #2: "glGetTexImage" (access violation error?)
glBindTexture(GL_TEXTURE_2D, bbs[i].texture);
textureData[i] = (BYTE *)malloc((int)(bbsWidthResolution[i] * bbsHeightResolution[i] * 4));
if (textureData[i] != nullptr)
{
  glGetTexImage(GL_TEXTURE_2D, 0, GL_RGBA, GL_FLOAT, textureData[i]);
}
glBindTexture(GL_TEXTURE_2D, 0);

// Method #3: "PixelBufferObjects" (slightly faster method than the previous two)
GLuint pbo;
glGenBuffers(1, &pbo);
glBindFramebuffer(GL_FRAMEBUFFER, bbs[i].frameBuffer);
glBindBuffer(GL_PIXEL_PACK_BUFFER, pbo);

// 异步读取帧缓冲的像素数据到 PBO
glReadPixels(0, 0, bbsWidthResolution[i], bbsHeightResolution[i], GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
glBindBuffer(GL_PIXEL_PACK_BUFFER, pbo);

void* ptr = glMapBuffer(GL_PIXEL_PACK_BUFFER, GL_READ_ONLY);
if (ptr) {
    // 复制数据到 textureAtlas[i]
    memcpy(textureAtlas[i], ptr, bbsWidthResolution[i] * bbsHeightResolution[i] * 4);
    glUnmapBuffer(GL_PIXEL_PACK_BUFFER);
}
glBindBuffer(GL_PIXEL_PACK_BUFFER, 0);
```

另外还留了两种方法。大体上也是调用 OpenGL 的功能。