(function (window, $) {

    var pages = ['app/view/overlay.html'];
    var control = uPREP.createControl(uPREP.SERVICE.OVERLAY, pages);

    control.buttonToggle = true;

    control.overlayData = null;
    //control.currentOverlayMethod = null;
    //control.selectedJSONFormat = null;
    control.selectedOverlayData = null;
    control.overlayTable = null;

    control.requestMethod = null;
    control.isCreate = null;

    control.WEBSOCKET_PORT = 9110;
    control.JSON_SPACE = 3;
    control.webSocket = null;

    control.TYPE = {
        "CREATE": 0,
        "MODIFY": 1
    };

    //control.METHOD = {
    //    "GET": "GET",
    //    "POST":"POST",
    //    "PUT":"PUT",
    //    "DELETE":"DELETE"
    //};

    //control.ACTION = {
    //    "CREATE_OVERLAY": "CreateOverlay",
    //    "MODIFY_OVERLAY":"ModifyOverlay",
    //    "REMOVE_OVERLAY":"RemoveOverlay",
    //    "CUSTOM_OVERLAY":"CustomOverlay",
    //    "SELECTED_MODIFY_OVERLAY" :"SelectedModifyOverlay"
    //};

    //control.ACTION_URL = {
    //    "CREATE_OVERLAY": "/oms",
    //    "MODIFY_OVERLAY":"/oms/OverlayID",
    //    "SELECT_MODIFY_OVERLAY" : "/oms/"
    //};

    control.bind = function () {
        $(window).resize(function () {
            control.closePopupWindow();
        });
        // control.currentOverlayMethod = control.METHOD.GET;

        //control.getOverlayMethodRadioGroup().change(function(event){
        //    control.currentOverlayMethod = event.target.value;
        //});

        control.getOverlayActionApplyButton().click(function () {
            control.sendRestfulMessage();
        });

        //control.getOverlayJsonFormatSelect().change(function(event){
        //    control.selectedJSONFormat = event.target.value;
        //
        //    if(control.selectedJSONFormat == "NONE"){
        //        return;
        //    }else if(control.selectedJSONFormat == control.ACTION.CUSTOM_OVERLAY){
        //        control.getOverlayMethodContainer().show();
        //        control.getOverlayRequestTextArea().val("");
        //        control.getOverlayUrlTextBox().val("");
        //    }else if(control.selectedJSONFormat == control.ACTION.SELECTED_MODIFY_OVERLAY && control.selectedOverlayData != null){
        //        control.getOverlayMethodContainer().hide();
        //        control.getOverlayUrlTextBox().val(control.ACTION_URL.SELECT_MODIFY_OVERLAY + control.selectedOverlayData.OVERLAY_NETWORK_ID);
        //        control.requestOverlayActionJsonFormatter(control.selectedJSONFormat, control.selectedOverlayData.OVERLAY_NETWORK_ID);
        //    }else{
        //        if(control.selectedJSONFormat ==  control.ACTION.CREATE_OVERLAY){
        //            control.getOverlayUrlTextBox().val(control.ACTION_URL.CREATE_OVERLAY);
        //        }else if(control.selectedJSONFormat ==  control.ACTION.MODIFY_OVERLAY){
        //            control.getOverlayUrlTextBox().val(control.ACTION_URL.MODIFY_OVERLAY);
        //        }
        //        control.getOverlayMethodContainer().hide();
        //        control.requestOverlayActionJsonFormatter(control.selectedJSONFormat);
        //    }
        //    control.getOverlayActionApplyButton().prop("disabled",false);
        //});

        control.getOverlayRemoveAllButton().click(function () {
            swal({
                    title: "Are you sure?",
                    text: "Are you sure you want to delete All Overlay Network?",
                    type: "warning",
                    showCancelButton: true,
                    confirmButtonColor: "#DD6B55",
                    confirmButtonText: "Yes, delete it!",
                    closeOnConfirm: true
                },
                function () {
                    control.removeAllOverlay();
                });
        });

        control.getCreateOverlayButton().popover({
            trigger: 'manual'
            ,
            template: '<div class="popover" style="max-width: 445px;width:445px;z-index:10" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>'
            ,
            content: function () {
                return control.getOverlayInfoContentForm().html();
            }
        }).click(function (e) {
            e.stopPropagation();
            control.getModifyOverlayButton().popover('hide');
            //control.getCsManagerButton().popover('hide');

            $(this).popover('toggle');
            $('.content-type-m').hide();
            $('.content-type-c').show();

            control.setPopUpWindowOverlayInfo(control.TYPE.CREATE);
        });

        control.getModifyOverlayButton().popover({
            trigger: 'manual'
            ,
            template: '<div class="popover" style="max-width: 445px;width:445px;z-index:10" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>'
            ,
            content: function () {
                return control.getOverlayInfoContentForm().html();
            }
        }).click(function (e) {
            e.stopPropagation();
            control.getCreateOverlayButton().popover('hide');
            //control.getCsManagerButton().popover('hide');

            $(this).popover('toggle');
            $('.content-type-m').show();
            $('.content-type-c').hide();

            control.setPopUpWindowOverlayInfo(control.TYPE.MODIFY);
        });

        /*control.getCsManagerButton().popover({
         trigger: 'manual'
         ,template: '<div class="popover" style="max-width: 445px;width:445px;z-index:10" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>'
         ,content : function(){
         return control.getCsManagerFormHtml().html();
         }
         }).click(function(e){
         e.stopPropagation();
         control.getCreateOverlayButton().popover('hide');
         control.getModifyOverlayButton().popover('hide');

         $(this).popover('toggle');
         control.getUseResource();
         });*/


        control.getRefreshButton().click(function () {
            control.requestOverlayList();
            control.clearOverlayInformationPanel();
        });

        control.initializedOverlay();
    };

    control.event = function (event) {
        if (event.action == 'beforeShow') {
            if (control.overlayTable != null) {
                control.requestOverlayList();
            }
        }
        if (event.action == 'afterShow') {
            if (control.overlayTable != null) {
                control.clearOverlayInformationPanel();
            }
        }
    };

    control.initializedOverlay = function () {
        control.getWebSocketPort();
        control.requestOverlayList();
    };

    /* control 선언 */
    control.getOverlayMethodRadioGroup = function () {
        return $('[name="overlayMethod"]');
    };
    control.getOverlayMethodCheckedRadioGroup = function () {
        return $('[name="overlayMethod"]:checked');
    };
    control.getOverlayListGrid = function () {
        return $("#overlayGrid");
    };
    control.getOverlayActionApplyButton = function () {
        return $("#overlayActionApplyButton");
    };
    control.getOverlayRequestTextArea = function () {
        return $("#overlayRequestTextArea");
    };
    //control.getOverlayJsonFormatSelect = function() {
    //    return $( "#overlayJsonFormatSelect" );
    //};
    control.getOverlayMethodContainer = function () {
        return $("#overlayMethodContainer");
    };
    control.getOverlayUrlTextBox = function () {
        return $("#overlayUrlText");
    };
    control.getOverlayRemoveAllButton = function () {
        return $("#overlayRemoveAllButton");
    };
    control.getLastUpdateTime = function () {
        return $("#lastUpdateTime");
    };
    control.getRefreshButton = function () {
        return $("#refreshButton");
    };
    control.getRefreshMessage = function () {
        return $("#refreshMessage");
    };
    control.getOverlayResponseTextArea = function () {
        return $("#overlayResponseTextArea");
    };
    //control.getOverlayJsonFormatSelectedOption = function() {
    //    return $( "#overlayJsonFormatSelectedOption" );
    //};
    control.getCreateOverlayButton = function () {
        return $("#createOverlayButton");
    };
    control.getModifyOverlayButton = function () {
        return $("#modifyOverlayButton");
    };
    control.getOverlayInfoContentForm = function () {
        return $('#overlayInfoContentFormHtml');
    };
    /*control.getCsManagerButton = function() {
     return $( "#csManagerButton" );
     };*/
    /* control.getCsManagerFormHtml = function() {
     return $('#csManagerFormHtml');
     };*/
    /*control.getCsEnableButton = function() {
     return $('#csEnableButton');
     };*/
    /*control.getCsDisableButton = function() {
     return $('#csDisableButton');
     };*/
    /*control.getCsResourceId = function() {
     return $('#csResourceId');
     };*/
    /*control.getCsVirtualPeerId = function() {
     return $('#csVirtualPeerId');
     };*/
    /*control.getCsEnableMessageBox = function() {
     return $('#csEnableMessageBox');
     };*/
    /*control.getCsDisableMessageBox = function() {
     return $('#csDisableMessageBox');
     };*/

    /* WebSocket */
    control.initializeWebSocket = function (port, path) {
        control.webSocket = uPREP.createWebSocket(port, path, function (result) {
            control.setRefreshMessageVisible(true);
        });
    };

    /* Ajax Request */
    control.getWebSocketPort = function () {
        var jsonData = {};
        jsonData.UPREP = "uPREP";

        uPREP.sendAjax('/WebSocketPort', 'POST', jsonData, function (result) {
            var port = control.WEBSOCKET_PORT;

            if (result.WEBSOCKET != null) {
                port = result.WEBSOCKET;
            }

            control.initializeWebSocket(port, "OMS");
        }, function (err) {
            console.log(err);
        });
    };
    control.getOverlayInfo = function () {
        var jsonData = {};
        jsonData.UPREP = "uPREP";
        jsonData.OVERLAY_ID = control.selectedOverlayData.OVERLAY_NETWORK_ID;

        uPREP.sendAjax('/GetOverlayNetwork', 'POST', jsonData, function (result) {
            var json = result;

            if (json != null) {
                if (json.VERSION != null) {
                    $("#overlayInfoVersion").val(json.VERSION);
                }
                if (json.INDEX_URL != null) {
                    $("#overlayInfoIndexUrl").val(json.INDEX_URL);
                }
                if (json.OWNER_ID != null) {
                    $("#overlayInfoOwnerId").val(json.OWNER_ID);
                }
                if (json.EXPIRSE != null) {
                    $("#overlayInfoExpires").val(json.EXPIRSE);
                }
                if (json.CLOSED != null) {
                    $("#overlayInfoPamEnabled").val(json.CLOSED);
                }
                if (json.AUTH_KEY != null) {
                    $("#overlayInfoAuthKey").val(json.AUTH_KEY);
                }
                if (json.USERS != null) {
                    $("#overlayInfoUsers").val(json.USERS);
                }
            }
        }, function (err) {
            console.log(err);
        });
    };
    /*control.getUseResource = function(){
     var jsonData = {};
     jsonData.UPREP = "uPREP";
     jsonData.OVERLAY_ID = control.selectedOverlayData.OVERLAY_NETWORK_ID;

     uPREP.sendAjax('/GetUseResource', 'POST', jsonData, function(result){
     var json = result;

     if(json != null){
     if(json.result){
     control.getCsVirtualPeerId().val(json.VIRTUAL_PEER_ID);
     control.getCsResourceId().val(json.RESOURCE_ID);

     control.getCsVirtualPeerId().text(json.VIRTUAL_PEER_ID);
     control.getCsResourceId().text(json.RESOURCE_ID);

     control.setCsManagerForm(true);
     }
     else{
     control.setCsManagerForm(false);
     }
     }
     },function(err){
     control.setCsManagerForm();
     console.log(err);
     });
     };*/

    /*control.sendEnableCsMessage = function(jsonData){
     uPREP.sendAjax('/EnableCsMessage', 'POST', jsonData, function(result){
     if(result.result){
     control.getCsManagerButton().popover('hide');
     //swal("","Success","success");
     control.setCsManagerForm(false);
     }
     },function(err){
     setTimeout(function(){
     swal("","Failed Use Virtual Peer","error");
     }, 700);
     });
     };
     control.sendDisableCsMessage = function(){
     var jsonData = {};
     jsonData.UPREP = "uPREP";
     //jsonData.OVERLAY_ID = control.selectedOverlayData.OVERLAY_NETWORK_ID;
     jsonData.VIRTUAL_PEER_ID = control.getCsVirtualPeerId().val();
     jsonData.RESOURCE_ID = control.getCsResourceId().val();

     uPREP.sendAjax('/DisableCsMessage', 'POST', jsonData, function(result){
     if(result.result){
     control.getCsManagerButton().popover('hide');
     //swal("","Success","success");
     control.setCsManagerForm(true);
     /!*control.closePopupWindow(function(){
     swal("","Success","success");
     control.setCsManagerForm(true);
     });*!/
     }
     },function(err){
     setTimeout(function(){
     swal("","Failed Delete Virtual Peer","error");
     }, 700);
     });
     };*/
    //control.getOverlayInformation = function(overlayId){
    //    var jsonData = {};
    //    jsonData.UPREP = "uPREP";
    //    jsonData.OVERLAY_NETWORK_ID = overlayId;
    //
    //    uPREP.sendAjax('/GetOverlayNetwork', 'POST', jsonData, function(result){
    //        var msg = result;
    //
    //        try{
    //            msg = JSON.stringify(result, null, control.JSON_SPACE);
    //        }catch(err){
    //        }
    //        control.getOverlayRequestTextArea().val(msg);
    //    },function(err){
    //        console.log(err);
    //    });
    //};
    control.requestOverlayList = function (typeFlag) {
        var jsonData = {};
        jsonData.UPREP = "uPREP";

        uPREP.sendAjax('/GetOverlayNetworkList', 'POST', jsonData, function (result) {
            control.createOverlayListDataTable(result, typeFlag, function () {

            });
        }, function (err) {
            console.log(err);
        });
    };
    control.requestRemoveOverlay = function (overlayId) {
        var jsonData = {};
        jsonData.UPREP = "uPREP";

        uPREP.sendAjax('/RemoveOverlay/' + overlayId, 'POST', jsonData, function (result) {
            control.requestOverlayList();
        }, function (err) {
            if (err.status == 200) {
                control.requestOverlayList();
            } else {
                console.log(err);
            }
        });
    };
    control.removeAllOverlay = function () {
        var jsonData = {};
        jsonData.UPREP = "uPREP";

        uPREP.sendAjax('/RemoveAllOverlayNetwork', 'POST', jsonData, function (result) {
            control.requestOverlayList();
        }, function (err) {
            if (err.status == 200) {
                control.requestOverlayList();
            } else {
                console.log(err);
            }
        });
    };
    control.requestOverlayActionJsonFormatter = function (type, overlayId) {
        var jsonData = {
            "type": type
        };
        if (overlayId != null) {
            jsonData.OVERLAY_ID = overlayId;
        }

        uPREP.sendAjax('/JsonFormatter', 'POST', jsonData, function (result) {
            var msg = result;

            try {
                msg = JSON.stringify(result, null, control.JSON_SPACE);
            } catch (err) {
            }

            control.getOverlayRequestTextArea().val(msg);
        }, function (err) {
            control.getOverlayRequestTextArea().val("Request Error");
        });
    };
    control.sendRestfulMessage = function () {
        var json = {};
        var jsonStr = control.getOverlayRequestTextArea().val().trim();
        var url = control.getOverlayUrlTextBox().val().trim();
        var method = control.requestMethod;

        //if(control.selectedJSONFormat ==  control.ACTION.CUSTOM_OVERLAY){
        //    method = control.getOverlayMethodCheckedRadioGroup().val();
        //}else if(control.selectedJSONFormat ==  control.ACTION.CREATE_OVERLAY){
        //    method = control.METHOD.POST;
        //}else if(control.selectedJSONFormat ==  control.ACTION.MODIFY_OVERLAY || control.selectedJSONFormat ==  control.ACTION.SELECTED_MODIFY_OVERLAY){
        //    method = control.METHOD.PUT;
        //}

        try {
            if (jsonStr.length > 0) {
                json = $.parseJSON(jsonStr);
            }
        } catch (err) {
            control.getOverlayResponseTextArea().val("Failed to create JSON Object");
            return;
        }

        uPREP.sendAjax(url, method, json, function (result) {
            var msg = result;

            try {
                msg = JSON.stringify(result, null, control.JSON_SPACE);
            } catch (err) {
            }
            control.getOverlayResponseTextArea().val(msg);
        }, function (err) {
            if (err.status == 200) {
                control.getOverlayResponseTextArea().val("Response 200 OK");
            } else {
                control.getOverlayResponseTextArea().val("Request Error :" + err.status);
            }
        });
    };


    /* Control Action */
    //TODO
    control.enableButtonClick = function () {
        var timeout = $("#csTimeout").val();
        var maxUpBw = $("#csMaxUpBw").val();
        var maxDnBw = $("#csMaxDnBw").val();
        var maxNumConnection = $("#csMaxNumConnection").val();

        var jsonData = {};
        jsonData.UPREP = "uPREP";
        jsonData.OVERLAY_ID = control.selectedOverlayData.OVERLAY_NETWORK_ID;
        jsonData.ACTION_TYPE = $("#csActionType").val();
        jsonData.NOTIFICATION_ADDRESS = $("#csNotificationAddress").val().trim();
        jsonData.STORAGE_SIZE = parseInt($("#csStorageSize").val());
        jsonData.MAX_UP_BW = maxUpBw != "" ? parseInt(maxUpBw) : null;
        jsonData.MAX_DN_BW = maxDnBw != "" ? parseInt(maxDnBw) : null;
        jsonData.MAX_NUM_CONNECTION = maxNumConnection != "" ? parseInt(maxNumConnection) : null;
        jsonData.TIMEOUT = timeout != "" ? parseInt(timeout) : null;
        jsonData.MAX_TRAFFIC = parseInt($("#csMaxTraffic").val());
        jsonData.NUM_OF_SEEDER = parseInt($("#csNumOfSeeder").val());
        jsonData.COMPLETED = $("#csCompleted").val() == "true";

        if (jsonData.TIMEOUT == null || jsonData.MAX_UP_BW == null || jsonData.MAX_DN_BW == null || jsonData.MAX_NUM_CONNECTION == null) {
            swal("", "Input Values", "info");
            return;
        }

        swal({
                title: "",
                text: "Are you sure you want to Use Virtual Peer?",
                type: "info",
                showCancelButton: true,
                /*confirmButtonColor : "#DD6B55",*/
                confirmButtonText: "Yes",
                closeOnConfirm: true
            },
            function () {
                control.sendEnableCsMessage(jsonData);
            });
    };
    control.disableButtonClick = function () {
        swal({
                title: "",
                text: "Are you sure you want to Delete Virtual Peer?",
                type: "info",
                showCancelButton: true,
                confirmButtonColor: "#DD6B55",
                confirmButtonText: "Yes, delete it!",
                closeOnConfirm: true
            },
            function () {
                control.sendDisableCsMessage();
            });
    };
    /*control.setCsManagerForm = function(type){
     if(type){
     control.getCsEnableMessageBox().show();
     control.getCsDisableMessageBox().hide();

     control.getCsEnableButton().prop("disabled", true);
     control.getCsDisableButton().prop("disabled", false);
     } else if(!type){
     control.getCsEnableMessageBox().hide();
     control.getCsDisableMessageBox().show();

     control.getCsEnableButton().prop("disabled", false);
     control.getCsDisableButton().prop("disabled", true);
     } else{
     control.getCsEnableMessageBox().hide();
     control.getCsDisableMessageBox().hide();

     control.getCsEnableButton().prop("disabled", true);
     control.getCsDisableButton().prop("disabled", true);
     }
     };*/
    control.closePopupWindow = function (callback) {
        control.getCreateOverlayButton().popover('hide');
        control.getModifyOverlayButton().popover('hide');
        //control.getCsManagerButton().popover('hide');
        if (callback != null) {
            callback();
        }
    };
    control.setPopUpWindowOverlayInfo = function (type) {
        control.isCreate = (type == control.TYPE.CREATE);

        if (type == control.TYPE.CREATE) {
            $("#overlayInfoVersion").val("");
            $("#overlayInfoIndexUrl").val("");
            $("#overlayInfoOwnerId").val("");
            $("#overlayInfoExpires").val("");
            $("#overlayInfoAuthKey").val("");
            $("#overlayInfoUsers").val("");

            $("#overlayInfoClosed").val("no");
            $("#overlayInfoPamEnabled").val("false");
        } else if (type == control.TYPE.MODIFY) {
            control.getOverlayInfo();
        }
    };
    control.setRefreshMessageVisible = function (type) {
        if (type != null && type == true) {
            control.getRefreshMessage().show();
        }
        else {
            control.getRefreshMessage().hide();
        }
    };
    control.setCurrentTime = function () {
        var data = new Date();
        var current_time = data.toTimeString().split(" ")[0];
        control.getLastUpdateTime().text(current_time);
    };
    control.loadDataTable = function (callback) {

        control.overlayTable = $('#overlayDataTable').on('search.dt', control.OnChange).on('page.dt', control.OnChange).DataTable(
            {
                "lengthMenu": [[5, 10, 20, -1], [5, 10, 20, "All"]],
                "order": [[4, "desc"]],
                "columnDefs": [{"targets": 5, "orderable": false, "searchable": false}, {
                    "targets": 6,
                    "orderable": false,
                    "searchable": false
                }]
            }
        );

        if (callback != null) {
            callback();
        }
    };
    control.clearOverlayInformationPanel = function () {
        //control.selectedJSONFormat = null;
        control.getOverlayMethodContainer().hide();
        control.getOverlayRequestTextArea().val("");
        control.getOverlayResponseTextArea().val("");
        control.getOverlayUrlTextBox().val("");
        //control.getOverlayJsonFormatSelect().val("NONE");
        control.getOverlayActionApplyButton().prop("disabled", true);
    };
    control.createOverlayListDataTable = function (data, typeFlag, callback) {
        control.overlayData = data;
        control.selectedOverlayData = null;
        control.getModifyOverlayButton().prop("disabled", true);
        //control.getCsManagerButton().prop("disabled", true);
        //control.getOverlayJsonFormatSelectedOption().prop("disabled", true);
        var html = "";

        control.setCurrentTime();
        control.setRefreshMessageVisible(false);

        if (control.overlayTable != null) {
            $('#overlayDataTable').DataTable().destroy();
            control.overlayTable = null;
        }

        for (var index = 0; index < control.overlayData.length; index++) {
            var trTag = "";

            var title = control.overlayData[index].TITLE != null ? control.overlayData[index].TITLE : "-";
            var channel_id = control.overlayData[index].CHANNEL_ID != null ? control.overlayData[index].CHANNEL_ID : "-";
            var overlay_network_id = control.overlayData[index].OVERLAY_NETWORK_ID != null ? control.overlayData[index].OVERLAY_NETWORK_ID : "";
            var owner_id = control.overlayData[index].OWNER_ID != null ? control.overlayData[index].OWNER_ID : "";
            var created_at = control.overlayData[index].CREATED_AT != null ? control.overlayData[index].CREATED_AT : "";
            var oms_vp_cnt = control.overlayData[index].OMS_VP_CNT != null ? control.overlayData[index].OMS_VP_CNT : "";

            trTag += "<tr>";
            trTag += "<td class='dataTableCell' style='none'>" + title + "</td>";
            trTag += "<td class='dataTableCell' style='none'>" + channel_id + "</td>";
            trTag += "<td class='dataTableCell' style='none'name='OVERLAY_NETWORK_ID'>" + overlay_network_id + "</td>";
            trTag += "<td class='dataTableCell' style='none'>" + owner_id + "</td>";
            trTag += "<td class='dataTableCell' style='none'>" + created_at + "</td>";
            trTag += "<td class='dataTableCell' style='none'>";
            trTag += "<button type='button' class='btn btn-sm btn-danger' value='" + overlay_network_id + "'>Delete</button>";
            /* trTag +=    "<button type='button' class='btn-primary' value='"+ overlay_network_id +"'>CS Use</button>";*/
            trTag += "</td>";
            trTag += "<td class='dataTableCell' style='none'>";
            trTag += "<div>";
            trTag += "<button type='button' class='btn btn-sm button_cs button_cs_left' value='" + overlay_network_id + "' name='m'>-</button>";
            trTag += "<input type='number' value='" + oms_vp_cnt + "' class='input_cs' readonly>";
            trTag += "<button type='button' class='btn btn-sm button_cs button_cs_right' value='" + overlay_network_id + "' name='p'>+</button>";
            trTag += "</div>";
            trTag += "</td>";
            //if(index%2 == 0){
            //    trTag += "<button style='margin-left: 5px;' type='button'class='btn-info' value='"+ overlay_network_id +"'>PAMS</button></td>";
            //}
            trTag += "</tr>";

            html += trTag;
            //html += trTag.replace(/none/gi, isSelectedRow ? "background-color:#BDF3F3" : "");
        }

        control.getOverlayListGrid().html(html);
        control.loadDataTable();

        control.bindingDataTableSelectEvent();
        control.bindDataTableDeleteButtonEvent();
        /*control.bindDataTableCsButtonEvent();*/

        if (callback != null) {
            callback();
        }
    };


    /* Event */
    control.OnChange = function (a, b, c) {
        //control.setAutoRefreshStatus(control.overlayTable==null || control.overlayTable.page() == 0 && control.overlayTable.search() == "");
    };

    /*control.convertJsonString = function(){
     var jsonResult = {};

     var version = $("#overlayInfoVersion").val().trim();
     var indexUrl = $("#overlayInfoIndexUrl").val().trim();
     var ownerId = $("#overlayInfoOwnerId").val().trim();
     var expiresStr = $("#overlayInfoExpires").val().trim();
     var pamEnabled = $("#overlayInfoPamEnabled").val() == "true";
     var closed = $("#overlayInfoClosed").val();
     var authKey = $("#overlayInfoAuthKey").val().trim();
     var usersStr = $("#overlayInfoUsers").val().trim();
     var expires;
     var users = usersStr.split(",");

     try{
     expires = Number(expiresStr);
     version = Number(version);
     }catch(err){
     swal("","Failed to create JSON Object","info");
     return;
     }

     if(control.isCreate){
     control.requestMethod = "POST";

     var auth = {
     "closed" : closed
     ,"auth-key" : authKey
     };
     if(closed != "auth" || authKey.length < 1){
     delete auth["auth-key"];
     }

     jsonResult = {
     "owner-id" : ownerId
     ,"expires" : expires
     ,"pam-enabled" : pamEnabled
     ,"auth" : auth
     ,"users" : users
     };

     if(expiresStr.length < 1){
     delete jsonResult["expires"];
     }
     if(usersStr.length < 1){
     delete jsonResult["users"];
     }

     }else{
     control.requestMethod = "PUT";

     var auth = {
     "closed" : closed
     ,"auth-key" : authKey
     };
     if(closed != "auth" || authKey.length < 1){
     delete auth["auth-key"];
     }

     jsonResult = {
     "version" : version
     ,"index-url" : indexUrl
     ,"owner-id" : ownerId
     ,"expires" : expires
     ,"auth" : auth
     ,"users" : users
     };

     if(indexUrl.length < 1){
     delete jsonResult["index-url"];
     }
     if(expiresStr.length < 1){
     delete jsonResult["expires"];
     }
     if(usersStr.length < 1){
     delete jsonResult["users"];
     }
     }

     try{
     msg = JSON.stringify(jsonResult, null, control.JSON_SPACE);
     }catch(err){
     swal("","Failed to create JSON Object","info");
     control.getOverlayActionApplyButton().prop("disabled", true);
     return;
     }

     control.getOverlayRequestTextArea().val(msg);
     control.closePopupWindow();

     if(control.isCreate){
     control.getOverlayUrlTextBox().val("/oms");
     } else{
     control.getOverlayUrlTextBox().val("/oms/" + control.selectedOverlayData.OVERLAY_NETWORK_ID);
     }

     control.getOverlayActionApplyButton().prop("disabled",false);
     };*/

    control.bindDataTableDeleteButtonEvent = function () {
        $("#overlayGrid").find(".btn-danger").click(function (event) {
            var overlayId = event.target.value;
            if (overlayId != null) {
                control.requestRemoveOverlay(overlayId);
            }
        });

        $("#overlayGrid").find(".button_cs").click(function (event) {
            var overlayId = event.target.value;
            var row = $.grep(control.overlayData, function (e) {
                return e.OVERLAY_NETWORK_ID == event.target.value
            })[0];

            var isPlus = event.target.name == "p";
            if (row != null && row.OMS_VP_CNT != null) {
                var jsonData = {
                    UPREP :"uPREP",
                    OVERLAY_ID : overlayId
                };

                if (isPlus) {
                    control.sendEnableCsMessage(jsonData);
                } else {
                    if (row.OMS_VP_CNT > 0) {
                        control.sendDisableCsMessage(jsonData);
                    }
                }
            } else {
                console.log("Error : VP " + overlayId);
            }
        });
    };

    control.sendEnableCsMessage = function (jsonData) {
        uPREP.sendAjax('/EnableCsMessage', 'POST', jsonData, function (result) {
            if (result.result) {
                swal("","Success","success");
            }
        }, function (err) {
            setTimeout(function () {
                var obj;
                try{
                    obj = JSON.parse(err.responseText);
                }catch(e){
                    obj = null;
                }
                var message = "Failed Use Virtual Peer";
                if (obj != null) {
                    message += " : "+obj["error reason"];
                }
                swal("", message, "error");
            }, 700);
        });
    };
    control.sendDisableCsMessage = function (jsonData) {
        uPREP.sendAjax('/DisableCsMessage', 'POST', jsonData, function (result) {
            if (result.result) {
                swal("","Success","success");
            }
        }, function (err) {
            setTimeout(function () {
                var obj;
                try{
                    obj = JSON.parse(err.responseText);
                }catch(e){
                    obj = null;
                }
                var message = "Failed Delete Virtual Peer";
                if (obj != null) {
                    message += " : "+obj["error reason"];
                }
                swal("", message, "error");
            }, 700);
        });
    };
    /* control.bindDataTableCsButtonEvent = function(){
     $("#overlayGrid").find(".btn-primary").click(function(event){
     var overlayId  = event.target.value;
     console.log("primary =" + overlayId);
     });
     };*/
    control.bindingDataTableSelectEvent = function () {
        control.getOverlayListGrid().undelegate("td", "click");
        control.getOverlayListGrid().delegate("td", "click", function () {
            var col = $(this)[0];
            var currentRow = $(this).closest('tr');

            if (col != null) {
                var row = col.parentNode;

                if (row != null) {
                    var rowData = $.grep(control.overlayData, function (e) {
                        return e.OVERLAY_NETWORK_ID == row.cells["OVERLAY_NETWORK_ID"].textContent
                    });
                    var data = null;

                    if (rowData.length > 0 && rowData[0] != null) {
                        data = rowData[0];
                    }

                    if (data != null) {
                        control.selectedOverlayData = data;
                        //control.getOverlayJsonFormatSelectedOption().prop("disabled", false);
                        control.getModifyOverlayButton().prop("disabled", false);
                        // control.getCsManagerButton().prop("disabled", false);
                        control.getOverlayListGrid().find("td").css({"background-color": ""});
                        currentRow.find("td").css({"background-color": "#BDF3F3"});

                        if (col.cellIndex == 1) {
                            //if(col.textContent != null){
                            //    control.clearOverlayInformationPanel();
                            //    control.getOverlayInformation(col.textContent);
                            //}
                            if (data.INDEX_URL != null && data.INDEX_URL.length > 0) {
                                var url = data.INDEX_URL;
                                if (url.indexOf("http://") < 0) {
                                    url = "http://" + url;
                                }
                                var ixsUrl = url.split("/ixs")[0];

                                window.open(ixsUrl, "_blank");
                            } else {
                                swal("", "Dose not exist INDEX-URL", "info");
                            }

                        } else if (col.cellIndex == 2) {
                            if (data.PAMS_URL != null && data.PAMS_URL.length > 0) {
                                var url = data.PAMS_URL;
                                if (url.indexOf("http://") < 0) {
                                    url = "http://" + url;
                                }
                                var pamsUrl = url.split("/pams")[0];

                                window.open(pamsUrl, "_blank");
                            } else {
                                swal("", "Dose not exist PAMS-URL", "info");
                            }
                        }
                        /*else if(control.selectedJSONFormat == control.ACTION.SELECTED_MODIFY_OVERLAY){
                         control.getOverlayUrlTextBox().val(control.ACTION_URL.SELECT_MODIFY_OVERLAY + control.selectedOverlayData.OVERLAY_NETWORK_ID);
                         control.requestOverlayActionJsonFormatter(control.ACTION.SELECTED_MODIFY_OVERLAY, control.selectedOverlayData.OVERLAY_NETWORK_ID);
                         }*/
                    }
                }
            }
        });
    };

})(window, jQuery);