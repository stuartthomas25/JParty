from websocket import create_connection
import functools
import RPi.GPIO as GPIO
import json
import time

host_ip = "10.0.0.112"
sockets = {}
GPIO.setmode(GPIO.BCM)

buzzers = [
  {
    "color": "red",
    "button_pin": 21,
    "led_pin": 26,
  },
  {
    "color": "blue",
    "button_pin": 20,
    "led_pin": 19,
  },
  {
    "color": "yellow",
    "button_pin": 16,
    "led_pin": 13,
  },
  {
    "color": "green",
    "button_pin": 12,
    "led_pin": 6,
  },
]
  
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

def main():
  for buzzer in buzzers:
    GPIO.setup(buzzer["button_pin"], GPIO.IN)
    GPIO.add_event_detect(buzzer["button_pin"], GPIO.RISING, callback=functools.partial(sendBuzz, color=buzzer["color"]))

  while True:
    time.sleep(10)

if __name__ == "__main__":
  main()