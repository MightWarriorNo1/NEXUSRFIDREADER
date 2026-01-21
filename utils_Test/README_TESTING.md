# Testing Overview - Azure IoT Hub Integration

Quick reference guide for testing the IPC → Azure IoT Hub → C# Function → PostgreSQL flow.

## 🎯 Quick Start

**Prerequisites:**
- Azure IoT Hub configured with your device
- Azure IoT service running on Raspberry Pi
- C# Azure Function deployed (see `CSHARP_AZURE_FUNCTION.md`)

## 📋 Test Files

| File | Purpose | Where to Run |
|------|---------|--------------|
| `test_simple_socket.py` | Basic IPC test (no Azure) | Raspberry Pi |
| `test_iot_service.py` | Full IoT service with socket server | Raspberry Pi (sudo) |
| `test_iot_publisher.py` | Sends test scans via IPC | Raspberry Pi |
| `TEST_INSTRUCTIONS.md` | Detailed step-by-step guide | Documentation |
| `CSHARP_AZURE_FUNCTION.md` | C# Function deployment guide | Documentation |

## 🚀 Testing Sequence

### 1. Test Basic IPC (5 minutes)

Verify Unix socket communication works:

```bash
# Terminal 1
sudo python3 utils_Test/test_simple_socket.py server

# Terminal 2
python3 utils_Test/test_simple_socket.py client
```

**Expected:** Messages sent and received successfully ✓

---

### 2. Test with Azure IoT Hub (10 minutes)

#### Start IoT Service

```bash
# Terminal 1 - Keep running
sudo python3 utils_Test/test_iot_service.py
```

**Expected output:**
```
✓ Connected to IoT Hub
✓ Socket server listening on /var/run/nexus-iot.sock
Service is running and ready to receive scan data
```

#### Send Test Scans

```bash
# Terminal 2
python3 utils_Test/test_iot_publisher.py 3
```

**Expected output:**
```
✓ Connected to Azure IoT service
✓ Sent scan to IoT Hub: E20034120B1B017012345678
✓ Sent scan to IoT Hub: E20034120B1B017023456789
✓ Sent scan to IoT Hub: E20034120B1B017034567890
Test completed!
```

---

### 3. Verify in Azure (5 minutes)

#### Check IoT Hub Metrics

1. Azure Portal → IoT Hub → Metrics
2. Metric: "Telemetry messages sent"
3. Should show 3 new messages ✓

#### Use Azure IoT Explorer (Recommended)

1. Download from [GitHub](https://github.com/Azure/azure-iot-explorer/releases)
2. Connect to IoT Hub
3. Monitor device telemetry
4. Verify messages contain `tagName`, `latitude`, `longitude`, etc.

---

### 4. Verify C# Azure Function (5 minutes)

#### Check Function Logs

```bash
# Azure Portal
Function App → Monitor → Logs
```

**Expected:**
```
Inserted 3 rows into public."Scans".
```

#### Query PostgreSQL

```sql
SELECT * FROM public."ActiveScans"
ORDER BY "CreatedOn" DESC
LIMIT 10;
```

**Expected:** 3 new rows with test data ✓

---

## ✅ Success Criteria

- [x] IPC socket communication works
- [x] Messages reach Azure IoT Hub
- [x] C# Function processes messages
- [x] Data appears in PostgreSQL
- [x] No errors in logs

---

## 🔧 Common Issues

### Socket file not found

```bash
# Make sure IoT service is running
sudo python3 utils_Test/test_iot_service.py
```

### Permission denied

```bash
# Always use sudo for IoT service
sudo python3 utils_Test/test_iot_service.py
```

### Function not triggering

- Check consumer group exists: `func-cg-nexuslocate`
- Verify `IOTHUB_CONNECTION` in Function App settings
- Ensure Function App is running (not stopped)

### Database connection errors

- Check PostgreSQL firewall allows Azure services
- Verify `POSTGRES_CONN` connection string
- Test connection from Azure Cloud Shell

---

## 📊 Message Format

The test publisher sends messages compatible with your C# function:

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
  "comment": null
}
```

**Mapped to PostgreSQL:**
- `tagName` → `TagName` (VARCHAR)
- `siteId` → `SiteId` (UUID)
- `latitude` → `Latitude` (DOUBLE PRECISION)
- `longitude` → `Longitude` (DOUBLE PRECISION)
- `speed` → `Speed` (DOUBLE PRECISION)
- `deviceId` → `DeviceId` (VARCHAR)
- `antenna` → `Antenna` (VARCHAR)
- `barrier` → `Barrier` (DOUBLE PRECISION)

---

## 🔄 Next Steps After Testing

1. **Integrate into main application:**
   - Copy `utils_Test/test_iot_publisher.py` → `utils/iot_publisher.py`
   - Modify `Azure-IoT-Connection/iot_service.py` with socket server
   - Update `screens/overview.py` to use IoT publisher

2. **Deploy to production:**
   - Update production IoT service
   - Monitor initial data flow
   - Set up alerts in Azure

3. **Monitor performance:**
   - Azure Function execution metrics
   - PostgreSQL query performance
   - Message processing latency

---

## 📚 Documentation

- **`TEST_INSTRUCTIONS.md`** - Detailed testing steps
- **`CSHARP_AZURE_FUNCTION.md`** - C# Function deployment
- **`AZURE_FUNCTION_SETUP.md`** - (Legacy Python guide, ignore)

---

## 🆘 Need Help?

1. Check `TEST_INSTRUCTIONS.md` for detailed troubleshooting
2. Review Azure Function logs for errors
3. Verify IoT Hub device connectivity
4. Test PostgreSQL connection independently

**Architecture Diagram:**

```
Raspberry Pi RFID App
    ↓ (Unix Socket IPC)
Azure IoT Service (Python)
    ↓ (MQTT over TLS)
Azure IoT Hub
    ↓ (Event Hub Trigger)
C# Azure Function
    ↓ (Npgsql)
Azure PostgreSQL Database
```

---

**Ready to start?** Begin with Step 1 (basic IPC test)!
