//
// Created by zhangkuo on 17-9-16.
//
#include "Buffer.h"
#include "SocketOps.h"

using namespace xnet;

const char Buffer::kCRLF[] = "\r\n";

ssize_t Buffer::readFd(int fd, int* savedErrno)
{
    char extraBuf[65536];
    struct iovec vec[2];
    vec[0].iov_base = begin() + writerIndex_;
    vec[0].iov_len = writableBytes();
    vec[1].iov_base = extraBuf;
    vec[1].iov_len = sizeof extraBuf;

    int iovCnt = writableBytes() < sizeof extraBuf ? 2 : 1;
    const ssize_t n = sockets::readv(fd, vec, iovCnt);
    if(n < 0)
    {
        *savedErrno = errno;
    }
    else if(n <= writableBytes())
    {
        writerIndex_ += n;
    }
    else
    {
        writerIndex_ = buffer_.size();
        append(extraBuf, n - writableBytes());
    }

    return n;
}
