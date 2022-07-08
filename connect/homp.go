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

package connect

import (
	"encoding/json"
	"logger"

	"github.com/go-resty/resty/v2"
)

type HOMP struct {
	OverlayAddr string
}

func (self *HOMP) CreateOverlay(hoc *HybridOverlayCreation) *HybridOverlayCreationResponseOverlayInfo {

	//hocjson := hoc.get()

	//self.printJson(hocjson, "Create overlay", logger.WORK)

	logger.PrintJson(logger.WORK, "Create overlay", hoc)

	//buf, _ := json.MarshalIndent(hoc, "", "   ")

	client := resty.New()
	resp, err := client.R().
		SetHeader("Content-Type", "application/json").
		SetBody(hoc).
		Post(self.OverlayAddr + "/homs")

	if err != nil {
		logger.Println(logger.WORK, "Create overlay error : ", err)
		return nil
	}

	if resp.StatusCode() != 200 {
		logger.Println(logger.WORK, "Create overlay error : ", resp.Status(), resp)
		return nil
	}

	ovinfo := new(HybridOverlayCreationResponse)
	json.Unmarshal(resp.Body(), ovinfo)

	logger.PrintJson(logger.WORK, "Create overlay resp", ovinfo)

	return &ovinfo.OverlayInfo
}

func (self *HOMP) QueryOverlay(ovid *string, title *string, desc *string) *[]HybridOverlayQueryResponse {
	logger.Printf(logger.WORK, "Query Overlay : Overlay ID:%v, Title:%v, Description:%v", ovid, title, desc)

	params := map[string]string{}

	if ovid != nil && len(*ovid) > 0 {
		params["overlay-id"] = *ovid
	}

	if title != nil && len(*title) > 0 {
		params["title"] = *title
	}

	if desc != nil && len(*desc) > 0 {
		params["description"] = *desc
	}

	client := resty.New()
	resp, err := client.R().
		SetQueryParams(params).
		Get(self.OverlayAddr + "/homs")

	if err != nil {
		logger.Println(logger.WORK, "Query overlay error : ", err)
		return nil
	}

	ovinfo := new([]HybridOverlayQueryResponse)
	json.Unmarshal(resp.Body(), ovinfo)
	logger.PrintJson(logger.WORK, "Query overlay resp", ovinfo)

	return ovinfo
}

func (self *HOMP) OverlayJoin(hoj *HybridOverlayJoin) *HybridOverlayJoinResponseOverlay {

	logger.PrintJson(logger.WORK, "Join overlay", hoj)

	client := resty.New()
	resp, err := client.R().
		SetBody(hoj).
		Post(self.OverlayAddr + "/peer")

	if err != nil {
		logger.Println(logger.WORK, "Join overlay error : ", err)
		return nil
	}

	ovinfo := new(HybridOverlayJoinResponse)
	json.Unmarshal(resp.Body(), ovinfo)

	logger.PrintJson(logger.WORK, "Join overlay resp", ovinfo)

	return &ovinfo.Overlay
}

func (self *HOMP) OverlayModification(hom *HybridOverlayModification) *HybridOverlayModificationOverlay {

	logger.PrintJson(logger.WORK, "Modification overlay", hom)

	client := resty.New()
	resp, err := client.R().
		SetBody(hom).
		Put(self.OverlayAddr + "/homs")

	if err != nil {
		logger.Println(logger.WORK, "Modification overlay error : ", err)
		return nil
	}

	ovinfo := new(HybridOverlayModification)
	json.Unmarshal(resp.Body(), ovinfo)

	logger.PrintJson(logger.WORK, "Modification overlay resp", ovinfo)

	return &ovinfo.Overlay
}

func (self *HOMP) OverlayRemoval(hor *HybridOverlayRemoval) *HybridOverlayRemovalResponseOverlay {

	logger.PrintJson(logger.WORK, "Remove overlay", hor)

	client := resty.New()
	resp, err := client.R().
		SetBody(hor).
		Delete(self.OverlayAddr + "/homs")

	if err != nil {
		logger.Println(logger.WORK, "Remove overlay error : ", err)
		return nil
	}

	rslt := new(HybridOverlayRemovalResponse)
	json.Unmarshal(resp.Body(), rslt)

	logger.PrintJson(logger.WORK, "Remove overlay resp", rslt)

	return &rslt.Overlay
}

func (self *HOMP) OverlayReport(hor *HybridOverlayReport) *HybridOverlayReportOverlay {

	logger.PrintJson(logger.WORK, "Report Overlay", hor)

	client := resty.New()
	resp, err := client.R().
		SetBody(hor).
		Post(self.OverlayAddr + "/peer/report")

	if err != nil {
		logger.Println(logger.WORK, "Report overlay error : ", err)
		return nil
	}

	ovinfo := new(HybridOverlayReportResponse)
	json.Unmarshal(resp.Body(), ovinfo)

	logger.PrintJson(logger.WORK, "Report Overlay resp", ovinfo)

	return &ovinfo.Overlay
}

func (self *HOMP) OverlayRefresh(hor *HybridOverlayRefresh) *HybridOverlayRefreshResponse {

	//self.printJson(hor, "Refresh Overlay: ", logger.INFO)
	//logger.Println(logger.WORK, "Send Refresh Overlay")

	client := resty.New()
	resp, err := client.R().
		SetBody(hor).
		Put(self.OverlayAddr + "/peer")

	if err != nil {
		logger.Println(logger.ERROR, "Refresh overlay error : ", err)
		return nil
	}

	ovinfo := new(HybridOverlayRefreshResponse)
	json.Unmarshal(resp.Body(), ovinfo)

	//self.printJson(ovinfo, "Refresh overlay resp: ", logger.INFO)
	//logger.Println(logger.WORK, "Recv Refresh Overlay resp")

	return ovinfo
}

func (self *HOMP) OverlayLeave(hol *HybridOverlayLeave) *HybridOverlayLeaveResponse {
	logger.Println(logger.WORK, "Send Overlay leave")

	client := resty.New()
	resp, err := client.R().
		SetBody(hol).
		Delete(self.OverlayAddr + "/peer")

	if err != nil {
		logger.Println(logger.ERROR, "Overlay leave error : ", err)
		return nil
	}

	ovl := new(HybridOverlayLeaveResponse)
	json.Unmarshal(resp.Body(), ovl)

	logger.Println(logger.WORK, "Recv Overlay leave resp")

	return ovl
}
