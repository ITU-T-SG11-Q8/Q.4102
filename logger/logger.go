// 
// The MIT License
// 
// Copyright (c) 2022 ETRI
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.
// 

package logger

import (
	"encoding/json"
	"io"
	"log"
	"os"
)

var LEVEL int = 2

var INFO int = 2
var WORK int = 1
var ERROR int = 0

var FileLog bool = false

var logger *log.Logger

func init() {
	if FileLog {
		file, err := os.OpenFile("log.txt", os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0666)
		if err != nil {
			log.Fatal(err)
		}

		mw := io.MultiWriter(os.Stdout, file)
		logger = log.New(mw, "", log.LstdFlags)
	} else {
		logger = log.New(os.Stdout, "", log.LstdFlags)
	}
}

func Printf(level int, format string, v ...interface{}) {
	if level <= LEVEL {
		logger.Printf(format, v...)
	}
}

func Println(level int, v ...interface{}) {
	if level <= LEVEL {
		logger.Println(v...)
	}
}

func PrintJson(level int, header string, jsonv interface{}) {
	buf, err := json.MarshalIndent(jsonv, "", "   ")
	if err != nil {
		logger.Println(level, header, "json marshal err: ", err)
	} else {
		logger.Println(level, header, ": ", string(buf))
	}
}

func SetLevel(level int) {
	LEVEL = level
}
