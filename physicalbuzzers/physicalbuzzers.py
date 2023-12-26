import websocket
import json
import pygame

from websocket import create_connection

host_ip = "localhost"

buzzers = [
  "red",
  "blue",
  "yellow",
  "green",
  "white",
  "black",
]
  
def sendBuzz(color):
  try:
    ws = websocket.create_connection("ws://" + host_ip + ":8080/buzzersocket", timeout=2)
    connectPayload = json.dumps({'buzzerColor': color, 'message': 'CHECK_IF_EXISTS', 'text': ''})
    ws.send(connectPayload)
    server_res = ws.recv()
    print("server res: " + server_res)
    res_json = json.loads(server_res)
    if res_json["message"] == "EXISTS":
      print("Sending " + color + " buzz...")
      value = json.dumps({'buzzerColor': color, 'message': 'BUZZ', 'text': ''})
      ws.send(value)
      print("Done.")
    ws.close()
  except Exception as e:
    print("failed to buzz: ", e)


pygame.init()
j = pygame.joystick.Joystick(0)
j.init()

try:
    while True:
        events = pygame.event.get()
        for event in events:
            print(event.type)
            if event.type == pygame.JOYBUTTONDOWN:
                print(event.dict, event.joy, event.button, 'pressed')
                sendBuzz(buzzers[event.button])

except KeyboardInterrupt:
    print("EXITING NOW")
    j.quit()