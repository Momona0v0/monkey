# 贴猴

一个适用于Hoshinobot的贴猴插件

## 功能特性

让机器人给你的群友全自动贴猴。

## 部署教程

1.下载或git clone本插件：

在 HoshinoBot\hoshino\modules 目录下使用以下命令拉取本项目

git clone https://github.com/Momona0v0/monkey/

2.启用：

在 HoshinoBot\hoshino\config\ bot.py 文件的 MODULES_ON 加入 'monkey'

然后重启 HoshinoBot

## 指令
仅限qq群管理员：

【开启无差别贴猴 [概率值]】：开启无差别贴猴。概率值可支持小数，百分数，缺省（默认100）

【关闭无差别贴猴】：关闭贴猴

【贴猴成员@某人】：只贴指定成员的消息

【取消贴猴成员@某人】：取消只贴指定成员

【贴猴关键词 XXX】：只贴包含关键词的消息

【取消贴猴关键词 XXX】：取消关键词过滤

【清空贴猴设置】：重置所有设置

【查看贴猴设置】：显示当前设置

通用：

【回复一条消息并发送"贴猴"】：手动给该消息贴猴

【贴猴帮助】：显示此帮助信息

## 致谢

感谢 DeepSeek AI 帮我写的代码。

感谢 HoshinoBot 项目提供的优秀机器人框架。
