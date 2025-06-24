import argparse
import json
import socket
import sys
import time
from threading import Thread
from game_state import *
import select


class GameServer:
    def __init__(self, host='0.0.0.0', port=6001, timeout=30, teams=None):
        self.awaiting_responses = None
        self.round_responses = None
        self.round_start_time = None
        self.host = host
        self.port = port
        self.register_timeout = timeout
        self.required_teams = teams.split(',') if teams else []
        self.registered_teams = {}
        self.ready_teams = set()
        self.server_socket = None
        self.all_sockets = []
        self.running = False
        self.game_started = False
        self.round_count = 0
        self.max_rounds = 500
        self.round_timeout = 0.5  # 0.5秒回合超时
        self.team_timeout_times = {}
        self.game_state = GameState()

    def start(self):
        # 创建服务器socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.server_socket.setblocking(False)

        self.all_sockets = [self.server_socket]
        self.running = True

        print(f"Server started on {self.host}:{self.port}")
        print(f"Waiting for teams: {', '.join(self.required_teams)}")
        print(f"Registration timeout: {self.register_timeout} seconds")

        # 启动注册超时计时器
        Thread(target=self.registration_timer).start()

        # 主事件循环
        while self.running:
            try:
                # 使用select处理多路IO
                readable, _, _ = select.select(self.all_sockets, [], [], 1)

                for sock in readable:
                    if sock is self.server_socket:
                        # 处理新连接
                        self.accept_new_connection()
                    else:
                        # 处理客户端消息
                        self.handle_client_message(sock)

            except Exception as e:
                print(f"Error: {e}")
                continue

    def registration_timer(self):
        # 等待注册超时
        time.sleep(self.register_timeout)

        if not self.running:
            return

        # 检查是否所有队伍都已注册
        missing_teams = [t for t in self.required_teams if t not in self.registered_teams]

        if missing_teams:
            print(f"Registration timeout. Missing teams: {', '.join(missing_teams)}")
            self.shutdown()
        elif self.required_teams:
            print("All teams registered. Starting game...")
            self.start_game()

    def accept_new_connection(self):
        try:
            client_socket, addr = self.server_socket.accept()
            client_socket.setblocking(False)
            self.all_sockets.append(client_socket)
            print(f"New connection from {addr}")
        except socket.error:
            pass

    def handle_client_message(self, client_socket):
        try:
            data = client_socket.recv(4096)
            if not data:
                # 客户端断开连接
                self.remove_client(client_socket)
                return

            try:
                message = json.loads(data.decode())
                self.process_message(client_socket, message)
            except json.JSONDecodeError:
                print("Received invalid JSON")
        except socket.error:
            self.remove_client(client_socket)

    def process_message(self, client_socket, message):
        msg_name = message.get('msgName')
        msg_data = message.get('msgData')
        player_id = msg_data.get('playerId')

        if not player_id:
            print("Missing player_id in message")
            return

        # 处理注册消息
        if msg_name == 'register':
            player_name = msg_data.get('playerName')
            team_name = msg_data.get("team_name")
            if player_id in self.registered_teams:
                print(f"Team {player_id} already registered")
                return
            if player_id == self.required_teams[0]:
                side = 'left'
            else:
                side = 'right'
            self.game_state.static_player_info.append(StaticPlayerInfo(player_id, side, player_name, team_name))
            # 记录注册的队伍
            self.registered_teams[player_id] = client_socket
            self.team_timeout_times[player_id] = 0
            print(f"Team registered: {player_id}")
            # 检查是否所有队伍都已注册
            if all(t in self.registered_teams for t in self.required_teams):
                print("All teams registered. Starting game...")
                self.start_game()

        # 处理准备消息
        elif msg_name == 'gameready':
            print(f"Team {player_id} is ready")
            self.ready_teams.add(player_id)

            # 检查是否所有队伍都已准备
            if self.ready_teams == set(self.required_teams):
                print("All teams are ready. Starting rounds...")
                self.start_round()

        # 处理回合响应
        elif msg_name == 'response':
            if player_id in self.awaiting_responses:
                print(f"Received response from {player_id}")
                self.awaiting_responses.remove(player_id)
                self.round_responses[player_id] = message.get('data', {})

                # 游戏进行中，检查回合状态
                if self.game_started and self.round_count < self.max_rounds:
                    if not self.check_round_status(player_id):
                        return

                # 检查是否所有队伍都已响应
                if not self.awaiting_responses:
                    print("All teams responded. Processing round...")
                    self.process_round()
                    self.start_round()

    def start_game(self):
        if self.game_started:
            return
        self.game_started = True
        self.round_count = 0
        self.game_state.round_info.ball_info = BallInfo()
        self.game_state.round_info.player_info.append(
            PlayerInfo(self.required_teams[0], 'left', self.game_state.static_player_info[0].team_name))
        self.game_state.round_info.player_info.append(
            PlayerInfo(self.required_teams[1], 'right', self.game_state.static_player_info[1].team_name))

        # 发送游戏开始消息
        game_start_msg = json.dumps({
            "msgName": "gamestart",
            "msgData": {
                "max_rounds": self.max_rounds}
        }).encode()

        for player_id, sock in self.registered_teams.items():
            try:
                sock.send(game_start_msg)
                print(f"Sent gamestart to {player_id}")
            except socket.error:
                print(f"Failed to send gamestart to {player_id}")
                self.remove_client(sock)

    def reset_game(self, msg_data):
        return

    def start_round(self):
        if self.round_count >= self.max_rounds:
            self.end_game("Game completed")
            return

        self.round_count += 1
        self.round_start_time = time.time()
        self.awaiting_responses = set(self.registered_teams.keys())
        self.round_responses = {}

        print(f"\nStarting round {self.round_count}/{self.max_rounds}")

        # 发送回合查询消息
        inquiry_msg = json.dumps({
            "msgName": "inquiry",
            "msgData": {
                "round": self.round_count}
        }).encode()

        for player_id, sock in self.registered_teams.items():
            try:
                sock.send(inquiry_msg)
            except socket.error:
                print(f"Failed to send inquiry to {player_id}")
                self.remove_client(sock)

    def check_round_status(self, player_id):
        if not hasattr(self, 'round_start_time'):
            return False

        elapsed = time.time() - self.round_start_time
        if elapsed > self.round_timeout and player_id:
            print(f"Round timeout! Missing responses from: {player_id}")
            self.team_timeout_times[player_id] += 1
            if self.team_timeout_times[player_id] >= 10:
                self.end_game("Round timeout")
            return False
        return True

    def process_round(self):
        # 这里可以添加游戏逻辑，处理回合响应
        print(f"Round {self.round_count} responses received")
        # 示例：打印所有队伍的响应
        for player_id, response in self.round_responses.items():
            print(f"  {player_id}: {response}")

    def end_game(self, reason):
        print(f"Game over: {reason}")

        # 发送游戏结束消息
        game_over_msg = json.dumps({
            "msgName": "gameover",
            "msgData": {
                "reason": reason,
                "total_rounds": self.round_count}
        }).encode()

        for player_id, sock in self.registered_teams.items():
            try:
                sock.send(game_over_msg)
                print(f"Sent gameover to {player_id}")
            except socket.error:
                print(f"Failed to send gameover to {player_id}")

        self.shutdown()

    def remove_client(self, client_socket):
        if client_socket in self.all_sockets:
            self.all_sockets.remove(client_socket)

        # 从注册队伍中移除
        for player_id, sock in list(self.registered_teams.items()):
            if sock == client_socket:
                del self.registered_teams[player_id]
                if player_id in self.ready_teams:
                    self.ready_teams.remove(player_id)
                print(f"Team disconnected: {player_id}")

                # 如果有队伍断开连接，结束游戏
                if self.game_started:
                    self.end_game(f"Team {player_id} disconnected")

        try:
            client_socket.close()
        finally:
            pass

    def shutdown(self):
        print("Shutting down server...")
        self.running = False
        for sock in self.all_sockets:
            try:
                sock.close()
            finally:
                pass
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Game Server')
    parser.add_argument('-p', '--port', type=int, default=6001, help='Listening port (default: 6001)')
    parser.add_argument('-l', '--host', default='0.0.0.0', help='Listening IP (default: 0.0.0.0)')
    parser.add_argument('-c', '--timeout', type=int, default=30, help='Registration timeout in seconds (default: 30)')
    parser.add_argument('-C', '--teams', help='Comma-separated team IDs (e.g., "team1,team2")')

    args = parser.parse_args()

    if args.teams and len(args.teams.split(',')) < 2:
        print("Error: At least two team IDs required for -C argument")
        sys.exit(1)

    server = GameServer(
        host=args.host,
        port=args.port,
        timeout=args.timeout,
        teams=args.teams
    )

    try:
        server.start()
    except KeyboardInterrupt:
        server.shutdown()
