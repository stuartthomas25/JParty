

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

var last_buzz = new Date().getTime();

async function buzz() {
    var now = new Date().getTime();
    // if (now - window.last_buzz > 250) {
        // window.last_buzz = now;
        console.log("BUZZ");
        send("BUZZ");

        $("#buzzer").prop("disabled", true);
        setTimeout(function () {
            $("#buzzer").prop("disabled", false);
        }, 250)
    // };

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

function nameForm(name) {
    console.log(name);
    send("NAME",name);
    load_page("buzz");
}

const padding = 2;
const canvasratio = 2;

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

    const canvas = document.querySelector("canvas");
    canvas.style.width = "100%";

    const signaturePad = new SignaturePad(canvas, {
        penColor: "#ffffff",
        backgroundColor: "#031591"
    });

    function resizeCanvas() {
        console.log("resize");
        const ratio =  Math.max(window.devicePixelRatio || 1, 1);
        canvas.width = canvas.offsetWidth * ratio;
        canvas.height = canvas.width / canvasratio;
        canvas.getContext("2d").scale(ratio, ratio);
        signaturePad.clear(); // otherwise isEmpty() might return incorrect value
    }

    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();

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



