//
// Vehicle Application Implementation for Highway Scenario
//

#include "VehicleApp.h"
#include "HighwayStructures.h"
#include <inet/common/ModuleAccess.h>
#include <inet/common/packet/Packet.h>
#include <inet/common/packet/chunk/BytesChunk.h>
#include <inet/networklayer/common/L3AddressResolver.h>
#include <inet/mobility/contract/IMobility.h>
#include <cmath>
#include <sstream>

Define_Module(VehicleApp);

VehicleApp::VehicleApp() :
    localPort(9999),
    vehicleId(-1),
    speed(0.0),
    mobility(nullptr),
    transactionInterval(2.0),  // 2 seconds
    sendTimer(nullptr),
    transactionCounter(0),
    currentRSU(-1),
    targetRSU(-1),
    inHandover(false)
{
}

VehicleApp::~VehicleApp()
{
    cancelAndDelete(sendTimer);
}

void VehicleApp::initialize(int stage)
{
    ApplicationBase::initialize(stage);
    
    if (stage == INITSTAGE_LOCAL) {
        // Get vehicle parameters
        vehicleId = getIndex();
        transactionInterval = par("transactionInterval");
        
        // Register signals
        authLatencySignal = registerSignal("authLatency");
        handoverSignal = registerSignal("handover");
        
        // Get mobility module
        mobility = getParentModule()->getSubmodule("mobility");
        if (mobility) {
            // Set random highway speed (100-130 km/h)
            speed = uniform(100.0, 130.0);  // km/h
            mobility->par("speed") = speed;
        }
        
        // Create timer for transactions
        sendTimer = new cMessage("sendTransaction");
        
        EV_INFO << "Vehicle " << vehicleId << " initialized with speed " 
                << speed << " km/h" << endl;
    }
    else if (stage == INITSTAGE_APPLICATION_LAYER) {
        // Initialize UDP socket
        socket.setOutputGate(gate("socketOut"));
        socket.setCallback(this);
        socket.bind(localPort);
        socket.setBroadcast(true);
        
        // Start sending transactions
        scheduleNextTransaction();
        
        // Initialize RSU connection
        currentRSU = findNearestRSU();
    }
}

void VehicleApp::handleMessageWhenUp(cMessage *msg)
{
    if (msg == sendTimer) {
        sendTransaction();
        scheduleNextTransaction();
    }
    else if (msg->isSelfMessage()) {
        delete msg;
    }
    else {
        socket.processMessage(msg);
    }
}

void VehicleApp::socketDataArrived(UdpSocket *socket, Packet *packet)
{
    auto chunk = packet->peekDataAt<BytesChunk>(b(0), packet->getDataLength());
    std::string data = chunk->getBytes().str();
    
    // Parse response messages
    if (data.find("TX_RESPONSE:") == 0) {
        // Parse transaction response
        std::istringstream iss(data.substr(12));
        uint64_t txId;
        bool success;
        double latency;
        iss >> txId >> success >> latency;
        
        processTransactionResponse(txId, success, latency);
    }
    else if (data.find("HANDOVER_RESPONSE:") == 0) {
        // Parse handover response
        std::istringstream iss(data.substr(18));
        int rsuId;
        bool success;
        iss >> rsuId >> success;
        
        completeHandover(rsuId, success);
    }
    
    delete packet;
}

void VehicleApp::socketErrorArrived(UdpSocket *socket, Indication *indication)
{
    EV_WARN << "Vehicle " << vehicleId << " socket error: " << indication->getName() << endl;
    delete indication;
}

void VehicleApp::socketClosed(UdpSocket *socket)
{
    EV_INFO << "Vehicle " << vehicleId << " socket closed" << endl;
}

void VehicleApp::sendTransaction()
{
    // Check if we need to handover to a new RSU
    checkRSURange();
    
    // Create transaction
    transactionCounter++;
    uint64_t txId = vehicleId * 1000000 + transactionCounter;
    
    // Record start time
    pendingTransactions[txId] = simTime();
    
    // Create transaction message
    std::ostringstream msg;
    msg << "TRANSACTION:" << txId << " " << vehicleId << " " 
        << simTime().inUnit(SIMTIME_MS) << " " << currentRSU;
    
    // Send to current RSU (broadcast for simplicity)
    auto packet = new Packet("transaction");
    auto chunk = makeShared<BytesChunk>();
    chunk->setBytes(msg.str().c_str());
    packet->insertAtBack(chunk);
    
    socket.sendBroadcast(packet, 8888);  // RSU port
    
    EV_INFO << "Vehicle " << vehicleId << " sent transaction " << txId 
            << " to RSU " << currentRSU << endl;
}

void VehicleApp::processTransactionResponse(uint64_t txId, bool success, simtime_t latency)
{
    auto it = pendingTransactions.find(txId);
    if (it != pendingTransactions.end()) {
        simtime_t totalLatency = simTime() - it->second;
        
        emit(authLatencySignal, totalLatency.dbl());
        
        pendingTransactions.erase(it);
        
        EV_INFO << "Vehicle " << vehicleId << " received response for transaction " 
                << txId << ", latency: " << totalLatency << "s" << endl;
    }
}

void VehicleApp::checkRSURange()
{
    int nearestRSU = findNearestRSU();
    
    if (nearestRSU != currentRSU && !inHandover) {
        // Need to handover to new RSU
        initiateHandover(nearestRSU);
    }
}

void VehicleApp::initiateHandover(int newRSU)
{
    if (inHandover) return;
    
    inHandover = true;
    targetRSU = newRSU;
    
    // Create handover request
    std::ostringstream msg;
    msg << "HANDOVER:" << vehicleId << " " << currentRSU << " " << newRSU;
    
    auto packet = new Packet("handover");
    auto chunk = makeShared<BytesChunk>();
    chunk->setBytes(msg.str().c_str());
    packet->insertAtBack(chunk);
    
    socket.sendBroadcast(packet, 8888);  // RSU port
    
    emit(handoverSignal, 1.0);  // Handover initiated
    
    EV_INFO << "Vehicle " << vehicleId << " initiated handover from RSU " 
            << currentRSU << " to RSU " << newRSU << endl;
}

void VehicleApp::completeHandover(int rsuId, bool success)
{
    if (!inHandover || rsuId != targetRSU) return;
    
    if (success) {
        currentRSU = targetRSU;
        rsuContactTimes[currentRSU] = simTime();
        
        EV_INFO << "Vehicle " << vehicleId << " completed handover to RSU " 
                << currentRSU << endl;
    } else {
        EV_WARN << "Vehicle " << vehicleId << " failed handover to RSU " 
                << targetRSU << endl;
    }
    
    inHandover = false;
    targetRSU = -1;
}

int VehicleApp::findNearestRSU()
{
    if (!mobility) return 0;  // Default to RSU 0
    
    // Get current position (simplified)
    double position = uniform(0.0, 20000.0);  // Position along highway
    
    // RSUs are at positions: 2km, 6km, 10km, 14km, 18km
    std::vector<double> rsuPositions = {2000, 6000, 10000, 14000, 18000};
    
    int nearestRSU = 0;
    double minDistance = std::abs(position - rsuPositions[0]);
    
    for (int i = 1; i < 5; i++) {
        double distance = std::abs(position - rsuPositions[i]);
        if (distance < minDistance) {
            minDistance = distance;
            nearestRSU = i;
        }
    }
    
    // Check if within coverage range (1000m)
    if (minDistance > 1000.0) {
        return -1;  // No RSU in range
    }
    
    return nearestRSU;
}

double VehicleApp::getDistanceToRSU(int rsuId)
{
    if (rsuId < 0 || rsuId >= 5) return 99999.0;
    
    std::vector<double> rsuPositions = {2000, 6000, 10000, 14000, 18000};
    double vehiclePos = uniform(0.0, 20000.0);  // Simplified position
    
    return std::abs(vehiclePos - rsuPositions[rsuId]);
}

void VehicleApp::scheduleNextTransaction()
{
    scheduleAt(simTime() + transactionInterval, sendTimer);
}

void VehicleApp::finish()
{
    ApplicationBase::finish();
    
    EV_INFO << "Vehicle " << vehicleId << " final stats:" << endl;
    EV_INFO << "  Total transactions sent: " << transactionCounter << endl;
    EV_INFO << "  Pending transactions: " << pendingTransactions.size() << endl;
    EV_INFO << "  Final RSU: " << currentRSU << endl;
}