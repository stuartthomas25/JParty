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
    if (now - last_buzz > 250) {
        last_buzz = now;
        var message = {message:'BUZZ', text: ''};
        updater.socket.send(JSON.stringify(message));
    };

}

async function yourturn() {

    //var secs = 5;
    //var buzzer_obj = document.getElementById("buzzer");
    //buzzer_obj.classList.add('answering');
    //for (let i = 0; i < secs; i++) {
        //lights_on(i);
    //}
    //for (let i = 0; i < secs; i++) {
        //await sleep(1000);
        //lights_off(i);
    //}
    /*buzzer_obj.classList.remove('answering');*/
}

function nameForm() {
    var name = $("input[name='playername']").val();
    console.log(name);
    var message = {message:'NAME', text: name};
    updater.socket.send(JSON.stringify(message));

    $(".name-page").hide();
    $(".buzz-page").show();


    return false;
}

$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};
    $(".buzz-page").hide();
    updater.start();
});

var updater = {
    socket: null,

    start: function() {
        var url = "ws://" + location.host + "/buzzersocket";
        updater.socket = new WebSocket(url);
        updater.socket.onmessage = function(event) {
            jsondata = JSON.parse(event.data);
            switch (jsondata.message) {
                case "GAMEFULL":
                    game_full();
                    break;
                case "TOOLATE":
                    alert("toolate");
                    break;
                case "YOURTURN":
                    yourturn();
            }
        }
    }
};

function game_full() {
    alert("This game already has enough players!")
}


