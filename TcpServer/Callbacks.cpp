#include <iostream>
#include "Callbacks.h"
#include "TcpConnection.h"

using namespace net;
using namespace std;

void net::defaultConnectionCallback(const TcpConnectionPtr& conn)
{
	cout << "New client connected from - " << conn->peerIpPort() << endl;
}

void net::defaultMessageCallback(const TcpConnectionPtr& conn, const void* data, size_t len)
{
	cout << "received: " << len << "bytes" << endl;
}

void net::defaultWriteCompleteCallback(const TcpConnectionPtr& conn, size_t len)
{
	cout << "send: " << len << "bytes" << endl;
}