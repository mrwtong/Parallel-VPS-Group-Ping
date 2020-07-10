# A Parallel VPS Group Ping Program

## **该程序支持的主要功能：**  
+ 并发的对多个服务器进行Ping
+ 能够以小间隔向同一地址进行多次Ping，并且统计最小、平均、最高延迟和丢包率
+ 命令行格式化列表输出
+ 常见VPS服务器链接订阅的解析和显示
+ 针对长时间没有相应的服务器支持直接Ctrl+C中断Ping子进程，并返回结果
---
## **使用方法**：  
**1. 从订阅连接导入：** 将订阅地址分行添加到urllist.txt文件中（注释行使用//开头）  
**2. 按服务器信息导入：** 将服务器订阅信息按照固定的格式添加到serverlist.txt文件中（格式实例再文件中,注释行使用//开头）    

---
##  **特征**：
借用子线程对Ping进程的进度及延迟数据进行异步IO，结构如下：  
![结构](https://github.com/mrwtong/Parallel-VPS-Group-Ping/blob/master/img/Diagram.jpg?raw=true)
每一个Ping子进程的内存占用约为1M  
输出格式：  
![输出](https://github.com/mrwtong/Parallel-VPS-Group-Ping/blob/master/img/case.jpg?raw=true)
相关工具链接 [psping64](https://docs.microsoft.com/en-us/sysinternals/downloads/psping)
