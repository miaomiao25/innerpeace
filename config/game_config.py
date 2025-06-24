# config.py - 全局参数配置

class GameConfig:
    # 地图尺寸
    FIELD_WIDTH = 91
    FIELD_HEIGHT = 61

    # 动作类型
    ACTION_TYPES = [
        "run",  # 移动1格
        "rush",  # 移动2格
        "steal",  # 抢断距离0-1
        "slide",  # 铲球距离2
        "shortPass",  # 短传距离1-35
        "longPass",  # 长传距离5-45
        "nope"  # 原地不动
    ]

    # 体力消耗
    STAMINA_COST = {
        "run": 8,
        "rush": 40,
        "steal": 100,
        "slide": 300,
        "shortPass": 8,
        "longPass": 80,
        "nope": -40  # 恢复体力
    }

    # 最大体力值
    MAX_STAMINA = 7600

    # 最大僵直回合
    MAX_STUN_ROUNDS = 3

    # 最大进球数
    MAX_SCORE = 100

    # 最大回合数
    MAX_TURNS = 500

    # 传球参数
    SHORT_PASS_MAX_DISTANCE = 35
    LONG_PASS_MIN_DISTANCE = 5
    LONG_PASS_MAX_DISTANCE = 45
