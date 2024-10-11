const localVideo = document.getElementById('localVideo');
const remoteVideo = document.getElementById('remoteVideo');
const startButton = document.getElementById('startButton');

let localStream;
let peerConnection;
const server = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' } // STUN-сервер
    ]
};

// Начать звонок
startButton.onclick = async () => {
    await startCall();
};

async function startCall() {
    // Получить локальный медиапоток
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    localVideo.srcObject = localStream;

    // Создать соединение пира
    peerConnection = new RTCPeerConnection(server);

    // Добавить локальные треки в соединение пира
    localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream);
    });

    // Обработать входящий удаленный поток
    peerConnection.ontrack = (event) => {
        remoteVideo.srcObject = event.streams[0];
    };

    // Создать предложение и установить локальное описание
    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);

    // Отправить предложение на сервер сигнализации (реализуйте эту часть)
    // signalingServer.send({ type: 'offer', offer: offer });
}

// Обработать входящие сообщения сигнализации (реализуйте эту часть)
async function handleSignalingMessage(message) {
    if (message.type === 'offer') {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(message.offer));
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        // signalingServer.send({ type: 'answer', answer: answer });
    } else if (message.type === 'answer') {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(message.answer));
    } else if (message.type === 'ice-candidate') {
        await peerConnection.addIceCandidate(new RTCIceCandidate(message.candidate));
    }
}

// Обработать ICE-кандидатов
peerConnection.onicecandidate = (event) => {
    if (event.candidate) {
        // Отправить кандидата на сервер сигнализации (реализуйте эту часть)
        // signalingServer.send({ type: 'ice-candidate', candidate: event.candidate });
    }
};
