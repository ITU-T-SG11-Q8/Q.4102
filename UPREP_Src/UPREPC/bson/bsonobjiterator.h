// bson objiterator.h

/*    Copyright 2009 10gen Inc.
 *
 *    Licensed under the Apache License, Version 2.0 (the "License");
 *    you may not use this file except in compliance with the License.
 *    You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS,
 *    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *    See the License for the specific language governing permissions and
 *    limitations under the License.
 */

#pragma once

#include "bsonobj.h"

namespace _bson {

    /** iterator for a bsonobj

       Note each bsonobj ends with an EOO element: so you will get more() on an empty
       object, although next().eoo() will be true.

       The bsonobj must stay in scope for the duration of the iterator's execution.

       todo: we may want to make a more stl-like iterator interface for this
             with things like begin() and end()
    */
    class bsonobjiterator {
    public:
        /** Create an iterator for a BSON object.
        */
        bsonobjiterator(const bsonobj& jso) {
            int sz = jso.objsize();
            if ( sz == 0 ) {
                _pos = _theend = 0;
                return;
            }
            _pos = jso.objdata() + 4;
            _theend = jso.objdata() + sz - 1;
        }

        bsonobjiterator( const char * start , const char * end ) {
            _pos = start + 4;
            _theend = end - 1;
        }

        /** @return true if more elements exist to be enumerated. */
        bool more() { return _pos < _theend; }

        /** @return true if more elements exist to be enumerated INCLUDING the EOO element which is always at the end. */
        bool moreWithEOO() { return _pos <= _theend; }

        /** @return the next element in the object. For the final element, element.eoo() will be true. */
        bsonelement next( bool checkEnd ) {
            verify( _pos <= _theend );
            
            int maxLen = -1;
            if ( checkEnd ) {
                maxLen = _theend + 1 - _pos;
                verify( maxLen > 0 );
            }

            bsonelement e( _pos, maxLen );
            int esize = e.size( maxLen );
            massert( 16446, "bsonelement has bad size", esize > 0 );
            _pos += esize;

            return e;
        }
        bsonelement next() {
            verify( _pos <= _theend );
            bsonelement e(_pos);
            _pos += e.size();
            return e;
        }
        void operator++() { next(); }
        void operator++(int) { next(); }

        bsonelement operator*() {
            verify( _pos <= _theend );
            return bsonelement(_pos);
        }

    private:
        const char* _pos;
        const char* _theend;
    };
#if 0
    /** Base class implementing ordered iteration through BSONElements. */
    class BSONIteratorSorted {
        MONGO_DISALLOW_COPYING(BSONIteratorSorted);
    public:
        ~BSONIteratorSorted() {
            verify( _fields );
            delete[] _fields;
            _fields = 0;
        }

        bool more() {
            return _cur < _nfields;
        }

        bsonelement next() {
            verify( _fields );
            if ( _cur < _nfields )
                return bsonelement( _fields[_cur++] );
            return bsonelement();
        }

    protected:
        class ElementFieldCmp;
        BSONIteratorSorted( const bsonobj &o, const ElementFieldCmp &cmp );
        
    private:
        const char ** _fields;
        int _nfields;
        int _cur;
    };

    /** Provides iteration of a bsonobj's BSONElements in lexical field order. */
    class BSONObjIteratorSorted : public BSONIteratorSorted {
    public:
        BSONObjIteratorSorted( const bsonobj &object );
    };

    /**
     * Provides iteration of a BSONArray's BSONElements in numeric field order.
     * The elements of a bson array should always be numerically ordered by field name, but this
     * implementation re-sorts them anyway.
     */
    class BSONArrayIteratorSorted : public BSONIteratorSorted {
    public:
        BSONArrayIteratorSorted( const BSONArray &array );
    };

    /** Similar to BOOST_FOREACH
     *
     *  because the iterator is defined outside of the for, you must use {} around
     *  the surrounding scope. Don't do this:
     *
     *  if (foo)
     *      BSONForEach(e, obj)
     *          doSomething(e);
     *
     *  but this is OK:
     *
     *  if (foo) {
     *      BSONForEach(e, obj)
     *          doSomething(e);
     *  }
     *
     */

#define BSONForEach(e, obj)                                       \
    ::mongo::bsonobjiterator BOOST_PP_CAT(it_,__LINE__)(obj);     \
    for ( ::mongo::bsonelement e;                                 \
          (BOOST_PP_CAT(it_,__LINE__).more() ?                    \
           (e = BOOST_PP_CAT(it_,__LINE__).next(), true) :        \
           false) ;                                               \
          /*nothing*/ )

#endif

}
