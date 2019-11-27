/**
 * Created by JH_KIM on 2016-02-22.
 */

(function(window, $) {

    $( document ).ready(function() {
        uPREP.initialized();
    });

    var current_view = null;
    var current_control = null;
    var viewOutConfirm = null;

    var uPREP = function() {

    };

    uPREP.SERVICE = {
        'OVERLAY': "overlay"
        ,'RESOURCE':"resource"
    };

    uPREP.LOAD_SERVICE_SCRIPT = [
        uPREP.SERVICE.OVERLAY
        , uPREP.SERVICE.RESOURCE
    ];

    uPREP.START_SERVICE = uPREP.SERVICE.OVERLAY;

    uPREP.METHOD = {
        "GET": "GET",
        "POST":"POST",
        "PUT":"PUT",
        "DELETE":"DELETE"
    };

    uPREP.WEBSOCKET = {};

    uPREP.initialized = function() {

        for(var i = 0; i < uPREP.LOAD_SERVICE_SCRIPT.length; i++) {
            var service = uPREP.LOAD_SERVICE_SCRIPT[i];
            uPREP.loadScript(service, 'app/js/' + service + '.js', function(service, path, state) {
                var control = uPREP[service];
                if(control != null) {
                    control.initialized();
                }
                if(service == uPREP.START_SERVICE){
                    control.show();
                }
            });
        }
    };

    uPREP.loadScript = function(service, path, callback) {
        var done = false;
        var head= document.getElementsByTagName('head')[0];
        var scr = document.createElement('script');

        scr.onload = handleLoad;
        scr.onreadystatechange = handleReadyStateChange;
        scr.onerror = handleError;
        scr.src = path;
        head.appendChild(scr);

        function handleLoad() {
            if (!done) {
                done = true;
                callback(service, path, "ok");
            }
        }

        function handleReadyStateChange() {
            var state;

            if (!done) {
                state = scr.readyState;
                if (state === "complete") {
                    handleLoad();
                }
            }
        }
        function handleError() {
            if (!done) {
                done = true;
                callback(service, path, "error");
            }
        }
    };

    uPREP.getOverlay = function() {
        return uPREP[uPREP.SERVICE.OVERLAY];
    };
    uPREP.getResource = function() {
        return uPREP[uPREP.SERVICE.RESOURCE];
    };

    uPREP.getWebSocket = function() {
        return uPREP[uPREP.SERVICE.WEBSOCKET];
    };

    uPREP.getContainer = function() {
        return document.getElementById('container');
    };

    uPREP.clear = function() {
        while(uPREP.getContainer().childNodes.length > 0) {
            uPREP.getContainer().removeChild(uPREP.getContainer().childNodes[0]);
        }
    };

    uPREP.createBody = function(id, html) {
        var body = document.createElement('div');
        $(body).html(html);
        return body;
    };

    uPREP.getView = function() {
        return current_view;
    };

    uPREP.setView = function(view) {
        current_view = view;
    };

    uPREP.getViewOutConfirm = function() {
        return viewOutConfirm;
    };

    uPREP.setViewOutConfirm = function(confirm) {
        viewOutConfirm = confirm;
    };

    uPREP.delayTimer = null;
    uPREP.delayTask = function(delay, callbak) {
        if(uPREP.delayTimer != null) {
            clearTimeout(uPREP.delayTimer);
        };

        uPREP.delayTimer = setTimeout(callbak, delay);
    };

    uPREP.showRun = function(control, callback) {
        var oldView = uPREP.getView();

        control.fire({'control': control, 'action': 'beforeShow'});
        if(current_control != null) {
            current_control.fire({'control': control, 'action': 'beforeHide'});
            current_control.beforeHide(oldView);
        }

        if(oldView == control.getView()) {
            return;
        }

        uPREP.clear();
        if(control.getContents() == null) {
            uPREP.html(control.getView(), function (html) {
                control.setContents(uPREP.createBody(control.getService(), html));
                uPREP.getContainer().appendChild(control.getContents());

                control.bind();
            });
        } else {
            uPREP.getContainer().appendChild(control.getContents());
        }

        uPREP.setView(control.getView());

        control.fire({'control': control, 'action': 'afterShow'});
        if(current_control != null) {
            if(control.buttonToggle) {
                //current_control.getTab()[0].className = '';
            }
            current_control.fire({'control': control, 'action': 'afterHide'});
            current_control.afterHide(oldView);
        }

        if(control.buttonToggle) {
            //control.getTab()[0].className = 'on';
        }
        current_control = control;
        window.control = current_control;

        if(callback != null) {
            uPREP.delayTask(200, callback);
        }

        window.document.body.scrollTop = 0;
    };

    uPREP.show = function(control, callback) {
        if(control.getView() == null) {
            return;
        }

        uPREP.showConfirm(control, callback, uPREP.showRun);
    };

    uPREP.showConfirm = function(control, callback, subFunc) {
        if(uPREP.getViewOutConfirm()) {
            $("#confirmDialog").modal({
                backdrop : 'static',
                keyboard : false
            });

            $("#confirmButton").unbind("click");
            $("#confirmButton").click(function(){
                uPREP.setViewOutConfirm(false);
                $("#confirmDialog").modal('hide');
                if(subFunc != null) {
                    subFunc(control, callback);
                } else {
                    callback(true);
                }
            });
        } else {
            if(subFunc != null) {
                subFunc(control, callback);
            } else {
                callback(true);
            }
        }
    };

    uPREP.html = function(url, callback) {
        uPREP.request(url, 'get', 'html', callback);
    };

    uPREP.json = function(url, callback) {
        uPREP.request(url, 'get', 'json', callback);
    };

    uPREP.request = function(url, type, dataType, callback) {
        jQuery.ajax({
            url: url,
            type: type,
            dataType: dataType,
            success: function(result) {
                callback(result);
            }
        });
    };

    uPREP.sendAjax = function(url, type, data, callback, callbackFail){
        $.ajax({
            url: url,
            type: type,
            dataType: 'json',
            data : JSON.stringify(data),
            success : function(response, options){
                if(callback != null){
                    callback(response, options);
                }
            },
            error : function(err){
                if(callbackFail != null){
                    callbackFail(err);
                }
            }
        });
    };

    uPREP.radioGroup = function(groupname) {
        return $('input:radio[name="' + groupname + '"]');
    };

    uPREP.query = function(value) {
        return $(value);
    };
    uPREP.checkedRadio = function(value) {
        return $('input:radio[name ="'+value+'"]:checked');
    };
    uPREP.selectedCheckbox = function(value) {
        return $('input[name ="'+value+'"]:checked').map(function () {return this.value;}).get().join(",");
    };
    uPREP.selectedCheckboxList = function(value) {
        return $('input[name ="'+value+'"]:checked');
    };
    uPREP.selectedOption = function(value) {
        return $('#'+value+' option:selected');
    };

    uPREP.createWebSocket = function(port, path, mainCallback, subCallback){
        var host = location.hostname;
        if(host == "localhost"){
            host = "127.0.0.1";
        }
        var webSocketUrl = "ws://" + host + ":" + port + "/" + path;

        var ws = $.websocket(webSocketUrl, {
            open: function() {
                console.log("open : " + webSocketUrl);
            },
            close: function() {
                console.log("close : " + webSocketUrl);
            },
            events: {
                CHANGE_MAIN: function(e) {
                    if(mainCallback != null){
                        mainCallback(e);
                    }
                },
                CHANGE_SUB: function(e) {
                    if(subCallback != null){
                        subCallback(e);
                    }
                }
            }
        });

        return ws;
    };

    uPREP.getUrlVars = function() {
        var vars = {};
        window.location.href.replace(/[?&]+([^=&]+)=([^&#]*)/gi, function(m,key,value) {
            vars[key] = value;
        });
        return vars;
    };

    uPREP.createControl = function(service, pages) {
        var initialized = false;
        var current_service = service;
        var current_view = null;
        var contents = {};

        var control = function() {
            //log("create " + service);
        };

        control.buttonToggle = false;

        control.getService = function() {
            return current_service;
        };

        control.getView = function() {
            return current_view;
        };

        control.setView = function(view) {
            current_view = view;
        };

        control.getContents = function() {
            return contents[control.getView()];
        };

        control.setContents = function(html) {
            contents[control.getView()] = html;
        };

        control.initialized = function() {
            if(initialized) {
                return;
            }

            initialized = true;

            control.getTab().mouseup(function() {
                control.show();
            });
        };

        control.getTab = function() {
            return $('#view_' + this.getService());
        };

        control.fire = function(event) {
            control.event(event);
        };

        control.event = function(event) {
            //log(event);
        };

        control.bind = function() {
        };

        control.show = function(callback) {
            uPREP.show(control, callback);
        };

        control.beforeHide = function(oldView) {
        };

        control.afterHide = function(oldView) {
        };

        if(pages != null) {
            control.setView(pages[0]);
        }

        uPREP[control.getService()] = control;

        return control;
    };

    window.uPREP = uPREP;
})(window, jQuery);