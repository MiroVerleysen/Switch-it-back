# pylint: skip-file
from repositories.DataRepository import DataRepository
from flask import Flask, jsonify
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
from helpers.klasseIR import InfraRood
from datetime import datetime
import time
from subprocess import check_output
import threading
import serial
from helpers.klasseknop import Button
from RPi import GPIO

#LCD BEGIN
# Definieren LCD pinnen
LCD_RS = 21
LCD_E  = 20
LCD_D4 = 23
LCD_D5 = 26
LCD_D6 = 19
LCD_D7 = 13
# LCD constantes definieren
LCD_WIDTH = 16
LCD_CHR = True
LCD_CMD = False
 
LCD_LINE_1 = 0x80 # LCD RAM 1e lijn
LCD_LINE_2 = 0xC0 # LCD RAM 2e lijn
#LCD EINDE

# Definieren pinnen
relais = 6
rood = 22
groen = 27

#Globale variabelen
inschakeltijd = 0
uitschakeltijd = 0
count = 0
status = ""
huidigestroom = "0.000000"

# Oproepen klassen 
knop1 = Button(5)
ir = InfraRood(18)

#GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(relais, GPIO.OUT)
GPIO.setup(rood, GPIO.OUT)
GPIO.setup(groen, GPIO.OUT)
GPIO.setup(LCD_E, GPIO.OUT)
GPIO.setup(LCD_RS, GPIO.OUT)
GPIO.setup(LCD_D4, GPIO.OUT)
GPIO.setup(LCD_D5, GPIO.OUT)
GPIO.setup(LCD_D6, GPIO.OUT)
GPIO.setup(LCD_D7, GPIO.OUT)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Hier mag je om het even wat schrijven, zolang het maar geheim blijft en een string is'

socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

#Begin API ENDPOINTS
@app.route('/')
def hallo():
  return "Server is running, er zijn momenteel geen API endpoints beschikbaar."

@app.route('/read_all')
def ophalen_sensoren_data():
  output = DataRepository.read_all_sensors()
  return jsonify(data = output), 200

@app.route('/read_sensor/<sensorID>')
def ophalen_sensor_data(sensorID):
  output = DataRepository.read_sensor_by_id_one(sensorID)
  return jsonify(data = output), 200

@app.route('/read_sensor_recent/<sensorID>.<tijd>')
def ophalen_sensor_recent_data(sensorID, tijd):
  output = DataRepository.read_sensor_by_id_recent(sensorID, tijd)
  return jsonify(data = output), 200

@app.route('/read_gepland/<status>')
def ophalen_actuator_gepland(status):
  output = DataRepository.read_gepland(status)
  return jsonify(data = output), 200

@app.route('/read_gepland_all')
def ophalen_actuator_gepland_all():
  output = DataRepository.read_gepland_all()
  return jsonify(data = output), 200
#Einde API ENDPOINTS

#Socket
@socketio.on('connect')
def connect_message():
  print("client connected")
  emit("B2F_client_connected", "yo", broadcast = True)

@socketio.on("F2B_getdata")
def getdata():
  if GPIO.input(relais) == 1:
    socketio.emit("B2F_sentdata", {"status": 1})
  else:
    socketio.emit("B2F_sentdata", {"status": 0})
  
@socketio.on("F2B_plannen")
def plannen(data):
  global inschakeltijd
  global uitschakeltijd
  data = data.replace("T", " ")
  inschakeltijd = data[:data.find(';')]
  uitschakeltijd = data[data.find(';'):]
  uitschakeltijd = uitschakeltijd[1:]
  aantaldp = inschakeltijd.count(':')
  if (aantaldp == 1):
    inschakeltijd = inschakeltijd + ":00"
    uitschakeltijd = uitschakeltijd + ":00"
  print(inschakeltijd)
  print(uitschakeltijd)
  DataRepository.update_waarde_actuator(1,inschakeltijd ,1)
  DataRepository.update_waarde_actuator(1,uitschakeltijd ,0)
  socketio.emit("B2F_gepland")
  print("'t zit erin")
  
@socketio.on('F2B_schakelen')
def schakelmethode():
  toggle_relais()
#Einde Socket

def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(0.0005)

def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = data
  # mode = True  for character
  #        False for command
 
  GPIO.output(LCD_RS, mode) # RS
 
  # High bits
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x10==0x10:
    GPIO.output(LCD_D4, True)
  if bits&0x20==0x20:
    GPIO.output(LCD_D5, True)
  if bits&0x40==0x40:
    GPIO.output(LCD_D6, True)
  if bits&0x80==0x80:
    GPIO.output(LCD_D7, True)
 
  # Toggle 'Enable' pin
  lcd_toggle_enable()
 
  # Low bits
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x01==0x01:
    GPIO.output(LCD_D4, True)
  if bits&0x02==0x02:
    GPIO.output(LCD_D5, True)
  if bits&0x04==0x04:
    GPIO.output(LCD_D6, True)
  if bits&0x08==0x08:
    GPIO.output(LCD_D7, True)
 
  # Toggle 'Enable' pin
  lcd_toggle_enable()
 
def lcd_toggle_enable():
  # Toggle enable
  time.sleep(0.0005)
  GPIO.output(LCD_E, True)
  time.sleep(0.0005)
  GPIO.output(LCD_E, False)
  time.sleep(0.0005)
 
def lcd_string(message,line):
  # Send string to display
  message = message.ljust(LCD_WIDTH," ")
  lcd_byte(line, LCD_CMD)
  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)

def printIP():
  while True:
    ips = check_output(["hostname", "-I"]).split()[0]
    ip = str(ips)[2:-1]
    lcd_string(f"{ip}" ,LCD_LINE_1)
    time.sleep(0.5)

def lees_knop(pin):
  global count
  print("button pressed")
  kaas = DataRepository.read_status_actuator_by_id(1)
  if (count == 0):
    print(count)
    count += 1
    time.sleep(0.05)
    lcdéén()
  elif (count == 1):
    print(count)
    count += 1
    time.sleep(0.05)
    lcd_string(f"2",LCD_LINE_2)
  elif (count == 2):
    print(count)
    count = 0
    time.sleep(0.05)
    lcd_string(f"3",LCD_LINE_2)

def lcdéén():
  time.sleep(0.05)
  if GPIO.input(relais) == 1:
    lcd_string(f"status: aan",LCD_LINE_2)
  elif GPIO.input(relais) == 0:
    lcd_string(f"status: uit",LCD_LINE_2)


def startIR():
  print("Zoektocht naar IR signalen starten")
  while True:
    print("Wachtend op een signaal")
    GPIO.wait_for_edge(18, GPIO.FALLING)
    code = ir.on_ir_receive(18)
    if code:
      print(str((code)))
      DataRepository.update_waarde_sensor(1,code)
      if (code == 16753245):
        code = 1
        time.sleep(0.75)
        toggle_relais()
        print("code ok")
        time.sleep(0.05)
      else:
        print("Foute code")

def toggle_relais():
  global count
  now = datetime.now()
  formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
  count = 0
  if GPIO.input(relais) == 1:
    socketio.emit("B2F_geschakeld", {"status": 0})
    GPIO.output(relais, GPIO.LOW)
    GPIO.output(groen, GPIO.LOW)
    GPIO.output(rood, GPIO.HIGH)
    DataRepository.update_waarde_actuator(1,formatted_date ,0)
  else:
    socketio.emit("B2F_geschakeld", {"status": 1})
    GPIO.output(relais, GPIO.HIGH)
    GPIO.output(groen, GPIO.HIGH)
    GPIO.output(rood, GPIO.LOW)
    DataRepository.update_waarde_actuator(1,formatted_date ,1)
  print("Toggle")
  if (count == 0):
    lcdéén()
  time.sleep(0.05)

def socket():
  socketio.run(app, debug=False, host='0.0.0.0')

def arduinocom():
  ser = serial.Serial('/dev/ttyS0',9600)
  ser.flushInput()
  time.sleep(0.1)
  rfid = ""
  stroom = -1
  while True:
    read_serial=str(ser.readline())[2:-5]
    if (str(read_serial)[0].isdigit()):
      global huidigestroom
      if str(read_serial) == "0.017256" or str(read_serial) == "0.034517":
        read_serial = "0.000000"
      while (huidigestroom != str(read_serial)):
        print(f"{read_serial} ampére")
        huidigestroom = read_serial
        DataRepository.update_waarde_sensor(2,read_serial)
        socketio.emit("B2F_newStroomData")
    elif (str(read_serial)[0].isalpha()):
      print("RFID")
      toggle_relais();
      #kaart
      if (str(read_serial)[0] == "B"):
        DataRepository.update_waarde_sensor(3, 1)
      #druppel
      if (str(read_serial)[0] == "F"):
        DataRepository.update_waarde_sensor(3, 2)

def plannen():
  tijd = 0
  indata = -1
  uitdata = -2
  inschtijd = -3
  uitschtijd = -4
  while True:
    #Huidige tijd omzetten naar zelfde formaat als in database
    tijd = str(datetime.now())
    tijd = tijd.replace(".", ":")
    tijd = tijd[:-10]
    #controleren of huidige tijd gelijk is aan tijd gegeven in json 
    if (str(tijd) == str(inschtijd)):
      if GPIO.input(relais) == 0:
        toggle_relais()
      else:
        print("reeds ingeschakeld")
    if (str(tijd) == str(uitschtijd)):
      if GPIO.input(relais) == 1:
        toggle_relais()
      else:
        print("reeds uitgeschakeld")
    #telkens nieuwste in en uitschakel json ophalen
    indata = DataRepository.read_gepland(1)
    uitdata = DataRepository.read_gepland(0)
    socketio.emit("B2F_gepland")
    #inschakeltijd en uitschakeltijd uit json halen
    for data in indata:
      inschtijd = data["tijdstip"]
      inschtijd = str(inschtijd)[:-3]
    for data in uitdata:
      uitschtijd = data["tijdstip"]
      uitschtijd = str(uitschtijd)[:-3]
    time.sleep(59)

knop1.on_press(lees_knop)

ir.on_ir_receive()

lcd_init()

proces = threading.Thread(target=printIP)
proces2 = threading.Thread(target=socket)
proces3 = threading.Thread(target=arduinocom)
proces4 = threading.Thread(target=plannen)

if __name__ == '__main__':
  try:
    proces4.start()
    proces3.start()
    proces2.start()
    proces.start()
    startIR()
  except KeyboardInterrupt:
    pass
  finally:
    lcd_byte(0x01, LCD_CMD)
    lcd_string("Goodbye!",LCD_LINE_1)
    GPIO.cleanup()
    