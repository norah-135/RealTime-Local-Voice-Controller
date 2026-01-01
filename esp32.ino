#include <driver/i2s.h>

#define I2S_SD 25 
#define I2S_WS 26
#define I2S_SCK 27
#define I2S_PORT I2S_NUM_0
#define LED_PIN 17 

const int sample_rate = 16000;
const int record_seconds = 2;
const int VAD_THRESHOLD = 1200; 

void setupI2S() {
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = sample_rate,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = (i2s_comm_format_t)(I2S_COMM_FORMAT_I2S | I2S_COMM_FORMAT_I2S_MSB),
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 1024,
    .use_apll = false
  };
  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_SCK, .ws_io_num = I2S_WS, .data_out_num = I2S_PIN_NO_CHANGE, .data_in_num = I2S_SD
  };
  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_PORT, &pin_config);
}

void setup() {
  Serial.begin(921600); 
  pinMode(LED_PIN, OUTPUT);
  setupI2S();
  Serial.println("\n[ESP32] Fast Trigger Mode Ready");
}

void loop() {
  size_t bytesRead;
  int32_t sample = 0;
  
  i2s_read(I2S_PORT, &sample, 4, &bytesRead, portMAX_DELAY);
  int currentVolume = abs(sample >> 14); 

  if (currentVolume > VAD_THRESHOLD) {
    Serial.println("\n[RECORDING]");
    
    for (int i = 0; i < (sample_rate * record_seconds); i++) {
      int32_t rawSample;
      i2s_read(I2S_PORT, &rawSample, 4, &bytesRead, portMAX_DELAY);
      int16_t processedSample = (int16_t)((rawSample >> 14) & 0xFFFF);
      Serial.write((uint8_t*)&processedSample, sizeof(processedSample));
      delayMicroseconds(2); 
    }
    
    Serial.println("\n[DONE]");
    Serial.flush();
  }

  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == '1') digitalWrite(LED_PIN, HIGH);
    else if (command == '0') digitalWrite(LED_PIN, LOW);
  }
}