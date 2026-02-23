#include <windows.h>
#include <wtsapi32.h>
#include <psapi.h>
#include <tlhelp32.h>
#include <iphlpapi.h>
#include <winsock2.h>
#include <wininet.h>
#include <openssl/aes.h>
#include <openssl/rand.h>
#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <nlohmann/json.hpp>
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <map>
#include <string>
#include <ctime>
#include <cstring>
#include <filesystem>
#include <thread>
#include <mutex>
#include <queue>
#include <chrono>
#include <random>
#include <memory>

#pragma comment(lib, "wtsapi32.lib")
#pragma comment(lib, "psapi.lib")
#pragma comment(lib, "iphlpapi.lib")
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "wininet.lib")
#pragma comment(lib, "netapi32.lib")
#pragma comment(lib, "crypt32.lib")

using json = nlohmann::json;
namespace fs = std::filesystem;

// ==================== ENCRYPTION ENGINE ====================

class EncryptionEngine {
private:
    unsigned char aes_key[32]; // 256-bit key
    unsigned char aes_iv[16];  // 128-bit IV
    std::mutex key_mutex;

public:
    EncryptionEngine() {
        if (!generateNewKey()) {
            std::cerr << "CRITICAL: Failed to generate encryption key!" << std::endl;
            exit(1);
        }
    }

    bool generateNewKey() {
        std::lock_guard<std::mutex> lock(key_mutex);
        
        // Generate random 256-bit key and 128-bit IV
        if (!RAND_bytes(aes_key, 32) || !RAND_bytes(aes_iv, 16)) {
            return false;
        }
        
        // Store key securely using Windows DPAPI
        return storeKeySecurely();
    }

    bool storeKeySecurely() {
        DATA_BLOB dataIn, dataOut;
        dataIn.pbData = aes_key;
        dataIn.cbData = 32;

        if (CryptProtectData(&dataIn, L"SmartAI_AES_Key", NULL, NULL, NULL, 0, &dataOut)) {
            std::ofstream keyFile("smartai.key", std::ios::binary);
            keyFile.write((char*)dataOut.pbData, dataOut.cbData);
            keyFile.close();
            
            LocalFree(dataOut.pbData);
            return true;
        }
        return false;
    }

    bool loadKeySecurely() {
        std::lock_guard<std::mutex> lock(key_mutex);
        
        std::ifstream keyFile("smartai.key", std::ios::binary);
        if (!keyFile.is_open()) return false;

        std::vector<unsigned char> encryptedKey((std::istreambuf_iterator<char>(keyFile)),
                                                std::istreambuf_iterator<char>());
        keyFile.close();

        DATA_BLOB dataIn, dataOut;
        dataIn.pbData = encryptedKey.data();
        dataIn.cbData = encryptedKey.size();

        if (CryptUnprotectData(&dataIn, NULL, NULL, NULL, NULL, 0, &dataOut)) {
            std::memcpy(aes_key, dataOut.pbData, 32);
            SecureZeroMemory(dataOut.pbData, 32);
            LocalFree(dataOut.pbData);
            return true;
        }
        return false;
    }

    std::string encryptData(const std::string& plaintext) {
        std::lock_guard<std::mutex> lock(key_mutex);
        
        EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
        unsigned char ciphertext[plaintext.length() + EVP_MAX_BLOCK_LENGTH];
        int len = 0, ciphertext_len = 0;

        EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, aes_key, aes_iv);
        EVP_EncryptUpdate(ctx, ciphertext, &len, (unsigned char*)plaintext.c_str(), plaintext.length());
        ciphertext_len = len;
        EVP_EncryptFinal_ex(ctx, ciphertext + len, &len);
        ciphertext_len += len;
        EVP_CIPHER_CTX_free(ctx);

        // Convert to hex string
        std::stringstream ss;
        for (int i = 0; i < ciphertext_len; i++) {
            ss << std::hex << (int)ciphertext[i];
        }
        return ss.str();
    }

    std::string decryptData(const std::string& ciphertext_hex) {
        std::lock_guard<std::mutex> lock(key_mutex);
        
        // Convert hex string to bytes
        std::vector<unsigned char> ciphertext;
        for (size_t i = 0; i < ciphertext_hex.length(); i += 2) {
            std::string byte = ciphertext_hex.substr(i, 2);
            unsigned char c = (unsigned char)strtol(byte.c_str(), NULL, 16);
            ciphertext.push_back(c);
        }

        EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
        unsigned char plaintext[ciphertext.size()];
        int len = 0, plaintext_len = 0;

        EVP_DecryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, aes_key, aes_iv);
        EVP_DecryptUpdate(ctx, plaintext, &len, ciphertext.data(), ciphertext.size());
        plaintext_len = len;
        EVP_DecryptFinal_ex(ctx, plaintext + len, &len);
        plaintext_len += len;
        EVP_CIPHER_CTX_free(ctx);

        return std::string((char*)plaintext, plaintext_len);
    }

    std::string generateHMAC(const std::string& data) {
        std::lock_guard<std::mutex> lock(key_mutex);
        
        unsigned char digest[EVP_MAX_MD_SIZE];
        unsigned int digest_len;

        HMAC(EVP_sha256(), aes_key, 32, 
             (unsigned char*)data.c_str(), data.length(),
             digest, &digest_len);

        std::stringstream ss;
        for (unsigned int i = 0; i < digest_len; i++) {
            ss << std::hex << (int)digest[i];
        }
        return ss.str();
    }

    void rotateKey() {
        std::lock_guard<std::mutex> lock(key_mutex);
        SecureZeroMemory(aes_key, 32);
        SecureZeroMemory(aes_iv, 16);
        // Regenerate new key
        generateNewKey();
    }
};

// ==================== SYSTEM MONITORING ====================

class SystemMonitor {
public:
    struct ProcessInfo {
        DWORD pid;
        std::string name;
        double cpu_percent;
        double memory_mb;
        std::vector<std::string> connections;
    };

    struct SystemStats {
        double cpu_usage;
        double memory_usage;
        double network_in_mbps;
        double network_out_mbps;
        std::vector<ProcessInfo> processes;
        std::time_t timestamp;
    };

    static SystemStats getSystemStats() {
        SystemStats stats;
        stats.timestamp = std::time(nullptr);

        stats.cpu_usage = getCPUUsage();
        stats.memory_usage = getMemoryUsage();
        getNetworkStats(stats.network_in_mbps, stats.network_out_mbps);
        stats.processes = getRunningProcesses();

        return stats;
    }

private:
    static double getCPUUsage() {
        FILETIME prevIdleTime, prevKernelTime, prevUserTime;
        FILETIME idleTime, kernelTime, userTime;

        GetSystemTimes(&prevIdleTime, &prevKernelTime, &prevUserTime);
        Sleep(100); // Sample for 100ms
        GetSystemTimes(&idleTime, &kernelTime, &userTime);

        ULONGLONG prevIdle = filetime_to_ulonglong(prevIdleTime);
        ULONGLONG prevKernel = filetime_to_ulonglong(prevKernelTime);
        ULONGLONG prevUser = filetime_to_ulonglong(prevUserTime);

        ULONGLONG idle = filetime_to_ulonglong(idleTime);
        ULONGLONG kernel = filetime_to_ulonglong(kernelTime);
        ULONGLONG user = filetime_to_ulonglong(userTime);

        ULONGLONG totalTick = (kernel - prevKernel) + (user - prevUser);
        ULONGLONG idleTick = idle - prevIdle;

        return (totalTick == 0) ? 0.0 : (100.0 * (totalTick - idleTick) / totalTick);
    }

    static double getMemoryUsage() {
        MEMORYSTATUSEX stat;
        stat.dwLength = sizeof(stat);
        GlobalMemoryStatusEx(&stat);
        return (100.0 * (stat.ullTotalPhys - stat.ullAvailPhys)) / stat.ullTotalPhys;
    }

    static void getNetworkStats(double& in_mbps, double& out_mbps) {
        DWORD dwSize = 0;
        PMIB_IFTABLE pIfTable = NULL;

        if (GetIfTable(NULL, &dwSize, FALSE) == ERROR_INSUFFICIENT_BUFFER) {
            pIfTable = (MIB_IFTABLE*)malloc(dwSize);
            if (GetIfTable(pIfTable, &dwSize, FALSE) == NO_ERROR) {
                in_mbps = out_mbps = 0;
                for (DWORD i = 0; i < pIfTable->dwNumEntries; i++) {
                    in_mbps += pIfTable->table[i].dwInOctets / 1000000.0;
                    out_mbps += pIfTable->table[i].dwOutOctets / 1000000.0;
                }
            }
            free(pIfTable);
        }
    }

    static std::vector<ProcessInfo> getRunningProcesses() {
        std::vector<ProcessInfo> processes;
        HANDLE hProcessSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);

        if (hProcessSnap != INVALID_HANDLE_VALUE) {
            PROCESSENTRY32 pe32;
            pe32.dwSize = sizeof(PROCESSENTRY32);

            if (Process32First(hProcessSnap, &pe32)) {
                do {
                    ProcessInfo info;
                    info.pid = pe32.th32ProcessID;
                    info.name = std::string(pe32.szExeFile);
                    info.cpu_percent = getProcessCPU(pe32.th32ProcessID);
                    info.memory_mb = getProcessMemory(pe32.th32ProcessID);
                    info.connections = getProcessConnections(pe32.th32ProcessID);
                    
                    processes.push_back(info);
                } while (Process32Next(hProcessSnap, &pe32));
            }
            CloseHandle(hProcessSnap);
        }

        return processes;
    }

    static double getProcessCPU(DWORD pid) {
        HANDLE hProcess = OpenProcess(PROCESS_QUERY_INFORMATION, FALSE, pid);
        if (!hProcess) return 0.0;

        FILETIME creationTime, exitTime, kernelTime, userTime;
        if (GetProcessTimes(hProcess, &creationTime, &exitTime, &kernelTime, &userTime)) {
            ULONGLONG kernelTicks = filetime_to_ulonglong(kernelTime);
            ULONGLONG userTicks = filetime_to_ulonglong(userTime);
            ULONGLONG totalTicks = kernelTicks + userTicks;
            CloseHandle(hProcess);
            return (totalTicks / 10000000.0) * 100.0; // Simplified
        }

        CloseHandle(hProcess);
        return 0.0;
    }

    static double getProcessMemory(DWORD pid) {
        HANDLE hProcess = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, FALSE, pid);
        if (!hProcess) return 0.0;

        PROCESS_MEMORY_COUNTERS pmc;
        if (GetProcessMemoryInfo(hProcess, &pmc, sizeof(pmc))) {
            CloseHandle(hProcess);
            return pmc.WorkingSetSize / (1024.0 * 1024.0);
        }

        CloseHandle(hProcess);
        return 0.0;
    }

    static std::vector<std::string> getProcessConnections(DWORD pid) {
        std::vector<std::string> connections;
        // Implementation would use MIB_TCPTABLE or netstat command
        // Simplified for brevity
        return connections;
    }

    static ULONGLONG filetime_to_ulonglong(FILETIME ft) {
        return ((ULONGLONG)ft.dwHighDateTime << 32) | ft.dwLowDateTime;
    }
};

// ==================== AUTO-RESPONSE ENGINE ====================

class AutoResponseEngine {
private:
    std::mutex response_mutex;
    bool vpn_active = false;
    double current_risk_score = 0.0;

public:
    void executeResponse(double risk_score) {
        std::lock_guard<std::mutex> lock(response_mutex);
        current_risk_score = risk_score;

        // Emergency Mode: Risk > 90
        if (risk_score > 90) {
            blockAllOutbound();
            logAction("EMERGENCY_MODE_ACTIVATED", "All outbound traffic blocked");
        }
        // High Risk: Risk > 70
        else if (risk_score > 70) {
            activateVPN();
            modifyFirewallRules();
            blockSuspiciousPorts();
            logAction("HIGH_RISK_RESPONSE", "VPN activated, firewall modified");
        }
        // Risk decreasing: Risk < 30
        else if (risk_score < 30 && vpn_active) {
            deactivateVPN();
            logAction("RISK_DECREASED", "VPN deactivated, firewall restored");
        }
    }

private:
    void activateVPN() {
        if (vpn_active) return;

        // Activate WireGuard/OpenVPN via system call
        system("C:\\Program Files\\WireGuard\\wireguard.exe /installtunnelservice");
        system("wg-quick up smartai-vpn");
        
        vpn_active = true;
        logAction("VPN_ACTIVATED", "VPN connection established");
    }

    void deactivateVPN() {
        if (!vpn_active) return;

        system("wg-quick down smartai-vpn");
        vpn_active = false;
        logAction("VPN_DEACTIVATED", "VPN connection closed");
    }

    void modifyFirewallRules() {
        // Use Windows Firewall API or netsh commands
        system("netsh advfirewall firewall add rule name=\"SmartAI_BlockSuspicious\" dir=in action=block");
        logAction("FIREWALL_MODIFIED", "Suspicious process blocking rule added");
    }

    void blockSuspiciousPorts() {
        // Block common attack ports
        system("netsh advfirewall firewall add rule name=\"Block_RDP\" dir=in action=block protocol=tcp localport=3389");
        system("netsh advfirewall firewall add rule name=\"Block_SMB\" dir=in action=block protocol=tcp localport=445");
        logAction("PORTS_BLOCKED", "RDP and SMB ports blocked");
    }

    void blockAllOutbound() {
        system("netsh advfirewall firewall add rule name=\"Emergency_BlockAll\" dir=out action=block");
        logAction("ALL_OUTBOUND_BLOCKED", "Emergency mode: all outbound traffic blocked");
    }

    void logAction(const std::string& action, const std::string& details) {
        std::ofstream log("smartai_actions.log", std::ios::app);
        auto now = std::time(nullptr);
        char timestamp[100];
        std::strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", std::localtime(&now));
        
        log << "[" << timestamp << "] " << action << " - " << details << std::endl;
        log.close();
    }
};

// ==================== IPC COMMUNICATION ====================

class IPCManager {
private:
    EncryptionEngine& crypto;
    HANDLE hPipe;
    std::string pipe_name = "\\\\.\\pipe\\SmartAI_Core";

public:
    IPCManager(EncryptionEngine& enc) : crypto(enc), hPipe(INVALID_HANDLE_VALUE) {}

    bool initializePipe() {
        hPipe = CreateNamedPipeA(
            pipe_name.c_str(),
            PIPE_ACCESS_DUPLEX,
            PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE,
            1,
            4096,
            4096,
            0,
            NULL
        );

        return (hPipe != INVALID_HANDLE_VALUE);
    }

    bool sendEncryptedData(const json& data) {
        std::string plaintext = data.dump();
        std::string ciphertext = crypto.encryptData(plaintext);
        std::string hmac = crypto.generateHMAC(ciphertext);

        json packet;
        packet["ciphertext"] = ciphertext;
        packet["hmac"] = hmac;
        packet["timestamp"] = std::time(nullptr);

        std::string packet_str = packet.dump();
        
        DWORD bytesWritten;
        return WriteFile(hPipe, packet_str.c_str(), packet_str.length(), &bytesWritten, NULL);
    }

    json receiveEncryptedData() {
        char buffer[4096];
        DWORD bytesRead;

        if (ReadFile(hPipe, buffer, sizeof(buffer), &bytesRead, NULL)) {
            std::string packet_str(buffer, bytesRead);
            json packet = json::parse(packet_str);

            // Verify HMAC
            std::string received_hmac = packet["hmac"];
            std::string ciphertext = packet["ciphertext"];
            std::string calculated_hmac = crypto.generateHMAC(ciphertext);

            if (received_hmac != calculated_hmac) {
                std::cerr << "ERROR: HMAC verification failed!" << std::endl;
                return json();
            }

            std::string plaintext = crypto.decryptData(ciphertext);
            return json::parse(plaintext);
        }

        return json();
    }
};

// ==================== KEY ROTATION ====================

class KeyRotationManager {
private:
    EncryptionEngine& crypto;
    IPCManager& ipc;
    std::thread rotation_thread;
    bool running = true;
    std::mutex rotation_mutex;

    static constexpr int MIN_ROTATION_HOURS = 48;
    static constexpr int MAX_ROTATION_HOURS = 72;

public:
    KeyRotationManager(EncryptionEngine& enc, IPCManager& i) : crypto(enc), ipc(i) {
        rotation_thread = std::thread(&KeyRotationManager::rotationLoop, this);
    }

    ~KeyRotationManager() {
        running = false;
        if (rotation_thread.joinable()) {
            rotation_thread.join();
        }
    }

private:
    void rotationLoop() {
        while (running) {
            // Random rotation interval between 48-72 hours
            std::random_device rd;
            std::mt19937 gen(rd());
            std::uniform_int_distribution<> dis(MIN_ROTATION_HOURS, MAX_ROTATION_HOURS);
            
            int rotation_hours = dis(gen);
            std::this_thread::sleep_for(std::chrono::hours(rotation_hours));

            performKeyRotation();
        }
    }

    void performKeyRotation() {
        std::lock_guard<std::mutex> lock(rotation_mutex);
        
        std::cout << "[KEY ROTATION] Starting key rotation..." << std::endl;

        // Rotate key in C++ engine
        crypto.rotateKey();

        // Notify Python module via IPC
        json rotation_msg;
        rotation_msg["type"] = "key_rotation";
        rotation_msg["timestamp"] = std::time(nullptr);
        rotation_msg["action"] = "sync_new_key";

        ipc.sendEncryptedData(rotation_msg);

        std::cout << "[KEY ROTATION] Key rotation completed successfully" << std::endl;
    }
};

// ==================== MAIN APPLICATION ====================

class SmartAICoreEngine {
private:
    EncryptionEngine crypto;
    IPCManager ipc;
    AutoResponseEngine response_engine;
    KeyRotationManager key_rotation;
    SystemMonitor monitor;
    std::thread monitoring_thread;
    bool running = true;

public:
    SmartAICoreEngine() : ipc(crypto), key_rotation(crypto, ipc) {
        std::cout << "[SmartAI Core Engine] Initializing..." << std::endl;

        // Load or generate encryption key
        if (!crypto.loadKeySecurely()) {
            crypto.generateNewKey();
        }

        // Initialize IPC pipe
        if (!ipc.initializePipe()) {
            std::cerr << "CRITICAL: Failed to initialize IPC pipe!" << std::endl;
            exit(1);
        }

        // Start monitoring thread
        monitoring_thread = std::thread(&SmartAICoreEngine::monitoringLoop, this);

        std::cout << "[SmartAI Core Engine] Ready and waiting for connections..." << std::endl;
    }

    ~SmartAICoreEngine() {
        running = false;
        if (monitoring_thread.joinable()) {
            monitoring_thread.join();
        }
    }

    void run() {
        while (running) {
            try {
                json response = ipc.receiveEncryptedData();
                
                if (!response.empty() && response.contains("risk_score")) {
                    double risk_score = response["risk_score"];
                    response_engine.executeResponse(risk_score);
                }
            }
            catch (const std::exception& e) {
                std::cerr << "Error receiving data: " << e.what() << std::endl;
            }

            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }

private:
    void monitoringLoop() {
        while (running) {
            try {
                auto stats = SystemMonitor::getSystemStats();
                
                json data;
                data["type"] = "system_stats";
                data["cpu_usage"] = stats.cpu_usage;
                data["memory_usage"] = stats.memory_usage;
                data["network_in"] = stats.network_in_mbps;
                data["network_out"] = stats.network_out_mbps;
                data["process_count"] = stats.processes.size();
                data["timestamp"] = stats.timestamp;

                // Add detailed process info
                json processes_array = json::array();
                for (const auto& proc : stats.processes) {
                    json proc_obj;
                    proc_obj["name"] = proc.name;
                    proc_obj["pid"] = proc.pid;
                    proc_obj["cpu"] = proc.cpu_percent;
                    proc_obj["memory"] = proc.memory_mb;
                    processes_array.push_back(proc_obj);
                }
                data["processes"] = processes_array;

                ipc.sendEncryptedData(data);
            }
            catch (const std::exception& e) {
                std::cerr << "Error in monitoring loop: " << e.what() << std::endl;
            }

            std::this_thread::sleep_for(std::chrono::seconds(5));
        }
    }
};

// ==================== ENTRY POINT ====================

int main() {
    try {
        SmartAICoreEngine engine;
        engine.run();
    }
    catch (const std::exception& e) {
        std::cerr << "FATAL ERROR: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
