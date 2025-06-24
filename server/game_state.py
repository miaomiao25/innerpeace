class Pos:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class StaticStarInfo:
    def __init__(self, star_id, stamina=7600, run=8, rush=40, short_pass=8, long_pass=40, shot=100, steal=100,
                 slide=200):
        self.star_id = star_id
        self.stamina = stamina
        self.run = run
        self.rush = rush
        self.shortPass = short_pass
        self.longPass = long_pass
        self.shot = shot
        self.steal = steal
        self.slide = slide
        self.overall = stamina + run + rush + short_pass + long_pass + shot + steal + slide


class StaticPlayerInfo:
    def __init__(self, player_id, side, player_name, team_name):
        self.player_id = player_id
        self.player_name = player_name
        self.team_name = team_name
        self.side = side
        if team_name == "A":
            self.stars = [StaticStarInfo(1), StaticStarInfo(2), StaticStarInfo(3), StaticStarInfo(4), StaticStarInfo(5)]
        elif team_name == "B":
            self.stars = [StaticStarInfo(6), StaticStarInfo(7), StaticStarInfo(8), StaticStarInfo(9),
                          StaticStarInfo(10)]


class StarStatus:
    def __init__(self):
        self.state = "normal"
        self.cd_remain = 0


class StarInfo:
    def __init__(self, star_id):
        self.star_id = star_id
        self.pos = None
        self.stamina = 0
        self.star_state = StarStatus()


class PlayerInfo:
    def __init__(self, player_id, side, team_name):
        self.player_id = player_id
        self.side = side
        if team_name == "A":
            self.stars = [StarInfo(1), StarInfo(2), StarInfo(3), StarInfo(4), StarInfo(5)]
        elif team_name == "B":
            self.stars = [StarInfo(6), StarInfo(7), StarInfo(8), StarInfo(9), StarInfo(10)]


class BallPassInfo:
    def __init__(self, start_pos, target_pos, round_begin, round_end, path):
        self.start_pos = start_pos
        self.target_pos = target_pos
        self.round_begin = round_begin
        self.round_end = round_end
        self.path = path


class BallInfo:
    def __init__(self):
        self.status = "stand"
        self.pos = Pos(-1, -1)
        self.player_id = -1
        self.star_id = -1
        self.pass_info = None


class RoundInfo:
    def __init__(self):
        self.ball_info = None
        self.player_info = []


class GameState:
    def __init__(self):
        self.static_player_info = []
        self.round_info = RoundInfo()
