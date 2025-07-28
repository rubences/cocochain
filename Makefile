#
# CoCoChain Highway Scenario Makefile
#

# OMNeT++ configuration
OMNETPP_ROOT ?= $(shell readlink -f $$(which omnetpp-config 2>/dev/null | head -1 | sed 's|/bin/omnetpp-config||') 2>/dev/null || echo "/usr")
CONFIGFILE = $(OMNETPP_ROOT)/Makefile.inc
ifneq ("$(wildcard $(CONFIGFILE))","")
include $(CONFIGFILE)
endif

# Project configuration
TARGET = CoCoChain
SRCDIR = src
NEDDIR = ned

# Source files (include new highway scenario files)
SOURCES = $(wildcard $(SRCDIR)/*.cc) $(wildcard $(SRCDIR)/*.cpp)
HEADERS = $(wildcard $(SRCDIR)/*.h) $(wildcard $(SRCDIR)/*.hpp)

# Compiler flags
CXXFLAGS += -std=c++17 -Wall -Wextra

# Include paths
INCLUDE_PATH += -I$(SRCDIR)

# Dependencies - using simplified version for compatibility
LIBS += -lm

# Veins support (optional)
ifdef VEINS_ROOT
INCLUDE_PATH += -I$(VEINS_ROOT)/src
LIBS += -lveins$(D)
endif

# INET support (optional)  
ifdef INET_ROOT
INCLUDE_PATH += -I$(INET_ROOT)/src
LIBS += -linet$(D)
endif

# Build targets
all: $(TARGET)

$(TARGET): $(SOURCES) $(HEADERS)
	@echo "Building $(TARGET) for highway scenario..."
	@echo "Sources: $(SOURCES)"
	$(CXX) $(CXXFLAGS) $(INCLUDE_PATH) -o $@ $(SOURCES) $(LDFLAGS) $(LIBS)

clean:
	rm -f $(TARGET) *.o *_m.cc *_m.h
	rm -rf results/*

# Run highway scenario
run-highway: $(TARGET)
	./run_highway_simulation.sh

# Run original urban scenario
run-urban: $(TARGET)
	cd simulations && ../$(TARGET) -u Cmdenv -c General --repeat=10

# Analyze highway results
analyze-highway:
	cd scripts && python3 analyze_highway.py

# Quick test without OMNeT++
test:
	cd scripts && python3 test_cocochain.py

.PHONY: all clean run-highway run-urban analyze-highway test