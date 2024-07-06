#include <Wire.h>
#include <ArduCAM.h>
#include <SPI.h>
#include "memorysaver.h"

// Only enable the OV5642 camera module
#define OV5642_CAM
#include "memorysaver.h"

#define CS 7 // Change as per your CS pin connected to your ArduCAM

ArduCAM myCAM(OV5642, CS);

void setup()
{
    pinMode(2, OUTPUT);
    pinMode(53, OUTPUT);
    pinMode(49, OUTPUT);
    pinMode(3, OUTPUT);

    uint8_t vid, pid;
    Wire.begin();
    Serial.begin(115200);
    pinMode(CS, OUTPUT);
    digitalWrite(CS, HIGH);
    SPI.begin();
    myCAM.write_reg(0x07, 0x80);
    delay(100);
    myCAM.write_reg(0x07, 0x00);
    delay(100);

    while (1)
    {
        myCAM.write_reg(ARDUCHIP_TEST1, 0x55);
        if (myCAM.read_reg(ARDUCHIP_TEST1) != 0x55)
        {
            Serial.println("SPI interface Error!");
            delay(1000);
            continue;
        }
        else
        {
            break;
        }
    }

    myCAM.set_format(JPEG);
    myCAM.InitCAM();
    myCAM.write_reg(ARDUCHIP_TIM, VSYNC_LEVEL_MASK);
    myCAM.OV5642_set_JPEG_size(OV5642_320x240);
    // myCAM.OV5642_set_JPEG_size(OV5642_2592x1944);
    delay(1000);
}

void loop()
{

    if (Serial.available())
    {
        char cmd = Serial.read();
        if (cmd == 's')
        { // 's' is the trigger command from your server
            captureAndSendImage();
        }
    }

    if (Serial.available())
    {
        char cmd = Serial.read();
        if (cmd == 'u')
        { // 's' is the trigger command from your server
            digitalWrite(53, HIGH);
            delay(1000);
            digitalWrite(53, LOW);
        }
    }

    if (Serial.available())
    {
        char cmd = Serial.read();
        if (cmd == 'd')
        { // 's' is the trigger command from your server
            digitalWrite(49, HIGH);
            delay(1000);
            digitalWrite(49, LOW);
        }
    }

    if (Serial.available())
    {
        char cmd = Serial.read();
        if (cmd == 'n')
        { // 's' is the trigger command from your server
            digitalWrite(3, HIGH);
            delay(1000);
            digitalWrite(3, LOW);
        }
    }
}

void captureAndSendImage()
{
    myCAM.flush_fifo();
    myCAM.clear_fifo_flag();
    myCAM.start_capture();

    while (!myCAM.get_bit(ARDUCHIP_TRIG, CAP_DONE_MASK))
        ;

    uint32_t len = myCAM.read_fifo_length();
    if (len > MAX_FIFO_SIZE || len == 0)
    {
        Serial.println("Invalid size.");
        return;
    }

    myCAM.CS_LOW();
    myCAM.set_fifo_burst();

    while (len--)
    {
        byte data = SPI.transfer(0x00);
        Serial.write(data);
        digitalWrite(2, HIGH);
    }

    digitalWrite(2, LOW);

    myCAM.CS_HIGH();
    myCAM.clear_fifo_flag();
}
