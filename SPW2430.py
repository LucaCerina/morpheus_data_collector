import spidev
import time
import RPi.GPIO as GPIO

class SPW2430:
    def __init__(self,pin):
        self.pin = pin
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.IN)


    def read_noise(self):
        num_cycles = 100
        tStart = time.perf_counter() #dal momento in cui è stato chiamato
        for i in range(num_cycles):
            GPIO.wait_for_edge(self,pin, GPIO.FALLING/RISING)
            #funzione che rileva il picco! tra l'altro dopo il self non va una virgola?
			#rilevo poi la durata della funzione, tempo trascorso dall'inizio alla rilevazione del picco
        duration = time.perf_counter() - tStart
    #   calcolo la frequenza dei rumori durante la notte.
        frequency_noise = num_cycles / duration
        return frequency_noise