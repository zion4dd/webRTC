const connect = document.getElementById('connect');
const clientId = document.getElementById('clientId');
const form = document.getElementById('form');
const input = document.getElementById('message');
const messages = document.getElementById('messages');
const clients = document.getElementById('clients');

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

connect.onsubmit = function(event) {
    event.preventDefault();
    console.log(clientId.value)
    const ws = new WebSocket(`ws://localhost:8000/call/${clientId.value}`);
    input.value = '';

    ws.onmessage = async function(event) {
        if (event.data.startsWith("@clients:")) {
            // Если сообщение начинается с "@clients:", добавляем в объект clients
            const clients = document.getElementById('clients');
            clients.textContent = event.data;
        } else if (event.data.startsWith("ping")) {
            console.log(event.data)
        } else if (event.data.startsWith("{")) {
            await handleSignalingMessage(JSON.parse(event.data))
        } else {
            const li = document.createElement('li');
            li.textContent = event.data;
            messages.appendChild(li);
        }
    };

    form.onsubmit = function(event) {
        event.preventDefault();
        ws.send(input.value);
        input.value = '';
    };

    // Начать звонок
    startButton.onclick = async () => {
        await startCall();
    };

    async function startCall() {
        // Создать соединение пира
        peerConnection = new RTCPeerConnection(server);
        
        // Получить локальный медиапоток
        localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        localVideo.srcObject = localStream;
    
        // Добавить локальные треки в соединение пира
        localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, localStream);
        });

        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                // Отправьте кандидата на сервер для другого участника
                //console.log(event)
                ws.send(JSON.stringify({
                    type: "icecandidate",
                    candidate: event.candidate
                }))
            }
        };
    
        // Обработать входящий удаленный поток
        peerConnection.ontrack = (event) => {
            remoteVideo.srcObject = event.streams[0];
        };
    
        // Создать предложение и установить локальное описание
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        console.log(`setLocalDescription complete`);
        
        // Отправить предложение на сервер сигнализации
        //console.log(offer)
        ws.send(JSON.stringify(offer))
    }

    // Обработать входящие сообщения сигнализации (реализуйте эту часть)
    async function handleSignalingMessage(message) {
        if (message.type === 'offer') {
            // Создать соединение пира
            peerConnection = new RTCPeerConnection(server);

            // Получить локальный медиапоток
            localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            localVideo.srcObject = localStream;
        
            // Добавить локальные треки в соединение пира
            localStream.getTracks().forEach(track => {
                peerConnection.addTrack(track, localStream);
            });

            peerConnection.onicecandidate = (event) => {
                if (event.candidate) {
                    // Отправьте кандидата на сервер для другого участника
                    //console.log(event)
                    ws.send(JSON.stringify({
                        type: "icecandidate",
                        candidate: event.candidate
                    }))
                }
            };

            // Обработать входящий удаленный поток
            peerConnection.ontrack = (event) => {
                remoteVideo.srcObject = event.streams[0];
            };
            
            await peerConnection.setRemoteDescription(new RTCSessionDescription(message));
            console.log(`setRemoteDescription complete`);
            const answer = await peerConnection.createAnswer();
            await peerConnection.setLocalDescription(answer);
            console.log(`setLocalDescription complete`);
            ws.send(JSON.stringify(answer))
            // signalingServer.send({ type: 'answer', answer: answer });

        } else if (message.type === 'answer') {
            //console.log(message)
            await peerConnection.setRemoteDescription(new RTCSessionDescription(message));
            console.log(`setRemoteDescription complete`);

        } else if (message.type === 'icecandidate') {
            console.log(message)
            await peerConnection.addIceCandidate(new RTCIceCandidate(message.candidate)).catch(window.reportError);
            console.log(`addIceCandidate success`);
        }
    }
    
};

