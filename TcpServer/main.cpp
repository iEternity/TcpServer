#include <iostream>
#include <string>
#include "TcpServer.h"
#include "TcpConnection.h"
using namespace net;
using namespace std;

struct BuildConfig
{
	string appName;
	//打包类型，0：外网正式，125：内网测试，888：外网内测
	int16_t buildType;
	string recommendID;
	string channel;
	bool isUpdateSVN;
	bool isEncrypt;
	bool isYQW;
};

struct Message
{
	int32_t		request;
	size_t		size;
};

void onMessage(const std::shared_ptr<TcpConnection>& conn, const void* data, size_t len);
void sendString(const std::shared_ptr<TcpConnection>& conn, const string& content);
void sendFile(const std::shared_ptr<TcpConnection>& conn, const string& path);

int main()
{
	boost::asio::io_service ioService;
	TcpServer server(ioService, 12345);
	server.setMessageCallback(onMessage);

	ioService.run();
}

void onMessage(const std::shared_ptr<TcpConnection>& conn, const void* data, size_t len)
{
	const BuildConfig* pConfig = reinterpret_cast<const BuildConfig*>(data);

	sendString(conn, "开始打包，请稍后...");

	string content =
		"打包配置为:\n"
		"游戏包名	： " + pConfig->appName + "\n"
		"打包类型： " + to_string(pConfig->buildType) + "\n"
		"推广ID： " + pConfig->recommendID + "\n"
		"渠道类型	： " + pConfig->channel + "\n"
		"是否更新SVN： " + (pConfig->isUpdateSVN ? "是" : "否") + "\n"
		"是否加密	： " + (pConfig->isEncrypt ? "是" : "否") + "\n"
		"是否使用一起玩引擎： " + (pConfig->isYQW ? "是" : "否") + "\n";

	sendString(conn, content);

	sendFile(conn, "TestData.exe");
}

void sendString(const std::shared_ptr<TcpConnection>& conn, const string& content)
{
	Message msg;
	msg.request = 10000;
	msg.size = content.size();

	conn->send(&msg, sizeof(msg));
	conn->send(content.data(), content.size());
}

void sendFile(const std::shared_ptr<TcpConnection>& conn, const string& path)
{
	Message msg;
	msg.request = 10001;
	
	FILE* fp = fopen(path.c_str(), "rb");
	if (fp)
	{
		fseek(fp, 0, SEEK_END);
		long len = ftell(fp);
		fseek(fp, 0, SEEK_SET);

		msg.size = len;
		conn->send(&msg, sizeof(msg));

		char buf[128 * 1024];
		size_t nRead = fread(buf, 1, sizeof buf, fp);

		int hasSendBytes = 0;
		while (nRead > 0)
		{
			conn->send(buf, nRead);

			nRead = fread(buf, 1, sizeof buf, fp);
		}

		fclose(fp);
	}
	else
	{
		cerr << "failed to open " << path << endl;
	}
}