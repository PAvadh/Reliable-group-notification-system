# Reliable-group-notification-system

UDP-based group notification system that reliably delivers alerts to multiple subscribers with acknowledgement, re-transmission, and timeout handling.

## Overview

This project implements a reliable group notification system using UDP protocol. Since UDP does not guarantee delivery, this system ensures reliability through acknowledgement, retransmission, and timeout mechanisms.

## Features

* Reliable message delivery over UDP
* Acknowledgement handling
* Retransmission mechanism
* Timeout detection
* Multiple subscriber support
* Lightweight and fast communication

## Technologies Used

* Python (or C / Java — change based on your project)
* UDP Socket Programming
* Networking Concepts

## Project Structure

*File	                    Description
server.py	            Sends notifications to clients
client.py	            Receives notifications
packet.py	            Handles packet creation and processing
constants.py	        Stores configuration constants
performance_test.py	    Tests system performance
smoke_test.py	        Basic functionality testing
ssl_config.py	        SSL security configuration
README.md	            Project documentation

## How to Run

### Step 1: Clone Repository

git clone https://github.com/PAvadh/Reliable-group-notification-system.git

### Step 2: Run Server

python server.py

### Step 3: Run Client

python client.py

## Use Cases

* Group alert systems
* Emergency notification systems
* Lab communication system
* Classroom announcements

## Authors

Praakruthi
Prithviraj
Pooja Avadhani

## 📎 GitHub Repository

https://github.com/PAvadh/Reliable-group-notification-system
