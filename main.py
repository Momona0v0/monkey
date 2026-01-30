from hoshino import Service, R, priv
from hoshino.typing import CQEvent, MessageSegment
import random
import aiohttp
import asyncio
import re
import json
import os
from pathlib import Path

sv_help = '''
【管理员指令】
1. 贴猴初始化：重置当前群的所有设置，首次使用前请先执行此命令
2. 开启无差别贴猴 [概率值] ：开启无差别贴猴 (概率可选: 0-100，默认100)
3. 关闭无差别贴猴：关闭随机贴猴
4. 贴猴成员@某人：只贴指定成员的消息
5. 取消贴猴成员@某人：取消只贴指定成员
6. 贴猴关键词 XXX ：只贴包含关键词的消息
7. 取消贴猴关键词 XXX ：取消关键词过滤 
8. 查看贴猴设置：显示当前设置

注意: 所有贴猴操作都会添加0-1秒的随机延迟以防止API限制
'''.strip()

sv = Service(name='贴猴机', enable_on_default=True, visible=True, bundle="娱乐", help_=sv_help)

# 猴子表情的ID
MONKEY_EMOJI_ID = 128053

# 默认设置
DEFAULT_SETTINGS = {
    'global_enabled': False,  # 无差别贴猴开关
    'global_probability': 1.0,  # 无差别贴猴概率 (0.0-1.0)
    'target_users': [],       # 只贴这些用户
    'target_keywords': []     # 只贴包含这些关键词的消息
}

# 检查是否是管理员
def is_admin(ev: CQEvent):
    return priv.check_priv(ev, priv.ADMIN)

# 获取群设置的保存路径
def get_record_dir():
    # 获取当前文件的目录
    current_dir = Path(__file__).parent
    record_dir = current_dir / 'monkey_records'
    record_dir.mkdir(exist_ok=True)
    return record_dir

# 获取群设置文件路径
def get_group_file(group_id):
    record_dir = get_record_dir()
    return record_dir / f'{group_id}.json'

# 加载群设置
def load_group_settings(group_id):
    group_file = get_group_file(group_id)
    
    # 如果文件不存在，使用默认设置
    if not group_file.exists():
        save_group_settings(group_id, DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()
    
    try:
        with open(group_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # 确保设置包含所有必要的键
        for key in DEFAULT_SETTINGS:
            if key not in settings:
                settings[key] = DEFAULT_SETTINGS[key]
        
        return settings
    except Exception as e:
        sv.logger.error(f"加载群 {group_id} 设置失败: {e}")
        return DEFAULT_SETTINGS.copy()

# 保存群设置
def save_group_settings(group_id, settings):
    group_file = get_group_file(group_id)
    try:
        with open(group_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        sv.logger.info(f"已保存群 {group_id} 的贴猴设置")
    except Exception as e:
        sv.logger.error(f"保存群 {group_id} 设置失败: {e}")

@sv.on_message('group')
async def stick_monkey(bot, ev: CQEvent):
    group_id = ev.group_id
    
    # 加载当前群的设置
    monkey_settings = load_group_settings(group_id)
    
    # 如果全局开关关闭，且没有设置特定用户或关键词，则不处理
    if not monkey_settings['global_enabled'] and \
       not monkey_settings['target_users'] and \
       not monkey_settings['target_keywords']:
        return
    
    user_id = ev.user_id
    message = str(ev.message)
    
    # 检查是否针对特定用户
    target_user_match = False
    if monkey_settings['target_users']:
        if user_id in monkey_settings['target_users']:
            target_user_match = True
        else:
            # 如果设置了目标用户但当前用户不在其中，则不处理
            return
    
    # 检查是否包含关键词
    keyword_match = False
    if monkey_settings['target_keywords']:
        contains_keyword = any(keyword in message for keyword in monkey_settings['target_keywords'])
        if contains_keyword:
            keyword_match = True
        else:
            # 如果设置了关键词但当前消息不包含，则不处理
            return
    
    # 如果是针对特定用户或关键词的模式，则100%贴猴
    if target_user_match or keyword_match:
        # 添加随机延迟 (0-1秒)
        await asyncio.sleep(random.random())
        
        # 获取消息ID
        message_id = ev.message_id
        
        try:
            # 使用HoshinoBot提供的call_action方法
            result = await bot.call_action('set_msg_emoji_like', 
                                          message_id=message_id, 
                                          emoji_id=MONKEY_EMOJI_ID)
            
            if result.get('retcode') == 0:
                sv.logger.info(f"成功给消息 {message_id} 添加猴子表情")
            else:
                sv.logger.error(f"添加表情失败: {result}")
        
        except Exception as e:
            sv.logger.error(f"调用API时出错: {e}")
        return
    
    # 如果是无差别模式，使用设置的概率
    if monkey_settings['global_enabled']:
        if random.random() > monkey_settings['global_probability']:
            return
        
        # 添加随机延迟 (0-1秒)
        await asyncio.sleep(random.random())
        
        # 获取消息ID
        message_id = ev.message_id
        
        try:
            # 使用HoshinoBot提供的call_action方法
            result = await bot.call_action('set_msg_emoji_like', 
                                          message_id=message_id, 
                                          emoji_id=MONKEY_EMOJI_ID)
            
            if result.get('retcode') == 0:
                sv.logger.info(f"成功给消息 {message_id} 添加猴子表情")
            else:
                sv.logger.error(f"添加表情失败: {result}")
        
        except Exception as e:
            sv.logger.error(f"调用API时出错: {e}")

# 贴猴初始化
@sv.on_fullmatch('贴猴初始化')
async def init_monkey_settings(bot, ev: CQEvent):
    if not is_admin(ev):
        await bot.send(ev, "需要管理员权限才能执行此操作", at_sender=True)
        return
    
    group_id = ev.group_id
    
    # 重置为默认设置
    settings = DEFAULT_SETTINGS.copy()
    save_group_settings(group_id, settings)
    
    await bot.send(ev, f"群 {group_id} 的贴猴设置已初始化")

# 设置无差别贴猴概率（可开启或修改概率）
@sv.on_prefix('开启无差别贴猴')
async def set_global_monkey_probability(bot, ev: CQEvent):
    if not is_admin(ev):
        await bot.send(ev, "需要管理员权限才能执行此操作", at_sender=True)
        return
    
    group_id = ev.group_id
    
    # 加载当前群的设置
    monkey_settings = load_group_settings(group_id)
    
    # 获取原始消息文本
    raw_message = ev.message.extract_plain_text().strip()
    
    # 使用正则表达式提取概率参数
    match = re.search(r'(\d+(?:\.\d+)?)%?', raw_message)
    
    # 记录当前状态
    was_enabled = monkey_settings['global_enabled']
    
    if match:
        try:
            # 提取数字并转换为小数
            probability_value = float(match.group(1))
            
            # 如果数字大于1，假设是百分比格式
            if probability_value > 1:
                probability = probability_value / 100.0
            else:
                probability = probability_value
            
            # 确保概率在0-1之间
            probability = max(0.0, min(1.0, probability))
            monkey_settings['global_probability'] = probability
        except ValueError:
            await bot.send(ev, "概率参数格式错误，请输入0-100之间的数字", at_sender=True)
            return
    else:
        # 默认100%概率
        monkey_settings['global_probability'] = 1.0
    
    # 开启无差别贴猴模式
    monkey_settings['global_enabled'] = True
    
    # 保存设置
    save_group_settings(group_id, monkey_settings)
    
    probability_percent = monkey_settings['global_probability'] * 100
    
    if was_enabled:
        await bot.send(ev, f"已更新无差别贴猴概率: {probability_percent:.1f}%")
    else:
        await bot.send(ev, f"已开启无差别贴猴模式，概率: {probability_percent:.1f}%")

# 关闭无差别贴猴
@sv.on_fullmatch('关闭无差别贴猴')
async def disable_global_monkey(bot, ev: CQEvent):
    if not is_admin(ev):
        await bot.send(ev, "需要管理员权限才能执行此操作", at_sender=True)
        return
    
    group_id = ev.group_id
    
    # 加载当前群的设置
    monkey_settings = load_group_settings(group_id)
    
    monkey_settings['global_enabled'] = False
    
    # 保存设置
    save_group_settings(group_id, monkey_settings)
    
    await bot.send(ev, "已关闭无差别贴猴模式")

# 添加目标用户
@sv.on_prefix('贴猴成员')
async def add_target_user(bot, ev: CQEvent):
    if not is_admin(ev):
        await bot.send(ev, "需要管理员权限才能执行此操作", at_sender=True)
        return
    
    group_id = ev.group_id
    
    # 加载当前群的设置
    monkey_settings = load_group_settings(group_id)
    
    # 获取被@的用户
    target_users = []
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            target_users.append(int(m.data['qq']))
    
    if not target_users:
        await bot.send(ev, "请@要贴猴的成员", at_sender=True)
        return
    
    # 添加用户到目标列表
    added_count = 0
    for user_id in target_users:
        if user_id not in monkey_settings['target_users']:
            monkey_settings['target_users'].append(user_id)
            added_count += 1
    
    # 保存设置
    save_group_settings(group_id, monkey_settings)
    
    await bot.send(ev, f"已添加 {added_count} 个用户到贴猴目标列表")

# 移除目标用户
@sv.on_prefix('取消贴猴成员')
async def remove_target_user(bot, ev: CQEvent):
    if not is_admin(ev):
        await bot.send(ev, "需要管理员权限才能执行此操作", at_sender=True)
        return
    
    group_id = ev.group_id
    
    # 加载当前群的设置
    monkey_settings = load_group_settings(group_id)
    
    # 获取被@的用户
    target_users = []
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            target_users.append(int(m.data['qq']))
    
    if not target_users:
        await bot.send(ev, "请@要取消贴猴的成员", at_sender=True)
        return
    
    # 从目标列表中移除用户
    removed_count = 0
    for user_id in target_users:
        if user_id in monkey_settings['target_users']:
            monkey_settings['target_users'].remove(user_id)
            removed_count += 1
    
    # 保存设置
    save_group_settings(group_id, monkey_settings)
    
    await bot.send(ev, f"已从贴猴目标列表中移除 {removed_count} 个用户")

# 添加关键词
@sv.on_prefix('贴猴关键词')
async def add_keyword(bot, ev: CQEvent):
    if not is_admin(ev):
        await bot.send(ev, "需要管理员权限才能执行此操作", at_sender=True)
        return
    
    group_id = ev.group_id
    
    # 加载当前群的设置
    monkey_settings = load_group_settings(group_id)
    
    # 使用正则表达式提取关键词（排除指令部分）
    raw_message = ev.message.extract_plain_text().strip()
    keyword_match = re.search(r'贴猴关键词\s+(.+)', raw_message)
    
    if keyword_match:
        keyword = keyword_match.group(1).strip()
    else:
        keyword = raw_message
    
    if not keyword:
        await bot.send(ev, "请输入要添加的关键词", at_sender=True)
        return
    
    if keyword not in monkey_settings['target_keywords']:
        monkey_settings['target_keywords'].append(keyword)
        # 保存设置
        save_group_settings(group_id, monkey_settings)
        await bot.send(ev, f"已添加关键词: {keyword}")
    else:
        await bot.send(ev, f"关键词 {keyword} 已存在")

# 移除关键词
@sv.on_prefix('取消贴猴关键词')
async def remove_keyword(bot, ev: CQEvent):
    if not is_admin(ev):
        await bot.send(ev, "需要管理员权限才能执行此操作", at_sender=True)
        return
    
    group_id = ev.group_id
    
    # 加载当前群的设置
    monkey_settings = load_group_settings(group_id)
    
    # 使用正则表达式提取关键词（排除指令部分）
    raw_message = ev.message.extract_plain_text().strip()
    keyword_match = re.search(r'取消贴猴关键词\s+(.+)', raw_message)
    
    if keyword_match:
        keyword = keyword_match.group(1).strip()
    else:
        keyword = raw_message
    
    if not keyword:
        await bot.send(ev, "请输入要移除的关键词", at_sender=True)
        return
    
    if keyword in monkey_settings['target_keywords']:
        monkey_settings['target_keywords'].remove(keyword)
        # 保存设置
        save_group_settings(group_id, monkey_settings)
        await bot.send(ev, f"已移除关键词: {keyword}")
    else:
        await bot.send(ev, f"关键词 {keyword} 不存在")

# 查看当前设置
@sv.on_fullmatch('查看贴猴设置')
async def view_monkey_settings(bot, ev: CQEvent):
    if not is_admin(ev):
        await bot.send(ev, "需要管理员权限才能执行此操作", at_sender=True)
        return
    
    group_id = ev.group_id
    
    # 加载当前群的设置
    monkey_settings = load_group_settings(group_id)
    
    probability_percent = monkey_settings['global_probability'] * 100
    
    # 格式化用户列表
    target_users = monkey_settings['target_users']
    if target_users:
        users_str = ', '.join([str(uid) for uid in target_users])
    else:
        users_str = '无'
    
    # 格式化关键词列表
    target_keywords = monkey_settings['target_keywords']
    if target_keywords:
        keywords_str = ', '.join(target_keywords)
    else:
        keywords_str = '无'
    
    settings_msg = f"""
当前群({group_id})贴猴设置:
无差别贴猴: {'开启' if monkey_settings['global_enabled'] else '关闭'}
无差别贴猴概率: {probability_percent:.1f}%
目标用户: {users_str}
关键词: {keywords_str}
""".strip()
    
    await bot.send(ev, settings_msg)

# 检查是否已初始化
@sv.on_fullmatch('检查贴猴设置')
async def check_monkey_settings(bot, ev: CQEvent):
    group_id = ev.group_id
    group_file = get_group_file(group_id)
    
    if group_file.exists():
        await bot.send(ev, f"群 {group_id} 的贴猴设置已存在")
    else:

        await bot.send(ev, f"群 {group_id} 尚未初始化贴猴设置，请管理员发送【贴猴初始化】")
