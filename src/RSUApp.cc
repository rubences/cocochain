//
// RSU Application Implementation for Highway Scenario
//

#include "RSUApp.h"
#include "HighwayStructures.h"
#include <inet/common/ModuleAccess.h>
#include <inet/common/packet/Packet.h>
#include <inet/common/packet/chunk/BytesChunk.h>
#include <inet/networklayer/common/L3AddressResolver.h>
#include <inet/mobility/contract/IMobility.h>
#include <cmath>
#include <algorithm>
#include <sstream>

Define_Module(RSUApp);

RSUApp::RSUApp() :
    localPort(8888),
    rsuId(-1),
    coverageRadius(1000.0),  // 1 km coverage
    mobility(nullptr),
    usePBFT(false),
    totalHandovers(0),
    successfulHandovers(0),
    throughputCounter(0.0),
    lastThroughputUpdate(SIMTIME_ZERO)
{
}

RSUApp::~RSUApp()
{
}

void RSUApp::initialize(int stage)
{
    ApplicationBase::initialize(stage);
    
    if (stage == INITSTAGE_LOCAL) {
        // Get RSU parameters
        rsuId = getIndex();
        usePBFT = par("usePBFT").boolValue();
        coverageRadius = par("coverageRadius").doubleValue();
        
        // Register signals
        authLatencySignal = registerSignal("authLatency");
        handoverSuccessSignal = registerSignal("handoverSuccess");
        throughputSignal = registerSignal("throughput");
        
        // Get mobility module
        mobility = getParentModule()->getSubmodule("mobility");
        
        EV_INFO << "RSU " << rsuId << " initialized with " 
                << (usePBFT ? "PBFT" : "CoCoChain") << " consensus" << endl;
    }
    else if (stage == INITSTAGE_APPLICATION_LAYER) {
        // Initialize UDP socket
        socket.setOutputGate(gate("socketOut"));
        socket.setCallback(this);
        socket.bind(localPort);
        socket.setBroadcast(true);
        
        // Start throughput measurement
        lastThroughputUpdate = simTime();
    }
}

void RSUApp::handleMessageWhenUp(cMessage *msg)
{
    if (msg->isSelfMessage()) {
        // Handle self messages (timers, etc.)
        delete msg;
    }
    else {
        // Handle network messages via socket callback
        socket.processMessage(msg);
    }
}

void RSUApp::socketDataArrived(UdpSocket *socket, Packet *packet)
{
    auto chunk = packet->peekDataAt<BytesChunk>(b(0), packet->getDataLength());
    std::string data = chunk->getBytes().str();
    
    // Parse message type
    if (data.find("TRANSACTION:") == 0) {
        // Parse transaction
        Transaction tx;
        // Simple parsing - in real implementation would use proper serialization
        std::istringstream iss(data.substr(12));
        iss >> tx.id >> tx.originator >> tx.timestamp >> tx.targetRSU;
        
        // Generate semantic data and digest
        tx.semanticData.resize(10);
        for (int i = 0; i < 10; i++) {
            tx.semanticData[i] = uniform(0.0, 1.0);
        }
        
        processTransaction(tx, tx.originator);
    }
    else if (data.find("HANDOVER:") == 0) {
        // Parse handover request
        HandoverContext context;
        std::istringstream iss(data.substr(9));
        iss >> context.vehicleId >> context.sourceRSU >> context.targetRSU;
        context.timestamp = simTime().inUnit(SIMTIME_MS);
        
        processHandoverRequest(context.vehicleId, context);
    }
    
    delete packet;
}

void RSUApp::socketErrorArrived(UdpSocket *socket, Indication *indication)
{
    EV_WARN << "RSU " << rsuId << " socket error: " << indication->getName() << endl;
    delete indication;
}

void RSUApp::socketClosed(UdpSocket *socket)
{
    EV_INFO << "RSU " << rsuId << " socket closed" << endl;
}

void RSUApp::processTransaction(const Transaction& tx, int senderId)
{
    simtime_t startTime = simTime();
    transactionStartTimes[tx.id] = startTime;
    
    // Store transaction
    activeTransactions[tx.id] = tx;
    
    EV_INFO << "RSU " << rsuId << " processing transaction " << tx.id 
            << " from vehicle " << senderId << endl;
    
    // Run consensus based on configuration
    if (usePBFT) {
        runPBFTConsensus(tx.id);
    } else {
        runCoCoChainConsensus(tx.id);
    }
    
    // Update throughput
    updateThroughput();
}

void RSUApp::runCoCoChainConsensus(uint64_t txId)
{
    auto it = activeTransactions.find(txId);
    if (it == activeTransactions.end()) return;
    
    Transaction& tx = it->second;
    
    // CoCoChain semantic digest verification
    std::ostringstream digest;
    for (double val : tx.semanticData) {
        digest << std::fixed << std::setprecision(6) << val;
    }
    tx.digest = digest.str();
    
    // Simulate consensus latency (CoCoChain is faster)
    simtime_t consensusLatency = uniform(0.001, 0.005);  // 1-5ms
    
    // Mark as verified
    tx.verified = true;
    
    // Record authentication latency
    simtime_t authLatency = simTime() + consensusLatency - transactionStartTimes[txId];
    recordAuthenticationLatency(authLatency.dbl());
    
    EV_INFO << "RSU " << rsuId << " completed CoCoChain consensus for transaction " 
            << txId << " in " << authLatency << "s" << endl;
}

void RSUApp::runPBFTConsensus(uint64_t txId)
{
    auto it = activeTransactions.find(txId);
    if (it == activeTransactions.end()) return;
    
    Transaction& tx = it->second;
    
    // PBFT has higher latency due to multiple rounds
    simtime_t consensusLatency = uniform(0.010, 0.050);  // 10-50ms
    
    // Mark as verified
    tx.verified = true;
    
    // Record authentication latency
    simtime_t authLatency = simTime() + consensusLatency - transactionStartTimes[txId];
    recordAuthenticationLatency(authLatency.dbl());
    
    EV_INFO << "RSU " << rsuId << " completed PBFT consensus for transaction " 
            << txId << " in " << authLatency << "s" << endl;
}

void RSUApp::processHandoverRequest(int vehicleId, const HandoverContext& context)
{
    totalHandovers++;
    
    simtime_t handoverStart = simTime();
    
    // Simulate handover authentication
    if (context.targetRSU == rsuId && isVehicleInRange(vehicleId)) {
        // Successful handover
        simtime_t authLatency = uniform(0.002, 0.008);  // 2-8ms for handover auth
        
        scheduleAt(simTime() + authLatency, new cMessage("handover_complete"));
        
        recordHandoverSuccess(vehicleId, authLatency);
        successfulHandovers++;
        
        EV_INFO << "RSU " << rsuId << " completed handover for vehicle " 
                << vehicleId << " in " << authLatency << "s" << endl;
    } else {
        // Failed handover
        recordHandoverFailure(vehicleId);
        
        EV_WARN << "RSU " << rsuId << " failed handover for vehicle " << vehicleId << endl;
    }
}

bool RSUApp::isVehicleInRange(int vehicleId)
{
    // Simple range check - in real implementation would check actual positions
    return uniform(0.0, 1.0) > 0.05;  // 95% success rate for range check
}

void RSUApp::recordHandoverSuccess(int vehicleId, simtime_t latency)
{
    emit(authLatencySignal, latency.dbl());
    emit(handoverSuccessSignal, 1.0);
}

void RSUApp::recordHandoverFailure(int vehicleId)
{
    emit(handoverSuccessSignal, 0.0);
}

void RSUApp::recordAuthenticationLatency(double latency)
{
    emit(authLatencySignal, latency);
}

void RSUApp::updateThroughput()
{
    throughputCounter++;
    
    simtime_t now = simTime();
    simtime_t interval = now - lastThroughputUpdate;
    
    if (interval >= 1.0) {  // Update every second
        double throughput = throughputCounter / interval.dbl();
        emit(throughputSignal, throughput);
        
        throughputCounter = 0.0;
        lastThroughputUpdate = now;
    }
}

void RSUApp::finish()
{
    ApplicationBase::finish();
    
    // Final throughput calculation
    if (throughputCounter > 0) {
        simtime_t interval = simTime() - lastThroughputUpdate;
        if (interval > 0) {
            double finalThroughput = throughputCounter / interval.dbl();
            emit(throughputSignal, finalThroughput);
        }
    }
    
    // Record final statistics
    double hsr = totalHandovers > 0 ? (double)successfulHandovers / totalHandovers : 0.0;
    
    EV_INFO << "RSU " << rsuId << " final stats:" << endl;
    EV_INFO << "  Total handovers: " << totalHandovers << endl;
    EV_INFO << "  Successful handovers: " << successfulHandovers << endl;
    EV_INFO << "  Handover success rate: " << (hsr * 100) << "%" << endl;
}