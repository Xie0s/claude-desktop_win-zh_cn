#!/usr/bin/env python3
"""Sync missing zh-CN i18n keys from the installed Claude resources.

This is a deterministic best-effort updater for version bumps. It keeps all
existing translations, reuses exact translation memory, then applies a compact
rule dictionary for newly added strings.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_RESOURCES = ROOT / "resources"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import patch_windowsapps_json_only  # noqa: E402


RESOURCE_PAIRS = {
    "desktop": {
        "local": LOCAL_RESOURCES / "desktop-zh-CN.json",
        "installed_en": Path("resources/en-US.json"),
    },
    "frontend": {
        "local": LOCAL_RESOURCES / "frontend-zh-CN.json",
        "installed_en": Path("resources/ion-dist/i18n/en-US.json"),
    },
    "statsig": {
        "local": LOCAL_RESOURCES / "statsig-zh-CN.json",
        "installed_en": Path("resources/ion-dist/i18n/statsig/en-US.json"),
    },
}


EXACT_TRANSLATIONS = {
    "Active Claude Code users in this period": "此期间活跃的 Claude Code 用户",
    "Adds to this run's prompt:": "添加到本次运行的提示词：",
    "Adding marketplaces is blocked by your organization's policy. Contact your administrator.": "添加市场已被组织策略阻止。请联系管理员。",
    "Allow using Claude Design to generate design artifacts.": "允许使用 Claude Design 生成设计工件。",
    "Allow your team to run multi-agent workflows in Claude Code.": "允许你的团队在 Claude Code 中运行多智能体工作流。",
    "Always uses deep reasoning": "始终使用深度推理",
    "Already in this workspace": "已在此工作区中",
    "About discoverable domains": "关于可发现域名",
    "About this chart": "关于此图表",
    "Account executive": "客户经理",
    "Actuary": "精算师",
    "Academic": "学术人员",
    "AI engineer": "AI 工程师",
    "Artifcats that stay up to date": "保持更新的工件",
    "Artifacts that stay up to date": "保持更新的工件",
    "At limit": "已达限制",
    "Auto-accept permissions mode": "自动接受权限模式",
    "Balanced for everyday work": "适合日常工作的均衡模式",
    "Business owner": "企业主",
    "Business development": "业务拓展",
    "Buying agent": "采购代理",
    "By group / tier": "按组/层级",
    "By clicking to accept, you represent and warrant that: (i) you are the individual registered to this administrator account; (ii) you have full legal authority to bind {organization} to this BAA; (iii) you have read and understand this BAA and the Implementation Guide; and (iv) you agree, on behalf of your Organization, to the terms and conditions of this BAA.": "点击接受即表示你声明并保证：(i) 你是此管理员账号的注册个人；(ii) 你拥有让 {organization} 受此 BAA 约束的完整法律权限；(iii) 你已阅读并理解此 BAA 和实施指南；(iv) 你代表组织同意此 BAA 的条款和条件。",
    "Bypass permissions mode and auto mode controls for Claude Code Desktop are moving to Managed settings on June 5, 2026, alongside the CLI and IDE.": "Claude Code Desktop 的绕过权限模式和自动模式控制项将于 2026 年 6 月 5 日与 CLI 和 IDE 一起迁移到托管设置。",
    "Can think for more complex tasks": "可为更复杂的任务进行思考",
    "Change location for Cowork files?": "更改 Cowork 文件位置？",
    "Checking install status…": "正在检查安装状态…",
    "Choose Claude data folder": "选择 Claude 数据文件夹",
    "Claude Code analytics view": "Claude Code 分析视图",
    "Claude Code remote control": "Claude Code 远程控制",
    "Claude for Outlook": "Claude for Outlook",
    "Claude Pro is required to connect to Claude Code": "连接 Claude Code 需要 Claude Pro",
    "Claude Security requires usage credits to be turned on. Contact an organization admin to turn them on.": "Claude Security 需要开启用量额度。请联系组织管理员开启。",
    "Claude will keep these in mind across chats and Cowork within Anthropic's guidelines. Learn more": "Claude 会在 Anthropic 指南范围内，在聊天和 Cowork 中记住这些内容。了解更多",
    "Claude will keep these in mind across chats and Cowork within <aupLink>Anthropic's guidelines</aupLink>. <learnMoreLink>Learn more</learnMoreLink>": "Claude 会在聊天和 Cowork 中记住这些内容，并遵循<aupLink>Anthropic 的指南</aupLink>。<learnMoreLink>了解更多</learnMoreLink>",
    "Claude is still working": "Claude 仍在工作",
    "Claude is working in {count, plural, one {# session} other {# sessions}}. Quitting now will interrupt that work.": "Claude 正在 {count, plural, one {# 个会话} other {# 个会话}} 中工作。现在退出会中断这些工作。",
    "Complex, detailed work": "复杂、细致的工作",
    "Connected · {latency}ms": "已连接 · {latency}ms",
    "Connector data hidden in shared chats": "共享聊天中已隐藏连接器数据",
    "Connector updated": "连接器已更新",
    "Connectors needed": "需要连接器",
    "Controls which repositories Claude can reach across your organization.": "控制 Claude 可访问组织中的哪些仓库。",
    "Connect your organization's GitHub Enterprise instances to enable code review and repository access.": "连接组织的 GitHub Enterprise 实例，以启用代码审查和仓库访问。",
    "Continue without answering": "不回答并继续",
    "Copy and restart": "复制并重启",
    "Copy organization ID": "复制组织 ID",
    "Copy relative path": "复制相对路径",
    "Couldn’t rotate the secret. Try again.": "无法轮换密钥。请重试。",
    "Crash reports and error diagnostics, so we can fix bugs": "崩溃报告和错误诊断，用于帮助修复问题",
    "Create API key": "创建 API 密钥",
    "Daily usage: {capped} of {total, plural, one {# day} other {# days}} hit the limit": "每日用量：{total, plural, one {# 天} other {# 天}}中有 {capped} 天达到限制",
    "Define a collection of users": "定义一组用户",
    "Detached comment": "分离的评论",
    "Digital marketer": "数字营销人员",
    "Dismiss session": "关闭会话",
    "Domain claim could not be started because one or more required settings were changed. Review the requirements and try again.": "由于一个或多个必需设置已更改，无法开始域名声明。请检查要求后重试。",
    "Domains where this credential can be sent. Wildcard only as the leftmost label (e.g. *.example.com).": "此凭据可发送到的域名。通配符只能作为最左侧标签使用（例如 *.example.com）。",
    "Discard Changes": "放弃更改",
    "Apply Changes": "应用更改",
    "Discard unsaved changes?": "放弃未保存的更改？",
    "Estimated usage cost": "预计用量成本",
    "Dynamic workflows": "动态工作流",
    "Empty": "空",
    "Extended": "扩展",
    "Extra": "超高",
    "Failed to remove source.": "移除来源失败。",
    "Failed to save rule. Check your inputs and try again.": "保存规则失败。请检查输入后重试。",
    "Failed to update Claude Code setting. You can try again.": "更新 Claude Code 设置失败。你可以重试。",
    "Feature requests ({count})": "功能请求（{count}）",
    "Faster": "更快",
    "Financial analyst": "金融分析师",
    "Filter projects (active)": "筛选项目（活跃）",
    "General restrictions": "通用限制",
    "Get Claude Code": "获取 Claude Code",
    "Get usage credits when you run it": "运行时获取用量额度",
    "Give your developers access to Claude Code": "向开发者开放 Claude Code 访问权限",
    "GitHub App installed": "GitHub App 已安装",
    "GitHub access check failed": "GitHub 访问检查失败",
    "GitHub App": "GitHub App",
    "GitHub credentials were rejected. Reconnect GitHub to continue.": "GitHub 凭据被拒绝。请重新连接 GitHub 后继续。",
    "Have a visual UI MCP App now? Email your carousel images to <link>{email}</link> and we'll attach them to your listing manually.": "已经有可视化 UI MCP App 了吗？请将轮播图发送到 <link>{email}</link>，我们会手动附加到你的列表。",
    "High-contrast dark theme": "高对比度深色主题",
    "Holding {keys}": "按住 {keys}",
    "Install Claude Code in your terminal or IDE": "在终端或 IDE 中安装 Claude Code",
    "Inference configuration": "推理配置",
    "Invite requested": "已请求邀请",
    "Invalid request": "无效请求",
    "Installation": "安装",
    "Intelligence analyst": "情报分析师",
    "Issuer URLs the OAuth sign-in may use, as a JSON array. Pre-filled by presets; ask your IdP admin if unsure.": "OAuth 登录可使用的颁发者 URL，格式为 JSON 数组。预设会自动填充；不确定时请询问你的 IdP 管理员。",
    "Keep chatting": "继续聊天",
    "Keep editing": "继续编辑",
    "Learn how to level up": "了解如何进阶",
    "Light, casual tasks": "轻量、日常任务",
    "Loading older messages": "正在加载较早消息",
    "Loading routines": "正在加载例程",
    "Loading devices…": "正在加载设备…",
    "Loading output…": "正在加载输出…",
    "Low": "低",
    "Longer chats draw down your usage faster": "较长聊天会更快消耗你的用量",
    "Match a writing style": "匹配写作风格",
    "Max": "超高",
    "Medium": "中",
    "Migrate accounts using your domains": "使用你的域名迁移账号",
    "Monthly limit": "每月限制",
    "More usage, SSO, advanced security, and dedicated support for your organization.": "为你的组织提供更多用量、SSO、高级安全和专属支持。",
    "Not in use — toggle on to fetch and apply this URL.": "未使用；开启后会获取并应用此 URL。",
    "Not delivered": "未送达",
    "Not synced yet": "尚未同步",
    "No active subscription": "没有活跃订阅",
    "No browsers connected": "没有已连接的浏览器",
    "No chats match “{query}”": "没有匹配“{query}”的聊天",
    "No limit": "无限制",
    "no limit": "无限制",
    "No limit set": "未设置限制",
    "No messages yet": "暂无消息",
    "No project": "没有项目",
    "No runs yet": "暂无运行",
    "No server selected.": "未选择服务器。",
    "No targets routed through this proxy yet.": "尚无目标通过此代理路由。",
    "Off": "关",
    "Offer 1M-context variant": "提供 1M 上下文变体",
    "Org default": "组织默认值",
    "Outline my pitch deck": "梳理我的路演演示结构",
    "Power user": "深度用户",
    "Photographer": "摄影师",
    "Physiotherapist": "物理治疗师",
    "Primary school teacher": "小学教师",
    "Private equity associate": "私募股权投资助理",
    "Product owner": "产品负责人",
    "Project ID": "项目 ID",
    "Project conversation view": "项目对话视图",
    "Program manager": "项目经理",
    "Public Projects": "公共项目",
    "Quick replies to simple questions": "适合简单问题的快速回复",
    "Reading console messages": "正在读取控制台消息",
    "Reading memory…": "正在读取记忆…",
    "Reading network requests": "正在读取网络请求",
    "Request usage credits": "请求用量额度",
    "Remove queued message": "移除排队消息",
    "Request is too large": "请求过大",
    "Restricted by your organization's Managed settings. Update Managed settings or your MDM-deployed configuration to change this.": "受组织的托管设置限制。请更新托管设置或 MDM 下发配置来更改此项。",
    "Restart to apply this configuration.": "重启以应用此配置。",
    "Running on this device": "正在此设备上运行",
    "Runs weekdays at {time} {tz}": "工作日 {time} {tz} 运行",
    "SCIM synced": "已通过 SCIM 同步",
    "Scanning…": "正在扫描…",
    "Search artifacts...": "搜索工件...",
    "Searching…": "正在搜索…",
    "Secure VM features": "安全虚拟机功能",
    "Secret copied to clipboard.": "密钥已复制到剪贴板。",
    "Shown in the model picker. Leave blank to auto-format from the ID.": "显示在模型选择器中。留空则根据 ID 自动格式化。",
    "Show fewer": "显示更少",
    "Sidebar pins and starred sessions survive sign-out": "侧边栏固定项和星标会话会在退出登录后保留",
    "Session was interrupted": "会话已中断",
    "Sessions you start will show up here": "你启动的会话会显示在这里",
    "Set up usage credits so anyone with a usage-based seat can use Claude.": "设置用量额度，让任何拥有按用量计费席位的人都可以使用 Claude。",
    "This capability is enabled but its required capability Chat is not.": "此能力已启用，但必需的 Chat 能力未启用。",
    "This capability is enabled but its required capability Claude Code is not.": "此能力已启用，但必需的 Claude Code 能力未启用。",
    "This capability is enabled but its required capability Cowork is not.": "此能力已启用，但必需的 Cowork 能力未启用。",
    "This connector doesn't use authentication. You can block individual tools instead.": "此连接器不使用身份验证。你可以改为阻止单个工具。",
    "This runner's token is invalidated immediately. Its next API call will be rejected.": "此运行器的令牌会立即失效。它的下一次 API 调用将被拒绝。",
    "Software architect": "软件架构师",
    "Solopreneur": "个体创业者",
    "Sports coach": "体育教练",
    "Something went wrong. Try again.": "出了点问题。请重试。",
    "Spend · {used}": "消耗 · {used}",
    "Spend · {used} of {limit}": "消耗 · {used} / {limit}",
    "Stop this task": "停止此任务",
    "Supply chain manager": "供应链经理",
    "Team": "团队",
    "Thinking": "思考",
    "The hardest problems. Takes longest.": "最困难的问题。耗时最长。",
    "Higher effort means more thorough responses, but takes longer and uses your limits faster.": "更高强度意味着回答更彻底，但耗时更长，也会更快消耗你的额度。",
    "May use excessive tokens resulting in long response times and may hit token limits. Use sparingly for the hardest tasks.": "可能使用大量 token，导致响应时间较长，并可能触及 token 限制。仅建议在最困难的任务中谨慎使用。",
    "This clears your current conversation and starts a new one.": "这会清空当前对话并开始一个新对话。",
    "Turn any idea into a diagram, chart, or visual you can click and explore.": "将任何想法变成可点击、可探索的图表、图形或可视化内容。",
    "Type or paste in emails separated by commas or new lines": "输入或粘贴邮箱，并用逗号或换行分隔",
    "Updated {time}": "已更新 {time}",
    "Usage-limit notices now say which limit you hit and when it resets": "用量限制通知现在会说明你触及了哪项限制以及何时重置",
    "Usage credits ({count})": "用量额度（{count}）",
    "Usage credits draw down as you go. Good for occasional busy days.": "用量额度会随使用扣减，适合偶尔忙碌的日子。",
    "Usage credits show up on your invoice at the end of each billing cycle.": "用量额度会在每个账单周期结束时显示在发票上。",
    "Visualize anything": "可视化任何内容",
    "We'll package up your conversations, projects, and settings for download. This might take some time to complete.": "我们会打包你的对话、项目和设置供下载。这可能需要一些时间。",
    "We're doing some quick maintenance on billing. Your current plan still works as usual — check back shortly to upgrade.": "我们正在进行账单快速维护。你的当前方案仍可正常使用，请稍后再回来升级。",
    "Which organization is this about?": "这是关于哪个组织？",
    "What do you want automated?": "你想自动化什么？",
    "Your GitHub credentials were rejected. Reconnect GitHub to continue.": "你的 GitHub 凭据被拒绝。请重新连接 GitHub 后继续。",
    "Your local time, next day": "你的本地时间，次日",
    "Your session has expired.": "你的会话已过期。",
    "Your session has expired. Sign in again from the home screen.": "你的会话已过期。请从主屏幕重新登录。",
    "Your session credentials expired.": "你的会话凭据已过期。",
    "Your organization hasn't provided plugins. Contact your organization administrator to add them.": "这是组织插件目录。当前组织尚未提供插件；本地/个人插件请前往“设置 > 自定义 > 个人插件”上传或管理。",
    "Your organization hasn’t provided plugins. Contact your organization administrator to add them.": "这是组织插件目录。当前组织尚未提供插件；本地/个人插件请前往“设置 > 自定义 > 个人插件”上传或管理。",
    "Your organization has disabled usage.": "你的组织已禁用用量。",
    "Registered nurse": "注册护士",
    "Payroll specialist": "薪资专员",
    "Psychiatrist": "精神科医生",
    "Therapist": "治疗师",
    "Vice president": "副总裁",
    "Sign in again": "重新登录",
    "Cancel": "取消",
    "Open": "打开",
    "Choose": "选择",
    "Leave": "离开",
    "Design": "设计",
    "Pro": "Pro",
    "Headers": "标头",
    "Header": "标头",
    "Invocations": "调用次数",
    "OAuth 2.0 JWT bearer": "OAuth 2.0 JWT bearer",
    "{pct} · resets {date}": "{pct} · {date} 重置",
    "{pct} · resets {when}": "{pct} · {when} 重置",
    "{product} grant": "{product} 授权额度",
    "{tier} plan": "{tier} 方案",
    "· in {dir}": "· 位于 {dir}",
    "<b>{category}</b> needs {count, plural, one {{label}} other {# fields}}": "<b>{category}</b> 需要 {count, plural, one {{label}} other {# 个字段}}",
}


EFFORT_TRANSLATIONS = {
    "Effort": "推理强度",
    "About effort": "关于推理强度",
    "Higher effort means more thorough responses, but takes longer and uses your limits faster.": "更高的推理强度会带来更全面的回答，但耗时更长，也会更快消耗你的额度。",
    "Faster": "响应更快",
    "Smarter": "回答更深入",
    "Change effort level?": "更改推理强度？",
    "Open effort selector": "打开推理强度选择器",
    "Choose effort with a slider next to the model picker": "使用模型选择器旁的滑杆选择推理强度",
    "Effort change couldn’t be applied. You can try again.": "无法应用推理强度更改。你可以重试。",
    "Max effort can use excessive tokens resulting in hitting limits. Consider using a lower effort setting.": "最高推理强度可能使用过多 token，导致触及限制。请考虑使用较低的推理强度设置。",
    "Your next response will be slower and use more tokens. This task is cached for the current effort level. Switching to <bold>{targetLabel}</bold> means the full history gets re-read on your next message.": "你的下一条回复会更慢，并使用更多 token。此任务已按当前推理强度缓存。切换到 <bold>{targetLabel}</bold> 意味着下一条消息会重新读取完整历史。",
    "Ultracode": "Ultracode",
    "Ultracode is xhigh effort plus workflows. Most thorough, slowest, and heaviest on your limits. Applies to this chat only. New chats start without it.": "Ultracode 结合超高推理强度与工作流。它的回答最全面、耗时最长，也最消耗你的额度。仅适用于当前对话；新对话默认不会启用。",
}

EXACT_TRANSLATIONS.update(EFFORT_TRANSLATIONS)


QUALITY_TRANSLATIONS = {
    "RECOMMENDED": "推荐",
    "Open it on GitHub instead.": "改为在 GitHub 上打开。",
    "Failed to update Routines setting. You can try again.": "更新例程设置失败。你可以重试。",
    "SKILL.md is missing its frontmatter, so the description can’t be updated. Fix the file’s leading --- block and try again.": "SKILL.md 缺少 frontmatter，因此无法更新描述。请修复文件开头的 --- 块，然后重试。",
    "Anthropic Sans": "Anthropic Sans",
    "Cancel rename": "取消重命名",
    "“We hit the seat cap in week two.” — Meridian, renewal call": "“第二周我们就达到席位上限了。”——Meridian，续约通话",
    "Failed to read the device's state: No simulator with UDID {udid}": "无法读取设备状态：找不到 UDID 为 {udid} 的模拟器",
    "Claude pressed Siri": "Claude 按下了 Siri",
    "Only for IdPs that don’t serve a .well-known discovery document. Set together with Token URL; requires Client ID.": "仅适用于不提供 \u0060.well-known\u0060 发现文档的 IdP。请与令牌 URL 一并设置；需要客户端 ID。",
    "Only for IdPs that don’t serve a .well-known discovery document. Set together with Authorization URL; requires Client ID.": "仅适用于不提供 \u0060.well-known\u0060 发现文档的 IdP。请与授权 URL 一并设置；需要客户端 ID。",
    "This worktree no longer links back to its repository, usually because the folder was moved or renamed. Run git worktree repair inside the folder, then try again.": "此工作树已不再关联其仓库，通常是因为文件夹被移动或重命名。请在该文件夹中运行 git worktree repair，然后重试。",
    "Defaults to the token URL. Okta users normally leave this empty.": "默认为令牌 URL。Okta 用户通常留空。",
    "Enter a path like scripts/run.py.": "请输入类似 scripts/run.py 的路径。",
    "Keep Max 20x": "保留 Max 20x",
    "Adds offline_access to the authorize request so the IdP returns a refresh token for silent renewal.": "在授权请求中添加 offline_access，使 IdP 返回刷新令牌，以便静默续期。",
    "Block Claude’s mobile simulator tools (iOS Simulator and Android Emulator) in Claude Code. Users can still run and operate simulators themselves.": "在 Claude Code 中阻止 Claude 使用移动端模拟器工具（iOS Simulator 和 Android Emulator）。用户仍可自行运行和操作模拟器。",
    "roles": "角色",
    "Couldn’t load environments. Try again.": "无法加载环境。请重试。",
    "Coordinator model": "协调器模型",
    "Switch to Max 5x": "切换到 Max 5x",
    "Use this value in your AWS KMS key policy condition on kms:EncryptionContext:anthropic:compartment_uuid to restrict the key to your organization.": "在 AWS KMS 密钥策略的 kms:EncryptionContext:anthropic:compartment_uuid 条件中使用此值，将密钥限制在你的组织内。",
    "Choose project": "选择项目",
    "Your WorktreeCreate hook failed": "你的 WorktreeCreate 钩子执行失败",
    "being created": "正在创建",
    "Keep Max 5x": "保留 Max 5x",
    "Design system": "设计系统",
    "Choose emulator": "选择模拟器",
    "Couldn't find \u0060adb\u0060. Install Android SDK platform-tools (or set ANDROID_HOME).": "找不到 \u0060adb\u0060。请安装 Android SDK platform-tools（或设置 ANDROID_HOME）。",
    "Teams user": "Teams 用户",
    "Failed to update fast mode setting. You can try again.": "更新快速模式设置失败。你可以重试。",
    "Priya needs your take on the launch email": "Priya 需要你对发布邮件的看法",
    "Sessions created": "已创建会话",
    "Includes Claude Design": "包含 Claude Design",
    "Failed to update Artifacts setting. You can try again.": "更新工件设置失败。你可以重试。",
    "Simulator installed": "模拟器已安装",
    "Only enable if your IdP rejects the offline_access scope on this client. Without it the app prompts for sign-in each time the token expires.": "仅当你的 IdP 拒绝此客户端的 offline_access 作用域时启用。否则，每次令牌过期时，应用都会提示你登录。",
    "Your instructions start with a --- frontmatter block. Remove it — the name and description fields above become the frontmatter.": "你的指令以 --- frontmatter 块开头。请删除它，上方的名称和描述字段会成为 frontmatter。",
    "I work in {role}.": "我的工作领域是 {role}。",
    "Fast mode requires usage credits. Turn them on under <link>Usage</link>.": "快速模式需要用量额度。请在 <link>用量</link> 下开启。",
    "Your WorktreeCreate hook didn’t complete successfully. Check the hook output in the details below and fix the hook, then send your message again.": "你的 WorktreeCreate 钩子未成功完成。请检查下方详细信息中的钩子输出，修复钩子后重新发送消息。",
}

ICU_QUALITY_TRANSLATIONS = {
    "{pluginCount, plural, =0 {no plugins} one {# plugin} other {# plugins}}": "{pluginCount, plural, =0 {无插件} one {# 个插件} other {# 个插件}}",
    "{count, plural, one {# commit pushed} other {# commits pushed}}": "{count, plural, one {已推送 # 个提交} other {已推送 # 个提交}}",
    "Your own account is in good standing, but {count, plural, one {an organization you belong to is on hold because we found signals it was used by someone under 18.} other {# organizations you belong to are on hold because we found signals they were used by someone under 18.}} Verify your age below to restore access.": "你的账号状态正常，但 {count, plural, one {你所属的一个组织已被暂停，因为我们发现该组织可能由未满 18 岁的人使用。} other {你所属的 # 个组织已被暂停，因为我们发现这些组织可能由未满 18 岁的人使用。}} 请在下方验证年龄以恢复访问权限。",
    "Your purchase from {time} is waiting on card verification from your bank. Finish the verification in your bank’s app or popup, or wait. Unfinished attempts expire in {minutes, plural, one {# minute} other {# minutes}}. Trying a different card won’t help until then.": "你在 {time} 发起的购买正在等待银行验证付款卡。请在银行应用或弹窗中完成验证，也可以继续等待。未完成的尝试将在 {minutes, plural, one {# 分钟} other {# 分钟}}后过期。在此之前更换银行卡也无法继续。",
    "{count, plural, one {# environment} other {# environments}}": "{count, plural, one {# 个环境} other {# 个环境}}",
    "Shared artifacts will be deleted after {count, plural, one {# month} other {# months}} of inactivity": "共享工件在连续 {count, plural, one {# 个月} other {# 个月}}未使用后将被删除",
    "{count, plural, one {# repository} other {# repositories}}": "{count, plural, one {# 个仓库} other {# 个仓库}}",
    "{connCount, plural, =0 {no connections} one {# connection} other {# connections}}": "{connCount, plural, =0 {无连接} one {# 个连接} other {# 个连接}}",
    "{queued, plural, one {# session queued} other {# sessions queued}}": "{queued, plural, one {# 个会话已排队} other {# 个会话已排队}}",
    "That edit is too long — memory edits are limited to {max, plural, one {# character} other {# characters}}.": "此次编辑内容过长。记忆编辑最多支持 {max, plural, one {# 个字符} other {# 个字符}}。",
    "Model couldn’t be set for {count, plural, one {# session} other {# sessions}}. Try again.": "无法为 {count, plural, one {# 个会话} other {# 个会话}}设置模型。请重试。",
    "Private artifacts will be deleted after {count, plural, one {# month} other {# months}} of inactivity": "私有工件在连续 {count, plural, one {# 个月} other {# 个月}}未使用后将被删除",
    "{count, plural, one {Removed # image} other {Removed # images}} — this session allows up to {max}.": "{count, plural, one {已移除 # 张图片} other {已移除 # 张图片}}。此会话最多允许 {max} 张图片。",
    "{attempts, plural, one {# attempt} other {# attempts}}.": "{attempts, plural, one {# 次尝试} other {# 次尝试}}。",
    "… {count, plural, one {# more character} other {# more characters}}. Open the hook in the plugin’s Hooks tab for the full command.": "…还有 {count, plural, one {# 个字符} other {# 个字符}}。请在插件的“钩子”标签页中打开该钩子，以查看完整命令。",
    "Chats, projects, and artifacts will be deleted after {count, plural, one {# month} other {# months}} of inactivity": "聊天、项目和工件在连续 {count, plural, one {# 个月} other {# 个月}}未使用后将被删除",
    "Memory edits are limited to {max, plural, one {# character} other {# characters}}.": "记忆编辑最多支持 {max, plural, one {# 个字符} other {# 个字符}}。",
    "Model set for {count, plural, one {# session} other {# sessions}}": "已为 {count, plural, one {# 个会话} other {# 个会话}}设置模型",
    "{count, plural, one {Skill proposal} other {Skill proposals}}": "{count, plural, one {技能建议} other {技能建议}}",
    "{count, plural, one {An organization you belong to is on hold because we found signals it was used by someone under 18.} other {# organizations you belong to are on hold because we found signals they were used by someone under 18.}} Verify your age below to restore access.": "{count, plural, one {你所属的一个组织已被暂停，因为我们发现该组织可能由未满 18 岁的人使用。} other {你所属的 # 个组织已被暂停，因为我们发现这些组织可能由未满 18 岁的人使用。}} 请在下方验证年龄以恢复访问权限。",
    "{count, plural, one {# assigned member will automatically lose their seat at renewal.} other {# assigned members will automatically lose their seats at renewal, starting with the most recently assigned.}} You can reassign seats after renewal.": "{count, plural, one {# 名已分配成员将在续订时自动失去席位。} other {# 名已分配成员将在续订时自动失去席位，并从最近分配的成员开始。}} 续订后可以重新分配席位。",
    "A credit purchase for your organization, started at {time}, is still processing. This usually takes a few seconds. If it doesn’t complete, you can try again in {minutes, plural, one {# minute} other {# minutes}}.": "你所在组织于 {time} 发起的用量额度购买仍在处理中，通常只需几秒。如果仍未完成，可在 {minutes, plural, one {# 分钟} other {# 分钟}}后重试。",
    "{count, plural, =0 {Custom} one {Custom (# host)} other {Custom (# hosts)}}": "{count, plural, =0 {自定义} one {自定义（# 个主机）} other {自定义（# 个主机）}}",
    "Search history: {query}{matchIndex, plural, =0 {} one { — match # of {total}} other { — match # of {total}}}{failed, select, true { — no match} other {}}": "搜索历史：{query}{matchIndex, plural, =0 {} one { — 第 # 项，共 {total} 项} other { — 第 # 项，共 {total} 项}}{failed, select, true { — 无匹配项} other {}}",
    "{failed, plural, one {# failed session} other {# failed sessions}}": "{failed, plural, one {# 个失败的会话} other {# 个失败的会话}}",
    "{count, plural, one {# unresolved review comment} other {# unresolved review comments}}": "{count, plural, one {# 条未解决的审核评论} other {# 条未解决的审核评论}}",
    "{cached} cached · {searches, plural, one {# web search} other {# web searches}}": "已缓存 {cached} 条 · {searches, plural, one {# 次网页搜索} other {# 次网页搜索}}",
    "{count, plural, one {# result} other {# results}}. Some results couldn’t load. Try again in a moment.": "{count, plural, one {# 个结果} other {# 个结果}}。部分结果加载失败，请稍后重试。",
    "{count, plural, one {# assigned member will automatically lose their seat at the end of the billing period.} other {# assigned members will automatically lose their seats at the end of the billing period, starting with the most recently assigned.}} You can reassign seats after renewal.": "{count, plural, one {# 名已分配成员将在计费周期结束时自动失去席位。} other {# 名已分配成员将在计费周期结束时自动失去席位，并从最近分配的成员开始。}} 续订后可以重新分配席位。",
    "Chats, projects, and artifacts will be deleted after {count, plural, one {# day} other {# days}} of inactivity": "聊天、项目和工件在连续 {count, plural, one {# 天} other {# 天}}未使用后将被删除",
    "{count, plural, one {# thing blocks the merge} other {# things block the merge}}": "{count, plural, one {# 项内容阻止合并} other {# 项内容阻止合并}}",
    "Private artifacts will be deleted after {count, plural, one {# day} other {# days}} of inactivity": "私有工件在连续 {count, plural, one {# 天} other {# 天}}未使用后将被删除",
    "{queued, plural, one {# session is} other {# sessions are}} waiting. Check your deployment. Runners may have failed to start or can’t reach the API.": "{queued, plural, one {# 个会话} other {# 个会话}}正在等待。请检查部署；运行器可能启动失败，或无法访问 API。",
    "{count, plural, one {# connection} other {# connections}}": "{count, plural, one {# 个连接} other {# 个连接}}",
    "{count, plural, one {# person you added was already a member of this group} other {# people you added were already members of this group}}. They’re shown in the member list below. If you meant to remove them, remove them there and save again.": "{count, plural, one {你添加的 # 人已是此组成员} other {你添加的 # 人已是此组成员}}。这些成员显示在下方列表中。如果要移除他们，请在列表中移除后重新保存。",
    "Show {count} more personal {count, plural, one {account} other {accounts}}": "再显示 {count} 个个人{count, plural, one {账号} other {账号}}",
    "Saving will replace this environment’s custom network configuration{count, plural, =0 {} one { (# allowed host)} other { (# allowed hosts)}}.": "保存后会替换此环境的自定义网络配置{count, plural, =0 {} one {（# 个允许的主机）} other {（# 个允许的主机）}}。",
    "Shared artifacts will be deleted after {count, plural, one {# day} other {# days}} of inactivity": "共享工件在连续 {count, plural, one {# 天} other {# 天}}未使用后将被删除",
    "… {count, plural, one {# more hook action not shown} other {# more hook actions not shown}}. Open the plugin’s Hooks tab to review all of them.": "…还有 {count, plural, one {# 个钩子操作} other {# 个钩子操作}}未显示。请打开插件的“钩子”标签页查看全部操作。",
    "Across {count, plural, one {# session} other {# sessions}} with a PR": "涉及 {count, plural, one {# 个带 PR 的会话} other {# 个带 PR 的会话}}",
    "{count, plural, one {This file type needs} other {These file types need}} code execution, which isn’t available in this chat yet: {formats}": "{count, plural, one {此文件类型需要} other {这些文件类型需要}}执行代码，但此聊天暂不支持：{formats}",
    "{author} {verb, select, merged {merged {commits} into {base} from {head}} closed {wanted to merge {commits} into {base} from {head}} other {wants to merge {commits} into {base} from {head}}}": "{author} {verb, select, merged {已将 {commits} 从 {head} 合并到 {base}} closed {已关闭从 {head} 向 {base} 合并 {commits} 的请求} other {想将 {commits} 从 {head} 合并到 {base}}}",
    "{pluginCount, plural, one {# plugin} other {# plugins}}": "{pluginCount, plural, one {# 个插件} other {# 个插件}}",
    "Connect <orgPluginsLink>org plugins</orgPluginsLink> for {scope, select, channel {this channel} workspace {this workspace} other {all of Slack}}. Plugins from {scope, select, channel {the workspace, all of Slack, and access bundles} workspace {all of Slack and access bundles} other {access bundles}} are inherited automatically.": "为 {scope, select, channel {此频道} workspace {此工作区} other {整个 Slack}}连接<orgPluginsLink>组织插件</orgPluginsLink>。系统会自动继承来自 {scope, select, channel {工作区、整个 Slack 和访问包} workspace {整个 Slack 和访问包} other {访问包}}的插件。",
    "{failed, plural, one {# session} other {# sessions}} failed to start on a runner. Open the environment to retry.": "{failed, plural, one {# 个会话} other {# 个会话}}未能在运行器上启动。请打开环境重试。",
    "… {count, plural, one {# more character} other {# more characters}}. Open the monitor in the plugin’s Monitors tab for the full command.": "…还有 {count, plural, one {# 个字符} other {# 个字符}}。请在插件的“监视器”标签页中打开该监视器，以查看完整命令。",
    "{count, plural, one {# check failing} other {# checks failing}}": "{count, plural, one {# 项检查失败} other {# 项检查失败}}",
    "{count, plural, one {# more approval waiting} other {# more approvals waiting}}": "{count, plural, one {还有 # 项审批等待处理} other {还有 # 项审批等待处理}}",
    "{count, plural, one {# check still running} other {# checks still running}}": "{count, plural, one {# 项检查仍在运行} other {# 项检查仍在运行}}",
    "{repoCount, plural, =0 {No repositories} one {# repository} other {# repositories}}": "{repoCount, plural, =0 {无仓库} one {# 个仓库} other {# 个仓库}}",
    "{count, plural, one {# organization is} other {# organizations are}} hidden by SSO. Authorize the Claude app for those organizations on GitHub to see them here.": "{count, plural, one {# 个组织} other {# 个组织}}被 SSO 隐藏。请在 GitHub 上为这些组织授权 Claude App，以便在此处显示。",
    "{unplaceable, plural, one {# session} other {# sessions}} waiting for an idle runner": "{unplaceable, plural, one {# 个会话} other {# 个会话}}正在等待空闲运行器",
    "A credit purchase for your organization, started at {time}, is waiting on card verification from the bank. If it isn’t finished, it expires in {minutes, plural, one {# minute} other {# minutes}}. New purchases are blocked until then.": "你所在组织于 {time} 发起的用量额度购买正在等待银行验证付款卡。如果未完成，将在 {minutes, plural, one {# 分钟} other {# 分钟}}后过期。在此之前无法发起新购买。",
    "Your purchase from {time} is still processing. This usually takes a few seconds. If it doesn’t complete, you can try again in {minutes, plural, one {# minute} other {# minutes}}.": "你在 {time} 发起的购买仍在处理中，通常只需几秒。如果仍未完成，可在 {minutes, plural, one {# 分钟} other {# 分钟}}后重试。",
    "{count, plural, one {# Claude Tag} other {# Claude Tag}}": "{count, plural, one {# 个 Claude Tag} other {# 个 Claude Tag}}",
}

PLACEHOLDER_QUALITY_TRANSLATIONS = {
    "({change, number, ::sign-always})": "({change, number, ::sign-always})",
    "{low} – {high} / mo": "{low}–{high} / 月",
    "You’ve hit your {period, select, daily {daily } weekly {weekly } monthly {monthly } other {}}spend limit and you’re out of credits.": "你已达到{period, select, daily {每日} weekly {每周} monthly {每月} other {}}支出上限，且用量额度已用完。",
    "{name} used in <places>{count, plural, one {# place} other {# places}}</places>": "{name} 已在 <places>{count, plural, one {# 个位置} other {# 个位置}}</places> 中使用",
    "+{added}": "+{added}",
    "Delete secret “{name}”": "删除密钥“{name}”",
    "from {plugin} plugin": "来自 {plugin} 插件",
    "{roleList} have different permission levels for this connector. Members assigned to multiple of these roles get the more permissive level.": "{roleList} 对此连接器具有不同的权限级别。被分配多个角色的成员将获得权限更高的级别。",
    "{action}: {audience}": "{action}：{audience}",
    "Copy {file}": "复制 {file}",
    "Remove {domain}": "移除 {domain}",
    "Page {page} of {total}": "第 {page} 页，共 {total} 页",
    "weekly {model} limit": "每周 {model} 限额",
    "{state} for {tool}": "{tool}：{state}",
    "Something went wrong. Try again in a moment. If it persists, check {statusUrl}.": "出现问题，请稍后重试。如果问题持续，请查看 {statusUrl}。",
    "Allow {modelName} for the organization": "允许组织使用 {modelName}",
    "{count, number} / {limit, number}": "{count, number} / {limit, number}",
    "{category}: {actions}": "{category}：{actions}",
    "{date} at {approx, select, yes {~} other {}}{time}": "{date} {approx, select, yes {约} other {}}{time}",
    "Deleted “{name}”": "已删除“{name}”",
    "{name} won’t be enabled": "{name} 将不会启用",
    "That looks like {kind, select, anthropic_api_key {an Anthropic API key} openai_style_key {an API key} stripe_key {a Stripe API key} github_token {a GitHub token} gitlab_token {a GitLab token} slack_token {a Slack token} aws_access_key {an AWS access key} google_api_key {a Google API key} google_oauth_secret {a Google OAuth client secret} bearer_header {an Authorization header} private_key {a private key} other {a secret}}, not a client ID. Did you mean to paste this into Client Secret below?": "这看起来像{kind, select, anthropic_api_key {Anthropic API 密钥} openai_style_key {API 密钥} stripe_key {Stripe API 密钥} github_token {GitHub token} gitlab_token {GitLab token} slack_token {Slack token} aws_access_key {AWS 访问密钥} google_api_key {Google API 密钥} google_oauth_secret {Google OAuth 客户端密钥} bearer_header {Authorization 请求头} private_key {私钥} other {密钥}}，不是客户端 ID。你是不是想把它粘贴到下方的“客户端密钥”中？",
    "{filename} · covers {juris} · expires {date}": "{filename} · 覆盖 {juris} · 到期日 {date}",
    "/{skill} isn’t available in {surface, select, chat {Chat} cowork {Cowork} other {this mode}}": "/{skill} 在 {surface, select, chat {Chat} cowork {Cowork} other {此模式}} 中不可用",
    "{model} · {effort}": "{model} · {effort}",
    "{model} for {products}": "{model}（适用于 {products}）",
    "{granularity, select, weekly {Weekly} other {Daily}} spend by {groupBy, select, model_tier {model} other {product}}": "{granularity, select, weekly {每周} other {每日}}用量，按{groupBy, select, model_tier {模型} other {产品}}统计",
    "{approx, select, yes {~} other {}}{schedule}": "{approx, select, yes {约} other {}}{schedule}",
    "Delete {name}": "删除 {name}",
    "{kind, select, tasks {Search tasks...} chats {Search chats...} other {Search chats and tasks...}}": "{kind, select, tasks {搜索任务...} chats {搜索聊天...} other {搜索聊天和任务...}}",
    "Failed to {action} “{connectorName}”. You can try again.": "无法{action}“{connectorName}”，请重试。",
    "{progress}%": "{progress}%",
    "Use Claude Design to {task}": "使用 Claude Design 来{task}",
    "<name>{orgLabel}</name>: {changes}": "<name>{orgLabel}</name>：{changes}",
    "1-token completion in {ms} ms{model, select, none {} other { ({modelCode})}}{sourceLabel, select, undefined {} other { · via {sourceLabel}}}": "1-token 补全耗时 {ms} 毫秒{model, select, none {} other {（{modelCode}）}}{sourceLabel, select, undefined {} other { · 通过 {sourceLabel}}}",
    "{name} is connected": "{name} 已连接",
    "by {author} · {plugin} plugin": "由 {author} 提供 · {plugin} 插件",
    "Delete “{name}”": "删除“{name}”",
    "{open, select, true {Collapse} other {Expand}} {section} section": "{open, select, true {收起} other {展开}} {section} 部分",
    "From {source}": "来自 {source}",
    "HTTP {status}": "HTTP {status}",
    "{announcement}. {extra}": "{announcement}。{extra}",
    "Download {name}": "下载 {name}",
    "Add channel to {name}": "将频道添加到 {name}",
    "{action}, from {origin}": "{action}，来自 {origin}",
    "{kind, select, tasks {Tasks} chats {Chats} other {Chats and tasks}}": "{kind, select, tasks {任务} chats {聊天} other {聊天和任务}}",
    "{current}/{max}": "{current}/{max}",
    "Message from {name}": "来自 {name} 的消息",
    "{rate} × {seats}": "{rate} × {seats}",
    "Permission request: {action}": "权限请求：{action}",
    "Allow Claude to change files in “{directory}”?": "允许 Claude 修改“{directory}”中的文件吗？",
    "{count, plural, one {{roleNames} uses this model as its default. Change that role’s default model first.} other {{roleNames} use this model as their default. Change the default model for each role first.}}": "{count, plural, one {{roleNames} 将此模型设为默认模型。请先重新启用该角色的默认模型。} other {{roleNames} 将此模型设为默认模型。请先为每个角色更改默认模型。}}",
    "{label} · {status}": "{label} · {status}",
    "Keep {currentModeLabel}": "保留 {currentModeLabel}",
    "{title} {action}": "{title} {action}",
    "{name} added for your team": "已为你的团队添加 {name}",
    "Preview {name}": "预览 {name}",
    "Reading {file}": "正在读取 {file}",
    "Connected to “{name}”.": "已连接到“{name}”。",
    " ({defaultsByProduct})": "（{defaultsByProduct}）",
    "{count, plural, one {# item} other {# items}} {action, select, archive {archived} unarchive {unarchived} delete {deleted} other {}}": "{count, plural, one {# 项} other {# 项}} {action, select, archive {已归档} unarchive {已取消归档} delete {已删除} other {}}",
    "{control}: {selection}": "{control}：{selection}",
    "{name} access": "{name} 的访问权限",
    "Delete {name}?": "删除 {name}？",
    "{expanded, select, true {Hide} other {Show}} chats for {name}": "{expanded, select, true {隐藏} other {显示}} {name} 的聊天",
    "Edit {period, select, daily {daily} weekly {weekly} other {monthly}} spend limit for {name}": "编辑 {name} 的{period, select, daily {每日} weekly {每周} other {每月}}支出上限",
    "{status} · {ref}": "{status} · {ref}",
    "{count}/{max}": "{count}/{max}",
    "Actions for {name}": "{name} 的操作",
    "by {source}": "由 {source} 提供",
    "Start on {host}": "在 {host} 上开始",
    "Enter the details below to connect Claude to {server}.": "填写下方信息，将 Claude 连接到 {server}。",
    "Connecting to {name}…": "正在连接到 {name}…",
    "{count, plural, one {# more match} other {# more matches}} in {section}": "{count, plural, one {# 个匹配项} other {# 个匹配项}}（位于 {section}）",
    "−{removed}": "−{removed}",
    "{count, plural, one {{roleNames} inherits this model as its default. Turn it back on, or change the organization default.} other {{roleNames} inherit this model as their default. Turn it back on, or change the organization default.}}": "{count, plural, one {{roleNames} 将此模型设为默认模型。请重新启用该设置，或更改组织默认模型。} other {{roleNames} 将此模型设为默认模型。请重新启用该设置，或更改组织默认模型。}}",
    "Connect {server}": "连接 {server}",
    "{fullName} ({email})": "{fullName}（{email}）",
    "{pct} of your {model} limit": "{pct} 占 {model} 限额",
    "Visibility for {name}": "{name} 的可见性",
    "{hostname} · Opened in Browser": "{hostname} · 已在浏览器中打开",
    "Added {name}": "已添加 {name}",
    "{low}–{high} × {seats}": "{low}–{high} × {seats}",
    "{count, plural, one {{modelNames} is disabled. Choose an enabled model.} other {{modelNames} are disabled. Choose an enabled model.}}": "{count, plural, one {{modelNames} 已停用。请选择已启用的模型。} other {{modelNames} 已停用。请选择已启用的模型。}}",
    "Open folder {name}": "打开文件夹 {name}",
    "{count} × {name}": "{count} × {name}",
    "Archive “{name}”": "归档“{name}”",
    "{period, select, daily {daily} weekly {weekly} other {monthly}}": "{period, select, daily {每日} weekly {每周} other {每月}}",
    "Connected to {name}": "{name} 已连接",
    "Edit {period, select, daily {daily} weekly {weekly} other {monthly}} spend limit for {name}, currently {amount}": "编辑 {name} 的{period, select, daily {每日} weekly {每周} other {每月}}支出上限，当前为 {amount}",
    "{names} need additional consent. Finish setting them up in connector settings.": "{names} 需要额外同意。请在连接器设置中完成设置。",
    "{row} in {section}": "{row}（位于 {section}）",
}

SHORT_UI_TRANSLATIONS = {
    "See reviews on GitHub": "在 GitHub 上查看评论",
    "Sort A to Z": "按字母升序排序",
    "Claude was interrupted when your computer went to sleep.": "电脑进入睡眠状态时，Claude 的任务被中断。",
    "Let Claude use it": "让 Claude 使用它",
    "Setup · tailored to you": "设置 · 为你量身定制",
    "Couldn’t load this channel. Try again.": "无法加载此频道，请重试。",
    "Copy report": "复制报告",
    "Install Claude Code GitHub App": "安装 Claude Code GitHub App",
    "Environment archived": "环境已存档",
    "Filter usage by product": "按产品筛选用量",
    "Pick a task": "选择任务",
    "Review pending permissions for {login} on GitHub": "在 GitHub 上审核 {login} 的待处理权限",
    "url": "URL",
    "Search by name or email": "按姓名或邮箱搜索",
    "waiting for {dur}": "已等待 {dur}",
    "Pick something to start": "选择一项开始",
    "Start a side chat": "发起侧聊",
    "Research a topic and draft a doc": "研究一个主题并起草文档",
    "Quiet morning. The afternoon is loaded.": "上午比较清闲，下午安排得很满。",
    "Couldn’t rename environment. Try again.": "环境重命名失败，请重试。",
    "Includes Claude Code and Claude Cowork": "包含 Claude Code 和 Claude Cowork",
    "Memories": "记忆",
    "Claude pressed a device button": "Claude 按下了设备按钮",
    "Used by": "使用方",
    "{used} of {cap} used": "已使用 {used} / {cap}",
    "Sharing with Anthropic support disabled": "已禁止与 Anthropic 支持团队共享",
    "Lines changed": "更改行数",
    "Run - {time}": "运行时间：{time}",
    "deal-desk-helper": "交易审批助手",
    "open a file outside your project folder": "打开项目文件夹外的文件",
    "Can’t determine which sandbox holds this file.": "无法确定此文件位于哪个沙箱中。",
    "Reviewing chat details": "正在查看聊天详情",
    "Removed {name}": "已移除 {name}",
    "Weekdays at {time} ({timezone}).": "工作日 {time}（{timezone}）",
    "no data": "暂无数据",
    "Couldn’t retry session. Try again.": "重试会话失败，请再试一次。",
    "Seat limits stall upgrades — named in 27 of 41 calls": "席位限制阻碍升级，41 次通话中有 27 次提到这一点",
    "Drafts in your voice": "以你的语气生成草稿",
    "Trending feature requests": "热门功能请求",
    "Anthropic-hosted environments": "Anthropic 托管环境",
    "Send a message to see context usage.": "发送消息后即可查看上下文用量。",
    "Set by this connection and can’t be changed.": "由此连接设置，无法更改。",
    "Onboard": "接入",
    "Granted credits": "已授予额度",
    "Retention period for private artifacts": "私有工件的保留期限",
    "Updated project settings": "项目设置已更新",
    "1 PM onward": "下午 1 点后",
    "Recording stopped unexpectedly. Start again to resume.": "录音意外停止。请重新开始以继续录音。",
    "Previous tasks": "以往任务",
    "Credit balance": "用量额度余额",
    "star": "加星",
    "What is the compartment ID used for?": "隔离区 ID 有什么用途？",
    "Research a topic and create a presentation": "研究一个主题并制作演示文稿",
    "Already in this group": "已在此组中",
    "Syncing from GitHub…": "正在从 GitHub 同步…",
    "You can use this emulator yourself, but Claude can’t.": "你可以自行使用此模拟器，但 Claude 无法使用。",
    "You have an unsubmitted review on GitHub": "你在 GitHub 上有一条尚未提交的评审",
    "Enable sharing with Anthropic support": "启用与 Anthropic 支持团队共享",
    "Couldn’t load runners. Try again later.": "无法加载运行器，请稍后重试。",
    "Active runners": "活跃运行器",
    "Failed to update network settings": "更新网络设置失败",
    "Fork “{name}”": "派生“{name}”",
    "{amount} credits/mo allowance": "每月 {amount} 用量额度",
    "Sign off usage pricing — board reads Thu": "确认用量定价，董事会将于周四审阅",
    "Trending connectors": "热门连接器",
    "{count} needed no change": "其中 {count} 项无需更改",
    "Per-platform overrides": "各平台覆盖设置",
    "Continuing…": "正在继续…",
    "Staged": "已暂存",
    "Claude is using this device": "Claude 正在使用此设备",
    "Authorize SSO": "授权 SSO",
    "Complete cancellation": "完成取消",
    "Project ID copied to clipboard.": "项目 ID 已复制到剪贴板。",
    "Keep annual plan": "保留年度方案",
    "Waiting on you": "等待你的操作",
    "Undo removing {name}": "撤销移除 {name}",
    "No channels in this workspace for this period.": "在此期间，此工作区没有频道。",
    "Custom tool": "自定义工具",
    "booting": "正在启动",
    "path/to/file.md": "path/to/file.md",
    "Remove member?": "移除成员？",
    "Answer the approval above to continue": "请处理上方的批准请求以继续",
    "Allow direct messages with Claude": "允许与 Claude 私信",
    "Xcode installed": "Xcode 已安装",
    "shutting down": "正在关闭",
    "$148k": "$148k",
    "Slack user": "Slack 用户",
    "Open Android Studio": "打开 Android Studio",
    "Saving restarts the conversation from here.": "保存后，对话将从此处重新开始。",
    "Failed to disconnect the GitHub installation.": "断开 GitHub 安装连接失败。",
    "Block mobile simulator tools": "阻止移动端模拟器工具",
    "Nothing needs your review right now": "目前没有需要你审核的内容",
    "Client assertion audience (optional)": "客户端断言的受众（可选）",
    "Total cost": "总费用",
    "Record a skill": "录制技能",
    "Claude in GitHub App": "GitHub App 中的 Claude",
    "Checking for a system image…": "正在检查系统映像…",
    "Start your day with a daily briefing": "用每日简报开启一天",
    "Checking the selected Xcode…": "正在检查所选 Xcode…",
    "Install the Claude Code GitHub App": "安装 Claude Code GitHub App",
    "{count} fixed": "已修复 {count} 项",
    "Or run it where you already work:": "也可以在你现有的工作环境中运行：",
    "Price the Acme renewal": "为 Acme 的续约定价",
    "No session usage yet": "暂无会话用量",
    "Couldn’t save environment. Try again.": "保存环境失败，请重试。",
    "10 AM – 1 PM": "上午 10 点至下午 1 点",
    "Android SDK installed": "Android SDK 已安装",
    "Make this artifact public?": "将此工件设为公开？",
    "Failed sessions": "失败会话",
    "Attach a simulator so Claude can see your app": "连接模拟器，让 Claude 查看你的应用",
    "Loading routine": "正在加载例程",
    "Projects moved": "项目已移动",
    "Not connected via remote control. <link>Learn more</link>": "未通过远程控制连接。<link>了解更多</link>",
    "Draining": "正在清空任务",
    "Searching connector directory…": "正在搜索连接器目录…",
    "Couldn’t save this skill. Try again.": "保存此技能失败，请重试。",
    "Show session details": "显示会话详情",
    "Slack channel link or ID": "Slack 频道链接或 ID",
    "Synced from GitHub (some installations skipped)": "已从 GitHub 同步（部分安装已跳过）",
    "In this project": "此项目中",
    "Archive this environment?": "要归档此环境吗？",
    "Couldn’t switch to that device. You can try again.": "无法切换到该设备，请重试。",
    "Runner actions": "运行器操作",
    "e.g. a launch or project to track": "例如要跟踪的发布或项目",
    "Binaries ({count})": "二进制文件（{count}）",
    "Cloud sharing": "云共享",
    "Added {slug} to project permissions": "已将 {slug} 添加到项目权限",
    "Make public": "设为公开",
    "Add a folder": "添加文件夹",
    "Usage pricing: the case": "用量定价：商业案例",
    "Interesting product design launches": "值得关注的产品设计发布",
    "The Claude app was uninstalled on GitHub for {login}.": "GitHub 上 {login} 的 Claude App 已卸载。",
    "duplicate": "重复",
    "Defaults for new sessions started in this project.": "此项目中新会话的默认设置。",
    "All runner slots are in use.": "所有运行器槽位都在使用中。",
    "Claude Tag": "Claude Tag",
    "Bring two or three thoughts to the retro": "把两三个想法带到复盘会上",
    "Claude pressed Apple Pay": "Claude 按下了 Apple Pay",
    "Not available for Ants": "不适用于 Ants",
    "About the promotional credit balance": "关于促销额度余额",
    "Changes at your next billing date": "下一个账单日的更改",
    "Claude pressed Back": "Claude 按下了返回键",
    "{input} in · {output} out": "输入 {input} · 输出 {output}",
    "Switch to Pro monthly": "切换到 Pro 月度方案",
    "Versions couldn’t be loaded. Close and try again.": "无法加载版本。请关闭后重试。",
    "No other organizations available to link.": "没有其他可关联的组织。",
    "No connected accounts": "没有已连接的账号",
    "Couldn’t archive environment. Try again.": "无法归档环境，请重试。",
    "{count} passed": "已通过 {count} 项",
    "Weekly credit budget": "每周用量额度预算",
    "Synced from GitHub just now": "刚刚已从 GitHub 同步",
    "Output truncated": "输出已截断",
    "Checking what’s loaded into this chat…": "正在检查此聊天中加载的内容…",
    "Send to side chat": "发送到侧聊",
    "Couldn’t narrow down what triggered this.": "无法确定触发原因。",
    "{count} idle": "{count} 个空闲",
    "Code changes": "代码更改",
    "{amount} left": "剩余 {amount}",
    "Schedule brief": "日程摘要",
    "Members now get {version}.": "成员现已获得 {version}。",
    "{wall} wall · {api} API": "{wall} 实际用时 · {api} API",
    "Draft · in your voice": "草稿 · 以你的语气",
    "Onboarding mock": "入门演示",
    "Start a task": "开始任务",
    "Re-approve emulator access": "重新批准模拟器访问权限",
    "Settings default": "默认设置",
    "No idle runners": "没有空闲运行器",
    "Deals that have gone quiet": "暂无进展的交易",
    "All products/models": "所有产品/模型",
    "Add a folder — {project}": "添加文件夹 — {project}",
    "Archive coordinator": "归档协调器",
    "$84k": "$84k",
    "New sessions": "新会话",
    "This folder isn’t a git repository": "该文件夹不是 Git 仓库",
    "Claude takes on tasks and keeps the project organized": "Claude 会接手任务并整理项目",
    "Pro monthly · {price}/month": "Pro 月度方案 · {price}/月",
    "Claude’s Android Emulator tools are turned off.": "Claude 的 Android 模拟器工具已关闭。",
    "Let Claude use this emulator?": "让 Claude 使用此模拟器？",
    "Give Claude a task to run autonomously": "给 Claude 一项任务，让它自主运行",
    "Run this in your terminal to use Claude Code": "在终端运行此命令即可使用 Claude Code",
    "Competitor teardown": "竞品拆解",
    "Export traces (beta)": "导出跟踪数据（测试版）",
    "Allow your organization to code with Claude on the web.": "允许你的组织在 Web 端使用 Claude 编程。",
    "Environment keys": "环境密钥",
    "See all {count, number} skills": "查看全部 {count, number} 项技能",
    "{price}/month — changes at your next billing date": "{price}/月 — 下一个账单日生效变更",
    "members": "成员",
    "Recording is already running on another device.": "另一台设备上已在录音。",
    "Let Claude use this simulator?": "让 Claude 使用此模拟器？",
    "Unlink from this workspace": "取消与此工作区的关联",
    "Write tomorrow’s briefing": "撰写明日简报",
    "Unlinked accounts": "未关联的账号",
    "No command is declared for this monitor.": "此监视器未声明任何命令。",
    "Ability to use more Claude models": "使用更多 Claude 模型的能力",
    "Turn on computer use in Settings, then try recording again.": "在设置中开启电脑控制，然后再次尝试录制。",
    "{count} failing": "{count} 个失败",
    "Watch checks": "查看检查项",
    "usage": "用量",
    "Remove from sidebar": "从侧边栏移除",
    "Plugin created.": "插件已创建。",
    "You can start with as few as {minimumSeats}.": "最少从 {minimumSeats} 个席位开始。",
    "Clawd the crab": "螃蟹 Clawd",
    "Includes Claude Science": "包含 Claude Science",
    "Includes Claude Cowork": "包含 Claude Cowork",
    "took {elapsed}": "耗时 {elapsed}",
    "Claude needs your approval": "Claude 需要你的批准",
    "Synced from GitHub {time}": "已于 {time} 从 GitHub 同步",
    "Claude is typing": "Claude 正在输入",
    "This message has attachments that can’t return to the input.": "此消息包含无法返回输入框的附件。",
    "Failed to add repository": "添加仓库失败",
    "Interview scorecard due before the 1:40 panel": "面试评分表需在 1:40 的面试小组前提交",
    "Purchased credits": "已购买的用量额度",
    "Claude’s iOS Simulator tools are turned off.": "Claude 的 iOS 模拟器工具已关闭。",
    "Key ID": "密钥 ID",
    "$7.8k/mo": "$7.8k/月",
    "Changes apply to new sessions started in this environment.": "更改将应用于此环境中新启动的会话。",
    "Teach Claude your voice": "教 Claude 识别你的声音",
    "{planName} plan": "{planName} 方案",
    "Failed runners": "失败的运行器",
    "Design feedback waiting on you": "设计反馈正在等待你的处理",
    "Connected GitHub accounts": "已连接的 GitHub 账号",
    "Open it on Claude": "改为在 Claude 中打开",
    "Weekly credit budget in US dollars": "每周用量额度预算（美元）",
    "Applies to this project’s coordinator session.": "适用于该项目的协调器会话。",
    "left": "剩余",
    "As of {date} (UTC). Data has a one-day delay.": "截至 {date}（UTC）。数据延迟一天。",
    "Discard this draft?": "要放弃此草稿吗？",
    "Connected via remote control. <link>Learn more</link>": "已通过远程控制连接。<link>了解更多</link>",
    "Also include default list of common package managers": "同时包含常用包管理器的默认列表",
    "Promotional credit": "促销额度",
    "The status of your open PRs and review requests": "你的未关闭 PR 和评审请求的状态",
    "{projectName}, View-only access": "{projectName}，仅限查看",
    "Mix and match seat types": "混合使用不同席位类型",
    "Disable Claude Code on the web?": "要在 Web 端禁用 Claude Code 吗？",
    "Available on Team and Enterprise plans.": "适用于 Team 和 Enterprise 方案。",
    "Virtual device created": "已创建虚拟设备",
    "Holiday. The afternoon is yours.": "假期。下午由你自由安排。",
    "Download Android Studio": "下载 Android Studio",
    "Board deck": "董事会演示文稿",
    "Synthesise 41 customer calls": "汇总 41 次客户通话",
    "An image couldn’t be read. Start a new session to continue.": "无法读取图像。请开始新会话以继续。",
    "Ranked by accounts that attempted to connect (30d)": "按尝试连接的账号排名（30 天）",
    "Manage members": "管理成员",
    "Client health": "客户端健康状况",
    "OAuth discovery overrides": "OAuth 发现覆盖项",
    "Tokens per week": "每周令牌数",
    "Top sessions by usage": "按用量排序的热门会话",
    "Install a system image": "安装系统映像",
    "Last updated {time}. Send a message to refresh.": "上次更新于 {time}。发送消息以刷新。",
    "Claude can use the iOS Simulator": "Claude 可以使用 iOS 模拟器",
    "Sources in this chat’s context are triggering safety flags.": "此聊天上下文中的来源触发了安全标记。",
    "Temporary error. Try syncing again.": "出现临时错误，请重新同步。",
    "Every session, from session start": "每个会话：从会话开始时",
    "Consumer health": "消费者业务健康度",
    "Live stream of {deviceName} emulator": "{deviceName} 模拟器实时画面",
    "Outcomes reported": "已报告结果",
    "Automatically buy more usage when your balance is low": "余额不足时自动购买更多用量额度",
    "An attachment is too large. Start a new session to continue.": "附件过大。请新建会话以继续。",
    "Attach an emulator so Claude can see your app": "连接模拟器，让 Claude 查看你的应用",
    "Q3: $18.2M, 6% under": "第三季度：1820 万美元，低于目标 6%",
    "Draft the Q3 board deck": "起草 Q3 董事会演示文稿",
    "Output tokens": "输出令牌",
    "Keep Max, just smaller · {price}/month": "继续使用 Max，降低用量额度 · {price}/月",
    "Tokens per day": "每日令牌数",
    "Monitor {number}": "监视器 {number}",
    "% of project": "项目占比",
    "Fast mode respects spend limits set.": "快速模式遵循已设置的支出上限。",
    "One last step to cancel": "再完成一步即可取消",
    "What needs your attention": "需要你处理的事项",
    "Session ID": "会话 ID",
    "Couldn’t update quick setup. Try again.": "更新快速设置失败，请重试。",
    "Show session usage": "查看会话用量",
    "e.g. Engineering": "例如：工程部门",
    "Hand off entire tasks to Cowork": "将整项任务交给 Cowork",
    "Learn more about Claude Code": "了解 Claude Code",
    "Homespaces": "个人空间",
    "A reviewer requested changes": "评审者请求更改",
    "Remove {name}?": "要移除 {name} 吗？",
    "View sent prompt": "查看已发送的提示词",
    "Quick one before Monday — here’s where we landed.": "周一前快速同步一下，这是目前的进展。",
    "Failed to turn off Claude Security. You can try again.": "关闭 Claude Security 失败，请重试。",
    "Connect Claude to GitHub": "将 Claude 连接到 GitHub",
    "Message couldn’t be sent. Try again.": "消息发送失败，请重试。",
    "Refills {date}": "将于 {date} 补充额度",
    "Speaker notes drafted · sources linked per slide": "演讲者备注已起草 · 每页幻灯片均已关联来源",
    "Try Claude Code for GitHub": "试用 GitHub 中的 Claude Code",
    "Sync, weekly, vendor check-in run back to back.": "同步会、周会和供应商沟通会接连进行。",
    "Couldn’t load usage": "无法加载用量",
    "Reviews": "评审",
    "Or switch to a cheaper plan": "或切换为更便宜的方案",
    "{deviceName} is {deviceState}. Boot it before attaching.": "{deviceName} 当前状态为 {deviceState}。请先启动再连接。",
    "If trying again doesn’t work, <link>contact support</link>.": "如果重试后仍未解决，请<link>联系支持团队</link>。",
    "Starting up document tools…": "正在启动文档工具…",
    "Keep Max, just smaller": "继续使用 Max，降低用量额度",
    "Deployment display subtitle": "部署显示副标题",
    "Haiku isn’t recommended as a default.": "不建议将 Haiku 设为默认模型。",
    "Copy compartment ID": "复制隔离区 ID",
    "Where this connection is used": "此连接的使用位置",
    "In use by": "使用方",
    "Make current": "设为当前版本",
    "Tools connected": "已连接的工具",
    "No emulators found. Create one in Android Studio": "未找到模拟器。请在 Android Studio 中创建一个",
    "Claude pressed Lock": "Claude 按下了锁定键",
    "Archive {name}?": "归档 {name}？",
    "End-user attribution": "终端用户归因",
    "What this plugin helps with": "此插件的用途",
    "Here are a few repositories you can add to this project:": "以下是可添加到此项目的几个仓库：",
    "Compartment ID": "隔离区 ID",
    "Production": "生产环境",
    "Free from the Mac App Store.": "可从 Mac App Store 免费获取。",
    "This check isn’t available right now.": "此检查当前不可用。",
    "Detach emulator": "断开模拟器连接",
    "Don’t ask": "不再询问",
    "{names} requested changes": "{names} 请求了更改",
    "Couldn’t remove the member": "无法移除该成员",
    "Unlink {login} from this workspace?": "取消 {login} 与此工作区的关联？",
    "Tool call users (30d)": "工具调用用户（近 30 天）",
    "Editing earlier messages isn’t available in this chat": "此聊天不支持编辑早先的消息",
    "Coordinator": "协调器",
    "Loading skill files…": "正在加载技能文件…",
    "No simulators found. Install one in Xcode": "未找到模拟器。请在 Xcode 中安装一个",
    "yes": "是",
    "Deny actions that aren’t pre-approved, without prompting": "直接拒绝未经预先批准的操作，不再询问",
    "Checking your simulator setup…": "正在检查模拟器配置…",
    "Couldn’t change sharing. Try again in a moment.": "更改共享设置失败，请稍后重试。",
    "No monitors match your search": "没有与搜索条件匹配的监视器",
    "24-month locks a 12% discount — ready to send before Friday": "锁定 24 个月可享 12% 折扣，周五前即可发出",
    "Your changes haven’t been saved and will be lost.": "未保存的更改将会丢失。",
    "Claude didn’t stop. You can try again.": "Claude 未能停止，请重试。",
    "Admins set user and org spend limits": "管理员设置用户和组织支出上限",
    "Customize Cowork for your role": "根据你的岗位定制 Cowork",
    "Claude pressed the side button": "Claude 按下了侧边按钮",
    "additional grant types": "其他授权类型",
    "Quick setup enabled": "快速设置已启用",
    "Updating project settings": "正在更新项目设置",
    "Device tools changed on disk": "磁盘中的设备工具已更改",
    "Failed to unpublish the version.": "取消发布版本失败。",
    "Show previous suggestion": "查看上一条建议",
    "Promotional credit usage": "促销额度用量",
    "Speaker {n}": "发言人 {n}",
    "Couldn’t toggle Remote Control. Try again.": "切换远程控制失败，请重试。",
    "Claude Code artifacts": "Claude Code 工件",
    "Set model for {count}": "为 {count} 个会话设置模型",
    "Profile instructions": "个人偏好指令",
    "Claude pressed Recents": "Claude 按下了最近任务键",
    "24-month": "24 个月",
    "Chat and Cowork have a new home": "Chat 和 Cowork 有了新入口",
    "Link organizations you own": "关联你拥有的组织",
    "Toggle chats for {name}": "展开或收起 {name} 的聊天",
    "Exit full screen to answer the pending approval first": "请先退出全屏模式，处理待审批请求",
    "Checking for the Android SDK…": "正在检查 Android SDK…",
    "Routine settings": "例程设置",
    "You’ll need to be an owner of the GitHub account to connect.": "你需要拥有该 GitHub 账号才能连接。",
    "Manage on GitHub": "在 GitHub 上管理",
    "Loading chart data": "正在加载图表数据",
    "Install the Claude Code GitHub App to connect your codebases": "安装 Claude Code GitHub App 以连接代码库",
    "Continue to GitHub sync": "继续同步 GitHub",
    "The installation for {login} is suspended on GitHub.": "GitHub 上 {login} 的安装已被暂停。",
    "Admin settings": "管理员设置",
    "See failing checks": "查看失败的检查项",
    "Mobile access currently follows your Web setting.": "移动端访问权限当前沿用 Web 端设置。",
    "Workspace ID": "工作区 ID",
    "Annotate image": "标注图片",
    "Claude Security (beta)": "Claude Security（测试版）",
    "Connect your GitHub to see more organizations you can link.": "连接 GitHub 以查看更多可关联的组织。",
    "{from}–{to} of {total}": "{from}–{to}，共 {total} 项",
    "Notable signups or churn": "重要的新增注册或客户流失情况",
    "Show all {count}": "显示全部 {count} 项",
    "managed authentication settings": "托管身份验证设置",
    "System image installed": "系统映像已安装",
    "Open the run to see what happened.": "打开本次运行以查看详情。",
    "Install Xcode": "安装 Xcode",
    "Key saved — it won’t be shown again.": "密钥已保存，之后不会再次显示。",
    "Saved tool selection — not active until connected": "工具选择已保存，连接后才会生效",
    "No usage yet": "暂无用量",
    "Ready for your week": "为新一周做好准备",
    "Claude needs your permission to use {deviceName}.": "Claude 需要你的许可才能使用 {deviceName}。",
    "Raw": "原始",
    "Monthly active users": "月活跃用户数",
    "41 calls · Apr–Jun · 12 accounts": "41 次通话 · 4 月至 6 月 · 12 个账号",
    "12-month": "12 个月",
    "Enable the GitHub integration to link more organizations.": "启用 GitHub 集成以关联更多组织。",
    "Cancel without answering": "取消且不作答",
    "Native binary": "原生二进制文件",
    "Pin projects to keep them here": "固定项目，使其保留在此处",
    "Paying for more than you need?": "正在为超出需求的部分付费？",
    "Unsaved edits — will save when Claude finishes": "编辑内容尚未保存，Claude 完成后将自动保存",
    "Available once a system image is installed.": "安装系统映像后即可使用。",
    "Attach aborted by concurrent detach.": "同时执行了断开操作，连接已中止。",
    "See all {count, number}": "查看全部 {count, number} 项",
    "Unsaved edits — will apply when Claude finishes": "编辑内容尚未保存，Claude 完成后将应用",
    "Checking your Android setup…": "正在检查 Android 配置…",
    "Environment ID": "环境 ID",
    "Sharing with Anthropic support enabled": "已启用与 Anthropic 支持团队共享",
    "Claude pressed Home": "Claude 按下了主屏幕键",
    "opened this pull request": "打开了此拉取请求",
    "Failed to change the current version.": "更改当前版本失败。",
    "Couldn’t update sharing with Anthropic support. Try again.": "更新与 Anthropic 支持团队的共享设置失败，请重试。",
    "Q3 board · 24 slides · draft 2": "Q3 董事会材料 · 24 张幻灯片 · 第 2 版草稿",
    "Sharing controls aren’t available for this artifact.": "此工件不支持共享控制。",
    "To make this artifact public, open it and use Share.": "要公开此工件，请打开工件并使用“共享”。",
    "Distinct accounts that called at least one tool": "至少调用过一种工具的不同账号数",
    "{yColumn} by {xColumn}": "按 {xColumn} 显示 {yColumn}",
    "Copy link to “{name}”": "复制“{name}”的链接",
    "From the {skillName} skill — runs when that skill is used.": "来自 {skillName} 技能，使用该技能时运行。",
    "Install on another organization": "在其他组织中安装",
    "{name}, quiet morning. The afternoon is loaded.": "{name}，上午比较清闲，下午安排得很满。",
    "Help me fix it": "帮我修复",
    "Type {name} to confirm": "输入 {name} 以确认",
    "Mobile simulators": "移动端模拟器",
    "Tool output": "工具输出",
    "{version} unpublished.": "{version} 已取消发布。",
    "Access to unlimited projects to organize chats and documents": "可使用无限数量的项目来整理聊天和文档",
    "Copy environment ID": "复制环境 ID",
    "Your weekly limit across all models": "所有模型共用的每周限额",
    "Update Claude": "更新 Claude",
    "Three calls before ten. The holiday has the rest.": "上午十点前有三场通话，之后即可享受假期。",
    "No pull requests yet": "暂无拉取请求",
    "Claim credits": "领取用量额度",
    "Select Xcode": "选择 Xcode",
    "Why upgrades stall": "升级为何受阻",
    "Switch to Pro instead · {price}/month": "改用 Pro · {price}/月",
    "Connect at least one tool to continue": "至少连接一个工具以继续",
    "Copy message for your GitHub admin": "复制消息并发送给 GitHub 管理员",
    "Set up the iOS simulator": "设置 iOS 模拟器",
    "Regenerating responses isn’t available in this chat": "此聊天不支持重新生成回复",
    "Not linked": "未关联",
    "{name}, three calls before ten. The holiday has the rest.": "{name}，上午十点前有三场通话，之后即可享受假期。",
    "Android Studio installed": "Android Studio 已安装",
    "shut down": "已关机",
    "Sent prompt": "已发送的提示词",
    "Couldn’t load role permissions. Close and try again.": "无法加载角色权限，请关闭后重试。",
    "Not a GitHub account owner?": "你不是 GitHub 账号所有者？",
    "Artifact preview iframe": "工件预览 iframe",
    "Artifact preview iframe origin": "工件预览 iframe 来源",
    "Pin / unpin session": "固定或取消固定会话",
    "Deploy a runner with your environment key.": "使用环境密钥部署运行器。",
    "Save & turn on": "保存并开启",
    "Android SDK and emulator installed": "Android SDK 和模拟器已安装",
    "member": "成员",
    "Microphone access is blocked. Check browser permissions.": "麦克风访问被阻止，请检查浏览器权限。",
    "Adding repository": "正在添加仓库",
    "No runners": "没有运行器",
    "Checking for the simulator runtime…": "正在检查模拟器运行时…",
    "Everything stays. Only your usage allowance changes.": "其他内容保持不变，仅调整你的用量额度。",
    "Coordinator effort": "协调器推理强度",
    "Bash script that runs before each session starts.": "每次会话开始前运行的 Bash 脚本。",
    "Checking for a virtual device…": "正在检查虚拟设备…",
    "Create role": "创建角色",
    "favorite": "收藏",
    "Top connectors": "热门连接器",
    "Renews {date}": "将于 {date} 续订",
    "cycle": "周期",
    "Switch to monthly billing": "切换为月度计费",
    "Per-session usage breakdowns are coming soon.": "按会话查看用量明细的功能即将推出。",
    "Three open hours before the half-day starts.": "半天假期开始前还有三个小时的空闲时间。",
    "Anthropic-managed client credentials": "Anthropic 管理的客户端凭据",
    "Added repository to project permissions": "已将仓库添加到项目权限",
    "Couldn’t run security scan. Try syncing again.": "安全扫描失败，请重新同步。",
    "Go to thread": "前往会话",
    "I work in {role}.": "我的职位是 {role}。",
    "Monitors": "监视器",
    "Install Android Studio": "安装 Android Studio",
    "Claude in Chrome settings": "Chrome 设置中的 Claude",
    "Curated by Anthropic": "由 Anthropic 精选",
    "When Claude requests access to an app": "Claude 请求访问应用时",
    "Claude Tag channel setup": "Claude Tag 频道设置",
    "Cancel and edit message": "取消并编辑消息",
    "Still checking Cowork availability — try again in a moment.": "仍在检查 Cowork 可用性，请稍后重试。",
    "Use this code in your browser to finish signing in.": "在浏览器中输入此代码以完成登录。",
    "By model": "按模型",
    "Search sessions and runners": "搜索会话和运行器",
    "Why this chat was flagged": "此聊天被标记的原因",
    "Key ID (kid, optional)": "密钥 ID（kid，可选）",
    "Set different periods for chats, projects, and artifacts": "分别设置聊天、项目和工件的保留期限",
    "Close without granting permission": "关闭且不授予权限",
    "{multiplier}× usage allowance": "{multiplier}× 用量额度",
    "Couldn’t link that installation. Try again in a moment.": "无法关联该安装，请稍后重试。",
    "Retry without files": "不附带文件并重试",
    "Folders where Claude may work. Applies to both the Cowork and Code tabs. Leave unset for unrestricted access.": "Claude 可能使用的文件夹。适用于 Cowork 和 Code 两个标签页。留空表示不限制访问。",
    "Claude’s Android Emulator tools are turned off by your organization.": "你的组织已关闭 Claude 的 Android 模拟器工具。",
    "Send this message to someone who is. They’ll need to be an admin of this Claude workspace too.": "将此消息发送给具备该权限的人员。他们还需要是此 Claude 工作区的管理员。",
    "Claude will view this device’s screen through screenshots and control it by tapping and typing.": "Claude 会通过屏幕截图查看此设备的屏幕，并通过点按和输入进行控制。",
    "Couldn’t attach connectors to this task. Claude will retry automatically.": "无法将连接器附加到此任务。Claude 会自动重试。",
    "Claude can browse, click, and screenshot in this browser. Enter a URL above.": "Claude 可以在此浏览器中浏览、点击和截屏。请在上方输入 URL。",
    "The GitHub authorization was canceled or didn’t go through. You can try again, or pick up where you left off.": "GitHub 授权已取消或未完成。你可以重试，也可以从上次中断处继续。",
    "Claude gathers the sources and writes them up in a doc you can react to.": "Claude 会收集来源并整理成文档，供你查看和反馈。",
    "Claude will keep an updated summary of what’s happening across your project.": "Claude 会持续更新项目进展摘要。",
    "Give Claude a topic and get back a deck that’s researched, structured, and ready to send.": "给 Claude 一个主题，即可获得经过研究、结构清晰且可以直接发送的演示文稿。",
    "This file is outside your project folder. Anything shown in the preview is readable by Claude in this session.": "该文件位于项目文件夹之外。预览中显示的任何内容都可被 Claude 在此会话中读取。",
    "Tell Claude what you care about once, and you’ll get a fresh briefing every morning.": "只需告诉 Claude 你关心的内容，每天早上都会收到最新简报。",
    "The exact text Claude received for this message, shown verbatim.": "此消息中 Claude 收到的原始文本，按原样显示。",
    "You can use this simulator yourself, but Claude can’t.": "你可以自行使用此模拟器，但 Claude 无法使用。",
    "Includes Claude Code": "包含 Claude Code",
    "Claude’s iOS Simulator tools are turned off by your organization.": "你的组织已关闭 Claude 的 iOS 模拟器工具。",
    "Claude works in the background while you’re away: a morning brief, ready before you sit down.": "你离开时，Claude 会在后台工作，在你开始一天前准备好晨间简报。",
    "Anything on the screen, including notifications and other open apps, can end up in your conversation.": "屏幕上的任何内容（包括通知和其他打开的应用）都可能出现在你的对话中。",
    "Restart the app and try again.": "重启应用并重试。",
    "Claude will work in these apps in the background while you keep using your Mac.": "当你继续使用 Mac 时，Claude 会在后台操作这些应用。",
    "Git is installed, but your system blocked Claude from running it. This is usually an endpoint security or application control policy. Ask your IT team to allow Claude to run Git, or switch to a remote environment.": "Git 已安装，但系统阻止 Claude 运行它。这通常由终端安全或应用控制策略导致。请让 IT 团队允许 Claude 运行 Git，或切换到远程环境。",
    "It’s built for simple, repeatable tasks and everyday chat, not complex work or tools like Cowork, Claude Code, and Claude Design. Members can still choose a different model for any chat.": "它适合简单、可重复的任务和日常聊天，不适合复杂工作或 Cowork、Claude Code、Claude Design 等工具。成员仍可为任何聊天选择其他模型。",
    "This skill includes files beyond SKILL.md, which this app can’t save yet. Ask Claude to combine the skill into a single SKILL.md file.": "此技能包含 SKILL.md 之外的文件，当前应用还无法保存这些文件。请让 Claude 将技能合并到单个 SKILL.md 文件中。",
    "Switch to Pro": "切换到 Pro",
    "Git was found at {path}, but your system blocked Claude from running it. This is usually an endpoint security or application control policy. Ask your IT team to allow Claude to run Git, or switch to a remote environment.": "在 {path} 找到了 Git，但系统阻止 Claude 运行它。这通常由终端安全或应用控制策略导致。请让 IT 团队允许 Claude 运行 Git，或切换到远程环境。",
    "Use credits for usage past your plan limits and products with their own limits, like Claude Design. <link>Learn more</link>": "用量超出方案限额，或使用具有独立限额的产品（如 Claude Design）时，将消耗用量额度。<link>了解更多</link>",
    "Values the plugin’s author set as defaults. The Claude desktop app substitutes them into the command, arguments, and environment variables above when installing the plugin.": "插件作者设置的默认值。安装插件时，Claude 桌面应用会将这些值代入上方的命令、参数和环境变量。",
    "Connecting GitHub for your organization isn’t available in the desktop app. Open claude.ai in your web browser and connect from the GitHub page in admin settings.": "桌面应用暂不支持为组织连接 GitHub。请在浏览器中打开 claude.ai，然后前往管理员设置中的 GitHub 页面完成连接。",
    "Automatically keep plugins up to date when the repository changes on GitHub": "GitHub 上的仓库发生变化时，自动更新插件",
    "Keep plugins up to date when the repository changes on GitHub": "GitHub 上的仓库发生变化时，保持插件为最新版本",
    "Token usage on this device across Chat, Cowork, and Code. Costs aren’t shown — your organization is billed at its own provider rates.": "此设备上 Chat、Cowork 和 Code 的令牌用量。此处不显示费用；你的组织将按其提供商费率结算。",
    "You’ll be sent to GitHub to install the Claude app on an organization you own.": "系统将跳转到 GitHub，以便在你拥有的组织中安装 Claude App。",
    "Credits are used when you go past your plan limits, and for products with their own limits.": "用量超出方案限额，或使用具有独立限额的产品时，将消耗用量额度。",
    "Install the Claude Code GitHub App in your accounts to give Claude Tag, Claude Security, or Claude Code access to your codebases.": "在你的 GitHub 账号中安装 Claude Code GitHub App，让 Claude Tag、Claude Security 或 Claude Code 能够访问你的代码库。",
    "No GitHub App installation is connected to this organization.": "此组织尚未连接 GitHub App 安装。",
    "Routine saved, but the GitHub trigger couldn’t be updated — the Claude GitHub App isn’t installed on the repository. <link>Install the GitHub App</link>, then edit again to retry.": "例程已保存，但无法更新 GitHub 触发器：该仓库尚未安装 Claude GitHub App。请先<link>安装 GitHub App</link>，再编辑例程以重试。",
    "Once connected, admins of workspaces you belong to can grant Claude access to repositories on your personal account.": "连接后，你所属工作区的管理员可以授权 Claude 访问你个人账号中的仓库。",
    "Sign in with GitHub so Claude can list organizations you own where the app is installed.": "登录 GitHub 后，Claude 即可列出你拥有且已安装 Claude App 的组织。",
    "Let Claude verify your changes in the iOS Simulator on this Mac: running your app, driving it through flows, and capturing screenshots and recordings. You will be asked before Claude uses each device. When off, Claude doesn’t get its simulator tools, and you can still use the simulator in the app yourself.": "让 Claude 在这台 Mac 的 iOS 模拟器中验证你的更改，包括运行应用、执行操作流程以及截取屏幕截图和录屏。Claude 每次使用设备前都会请求你的确认。关闭此功能后，Claude 将无法使用模拟器工具，但你仍可自行使用应用中的模拟器。",
    "Could not enable PR auto-fix. Update the desktop app to use it.": "无法启用 PR 自动修复。请更新桌面应用后再使用。",
    "Showing counts for the first {loaded} runners. Load more to see all.": "当前显示前 {loaded} 个运行器的数量统计。加载更多即可查看全部。",
    "Hi! Can you connect GitHub for our Claude workspace? Use this link: {link}\nYou’ll need to be an owner of our GitHub organization and an admin of our Claude workspace. If you’re not a workspace admin yet, ask our Claude admin to add you. When GitHub asks which repositories Claude can access, include the ones we want Claude to work with.": "你好！可以帮我们的 Claude 工作区连接 GitHub 吗？请使用此链接：{link}\n你需要拥有我们的 GitHub 组织，同时是 Claude 工作区管理员。如果你还没有工作区管理员权限，请让 Claude 管理员为你添加。GitHub 询问 Claude 可以访问哪些仓库时，请选择需要 Claude 处理的仓库。",
    "Re-approve emulator access in Settings → Claude Code → Mobile simulators, or restart the app.": "在“设置”→“Claude Code”→“移动端模拟器”中重新批准模拟器访问权限，或重启应用。",
    "No usage data yet. Token totals will appear here once sessions in this project have reported usage.": "暂无用量数据。此项目中的会话上报用量后，此处会显示令牌总数。",
    "Your granted credits will be used before any purchased credits.": "获赠的用量额度会优先于已购买的额度使用。",
    "{version} is now live for members.": "{version} 已面向成员启用。",
    "Once you use Chat, Cowork, or Code on this device, token usage will show up here.": "在此设备上使用 Chat、Cowork 或 Code 后，此处将显示令牌用量。",
    "Claude features that use {login} repositories stop working in this workspace. The app stays installed on GitHub until you remove it there. Existing credentials expire within an hour.": "此工作区中依赖 {login} 仓库的 Claude 功能将停止工作。Claude App 会继续保留在 GitHub 上，直到你从 GitHub 移除；现有凭据将在一小时内过期。",
    "Auto-fix isn’t available in this version of the desktop app. Update the app to use it.": "此桌面应用版本不支持自动修复。请更新应用后再使用。",
    "The Claude app is installed on these GitHub accounts, but they aren’t linked to this workspace yet.": "这些 GitHub 账号已安装 Claude App，但尚未关联到此工作区。",
    "Add runners, or wait for active sessions to finish before queued sessions can start.": "添加运行器，或等待活动会话完成，之后排队中的会话才能启动。",
    "Significantly faster output at the same model quality. Charged at a higher rate from your usage credits.": "在模型质量相同的前提下显著提升输出速度，并按更高费率消耗用量额度。",
    "I noticed you’ve been working in these repositories recently. Do you want me to add them to this project?": "我注意到你最近在这些仓库中工作。要将它们添加到此项目吗？",
    "No GitHub organizations to link. Install the Claude app on a GitHub organization you own to get started.": "没有可关联的 GitHub 组织。请先在你拥有的 GitHub 组织中安装 Claude App。",
    "Background lets you keep working while Claude drives one app. Full control takes over the whole screen.": "“后台”模式允许你在 Claude 操作单个应用时继续工作；“完全控制”会接管整个屏幕。",
    "The Claude app is installed on these GitHub accounts. Link one to give this workspace access to its repositories.": "这些 GitHub 账号已安装 Claude App。关联其中一个账号，即可让此工作区访问其仓库。",
    "How much of this org’s promotional credit for Claude in Slack has been used, and when it expires.": "此组织的 Claude in Slack 促销额度已使用多少，以及额度何时到期。",
    "You’ll keep Pro until your annual plan ends, then move to the Free plan.": "你可以继续使用 Pro，直到年度方案结束，之后将切换为 Free。",
    "Ultrareview reviews the code in a git repository, and this session’s folder isn’t inside one. Choose a folder that contains a repository to continue.": "Ultrareview 用于审核 Git 仓库中的代码，而当前会话文件夹不在仓库中。请选择包含 Git 仓库的文件夹以继续。",
    "Let Claude verify your changes in Android emulators on this Mac: running your app, driving it through flows, and capturing screenshots and recordings. You will be asked before Claude uses each device. When off, Claude doesn’t get its emulator tools, and you can still use the emulator in the app yourself.": "让 Claude 在这台 Mac 的 Android 模拟器中验证你的更改，包括运行应用、执行操作流程以及截取屏幕截图和录屏。Claude 每次使用设备前都会请求你的确认。关闭此功能后，Claude 将无法使用模拟器工具，但你仍可自行使用应用中的模拟器。",
    "Routine duplicated, but the GitHub trigger couldn’t be configured — the Claude GitHub App isn’t installed on the repository. <link>Install the GitHub App</link>, then edit the copy to retry.": "例程已复制，但无法配置 GitHub 触发器：该仓库尚未安装 Claude GitHub App。请先<link>安装 GitHub App</link>，再编辑副本以重试。",
    "Routine created, but the GitHub trigger couldn’t be linked — the Claude GitHub App isn’t installed on the repository. <link>Install the GitHub App</link>, then edit the routine to retry.": "例程已创建，但无法关联 GitHub 触发器：该仓库尚未安装 Claude GitHub App。请先<link>安装 GitHub App</link>，再编辑例程以重试。",
    "Sent alongside the IAP token on every proxied request — for backends behind IAP with their own API key. Cannot target a header the IAP handler already uses: the IAP token’s header, or Authorization when App audience is set. Values are write-only and never shown after saving.": "每个代理请求都会将此值与 IAP token 一并发送，适用于位于 IAP 后方且使用自身 API 密钥的后端。不能将其设置为 IAP 处理器已占用的请求头：IAP token 所在请求头；设置 App audience 时也不能使用 Authorization。此值只写，保存后不会再次显示。",
    "This removes the stale connection record from this workspace. The Claude app is already uninstalled on GitHub, so there is no access to revoke.": "这会从工作区移除失效的连接记录。Claude App 已从 GitHub 卸载，因此没有需要撤销的访问权限。",
    "All runner slots are in use. Add runners or wait for active sessions to finish.": "所有运行器槽位均在使用中。请添加运行器，或等待活动会话结束。",
    "Allow your organization to code with Claude in the desktop app.": "允许组织成员在桌面应用中使用 Claude 编程。",
    "Allow your organization to code with Claude in the mobile app.": "允许组织成员在移动应用中使用 Claude 编程。",
    "Claude can launch, tap, and screenshot to test your app, right in the iOS Simulator.": "Claude 可以直接在 iOS 模拟器中启动、点按并截屏，以测试你的应用。",
    "This version is currently serving members. Set a different version as current first.": "此版本当前正供成员使用。请先将其他版本设为当前版本。",
    "Your new card was saved but couldn’t be set for this charge, so no credits were purchased. Submit again to continue.": "新银行卡已保存，但无法用于本次扣款，因此未购买用量额度。请重新提交以继续。",
    "Both features use your organization’s <link>usage credits</link>.": "这两项功能都会消耗组织的<link>用量额度</link>。",
    "Couldn’t match this pull request to a repository in the session.": "无法将此拉取请求与会话中的仓库对应起来。",
    "Git repositories to surface as plugin marketplaces in the Directory’s Organization tab. The app re-clones each periodically.": "在“目录”的“组织”标签页中，将 Git 仓库显示为插件市场。应用会定期重新克隆这些仓库。",
    "Select an environment that supports multiple repositories in the Resources tab": "请在“资源”标签页中选择支持多个仓库的环境",
    "Deploy runners using your environment key. Runners host Claude sessions on your infrastructure. <link>Learn more</link>": "使用环境密钥部署运行器。运行器会在你的基础设施上承载 Claude 会话。<link>了解更多</link>",
    "Connect GitHub to give Claude access to your organization’s repositories in Claude Tag, Claude Security, and Claude Code.": "连接 GitHub，让 Claude Tag、Claude Security 和 Claude Code 能够访问你组织的仓库。",
    "Members can switch anytime. Their choice sticks until you set or change a default.": "成员可随时切换模型，选择会一直保留，直到你设置或更改默认模型。",
    "You’ll keep Pro until your annual plan ends on {date}, then move to the Free plan.": "你可以继续使用 Pro，直到年度方案于 {date} 结束，之后将切换为 Free。",
    "As you delegate work, you can ask me to directly modify my instructions, add more repositories, send scheduled messages, and more. Start all your work here, and I’ll keep watch over everything running and post updates as things finish or need you.": "委派工作时，你可以让我直接修改指令、添加仓库、发送定时消息等。所有工作都可以从这里开始，我会持续跟踪运行状态，并在任务完成或需要你处理时发布更新。",
    "Claude Code on the web is a far more capable way to work with your GitHub repos. It can read, edit, run, and reason over your whole codebase.": "网页版 Claude Code 能更高效地处理 GitHub 仓库，可读取、编辑、运行代码并理解整个代码库。",
    "Let Claude verify your changes in Android emulators on this computer: running your app, driving it through flows, and capturing screenshots and recordings. You will be asked before Claude uses each device. When off, Claude doesn’t get its emulator tools, and you can still use the emulator in the app yourself.": "让 Claude 在这台电脑的 Android 模拟器中验证你的更改，包括运行应用、执行操作流程以及截取屏幕截图和录屏。Claude 每次使用设备前都会请求你的确认。关闭此功能后，Claude 将无法使用模拟器工具，但你仍可自行使用应用中的模拟器。",
}

CURRENT_RELEASE_TRANSLATIONS = {
    "Your organization admin has disabled connectors in artifacts. To use this feature, ask your admin to enable connectors in artifacts.": "你的组织管理员已禁用工件中的连接器。若要使用此功能，请让管理员启用工件中的连接器。",
    "Artifacts disabled": "工件已禁用",
    "AI-powered artifacts disabled": "AI 工件已禁用",
    "When you delete this chat, you’ll also delete the published artifacts in this chat.": "删除此聊天时，其中已发布的工件也会一并删除。",
    "Go to page {n}": "前往第 {n} 页",
    "Go to organization settings": "前往组织设置",
    "Submit feedback, report a bug, or share your conversation": "提交反馈、报告问题或分享你的对话",
    "{count, plural, one {# fix} other {# fixes}} in progress": "{count, plural, one {# 项修复进行中} other {# 项修复进行中}}",
    "{pct} of your weekly limit": "已使用每周限额的 {pct}",
    "Stop loading": "停止加载",
    "Not in project": "不在项目中",
    "Spend limit removed for “{groupName}”.": "已移除“{groupName}”的支出限额。",
    "Connect for your team": "为团队连接",
    "Contact your organization’s admin to change your plan.": "请联系组织管理员更改方案。",
    "Delete all": "全部删除",
    "Failed to add folder. You can try again.": "添加文件夹失败，请重试。",
    "Open Browser tab": "打开浏览器标签页",
    "Watch for news or mentions of a topic, competitor, or keyword.": "关注某个主题、竞争对手或关键词的新闻和提及。",
    "Categorize your inbox and draft replies to anything urgent.": "整理收件箱，并为所有紧急邮件起草回复。",
    "No shared artifacts yet": "暂无共享工件",
    "The selected model is no longer available.": "所选模型已不可用。",
    "Send me a daily briefing": "给我发送每日简报",
    "Pin session": "固定会话",
    "Message sent to another session": "消息已发送到另一个会话",
    "Failed to create artifact": "创建工件失败",
    "I’ll pull context from your files and connectors": "我会从你的文件和连接器中获取上下文",
    "{count, plural, one {# folder or file} other {# folders and files}}": "{count, plural, one {# 个文件夹或文件} other {# 个文件夹和文件}}",
    "Loading the site…": "正在加载网站…",
    "Reopened": "已重新打开",
    "Opened": "已打开",
    "{count, plural, one {# configured marketplace couldn’t load} other {# configured marketplaces couldn’t load}}": "{count, plural, one {# 个已配置的市场无法加载} other {# 个已配置的市场无法加载}}",
    "Edit settings for {count, plural, one {# group} other {# groups}}": "编辑 {count, plural, one {# 个组} other {# 个组}}的设置",
    "Open logs on GitHub": "在 GitHub 上打开日志",
    "No environments yet": "暂无环境",
    "artifacts": "工件",
    "{pct} of your usage": "已使用 {pct}",
    "Repository access for {login}": "{login} 的仓库访问权限",
    "Open in app": "在应用中打开",
    "No connectors to connect": "没有可连接的连接器",
    "Failed to add connector.": "添加连接器失败。",
    "Connecting to Claude": "正在连接 Claude",
    "Failed to message another session": "向另一个会话发送消息失败",
    "Go to chat": "前往聊天",
    "Only you can access artifacts you share.": "只有你可以访问自己分享的工件。",
    "In app browser": "应用内浏览器",
    "{count, plural, one {“{fileName}” can’t be attached in this chat yet — this file type isn’t supported here. You can paste its contents into the message instead.} other {{count} files can’t be attached in this chat yet — their file types aren’t supported here. You can paste their contents into the message instead.}}": "{count, plural, one {暂时无法在此聊天中附加“{fileName}”，这里尚不支持此文件类型。你可以改为将文件内容粘贴到消息中。} other {暂时无法在此聊天中附加这 {count} 个文件，这里尚不支持这些文件类型。你可以改为将文件内容粘贴到消息中。}}",
    "I want to make a live artifact. Explain what live artifacts are in Cowork, then look at my connectors (MCP servers), and ask me a few questions to figure out what kind of live artifact would be most useful for me.": "我想制作一个实时工件。请先说明 Cowork 中的实时工件是什么，再查看我的连接器（MCP 服务器），并问我几个问题，以确定哪种实时工件最适合我。",
    "Disabled for the organization": "已为组织禁用",
    "read page content on": "读取以下网站的页面内容",
    "You’re close to your weekly limit. Turn on usage credits to keep going.": "你即将达到每周限额。请开启用量额度以继续使用。",
    "Runner disconnected": "运行器已断开连接",
    "Directory is up to date.": "目录已是最新状态。",
    "Preview isn’t available for {fileName} ({fileSize}).": "无法预览 {fileName}（{fileSize}）。",
    "Preview isn’t available for {fileName}.": "无法预览 {fileName}。",
    "Go to previous match": "前往上一个匹配项",
    "Failed to write draft": "起草失败",
    "Failed to post.": "发布失败。",
    "You can’t approve or request changes on your own pull request.": "你无法批准自己的拉取请求，也无法对其请求更改。",
    "Failed to send message": "发送消息失败",
    "You ran out of usage credits · Limit resets {time}": "用量额度已用完 · 限额于 {time} 重置",
    "You hit your spend limit · Limit resets {time}": "已达到支出限额 · 限额于 {time} 重置",
    "Failed to check connectors": "检查连接器失败",
    "Apply to {count, plural, one {# group} other {# groups}}": "应用到 {count, plural, one {# 个组} other {# 个组}}",
    "Failed to check skills": "检查技能失败",
    "Not active": "未启用",
    "No workspaces connected yet": "尚未连接工作区",
    "Stop server": "停止服务器",
    "Failed to save skill": "保存技能失败",
    "Open the Claude app": "打开 Claude 应用",
    "Failed to request folder access": "请求文件夹访问权限失败",
    "Add role": "添加角色",
    "Added to memory, removed {count, plural, one {# memory file} other {# memory files}}": "已添加到记忆，并移除 {count, plural, one {# 个记忆文件} other {# 个记忆文件}}",
    "Let org members run dynamic workflows in Claude Code.": "允许组织成员在 Claude Code 中运行动态工作流。",
    "{count, plural, one {# connector} other {# connectors}}": "{count, plural, one {# 个连接器} other {# 个连接器}}",
    "Spend limit added for “{groupName}”.": "已为“{groupName}”添加支出限额。",
    "Finding {current} of {total}": "第 {current} 项，共 {total} 项",
    "Draft and iterate on websites, graphics, documents, and code alongside your chat with Artifacts.": "在聊天旁使用工件起草并迭代网站、图形、文档和代码。",
    "{pct} of your extra usage": "已使用额外用量的 {pct}",
    "No skills from Anthropic yet.": "Anthropic 尚未提供技能。",
    "Failed to run code": "运行代码失败",
    "On another device": "在另一台设备上",
    "{expanded, select, true {Hide} other {Show}} repositories for {login}": "{expanded, select, true {隐藏} other {显示}} {login} 的仓库",
    "Running your WorktreeCreate hook…": "正在运行 WorktreeCreate 钩子…",
    "Failed to message session": "向会话发送消息失败",
    "Download and open": "下载并打开",
    "Request sent to your admin. Your <link>plan usage</link> resets {day} at {time}.": "请求已发送给管理员。你的<link>方案用量</link>将于 {day} {time} 重置。",
    "Request sent to your admin. Your <link>plan usage</link> resets at {time}.": "请求已发送给管理员。你的<link>方案用量</link>将于 {time} 重置。",
    "Add to your brief": "添加到简报",
    "Cowork isn’t available on this device.": "此设备无法使用 Cowork。",
    "QR code for Claude app billing settings": "Claude 应用账单设置二维码",
    "Shell disconnected: {reason}": "Shell 已断开连接：{reason}",
    "{pct} of your session limit": "已使用会话限额的 {pct}",
    "Connect GitHub so Claude can read and write to your repositories.": "连接 GitHub，让 Claude 可以读写你的仓库。",
    "Add to channels": "添加到频道",
    "Failed to message agent": "向智能体发送消息失败",
    "On this device": "在此设备上",
    "All groups": "所有组",
    "Archive all": "全部归档",
    "Reset to defaults": "恢复默认设置",
    "Create new task with context from “{projectName}”?": "要使用“{projectName}”中的上下文创建新任务吗？",
    "No plugins available in your organization.": "你的组织中没有可用插件。",
    "Failed to add source.": "添加来源失败。",
    "Default to 1M context": "默认使用 1M 上下文",
    "Build for the Claude Directory": "为 Claude 目录构建",
    "Write your draft…": "撰写草稿…",
    "{count, plural, one {Claude also edited a section you changed} other {Claude also edited # sections you changed}}": "{count, plural, one {Claude 也编辑了你更改的一个部分} other {Claude 也编辑了你更改的 # 个部分}}",
    "Message {position} of {count}": "第 {position} 条消息，共 {count} 条",
    "Open in new window": "在新窗口中打开",
    "Allow your team to run dynamic workflows in Claude Code.": "允许你的团队在 Claude Code 中运行动态工作流。",
    "Tab to add": "按 Tab 键添加",
    "Your feedback": "你的反馈",
    "“{value}” isn’t an available model.": "“{value}”不是可用模型。",
    "CI: checks in progress": "CI：检查进行中",
    "{count, plural, one {Add # organization member} other {Add all # organization members}}": "{count, plural, one {添加 # 名组织成员} other {添加全部 # 名组织成员}}",
    "Connect your tools": "连接你的工具",
    "Go to projects": "前往项目",
    "Available on Enterprise": "Enterprise 方案可用",
    "Failed to run command": "运行命令失败",
    "Failed to message @{to}": "向 @{to} 发送消息失败",
    "We’ll review your account": "我们将审核你的账号",
    "No projects yet": "暂无项目",
    "Failed to archive session": "归档会话失败",
    "Claude Code isn’t available on your account": "你的账号无法使用 Claude Code",
    "Not available on your plan": "当前方案不可用",
    "Projects are now in Claude Code": "项目现已移至 Claude Code",
    "Failed to check artifacts": "检查工件失败",
    "No connectors available": "没有可用连接器",
    "Chat isn’t available in local projects": "本地项目无法使用聊天",
    "Repositories in {login}": "{login} 中的仓库",
    "Don’t see your repository?": "没有看到你的仓库？",
    "Failed to add the connector": "添加连接器失败",
    "Connect to Claude": "连接 Claude",
    "No domains added yet": "尚未添加域名",
    "Add to prompt": "添加到提示词",
    "Security Center isn’t available on your plan.": "当前方案无法使用 Security Center。",
    "Failed to delete scheduled task. Try again.": "删除计划任务失败，请重试。",
    "All changes saved": "所有更改均已保存",
    "View-only access": "仅查看权限",
    "click on": "点击",
    "Shared with your organization": "已与组织共享",
    "{count, plural, one {Stop server and close} other {Stop # servers and close}}": "{count, plural, one {停止服务器并关闭} other {停止 # 个服务器并关闭}}",
    "No artifacts yet": "暂无工件",
    "Failed to send file": "发送文件失败",
    "Only selected": "仅所选项",
    "{mod} Enter to send": "按 {mod} Enter 发送",
    "Enter the details of the key you’ve configured in your {provider} account.": "输入你在 {provider} 账号中配置的密钥详情。",
    "Added to memory, removed {fileNames}": "已添加到记忆，并移除 {fileNames}",
    "Connecting to GitHub…": "正在连接 GitHub…",
    "No repositories yet — use Add to connect one.": "尚无仓库，请使用“添加”进行连接。",
    "No sessions yet.": "暂无会话。",
    "No connected connectors": "没有已连接的连接器",
    "Security Center isn’t enabled for your organization.": "你的组织尚未启用 Security Center。",
    "Cmd or Ctrl click a link to open it in your default browser.": "按住 Cmd 或 Ctrl 并点击链接，即可在默认浏览器中打开。",
    "Added to memory": "已添加到记忆",
    "Cowork isn’t enabled for your organization": "你的组织尚未启用 Cowork",
    "Shared artifacts": "共享工件",
    "Failed to check plugins": "检查插件失败",
    "Add model": "添加模型",
    "You’ll only see tools your organization has given you access to.": "此处只会显示组织授权你使用的工具。",
    "Only your 60 most recent Code artifacts are searchable here.": "此处只能搜索最近 60 个 Code 工件。",
    "Paste a shared artifact link to add a copy to your artifacts.": "粘贴共享工件链接，将副本添加到你的工件中。",
    "Failed to read task": "读取任务失败",
    "This artifact wants to open a {protocol} link in another app: {url}": "此工件想在其他应用中打开 {protocol} 链接：{url}",
    "Always allow {protocol} links from artifacts": "始终允许工件中的 {protocol} 链接",
    "This artifact wants to open {appName} with the link {url}": "此工件想通过链接 {url} 打开 {appName}",
    "The live artifact {artifactId} can use the following connectors automatically without asking for additional permissions.": "实时工件 {artifactId} 可自动使用以下连接器，无需请求额外权限。",
    "The {artifactId} live artifact uses connectors you haven’t set up yet:": "实时工件 {artifactId} 使用了你尚未设置的连接器：",
    "Messaging @{to}": "正在向 @{to} 发送消息",
    "Approved plan from @{to}": "已批准来自 @{to} 的计划",
    "Members currently get {from}. Publish and serve the older {to} instead?": "成员当前使用 {from}。要改为发布并提供旧版 {to} 吗？",
    "Members currently get {from}. Make {to} current so everyone gets it instead?": "成员当前使用 {from}。要将 {to} 设为当前版本，供所有成员使用吗？",
    "Members currently get {from}. Roll back so everyone gets {to} instead?": "成员当前使用 {from}。要回滚到 {to}，让所有成员改用该版本吗？",
    "the dev server": "开发服务器",
    "Create and name your own session groups — drag sessions in, or right-click a session → `Move to group`": "创建并命名你自己的会话组：将会话拖入组中，或右键点击会话并选择`移到组`",
    "Claude in {suiteName} is available on Pro, Max, Team, and Enterprise plans": "Pro、Max、Team 和 Enterprise 方案可以在 {suiteName} 中使用 Claude",
    "Delete <b>{name}</b> from your live artifacts?": "要从实时工件中删除 <b>{name}</b> 吗？",
    "Delete <b>{name}</b> from your live artifacts? This will also unshare it.": "要从实时工件中删除 <b>{name}</b> 吗？这也会取消共享。",
    "Artifacts are interactive pages that open in the Cowork sidebar on your connected desktop. <b>Cancel</b> to skip creating it.": "工件是交互式页面，会在已连接桌面端的 Cowork 侧边栏中打开。选择<b>取消</b>可跳过创建。",
    "Reconnecting to {host}…": "正在重新连接 {host}…",
    "`Open in editor` from the diff view or a session’s right-click menu": "在差异视图或会话右键菜单中选择`在编辑器中打开`",
    "Get Claude for Desktop to use this extension": "获取 Claude Desktop 以使用此扩展",
    "Update Claude for Desktop to enable this feature.": "更新 Claude Desktop 以启用此功能。",
    "Update to the latest version of Claude for Desktop to use desktop extensions": "更新到最新版本的 Claude Desktop 以使用桌面扩展",
    "What is a Claude gift membership?": "什么是 Claude 赠礼订阅？",
    "A Claude gift membership gives someone access to Claude Pro or Claude Max for a set period of time. They’ll get all the benefits of a paid subscription, including access to our latest models, Claude Code, and unlimited projects.": "Claude 赠礼订阅可让对方在指定期限内使用 Claude Pro 或 Claude Max，并享受付费订阅的全部权益，包括使用最新模型、Claude Code 和无限项目。",
    "Group Memberships": "所属组",
    "Can manage user membership": "可以管理用户成员关系",
    "Token couldn’t be validated. Check that it has repo scope and try again.": "无法验证令牌。请确认令牌具有 `repo` 作用域，然后重试。",
    "Marketplace “{marketplaceName}” removed.": "市场“{marketplaceName}”已移除。",
    "Issue opened": "议题已打开",
    "Issue opened, edited, deleted, etc.": "议题被打开、编辑、删除等",
    "Run by schedule": "按计划运行",
    "Run by weekly schedule": "按每周计划运行",
    "Run by daily schedule": "按每日计划运行",
    "Try Claude Design": "试用 Claude Design",
    "{n, plural, one {<v>#</v> tool use} other {<v>#</v> tool uses}}": "{n, plural, one {<v>#</v> 次工具调用} other {<v>#</v> 次工具调用}}",
    "Running code…": "正在运行代码…",
    "Add link": "添加链接",
    "Office Agents": "Office Agents",
    "Default app": "默认应用",
    "Following a plan": "正在按计划执行",
    "Claude now has a browser": "Claude 现在可以使用浏览器了",
    "Run cancelled": "运行已取消",
    "Cancel run": "取消运行",
    "Connect an app": "连接应用",
    "Add project context from “{projectName}”?": "要从“{projectName}”添加项目上下文吗？",
    "claude://cowork/shared-artifact?uuid=…": "claude://cowork/shared-artifact?uuid=…",
    "Marketplace sync failed.": "市场同步失败。",
    "Could not access the marketplace archive. Check that the URL is correct and the file is publicly accessible.": "无法访问市场归档。请检查 URL 是否正确，并确认该文件可公开访问。",
    "Computer use is on. To finish setup, grant the macOS permissions below.": "计算机操控已开启。若要完成设置，请授予下方的 macOS 权限。",
    "Claude Design Admin": "Claude Design 管理员",
    "Create GitHub issue": "创建 GitHub 议题",
    "Triage new issues and flag duplicates each morning": "每天早上整理新议题并标记重复项",
    "Scheduled scan (cancelled)": "计划扫描（已取消）",
    "Scan (cancelled)": "扫描（已取消）",
    "Cancelled.": "已取消。",
    "Auto-merge canceled.": "自动合并已取消。",
    "Open on GitHub": "在 GitHub 上打开",
    "Add in connector settings": "在连接器设置中添加",
    "Add to": "添加到",
    "Add to message": "添加到消息",
    "Save to memory": "保存到记忆",
    "Add to chat": "添加到聊天",
    "Filter by group": "按组筛选",
    "Filter by category": "按类别筛选",
    "Filter sources by category": "按类别筛选来源",
    "Start in Cowork": "在 Cowork 中开始",
    "Start in Claude Code": "在 Claude Code 中开始",
    "Add an MCP server": "添加 MCP 服务器",
    "Show in Files": "在“文件”中显示",
    "Opening Claude Code…": "正在打开 Claude Code…",
    "Canceling…": "正在取消…",
    "No one": "无人",
    "Review a GitHub pull request": "审阅 GitHub 拉取请求",
    "Project or folder": "项目或文件夹",
    "Opens as a new task": "作为新任务打开",
    "API key or token": "API 密钥或令牌",
    "Connect a workspace": "连接工作区",
    "Enter a domain.": "输入域名。",
    "Scheduled a message": "已安排一条消息",
    "Add a GitHub org": "添加 GitHub 组织",
    "Re-run failed checks": "重新运行失败的检查",
    "No dev server configured": "未配置开发服务器",
    "OpenAI API key": "OpenAI API 密钥",
    "openid email https://www.googleapis.com/auth/cloud-platform": "openid email https://www.googleapis.com/auth/cloud-platform",
    "api://…/access_as_user offline_access": "api://…/access_as_user offline_access",
    "openid profile email offline_access": "openid profile email offline_access",
    "openid offline_access CLIENT_ID/.default": "openid offline_access CLIENT_ID/.default",
    "enduser.id": "enduser.id",
    "Welcome to Claude Max!": "欢迎使用 Claude Max！",
    "You will keep access to Claude Max.": "你将继续使用 Claude Max。",
    "Clawdmart": "Clawdmart",
    "Code in the terminal with Claude Code": "使用 Claude Code 在终端中编程",
    "Your seat in {orgName} doesn’t include Claude Code. Ask an admin for access.": "你在 {orgName} 中的席位不包含 Claude Code。请向管理员申请访问权限。",
    "Your seat in {orgName} doesn’t include Claude Code. Ask an admin for access, or switch to another organization.": "你在 {orgName} 中的席位不包含 Claude Code。请向管理员申请访问权限，或切换到其他组织。",
    "Open Claude Code settings": "打开 Claude Code 设置",
    "Starting Claude Code...": "正在启动 Claude Code...",
    "Started Claude Code": "已启动 Claude Code",
    "The installed Claude Code version doesn’t support a feature this app uses. Update Claude Code on this host.": "已安装的 Claude Code 版本不支持此应用使用的功能。请更新此主机上的 Claude Code。",
    "Claude Code isn’t set up yet. <link>Get started with Claude Code</link> to launch sessions from here.": "Claude Code 尚未设置。<link>开始使用 Claude Code</link>后，即可从这里启动会话。",
    "You can also open Claude <link>in your browser</link>.": "你也可以<link>在浏览器中打开 Claude</link>。",
    "Stop Claude’s response": "停止 Claude 回复",
    "Includes Claude Code access and more usage": "包含 Claude Code 使用权限和更高用量额度",
    "Chat + Claude Code seat required": "需要 Chat + Claude Code 席位",
    "*Team and Enterprise plans do not include access to Claude Code": "*Team 和 Enterprise 方案不包含 Claude Code 使用权限",
    "Free from developer.android.com. Bundles the SDK and emulator.": "可从 developer.android.com 免费获取，其中包含 SDK 和模拟器。",
    "Go to Claude": "前往 Claude",
    "Continue to Claude": "继续使用 Claude",
    "Hook re-prompted Claude": "Hook 已重新提示 Claude",
    "Create a pitch deck": "创建路演演示文稿",
    "Daily tokens by model": "按模型统计每日 token 用量",
    "I want to analyze an A/B test. Give me space to share the experiment setup, metrics, and data. I might have the raw data or experiment docs to upload. Follow up on anything that’s unclear, then calculate statistical significance, effect sizes, and confidence intervals, and present a clear recommendation with supporting charts.": "我想分析 A/B 测试。请留出空间让我分享实验设置、指标和数据。我可能会上传原始数据或实验文档。请追问任何不清楚的地方，然后计算统计显著性、效应量和置信区间，并用图表支撑给出明确建议。",
    "Name A-Z": "名称 A-Z",
    "Friends can try both Cowork and Claude Code.": "朋友可以同时试用 Cowork 和 Claude Code。",
    "Auto-merge isn’t available in SSH sessions yet. Use gh or GitHub directly.": "SSH 会话暂不支持自动合并。请直接使用 gh 或 GitHub。",
    "Claude for PowerPoint": "Claude for PowerPoint",
    "Claude for Slack": "Claude for Slack",
    "Claude Enterprise seat": "Claude Enterprise 席位",
    "Claude Cowork": "Claude Cowork",
    "Claude API": "Claude API",
    "Claude Free": "Claude Free",
    "Claude in Slack": "Claude in Slack",
    "Claude Enterprise": "Claude Enterprise",
    "Claude Code CLI": "Claude Code CLI",
    "Claude Max": "Claude Max",
    "Claude Pro": "Claude Pro",
    "Claude Platform": "Claude Platform",
    "Claude Ship": "Claude Ship",
    "Claude for Excel": "Claude for Excel",
    "the Claude API": "Claude API",
    "All Claude Models": "所有 Claude 模型",
    "Weekly · all models": "每周 · 所有模型",
    "Wires up sign-in with email magic links, adds the sign-in/out UI, and gates any private pages. If authentication isn’t configured for this project yet, Claude will set it up first and check in before continuing.": "连接电子邮件魔术链接登录，添加登录和退出界面，并限制对私有页面的访问。如果此项目尚未配置身份验证，Claude 会先完成配置，并在继续前向你确认。",
    "With Cowork, Claude can tackle several complex tasks at the same time. Organize files while drafting a report while crunching data.\n\nCheck in when you want or just let Claude cook.": "借助 Cowork，Claude 可同时处理多项复杂任务：在整理文件的同时起草报告、分析数据。\n\n你可以随时查看进度，也可以让 Claude 自主完成。",
    "With Cowork, Claude can tackle several complex tasks at the same time. Organize files while drafting a report while crunching data.\nCheck in when you want or just let Claude cook.": "借助 Cowork，Claude 可同时处理多项复杂任务：在整理文件的同时起草报告、分析数据。\n你可以随时查看进度，也可以让 Claude 自主完成。",
    "Take over the screen? You’ve set Background as your preferred mode, so Claude is checking before switching to full-screen control.": "要接管屏幕吗？你已将“后台”设为首选模式，因此 Claude 会在切换到全屏控制前询问。",
    "Take over the screen? Claude was working on {appName} in the background and now needs full-screen control.": "要接管屏幕吗？Claude 一直在后台操作 {appName}，现在需要全屏控制。",
    "Claude runs on its own and pauses to ask if anything looks unsafe.": "Claude 会自主运行，并在发现操作可能不安全时暂停询问。",
    "Claude checks in when it needs your input": "Claude 在需要你输入时会向你确认",
    "Dispatch to Claude and check in from anywhere—a task, a code session, in one continuous thread.": "将任务交给 Claude，并可从任何地方查看进度；任务和代码会话都会保留在同一条连续会话中。",
    "Check in when you want or just let Claude cook.": "你可以随时查看进度，也可以让 Claude 自主完成。",
    "Let’s get cooking! Pick an artifact category or start building your idea from scratch.": "开始创作吧！选择一个工件类别，或从零开始构思。",
    "Start cooking": "开始创作",
    "For feedback about Claude’s responses, use the thumbs up or down buttons under any message. That feedback goes directly to the teams improving Claude.": "如需反馈 Claude 的回复，请使用消息下方的赞或踩按钮。反馈会直接发送给负责改进 Claude 的团队。",
    "This check isn’t available right now. You can still switch to the other model.": "此检查当前不可用。你仍可切换到其他模型。",
    "You’re out of usage credits. Buy more to keep using {model} or switch models to continue this chat.": "你的用量额度已用完。购买更多额度以继续使用 {model}，或切换模型继续此聊天。",
    "You’re out of extra usage. Buy more to keep using {model} or switch models to continue this chat.": "额外用量已用完。购买更多额度以继续使用 {model}，或切换模型继续此聊天。",
    "This model isn’t available right now. You can switch to another model to continue using Claude.": "此模型当前不可用。你可以切换到其他模型继续使用 Claude。",
    "Couldn’t load checks. This view retries automatically.": "无法加载检查。此视图会自动重试。",
    "Checks cancelled.": "检查已取消。",
    "You’ve reached the temporary limit for these checks. Try again in a few minutes.": "这些检查已达到临时限额。请几分钟后重试。",
    "Support provided by {helplineName}, not Claude. <link>Learn more</link>": "支持服务由 {helplineName} 提供，并非 Claude。<link>了解更多</link>",
    "{orgName} is on Claude. Join your team to share projects and chats.": "{orgName} 已加入 Claude。加入团队即可共享项目和聊天。",
    "Try a quick task — Claude does it, you watch": "尝试一个简单任务：由 Claude 完成，你可以查看过程",
    "They’ll also get Claude in:": "他们还可在以下产品中使用 Claude：",
    "<b>Migrating an existing Claude Team or Enterprise plan to this AWS contract?</b> Don’t fill in this form. Your Anthropic account team will handle the migration. New to Claude? Continue with the form above.": "<b>要将现有 Claude Team 或 Enterprise 方案迁移到此 AWS 合同吗？</b>请勿填写此表单。你的 Anthropic 客户团队会处理迁移。首次使用 Claude？请继续填写上方表单。",
    "Welcome! I’m Claude.": "欢迎！我是 Claude。",
    "Welcome, {name}! I’m Claude.": "欢迎，{name}！我是 Claude。",
    "Let’s knock something off your list.": "先把你清单上的一件事搞定吧。",
}


EXACT_TRANSLATIONS.update(QUALITY_TRANSLATIONS)
EXACT_TRANSLATIONS.update(ICU_QUALITY_TRANSLATIONS)
EXACT_TRANSLATIONS.update(PLACEHOLDER_QUALITY_TRANSLATIONS)
EXACT_TRANSLATIONS.update(SHORT_UI_TRANSLATIONS)
EXACT_TRANSLATIONS.update(CURRENT_RELEASE_TRANSLATIONS)


FRAGMENT_TRANSLATIONS = {
    "absolute path": "绝对路径",
    "account": "账号",
    "accounts": "账号",
    "active subscription": "活跃订阅",
    "affected accounts": "受影响账号",
    "analytics": "分析",
    "API key": "API 密钥",
    "artifacts": "工件",
    "avatar": "头像",
    "billing": "账单",
    "browser": "浏览器",
    "browsers": "浏览器",
    "category": "类别",
    "chat": "聊天",
    "chats": "聊天",
    "Claude Code": "Claude Code",
    "code": "代码",
    "configuration": "配置",
    "console messages": "控制台消息",
    "conversation": "对话",
    "conversations": "对话",
    "connector": "连接器",
    "connectors": "连接器",
    "credential": "凭据",
    "credentials": "凭据",
    "dashboard": "仪表板",
    "device": "设备",
    "devices": "设备",
    "directory": "目录",
    "domain": "域名",
    "domains": "域名",
    "email": "邮箱",
    "emails": "邮箱",
    "file": "文件",
    "files": "文件",
    "folder": "文件夹",
    "GitHub App": "GitHub App",
    "group": "组",
    "groups": "组",
    "host": "主机",
    "hosts": "主机",
    "install status": "安装状态",
    "instructions": "指令",
    "key": "密钥",
    "keys": "密钥",
    "latest": "最新内容",
    "limit": "限制",
    "limits": "限制",
    "marketplace": "市场",
    "marketplaces": "市场",
    "memory": "记忆",
    "message": "消息",
    "messages": "消息",
    "model": "模型",
    "models": "模型",
    "network requests": "网络请求",
    "organization": "组织",
    "organization ID": "组织 ID",
    "output": "输出",
    "permissions": "权限",
    "Plan mode": "计划模式",
    "plugin": "插件",
    "plugins": "插件",
    "project": "项目",
    "Project ID": "项目 ID",
    "projects": "项目",
    "repository": "仓库",
    "repositories": "仓库",
    "relative path": "相对路径",
    "role": "角色",
    "routine": "例程",
    "routines": "例程",
    "rule": "规则",
    "rules": "规则",
    "run": "运行",
    "runs": "运行",
    "secret": "密钥",
    "server": "服务器",
    "session": "会话",
    "sessions": "会话",
    "settings": "设置",
    "skill": "技能",
    "skills": "技能",
    "source": "来源",
    "sources": "来源",
    "spend limit": "消费限制",
    "spend limits": "消费限制",
    "subscription": "订阅",
    "task": "任务",
    "tasks": "任务",
    "token": "令牌",
    "tokens": "令牌",
    "tool": "工具",
    "tools": "工具",
    "usage": "用量",
    "usage credits": "用量额度",
    "workspace": "工作区",
    "workspaces": "工作区",
    "workflow": "工作流",
    "workflows": "工作流",
}


PHRASE_REPLACEMENTS = [
    ("third-party returned an error", "第三方返回了错误"),
    ("Your connection works, but the provider rejected a test request.", "你的连接正常，但提供方拒绝了测试请求。"),
    ("Often a model-access or quota issue.", "这通常是模型访问权限或额度问题。"),
    ("Allowed outbound hosts", "允许的出站主机"),
    ("Allowed surfaces", "允许的界面"),
    ("General restrictions", "通用限制"),
    ("Offer 1M-context variant", "提供 1M 上下文变体"),
    ("Shown in the model picker", "显示在模型选择器中"),
    ("Leave blank to auto-format from the ID", "留空则根据 ID 自动格式化"),
    ("Cowork files", "Cowork 文件"),
    ("Dynamic workflows", "动态工作流"),
    ("High-contrast dark theme", "高对比度深色主题"),
    ("Discard unsaved changes", "放弃未保存的更改"),
    ("This configuration has changes that haven't been saved", "此配置有尚未保存的更改"),
    ("They will be lost", "这些更改将会丢失"),
    ("Apply Changes", "应用更改"),
    ("Discard Changes", "放弃更改"),
    ("Keep editing", "继续编辑"),
    ("Create API key", "创建 API 密钥"),
    ("Inference configuration", "推理配置"),
    ("Public Projects", "公共项目"),
    ("Secure VM features", "安全虚拟机功能"),
    ("Change location for Cowork files", "更改 Cowork 文件位置"),
    ("AWS config directory", "AWS 配置目录"),
    ("Couldn't save image", "无法保存图片"),
    ("What this URL is overriding", "此 URL 正在覆盖的内容"),
    ("The endpoint rejected the request", "端点拒绝了请求"),
    ("Check cert trust, IP allowlist, or auth headers", "请检查证书信任、IP 允许列表或认证标头"),
    ("Unsafe URL blocked", "已阻止不安全的 URL"),
    ("only http/https are allowed", "仅允许 http/https"),
    ("No usage data yet", "暂无用量数据"),
    ("plan usage appears once limits load", "限制加载后会显示方案用量"),
    ("session usage after Claude's first reply", "Claude 首次回复后会显示会话用量"),
    ("the Bedrock control-plane", "Bedrock 控制平面"),
    ("run a workflow", "运行工作流"),
    ("Read my eval metrics", "读取我的评估指标"),
    ("Move pane down", "下移窗格"),
    ("Log out of current session", "退出当前会话"),
    ("Select a role", "选择角色"),
    ("Select {email}", "选择 {email}"),
    ("Active Claude Code users in this period", "此期间活跃的 Claude Code 用户"),
    ("Allow your team to run multi-agent workflows in Claude Code", "允许你的团队在 Claude Code 中运行多智能体工作流"),
    ("Code with Claude on the go", "随时随地使用 Claude 编程"),
    ("run coding sessions in cloud environments", "在云环境中运行编码会话"),
    ("Career changer", "转行者"),
    ("Supply chain manager", "供应链经理"),
    ("Influencer", "影响者"),
    ("Gardener", "园艺师"),
    ("Receptionist", "接待员"),
    ("Team", "团队"),
    ("Leave", "离开"),
    ("Choose Claude data folder", "选择 Claude 数据文件夹"),
    ("The Chrome extension's session expired", "Chrome 扩展的会话已过期"),
    ("Open the Claude extension in Chrome and sign in again", "请在 Chrome 中打开 Claude 扩展并重新登录"),
    ("then retry", "然后重试"),
    ("Plan usage", "方案用量"),
    ("Usage image copied to clipboard", "用量图片已复制到剪贴板"),
    ("Wait for Claude", "等待 Claude"),
    ("Tap to open", "点按打开"),
    ("Weekly", "每周"),
    ("all models", "所有模型"),
    ("Version {version}", "版本 {version}"),
    ("Usage: {pct}", "用量：{pct}"),
    ("Sign back in to Claude in Chrome", "请在 Chrome 中重新登录 Claude"),
    ("5-hour limit", "5 小时限制"),
    ("Leave Design", "离开 Design"),
    ("Open link in another app", "在其他应用中打开链接"),
    ("Submit feedback and reinstall workspace", "提交反馈并重新安装工作区"),
    ("Your session has expired", "你的会话已过期"),
    ("Changes you made may not be saved", "你所做的更改可能不会保存"),
    ("Previous match", "上一个匹配项"),
    ("To exit full screen", "要退出全屏"),
    ("press {esc}", "请按 {esc}"),
    ("Quit anyway", "仍然退出"),
    ("Unlimited", "无限制"),
    ("Protected location", "受保护位置"),
    ("protected location", "受保护位置"),
    ("home/root directory", "主目录/根目录"),
    ("Choose a different folder", "请选择其他文件夹"),
    ("Thinking", "思考"),
    ("Always uses deep reasoning", "始终使用深度推理"),
    ("Complex, detailed work", "复杂、细致的工作"),
    ("Light, casual tasks", "轻量、日常任务"),
    ("Balanced for everyday work", "适合日常工作的均衡模式"),
    ("The hardest problems", "最困难的问题"),
    ("Takes longest", "耗时最长"),
    ("Quick replies to simple questions", "适合简单问题的快速回复"),
    ("Can think for more complex tasks", "可为更复杂的任务进行思考"),
    ("Higher effort means more thorough responses", "更高强度意味着回答更彻底"),
    ("takes longer", "耗时更长"),
    ("uses your limits faster", "更快消耗你的额度"),
    ("Default", "默认"),
    ("Extended", "扩展"),
    ("Medium", "中"),
    ("High", "高"),
    ("Low", "低"),
    ("Extra", "超高"),
    ("Faster", "更快"),
    ("Smarter", "更智能"),
    ("Off", "关"),
    ("Empty", "空"),
    ("Recheck", "重新检查"),
    ("Cancel", "取消"),
    ("Open", "打开"),
    ("Choose", "选择"),
    ("Design", "设计"),
    ("Headers", "标头"),
    ("Header", "标头"),
    ("role", "角色"),
    ("model", "模型"),
    ("workflow", "工作流"),
    ("workflows", "工作流"),
    ("architecture tradeoffs", "架构权衡"),
    ("Evaluate", "评估"),
    ("Build", "构建"),
    ("Write", "撰写"),
    ("Create", "创建"),
    ("Repurpose", "改写复用"),
    ("blog post", "博客文章"),
    ("across channels", "跨渠道"),
]


KNOWN_OK_EXACT = {
    "Claude",
    "Claude Code",
    "MCP",
    "GitHub",
    "Slack",
    "AWS",
    "API",
    "SDK",
    "URL",
    "SSH",
    "JSON",
    "OpenTelemetry",
    "X-Header-Name",
}


ASCII_WORD_RE = re.compile(r"[A-Za-z]{3,}")
PLACEHOLDER_ONLY_RE = re.compile(r"^[\s\d{}#%$.,:+\-_/()\\[\]<>|~]+$")
PLACEHOLDER_PREFIXES = ("待翻译：", "待补充翻译：")
QUOTED_JS_STRING_RE = re.compile(r'"((?:\\.|[^"\\])*)"')

ALLOWED_ENGLISH_WORDS = {
    "agent",
    "anthropic",
    "api",
    "aws",
    "azure",
    "baa",
    "bedrock",
    "chrome",
    "claude",
    "cli",
    "code",
    "cowork",
    "cpa",
    "fps",
    "github",
    "http",
    "https",
    "ide",
    "id",
    "json",
    "jwt",
    "linux",
    "macos",
    "mcp",
    "mdm",
    "oauth",
    "oidc",
    "opentelemetry",
    "pip",
    "psc",
    "scim",
    "sdk",
    "ssh",
    "sse",
    "ui",
    "url",
    "uri",
    "vertex",
    "vpc",
    "windows",
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(dict(sorted(data.items())), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_placeholder_translation(value: object) -> bool:
    return isinstance(value, str) and value.startswith(PLACEHOLDER_PREFIXES)


def placeholder_source(value: str) -> str:
    for prefix in PLACEHOLDER_PREFIXES:
        if value.startswith(prefix):
            return value[len(prefix) :]
    return value


def decode_js_string(value: str) -> str:
    try:
        return json.loads(f'"{value}"')
    except json.JSONDecodeError:
        return value


def quoted_values(pattern: str) -> list[str]:
    return [decode_js_string(match.group(1)) for match in QUOTED_JS_STRING_RE.finditer(pattern)]


def has_cjk(value: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value))


def changed_quoted_translation(old: str, new: str) -> tuple[str, str] | None:
    old_values = quoted_values(old)
    new_values = quoted_values(new)
    if not old_values or len(old_values) != len(new_values):
        return None

    changed = [(source, target) for source, target in zip(old_values, new_values) if source != target]
    if len(changed) != 1:
        return None

    source, target = changed[0]
    if source and target and has_cjk(target):
        return source, target
    return None


def quoted_whole_translation(old: str, new: str) -> tuple[str, str] | None:
    if old.startswith('"') and old.endswith('"') and new.startswith('"') and new.endswith('"'):
        source = decode_js_string(old[1:-1])
        target = decode_js_string(new[1:-1])
        if source != target and has_cjk(target):
            return source, target
    return None


def patch_translation_memory() -> dict[str, str]:
    memory: dict[str, str] = {}
    try:
        import patch_chunks_zh_cn
    except (ImportError, KeyError, OSError):
        return memory

    for replacements in patch_chunks_zh_cn.PATCHES.values():
        for old, new in replacements:
            translated = quoted_whole_translation(old, new) or changed_quoted_translation(old, new)
            if translated:
                memory.setdefault(translated[0], translated[1])
    return memory


def translation_memory(installed_resources: Path) -> dict[str, str]:
    memory: dict[str, str] = patch_translation_memory()
    for spec in RESOURCE_PAIRS.values():
        local_path = spec["local"]
        en_path = installed_resources.parent / spec["installed_en"]
        if not local_path.exists() or not en_path.exists():
            continue
        local_data = load_json(local_path)
        en_data = load_json(en_path)
        for key, source in en_data.items():
            translated = local_data.get(key)
            if (
                isinstance(source, str)
                and isinstance(translated, str)
                and translated
                and source != translated
                and not is_placeholder_translation(translated)
            ):
                memory.setdefault(source, translated)
    return memory


def looks_technical_or_placeholder(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    if EXACT_TRANSLATIONS.get(stripped) == stripped:
        return True
    if stripped in KNOWN_OK_EXACT:
        return True
    if stripped.startswith(("http://", "https://")):
        return True
    if re.fullmatch(r"\{[^{}]+\}", stripped):
        return True
    if PLACEHOLDER_ONLY_RE.match(stripped):
        return True
    if re.fullmatch(r"[A-Za-z]:[\\/].+", stripped):
        return True
    if stripped.startswith(("~/", "./", "../", "/", "[")):
        return True
    if re.fullmatch(r"\{[^{}]+\}\s*(ms|FPS|tokens?)", stripped, flags=re.IGNORECASE):
        return True
    if re.fullmatch(r"[~×x→·\s{}#%$.,:+\-_/()\\[\]<>|A-Z0-9]+", stripped):
        return True
    if re.fullmatch(r"[A-Z0-9_./:+-]{2,}", stripped):
        return True
    return False


def untranslated_words(value: str) -> list[str]:
    words = []
    for word in re.findall(r"[A-Za-z][A-Za-z0-9.+-]*", value):
        normalized = word.strip(".+-").lower()
        if len(normalized) < 3:
            continue
        if normalized in ALLOWED_ENGLISH_WORDS:
            continue
        words.append(word)
    return words


def translation_looks_complete(value: str) -> bool:
    if looks_technical_or_placeholder(value):
        return True
    if not has_cjk(value):
        return False
    return len(untranslated_words(value)) <= 1


def translate_fragment(value: str) -> str:
    translated = value.strip()
    if translated in EXACT_TRANSLATIONS:
        return EXACT_TRANSLATIONS[translated]

    for source, target in sorted(FRAGMENT_TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True):
        translated = re.sub(rf"\b{re.escape(source)}\b", target, translated, flags=re.IGNORECASE)
    return translated


def complete_fragment(value: str) -> str | None:
    translated = translate_fragment(value)
    if translated != value and translation_looks_complete(translated):
        return translated
    return None


def pattern_translation(value: str) -> str | None:
    simple_patterns: list[tuple[str, str]] = [
        (r"^Add (.+)$", "添加{part}"),
        (r"^Set up (.+)$", "设置{part}"),
        (r"^Manage (.+)$", "管理{part}"),
        (r"^Request (.+)$", "请求{part}"),
        (r"^Authorize (.+)$", "授权{part}"),
        (r"^Enable (.+)$", "启用{part}"),
        (r"^Disable (.+)$", "禁用{part}"),
        (r"^Use (.+)$", "使用{part}"),
        (r"^Select (.+)$", "选择{part}"),
        (r"^Filter (.+)$", "筛选{part}"),
        (r"^Collapse (.+)$", "折叠{part}"),
        (r"^Expand (.+)$", "展开{part}"),
        (r"^Copy (.+)$", "复制{part}"),
        (r"^View (.+)$", "查看{part}"),
        (r"^Open (.+)$", "打开{part}"),
        (r"^Download as (.+)$", "下载为 {part}"),
        (r"^Remove (.+)$", "移除{part}"),
        (r"^Refresh (.+)$", "刷新{part}"),
        (r"^Hide (.+)$", "隐藏{part}"),
        (r"^Show (.+)$", "显示{part}"),
        (r"^Save (.+)$", "保存{part}"),
        (r"^Run (.+)$", "运行{part}"),
        (r"^Start (.+)$", "开始{part}"),
        (r"^Back to (.+)$", "返回{part}"),
        (r"^Next: (.+)$", "下一步：{part}"),
        (r"^No (.+)$", "没有{part}"),
        (r"^Invalid (.+)$", "无效{part}"),
        (r"^Loading (.+)…$", "正在加载{part}…"),
        (r"^Reading (.+)$", "正在读取{part}"),
        (r"^Reading (.+)…$", "正在读取{part}…"),
        (r"^Checking (.+)…$", "正在检查{part}…"),
        (r"^Searching(.+)?…$", "正在搜索…"),
        (r"^Scanning(.+)?…$", "正在扫描…"),
        (r"^Editing (.+)…$", "正在编辑{part}…"),
        (r"^Writing (.+)…$", "正在写入{part}…"),
        (r"^Using (.+)…$", "正在使用{part}…"),
        (r"^Starting (.+)…$", "正在启动{part}…"),
    ]
    for pattern, template in simple_patterns:
        match = re.match(pattern, value, flags=re.IGNORECASE)
        if not match:
            continue
        part = ""
        if match.lastindex:
            raw_part = match.group(1) or ""
            part = complete_fragment(raw_part) or translate_fragment(raw_part)
            if untranslated_words(part) and not looks_technical_or_placeholder(part):
                continue
        translated = template.format(part=part)
        if translation_looks_complete(translated):
            return translated

    copied = re.match(r"^(.+) copied to clipboard\.$", value, flags=re.IGNORECASE)
    if copied:
        part = complete_fragment(copied.group(1)) or translate_fragment(copied.group(1))
        translated = f"{part}已复制到剪贴板。"
        if translation_looks_complete(translated):
            return translated

    match = re.match(r"^\{(.+)\} configuration$", value, flags=re.IGNORECASE)
    if match:
        return f"{{{match.group(1)}}} 配置"

    for pattern, template in [
        (r"^(.+) updated$", "{part}已更新"),
        (r"^(.+) installed$", "{part}已安装"),
        (r"^(.+) saved\.$", "{part}已保存。"),
        (r"^(.+) deleted$", "{part}已删除"),
        (r"^Downloaded (.+)$", "已下载{part}"),
        (r"^Copied (.+)$", "已复制{part}"),
        (r"^Failed to save (.+)\. Check your inputs and try again\.$", "保存{part}失败。请检查输入后重试。"),
        (r"^Failed to remove (.+)\.$", "移除{part}失败。"),
        (r"^Failed to update (.+)\. You can try again\.$", "更新{part}失败。你可以重试。"),
        (r"^Couldn’t load (.+)\. Try again\.$", "无法加载{part}。请重试。"),
        (r"^Can't reach (.+) — check your connection\.$", "无法连接{part}；请检查连接。"),
    ]:
        match = re.match(pattern, value, flags=re.IGNORECASE)
        if not match:
            continue
        part = complete_fragment(match.group(1)) or translate_fragment(match.group(1))
        translated = template.format(part=part)
        if translation_looks_complete(translated):
            return translated

    return None


def apply_phrase_rules(value: str) -> str:
    translated = value
    for source, target in sorted(PHRASE_REPLACEMENTS, key=lambda item: len(item[0]), reverse=True):
        translated = re.sub(re.escape(source), target, translated, flags=re.IGNORECASE)
    translated = translated.replace(" can't ", " 不能 ")
    translated = translated.replace(" can’t ", " 不能 ")
    translated = translated.replace("Couldn't", "无法")
    translated = translated.replace("couldn't", "无法")
    translated = translated.replace("Don't", "不要")
    translated = translated.replace("don't", "不要")
    translated = translated.replace("isn't", "不是")
    translated = translated.replace("isn’t", "不是")
    translated = translated.replace("—", "—")
    translated = re.sub(r"\s+([，。！？；：、）])", r"\1", translated)
    translated = re.sub(r"([（])\s+", r"\1", translated)
    translated = re.sub(r"\s+", " ", translated)
    return translated.strip()


def fallback_translation(value: str, mark_untranslated: bool = False) -> str:
    if looks_technical_or_placeholder(value):
        return value
    patterned = pattern_translation(value)
    if patterned:
        return patterned
    translated = apply_phrase_rules(value)
    if translated != value and translation_looks_complete(translated):
        return translated
    if not mark_untranslated:
        return value
    if len(value) <= 36 and ASCII_WORD_RE.search(value):
        return f"待翻译：{value}"
    return f"待补充翻译：{value}"


def translate_value(value: object, memory: dict[str, str], mark_untranslated: bool = False) -> object:
    if not isinstance(value, str):
        return value
    if value in EXACT_TRANSLATIONS:
        return EXACT_TRANSLATIONS[value]
    if value in memory:
        return memory[value]
    return fallback_translation(value, mark_untranslated=mark_untranslated)


def canonicalize_existing_translation(source: object, value: object) -> object:
    """Repair stable terminology drift in translations carried across releases."""
    if not isinstance(source, str) or not isinstance(value, str):
        return value

    source_lower = source.lower()
    translated = value

    if re.search(r"\brunners?\b", source_lower):
        translated = translated.replace("跑步者", "运行器")
    if re.search(r"\b(?:repos?|repositor(?:y|ies))\b", source_lower):
        translated = translated.replace("存储库", "仓库")
    if re.search(r"\bartifacts?\b", source_lower):
        translated = translated.replace("神器", "工件").replace("Artifact", "工件").replace("artifact", "工件")
    if "compartment" in source_lower:
        translated = translated.replace("车厢", "隔离区").replace("隔间", "隔离区")
    if re.search(r"\btools?\b", source_lower):
        translated = translated.replace("刀具", "工具")
    if re.search(r"\bdecks?\b", source_lower):
        translated = translated.replace("甲板", "演示文稿").replace("套牌", "演示文稿")
    if "anthropic" in source_lower:
        translated = translated.replace("人类", "Anthropic")
    if re.search(r"\bmembers?\b", source_lower):
        translated = translated.replace("会员", "成员")
    if re.search(r"\bcredits?\b", source_lower):
        translated = translated.replace("使用积分", "用量额度").replace("积分", "额度").replace("学分", "额度")
    if re.search(r"\b(?:apps?|application)\b", source_lower):
        translated = translated.replace("应用程序", "应用")
    if re.search(r"\bPro\b", source):
        translated = translated.replace("专业版", "Pro")
    if re.search(r"\bMax\b", source):
        translated = translated.replace("最高", "Max").replace("最大", "Max")
    if "marketplace" in source_lower:
        translated = translated.replace("market位置", "市场")
    if "usage" in source_lower and "site usage" not in source_lower:
        translated = translated.replace("使用情况", "用量")
    if re.search(r"\bmodels?\b", source_lower):
        translated = translated.replace("型号", "模型")
    if "check in" in source_lower:
        translated = translated.replace("请先签入，然后再继续", "请先向我确认，再继续")
    if "{period, select, daily {daily }" in source:
        translated = translated.replace("daily {日常的}", "daily {每日}")
    if re.search(r"\bsessions?\b", source_lower):
        translated = translated.replace(
            "one {# 会议} other {# 会话}",
            "one {# 个会话} other {# 个会话}",
        )
    translated = translated.replace("计划计划", "计划")
    return translated


def sync_resources(app_dir: Path, dry_run: bool = False, mark_untranslated: bool = False) -> dict[str, dict[str, int]]:
    installed_resources = app_dir / "resources"
    memory = translation_memory(installed_resources)
    summary: dict[str, dict[str, int]] = {}

    for name, spec in RESOURCE_PAIRS.items():
        local_path = spec["local"]
        installed_en = installed_resources.parent / spec["installed_en"]
        local_data = load_json(local_path)
        if not installed_en.exists():
            summary[name] = {
                "en": 0,
                "zh": len(local_data),
                "added": 0,
                "updated": 0,
                "reused": 0,
                "untranslated": 0,
                "missing_after": 0,
                "extra": len(local_data),
                "skipped_missing_en": 1,
            }
            continue
        en_data = load_json(installed_en)
        added = 0
        reused = 0
        updated = 0
        untranslated = 0
        for key, source in en_data.items():
            current = local_data.get(key)
            if key in local_data and not is_placeholder_translation(current) and current != source:
                translated = EXACT_TRANSLATIONS.get(source) if isinstance(source, str) else None
                if translated is None:
                    translated = canonicalize_existing_translation(source, current)
                if translated is None or translated == current:
                    continue
            else:
                translated = translate_value(source, memory, mark_untranslated=mark_untranslated)
            if is_placeholder_translation(current) and is_placeholder_translation(translated):
                translated = translate_value(placeholder_source(current), memory, mark_untranslated=mark_untranslated)
            if key in local_data and current == translated:
                continue
            if isinstance(source, str) and isinstance(translated, str) and translated == memory.get(source):
                reused += 1
            if isinstance(source, str) and translated == source and not looks_technical_or_placeholder(source):
                untranslated += 1
            if key in local_data:
                updated += 1
            else:
                added += 1
            local_data[key] = translated

        if not dry_run and (added or updated):
            write_json(local_path, local_data)
        summary[name] = {
            "en": len(en_data),
            "zh": len(local_data),
            "added": added,
            "updated": updated,
            "reused": reused,
            "untranslated": untranslated,
            "missing_after": len(set(en_data) - set(local_data)),
            "extra": len(set(local_data) - set(en_data)),
            "skipped_missing_en": 0,
        }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync missing zh-CN resource keys from installed Claude")
    parser.add_argument("--app-dir", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--mark-untranslated", action="store_true", help="write 待翻译 markers for review instead of English fallback")
    args = parser.parse_args()

    app_dir = Path(args.app_dir) if args.app_dir else patch_windowsapps_json_only.find_claude_package()
    if not app_dir:
        raise SystemExit("Claude app directory not found; pass --app-dir")

    summary = sync_resources(app_dir, dry_run=args.dry_run, mark_untranslated=args.mark_untranslated)
    print(f"Claude app: {app_dir}")
    for name, info in summary.items():
        skipped = ""
        if info.get("skipped_missing_en"):
            skipped = f" skipped_missing_en={info['skipped_missing_en']}"
        print(
            f"{name}: en={info['en']} zh={info['zh']} "
            f"added={info['added']} updated={info['updated']} reused={info['reused']} untranslated={info['untranslated']} "
            f"missing_after={info['missing_after']} extra={info['extra']}{skipped}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
