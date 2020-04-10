# -*-coding:Latin-1 -*

import pyfirmata
 
port = '/dev/ttyUSB0'   #linux
 
board = pyfirmata.Arduino(port)

#d = digital, 11 = numéro de la pin, p = PWM
LEDpin = board.get_pin("d:9:p")

print("-------------- CONTROLE DE LEDS ----------------")
print("En tout temps, vous pouvez quitter le programme en répondant par 'q'.")

while True:
    
    print("Luminosité désirée pour la LED:")
    luminosite = input("De 0 à 100 (ou q):  ")
    if (luminosite == 'q'):
        board.exit();
        print("Au revoir!")
        break;
    
    board.digital[LEDpin.pin_number].write(float(luminosite)/100.0)

