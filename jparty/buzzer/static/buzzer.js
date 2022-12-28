

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

var last_buzz = new Date().getTime();

async function buzz() {
    if (!$("#buzzer").prop("disabled")) {
        send("BUZZ");
        $("#buzzer").prop("disabled", true);

        setTimeout(function () {
            $("#buzzer").prop("disabled", false);
        }, 250);
    };
}

var current_page = "";
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
    document.activeElement.blur();
    load_page(null);
    return false;
}

function nameForm(name) {
    console.log(name);
    send("NAME",name);
}

function set_max_wager(score) {
    $(".wager_input").attr("max", score);
    $(".wager_input").attr("min",0);
    console.log("Max wager:" + $(".wager_input").attr("max"));
}

const padding = 2;
const canvasratio = 1.3422;

var signaturePad;

function resizeCanvas() {
    const ratio =  Math.max(window.devicePixelRatio || 1, 1);
    const canvas = document.querySelector("canvas");
    canvas.width = canvas.offsetWidth * ratio;
    canvas.height = canvas.width / canvasratio;
    canvas.getContext("2d").scale(ratio, ratio);
    signaturePad.clear(); // otherwise isEmpty() might return incorrect value
}


$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};
    // load_page("name");

    updater.start();

    const canvas = document.querySelector("canvas");
    canvas.style.width = "100%";

    signaturePad = new SignaturePad(canvas, {
        penColor: "#ffffff",
        backgroundColor: "#1010a1"
    });


    window.addEventListener("resize", resizeCanvas);
    // resizeCanvas();

    var cookie = getToken();
    if (cookie != "") {
        console.log("checking token "+cookie)
        updater.socket.onopen = function (event) {
            updater.socket.send(JSON.stringify({message:"CHECK_IF_EXISTS", text:cookie}));
        };
    } else {
        load_page("name");
        resizeCanvas();
    };



    $("#clear-button").on("click", function () {
        signaturePad.clear()
    });

    $("#undo-button").on("click", function () {
        const data = signaturePad.toData();

        if (data) {
            data.pop(); // remove the last dot or line
            signaturePad.fromData(data);
        }
    });

    $("#prompt-button").on("click", function () {
        let name = prompt("Enter name", "");
        if (name != null) {
            nameForm(name);
        };
    });

    $("#submit-button").on("click", function () {
        if (!signaturePad.isEmpty()) {
            let image = signaturePad.toDataURL();
            console.log(image);
            nameForm(image);
        };
    });
});





var updater = {
    socket: null,

    start: function() {
        var url = "ws://" + location.host + "/buzzersocket";
        updater.socket = new WebSocket(url);
        updater.socket.onclose = function(event) { location.reload(true); };
        updater.socket.onmessage = function(event) {
            jsondata = JSON.parse(event.data);
            switch (jsondata.message) {
                case "GAMEFULL":
                    alert("Game has too many players!")
                    window.location.reload()
                    break;
                case "GAMESTARTED":
                    alert("Game has started!")
                    break;
                case "TOKEN":
                    load_page("buzz");
                    setToken(jsondata.text);
                    break;
                case "NEW":
                    load_page("name");
                    resizeCanvas();
                    break;
                case "EXISTS":
                    console.log("Already exists" + jsondata.text);
                    state = JSON.parse(jsondata.text);
                    set_max_wager(state.score);
                    load_page(state.page);
                    break;
                case "PROMPTWAGER":
                    set_max_wager(jsondata.text);
                    load_page("wager");
                    break;
                case "PROMPTANSWER":
                    load_page("answer");
                    break;
                case "TOOLATE":
                    answerForm();
                    break;
            }
        }
    }
};



