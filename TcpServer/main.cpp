#include <iostream>
#include <string>
#include <map>
#include <array>
#include "TcpServer.h"
#include "TcpConnection.h"

#include <boost/algorithm/string.hpp>

using namespace net;
using namespace std;

void onMessage(const TcpConnectionPtr& conn, const void* data, size_t size)
{
	conn->asyncSend(data, size);
}

void test()
{
	boost::asio::io_service service;
	TcpServer echoServer(service, 12345);
	echoServer.setMessageCallback(onMessage);
	service.run();
}

int main(int argc, char*argv[])
{
	test();

	system("pause");
}