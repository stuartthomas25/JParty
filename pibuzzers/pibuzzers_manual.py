from websocket import create_connection
import json

host_ip = "10.0.0.112"

response = ""

valid_responses = ["red", "green", "blue", "yellow"]
sockets = {}
  
def sendBuzz(color):
  if color not in sockets:
    ws = create_connection("ws://" + host_ip + ":8080/buzzersocket")
    connectPayload = json.dumps({'buzzerColor': color, 'message': 'CHECK_IF_EXISTS', 'text': ''})
    ws.send(connectPayload)
    server_res = ws.recv()
    print("server res: " + server_res)
    res_json = json.loads(server_res)
    if res_json["message"] == "EXISTS":
      sockets[color] = ws # Successfully connected for this buzzer color


  if color in sockets:
    print("Sending " + color + " buzz...")
    value = json.dumps({'buzzerColor': color, 'message': 'BUZZ', 'text': ''})
    sockets[color].send(value)
    print("Done.")

while response != "quit":
  response = input("Buzz a color: ")
  if response not in valid_responses:
    print("Not a valid response, please enter one of:")
    print(*valid_responses, sep = ", ")
  else:
    # Valid response
    sendBuzz(response)