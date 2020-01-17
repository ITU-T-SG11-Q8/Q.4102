#pragma once

#include <cassert>
#include <string>

#define NOINLINE_DECL

namespace _bson {

    class MsgAssertionException : public std::exception {
    public:
        MsgAssertionException(unsigned, std::string _s) : s(_s) {}
        ~MsgAssertionException() throw() { }
        const std::string s;
        virtual const char * what() const throw() { return s.c_str();  }
    };

    inline void uasserted(unsigned, std::string) { assert(false); }
    inline void uassert(unsigned a, const char *str, bool x) {
        assert(x);
    }
    inline void uassert(unsigned, std::string, bool x) {
        assert(x);
    }
    inline void msgasserted(unsigned x, std::string s) { throw MsgAssertionException(x, s); }
    inline void massert(unsigned a, const char *b, bool x) {
        if (!x) msgasserted(a, std::string(b));
    }
    inline void massert(unsigned a, std::string b, bool x) {
        if (!x) msgasserted(a, b);
    }
    inline void verify(bool x) { assert(x); }

}
