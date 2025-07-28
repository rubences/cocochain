//
// Vehicle Application Header for Highway Scenario
//

#ifndef __VEHICLE_APP_H_
#define __VEHICLE_APP_H_

#include <omnetpp.h>
#include <inet/applications/base/ApplicationBase.h>
#include <inet/transportlayer/contract/udp/UdpSocket.h>
#include <map>
#include <vector>

using namespace omnetpp;
using namespace inet;

// Forward declarations
struct Transaction;
struct HandoverContext;

class VehicleApp : public ApplicationBase, public UdpSocket::ICallback
{
private:
    // Network
    UdpSocket socket;
    int localPort;
    
    // Vehicle parameters
    int vehicleId;
    double speed;
    cModule* mobility;
    
    // Transaction parameters
    simtime_t transactionInterval;
    cMessage* sendTimer;
    uint64_t transactionCounter;
    
    // RSU handover state
    int currentRSU;
    int targetRSU;
    std::map<int, simtime_t> rsuContactTimes;
    bool inHandover;
    
    // Transaction tracking
    std::map<uint64_t, simtime_t> pendingTransactions;
    
    // Statistics
    simsignal_t authLatencySignal;
    simsignal_t handoverSignal;

protected:
    virtual void initialize(int stage) override;
    virtual void handleMessageWhenUp(cMessage *msg) override;
    virtual void finish() override;
    
    // Socket callbacks
    virtual void socketDataArrived(UdpSocket *socket, Packet *packet) override;
    virtual void socketErrorArrived(UdpSocket *socket, Indication *indication) override;
    virtual void socketClosed(UdpSocket *socket) override;
    
    // Vehicle functionality
    void sendTransaction();
    void processTransactionResponse(uint64_t txId, bool success, simtime_t latency);
    void checkRSURange();
    void initiateHandover(int newRSU);
    void completeHandover(int rsuId, bool success);
    
    // Utilities
    int findNearestRSU();
    double getDistanceToRSU(int rsuId);
    void scheduleNextTransaction();

public:
    VehicleApp();
    virtual ~VehicleApp();
};

#endif