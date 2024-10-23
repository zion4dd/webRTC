const connect = document.getElementById("connect");
const connectId = document.getElementById("connectId");

const form = document.getElementById("form");
const formInput = document.getElementById("formInput");
const formButton = document.getElementById("formButton");

const goCall = document.getElementById("goCall");
const goCallId = document.getElementById("goCallId");
const goCallButton = document.getElementById("goCallButton");
const hangUpButton = document.getElementById("hangUpButton");

const messages = document.getElementById("messages");
const clients = document.getElementById("clients");

const localVideo = document.getElementById("localVideo");
const remoteVideo = document.getElementById("remoteVideo");

const server = {
  iceServers: [
    { urls: "stun:stun.l.google.com:19302" }, // STUN-сервер
  ],
};

let sender;
let target;
let ws;
let localStream;
let peerConnection;

goCallButton.disabled = true;
formButton.disabled = true;
hangUpButton.disabled = true;

connect.onsubmit = (event) => {
  event.preventDefault();
  console.log(connectId.value);
  sender = connectId.value;
  ws = new WebSocket(`ws://localhost:8000/ws/${connectId.value}`);
  formInput.value = "";

  ws.onmessage = async (event) => {
    if (event.data.startsWith("@clients:")) {
      // Если сообщение начинается с "@clients:", добавляем в объект clients
      const clients = document.getElementById("clients");
      clients.textContent = event.data;
    } else if (event.data.startsWith("ping")) {
      console.log(event.data);
    } else if (event.data.startsWith("{")) {
      await handleSignalingMessage(JSON.parse(event.data));
    } else {
      const li = document.createElement("li");
      li.textContent = event.data;
      messages.appendChild(li);
    }
  };
  goCallButton.disabled = false;
  formButton.disabled = false;
};

form.onsubmit = (event) => {
  event.preventDefault();
  ws.send(
    JSON.stringify({
      type: "msg",
      msg: formInput.value,
    })
  );
  formInput.value = "";
};

goCall.onsubmit = async (event) => {
  event.preventDefault();
  await startCall();
  goCallButton.disabled = true;
  hangUpButton.disabled = false;
};

hangUpButton.onclick = () => {
  hangup();
  ws.send(
    JSON.stringify({
      type: "bye",
      target: target,
    })
  );
};

function hangup() {
  console.log("Ending call");
  peerConnection.close();
  peerConnection = null;
  localStream.getTracks().forEach((track) => track.stop());
  localStream = null;
  hangUpButton.disabled = true;
  goCallButton.disabled = false;
}

async function startCall() {
  target = goCallId.value;
  const peerConnection = await getPeerConnection();
  // Создать предложение и установить локальное описание
  const offer = await peerConnection.createOffer();
  await peerConnection.setLocalDescription(offer);
  console.log(`setLocalDescription complete`);
  offer.sender = sender;
  offer.target = target;
  //console.log(offer)
  // Отправить предложение на сервер сигнализации
  ws.send(JSON.stringify(offer));
}

// Обработать входящие сообщения сигнализации
async function handleSignalingMessage(message) {
  if (message.type === "offer") {
    target = message.sender;
    const peerConnection = await getPeerConnection();
    await peerConnection.setRemoteDescription(
      new RTCSessionDescription(message)
    );
    console.log(`setRemoteDescription complete`);
    const answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);
    console.log(`setLocalDescription complete`);
    answer.sender = sender;
    answer.target = target;
    ws.send(JSON.stringify(answer));
  } else if (message.type === "answer") {
    await peerConnection.setRemoteDescription(
      new RTCSessionDescription(message)
    );
    console.log(`setRemoteDescription complete`);
  } else if (message.type === "icecandidate") {
    await peerConnection
      .addIceCandidate(new RTCIceCandidate(message.candidate))
      .catch(window.reportError);
    console.log(`addIceCandidate success`);
  } else if (message.type === "bye") {
    hangup();
  }
}

// Получить соединение пира с медиапотоком и локальными треками.
async function getPeerConnection() {
  // Создать соединение пира
  peerConnection = new RTCPeerConnection(server);
  // Получить локальный медиапоток
  localStream = await navigator.mediaDevices.getUserMedia({
    video: true,
    audio: true,
  });
  localVideo.srcObject = localStream;
  // Добавить локальные треки в соединение пира
  localStream.getTracks().forEach((track) => {
    peerConnection.addTrack(track, localStream);
  });
  // Отправьте кандидата на сервер для другого участника
  peerConnection.onicecandidate = (event) => {
    if (event.candidate) {
      ws.send(
        JSON.stringify({
          type: "icecandidate",
          candidate: event.candidate,
          target: target,
        })
      );
    }
  };
  // Обработать входящий удаленный поток
  peerConnection.ontrack = (event) => {
    remoteVideo.srcObject = event.streams[0];
  };
  return peerConnection;
}

//TODO hangUp, target user_id, verification user, chat
//https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Signaling_and_video_calling#sending_messages_to_the_signaling_server
