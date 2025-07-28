//
// CoCoChain Application Header
//

#ifndef __COCOCHAIN_APP_H_
#define __COCOCHAIN_APP_H_

#include <omnetpp.h>
#include <inet/applications/base/ApplicationBase.h>
#include <inet/transportlayer/contract/udp/UdpSocket.h>
#include <inet/common/packet/Packet.h>
#include <inet/common/packet/chunk/BytesChunk.h>
#include <map>
#include <vector>
#include <set>
#include <random>

using namespace omnetpp;
using namespace inet;

struct ConceptVector {
    std::vector<double> data;
    uint64_t timestamp;
    int nodeId;
    bool isCorrupted;
    
    ConceptVector() : timestamp(0), nodeId(-1), isCorrupted(false) {}
};

struct Transaction {
    uint64_t id;
    ConceptVector conceptVector;
    std::string semanticDigest;
    uint64_t timestamp;
    int originator;
    bool verified;
    
    Transaction() : id(0), timestamp(0), originator(-1), verified(false) {}
};

struct ConsensusMessage {
    enum Type { PROPOSE, VOTE, COMMIT };
    Type type;
    uint64_t transactionId;
    int senderId;
    bool vote; // true = accept, false = reject
    std::string semanticDigest;
    uint64_t timestamp;
};

class CoCoChainApp : public ApplicationBase, public UdpSocket::ICallback
{
private:
    // Parameters
    simtime_t messageInterval;
    double corruptionProbability;
    double bftThreshold;
    bool semanticVerification;
    simtime_t maxTransactionAge;
    
    // Network
    UdpSocket socket;
    int localPort;
    
    // CoCoChain state
    std::map<uint64_t, Transaction> pendingTransactions;
    std::map<uint64_t, std::vector<ConsensusMessage>> consensusVotes;
    std::set<uint64_t> confirmedTransactions;
    std::set<int> adversarialNodes;
    
    // Statistics
    simsignal_t endToEndLatencySignal;
    simsignal_t consensusOverheadSignal;
    simsignal_t malformedDetectedSignal;
    
    // Metrics tracking
    std::map<uint64_t, simtime_t> transactionStartTimes;
    int totalMessagesReceived;
    int totalMalformedDetected;
    
    // Random number generation
    std::mt19937 rng;
    std::uniform_real_distribution<> corruptionDist;
    std::normal_distribution<> conceptDist;
    
    // Message handling
    cMessage *sendTimer;
    uint64_t transactionCounter;
    
protected:
    virtual void initialize(int stage) override;
    virtual void handleMessageWhenUp(cMessage *msg) override;
    virtual void finish() override;
    
    // Socket callbacks
    virtual void socketDataArrived(UdpSocket *socket, Packet *packet) override;
    virtual void socketErrorArrived(UdpSocket *socket, Indication *indication) override;
    virtual void socketClosed(UdpSocket *socket) override;
    
    // CoCoChain functionality
    void sendTransaction();
    void processReceivedTransaction(const Transaction& tx);
    void startConsensus(const Transaction& tx);
    void processConsensusMessage(const ConsensusMessage& msg);
    void finalizeTransaction(uint64_t txId);
    
    // Concept corruption and verification
    ConceptVector generateConceptVector();
    void corruptConceptVector(ConceptVector& cv);
    std::string computeSemanticDigest(const ConceptVector& cv);
    bool verifySemanticIntegrity(const Transaction& tx);
    
    // Adversarial behavior
    bool isAdversarialNode();
    void injectMalformedVector(ConceptVector& cv);
    
    // Utilities
    void scheduleNextMessage();
    void recordMetrics(const Transaction& tx);
    
public:
    CoCoChainApp();
    virtual ~CoCoChainApp();
};

#endif