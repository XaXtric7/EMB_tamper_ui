#define F_CPU 8000000UL
#include <avr/io.h>
#include <util/delay.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>

#define HALL_PIN PD4
#define LED_PIN PD5

#define ADC_VOLT_CH 0
#define ADC_CURR_CH 1

// UART
void UART_init(uint16_t ubrr)
{
    UBRR0H = (ubrr >> 8);
    UBRR0L = ubrr & 0xFF;
    UCSR0B = (1 << TXEN0);                  // Enable TX only
    UCSR0C = (1 << UCSZ01) | (1 << UCSZ00); // 8-bit data
}

void UART_tx(char data)
{
    while (!(UCSR0A & (1 << UDRE0)))
        ;
    UDR0 = data;
}

void UART_send_string(char *s)
{
    while (*s)
        UART_tx(*s++);
}

// ADC
void ADC_Init()
{
    ADMUX = (1 << REFS0);                               // AVcc reference
    ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1); // ADC enable, prescaler 64
}

uint16_t ADC_Read(uint8_t ch)
{
    ADMUX = (ADMUX & 0xF0) | (ch & 0x0F);
    ADCSRA |= (1 << ADSC);
    while (ADCSRA & (1 << ADSC))
        ;
    return ADC;
}

int main(void)
{

    DDRD |= (1 << LED_PIN);   // LED output
    DDRD &= ~(1 << HALL_PIN); // Hall sensor input
    PORTD |= (1 << HALL_PIN); // Pull-up

    UART_init(51); // 9600 baud at 8 MHz
    ADC_Init();

    char vbuf[10], cbuf[10], out[50];

    while (1)
    {

        // Read voltage
        uint16_t v_adc = ADC_Read(ADC_VOLT_CH);
        float voltage = (v_adc * 5.0) / 1023.0;
        bool volt_tamper = (voltage < 2.5);

        // Read current
        uint16_t c_adc = ADC_Read(ADC_CURR_CH);
        int16_t delta = (int16_t)c_adc - 512;
        float current = delta / 37.0;
        bool curr_tamper = (delta > 3 || delta < -3);

        // Read hall sensor
        bool magnetic_field = !(PIND & (1 << HALL_PIN));
        bool hall_tamper = magnetic_field;

        // LED for tamper
        bool tamper = volt_tamper || curr_tamper || hall_tamper;
        if (tamper)
            PORTD |= (1 << LED_PIN);
        else
            PORTD &= ~(1 << LED_PIN);

        // Convert floats safely
        dtostrf(voltage, 4, 2, vbuf);
        dtostrf(current, 4, 3, cbuf);

        // Send CSV: voltage,current,magnetic_field
        sprintf(out, "%s,%s,%d\r\n", vbuf, cbuf, magnetic_field);
        UART_send_string(out);

        // Optional: send debug line for troubleshooting
        // sprintf(out, "V: %s, I: %s, M: %d, T: %d\r\n", vbuf, cbuf, magnetic_field, tamper);
        // UART_send_string(out);

        _delay_ms(50); // allow USB–TTL buffer to catch up
    }
}