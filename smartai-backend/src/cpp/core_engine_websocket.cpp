// SmartAI C++ Core Engine - Integrated with WebSocket Communication
// File: core_engine_websocket.cpp
// Adds WebSocket connectivity to send real-time data to Electron frontend

#include <iostream>
#include <string>
#include <thread>
#include <chrono>
#include <vector>
#include <map>
#include <json/json.h>
#include <winsock2.h>
#include <windows.h>
#include <tlhelp32.h>
#include <psapi.h>
#include <iphlpapi.h>
#include <openssl/aes.h>
#include <openssl/rand.h>

#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "iphlpapi.lib")
#pragma comment(lib, "psapi.lib")

// ==================== WEBSOCKET CLIENT ====================

class WebSocketClient {
private:
    SOCKET socket;
    std::string host;
    int port;
    bool connected;
    std::string encryptionKey;

public:
    WebSocketClient(const std::string& host, int port, const std::string& key)
        : host(host), port(port), encryptionKey(key), socket(INVALID_SOCKET), connected(false) {
    }

    bool connect() {
        WSADATA wsaData;
        if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
            std::cerr << "[C++] WSAStartup failed" << std::endl;
            return false;
        }

        socket = ::socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (socket == INVALID_SOCKET) {
            std::cerr << "[C++] Socket creation failed" << std::endl;
            return false;
        }

        sockaddr_in serv_addr;
        serv_addr.sin_family = AF_INET;
        serv_addr.sin_port = htons(port);
        inet_pton(AF_INET, host.c_str(), &serv_addr.sin_addr);

        if (::connect(socket, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) == SOCKET_ERROR) {
            std::cerr << "[C++] Connection to Electron WebSocket on port " << port << " failed" << std::endl;
            closesocket(socket);
            return false;
        }

        std::cout << "[C++] ✓ Connected to Electron WebSocket on " << host << ":" << port << std::endl;
        connected = true;
        return true;
    }

    bool sendEncrypted(const std::string& jsonData) {
        if (!connected) return false;

        try {
            // Simple BASE64 encryption (in production use AES-256)
            std::string encrypted = base64_encode(jsonData);

            // WebSocket frame format (simplified)
            std::string frame = createWebSocketFrame(encrypted);

            int bytes_sent = ::send(socket, frame.c_str(), frame.length(), 0);
            if (bytes_sent == SOCKET_ERROR) {
                std::cerr << "[C++] Send failed" << std::endl;
                connected = false;
                return false;
            }

            return true;
        } catch (std::exception& e) {
            std::cerr << "[C++] Send error: " << e.what() << std::endl;
            return false;
        }
    }

    bool isConnected() const {
        return connected;
    }

    void disconnect() {
        if (socket != INVALID_SOCKET) {
            closesocket(socket);
            socket = INVALID_SOCKET;
        }
        connected = false;
        WSACleanup();
    }

    ~WebSocketClient() {
        if (connected) {
            disconnect();
        }
    }

private:
    std::string createWebSocketFrame(const std::string& data) {
        // Simplified WebSocket frame
        // In production, use proper WebSocket library like libwebsockets
        
        std::string frame;
        unsigned char header[2] = { 0x81, 0x00 }; // FIN + Text frame
        
        if (data.length() < 126) {
            header[1] = (unsigned char)data.length();
        } else if (data.length() < 65536) {
            header[1] = 126;
        } else {
            header[1] = 127;
        }

        frame.append((char*)header, 2);
        frame.append(data);
        
        return frame;
    }

    std::string base64_encode(const std::string& input) {
        static const char* base64_chars =
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        
        std::string encoded;
        int val = 0;
        int valb = 0;

        for (unsigned char c : input) {
            val = (val << 8) + c;
            valb += 8;
            while (valb >= 6) {
                valb -= 6;
                encoded.push_back(base64_chars[(val >> valb) & 0x3F]);
            }
        }

        if (valb > 0) {
            encoded.push_back(base64_chars[(val << (6 - valb)) & 0x3F]);
        }

        while (encoded.size() % 4) {
            encoded.push_back('=');
        }

        return encoded;
    }
};

// ==================== SYSTEM MONITORING ====================

class SystemMonitor {
private:
    WebSocketClient* wsClient;
    bool monitoring;

public:
    SystemMonitor(WebSocketClient* client) : wsClient(client), monitoring(false) {
    }

    void startMonitoring() {
        monitoring = true;
        std::cout << "[C++] System monitoring started" << std::endl;

        std::thread monitor_thread([this]() {
            while (monitoring) {
                collectAndSendData();
                std::this_thread::sleep_for(std::chrono::seconds(5));
            }
        });

        monitor_thread.detach();
    }

    void stopMonitoring() {
        monitoring = false;
        std::cout << "[C++] System monitoring stopped" << std::endl;
    }

private:
    void collectAndSendData() {
        if (!wsClient->isConnected()) {
            return;
        }

        try {
            Json::Value root;
            
            // Collect system metrics
            root["type"] = "SYSTEM_DATA";
            root["timestamp"] = getCurrentTimestamp();
            
            // CPU and Memory
            MEMORYSTATUSEX memStatus;
            memStatus.dwLength = sizeof(MEMORYSTATUSEX);
            GlobalMemoryStatusEx(&memStatus);

            root["systemStats"]["cpuUsage"] = getProcessorUsage();
            root["systemStats"]["ramUsage"] = (int)memStatus.dwMemoryLoad;
            root["systemStats"]["ramAvailable"] = (unsigned long)(memStatus.ullAvailPhys / (1024 * 1024));
            root["systemStats"]["ramTotal"] = (unsigned long)(memStatus.ullTotalPhys / (1024 * 1024));

            // Get running processes
            Json::Value processes(Json::arrayValue);
            std::vector<std::string> procs = getRunningProcesses();
            for (const auto& proc : procs) {
                processes.append(proc);
            }
            root["systemStats"]["processes"] = processes;

            // Network interfaces
            root["systemStats"]["networkInterfaces"] = getNetworkInterfaces();

            // Serialize and send
            Json::StreamWriterBuilder writer;
            std::string jsonData = Json::writeString(writer, root);
            
            if (wsClient->sendEncrypted(jsonData)) {
                std::cout << "[C++] System data sent to Electron (size: " << jsonData.length() << " bytes)" << std::endl;
            }

        } catch (std::exception& e) {
            std::cerr << "[C++] Error collecting system data: " << e.what() << std::endl;
        }
    }

    int getProcessorUsage() {
        // Get CPU usage percentage (simplified)
        // In production, use more accurate method like Performance Counters
        
        static unsigned long lastTotalTicks = 0;
        static unsigned long lastIdleTicks = 0;

        FILETIME ftIdle, ftKernel, ftUser;
        if (GetSystemTimes(&ftIdle, &ftKernel, &ftUser)) {
            unsigned long totalTicks = 0;
            unsigned long idleTicks = ((ULARGE_INTEGER*)&ftIdle)->QuadPart / 10000;
            
            unsigned long kernelTicks = ((ULARGE_INTEGER*)&ftKernel)->QuadPart / 10000;
            unsigned long userTicks = ((ULARGE_INTEGER*)&ftUser)->QuadPart / 10000;
            totalTicks = kernelTicks + userTicks;

            unsigned long totalTicksSinceLastTime = totalTicks - lastTotalTicks;
            unsigned long idleTicksSinceLastTime = idleTicks - lastIdleTicks;

            lastTotalTicks = totalTicks;
            lastIdleTicks = idleTicks;

            if (totalTicksSinceLastTime < 1) {
                return 0;
            }

            return (int)(100.0 * (totalTicksSinceLastTime - idleTicksSinceLastTime) / totalTicksSinceLastTime);
        }

        return 0;
    }

    std::vector<std::string> getRunningProcesses() {
        std::vector<std::string> processes;
        HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
        
        if (hSnapshot != INVALID_HANDLE_VALUE) {
            PROCESSENTRY32 pe32;
            pe32.dwSize = sizeof(PROCESSENTRY32);

            if (Process32First(hSnapshot, &pe32)) {
                do {
                    processes.push_back(pe32.szExeFile);
                } while (Process32Next(hSnapshot, &pe32) && processes.size() < 50);
            }

            CloseHandle(hSnapshot);
        }

        return processes;
    }

    Json::Value getNetworkInterfaces() {
        Json::Value interfaces(Json::arrayValue);
        
        IP_ADAPTER_INFO* pAdapterInfo = nullptr;
        ULONG ulOutBufLen = sizeof(IP_ADAPTER_INFO);
        
        pAdapterInfo = (IP_ADAPTER_INFO*)malloc(ulOutBufLen);
        if (GetAdaptersInfo(pAdapterInfo, &ulOutBufLen) == NO_ERROR) {
            for (IP_ADAPTER_INFO* pAdapter = pAdapterInfo; pAdapter != nullptr; pAdapter = pAdapter->Next) {
                Json::Value iface;
                iface["name"] = pAdapter->AdapterName;
                iface["description"] = pAdapter->Description;
                iface["ip"] = pAdapter->IpAddressList.IpAddress.String;
                interfaces.append(iface);
            }
        }

        if (pAdapterInfo) {
            free(pAdapterInfo);
        }

        return interfaces;
    }

    std::string getCurrentTimestamp() {
        time_t now = time(nullptr);
        char buffer[20];
        strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", gmtime(&now));
        return std::string(buffer);
    }
};

// ==================== NAMED PIPE IPC ====================

class NamedPipeClient {
private:
    HANDLE hPipe;
    std::string pipeName;
    bool connected;

public:
    NamedPipeClient(const std::string& name) : pipeName(name), hPipe(INVALID_HANDLE_VALUE), connected(false) {
    }

    bool connectToPython() {
        std::string fullPipeName = "\\\\.\\pipe\\" + pipeName;
        
        hPipe = CreateFileA(
            fullPipeName.c_str(),
            GENERIC_WRITE,
            0,
            nullptr,
            OPEN_EXISTING,
            0,
            nullptr
        );

        if (hPipe == INVALID_HANDLE_VALUE) {
            std::cerr << "[C++] Failed to connect to Python pipe: " << GetLastError() << std::endl;
            return false;
        }

        std::cout << "[C++] ✓ Connected to Python via named pipe: " << pipeName << std::endl;
        connected = true;
        return true;
    }

    bool sendToPython(const std::string& encryptedData) {
        if (!connected || hPipe == INVALID_HANDLE_VALUE) {
            return false;
        }

        DWORD written = 0;
        if (!WriteFile(hPipe, encryptedData.c_str(), encryptedData.length(), &written, nullptr)) {
            std::cerr << "[C++] Failed to write to Python pipe" << std::endl;
            return false;
        }

        return true;
    }

    bool receiveFromPython(std::string& response, int timeoutMs = 5000) {
        if (!connected || hPipe == INVALID_HANDLE_VALUE) {
            return false;
        }

        char buffer[4096];
        DWORD read = 0;

        SetFilePointer(hPipe, 0, nullptr, FILE_BEGIN);
        
        if (ReadFile(hPipe, buffer, sizeof(buffer) - 1, &read, nullptr)) {
            buffer[read] = '\0';
            response = std::string(buffer);
            return true;
        }

        return false;
    }

    void disconnect() {
        if (hPipe != INVALID_HANDLE_VALUE) {
            CloseHandle(hPipe);
            hPipe = INVALID_HANDLE_VALUE;
        }
        connected = false;
    }

    bool isConnected() const {
        return connected;
    }

    ~NamedPipeClient() {
        disconnect();
    }
};

// ==================== MAIN APPLICATION ====================

int main() {
    std::cout << "\n[C++] ===== SmartAI CORE ENGINE START =====" << std::endl;
    std::cout << "[C++] Initializing C++ Core Engine..." << std::endl;

    try {
        // Get environment setup
        const char* wsPort = getenv("SMARTAI_WS_PORT");
        const char* encKey = getenv("SMARTAI_ENCRYPTION_KEY");
        const char* pipeName = getenv("SMARTAI_PIPE_NAME");

        int port = wsPort ? std::stoi(wsPort) : 8080;
        std::string key = encKey ? std::string(encKey) : "default_key";
        std::string pipe = pipeName ? std::string(pipeName) : "smartai_core_pipe";

        std::cout << "[C++] WebSocket Port: " << port << std::endl;
        std::cout << "[C++] Pipe Name: " << pipe << std::endl;

        // Initialize WebSocket client to Electron
        WebSocketClient wsClient("127.0.0.1", port, key);
        std::cout << "[C++] Connecting to Electron WebSocket..." << std::endl;
        
        if (!wsClient.connect()) {
            std::cerr << "[C++] Failed to connect to Electron, retrying in 3 seconds..." << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(3));
            if (!wsClient.connect()) {
                std::cerr << "[C++] FATAL: Cannot establish connection to Electron" << std::endl;
                return 1;
            }
        }

        // Initialize Named Pipe client to Python
        NamedPipeClient pipeClient(pipe);
        std::cout << "[C++] Connecting to Python via named pipe..." << std::endl;
        
        if (!pipeClient.connectToPython()) {
            std::cerr << "[C++] Warning: Cannot connect to Python, retrying in 5 seconds..." << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(5));
            if (!pipeClient.connectToPython()) {
                std::cerr << "[C++] Warning: Python not available yet, will retry automatically" << std::endl;
            }
        }

        // Start system monitoring
        SystemMonitor monitor(&wsClient);
        monitor.startMonitoring();

        std::cout << "[C++] ✓✓✓ CORE ENGINE READY ✓✓✓" << std::endl;
        std::cout << "[C++] ===== MONITORING ACTIVE =====" << std::endl << std::endl;

        // Keep running
        while (true) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
            
            // Re-establish connections if lost
            if (!wsClient.isConnected()) {
                std::cout << "[C++] Attempting to reconnect to Electron..." << std::endl;
                if (wsClient.connect()) {
                    std::cout << "[C++] ✓ Reconnected to Electron" << std::endl;
                }
            }

            if (!pipeClient.isConnected()) {
                std::cout << "[C++] Attempting to reconnect to Python..." << std::endl;
                if (pipeClient.connectToPython()) {
                    std::cout << "[C++] ✓ Reconnected to Python" << std::endl;
                }
            }
        }

    } catch (std::exception& e) {
        std::cerr << "[C++] FATAL ERROR: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
