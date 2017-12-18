#pragma once
#include <memory>
#include <boost/asio.hpp>
#include "Callbacks.h"

namespace net
{
	class TcpConnection : public std::enable_shared_from_this<TcpConnection>
	{
	public:
		using Tcp = boost::asio::ip::tcp;
	public:
		explicit TcpConnection(Tcp::socket&& socket);

		void start();

		void asyncSend(const void* data, size_t len);
		void asyncSend(const std::string& content);
		bool send(const void* data, size_t len);
		bool send(const std::string& content);

		void setMessageCallback(const MessageCallback& cb) { messageCallback_ = cb; }
		void setWriteCompleteCallback(const WriteCompleteCallback& cb) { writeCompleteCallback_ = cb; }

		void onMessage(const boost::system::error_code& error, size_t len);
		void onWriteComplete(const boost::system::error_code& error, size_t len);

		std::string peerAddress() const 
		{ 
			return socket_.remote_endpoint().address().to_string(); 
		}
		unsigned short peerPort() const 
		{ 
			return socket_.remote_endpoint().port(); 
		}
		std::string peerIpPort() const  
		{
			return std::string(peerAddress() + ":" + std::to_string(peerPort()));
		};

	private:
		void doRead();

	private:
		Tcp::socket socket_;
		static const int kBufferSize = 8 * 1024;
		char data_[kBufferSize];

		MessageCallback messageCallback_;
		WriteCompleteCallback writeCompleteCallback_;
	};
}