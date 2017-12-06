#include <iostream>
#include <string>
#include <thread>
#include "TcpConnection.h"

using namespace std;
using namespace net;
using namespace std::placeholders;

TcpConnection::TcpConnection(Tcp::socket&& socket):
	socket_(std::move(socket)),
	messageCallback_(defaultMessageCallback),
	writeCompleteCallback_(defaultWriteCompleteCallback)
{
}

void TcpConnection::start()
{
	doRead();
}

void TcpConnection::doRead()
{
	socket_.async_read_some(boost::asio::buffer(data_, kBufferSize),
							std::bind(&TcpConnection::onMessage, this, _1, _2));
}

void TcpConnection::asyncSend(const void* data, size_t len)
{
	boost::asio::async_write(socket_, boost::asio::buffer(data, len),
		std::bind(&TcpConnection::onWriteComplete, this, _1, _2));
}

void TcpConnection::asyncSend(const std::string& content)
{
	boost::asio::async_write(socket_, boost::asio::buffer(content.data(), content.size()),
							 std::bind(&TcpConnection::onWriteComplete, this, _1, _2));
}

bool TcpConnection::send(const void* data, size_t len)
{
	try
	{
		boost::asio::write(socket_, boost::asio::buffer(data, len));
	}
	catch (const std::exception& e)
	{
		cerr << e.what() << endl;
		return false;
	}
	return true;
}

bool TcpConnection::send(const std::string& content)
{
	try
	{
		boost::asio::write(socket_, boost::asio::buffer(content.data(), content.size()));
	}
	catch (const std::exception& e)
	{
		cerr << e.what() << endl;
		return false;
	}
	return true;
}

void TcpConnection::onMessage(const boost::system::error_code& error, size_t len)
{
	if (!error)
	{
		auto t = std::thread([=](){
			messageCallback_(shared_from_this(), data_, len);
		});
		t.detach();

		doRead();
	}
}

void TcpConnection::onWriteComplete(const boost::system::error_code& error, size_t len)
{
	if (!error)
	{
		writeCompleteCallback_(shared_from_this(), len);
	}
}