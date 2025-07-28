//
// Shared Data Structures for Highway CoCoChain Scenario
//

#ifndef __HIGHWAY_STRUCTURES_H_
#define __HIGHWAY_STRUCTURES_H_

#include <vector>
#include <string>
#include <cstdint>

// Transaction structure for highway scenario
struct Transaction {
    uint64_t id;
    int originator;          // Vehicle ID
    uint64_t timestamp;
    std::vector<double> semanticData;  // Semantic content
    std::string digest;               // CoCoChain semantic digest
    bool verified;
    int targetRSU;          // RSU handling this transaction
    
    Transaction() : id(0), originator(-1), timestamp(0), verified(false), targetRSU(-1) {}
};

// Handover context for RSU transitions
struct HandoverContext {
    int vehicleId;
    int sourceRSU;
    int targetRSU;
    uint64_t timestamp;
    std::vector<uint64_t> pendingTransactions;
    std::string authToken;
    bool inProgress;
    
    HandoverContext() : vehicleId(-1), sourceRSU(-1), targetRSU(-1), timestamp(0), inProgress(false) {}
};

// Consensus message types
enum ConsensusType {
    COCOCHAIN,
    PBFT
};

struct ConsensusMessage {
    enum Type { PROPOSE, VOTE, COMMIT, ABORT };
    Type type;
    ConsensusType consensusType;
    uint64_t transactionId;
    int senderId;
    bool vote;              // true = accept, false = reject
    std::string digest;     // Semantic digest for verification
    uint64_t timestamp;
    
    ConsensusMessage() : type(PROPOSE), consensusType(COCOCHAIN), transactionId(0), 
                        senderId(-1), vote(false), timestamp(0) {}
};

// Handover message for RSU transitions
struct HandoverMessage {
    enum Type { REQUEST, ACCEPT, REJECT, COMPLETE };
    Type type;
    int vehicleId;
    int sourceRSU;
    int targetRSU;
    HandoverContext context;
    uint64_t timestamp;
    
    HandoverMessage() : type(REQUEST), vehicleId(-1), sourceRSU(-1), targetRSU(-1), timestamp(0) {}
};

// Performance metrics for highway scenario
struct HighwayMetrics {
    // Authentication latency during handovers
    std::vector<double> authLatencies;
    
    // Handover success rate data
    int totalHandovers;
    int successfulHandovers;
    
    // Throughput measurements (transactions per second)
    std::vector<double> throughputSamples;
    
    // Speed-based analysis
    std::map<int, std::vector<double>> speedBandLatencies;  // speed -> latencies
    std::map<int, double> speedBandHSR;                     // speed -> handover success rate
    
    HighwayMetrics() : totalHandovers(0), successfulHandovers(0) {}
    
    double getHandoverSuccessRate() const {
        return totalHandovers > 0 ? (double)successfulHandovers / totalHandovers : 0.0;
    }
    
    double getAverageLatency() const {
        if (authLatencies.empty()) return 0.0;
        double sum = 0.0;
        for (double lat : authLatencies) sum += lat;
        return sum / authLatencies.size();
    }
    
    double getAverageThroughput() const {
        if (throughputSamples.empty()) return 0.0;
        double sum = 0.0;
        for (double tp : throughputSamples) sum += tp;
        return sum / throughputSamples.size();
    }
};

#endif