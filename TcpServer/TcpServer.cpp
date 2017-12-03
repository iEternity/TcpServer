#include <memory>
#include <iostream>
#include "TcpServer.h"

using namespace net;
using namespace std;
using namespace std::placeholders;

TcpServer::TcpServer(boost::asio::io_service& ioService, short port):
	acceptor_(ioService, Tcp::endpoint(Tcp::v4(), port)),
	socket_(ioService),
	connectionCallback_(defaultConnectionCallback),
	messageCallback_(defaultMessageCallback),
	writeCompleteCallback_(defaultWriteCompleteCallback)
{
	doAccept();
}

void TcpServer::doAccept()
{
	acceptor_.async_accept(socket_, std::bind(&TcpServer::newConnection, this, _1));
}

void TcpServer::newConnection(const boost::system::error_code& error)
{
	if (!error)
	{
		auto conn = std::make_shared<TcpConnection>(std::move(socket_));
		conn->setMessageCallback(messageCallback_);
		conn->setWriteCompleteCallback(writeCompleteCallback_);

		conn->start();
		connections_.push_back(conn);

		connectionCallback_(conn);

		doAccept();
	}
}