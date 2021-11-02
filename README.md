# gene spider 
## Method 
实验中发现，在details页面会出现需要爬取的信息处于loading的状态，网页加载太慢，没法依赖xpath获取数据，如下图。

![loading](imgs/2.png)

然后经过网页的Network的分析，可以发现用于获取数据的ajax的方法，如下图。

![ajax](imgs/1.png)

并且是get方法调用，实验后还不需要headers，这就简单了，很可。
