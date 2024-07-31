from machine import Pin, UART, Timer, PWM
import time
import secrets
is_master = True  # Indicador de maestro/esclavo
is_in_panic_mode= False
no_cargo = False
bypass = False


# Define out pins
PicoOut0 = 6
PicoOut1 = 7
PicoOut2 = 8
PicoOut3 = 9
PicoOut4 = 10
PicoOut5 = 11
LED_pin = 19 # 19 is a LED
RE_Pin = 24
DE_Pin = 23


#Define Input pins
PicoIn0 = 0
PicoIn1 = 1
PicoIn2 = 17
PicoIn3 = 18
PicoIn4 = 20
PicoIn5 = 21
#Hans w/h <3
delaycounts = 5 #Seconds
slave_msg = None
master_msg = None

keep_alive_count = 0
auth_token = False
sensor_status = False #Will help us monitor any input


def init():
    # Configuración de pines GPIO
    global In1, In2, In3, In4, In5, In6, Out1, Out2, Out3, Out4, Out5, Out6, Re_EN, De_EN, uart

    In1 = Pin(PicoIn0, Pin.IN) # Hood
    In2 = Pin(PicoIn1, Pin.IN) # Door
    In3 = Pin(PicoIn2, Pin.IN) # Tank
    In4 = Pin(PicoIn3, Pin.IN) # Engine
    In5 = Pin(PicoIn4, Pin.IN) # Airlock
    In6 = Pin(PicoIn5, Pin.IN) # Gates

    Out1 = Pin(PicoOut1, Pin.OUT)
    Out2 = Pin(PicoOut0, Pin.OUT)
    Out3 = Pin(PicoOut4, Pin.OUT)
    Out4 = Pin(PicoOut3, Pin.OUT)
    Out5 = PWM(PicoOut2, freq = 330, duty_u16 = 0)
    Out6 = Pin(PicoOut5, Pin.OUT)

    Re_EN = Pin(RE_Pin, Pin.OUT)
    De_EN = Pin(DE_Pin, Pin.OUT)

    # Inicialización de la comunicación UART y RS485
    uart = UART(1, 9600, tx=Pin(4), rx=Pin(5), timeout = 50)

    # Definición de variables globales
    global is_master
    global ecode, bigNumber

    # Detección automática de maestro/esclavo (opcional)
    # ... (código para determinar si el dispositivo es maestro o esclavo)

    # Inicialización de estados de salida
    Out1.value(0)  # Apagar actuador1
    Out2.value(0)  # Apagar actuador2
    Out3.value(0)  # Apagar 
    Out4.value(0)
    Out5.duty_u16(0)  # Encender Out5 (alarma de no conexión)/alarma trailer
    Out6.value(0)

def master_send_auth():
    # Enviar mensaje de autorización "AUTH" al esclavo
    Re_EN.value(1) 
    De_EN.value(1)   
    time.sleep(0.1)
    authorization_message = "AUTH".encode('utf-8')
    uart.write(authorization_message)
    time.sleep(0.1)  # Esperar un poco después de enviar el mensaje
    Re_EN.value(0) 
    De_EN.value(0)
    time.sleep(0.1)
    


def master_keep_alive():
    # Enviar mensaje "keep alive" al esclavo
    Re_EN.value(1) 
    De_EN.value(1)
    time.sleep(0.1)
    keep_alive_message = "KEEP_ALIVE".encode('utf-8')
    uart.write(keep_alive_message)
    time.sleep(0.1)
    Re_EN.value(0) 
    De_EN.value(0)
      # Esperar un poco después de enviar el mensaje




def monitor_inputs():
    # Monitorear entradas In1 a In6
    global is_master

    if In1.value() or In2.value() or In3.value() or In4.value() or In5.value() or In6.value():
        # Se ha detectado un cambio en alguna entrada


        print("Cambio detectado en entradas!")
        if is_master:
            # Maestro: activar salidas Out2 y Out3
            Out2.value(1)
            Out3.value(1)
        else:
            # Esclavo: enviar mensaje al maestro indicando el cambio
            change_message = "CHANGE".encode('utf-8')
            uart.write(change_message)
            time.sleep(0.1)  # Esperar un poco después de enviar el mensaje



# Function when
def master_disconnection(keep_alive_count):
    print(keep_alive_count)
    if(keep_alive_count <= 10):
        Out5.init(freq = 261,duty_u16 = 1276 )
    elif(keep_alive_count <= 15):
        Out5.init(freq = 277,duty_u16 = 1276*2 )
    elif(keep_alive_count > 15 and keep_alive_count <= 20):
        Out5.init(freq = 329,duty_u16 = 1276*3)
    else:
        Out5.init(freq = 698,duty_u16 = 1276*4)
        
        
def master_reconnect():
    Out5.duty_u16(0) ##will turn off the PWM 


    
def gen_ecode(sensor_error):
    _a = secrets.randbelow(9) 
    _b = secrets.randbelow(9)
    _c = secrets.randbelow(9)
    _d = secrets.randbelow(9)



    ecode = sensor_error*100000 + _a * 1000 + _b * 100 + _c * 10 + _d

    _e = (_a * _a) // 10
    _f = (_b // 2)
    _g = _c // (_a + 1)
    _h = (_d * _d * _d) // 100

    bigNumber = sensor_error*100000 + 50000 + _f * 1000 + _h * 100 + _g * 10 + _e

    return ecode


def main():
    init()  # Inicializar el sistema
    keep_alive_count = 0
    delaycount = 30

    # Dispositivo maestro
    print("Dispositivo maestro")
    #master_send_auth()  # Enviar mensaje de autorización al esclavo
    while True:
        master_send_auth()

        time.sleep(0.1) 
        Re_EN.value(0) 
        De_EN.value(0)
        time.sleep(0.1)
        data = uart.readline()
        if data:             
            if data == b"ACK_AUTH":
                keep_alive_count = 0
                master_reconnect()
                #These lines are for the display + keypad, change key to err
            elif data[0:3]== b"KEY":
                key= int(data[3:9])
                if key == bigNumber :
                    master_reconnect()
                    keep_alive_count = 0
            else:
               # master_disconnection(keep_alive_count)
               print("ay wei mi mente")
        else:
            print("No se ha recibido respuesta del esclavo")
            keep_alive_count += 1
            if keep_alive_count > 5:
                master_disconnection(keep_alive_count)
            if keep_alive_count >= 30:
                is_in_panic_mode= True
                
            
        monitor_inputs()  # Monitorear entradas



if __name__ == "__main__":
    main()
