from RPi import GPIO
from time import time

class InfraRood:
    def __init__(self, pin, bouncetime=100):
        self.pin = pin
        self.bouncetime = bouncetime
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN, GPIO.PUD_DOWN)

    def binary_ophalen(self, duration):
        # Vlug data ophalen
        t0 = time()
        results = []
        while (time() - t0) < duration:
            results.append(GPIO.input(self.pin))
        return results


    def on_ir_receive(self, bouncetime=150):
        # Wanneer edge gedetecteerd beginnen lezen
        data = self.binary_ophalen((self.bouncetime)/1000.0)
        if len(data) < (self.bouncetime):
            return
        rate = len(data) / ((self.bouncetime) / 1000.0)
        pulses = []
        i_break = 0
        # lengtes bepalen en in microseconden omzetten
        for i in range(1, len(data)):
            if (data[i] != data[i-1]) or (i == len(data)-1):
                pulses.append((data[i-1], int((i-i_break)/rate*1e6)))
                i_break = i
        # decode ( < 1 ms "1" pulse is a 1, > 1 ms "1" pulse is a 1, longer than 2 ms pulse is something else)
        # does not decode channel, which may be a piece of the information after the long 1 pulse in the middle
        outbin = ""
        for val, us in pulses:
            if val != 1:
                continue
            if outbin and us > 2000:
                break
            elif us < 1000:
                outbin += "0"
            elif 1000 < us < 2000:
                outbin += "1"
        try:
            return int(outbin, 2)
        except ValueError:
            # probably an empty code
            return None