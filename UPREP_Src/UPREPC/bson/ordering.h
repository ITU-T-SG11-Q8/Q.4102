// ordering.h

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

namespace _bson {

    /** A precomputation of a BSON sort key pattern.  That is something like: 
           { a : 1, b : -1 }
        The constructor is private to make conversion more explicit so we notice where we call make().
    */
    class Ordering {
        unsigned bits;
        Ordering(unsigned b) : bits(b) { }
    public:
        Ordering(const Ordering& r) : bits(r.bits) { }
        void operator=(const Ordering& r) {
            bits = r.bits;
        }

        /** so, for key pattern { a : 1, b : -1 }
            get(0) == 1
            get(1) == -1
        */
        int get(int i) const {
            return ((1 << i) & bits) ? -1 : 1;
        }

        // for woCompare...
        unsigned descending(unsigned mask) const { return bits & mask; }

        /*
        static Ordering make(const bsonobj& obj) {
            unsigned b = 0;
            bsonobjiterator k(obj);
            unsigned n = 0;
            while( 1 ) {
                bsonelement e = k.next();
                if( e.eoo() )
                    break;
                uassert( 13103, "too many compound keys", n <= 31 );
                if( e.number() < 0 )
                    b |= (1 << n);
                n++;
            }
            return Ordering(b);
        }*/
    };

}
