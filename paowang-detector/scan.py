#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聊天记录扫描器 · 炮王识别

用法：
    python scan.py chat.txt            # 扫描聊天记录
    python scan.py chat.txt -v         # 显示命中的原句
    python scan.py chat.txt --json     # 输出 JSON（便于二次处理）

说明：
    本脚本只做关键词初筛，输出的是"值得看一眼的地方"，不是结论。
    最终判断请对照 检测工具/聊天检测SOP.md 走完八步流程。
    命中不等于定罪 —— 一次是表达，三次才是方法。
"""

import argparse
import json
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# (模式编号, 模式名, 权重, [关键词])
PATTERNS = [
    (1, "纯情宣言", 1.0, ["我只谈恋爱", "不玩暧昧", "我很挑", "不是谁都", "我是认真的", "我不随便"]),
    (2, "前任切割", 1.0, ["断干净", "早就不联系", "不会复合", "分了很久", "别提她", "都过去了"]),
    (3, "人设三件套", 2.0, ["管得严", "管得死", "要报备", "周末要回家", "我爸的", "生活费", "被罚",
                            "中考", "高考", "年级前"]),
    (5, "撒娇索取连招", 1.0, ["留一个嘛", "想要嘛", "好不好", "行不行嘛", "哎哟喂", "一点面子不给", "你好拽"]),
    (6, "主动报备", 1.0, ["到健身房", "在吃饭", "到家了", "回学校", "我到啦", "刚到"]),
    (7, "固定约会日", 1.0, ["每周", "固定", "这周不行", "老规矩", "下次吧", "家里有事", "回不去"]),
    (8, "深夜真心话", 1.0, ["真心话", "大冒险", "你先问", "说实话", "走心", "睡不着", "聊会儿"]),
    (9, "共同仪式", 1.0, ["一起存钱", "小荷包", "我们的", "每天存", "打卡", "我们的歌"]),
    (10, "例外感", 1.0, ["和别人不一样", "跟别人不一样", "你是例外", "跟她们不同", "只有你能"]),
    (11, "小作文道歉", 1.0, ["我知道你现在", "我们能不能", "再给我一次", "我会改", "我和爸妈说了",
                             "但是我想说", "其实我"]),
    (12, "经济暗示", 1.0, ["手头紧", "最近没钱", "生活费还没到", "这个月有点", "我该收下", "我这个坏了"]),
    (13, "不确认关系", 2.0, ["顺其自然", "我们先这样", "不着急", "慢慢来", "不用定义", "感觉对了就行"]),
    (14, "被抓包话术链", 2.0, ["我记得你不是说", "那你呢", "你不也", "我会改一点", "也不知道能不能",
                               "我没有喝", "我没做", "不是你想的那样", "他去的", "我兄弟",
                               "爱是什么是什么"]),
    (15, "欲拒还迎收钱", 1.0, ["不敢领", "无功不受禄", "这不合适", "你这是干嘛"]),
    (16, "小额拒收", 1.0, ["这个不要", "别转了", "就算了"]),
    (17, "服从性测试", 1.0, ["叫我主人", "叫爸爸", "叫哥哥", "喊一声", "下次语音叫", "发语音", "听话", "叫一声"]),
    (18, "占有欲玩笑", 1.0, ["我的人", "不允许", "我的小三", "你别去"]),
]

# 组合信号：(名称, 需要同时命中的模式编号集合, 提示)
COMBOS = [
    ("绑定但不给名分", {13, 6}, "不确认关系 + 天天报备：在绑定你，但不给你位置"),
    ("时间块管理老手", {7, 14}, "固定时间 + 完整危机话术：有经验"),
    ("人设与行为矛盾", {3, 12}, "家里有钱 + 反复说紧：人设撑不住"),
    ("标准安抚流水线", {10, 11}, "例外感 + 小作文：出事后的标准处理流程"),
    ("控制型前兆", {17, 18}, "服从性测试 + 占有欲：关系在往控制方向走"),
    ("情感金钱双索取", {5, 15}, "撒娇索取 + 欲拒还迎收钱：两条线同时在要"),
]


def scan(text, verbose=False):
    hits = []
    total = 0.0
    for num, name, weight, words in PATTERNS:
        matched = {}
        for w in words:
            m = re.search(re.escape(w), text)
            if m and w not in matched:
                s = max(0, m.start() - 20)
                e = min(len(text), m.end() + 20)
                matched[w] = text[s:e].replace("\n", " ").strip()
        if matched:
            # 同一模式多词命中加权，封顶 3 分
            score = min(3, 1 + len(matched) // 2)
            weighted = score * weight
            total += weighted
            hits.append({
                "模式": f"{num} {name}",
                "命中次数": len(matched),
                "基础分": score,
                "加权分": round(weighted, 1),
                "例句": list(matched.values())[:3] if verbose else [],
            })
    total = round(total, 1)

    if total <= 8:
        level, advice = "🟢 低风险", "未见明显模式，正常相处，保持观察"
    elif total <= 18:
        level, advice = "🟡 需观察", "做 2-3 个验证动作再判断"
    elif total <= 30:
        level, advice = "🟠 高度可疑", "严肃谈话 + 要求明确关系"
    else:
        level, advice = "🔴 基本确认", "建议退出，先保护好自己"

    combos = []
    hit_nums = {int(h["模式"].split()[0]) for h in hits}
    for cname, need, tip in COMBOS:
        if need.issubset(hit_nums):
            combos.append({"组合": cname, "提示": tip})

    return {"总分": total, "等级": level, "建议": advice, "命中": hits, "组合信号": combos}


def main():
    ap = argparse.ArgumentParser(description="聊天记录扫描器 · 炮王识别")
    ap.add_argument("file", help="聊天记录文本文件（utf-8）")
    ap.add_argument("-v", "--verbose", action="store_true", help="显示命中原句")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    try:
        with open(args.file, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"找不到文件：{args.file}")
        sys.exit(1)

    r = scan(text, args.verbose)

    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return

    print("=" * 46)
    print(f"  检测结果：{r['等级']}   总分 {r['总分']}")
    print("=" * 46)
    print(f"  建议：{r['建议']}\n")

    if not r["命中"]:
        print("  未命中任何模式。样本可能不足，或对方确实没什么套路。\n")
    else:
        print("  命中模式：")
        for h in sorted(r["命中"], key=lambda x: -x["加权分"]):
            print(f"    · {h['模式']:<16} 命中{h['命中次数']}次   加权分 {h['加权分']}")
            if args.verbose:
                for ex in h["例句"]:
                    print(f"        「…{ex}…」")
        print()

    if r["组合信号"]:
        print("  ⚠ 组合信号：")
        for c in r["组合信号"]:
            print(f"    · {c['组合']} —— {c['提示']}")
        print()

    print("  说明：本脚本只做关键词初筛，不是结论。")
    print("        请对照 检测工具/聊天检测SOP.md 走完八步流程。")
    print("        一次是表达，三次才是方法。")


if __name__ == "__main__":
    main()
