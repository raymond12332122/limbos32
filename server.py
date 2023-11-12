import socketserver
from json import loads, dumps
from typing import Any
from time import time
from random import choice, seed

SC_WIDTH, SC_HEIGHT = 1920, 1080
W_WIDTH, W_HEIGHT = 260, 260

seed(0xF0C_5)  # FOCUS

step_map = {
    # 0: {0: 4, 1: 5, 2: 6, 3: 7, 4: 0, 5: 1, 6: 2, 7: 3},
    # 1: {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 0},
    # 2: {0: 7, 1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6},
    # 3: {0: 5, 1: 4, 4: 1, 5: 0, 2: 7, 3: 6, 6: 3, 7: 2},
    # 4: {0: 3, 1: 2, 2: 1, 3: 0, 4: 7, 5: 6, 6: 5, 7: 4},
    # 5: {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1, 7: 0},
    # 6: {0: 1, 1: 5, 5: 4, 4: 0, 2: 3, 3: 7, 7: 6, 6: 2},
    # 7: {1: 0, 5: 1, 4: 5, 0: 4, 3: 2, 7: 3, 6: 7, 2: 6}
    8: {1: 0, 5: 1, 4: 5, 0: 4, 2: 3, 3: 7, 7: 6, 6: 2}
}


def lerp(p1: list, p2: list, amt: float):
    return [p1[x] * (1 - amt) + p2[x] * amt for x in range(len(p1))]


def get_static_pos(client_id: int):
    return [
        int(SC_WIDTH / 2 - W_WIDTH * 2 - 40 + (client_id % 4) * (W_WIDTH + 20)),
        int(SC_HEIGHT / 2 - W_HEIGHT - 20 + (W_HEIGHT + 40) * (client_id // 4))
    ]


def get_pos(client_id: int, current_time: float, steps: list):
    music_bop_time = 3.4
    step_speed = 60/200

    if current_time < music_bop_time:
        return get_static_pos(client_id)

    running_time = current_time - music_bop_time

    completed_steps = steps[:int(running_time / step_speed)]
    try:
        current_step = steps[int(running_time / step_speed)]
    except IndexError:
        current_step = None

    spoofed_id = client_id
    for step in completed_steps:
        spoofed_id = step_map[step][spoofed_id]
    if current_step is None:
        return get_static_pos(spoofed_id)
    lerped = lerp(
        get_static_pos(spoofed_id),
        get_static_pos(step_map[current_step][spoofed_id]),
        (running_time / step_speed) % 1)
    # print(spoofed_id, step_map[current_step][spoofed_id])
    return lerped


class TCPHandler(socketserver.BaseRequestHandler):
    clients = []
    start_time = 0
    steps = []

    def handle(self) -> None:
        if len(TCPHandler.clients) >= 8:
            return
        client_id = 0
        while True:
            if client_id not in TCPHandler.clients:
                break
            client_id += 1
        TCPHandler.clients.append(client_id)
        if client_id == 0:
            TCPHandler.steps = [choice(list(step_map.keys())) for _ in range(30)]
            TCPHandler.start_time = time()
        print(f"{client_id} joined")
        try:
            while True:
                data: dict[str, Any] = loads(self.request.recv(1024).decode('ascii'))
                if data["quit"]:
                    quit()
                current_time = time() - TCPHandler.start_time
                reply = dumps({"id": client_id, "position": get_pos(client_id, current_time, TCPHandler.steps)})
                reply = reply.encode('ascii')
                self.request.sendall(reply)
        except WindowsError:
            pass
        finally:
            if len(TCPHandler.clients) == 1:
                print("======================")
            TCPHandler.clients.remove(client_id)


def main():
    host, port = "localhost", 6666

    with socketserver.ThreadingTCPServer((host, port), TCPHandler) as server:
        server.serve_forever()


if __name__ == '__main__':
    main()
