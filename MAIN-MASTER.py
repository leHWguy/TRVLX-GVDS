#If you are reading this, your mom is a dude :D
#and you should'nt be here, hopefully you smiled to the cameras :D
#we will find you :)

from machine import Pin, UART, Timer, PWM
import time
import _thread
import random
import errno


is_master = True  # Indicador de maestro/esclavo
is_in_panic_mode= False
no_cargo_mode = False
bypass = False

sleep_time = 15
PswdTypeUnlock = 1
PswdTypeBypass = 2
PswdTypeService = 3
prep_time = 5
SnsrTypeHood = 1
SnsrTypeDoor = 2
SnsrTypeTank = 3
SnsrTypeGates = 4
SnsrTypeEngine = 5 # from here to the end, not sensors but useful for creating error numbers
SnsrTypeAir = 6
SnsrTypeWheel = 7
SnsrTypeService = 8
SnsrTypeBox = 9 
SnsrTypeNoBox = 10

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

auth_token = False
sensor_status = False #Will help us monitor any input
#Strings for fun

slv_msg = b"SLV"
esl_msg = b"ESL"
key_msg = b"KEY"
ath_msg = b"ATH"
ack_msg = b"ACK"
mst_msg = b"MST"
nop_msg = b"NOP"
whl_msg = b"WHL"
pst_msg = b"PST"
xxx_msg = b"XXX"
srv_msg = b"SRV"
msk_msg = b"MSK"

#KBR mssgs
kbr_msg = b"KBR"
crk_msg = b"CRK"
err_msg = b"ERR" 
    #lck request
lps_msg = b"LPS"
lwh_msg = b"LWH"
lsb_msg = b"LSB"
arm_msg = b"ARM"
    #bps request
bhd_msg = b"BHD"
bdr_msg = b"BDR"
btk_msg = b"BTK"
bbd_msg = b"BBD"

kbr_payload = kbr_msg
slv_payload = slv_msg
snsrErr = 0




def init():
    # Configuración de pines GPIO
    global In1, In2, In3, In4, In5, In6, Out1, Out2, Out3, Out4, Out5, Out6, Re_EN, De_EN, uart

    global keep_alive_count, delaycount, sensorfault, auth_token
    delaycount = 30
    sensorfault = 0
    keep_alive_count = 0
    
    
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

def send_data(data_to_send):#Function to handle the data to send, to avoid writing the RE and DE values over and over again, what a f** pain
    Re_EN.value(1) 
    De_EN.value(1)
    time.sleep_ms(prep_time)
    #print(data_to_send)
    uart.write(data_to_send)
    time.sleep_ms(sleep_time)

def setNumbers(aVariable):
    
    
    match aVariable:
        case 0:
            return 6
        case 1:
            return 3
        case 2:
            return 8
        case 3:
            return 5
        case 4:
            return 2
        case 5:
            return 9
        case 6:
            return 1
        case 7:
            return 0
        case 8:
            return 7
        case 9:
            return 4
        case _:
            return 0

def recieve_data(): #Function to handle the data recieved, same reason as send_data() 
    aValue= 4
    global keep_alive_count, auth_token, bigNumber, kbr_payload, slv_payload, snsrErr
    try:   
        Re_EN.value(0)
        De_EN.value(0)
        time.sleep_ms(sleep_time)
        data = uart.readline()
        #print(data)
        if data and data != "" :#if data is not empty      
            cmd = data[0:3]  #extract command from uart
            print(data)
            if cmd == ack_msg:
                keep_alive_count = 0
                master_reconnect()
                is_in_panic_mode = False
                #These lines are for the display + keypad, change key to err
            elif cmd == kbr_msg:
                pass #do nothing, master should not recieve this message
            elif cmd == slv_msg:
                pass #do nothing, master should not recieve this message
            elif cmd == esl_msg:
                pass #do nothing, master should not recieve this message
            elif cmd == key_msg:
                key= int(data[3:9])
                #print(key)
                if key == bigNumber:
                    master_reconnect()
                    auth_token = False
                    is_in_panic_mode = False
                    keep_alive_count = 0
                    kbr_payload = crk_msg
                else:
                    #send_data(gen_ecode(sensorfault,PswdTypeUnlock)) #Create another error since the password was incorrect
                    
                    kbr_payload = gen_ecode(snsrErr, PswdTypeUnlock)
            elif cmd == mst_msg:#Recieve data from slave, the number is the sensor from it
                cmd_data = int(data[3])
                #print(cmd_data)
                if cmd_data == 48 and  not auth_token: #If there is an issue with the slave and a error haven't been triggered yet
                    pass # all sensors good :D
                    #kbr_payload = gen_ecode(cmd_data-48, PswdTypeUnlock)
                    #auth_token = True #Make sure we only generate one token until we got the issue resolved
                elif cmd_data == 49 and not auth_token:
                    kbr_payload = gen_ecode(cmd_data-aValue, PswdTypeUnlock)
                    auth_token = True
                elif cmd_data == 50 and not auth_token:
                    kbr_payload = gen_ecode(cmd_data-aValue, PswdTypeUnlock)
                    auth_token = True
                elif cmd_data == 51 and not auth_token:
                    kbr_payload = gen_ecode(cmd_data-aValue, PswdTypeUnlock)
                    auth_token = True
                elif cmd_data == 52 and not auth_token:
                    kbr_payload = gen_ecode(cmd_data-aValue, PswdTypeUnlock)
                    auth_token = True
                elif cmd_data == 53 and not auth_token:
                    kbr_payload = gen_ecode(cmd_data-aValue, PswdTypeUnlock)
                    auth_token = True
                elif cmd_data == 54 and not auth_token:
                    kbr_payload = gen_ecode(cmd_data-aValue, PswdTypeUnlock)
                    auth_token = True
                elif cmd_data == 55 and not auth_token:
                    kbr_payload = gen_ecode(cmd_data-aValue, PswdTypeUnlock)
                    auth_token = True
                elif cmd_data == 56 and not auth_token:
                    kbr_payload = gen_ecode(cmd_data-aValue, PswdTypeUnlock)
                    auth_token = True
                elif cmd_data == 57 and not auth_token:
                    kbr_payload = gen_ecode(cmd_data-aValue, PswdTypeUnlock)
                    auth_token = True
                else:
                    pass
            elif cmd == nop_msg:
                pass #do nothing command :D
            elif cmd == whl_msg: #generates an error to unlock the extra wheel in the slave side
                snsrErr=SnsrTypeWheel
                kbr_payload=gen_ecode(snsrErr, PswdTypeUnlock)
            elif cmd == pst_msg: #generates an error to unlock the pistons in the slave side (Door piston)
                snsrErr=SnsrTypeGates
                kbr_payload=gen_ecode(SnsrTypeGates, PswdTypeUnlock)
            elif cmd == xxx_msg:
                pass # do something but not implemented yet :D
            elif cmd == srv_msg:
                snsrErr=SnsrTypeService
                kbr_payload = gen_ecode(snsrErr, PswdTypeUnlock)
                no_cargo_mode = True 
            elif cmd == msk_msg:
                snsrErr=SnsrTypeNoBox
                kbr_payload = gen_ecode(SnsrTypeNoBox, PswdTypeUnlock)
                no_cargo_mode = True           
            elif cmd == crk_msg:
                pass #do nothing, master should not recieve this message
            elif cmd == lps_msg:
                slv_payload = slave_msg + lps_msg
            elif cmd == lwh_msg:
                slv_payload = slave_msg + lwh_msg
            elif cmd == lsb_msg:
                slv_payload = slave_msg + lsb_msg
            elif cmd == arm_msg:
                no_cargo_mode = False
            elif cmd == bhd_msg:
                snsrErr=SnsrTypeHood
                kbr_payload = gen_ecode(snsrErr, PswdTypeBypass)
            elif cmd == bdr_msg:
                snsrErr=SnsrTypeDoor
                kbr_payload = gen_ecode(snsrErr, PswdTypeBypass)
            elif cmd == btk_msg:
                snsrErr=SnsrTypeTank
                kbr_payload= gen_ecode(snsrErr, PswdTypeBypass)
            elif cmd == bbd_msg:
                snsrErr=SnsrTypeGates
                kbr_payload = gen_ecode(snsrErr, PswdTypeBypass)
            else:
                #master_disconnection(keep_alive_count)
                print(cmd)
                print("No deberiamos estar aqui cerebro")
                pass
                
        else:
                #print(keep_alive_count)
                keep_alive_count +=1
                if keep_alive_count > 5:
                    master_disconnection(keep_alive_count)
                if keep_alive_count >= 30:
                    is_in_panic_mode = True
    except:
        print("DOH!")


def monitor_inputs():

    if In1.value() or In2.value() or In3.value() or In4.value() or In5.value() or In6.value():
        # Se ha detectado un cambio en alguna entrada
        if In1.value():
            gen_ecode()
        print("Cambio detectado en entradas!")

def master_disconnection(count):
    while is_in_panic_mode:
        if(count <= 10):
            Out5.init(freq = 261,duty_u16 = 1276 )
            time.sleep_ms(1000)
            Out5.duty_u16(0)
            time.sleep_ms(1000)
        elif(count <= 15):
            Out5.init(freq = 277,duty_u16 = 1276*2 )
            time.sleep_ms(800)
            Out5.duty_u16(0)
            time.sleep_ms(800)
        elif(count > 15 and count <= 20):
            Out5.init(freq = 329,duty_u16 = 1276*3)
            time.sleep_ms(500)
            Out5.duty_u16(0)
            time.sleep_ms(500)
        else:
            Out5.init(freq = 698,duty_u16 = 1276*4)
            time.sleep_ms(300)
            Out5.duty_u16(0)
            time.sleep_ms(300)
    
def master_reconnect():
    Out5.duty_u16(0) ##will turn off the PWM 

def gen_ecode(sensor_error, passType):
    global bigNumber
   
    _a = random.randrange(0,9) 
    _b = random.randrange(0,9)
    _c = random.randrange(0,9)
    _d = random.randrange(0,9)
    _r = random.randrange(0,9)
    
    ecode = 100000 + (sensor_error-1)*10000 + _a * 1000 + _b * 100 + _c * 10 + _d
    
    _e = setNumbers(_a)#(_a * _a) // 10
    _f = setNumbers(_b)#(_b // 2)
    _g = setNumbers(_c)#_c // (_a + 1)
    _h = setNumbers(_d)#(_d * _d * _d) // 100
    
    if passType == PswdTypeUnlock:
        bigNumber = 100000 + _r*10000 + _f * 1000 + _h * 100 + _g * 10 + _e#100000 + (sensor_error-1)*10000 + _f * 1000 + _h * 100 + _g * 10 + _e
    elif passType == PswdTypeBypass:
        bigNumber = 100000 + _r*10000 + _e * 1000 + _f * 100 + _h * 10 + _g#100000 + (sensor_error-1)*10000 + _e * 1000 + _f * 100 + _h * 10 + _g
    elif passType == PswdTypeService:
        bigNumber = 100000 + _r*10000 + _h * 1000 + _e * 100 + _g * 10 + _f#100000 + (sensor_error-1)*10000 + _h * 1000 + _e * 100 + _g * 10 + _f
    else:
        pass
    
    #print(bigNumber)
    return err_msg + str(ecode)


def main():
    global kbr_payload, slv_payload
    try:
        init()  # Inicializar el sistema
        #_thread.start_new_thread(master_disconnection, ()) ##need to check if it works LOL
        while True:
            if not no_cargo_mode:
                send_data(ath_msg)
                recieve_data()
                send_data(slv_payload)
                slv_payload = slv_msg #return to default value
                recieve_data()
            send_data(kbr_payload)
            kbr_payload = kbr_msg #return to default value
            recieve_data()
            monitor_inputs()  # Monitorear entradas
    except OSError as exc:
        print("DOH!")
        pass #should make a log to know where TF I'm breaking


if __name__ == "__main__":
    main()
