
from machine import Pin, UART, Timer, PWM
import time
import _thread
import random
import errno

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
mky_msg = b"MKY"
#KBR mssgs
kbr_msg = b"KBR"
crk_msg = b"CRK"
cka_msg = b"CKA"
err_msg = b"ERR" 
mkb_msg = b"MKB"
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
bps_payload = ""
kbr_payload = kbr_msg
slv_payload = slv_msg
snsrErr = 0
cargo_rqst = False
srv_token = False
bypass_token = False
firstkey=False
lastPass = 0

def init():
    # Configuración de pines GPIO
    global In1, In2, In3, In4, In5, In6, Out1, Out2, Out3, Out4, Out5, Out6, Re_EN, De_EN, uart

    global keep_alive_count, delaycount, sensorfault, auth_token, is_in_panic_mode
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
    global ecode, bigNumber,bigNumber2

    # Detección automática de maestro/esclavo (opcional)
    # ... (código para determinar si el dispositivo es maestro o esclavo)
  
    # Inicialización de estados de salida
    Out1.value(0)  # Apagar actuador1
    Out2.value(0)  # Apagar actuador2
    Out3.value(0)  # Apagar 
    Out4.value(0)
    Out5.duty_u16(0)  # Encender Out5 (alarma de no conexión)/alarma trailer
    Out6.value(0)
    time.sleep_ms(500) #wait half a second to start doing stuff

def send_data(data_to_send):#Function to handle the data to send, to avoid writing the RE and DE values over and over again, what a f** pain
    Re_EN.value(1) 
    De_EN.value(1)
    time.sleep_ms(prep_time)
    #print(data_to_send)
    uart.write(data_to_send)
    time.sleep_ms(sleep_time)

def setNumbers(aVariable):
    if aVariable == 0:
        return 6
    elif aVariable == 1:
        return 3
    elif aVariable == 2:
        return 8
    elif aVariable == 3:
        return 5
    elif aVariable == 4:
        return 2
    elif aVariable == 5:
        return 9
    elif aVariable == 6:
        return 1
    elif aVariable == 7:
        return 0
    elif aVariable == 8:
        return 7
    elif aVariable == 9:
        return 4
    else:
        return 0

def setNumbers2(aVariable):
    if aVariable == 0:
        return 4
    elif aVariable == 1:
        return 7
    elif aVariable == 2:
        return 0
    elif aVariable == 3:
        return 1
    elif aVariable == 4:
        return 9
    elif aVariable == 5:
        return 2
    elif aVariable == 6:
        return 5
    elif aVariable == 7:
        return 8
    elif aVariable == 8:
        return 3
    elif aVariable == 9:
        return 6
    else:
        return 0


def sum_digits(number):
    # Ensure the input is a string and has 14 characters
    if len(number) != 14 or not number.isdigit():
        raise ValueError("Input must be a 14-character number.")
    
    # Convert each character to an integer and sum them
    total = sum(int(digit) for digit in number)
    return total

def recieve_data(): #Function to handle the data recieved, same reason as send_data() 
    aValue= 46
    mvalue = 89
    
    global firstkey, cargo_rqst, keep_alive_count, auth_token, bigNumber, bigNumber2, kbr_payload, slv_payload, snsrErr, no_cargo_mode, is_in_panic_mode, srv_token,bypass_token, lastPass, bps_payload
    try:   
        Re_EN.value(0)
        De_EN.value(0)
        time.sleep_ms(sleep_time)
        data = uart.readline()
        #print(data)
        if data and data != "" :#if data is not empty      
            cmd = data[0:3]  #extract command from uart
            #print(data)
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
                key= int(data[5:9])
                #print(key)
                if key == bigNumber:
                    kbr_payload = crk_msg
                    firstkey = True
                   
                elif key == bigNumber2 and firstkey:
                    master_reconnect()
                    auth_token = False #We can accept new errors
                    is_in_panic_mode = False
                    keep_alive_count = 0
                    kbr_payload = cka_msg
                    firstkey = False
                    if cargo_rqst:
                        no_cargo_mode = True
                        cargo_rqst = False
                        
                    else:
                        no_cargo_mode = False

                else:
                   #Create another error since the password was incorrect  
                    kbr_payload = gen_ecode(snsrErr, lastPass)

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
            elif cmd == mky_msg:
                mkey= data[3:16]

                if(sum_digits(mkey) == mvalue):
                    no_cargo_mode = True
                else:
                    no_cargo_mode = False  

                
            elif cmd == whl_msg: #generates an error to unlock the extra wheel in the slave side
                snsrErr=SnsrTypeWheel
                kbr_payload=gen_ecode(snsrErr, PswdTypeUnlock)
                auth_token = True
            elif cmd == pst_msg: #generates an error to unlock the pistons in the slave side (Door piston)
                snsrErr=SnsrTypeGates
                kbr_payload=gen_ecode(SnsrTypeGates, PswdTypeUnlock)
                auth_token = True
            elif cmd == xxx_msg:
                pass # do something but not implemented yet :D
            elif cmd == srv_msg:
                snsrErr=SnsrTypeService
                kbr_payload = gen_ecode(snsrErr, PswdTypeUnlock)
                cargo_rqst = True 
                srv_token = True
                auth_token = True
            elif cmd == msk_msg:
                snsrErr=SnsrTypeNoBox
                kbr_payload = gen_ecode(SnsrTypeNoBox, PswdTypeUnlock)
                cargo_rqst = True   
                auth_token = True        
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
                auth_token = True
                
            elif cmd == bdr_msg:
                snsrErr=SnsrTypeDoor
                kbr_payload = gen_ecode(snsrErr, PswdTypeBypass)
                bps_payload = bdr_msg
                auth_token = True
            elif cmd == btk_msg:
                snsrErr=SnsrTypeTank
                kbr_payload= gen_ecode(snsrErr, PswdTypeBypass)
                bps_payload = btk_msg
                auth_token = True
            elif cmd == bbd_msg:
                snsrErr=SnsrTypeGates
                kbr_payload = gen_ecode(snsrErr, PswdTypeBypass)
                bps_payload = bbd_msg
                auth_token = True
            else:
                #master_disconnection(keep_alive_count)
                #print(cmd)
                print("No deberiamos estar aqui cerebro")
                pass
                
        else:
                #print(keep_alive_count)
                if (keep_alive_count < 800):
                    keep_alive_count +=1

                if keep_alive_count > 30: #Approx 5 seg
                    #pass
                    #master_disconnection()
                    is_in_panic_mode = True
                    _thread.start_new_thread(master_disconnection, ())
                    
    except OSError as exc:
        #print("DOH!")
        #print(exc)
        pass

def sum_of_digits(number_str):
    # Convert the number to a string to iterate over each digit
    total_sum = 0
    
    # Iterate over each character in the string
    for digit in number_str:
        total_sum += int(digit)
    
    return total_sum

def monitor_inputs():

    if In1.value() or In2.value() or In3.value() or In4.value() or In5.value() or In6.value():
        # Se ha detectado un cambio en alguna entrada
        if In1.value():
            pass#gen_ecode(1,1)
        print("Cambio detectado en entradas!")

def master_disconnection():
    global  keep_alive_count, is_in_panic_mode
    firstAlarm = 100
    secondAlarm = 200
    thirdAlarm = 300
    if is_in_panic_mode: ## we sould not get here with the main thread
        if( keep_alive_count <= firstAlarm and  keep_alive_count > 5 ):
            Out5.init(freq = 261,duty_u16 = 1276 )
            time.sleep_ms(1000)
            Out5.duty_u16(0)
            time.sleep_ms(1000)
        elif( keep_alive_count > firstAlarm and  keep_alive_count <= secondAlarm):
            Out5.init(freq = 277,duty_u16 = 1276*2 )
            time.sleep_ms(800)
            Out5.duty_u16(0)
            time.sleep_ms(800)
        elif( keep_alive_count > secondAlarm and  keep_alive_count <= thirdAlarm):
            Out5.init(freq = 329,duty_u16 = 1276*3)
            time.sleep_ms(500)
            Out5.duty_u16(0)
            time.sleep_ms(500)
        else:
            Out5.init(freq = 698,duty_u16 = 1276*4)
            time.sleep_ms(300)
            Out5.duty_u16(0)
            time.sleep_ms(100)
    else:
        #print("thread 1 here")
        _thread.exit()
    _thread.exit()

def master_reconnect():
    Out5.duty_u16(0) ##will turn off the PWM 

def gen_ecode(sensor_error, passType):
    global bigNumber, bypass_token, lastPass, bigNumber2
   
    _a = random.randrange(0,9) 
    _b = random.randrange(0,9)
    _c = random.randrange(0,9)
    _d = random.randrange(0,9)
    _r = random.randrange(0,9)
    
    ecode = 100000 + _r*10000 + _a * 1000 + _b * 100 + _c * 10 + _d
    
    _e = setNumbers(_a)#(_a * _a) // 10
    _f = setNumbers(_b)#(_b // 2)
    _g = setNumbers(_c)#_c // (_a + 1)
    _h = setNumbers(_d)#(_d * _d * _d) // 100
    
    _e2 = setNumbers2(_a)#(_a * _a) // 10
    _f2 = setNumbers2(_b)#(_b // 2)
    _g2 = setNumbers2(_c)#_c // (_a + 1)
    _h2 = setNumbers2(_d)#(_d * _d * _d) // 100

    if passType == PswdTypeUnlock:
        lastPass = passType
        bigNumber = _f * 1000 + _h * 100 + _g * 10 + _e#100000 + (sensor_error-1)*10000 + _f * 1000 + _h * 100 + _g * 10 + _e
        bigNumber2 =_f2 * 1000 + _h2 * 100 + _g2 * 10 + _e2
    elif passType == PswdTypeBypass:
        lastPass = passType
        bigNumber = _e * 1000 + _f * 100 + _h * 10 + _g#100000 + (sensor_error-1)*10000 + _e * 1000 + _f * 100 + _h * 10 + _g
        bigNumber2 = _e2 * 1000 + _f2 * 100 + _h2 * 10 + _g2
        bypass_token = True
    elif passType == PswdTypeService:
        lastPass = passType
        bigNumber = _h * 1000 + _e * 100 + _g * 10 + _f#100000 + (sensor_error-1)*10000 + _h * 1000 + _e * 100 + _g * 10 + _f
        bigNumber2 = _h2 * 1000 + _e2 * 100 + _g2 * 10 + _f2
    else:
        
        pass
    
    
    return err_msg + str(ecode)


def main():
    global kbr_payload, slv_payload, no_cargo_mode,keep_alive_count, srv_token, bypass_token, bps_payload, auth_token, is_in_panic_mode
    
    try:
        init()  # Inicializar el sistema
        #auth_token = True
        #kbr_payload = gen_ecode(1, PswdTypeUnlock)
        #_thread.start_new_thread(master_disconnection, ())##need to check if it works LOL
        while True:
            if not no_cargo_mode: #Should not have an error generated and no cargo mode is not running
                if not auth_token: #if the authorization token is false (not requested)
                    send_data(ath_msg) #Send the authorization data
                    recieve_data() #Wait for a little moment for the respones
                send_data(slv_payload) #Monitor how the
                if bypass_token and not auth_token:
                    slv_payload = slv_msg + bps_payload
                    bypass_token = False
                else:
                   slv_payload = slv_msg #return to default value
                recieve_data()
                send_data(kbr_payload)
                kbr_payload = kbr_msg #return to default value
                recieve_data()
                send_data(mkb_msg)
                recieve_data()
                monitor_inputs()  # Monitorear entradas
            elif no_cargo_mode:
                keep_alive_count = 0
                time.sleep_ms(500)
                if srv_token:
                    send_data(slv_msg+srv_msg)
                    srv_token = False
                else:
                    send_data(kbr_payload)
                    kbr_payload=kbr_msg
                #print('Esperando mensaje')
                recieve_data()
            else:
                print('Dude')
                
            
    except OSError as exc:
        print("DOH!")
        print(exc)
        pass #should make a log to know where TF I'm breaking


if __name__ == "__main__":
    main()
