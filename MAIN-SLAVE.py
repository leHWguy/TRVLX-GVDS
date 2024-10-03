from machine import Pin, UART, Timer
import time

# Define out pins
PicoOut0 = 6
PicoOut1 = 7
PicoOut2 = 8
PicoOut3 = 9
PicoOut4 = 10
PicoOut5 = 11
LED19 = 19 # 19 is a LED
RE_Pin = 24
DE_Pin = 23

prep_time = 15
sleep_time = 10

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

#Define Input pins
PicoIn0 = 0
PicoIn1 = 1
PicoIn2 = 17
PicoIn3 = 18
PicoIn4 = 20
PicoIn5 = 21

delaycounts = 35 #Seconds
slave_msg = None
master_msg = None
ath_time = 0

keep_alive_count = 0
auth_token = False
input_changed = False
input_status = b"0"
srv_token = False

#Strings for fun
err_msg = b"ERR" 
kbr_msg = b"KBR"
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
crk_msg = b"CRK"
mky_msg = b"MKY"
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
in1_enable = True
in2_enable = True
in3_enable = True
in4_enable = True
in5_enable = True
in6_enable = True



def init():
    # Configuración de pines GPIO
    global In1, In2, In3, In4, In5, In6, Out1, Out2, Out3, Out4, Out5, Out6, Re_EN, De_EN, uart, LED_pin

    In1 = Pin(PicoIn0, Pin.IN)
    In2 = Pin(PicoIn1, Pin.IN)
    In3 = Pin(PicoIn2, Pin.IN)
    In4 = Pin(PicoIn3, Pin.IN)
    In5 = Pin(PicoIn4, Pin.IN)
    In6 = Pin(PicoIn5, Pin.IN)

    Out1 = Pin(PicoOut1, Pin.OUT)
    Out2 = Pin(PicoOut0, Pin.OUT)
    Out3 = Pin(PicoOut4, Pin.OUT) #Alarma
    Out4 = Pin(PicoOut3, Pin.OUT) #Valvula 2
    Out5 = Pin(PicoOut2, Pin.OUT)
    Out6 = Pin(PicoOut5, Pin.OUT) #Valvula 1
    LED_pin = Pin(LED19, Pin.OUT)

    Re_EN = Pin(RE_Pin, Pin.OUT)
    De_EN = Pin(DE_Pin, Pin.OUT)
    

    # Inicialización de la comunicación UART y RS485
    uart = UART(1, 9600, tx=Pin(4), rx=Pin(5), timeout = 20)

    # Definición de variables globales
    global is_master, ath_time

    # Detección automática de maestro/esclavo (opcional)
    # ... (código para determinar si el dispositivo es maestro o esclavo)
    ath_time = time.ticks_ms()
    # Inicialización de estados de salida
    Out1.value(0)  # Apagar actuador1
    Out2.value(0)  # Apagar actuador2
    Out3.value(0)  # Apagar 
    Out4.value(0)
    Out5.value(0)  # Apagar Out5 (alarma de no conexión)/alarma trailer
    Out6.value(0)
    Re_EN.value(0)
    De_EN.value(0)

def send_data(data_to_send):#Function to handle the data to send, to avoid writing the RE and DE values over and over again, what a f** pain
    Re_EN.value(1) 
    De_EN.value(1)
    time.sleep_ms(prep_time)
    #print(data_to_send)
    uart.write(data_to_send)
    time.sleep_ms(sleep_time)

def recieve_data(): #Function to handle the data recieved, same reason as send_data() 
    
    global keep_alive_count, srv_token,in1_enable, in2_enable, in3_enable, in4_enable, in5_enable, in6_enable, ath_time
    try:
        Re_EN.value(0)
        De_EN.value(0)
        time.sleep_ms(sleep_time)

        data = uart.readline()
        if data and data != "" :#if data is not empty      
            cmd=data[0:3]  #extract command from uart
            print(cmd)
            if cmd == ack_msg:
                pass
            elif cmd == ath_msg:
                
                keep_alive_count = 0
                send_data(ack_msg)
                srv_token = False #Override service token when it is connected to a Master 
                ath_time = time.ticks_ms()
                #print(time.ticks_diff(time.ticks_ms(), ath_time))
                slave_auth()
                #print(len(data))
            elif cmd == slv_msg:
                if (len(data) > 3 ):
                    if data[3:6] == lps_msg:
                        pass ##Turn on something
                    elif data[3:6] == lwh_msg:
                        pass ##Turn on something
                    elif data[3:6] == lsb_msg:
                        pass ##Turn on something
                    elif data[3:6] == bhd_msg:
                        pass
                    elif data[3:6] == bdr_msg:
                        pass
                    elif data[3:6] == btk_msg:
                        pass
                    elif data[3:6] == bbd_msg:
                        in1_enable = False
                    elif data[3:6] == srv_msg:
                        srv_token = True
                        slave_auth()
                        ath_time = time.ticks_ms()

                    else:
                        pass # Do nothing, good life
                else:
                    #print(mst_msg+input_status)
                    send_data(mst_msg+input_status)
            elif cmd == kbr_msg:
                pass #do nothing, slave should not recieve this message
            elif cmd == esl_msg:
                pass #do nothing, slave should not recieve this message               
            elif cmd == nop_msg:
                pass #do nothing command :D
            elif cmd == xxx_msg:
                pass # do something but not implemented yet :D        
            elif cmd == crk_msg:
                pass #do nothing, slave should not recieve this message
            elif cmd == lps_msg:
                pass #do nothing, slave should not recieve this message
            elif cmd == lwh_msg:
                pass #do nothing, slave should not recieve this message
            elif cmd == lsb_msg:
                pass #do nothing, slave should not recieve this message
            elif cmd == mkb_msg:
                pass #do nothing, slave should not recieve this message
            elif cmd == mky_msg:
                pass #do nothing, slave should not recieve this message
            
            else:
                #master_disconnection(keep_alive_count)
                #print(cmd)
                print("No deberiamos estar aqui cerebro, Snort!")
                pass
        else:
            keep_alive_count += 1
            pass
    except:
        pass


def monitor_inputs():
    global input_changed, input_status, in1_enable, in2_enable, in3_enable, in4_enable, in5_enable, in6_enable
    # Monitorear entradas In1 a In6
    
    if (In1.value() or In2.value() or In3.value() or In4.value() or In5.value() or In6.value()) and not input_changed:
        # Se ha detectado un cambio en alguna entrada
        input_changed = True
        if In1.value() and in1_enable:
            input_status = b"1"
        elif In2.value() and in2_enable:
            input_status = b"2"
        elif In3.value() and in3_enable:
            input_status = b"3"   
        elif In4.value() and in4_enable:
            input_status = b"4"   
        elif In5.value() and in5_enable:
            input_status = b"5"   
        elif In6.value() and in6_enable:
            input_status = b"6"   
        else:
            pass ##should not get here
        print("Cambio detectado en entradas!")
        # Esclavo: enviar mensaje al maestro indicando el cambio
    elif not (In1.value() or In2.value() or In3.value() or In4.value() or In5.value() or In6.value()) and input_changed:
        input_changed = False
        input_status = b"0"
    else:
        pass  
 
def slave_panic():
    Out3.value(1) # Apagar Out3 (alarma de no conexión)
    Out4.value(0) # Valvula
    Out6.value(0) # Valvula
    LED_pin.value(1) #

def slave_gates(open_gate):
    if open_gate:
        pass #Do something to open the piston
    else:
        pass #Do something to close the piston

def slave_auth():
    Out3.value(0) # Apagar Out3 (alarma de no conexión)
    Out4.value(1) # Valvula
    Out6.value(1) # Valvula
    LED_pin.value(0)#

def slave_wheel(open_wheel):
    if open_wheel:
        pass
    else:
        pass

def main():
    init()  # Inicializar el sistema
    global keep_alive_count, input_changed, srv_token,ath_time
    delaycount = 290
    deadTime = 35000 
    try:
        while True:
            # Bucle principal del esclavo

            recieve_data()
            if time.ticks_diff(time.ticks_ms(), ath_time) > deadTime :#keep_alive_count >= delaycount:
                slave_panic()
            else:
                keep_alive_count += 1
                #print(keep_alive_count)
            monitor_inputs()
            if srv_token:
                keep_alive_count = 0
                ath_time = time.ticks_ms()
            #print(time.ticks_diff(time.ticks_ms(), ath_time))          
    except:
        pass


if __name__ == "__main__":
    main()
