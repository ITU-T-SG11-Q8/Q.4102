BIN = UPREPC
CC = g++
CFLAGS = -c -Wall -std=c++11 
OBJECTS = \
	./bson/base64.o\
	./bson/bson.o\
	./bson/hex.o\
	./bson/json.o\
	./bson/parse_number.o\
	./NetworkUtil.o\
	./sha1.o\
	./HttpREST.o\
	./overlayAction.o\
	./PODOBuffer.cpp prepAgentManager.o\
	./prepBuffer.o\
	./prepProtocolControl.o\
	./bson/time_support.o\
	./Util.o\
	./main.o
OUTS = \
	base64.o \
	bson.o \
	hex.o \
	json.o \
	parse_number.o \
	time_support.o \
	NetworkUtil.o \
	sha1.o \
	HttpREST.o \
	overlayAction.o \
	PODOBuffer.cpp prepAgentManager.o \
	prepBuffer.o \
	prepProtocolControl.o \
	Util.o \
	main.o 

all : ${OBJECTS}
	${CC} -o ${BIN} ${OUTS} -lpthread
	
mac : CFLAGS += -DMACOS
mac : ${OBJECTS}
	${CC} -o ${BIN} ${OUTS} 

clean : 
	rm -rf *.o -rf ${BIN}

%.o : %.cpp
	${CC} ${CFLAGS} $<


