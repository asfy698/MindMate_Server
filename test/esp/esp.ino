#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";

#define IN1 26
#define IN2 27
#define IN3 32
#define IN4 33

#define FIRMWARE_VERSION "1.0"
#define MAX_DURATION 5

WebServer server(80);

String lastAction = "none";
int lastDuration = 0;
unsigned long bootTime;

void stopMotors()
{
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

void moveForward()
{
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void moveBackward()
{
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);

  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

String getTimeString()
{
  return String(millis() / 1000);
}

void handleHealth()
{
  String json = "{";
  json += "\"status\":\"online\",";
  json += "\"firmware\":\"" + String(FIRMWARE_VERSION) + "\",";
  json += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
  json += "\"uptime_seconds\":" + String((millis() / 1000)) + ",";
  json += "\"wifi_rssi\":" + String(WiFi.RSSI()) + ",";
  json += "\"free_heap\":" + String(ESP.getFreeHeap()) + ",";
  json += "\"last_action\":\"" + lastAction + "\",";
  json += "\"last_duration\":" + String(lastDuration);
  json += "}";

  Serial.println("\n================ HEALTH =================");
  Serial.println(json);
  Serial.println("=========================================\n");

  server.send(200, "application/json", json);
}

void handleMove()
{
  String action = server.arg("action");
  int duration = server.arg("duration").toInt();

  if (duration <= 0)
    duration = 1;

  if (duration > MAX_DURATION)
    duration = MAX_DURATION;

  Serial.println("\n================ REQUEST ================");
  Serial.print("Action : ");
  Serial.println(action);

  Serial.print("Duration : ");
  Serial.println(duration);

  Serial.print("Client : ");
  Serial.println(server.client().remoteIP());
  Serial.println("=========================================");

  lastAction = action;
  lastDuration = duration;

  String startTime = getTimeString();

  if (action == "forward")
  {
    moveForward();
    delay(duration * 1000);
    stopMotors();
  }
  else if (action == "backward")
  {
    moveBackward();
    delay(duration * 1000);
    stopMotors();
  }
  else if (action == "stop")
  {
    stopMotors();
  }
  else
  {
    server.send(400, "application/json",
                "{\"success\":false,\"error\":\"invalid_action\"}");
    return;
  }

  String endTime = getTimeString();

  String json = "{";
  json += "\"success\":true,";
  json += "\"action\":\"" + action + "\",";
  json += "\"duration\":" + String(duration) + ",";
  json += "\"status\":\"completed\",";
  json += "\"request_time\":\"" + startTime + "\",";
  json += "\"end_time\":\"" + endTime + "\",";
  json += "\"board_ip\":\"" + WiFi.localIP().toString() + "\"";
  json += "}";

  Serial.println("\n================ RESPONSE ===============");
  Serial.println(json);
  Serial.println("=========================================\n");

  server.send(200, "application/json", json);
}

void setup()
{
  Serial.begin(115200);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  stopMotors();

  bootTime = millis();

  Serial.println();
  Serial.println("=========================================");
  Serial.println("MindMate ESP32 Controller");
  Serial.println("Board Started");
  Serial.println("=========================================");

  WiFi.begin(ssid, password);

  Serial.println("Connecting WiFi...");

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Connected");

  Serial.print("IP : ");
  Serial.println(WiFi.localIP());

  Serial.println("Listening For Requests");

  server.on("/health", HTTP_GET, handleHealth);
  server.on("/move", HTTP_GET, handleMove);

  server.begin();
}

void loop()
{
  server.handleClient();
}

// #include <WiFi.h>
// #include <WebServer.h>

// const char* ssid = "Reaktek_AP_2.4G";
// const char* password = "4da7b1b84bd314e6461eca";

// WebServer server(80);

// #define IN1 26
// #define IN2 27
// #define IN3 32
// #define IN4 33

// void stopMotors()
// {
//   digitalWrite(IN1, LOW);
//   digitalWrite(IN2, LOW);
//   digitalWrite(IN3, LOW);
//   digitalWrite(IN4, LOW);
// }

// void moveForward()
// {
//   digitalWrite(IN1, HIGH);
//   digitalWrite(IN2, LOW);

//   digitalWrite(IN3, HIGH);
//   digitalWrite(IN4, LOW);

//   server.send(200, "text/plain", "FORWARD");
// }

// void moveBackward()
// {
//   digitalWrite(IN1, LOW);
//   digitalWrite(IN2, HIGH);

//   digitalWrite(IN3, LOW);
//   digitalWrite(IN4, HIGH);

//   server.send(200, "text/plain", "BACKWARD");
// }

// void stopRobot()
// {
//   stopMotors();
//   server.send(200, "text/plain", "STOP");
// }

// void setup()
// {
//   Serial.begin(115200);
//   delay(2000);
//   Serial.println("SETUP STARTED");

//   pinMode(IN1, OUTPUT);
//   pinMode(IN2, OUTPUT);
//   pinMode(IN3, OUTPUT);
//   pinMode(IN4, OUTPUT);

//   stopMotors();

//   WiFi.begin(ssid, password);

//   while (WiFi.status() != WL_CONNECTED)
//   {
//     delay(500);
//     Serial.print(".");
//   }

//   Serial.println();
//   Serial.println("Connected");

//   Serial.print("IP Address: ");
//   Serial.println(WiFi.localIP());

//   server.on("/forward", moveForward);
//   server.on("/backward", moveBackward);
//   server.on("/stop", stopRobot);

//   server.begin();
// }

// void loop()
// {
//   server.handleClient();
// }