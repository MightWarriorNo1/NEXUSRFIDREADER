# Testing Azure IoT Hub Integration with IPC

This guide explains how to test the IPC (Inter-Process Communication) → Azure IoT Hub → Azure Function → PostgreSQL flow before integrating into the main application.

## Overview

The test files simulate the complete data flow:
1. **Test Publisher** → sends scan data via Unix socket (simulates main RFID app)
2. **Test IoT Service** → receives data via socket and forwards to Azure IoT Hub
3. **Azure IoT Hub** → routes messages to Azure Function
4. **Azure Function** → stores data in PostgreSQL

## Prerequisites

1. **Azure IoT Hub** properly configured with your device
2. **Azure IoT service** already set up on Raspberry Pi (`/etc/azureiotpnp/provisioning_config.json` exists)
3. **Python dependencies** installed:
   ```bash
   sudo pip3 install azure-iot-device
   ```

## Testing Steps

### Step 1: Test Basic Socket Communication (Optional but Recommended)

Before testing with Azure IoT Hub, verify that Unix socket IPC works:

**Terminal 1 - Start simple socket server:**
```bash
sudo python3 utils_Test/test_simple_socket.py server
```

**Terminal 2 - Run simple socket client:**
```bash
python3 utils_Test/test_simple_socket.py client
```

**Expected Output:**
- Server shows "Client connected" and received messages
- Client shows "Connected!" and "Sent message X"

**If this works:** Socket IPC is functioning correctly ✓  
**If this fails:** Check file permissions and socket path

---

### Step 2: Test with Azure IoT Hub

Now test the complete flow with Azure IoT Hub.

#### 2.1 Start Test IoT Service

This service receives scan data via socket and forwards to Azure IoT Hub:

```bash
sudo python3 utils_Test/test_iot_service.py
```

**Expected Output:**
```
============================================================
Test Azure IoT Service with IPC Support
============================================================

✓ Loaded configuration for device: 1000000012345678
  Site: Lazer
  Truck: 0000000012345678
Starting device provisioning...
✓ Provisioned to hub: your-iothub.azure-devices.net
✓ Device ID: 1000000012345678
✓ Connected to IoT Hub
✓ Reported tags to IoT Hub

✓ Socket server listening on /var/run/nexus-iot.sock
Socket server ready to accept connections...
✓ Sent initial connection message

============================================================
Service is running and ready to receive scan data
Run test_iot_publisher.py to send test scans
Press Ctrl+C to stop
============================================================
```

**Troubleshooting:**
- **"Configuration file not found"**: Run Azure IoT device setup first
- **"Provisioning failed"**: Check Azure DPS credentials in config
- **"Connection failed"**: Verify network connectivity to Azure

#### 2.2 Send Test Scan Data

Keep the IoT service running, and in **another terminal**, send test scans:

```bash
python3 utils_Test/test_iot_publisher.py
```

To send a specific number of scans (e.g., 5):
```bash
python3 utils_Test/test_iot_publisher.py 5
```

**Expected Output:**
```
============================================================
Testing IoT Publisher (IPC Communication)
============================================================

Checking for socket file: /var/run/nexus-iot.sock
✓ Socket file exists

Sending test scan records...

--- Scan 1/3 ---
Tag: E20034120B1B017012345678
Location: (37.7749, -122.4194)
Speed: 15 km/h
✓ Connected to Azure IoT service at /var/run/nexus-iot.sock
✓ Sent scan to IoT Hub: E20034120B1B017012345678

--- Scan 2/3 ---
Tag: E20034120B1B017023456789
Location: (37.7749, -122.4194)
Speed: 15 km/h
✓ Sent scan to IoT Hub: E20034120B1B017023456789

--- Scan 3/3 ---
Tag: E20034120B1B017034567890
Location: (37.7749, -122.4194)
Speed: 15 km/h
✓ Sent scan to IoT Hub: E20034120B1B017034567890

✓ Socket connection closed

============================================================
Test completed!
============================================================
```

**In the IoT Service Terminal (Terminal 1)**, you should see:
```
✓ New client connected
✓ [1] Sent scan to IoT Hub: E20034120B1B017012345678
   Location: (37.7749, -122.4194)
   Site: Lazer, Truck: 0000000012345678
✓ [2] Sent scan to IoT Hub: E20034120B1B017023456789
   Location: (37.7749, -122.4194)
   Site: Lazer, Truck: 0000000012345678
✓ [3] Sent scan to IoT Hub: E20034120B1B017034567890
   Location: (37.7749, -122.4194)
   Site: Lazer, Truck: 0000000012345678
Client disconnected
```

---

### Step 3: Verify in Azure Portal

#### 3.1 Check IoT Hub Metrics

1. Go to **Azure Portal** → Your IoT Hub
2. Navigate to **Metrics**
3. Add metric: **Telemetry messages sent**
4. You should see message count increase

#### 3.2 Use Azure IoT Explorer

1. Install [Azure IoT Explorer](https://github.com/Azure/azure-iot-explorer/releases)
2. Connect to your IoT Hub
3. Select your device
4. Go to **Telemetry**
5. Click **Start** to monitor messages
6. You should see scan messages with data like:
   ```json
   {
     "siteId": "019a9e1e-81ff-75ab-99fc-4115bb92fec6",
     "tagName": "E20034120B1B017012345678",
     "latitude": 37.7749,
     "longitude": -122.4194,
     "speed": 15.0,
     "deviceId": "1000000012345678",
     "antenna": "1",
     "barrier": 270.0,
     "comment": null,
     "metadata": {
       "siteName": "Lazer",
       "truckNumber": "TestTruck001",
       "timestamp": 1234567890123456
     },
     "deviceInfo": {
       "registrationId": "1000000012345678",
       "deviceId": "1000000012345678",
       "siteName": "Lazer",
       "truckNumber": "0000000012345678",
       "deviceSerial": "0000000012345678"
     }
   }
   ```
   
   **Note**: This format matches your C# Azure Function (`IotHubToPostgres.cs`)

---

### Step 4: Verify Azure Function Processing (If Deployed)

If you've deployed the Azure Function:

1. Go to **Azure Portal** → Your Function App
2. Navigate to **Functions** → Your function → **Monitor**
3. Check **Invocation Traces** for executions
4. Look for logs showing "Processing scan: E20034120B1B017012345678"
5. Verify no errors in execution

#### Check PostgreSQL

If Azure Function is working, query your PostgreSQL database:

```sql
-- Query the Scans table (your C# function schema)
SELECT * FROM public."Scans" 
WHERE "IsDeleted" = FALSE
ORDER BY "CreatedOn" DESC 
LIMIT 10;

-- Or use the ActiveScans view
SELECT * FROM public."ActiveScans"
LIMIT 10;
```

You should see your test scan records with:
- `TagName` starting with "E20034120B1B..."
- `SiteId`: `019a9e1e-81ff-75ab-99fc-4115bb92fec6`
- `DeviceId`, `Latitude`, `Longitude`, `Speed` populated
- `CreatedOn` timestamps showing when records were inserted
- `Barrier` field with bearing/heading value (270.0)

---

## Troubleshooting

### Socket File Not Found
```
✗ Socket file not found: /var/run/nexus-iot.sock
```
**Solution:** Make sure `test_iot_service.py` is running

### Permission Denied
```
PermissionError: [Errno 13] Permission denied: '/var/run/nexus-iot.sock'
```
**Solution:** Run IoT service with sudo:
```bash
sudo python3 utils_Test/test_iot_service.py
```

### Connection Refused
```
✗ Connection refused to /var/run/nexus-iot.sock
```
**Solution:** IoT service may not have started socket server. Check service output for errors.

### No Messages in Azure IoT Hub
**Check:**
1. IoT service shows "Sent scan to IoT Hub" messages
2. Device is properly provisioned (check IoT service startup logs)
3. Network connectivity: `ping global.azure-devices-provisioning.net`
4. IoT Hub metrics show device as connected

### Azure Function Not Triggering
**Check:**
1. Function App is running (not stopped)
2. IoT Hub message routing is configured
3. Function connection string is correct
4. Check Function App logs for errors

---

## Next Steps

Once testing is successful:

1. **Verify Data Flow End-to-End:**
   - IPC communication works ✓
   - Messages reach Azure IoT Hub ✓
   - Azure Function processes messages ✓
   - Data appears in PostgreSQL ✓

2. **Integrate into Main Application:**
   - Copy `utils_Test/test_iot_publisher.py` → `utils/iot_publisher.py`
   - Modify `Azure-IoT-Connection/iot_service.py` with socket server code
   - Update `screens/overview.py` to use IoT publisher instead of REST API
   - Update `requirements.txt` if needed

3. **Deploy Azure Function (C#):**
   - See `CSHARP_AZURE_FUNCTION.md` for complete C# deployment instructions
   - Your existing C# code is fully compatible with the test flow

4. **Update Production IoT Service:**
   - Restart Azure IoT service with new code
   - Verify socket permissions
   - Monitor logs during initial deployment

---

## Test Files Summary

| File | Purpose |
|------|---------|
| `test_simple_socket.py` | Basic socket communication test (no Azure) |
| `test_iot_service.py` | Full IoT service with socket server + Azure IoT Hub |
| `test_iot_publisher.py` | Simulates main app sending scan data via IPC |
| `TEST_INSTRUCTIONS.md` | This file - complete testing guide |

---

## Support

If you encounter issues:
1. Check service logs: `sudo journalctl -u azure-iot.service -f`
2. Verify Azure IoT Hub connection in Azure Portal
3. Check socket file permissions: `ls -l /var/run/nexus-iot.sock`
4. Test network connectivity to Azure
