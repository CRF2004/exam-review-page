# 实验5：AlexNet实战

## 一、实验名称

**AlexNet 在 CIFAR-10 上的图像分类实验：隐藏层宽度对模型性能的影响**

## 二、实验目的

1.  理解 AlexNet 的基本结构及其相对于 LeNet 的改进思想。
2.  掌握使用卷积神经网络完成 CIFAR-10 图像分类任务的基本流程。
3.  学会在 PyTorch 中搭建 AlexNet 网络并完成训练、验证与测试。
4.  通过调整全连接隐藏层宽度，观察模型容量变化对训练效果、过拟合现象和计算开销的影响。

## 三、实验背景与原理1\. AlexNet 的核心思想

AlexNet 是深度卷积神经网络发展的重要代表，相比 LeNet，主要有以下提升：

- 网络更深，卷积层更多；
- 通道数更多，特征提取能力更强；
- 使用 ReLU 激活函数，加快训练；
- 使用最大池化，增强局部平移不变性；
- 使用 Dropout，减轻过拟合。

在 ImageNet 上，AlexNet 的输入通常是 224×224 图像；但在本实验中，CIFAR-10 图像大小仅为 **32×32**，因此需要对 AlexNet 进行**简化与适配**，否则特征图会过快缩小。

## 2\. CIFAR-10 数据集简介

CIFAR-10 是经典的小型彩色图像分类数据集，共有 10 个类别：

- airplane
- automobile
- bird
- cat
- deer
- dog
- frog
- horse
- ship
- truck

数据特点：

- 训练集：50000 张
- 测试集：10000 张
- 图像尺寸：32×32
- 通道数：3（RGB）

## 3\. 隐藏层宽度的含义

在 AlexNet 中，卷积层后通常接若干全连接层。  
其中“隐藏层宽度”一般指**全连接层神经元个数**，例如：

- 256
- 512
- 1024
- 2048

隐藏层越宽，通常意味着：

**优点：**

- 模型表达能力更强
- 更容易拟合复杂模式

**缺点：**

- 参数量更大
- 训练更慢
- 更容易过拟合

本实验要重点观察：  
**隐藏层宽度变化，会如何影响训练损失、测试精度和过拟合程度。**

# 四、实验内容

本实验分为两个部分：

## 任务1：在 CIFAR-10 上实现并训练简化版 AlexNet

要求：

- 完成数据加载与预处理
- 搭建适用于 CIFAR-10 的 AlexNet
- 训练模型并记录训练损失、训练精度、测试精度

## 任务2：调整隐藏层宽度并比较结果

建议设置 3 组实验：

- 方案A：隐藏层宽度 = 256
- 方案B：隐藏层宽度 = 512
- 方案C：隐藏层宽度 = 1024

比较内容包括：

- 训练速度
- 最终训练精度
- 最终测试精度
- 是否出现明显过拟合

# 五、实验步骤

## 步骤1：加载 CIFAR-10 数据集

### 数据预处理建议

由于 AlexNet 对输入尺寸通常较大，可采用两种方式：

### 方式A：直接使用 32×32

优点：简单、计算量小  
缺点：和原始 AlexNet 差别较大

### 方式B：将 CIFAR-10 放大到 224×224

优点：更接近 AlexNet 原始设计  
缺点：训练慢

对于教学实验，建议先采用 **32×32 版本**，更适合课堂实践。

batch_size = 128  
<br/>transform = transforms.Compose(\[  
transforms.ToTensor()  
\])  
<br/>train_dataset = datasets.CIFAR10(root='./data', train=True, download=True, transform=transform)  
test_dataset = datasets.CIFAR10(root='./data', train=False, download=True, transform=transform)  
<br/>train_iter = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)  
test_iter = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=2)

## 步骤3：构建适配 CIFAR-10 的 AlexNet

由于 CIFAR-10 图像较小，需要适当减小卷积核和步幅。

class AlexNetCIFAR(nn.Module):  
def \__init_\_(self, hidden_units=512, num_classes=10):  
super().\__init_\_()  
self.features = nn.Sequential(  
nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1), # 32x32  
nn.ReLU(),  
nn.MaxPool2d(kernel_size=2, stride=2), # 16x16  
<br/>nn.Conv2d(64, 192, kernel_size=3, padding=1),  
nn.ReLU(),  
nn.MaxPool2d(kernel_size=2, stride=2), # 8x8  
<br/>nn.Conv2d(192, 384, kernel_size=3, padding=1),  
nn.ReLU(),  
<br/>nn.Conv2d(384, 256, kernel_size=3, padding=1),  
nn.ReLU(),  
<br/>nn.Conv2d(256, 256, kernel_size=3, padding=1),  
nn.ReLU(),  
nn.MaxPool2d(kernel_size=2, stride=2) # 4x4  
)  
<br/>self.classifier = nn.Sequential(  
nn.Flatten(),  
nn.Linear(256 \* 4 \* 4, hidden_units),  
nn.ReLU(),  
nn.Dropout(0.5),  
<br/>nn.Linear(hidden_units, hidden_units),  
nn.ReLU(),  
nn.Dropout(0.5),  
<br/>nn.Linear(hidden_units, num_classes)  
)  
<br/>def forward(self, x):  
x = self.features(x)  
x = self.classifier(x)  
return x

## 步骤4：定义训练函数

def evaluate_accuracy(net, data_iter, device):  
net.eval()  
correct, total = 0, 0  
with torch.no_grad():  
for X, y in data_iter:  
X, y = X.to(device), y.to(device)  
pred = net(X).argmax(dim=1)  
correct += (pred == y).sum().item()  
total += y.numel()  
return correct / total  
def train(net, train_iter, test_iter, num_epochs, lr, device):  
net.to(device)  
optimizer = torch.optim.SGD(net.parameters(), lr=lr, momentum=0.9)  
loss = nn.CrossEntropyLoss()  
<br/>train_loss_list = \[\]  
train_acc_list = \[\]  
test_acc_list = \[\]  
<br/>for epoch in range(num_epochs):  
net.train()  
metric_loss = 0.0  
metric_correct = 0  
metric_total = 0  
<br/>for X, y in train_iter:  
X, y = X.to(device), y.to(device)  
<br/>optimizer.zero_grad()  
y_hat = net(X)  
l = loss(y_hat, y)  
l.backward()  
optimizer.step()  
<br/>metric_loss += l.item() \* X.shape\[0\]  
metric_correct += (y_hat.argmax(dim=1) == y).sum().item()  
metric_total += y.numel()  
<br/>train_loss = metric_loss / metric_total  
train_acc = metric_correct / metric_total  
test_acc = evaluate_accuracy(net, test_iter, device)  
<br/>train_loss_list.append(train_loss)  
train_acc_list.append(train_acc)  
test_acc_list.append(test_acc)  
<br/>print(f'epoch {epoch+1}, loss {train_loss:.4f}, train acc {train_acc:.4f}, test acc {test_acc:.4f}')  
<br/>return train_loss_list, train_acc_list, test_acc_list

## 步骤5：训练基线模型

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')  
<br/>net = AlexNetCIFAR(hidden_units=512)  
train_loss, train_acc, test_acc = train(net, train_iter, test_iter, num_epochs=10, lr=0.01, device=device)

## 步骤6：绘制曲线

plt.plot(train_loss, label='train loss')  
plt.plot(train_acc, label='train acc')  
plt.plot(test_acc, label='test acc')  
plt.legend()  
plt.show()

## 步骤7：调整隐藏层宽度进行对比实验

分别设置：

hidden_list = \[256, 512, 1024\]  
results = {}  
<br/>for h in hidden_list:  
print(f'\\nTraining hidden_units={h}')  
net = AlexNetCIFAR(hidden_units=h)  
train_loss, train_acc, test_acc = train(net, train_iter, test_iter, num_epochs=10, lr=0.01, device=device)  
results\[h\] = (train_loss, train_acc, test_acc)

# 七、实验记录表

## 表1 模型训练结果记录表

| 实验编号 |
| --- |
| A   |
| B   |
| C   |

# 八、结果分析要求

## 1\. AlexNet 在 CIFAR-10 上是否能够正常收敛？

观察：

- loss 是否持续下降
- train acc 是否持续上升
- test acc 是否有提升

## 2\. 隐藏层宽度变大后，训练集表现是否更好？

## 3\. 隐藏层宽度变大后，测试集精度是否一定提高？

## 4\. Dropout 的作用是什么？

# 九、思考题

1.  为什么原始 AlexNet 不能直接照搬到 CIFAR-10 上？
2.  ReLU 相比 Sigmoid / Tanh 有什么优势？
3.  最大池化在卷积网络中起什么作用？
4.  为什么隐藏层宽度增加后，参数量会快速增加？
5.  如果训练精度很高但测试精度不高，说明了什么问题？
6.  如果继续增大隐藏层宽度到 2048，结果可能怎样？为什么？
7.  AlexNet 和 LeNet 相比，最关键的提升体现在哪些方面？
8.  如果把 AlexNet 换成 VGG 风格结构，可能带来什么变化？

# 十、实验拓展（选做）

## 拓展1：加入数据增强

可尝试：

transform_train = transforms.Compose(\[  
transforms.RandomHorizontalFlip(),  
transforms.RandomCrop(32, padding=4),  
transforms.ToTensor()  
\])

观察数据增强对测试精度的提升。

## 拓展2：尝试 VGG 风格网络

例如使用多个 3×3 卷积堆叠代替较大的卷积核，比较：

- AlexNet：卷积层较粗放
- VGG：结构更规整，层数更深

## 拓展3：比较不同优化器

尝试：

- SGD
- SGD + momentum
- Adam

观察收敛速度和最终精度的差别。

# 十一、实验报告要求

实验报告建议包含以下内容：

1.  实验目的
2.  实验原理
3.  网络结构说明
4.  训练参数设置
5.  不同隐藏层宽度下的实验结果表
6.  训练曲线图
7.  结果分析与结论
8.  思考题回答