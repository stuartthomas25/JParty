function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function lights_on(i) {
    for (l of document.getElementsByClassName("l" + i.toString())){
        l.classList.add("lit");
    };
}

function lights_off(i) {
    for (l of document.getElementsByClassName("l" + i.toString())){
        l.classList.remove("lit");
    };
}
var last_buzz = new Date().getTime();
async function buzz() {
    var now = new Date().getTime();
    if (now - window.last_buzz > 250) {
        window.last_buzz = now;
        console.log("BUZZ");
        send("BUZZ");
    };

}

var current_page = "name";
function load_page(pagename) {
    try {
        if (pagename !== null && pagename != "null") {
            $("."+pagename+"-page").show();
        }
    } catch {
        return 1;
    }
    if (!!current_page) {
        $("."+current_page+"-page").hide();
    }
    current_page = pagename;
    return 0;
}

/*async function yourturn() {*/

    ////var secs = 5;
    ////var buzzer_obj = document.getElementById("buzzer");
    ////buzzer_obj.classList.add('answering');
    ////for (let i = 0; i < secs; i++) {
        ////lights_on(i);
    ////}
    ////for (let i = 0; i < secs; i++) {
        ////await sleep(1000);
        ////lights_off(i);
    ////}
    //[>buzzer_obj.classList.remove('answering');<]
/*}*/
function setToken(token) {
  var d = new Date();
  d.setTime(d.getTime() + (24*60*60*1000)); // lasts 24 hour
  var expires = "expires="+ d.toUTCString();
  document.cookie = "token=" + token + ";" + expires + ";path=/";
}

function getToken() {
  var name = "token=";
  var decodedCookie = decodeURIComponent(document.cookie);
  var ca = decodedCookie.split(';');
  for(var i = 0; i <ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

function send(msg, text="") {
    var message = {message:msg, text: text};
    updater.socket.send(JSON.stringify(message));
}
function wagerForm() {
    var amount =$("input[name='wager']").val().replace(/[\s,]/g, '');
    if (amount != "") {
        send("WAGER", amount);
        load_page(null);
    }
    return false;
}
function answerForm() {
    var answer = $("input[name='answer']").val();
    send("ANSWER",answer);
    load_page(null);
    return false;
}

function nameForm() {
    var name = $("input[name='playername']").val();
    if (name != "") {
        console.log(name);
        send("NAME",name);
        load_page("buzz");
    }
    return false;
}

$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};
    updater.start();
    var cookie = getToken();
    if (cookie != "") {
        console.log("checking token "+cookie)
        updater.socket.onopen = function (event) {
            updater.socket.send(JSON.stringify({message:"CHECK_IF_EXISTS", text:cookie}));
        };
    };
});

var updater = {
    socket: null,

    start: function() {
        var url = "ws://" + location.host + "/buzzersocket";
        updater.socket = new WebSocket(url);
        updater.socket.onclose = function(event) { location.reload(true); };
        updater.socket.onmessage = function(event) {
            //console.log("MSG RECIEVED: "+event.data);
            jsondata = JSON.parse(event.data);
            switch (jsondata.message) {
                case "GAMEFULL":
                    //alert((Date.now()-last_buzz) % 1000);
                    alert("This game already has three players!")
                    break;
                case "NAMETAKEN":
                    alert("That name is already taken");
                    window.location.reload()
                    break;
                case "TOKEN":
                    setToken(jsondata.text);
                    break;
                case "EXISTS":
                    console.log("Already exists");
                    load_page(jsondata.text);
                    break;
                case "PROMPTWAGER":
                    load_page("wager");
                    $(".wager_input").attr("max",jsondata.text);
                    $(".wager_input").attr("min",0);
                    console.log("Max wager:" + $(".wager_input").attr("max"));
                    break;
                case "PROMPTANSWER":
                    load_page("answer");
                    setInterval(answerForm, 31000);
                    break;
            }
        }
    }
};
