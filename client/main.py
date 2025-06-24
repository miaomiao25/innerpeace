import socket
import json
import argparse
import threading
import time
import sys
import random


class GameClient:
    def __init__(self, server_host, server_port, player_id):
        self.max_rounds = None
        self.server_host = server_host
        self.server_port = server_port
        self.player_id = player_id
        self.team_name = "A"
        self.client_socket = None
        self.running = False
        self.registered = False
        self.game_active = False
        self.current_round = 0

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_host, self.server_port))
            self.running = True
            print(f"Connected to server at {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def register(self):
        if not self.client_socket:
            print("Not connected to server")
            return False

        register_msg = json.dumps({
            "msgName": "register",
            "msgData": {
                "playerId": self.player_id,
                "playerName": self.player_id,
                "team_name": self.team_name
            }
        })

        try:
            self.client_socket.send(register_msg.encode())
            print(f"Sent registration for team: {self.player_id}")
            self.registered = True
            return True
        except Exception as e:
            print(f"Registration failed: {e}")
            return False

    def start(self):
        if not self.connect():
            return

        # 注册队伍
        if not self.register():
            return

        # 启动消息接收线程
        receiver = threading.Thread(target=self.receive_messages)
        receiver.daemon = True
        receiver.start()

        # 保持主线程运行
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.shutdown()

    def receive_messages(self):
        while self.running:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    print("Server disconnected")
                    self.shutdown()
                    return

                try:
                    message = json.loads(data.decode())
                    self.handle_message(message)
                except json.JSONDecodeError:
                    print("Received invalid JSON")
            except socket.error as e:
                print(f"Socket error: {e}")
                self.shutdown()
                return

    def handle_message(self, message):
        msg_name = message.get('msgName')
        msg_data = message.get('msgData')
        print(f"Received message: {message}")

        if msg_name == "gamestart":
            self.handle_gamestart(msg_data)
        elif msg_name == "inquiry":
            self.handle_inquiry(msg_data)
        elif msg_name == "gameover":
            self.handle_gameover(msg_data)

    def handle_gamestart(self, msg_data):
        self.game_active = True
        self.max_rounds = msg_data.get('max_rounds', 500)
        print(f"Game starting! Max rounds: {self.max_rounds}")

        # 发送准备消息
        ready_msg = json.dumps({
            "msgName": "gameready",
            "msgData": {
                "playerId": self.player_id,
                "status": "ready"}
        })

        try:
            self.client_socket.send(ready_msg.encode())
            print("Sent gameready message")
        except Exception as e:
            print(f"Failed to send gameready: {e}")

    def handle_inquiry(self, msg_data):
        if not self.game_active:
            return

        self.current_round = msg_data.get('round', 0)
        print(f"Round {self.current_round} inquiry received")

        # 模拟游戏逻辑：生成随机响应
        response_data = {
            "move": random.choice(["up", "down", "left", "right"]),
            "score": random.randint(1, 100)
        }

        # 发送响应消息
        response_msg = json.dumps({
            "msgName": "response",
            "msgData": {
                "playerId": self.player_id,
                "round": self.current_round,
                "data": response_data}
        })

        try:
            self.client_socket.send(response_msg.encode())
            print(f"Sent response for round {self.current_round}")
        except Exception as e:
            print(f"Failed to send response: {e}")

    def handle_gameover(self, msg_data):
        reason = msg_data.get('reason', "unknown")
        total_rounds = msg_data.get('total_rounds', 0)
        print(f"Game over: {reason}. Total rounds: {total_rounds}")
        self.shutdown()

    def shutdown(self):
        self.running = False
        self.game_active = False
        if self.client_socket:
            try:
                self.client_socket.close()
            finally:
                pass
        print("Client shutdown")
        sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Game Client')
    parser.add_argument('-s', '--server', default='127.0.0.1', help='Server IP (default: 127.0.0.1)')
    parser.add_argument('-p', '--port', type=int, default=6001, help='Server port (default: 6001)')
    parser.add_argument('-i', '--id', required=True, help='Team ID')

    args = parser.parse_args()

    client = GameClient(
        server_host=args.server,
        server_port=args.port,
        player_id=args.id
    )

    client.start()
