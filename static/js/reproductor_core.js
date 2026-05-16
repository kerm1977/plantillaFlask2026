// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️
// ✂️ INICIO DE CORTE: reproductor_core.js ✂️
// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️

// ==========================================
// LÓGICA DEL REPRODUCTOR GLOBAL Y PLAYLIST
// ==========================================
const audio = document.getElementById('globalAudioPlayer');
let songsList = [];
let currentIdx = -1;

let isShuffle = localStorage.getItem('tribu_music_shuffle') === 'true';
let isRepeatOne = localStorage.getItem('tribu_music_repeat') === 'true';

const offcanvasEl = document.getElementById('reproductorGlobal');

function showMiniPlayer() {
    const mp = document.getElementById('miniPlayer');
    if(mp) {
        mp.classList.remove('d-none');
        mp.classList.add('d-flex');
    }
}

function hideMiniPlayer() {
    const mp = document.getElementById('miniPlayer');
    if(mp) {
        mp.classList.remove('d-flex');
        mp.classList.add('d-none');
    }
}

if(offcanvasEl) {
    offcanvasEl.addEventListener('show.bs.offcanvas', () => {
        hideMiniPlayer();
    });
    
    offcanvasEl.addEventListener('hidden.bs.offcanvas', () => {
        if (currentIdx !== -1 && (!audio || !audio.paused || audio.currentTime > 0)) {
            showMiniPlayer();
        }
    });
}

function closeMiniPlayer() {
    hideMiniPlayer();
    
    if(audio) {
        audio.pause();
        audio.currentTime = 0;
        audio.removeAttribute('src');
        audio.load();
    }
    currentIdx = -1; 
    
    const miniTitle = document.getElementById('miniTitle');
    const bigTitle = document.getElementById('bigTitle');
    if(miniTitle) miniTitle.innerText = "Cargando...";
    if(bigTitle) bigTitle.innerText = "Selecciona una pista";
    
    const globalLogoUrl = `/static/music/logo.png?v=${new Date().getTime()}`;
    const miniCover = document.getElementById('miniCover');
    const bigCover = document.getElementById('bigCover');
    if(miniCover) miniCover.src = globalLogoUrl;
    if(bigCover) bigCover.src = globalLogoUrl;
    
    localStorage.removeItem('tribu_music_idx');
    localStorage.removeItem('tribu_music_time');
    localStorage.setItem('tribu_music_playing', 'false');
    
    updateUI();
}

document.addEventListener("DOMContentLoaded", async () => {
    updateControlColors(); 
    await fetchAndRenderSongs();
    
    const savedIdx = localStorage.getItem('tribu_music_idx');
    const savedTime = localStorage.getItem('tribu_music_time');
    const wasPlaying = localStorage.getItem('tribu_music_playing') === 'true';

    if (savedIdx !== null && songsList[savedIdx]) {
        currentIdx = parseInt(savedIdx);
        loadSongData(currentIdx);
        
        if (savedTime && audio) audio.currentTime = parseFloat(savedTime);
        
        if (wasPlaying && audio) {
            showMiniPlayer();
            audio.play().catch(e => {
                console.log("Se requiere interacción para reanudar.");
                updateUI();
            });
        }
    }
    
    // Asignar imagen base segura sin crear errores 404
    const avatarPreview = document.getElementById('avatarPreviewImg');
    const musicCover = document.getElementById('musicCoverPreviewImg');
    if(avatarPreview && avatarPreview.src.includes('default.png')) avatarPreview.src = cleanImage;
    if(musicCover && musicCover.src.includes('default.png')) musicCover.src = cleanImage;
});

async function fetchAndRenderSongs() {
    try {
        const res = await fetch('/api/songs');
        if(res.ok) {
            songsList = await res.json();
            renderPlaylist();
        }
    } catch (e) { console.error("Música no disponible", e); }
}

function renderPlaylist() {
    const container = document.getElementById('playlistContainer');
    if(!container) return;

    container.innerHTML = '';
    
    const totalCount = document.getElementById('totalSongsCount');
    if (songsList.length === 0) {
        container.innerHTML = '<div class="text-center text-white text-opacity-50 mt-3 small">No hay canciones disponibles.</div>';
        if(totalCount) totalCount.innerText = '0 canciones';
        return;
    }

    if(totalCount) totalCount.innerText = `${songsList.length} canciones disponibles`;

    songsList.forEach((song, idx) => {
        const isPlaying = (idx === currentIdx);
        const activeClass = isPlaying ? 'bg-orange bg-opacity-75 text-white shadow-sm' : 'bg-dark bg-opacity-25 text-white text-opacity-75';
        
        let playIconHTML = '<i class="bi bi-play-circle-fill fs-4"></i>';
        if (isPlaying) {
            playIconHTML = '<i class="bi bi-pause-circle-fill text-white fs-4"></i>';
        }

        let adminControls = '';
        const downloadBtn = `<a href="/static/music/${song.filename}" download="${song.title}.mp3" class="btn btn-sm btn-dark text-success p-1 ms-1 rounded-circle d-flex align-items-center justify-content-center" style="width:28px; height:28px;" onclick="event.stopPropagation();" title="Descargar"><i class="bi bi-cloud-arrow-down-fill"></i></a>`;

        if (isGlobalSuperUser) {
            adminControls = `
                <button class="btn btn-sm btn-dark text-info p-1 ms-1 rounded-circle d-flex align-items-center justify-content-center" style="width:28px; height:28px;" onclick="event.stopPropagation(); editSong(${song.id}, '${song.title.replace(/'/g, "\\'")}')" title="Renombrar"><i class="bi bi-pencil-fill"></i></button>
                <button class="btn btn-sm btn-dark text-danger p-1 ms-1 rounded-circle d-flex align-items-center justify-content-center" style="width:28px; height:28px;" onclick="event.stopPropagation(); deleteSong(${song.id})" title="Borrar"><i class="bi bi-trash-fill"></i></button>
            `;
        }

        const coverUrl = `/static/music/logo.png?v=${new Date().getTime()}`;

        container.innerHTML += `
            <div class="playlist-item d-flex align-items-center justify-content-between p-2 rounded-4 ${activeClass}" style="cursor: pointer; border: 1px solid rgba(255,255,255,0.05);" onclick="playSpecificSong(${idx})">
                <div class="d-flex align-items-center gap-3 overflow-hidden">
                    <div class="position-relative flex-shrink-0">
                        <img src="${coverUrl}" width="45" height="45" class="rounded-circle shadow-sm" style="object-fit: cover; border: 2px solid rgba(255,255,255,0.2);">
                    </div>
                    <div class="d-flex flex-column text-truncate">
                        <span class="fw-bold text-truncate" style="font-size: 0.9rem;">${song.title}</span>
                        <span class="small opacity-75" style="font-size: 0.7rem;">La Tribu</span>
                    </div>
                </div>
                <div class="d-flex align-items-center pe-2">
                    ${playIconHTML}
                    ${downloadBtn}
                    ${adminControls}
                </div>
            </div>
        `;
    });
}

function playSpecificSong(idx) {
    if (currentIdx === idx) {
        togglePlayPause();
    } else {
        currentIdx = idx;
        loadSongData(idx);
        if(audio) {
            audio.play();
            updateUI();
        }
    }
}

function loadSongData(idx) {
    if(idx < 0 || idx >= songsList.length) return;
    const song = songsList[idx];
    
    const miniIcon = document.getElementById('miniPlayIcon');
    if(miniIcon) miniIcon.className = 'spinner-border spinner-border-sm text-white mt-1 mb-1';
    
    const bigIcon = document.getElementById('bigPlayIcon');
    if(bigIcon) {
        bigIcon.className = 'spinner-border text-white';
        bigIcon.style.width = '2.5rem';
        bigIcon.style.height = '2.5rem';
        bigIcon.style.borderWidth = '0.25em';
    }

    if(audio) {
        audio.src = `/static/music/${song.filename}`;
        audio.load();
    }
    
    const coverUrl = `/static/music/logo.png?v=${new Date().getTime()}`;
    
    const miniCover = document.getElementById('miniCover');
    const bigCover = document.getElementById('bigCover');
    const miniTitle = document.getElementById('miniTitle');
    const bigTitle = document.getElementById('bigTitle');
    
    if(miniCover) miniCover.src = coverUrl;
    if(bigCover) bigCover.src = coverUrl;
    if(miniTitle) miniTitle.innerText = song.title;
    if(bigTitle) bigTitle.innerText = song.title;
    
    localStorage.setItem('tribu_music_idx', idx);
    renderPlaylist(); 
}

function togglePlayPause() {
    if(songsList.length === 0 || !audio) return;
    if(currentIdx === -1) { currentIdx = 0; loadSongData(currentIdx); }
    
    if (audio.paused) {
        audio.play();
        if (offcanvasEl && !offcanvasEl.classList.contains('show')) {
            showMiniPlayer();
        }
    } else {
        audio.pause();
    }
}

function updateUI() {
    if(!audio) return;
    const isPaused = audio.paused;
    
    const bigIcon = document.getElementById('bigPlayIcon');
    if(bigIcon) {
        bigIcon.style.width = '';
        bigIcon.style.height = '';
        bigIcon.style.borderWidth = '';
    }

    const miniIcon = document.getElementById('miniPlayIcon');
    if(miniIcon) miniIcon.className = isPaused ? 'bi bi-play-fill fs-3' : 'bi bi-pause-fill fs-3';
    if(bigIcon) bigIcon.className = isPaused ? 'bi bi-play-fill' : 'bi bi-pause-fill';
    
    const miniCover = document.getElementById('miniCover');
    const bigCover = document.getElementById('bigCover');

    if (isPaused || currentIdx === -1) {
        if(miniCover) miniCover.classList.remove('spin-animation');
        if(bigCover) bigCover.classList.remove('spin-animation');
        localStorage.setItem('tribu_music_playing', 'false');
    } else {
        if(miniCover) miniCover.classList.add('spin-animation');
        if(bigCover) bigCover.classList.add('spin-animation');
        localStorage.setItem('tribu_music_playing', 'true');
    }
    renderPlaylist(); 
}

if(audio) {
    audio.addEventListener('waiting', () => {
        const miniIcon = document.getElementById('miniPlayIcon');
        if(miniIcon) miniIcon.className = 'spinner-border spinner-border-sm text-white mt-1 mb-1';
        
        const bigIcon = document.getElementById('bigPlayIcon');
        if(bigIcon) {
            bigIcon.className = 'spinner-border text-white';
            bigIcon.style.width = '2.5rem';
            bigIcon.style.height = '2.5rem';
            bigIcon.style.borderWidth = '0.25em';
        }
    });

    audio.addEventListener('playing', updateUI);
    audio.addEventListener('pause', updateUI);
    audio.addEventListener('canplay', () => {
        if (!audio.paused) updateUI();
    });
    audio.addEventListener('ended', () => nextSong(true)); 

    audio.addEventListener('timeupdate', () => {
        if (audio.duration) {
            localStorage.setItem('tribu_music_time', audio.currentTime);
            const progress = (audio.currentTime / audio.duration) * 100;
            const pb = document.getElementById('progressBar');
            if(pb) pb.value = progress;
            
            const ct = document.getElementById('currentTime');
            const tt = document.getElementById('totalTime');
            if(ct) ct.innerText = formatTime(audio.currentTime);
            if(tt) tt.innerText = formatTime(audio.duration);
        }
    });
}

function toggleShuffle() {
    isShuffle = !isShuffle;
    localStorage.setItem('tribu_music_shuffle', isShuffle);
    updateControlColors();
}

function toggleRepeat() {
    isRepeatOne = !isRepeatOne;
    localStorage.setItem('tribu_music_repeat', isRepeatOne);
    updateControlColors();
}

function updateControlColors() {
    const btnShuffle = document.getElementById('btnShuffle');
    const btnRepeat = document.getElementById('btnRepeat');
    
    if (btnShuffle) {
        btnShuffle.className = isShuffle ? 'btn border-0 text-orange p-2' : 'btn border-0 text-white opacity-50 p-2';
    }
    if (btnRepeat) {
        btnRepeat.className = isRepeatOne ? 'btn border-0 text-orange p-2' : 'btn border-0 text-white opacity-50 p-2';
        btnRepeat.innerHTML = isRepeatOne ? '<i class="bi bi-repeat-1 fs-3"></i>' : '<i class="bi bi-repeat fs-3"></i>';
    }
}

function nextSong(isAutoPlay = false) {
    if(songsList.length === 0 || !audio) return;
    
    if (isAutoPlay && isRepeatOne) {
        audio.currentTime = 0;
        audio.play();
        return;
    }

    if (isShuffle && songsList.length > 1) {
        let randomIdx = currentIdx;
        while (randomIdx === currentIdx) {
            randomIdx = Math.floor(Math.random() * songsList.length);
        }
        currentIdx = randomIdx;
    } else {
        currentIdx = (currentIdx + 1) % songsList.length;
    }
    
    loadSongData(currentIdx);
    audio.play();
}

function prevSong() {
    if(songsList.length === 0 || !audio) return;
    
    if (audio.currentTime > 3) {
        audio.currentTime = 0;
        return;
    }

    currentIdx = (currentIdx - 1 + songsList.length) % songsList.length;
    loadSongData(currentIdx);
    audio.play();
}

const pb = document.getElementById('progressBar');
if(pb) {
    pb.addEventListener('input', (e) => {
        if(audio && audio.duration) audio.currentTime = (e.target.value / 100) * audio.duration;
    });
}

function formatTime(seconds) {
    if(isNaN(seconds)) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
}

// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️
// ✂️ FIN DE CORTE: reproductor_core.js ✂️
// ✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️✂️
