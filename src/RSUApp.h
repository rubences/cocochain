//
// RSU Application Header for Highway Scenario
//

#ifndef __RSU_APP_H_
#define __RSU_APP_H_

#include <omnetpp.h>
#include <inet/applications/base/ApplicationBase.h>
#include <inet/transportlayer/contract/udp/UdpSocket.h>
#include <map>
#include <vector>
#include <set>

using namespace omnetpp;
using namespace inet;

// Forward declarations
struct Transaction;
struct HandoverContext;

class RSUApp : public ApplicationBase, public UdpSocket::ICallback
{
private:
    // Network
    UdpSocket socket;
    int localPort;
    
    // RSU parameters
    int rsuId;
    double coverageRadius;
    cModule* mobility;
    
    // CoCoChain consensus state
    std::map<uint64_t, Transaction> activeTransactions;
    std::map<int, HandoverContext> handoverContexts;
    std::set<int> connectedVehicles;
    
    // PBFT comparison state
    std::map<uint64_t, std::vector<bool>> pbftVotes;
    bool usePBFT;
    
    // Statistics
    simsignal_t authLatencySignal;
    simsignal_t handoverSuccessSignal;
    simsignal_t throughputSignal;
    
    // Metrics tracking
    std::map<uint64_t, simtime_t> transactionStartTimes;
    int totalHandovers;
    int successfulHandovers;
    double throughputCounter;
    simtime_t lastThroughputUpdate;

protected:
    virtual void initialize(int stage) override;
    virtual void handleMessageWhenUp(cMessage *msg) override;
    virtual void finish() override;
    
    // Socket callbacks
    virtual void socketDataArrived(UdpSocket *socket, Packet *packet) override;
    virtual void socketErrorArrived(UdpSocket *socket, Indication *indication) override;
    virtual void socketClosed(UdpSocket *socket) override;
    
    // RSU functionality
    void processTransaction(const Transaction& tx, int senderId);
    void processHandoverRequest(int vehicleId, const HandoverContext& context);
    void authenticateVehicle(int vehicleId);
    void runCoCoChainConsensus(uint64_t txId);
    void runPBFTConsensus(uint64_t txId);
    
    // Handover management
    bool isVehicleInRange(int vehicleId);
    void recordHandoverSuccess(int vehicleId, simtime_t latency);
    void recordHandoverFailure(int vehicleId);
    
    // Metrics
    void updateThroughput();
    void recordAuthenticationLatency(simtime_t latency);

public:
    RSUApp();
    virtual ~RSUApp();
};

#endif