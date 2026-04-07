# 📡 Reliable UDP Group Notification System with Security

## 📌 Introduction

This project implements a **reliable group notification system over UDP**, enhanced with **security mechanisms**. Since UDP does not guarantee delivery, this system ensures reliable communication using acknowledgements, retransmissions, and timeout handling.

Additionally, messages are protected using encryption and authentication techniques to ensure **secure data transmission**.

---

## 🎯 Objectives

* Achieve reliable communication over UDP
* Implement acknowledgement and retransmission logic
* Secure messages using encryption techniques
* Simulate real-world network conditions

---

## 🚀 Features

* 📡 UDP-based client-server communication
* 🔁 Reliable delivery using ACK and retransmission
* ⏱️ Timeout handling for lost packets
* 🔐 Secure message encryption and authentication
* 👥 Multiple client subscription support
* ⚠️ Duplicate and loss packet handling
* 🧪 Performance and smoke testing included

---

## 🧠 Concepts Used

* Computer Networks (UDP Protocol)
* Reliable Data Transfer
* Socket Programming
* Encryption & Authentication (HMAC, Key Derivation)
* Multithreading
* Client-Server Architecture

---

## 🛠️ Technologies Used

* Language: Python
* Libraries: socket, threading, hashlib, hmac
* Platform: Command Line

---

## 📂 Project Structure

* `server.py` → Handles message broadcasting 
* `client.py` → Receives and processes messages 
* `packet.py` → Packet creation and parsing 
* `constants.py` → Configuration settings 
* `ssl_config.py` → Encryption and security logic 
* `performance_test.py` → Performance evaluation 
* `smoke_test.py` → Functional testing 

---

## ▶️ How to Run
(Windows PowerShell)

### Step 1:  Run Server

```bash
$env:UDP_SHARED_SECRET="right_"
python server.py
```

---

### Step 2: Run Client(s)

```bash
$env:UDP_CLIENT_SERVER_HOST="192.168.X.X"
$env:UDP_SHARED_SECRET="right_"
python client.py
```

---

## 📋 Working

1. Clients subscribe to the server
2. Server broadcasts alert messages
3. Clients receive and send ACK
4. If ACK not received → retransmission occurs
5. Encryption ensures secure communication

---

## 🧪 Testing

* Performance testing for latency and throughput
* Smoke testing for basic functionality

---

## ⚠️ Limitations

* Works on local or controlled network
* No GUI interface
* Basic reliability model

---

## 🔮 Future Scope

* Add GUI dashboard
* Improve congestion control
* Use advanced encryption protocols
* Deploy on cloud environment

---

## Authors

Praakruthi PS
Pruthviraj Patil
Pooja Avadhani

---

## ⭐ Conclusion

This project demonstrates how reliable and secure communication can be achieved over an unreliable protocol like UDP using networking and cryptographic concepts.
