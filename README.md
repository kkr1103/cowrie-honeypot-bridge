Cowrie Honeypot Real-Time Event Viewer

This project demonstrates a real-time monitoring bridge for the Cowrie SSH/Telnet honeypot.
It reads Cowrie’s JSON log in real time, parses attacker activity, and displays it in a web dashboard.
This serves as Phase 1 of a future Wazuh integration for SIEM-style alerting and automation.

Project Overview
The system consists of three main parts:
1. cowrie_bridge.py – a Python script that continuously reads Cowrie’s JSON log file, extracts key details, and writes a simplified JSON feed.
2. cowrie_viewer.html – a lightweight HTML and JavaScript page that refreshes every two seconds to show live events from the JSON feed.
3. generate_cowrie_test.sh – a shell script that generates synthetic Cowrie events and creates an evidence snapshot for demonstration and testing.
Evidence files such as cowrie_events.json and cowrie_events_snapshot.json are included to document the system output.

How It Works:
1. Cowrie honeypot logs all SSH/Telnet activity to /opt/cowrie/var/log/cowrie/cowrie.json
2. The Python bridge script tails that log file, extracts key data such as:
. login attempts (success or failed)
. commands executed
. file uploads or downloads
3. The filtered events are written to /opt/cowrie-bridge/out/cowrie_events.json
4. The Apache web server serves this JSON file through /cowrie_out/ and cowrie_viewer.html fetches and displays the latest events automatically.

Example Event

{
"ts": "2025-11-05T02:29:34Z",
"evt": "cowrie.login.failed",
"ip": "10.10.20.30",
"user": "root",
"pw": "pass20"
}

Testing and Evidence Generation
Run the test generator script to simulate attacker activity:
sudo ./generate_cowrie_test.sh
This will:
. Generate 20 synthetic Cowrie events
. Restart the bridge service if installed
. Save a snapshot of the processed JSON output in /opt/cowrie-bridge/test-evidence/cowrie_events_snapshot.json
You can then copy the snapshot file into the evidence folder of this project for reference.

Technologies Used:
. Cowrie Honeypot
. Python 3
. Apache 2
. HTML and JavaScript
. Bash scripting

Security Notes:
. This project is intended for educational and laboratory use only.
. Do not expose Cowrie or this dashboard to the public internet without authentication or isolation.
. It is designed to demonstrate log monitoring and visualization, not active network defense.

